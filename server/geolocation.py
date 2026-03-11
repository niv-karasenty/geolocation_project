# -*- coding: ascii -*-
"""
Geolocation: Analytical Angle-of-Arrival (AoA) intersection.

Overview
--------
Two receivers (RX1, RX2) each observe a transmitter (TX) and report
an angular range [min_angle, max_angle] where the signal could be
coming from. Each range defines a wedge-shaped region. The TX must
lie inside BOTH wedges, so the possible TX location is their overlap.

This module computes that overlap exactly using line equations --
no discretization or ray-length approximation.

How it works (step by step)
---------------------------
1. Each receiver contributes 2 boundary rays (min_angle, max_angle).
   That gives 4 rays total.

2. Every RX1 ray is intersected with every RX2 ray (4 combinations).
   Each intersection that lies forward on both rays becomes a vertex
   of the overlap polygon.

3. The vertices are sorted counter-clockwise and the polygon area is
   computed analytically with the Shoelace formula.

4. The most likely TX position is estimated as the intersection of
   the two center rays (the bisectors of each wedge).

Coordinate system
-----------------
- Positions are in meters (m).
- Angles are in degrees, measured counter-clockwise from the
  positive X-axis (East = 0 deg, North = 90 deg).

Data format
-----------
Each receiver is a dict:
    {"x": float, "y": float, "min_angle": float, "max_angle": float}

    x, y       -- receiver position in meters
    min_angle  -- left edge of the angular wedge (degrees)
    max_angle  -- right edge of the angular wedge (degrees)

    The TX is somewhere between min_angle and max_angle as seen
    from this receiver.
"""

import numpy as np
import matplotlib.pyplot as plt

# --- Configuration -----------------------------------------------------------
# Default receiver setup for standalone testing.
# Replace these or pass your own dicts to the functions.

RX1 = {"x": 0.0, "y": 0.0, "min_angle": 30, "max_angle": 60}
RX2 = {"x": 10.0, "y": 0.0, "min_angle": 100, "max_angle": 140}


# --- Ray / line helpers ------------------------------------------------------

def intersect_rays(rx1, ry1, a1_deg, rx2, ry2, a2_deg):
    """
    Find the intersection point of two rays.

    Each ray is defined by a starting point and an angle:
        Ray 1: starts at (rx1, ry1), goes in direction a1_deg
        Ray 2: starts at (rx2, ry2), goes in direction a2_deg

    Mathematically we want to solve:
        (rx1, ry1) + t * (cos a1, sin a1) = (rx2, ry2) + s * (cos a2, sin a2)

    This gives two equations (one for x, one for y) with two unknowns
    (t and s). We solve using Cramer's rule.

    Parameters
    ----------
    rx1, ry1 : float
        Starting position of ray 1 (meters).
    a1_deg : float
        Direction of ray 1 (degrees, CCW from East).
    rx2, ry2 : float
        Starting position of ray 2 (meters).
    a2_deg : float
        Direction of ray 2 (degrees, CCW from East).

    Returns
    -------
    (x, y, t, s) : tuple of float
        x, y  -- the intersection point in meters
        t     -- distance along ray 1 to the intersection
        s     -- distance along ray 2 to the intersection
    None
        If the rays are parallel (det ~ 0) or the intersection is
        behind one of the starting points (t < 0 or s < 0).
    """
    # Convert angles to unit direction vectors.
    # cos/sin give the x/y components of a unit vector pointing at that angle.
    d1x, d1y = np.cos(np.radians(a1_deg)), np.sin(np.radians(a1_deg))
    d2x, d2y = np.cos(np.radians(a2_deg)), np.sin(np.radians(a2_deg))

    # The gap between the two ray starting points.
    dx = rx2 - rx1
    dy = ry2 - ry1

    # We need to solve this 2x2 system (rearranged from the ray equation):
    #
    #   | d1x  -d2x | | t |   | dx |
    #   | d1y  -d2y | | s | = | dy |
    #
    # The determinant tells us if the rays are parallel.
    # If det = 0, the direction vectors are aligned -> no unique intersection.
    det = d1x * (-d2y) - (-d2x) * d1y
    if abs(det) < 1e-12:
        return None

    # Cramer's rule: replace one column at a time with the right-hand side
    # and divide by the determinant.
    #
    # For t: replace column 1 (the d1 column) with [dx, dy]:
    #   t = det(| dx  -d2x |) / det = (dx*(-d2y) - (-d2x)*dy) / det
    #          (| dy  -d2y |)
    #
    # For s: replace column 2 (the -d2 column) with [dx, dy]:
    #   s = det(| d1x  dx |) / det = (d1x*dy - d1y*dx) / det
    #          (| d1y  dy |)
    t = (dx * (-d2y) - (-d2x) * dy) / det
    s = (d1x * dy - d1y * dx) / det

    # t and s must be non-negative: a negative value means the intersection
    # is behind the receiver (opposite direction of the ray), which is
    # physically meaningless -- the signal comes FROM the TX, not behind.
    # The small tolerance (-1e-9) handles floating point noise at t=0.
    if t < -1e-9 or s < -1e-9:
        return None

    # Plug t back into ray 1's equation to get the intersection point.
    x = rx1 + t * d1x
    y = ry1 + t * d1y
    return (x, y, t, s)


def infer_tx(rx1, rx2):
    """
    Estimate the most likely transmitter position.

    Strategy: each receiver's best guess of direction is the CENTER
    of its angular wedge (the bisector). If the TX is equally likely
    to be anywhere in the wedge, the middle is the best single guess.
    The point where both center rays cross is the position both
    receivers agree on most.

    When the wedges are built symmetrically around the true TX angle
    (i.e., the TX is exactly in the middle of both wedges), this
    function returns the exact TX position.

    Parameters
    ----------
    rx1, rx2 : dict
        Receiver dicts with keys: x, y, min_angle, max_angle

    Returns
    -------
    (x, y) : tuple of float
        Estimated TX position in meters.
    None
        If the center rays are parallel (no intersection).
    """
    # Bisect each wedge to get the center angle.
    center1 = (rx1["min_angle"] + rx1["max_angle"]) / 2.0
    center2 = (rx2["min_angle"] + rx2["max_angle"]) / 2.0

    # Intersect the two center rays -- same math as boundary rays.
    result = intersect_rays(rx1["x"], rx1["y"], center1,
                            rx2["x"], rx2["y"], center2)
    if result is None:
        return None
    return (result[0], result[1])


def shoelace_area(vertices):
    """
    Compute the exact area of a polygon using the Shoelace formula.

    The formula works by summing cross products of consecutive vertex
    pairs. For vertices [(x0,y0), (x1,y1), ...]:

        area = 0.5 * |sum of (xi * y_{i+1} - x_{i+1} * yi)|

    The vertices must be ordered (CW or CCW) for correct results.
    The abs() ensures the result is positive regardless of winding.

    Parameters
    ----------
    vertices : list of (float, float)
        Ordered polygon vertices.

    Returns
    -------
    float
        Area in square meters (m^2).
    """
    n = len(vertices)
    area = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]   # wraps around: last -> first
        area += x1 * y2 - x2 * y1        # cross product of edge vectors
    return abs(area) / 2.0


def order_polygon(points):
    """
    Sort polygon vertices counter-clockwise around their centroid.

    This is needed because intersect_rays returns vertices in arbitrary
    order (depends on which ray pair was tested first). The Shoelace
    formula requires ordered vertices, so we sort by the angle from
    the centroid to each vertex using atan2.

    Parameters
    ----------
    points : list of (float, float)
        Unordered polygon vertices.

    Returns
    -------
    list of (float, float)
        Same vertices, sorted counter-clockwise.
    """
    cx = np.mean([p[0] for p in points])
    cy = np.mean([p[1] for p in points])
    return sorted(points, key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))


# --- Main computation -------------------------------------------------------

def compute_intersection(rx1, rx2):
    """
    Compute the overlap region of two receiver wedges.

    This is the core function. It takes two receivers and:
    1. Pairs each RX1 boundary ray with each RX2 boundary ray (4 pairs).
    2. Intersects each pair to find polygon vertices.
    3. Orders the vertices and computes the area.
    4. Prints the results and the inequality system defining the region.

    The overlap polygon typically has 4 vertices (a quadrilateral) when
    all 4 ray pairs intersect, or 3 vertices (a triangle) when one pair
    is parallel (e.g., both receivers have the same angle).

    Parameters
    ----------
    rx1, rx2 : dict
        Receiver dicts with keys: x, y, min_angle, max_angle

    Returns
    -------
    (area, vertices) : (float, list of (float, float))
        area     -- polygon area in m^2
        vertices -- ordered list of polygon corner points
    (None, [])
        If fewer than 3 intersections found (no bounded region).
    """
    # The 2 boundary angles from each receiver.
    rays_rx1 = [rx1["min_angle"], rx1["max_angle"]]
    rays_rx2 = [rx2["min_angle"], rx2["max_angle"]]

    # Try all 4 combinations: each RX1 ray x each RX2 ray.
    # Valid intersections (forward on both rays) become polygon vertices.
    vertices = []
    print("PAIRWISE RAY INTERSECTIONS")
    print("-" * 65)
    for a1 in rays_rx1:
        for a2 in rays_rx2:
            result = intersect_rays(rx1["x"], rx1["y"], a1,
                                    rx2["x"], rx2["y"], a2)
            tag = f"RX1@{a1} deg  x  RX2@{a2} deg"
            if result is None:
                print(f"  {tag} : no intersection (parallel or behind)")
                continue
            px, py, t, s = result
            print(f"  {tag} : ({px:.6f}, {py:.6f})  t={t:.4f} s={s:.4f}")
            vertices.append((px, py))

    # Need at least 3 points to form a polygon (area > 0).
    if len(vertices) < 3:
        print("\nFewer than 3 vertices -- no bounded overlap region.")
        return None, []

    # Sort vertices CCW so the Shoelace formula works correctly.
    vertices = order_polygon(vertices)
    area = shoelace_area(vertices)

    print(f"\nORDERED VERTICES ({len(vertices)}):")
    for i, (vx, vy) in enumerate(vertices):
        print(f"  V{i}: ({vx:.6f}, {vy:.6f})")

    print(f"\n  AREA  (Shoelace, exact) = {area:.6f} m^2")
    cx = np.mean([v[0] for v in vertices])
    cy = np.mean([v[1] for v in vertices])
    print(f"  CENTROID               = ({cx:.6f}, {cy:.6f})")

    # Print the analytical definition of the region as inequalities.
    # A point (x, y) is inside a wedge if it is:
    #   - to the LEFT of the min-angle ray  (cross product >= 0)
    #   - to the RIGHT of the max-angle ray (cross product <= 0)
    #
    # The cross product of direction vector d = (cos t, sin t) with
    # the vector from receiver R to point P = (x-rx, y-ry) is:
    #   cross = cos(t) * (y - ry) - sin(t) * (x - rx)
    #
    # So the two conditions per receiver are:
    #   cos(min_angle) * (y-ry) - sin(min_angle) * (x-rx) >= 0
    #   cos(max_angle) * (y-ry) - sin(max_angle) * (x-rx) <= 0
    #
    # The TX must satisfy all 4 inequalities (2 per receiver).
    print("\n" + "=" * 65)
    print("  TRANSMITTER REGION  (system of inequalities)")
    print("=" * 65)
    print("  The transmitter (x, y) satisfies ALL of:\n")
    for rx, name in [(rx1, "RX1"), (rx2, "RX2")]:
        t_min = np.radians(rx["min_angle"])
        t_max = np.radians(rx["max_angle"])
        print(f"  {name} at ({rx['x']}, {rx['y']}), "
              f"wedge [{rx['min_angle']} deg, {rx['max_angle']} deg]:")
        print(f"    cos({rx['min_angle']} deg)*(y-{rx['y']}) "
              f"- sin({rx['min_angle']} deg)*(x-{rx['x']}) >= 0")
        print(f"    cos({rx['max_angle']} deg)*(y-{rx['y']}) "
              f"- sin({rx['max_angle']} deg)*(x-{rx['x']}) <= 0")
        print()

    return area, vertices


# --- Plot --------------------------------------------------------------------

def plot_result(rx1, rx2, vertices):
    """
    Draw a static plot showing both wedges, the overlap polygon,
    boundary rays with their equations, and the most likely TX point.

    Parameters
    ----------
    rx1, rx2 : dict
        Receiver dicts.
    vertices : list of (float, float)
        Ordered overlap polygon vertices from compute_intersection().
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # --- Auto-zoom: find bounds from all points with some margin ---
    all_x = [v[0] for v in vertices] + [rx1["x"], rx2["x"]]
    all_y = [v[1] for v in vertices] + [rx1["y"], rx2["y"]]
    margin_x = (max(all_x) - min(all_x)) * 0.4 + 1
    margin_y = (max(all_y) - min(all_y)) * 0.4 + 1
    xlim = (min(all_x) - margin_x, max(all_x) + margin_x)
    ylim = (min(all_y) - margin_y, max(all_y) + margin_y)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # ray_len: how long to draw the visual rays. Set large enough to
    # extend well past the plot edges. This is only for DRAWING --
    # the actual math uses infinite rays (no length limit).
    ray_len = max(xlim[1] - xlim[0], ylim[1] - ylim[0]) * 1.5

    # --- Shade each receiver's wedge as a light-colored fan ---
    # We draw an arc of 100 points between min_angle and max_angle,
    # connect them back to the receiver, and fill the resulting polygon.
    colors = {"RX1": "steelblue", "RX2": "darkorange"}
    for rx, name in [(rx1, "RX1"), (rx2, "RX2")]:
        angles = np.linspace(np.radians(rx["min_angle"]),
                             np.radians(rx["max_angle"]), 100)
        fan_x = [rx["x"]] + [rx["x"] + ray_len * np.cos(a) for a in angles] + [rx["x"]]
        fan_y = [rx["y"]] + [rx["y"] + ray_len * np.sin(a) for a in angles] + [rx["y"]]
        ax.fill(fan_x, fan_y, color=colors[name], alpha=0.07,
                label=f"{name} wedge [{rx['min_angle']} deg - {rx['max_angle']} deg]")

    # --- Draw the 4 boundary rays as dashed lines ---
    # Each ray also gets a label showing its implicit line equation:
    #   sin(t)*x - cos(t)*y = sin(t)*rx - cos(t)*ry
    # which comes from the cross product being zero on the line.
    for rx, name in [(rx1, "RX1"), (rx2, "RX2")]:
        for angle_deg in [rx["min_angle"], rx["max_angle"]]:
            theta = np.radians(angle_deg)
            ex = rx["x"] + ray_len * np.cos(theta)
            ey = rx["y"] + ray_len * np.sin(theta)
            ax.plot([rx["x"], ex], [rx["y"], ey],
                    color=colors[name], linewidth=1.4, linestyle="--", alpha=0.65)

            # Place the equation label 3.5 m along the ray, rotated to
            # align with the ray direction so it reads naturally.
            ld = 3.5
            lx = rx["x"] + ld * np.cos(theta)
            ly = rx["y"] + ld * np.sin(theta)
            a_coef = np.sin(theta)       # coefficient of x
            b_coef = -np.cos(theta)      # coefficient of y
            c_coef = a_coef * rx["x"] + b_coef * rx["y"]  # constant
            eq_str = f"{a_coef:.3f}x + {b_coef:.3f}y = {c_coef:.3f}"
            rot = np.degrees(theta)
            if rot > 90:
                rot -= 180  # keep text right-side-up
            ax.annotate(eq_str, (lx, ly), fontsize=7.5, color=colors[name],
                        fontweight="bold", rotation=rot, rotation_mode="anchor",
                        ha="center", va="bottom")

    # --- Draw the overlap polygon (red shaded area) ---
    if vertices:
        area = shoelace_area(vertices)
        # Close the polygon by appending the first vertex at the end.
        poly_x = [v[0] for v in vertices] + [vertices[0][0]]
        poly_y = [v[1] for v in vertices] + [vertices[0][1]]
        ax.fill(poly_x, poly_y, color="red", alpha=0.30,
                label=f"TX region (area = {area:.4f} m^2)")
        ax.plot(poly_x, poly_y, color="red", linewidth=2.2)

        # Label each vertex with its index and coordinates.
        for i, (vx, vy) in enumerate(vertices):
            ax.plot(vx, vy, "ro", markersize=7, zorder=5)
            ax.annotate(f"V{i} ({vx:.2f}, {vy:.2f})",
                        (vx, vy), textcoords="offset points",
                        xytext=(8, 6), fontsize=8, color="darkred")

        # --- Most likely TX: intersection of center rays ---
        # Drawn as solid lines (vs dashed for boundaries) so you can
        # visually see the bisectors and where they cross.
        est = infer_tx(rx1, rx2)
        if est:
            c1 = (rx1["min_angle"] + rx1["max_angle"]) / 2.0
            c2 = (rx2["min_angle"] + rx2["max_angle"]) / 2.0
            for rx, ang, name in [(rx1, c1, "RX1"), (rx2, c2, "RX2")]:
                theta = np.radians(ang)
                ax.plot([rx["x"], rx["x"] + ray_len * np.cos(theta)],
                        [rx["y"], rx["y"] + ray_len * np.sin(theta)],
                        color=colors[name], linewidth=1.8, linestyle="-", alpha=0.5,
                        zorder=3)

            ax.plot(est[0], est[1], "k*", markersize=16, zorder=7,
                    label=f"Most likely TX ({est[0]:.2f}, {est[1]:.2f})")

    # --- Draw receiver positions as squares ---
    for rx, name, col in [(rx1, "RX1", "steelblue"), (rx2, "RX2", "darkorange")]:
        ax.plot(rx["x"], rx["y"], "s", color=col, markersize=12, zorder=5)
        ax.annotate(name, (rx["x"], rx["y"]), textcoords="offset points",
                    xytext=(10, -14), fontsize=12, fontweight="bold", color=col)

    ax.set_aspect("equal")
    ax.set_xlabel("X (m)", fontsize=11)
    ax.set_ylabel("Y (m)", fontsize=11)
    ax.set_title("Transmitter Geolocation -- Analytical Ray Equations", fontsize=13)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("geolocation_plot.png", dpi=150)
    print("\nPlot saved.")


# --- Run ---------------------------------------------------------------------

if __name__ == "__main__":
    area, vertices = compute_intersection(RX1, RX2)
    if vertices:
        plot_result(RX1, RX2, vertices)
