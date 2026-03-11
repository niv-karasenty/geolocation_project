"""
Visual test for geolocation plot.

Generates a plot with:
  - The analytical polygon (red)
  - The known TX position (green star)
  - A grid of test points colored green (inside region) / grey (outside)

If the polygon is correct, the green dots should fill exactly the red area
and the TX star should sit inside it.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geolocation import compute_intersection, shoelace_area

TOLERANCE = 1e-6


def point_in_region(px, py, rx1, rx2):
    """Check if point satisfies all 4 half-plane inequalities."""
    for rx in [rx1, rx2]:
        t_min = np.radians(rx["min_angle"])
        t_max = np.radians(rx["max_angle"])
        cross_min = np.cos(t_min) * (py - rx["y"]) - np.sin(t_min) * (px - rx["x"])
        cross_max = np.cos(t_max) * (py - rx["y"]) - np.sin(t_max) * (px - rx["x"])
        if cross_min < -TOLERANCE or cross_max > TOLERANCE:
            return False
    return True


def test_plot_visual():
    # ── Known transmitter ──
    TX = {"x": 5.0, "y": 8.0}

    rx1_pos = (0.0, 0.0)
    rx2_pos = (10.0, 0.0)

    angle1 = np.degrees(np.arctan2(TX["y"] - rx1_pos[1], TX["x"] - rx1_pos[0]))
    angle2 = np.degrees(np.arctan2(TX["y"] - rx2_pos[1], TX["x"] - rx2_pos[0]))

    spread = 8.0
    RX1 = {"x": rx1_pos[0], "y": rx1_pos[1],
            "min_angle": angle1 - spread, "max_angle": angle1 + spread}
    RX2 = {"x": rx2_pos[0], "y": rx2_pos[1],
            "min_angle": angle2 - spread, "max_angle": angle2 + spread}

    area, vertices = compute_intersection(RX1, RX2)
    assert vertices, "No intersection found"

    # ── Sample a grid of points and classify ──
    xs = np.linspace(-2, 12, 200)
    ys = np.linspace(-2, 18, 200)
    inside_x, inside_y = [], []
    outside_x, outside_y = [], []

    for x in xs:
        for y in ys:
            if point_in_region(x, y, RX1, RX2):
                inside_x.append(x)
                inside_y.append(y)
            else:
                outside_x.append(x)
                outside_y.append(y)

    # ── Monte Carlo area check ──
    # The ratio of inside points × total grid area should ≈ analytical area
    grid_area = (xs[-1] - xs[0]) * (ys[-1] - ys[0])
    total_pts = len(xs) * len(ys)
    mc_area = len(inside_x) / total_pts * grid_area
    print(f"\n  Analytical area : {area:.4f}")
    print(f"  Monte Carlo area: {mc_area:.4f}  (grid {len(xs)}x{len(ys)})")
    print(f"  Difference      : {abs(area - mc_area):.4f}  ({abs(area - mc_area)/area*100:.2f}%)")
    assert abs(area - mc_area) / area < 0.05, \
        f"FAIL: MC area {mc_area:.4f} differs from analytical {area:.4f} by > 5%"
    print(f"  [PASS] Monte Carlo area matches analytical (< 5% error)")

    # ── Plot ──
    fig, ax = plt.subplots(figsize=(11, 9))

    # Grey outside points (sparse for speed)
    ax.scatter(outside_x[::3], outside_y[::3], s=1, c="lightgrey", alpha=0.3, zorder=1)

    # Green inside points
    ax.scatter(inside_x, inside_y, s=2, c="limegreen", alpha=0.5, zorder=2,
               label=f"Inside region ({len(inside_x)} pts)")

    # Draw the analytical polygon on top
    poly_x = [v[0] for v in vertices] + [vertices[0][0]]
    poly_y = [v[1] for v in vertices] + [vertices[0][1]]
    ax.fill(poly_x, poly_y, color="red", alpha=0.20, zorder=3)
    ax.plot(poly_x, poly_y, color="red", linewidth=2.5, zorder=4,
            label=f"Analytical polygon (area={area:.2f})")

    # Vertex labels
    for i, (vx, vy) in enumerate(vertices):
        ax.plot(vx, vy, "ro", markersize=7, zorder=5)
        ax.annotate(f"V{i} ({vx:.2f}, {vy:.2f})", (vx, vy),
                    textcoords="offset points", xytext=(8, 6),
                    fontsize=8, color="darkred")

    # Draw rays
    ray_len = 25
    colors = {"RX1": "steelblue", "RX2": "darkorange"}
    for rx, name in [(RX1, "RX1"), (RX2, "RX2")]:
        for ang in [rx["min_angle"], rx["max_angle"]]:
            theta = np.radians(ang)
            ax.plot([rx["x"], rx["x"] + ray_len * np.cos(theta)],
                    [rx["y"], rx["y"] + ray_len * np.sin(theta)],
                    color=colors[name], linewidth=1.2, linestyle="--", alpha=0.6)

    # Receivers
    for rx, name, col in [(RX1, "RX1", "steelblue"), (RX2, "RX2", "darkorange")]:
        ax.plot(rx["x"], rx["y"], "s", color=col, markersize=12, zorder=6)
        ax.annotate(name, (rx["x"], rx["y"]), textcoords="offset points",
                    xytext=(10, -14), fontsize=12, fontweight="bold", color=col)

    # TX ground truth
    ax.plot(TX["x"], TX["y"], "*", color="green", markersize=20, zorder=7,
            markeredgecolor="black", markeredgewidth=0.8,
            label=f"TX ground truth ({TX['x']}, {TX['y']})")

    # Centroid
    cx = np.mean([v[0] for v in vertices])
    cy = np.mean([v[1] for v in vertices])
    ax.plot(cx, cy, "k*", markersize=14, zorder=7,
            label=f"Centroid ({cx:.2f}, {cy:.2f})")

    ax.set_xlim(-2, 12)
    ax.set_ylim(-2, 18)
    ax.set_aspect("equal")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Visual Test: green dots should fill exactly the red polygon\n"
                 "TX (green star) must be inside", fontsize=12)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    out = "test_geolocation_plot.png"
    plt.savefig(out, dpi=150)
    print(f"\n  Plot saved to {out}")
    print(f"  [PASS] Visual test complete — inspect the plot")


if __name__ == "__main__":
    test_plot_visual()
