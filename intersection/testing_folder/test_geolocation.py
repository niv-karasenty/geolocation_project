"""
Tests for geolocation.py

Sets up known receiver/transmitter geometry, computes expected values
analytically, and checks the code produces correct results.
"""

import numpy as np
import sys
import os

# Import from the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geolocation import compute_intersection, shoelace_area, order_polygon

TOLERANCE = 1e-4


def point_in_region(px, py, rx1, rx2):
    """Check a point satisfies all 4 half-plane inequalities."""
    for rx in [rx1, rx2]:
        t_min = np.radians(rx["min_angle"])
        t_max = np.radians(rx["max_angle"])
        # cross(dir_min, P - R) >= 0
        cross_min = np.cos(t_min) * (py - rx["y"]) - np.sin(t_min) * (px - rx["x"])
        # cross(dir_max, P - R) <= 0
        cross_max = np.cos(t_max) * (py - rx["y"]) - np.sin(t_max) * (px - rx["x"])
        if cross_min < -TOLERANCE or cross_max > TOLERANCE:
            return False
    return True


def test_known_geometry():
    """
    Place TX at a known point. Compute the exact angles from each receiver
    to the TX, build wedges around those angles, and verify:
      1. TX is inside the resulting region
      2. Area is positive
      3. Centroid is near TX
      4. All vertices satisfy the inequality system
    """
    print("TEST: known geometry")
    print("-" * 50)

    # Known transmitter location
    TX = {"x": 5.0, "y": 8.0}

    # Receiver positions
    rx1_pos = (0.0, 0.0)
    rx2_pos = (10.0, 0.0)

    # Exact angles from each receiver to TX
    angle1 = np.degrees(np.arctan2(TX["y"] - rx1_pos[1], TX["x"] - rx1_pos[0]))
    angle2 = np.degrees(np.arctan2(TX["y"] - rx2_pos[1], TX["x"] - rx2_pos[0]))

    # Build wedges: ±5° around the true angle
    spread = 5.0
    RX1 = {"x": rx1_pos[0], "y": rx1_pos[1],
            "min_angle": angle1 - spread, "max_angle": angle1 + spread}
    RX2 = {"x": rx2_pos[0], "y": rx2_pos[1],
            "min_angle": angle2 - spread, "max_angle": angle2 + spread}

    print(f"  TX         : ({TX['x']}, {TX['y']})")
    print(f"  True angle1: {angle1:.4f}°  wedge [{RX1['min_angle']:.4f}°, {RX1['max_angle']:.4f}°]")
    print(f"  True angle2: {angle2:.4f}°  wedge [{RX2['min_angle']:.4f}°, {RX2['max_angle']:.4f}°]")

    area, vertices = compute_intersection(RX1, RX2)

    # 1. Area must be positive
    assert area is not None and area > 0, f"FAIL: area should be > 0, got {area}"
    print(f"\n  [PASS] Area = {area:.4f} > 0")

    # 2. TX must be inside the region
    assert point_in_region(TX["x"], TX["y"], RX1, RX2), \
        "FAIL: TX is not inside the computed region"
    print(f"  [PASS] TX ({TX['x']}, {TX['y']}) is inside the region")

    # 3. All vertices must satisfy the inequality system
    for i, (vx, vy) in enumerate(vertices):
        assert point_in_region(vx, vy, RX1, RX2), \
            f"FAIL: vertex V{i} ({vx}, {vy}) is outside the region"
    print(f"  [PASS] All {len(vertices)} vertices satisfy the inequalities")

    # 4. Centroid should be near TX (within the spread)
    cx = np.mean([v[0] for v in vertices])
    cy = np.mean([v[1] for v in vertices])
    dist = np.hypot(cx - TX["x"], cy - TX["y"])
    print(f"  [INFO] Centroid: ({cx:.4f}, {cy:.4f}), dist to TX: {dist:.4f}")
    assert dist < 5.0, f"FAIL: centroid too far from TX ({dist:.4f})"
    print(f"  [PASS] Centroid is within 5 units of TX")


def test_exact_triangle():
    """
    Construct a case where the overlap is a known triangle with
    a calculable exact area, and verify the Shoelace result matches.
    """
    print("\nTEST: exact triangle area")
    print("-" * 50)

    # RX1 at origin, RX2 at (10, 0)
    # RX1 rays: 45° and 90° (y=x and x=0 lines from origin)
    # RX2 rays: 135° and 90° (y=-x+10 and x=10 lines from (10,0))
    # The 90° rays are parallel (both go straight up), so we get 3 intersections → triangle

    RX1 = {"x": 0.0, "y": 0.0, "min_angle": 45, "max_angle": 90}
    RX2 = {"x": 10.0, "y": 0.0, "min_angle": 90, "max_angle": 135}

    area, vertices = compute_intersection(RX1, RX2)

    # The intersecting rays:
    #   RX1@45° ∩ RX2@135°: y = x and y = -(x-10) → x=5, y=5 → (5, 5)
    #   RX1@45° ∩ RX2@90°:  y = x and x = 10      → (10, 10)
    #   RX1@90° ∩ RX2@135°: x = 0 and y = -(x-10) → (0, 10)
    #   RX1@90° ∩ RX2@90°:  parallel, no intersection

    expected_verts = [(5.0, 5.0), (10.0, 10.0), (0.0, 10.0)]
    expected_area = shoelace_area(order_polygon(expected_verts))

    assert area is not None, "FAIL: no area computed"
    assert abs(area - expected_area) < TOLERANCE, \
        f"FAIL: area {area:.6f} != expected {expected_area:.6f}"
    print(f"  [PASS] Area = {area:.4f}, expected = {expected_area:.4f}")

    # Verify vertices match
    verts_sorted = sorted(vertices)
    expected_sorted = sorted(expected_verts)
    for (vx, vy), (ex, ey) in zip(verts_sorted, expected_sorted):
        assert abs(vx - ex) < TOLERANCE and abs(vy - ey) < TOLERANCE, \
            f"FAIL: vertex ({vx}, {vy}) != expected ({ex}, {ey})"
    print(f"  [PASS] All vertices match expected positions")


def test_no_overlap():
    """
    Two wedges pointing away from each other should produce no overlap.
    """
    print("\nTEST: no overlap")
    print("-" * 50)

    RX1 = {"x": 0.0, "y": 0.0, "min_angle": 170, "max_angle": 190}
    RX2 = {"x": 10.0, "y": 0.0, "min_angle": -10, "max_angle": 10}

    area, vertices = compute_intersection(RX1, RX2)

    assert area is None or area < TOLERANCE, \
        f"FAIL: expected no overlap, got area {area}"
    print(f"  [PASS] No overlap detected")


if __name__ == "__main__":
    test_known_geometry()
    test_exact_triangle()
    test_no_overlap()
    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED")
    print("=" * 50)
