# -*- coding: ascii -*-
"""
Geolocation Dashboard

A live-updating matplotlib window that redraws the geolocation plot
every time new receiver data arrives. Designed to be driven from a
server or data pipeline via the update() method.

Architecture
------------
    +----------+      update(rx1, rx2)      +---------------------+
    |  Server  | -------------------------> | GeolocationDashboard |
    | (your    |   called each time new     | (matplotlib window)  |
    |  code)   |   angles are measured      |                      |
    +----------+                            +---------------------+

The dashboard:
  - Keeps a persistent matplotlib figure open.
  - On each update(), recomputes the intersection and redraws.
  - Stores a history of past TX estimates to show a trail.
  - Has a LIVE/PAUSED button to temporarily block updates.

Usage
-----
    from dashboard import GeolocationDashboard

    dash = GeolocationDashboard()

    # Every time your server gets new angle data:
    dash.update(rx1, rx2)       # first reading
    dash.update(rx1, rx2)       # new reading -> redraws everything
    dash.update(rx1, rx2)       # ...

    # Optional:
    dash.save("snapshot.png")   # save current view to file
    dash.clear_history()        # reset the TX estimate trail
    dash.close()                # close the window

Data format
-----------
Each receiver is a dict:
    {"x": float, "y": float, "min_angle": float, "max_angle": float}

    x, y       -- receiver position in meters
    min_angle  -- left edge of the angular wedge (degrees, CCW from East)
    max_angle  -- right edge of the angular wedge (degrees, CCW from East)
"""

import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # interactive backend -- change to "Qt5Agg" if needed
import matplotlib.pyplot as plt

from geolocation import (
    compute_intersection, infer_tx
)


class GeolocationDashboard:
    """
    Persistent dashboard that redraws on each update() call.

    The figure stays open between updates. Each call to update()
    clears the plot and redraws everything from scratch with the
    new data. This is simpler and more reliable than trying to
    move individual plot elements.

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The dashboard figure.
    ax : matplotlib.axes.Axes
        The main plot axes.
    """

    def __init__(self, figsize=(11, 9)):
        """
        Create the dashboard window.

        Parameters
        ----------
        figsize : tuple of (float, float)
            Width and height of the window in inches.
        """
        # plt.ion() enables interactive mode: the window stays open
        # and responsive while the Python program continues running.
        # Without this, plt.show() would block until the window is closed.
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Shrink the plot area to make room for the button at the bottom.
        self.fig.subplots_adjust(bottom=0.12)
        self.fig.canvas.manager.set_window_title("Geolocation Dashboard")

        self._colors = {"RX1": "steelblue", "RX2": "darkorange"}
        self._history = []    # list of (x, y) past TX estimates
        self._paused = False  # when True, update() does nothing
        self._dropped = 0     # how many updates were ignored while paused

        # --- Create the LIVE/PAUSED toggle button ---
        # fig.add_axes([left, bottom, width, height]) in figure coordinates
        # (0,0 = bottom-left, 1,1 = top-right).
        from matplotlib.widgets import Button
        self._btn_ax = self.fig.add_axes([0.42, 0.02, 0.16, 0.05])
        self._btn = Button(self._btn_ax, "LIVE", color="lightgreen",
                           hovercolor="palegreen")
        # Connect the button click to our toggle handler.
        self._btn.on_clicked(self._toggle_pause)
        self._status_text = None  # the text object shown above the button

        # Show the window and do an initial draw.
        plt.show(block=False)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # --- Pause/resume logic --------------------------------------------------

    def _toggle_pause(self, event):
        """
        Called when the LIVE/PAUSED button is clicked.

        Flips the paused state and updates the button appearance:
        - LIVE (green):   updates are processed normally
        - PAUSED (red):   updates are silently dropped and counted

        Parameters
        ----------
        event : matplotlib.backend_bases.Event
            The click event (unused, but required by matplotlib).
        """
        self._paused = not self._paused
        if self._paused:
            # Switch to paused appearance.
            self._btn.label.set_text("PAUSED")
            self._btn_ax.set_facecolor("salmon")
            self._btn.color = "salmon"
            self._btn.hovercolor = "lightsalmon"
            self._dropped = 0  # reset counter for this pause session
        else:
            # Switch back to live appearance.
            self._btn.label.set_text("LIVE")
            self._btn_ax.set_facecolor("lightgreen")
            self._btn.color = "lightgreen"
            self._btn.hovercolor = "palegreen"
            self._dropped = 0
        self._update_status_text()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _update_status_text(self):
        """
        Show or refresh the status message above the button.

        Displays either:
        - "Receiving updates" (green)  when live
        - "Updates blocked (N dropped)" (red)  when paused
        """
        # Remove the old text before creating a new one, otherwise
        # they stack on top of each other.
        if self._status_text:
            self._status_text.remove()
        if self._paused:
            msg = f"Updates blocked ({self._dropped} dropped)"
            color = "red"
        else:
            msg = "Receiving updates"
            color = "green"
        # fig.text() places text in figure coordinates (not data coordinates),
        # so it stays fixed regardless of axis zoom/pan.
        self._status_text = self.fig.text(
            0.50, 0.08, msg, ha="center", fontsize=10,
            color=color, fontweight="bold")

    # --- Main update entry point ---------------------------------------------

    def update(self, rx1, rx2):
        """
        Receive new RX1/RX2 data and redraw the dashboard.

        This is the main method your server should call. It:
        1. Checks if paused -- if so, increments drop counter and returns.
        2. Computes the intersection polygon and area.
        3. Estimates the most likely TX position.
        4. Appends the estimate to history.
        5. Redraws the entire plot.

        Parameters
        ----------
        rx1 : dict
            First receiver: {"x": float, "y": float,
                             "min_angle": float, "max_angle": float}
        rx2 : dict
            Second receiver: same format as rx1.
        """
        # If paused, just count the dropped update and refresh the
        # status text to show the new count.
        if self._paused:
            self._dropped += 1
            self._update_status_text()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            return

        # Run the core geolocation computation.
        area, vertices = compute_intersection(rx1, rx2)
        est = infer_tx(rx1, rx2)

        # Save the estimate for the history trail.
        if est:
            self._history.append(est)

        # Redraw everything with the new data.
        self._draw(rx1, rx2, vertices, area, est)
        self._update_status_text()

    # --- Drawing -------------------------------------------------------------

    def _draw(self, rx1, rx2, vertices, area, est):
        """
        Clear the plot and redraw all visual elements.

        We redraw from scratch each time rather than trying to
        update individual elements. This is simpler and avoids
        issues with stale plot objects.

        Parameters
        ----------
        rx1, rx2 : dict
            Receiver dicts (for positions and angles).
        vertices : list of (float, float)
            Ordered overlap polygon vertices.
        area : float or None
            Polygon area in m^2.
        est : (float, float) or None
            Estimated TX position.
        """
        ax = self.ax
        ax.clear()  # wipe everything from the previous frame

        # --- Auto-zoom: compute bounds from all relevant points ---
        points_x = [rx1["x"], rx2["x"]]
        points_y = [rx1["y"], rx2["y"]]
        if vertices:
            points_x += [v[0] for v in vertices]
            points_y += [v[1] for v in vertices]
        if est:
            points_x.append(est[0])
            points_y.append(est[1])

        margin_x = (max(points_x) - min(points_x)) * 0.4 + 2
        margin_y = (max(points_y) - min(points_y)) * 0.4 + 2
        xlim = (min(points_x) - margin_x, max(points_x) + margin_x)
        ylim = (min(points_y) - margin_y, max(points_y) + margin_y)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        # ray_len for visual drawing only (not used in computation).
        ray_len = max(xlim[1] - xlim[0], ylim[1] - ylim[0]) * 1.5

        # --- Wedge shading ---
        # Draw a filled fan shape for each receiver's angular range.
        # This is the region where the TX could be according to that
        # single receiver alone.
        for rx, name in [(rx1, "RX1"), (rx2, "RX2")]:
            angles = np.linspace(np.radians(rx["min_angle"]),
                                 np.radians(rx["max_angle"]), 100)
            # Build a polygon: receiver -> arc along the wedge -> back to receiver.
            fan_x = [rx["x"]] + [rx["x"] + ray_len * np.cos(a) for a in angles] + [rx["x"]]
            fan_y = [rx["y"]] + [rx["y"] + ray_len * np.sin(a) for a in angles] + [rx["y"]]
            ax.fill(fan_x, fan_y, color=self._colors[name], alpha=0.07,
                    label=f"{name} [{rx['min_angle']:.1f} deg - {rx['max_angle']:.1f} deg]")

        # --- Boundary rays (dashed) with equation labels ---
        # Each receiver has 2 boundary rays (min_angle and max_angle).
        # We draw them as dashed lines and label each with its
        # implicit line equation: a*x + b*y = c
        for rx, name in [(rx1, "RX1"), (rx2, "RX2")]:
            for angle_deg in [rx["min_angle"], rx["max_angle"]]:
                theta = np.radians(angle_deg)
                ex = rx["x"] + ray_len * np.cos(theta)
                ey = rx["y"] + ray_len * np.sin(theta)
                ax.plot([rx["x"], ex], [rx["y"], ey],
                        color=self._colors[name], linewidth=1.4,
                        linestyle="--", alpha=0.65)

                # Place the equation label along the ray.
                ld = 3.5  # distance from receiver to place the label
                lx = rx["x"] + ld * np.cos(theta)
                ly = rx["y"] + ld * np.sin(theta)
                # Compute the implicit line coefficients:
                # sin(t)*(x-rx) - cos(t)*(y-ry) = 0
                # -> sin(t)*x - cos(t)*y = sin(t)*rx - cos(t)*ry
                a_coef = np.sin(theta)
                b_coef = -np.cos(theta)
                c_coef = a_coef * rx["x"] + b_coef * rx["y"]
                eq_str = f"{a_coef:.3f}x + {b_coef:.3f}y = {c_coef:.3f}"
                # Rotate the label to align with the ray direction.
                rot = np.degrees(theta)
                if rot > 90:
                    rot -= 180  # keep text right-side-up
                ax.annotate(eq_str, (lx, ly), fontsize=7.5,
                            color=self._colors[name], fontweight="bold",
                            rotation=rot, rotation_mode="anchor",
                            ha="center", va="bottom")

        # --- Intersection polygon (the red TX region) ---
        # This is where BOTH receivers agree the TX could be.
        if vertices:
            poly_x = [v[0] for v in vertices] + [vertices[0][0]]
            poly_y = [v[1] for v in vertices] + [vertices[0][1]]
            ax.fill(poly_x, poly_y, color="red", alpha=0.25,
                    label=f"TX region (area = {area:.4f} m^2)")
            ax.plot(poly_x, poly_y, color="red", linewidth=2.2)

            # Label each vertex.
            for i, (vx, vy) in enumerate(vertices):
                ax.plot(vx, vy, "ro", markersize=7, zorder=5)
                ax.annotate(f"V{i} ({vx:.2f}, {vy:.2f})",
                            (vx, vy), textcoords="offset points",
                            xytext=(8, 6), fontsize=8, color="darkred")

        # --- Center rays (solid) and most likely TX (star) ---
        # The center rays bisect each wedge. Their intersection is the
        # best single-point estimate of where the TX is.
        # Drawn as solid lines to distinguish from the dashed boundaries.
        if est:
            c1 = (rx1["min_angle"] + rx1["max_angle"]) / 2.0
            c2 = (rx2["min_angle"] + rx2["max_angle"]) / 2.0
            for rx, ang, name in [(rx1, c1, "RX1"), (rx2, c2, "RX2")]:
                theta = np.radians(ang)
                ax.plot([rx["x"], rx["x"] + ray_len * np.cos(theta)],
                        [rx["y"], rx["y"] + ray_len * np.sin(theta)],
                        color=self._colors[name], linewidth=1.8,
                        linestyle="-", alpha=0.5, zorder=3)

            ax.plot(est[0], est[1], "k*", markersize=16, zorder=7,
                    label=f"Most likely TX ({est[0]:.2f}, {est[1]:.2f})")

        # --- Past estimates trail ---
        # Shows how the TX estimate has moved over successive readings.
        # Useful for seeing if the TX is moving or if the estimate is
        # converging as measurements improve.
        if len(self._history) > 1:
            hx = [p[0] for p in self._history]
            hy = [p[1] for p in self._history]
            ax.plot(hx, hy, "k.-", alpha=0.3, markersize=4, linewidth=0.8,
                    label=f"History ({len(self._history)} readings)")

        # --- Receiver positions (squares) ---
        for rx, name, col in [(rx1, "RX1", "steelblue"), (rx2, "RX2", "darkorange")]:
            ax.plot(rx["x"], rx["y"], "s", color=col, markersize=12, zorder=6)
            ax.annotate(name, (rx["x"], rx["y"]), textcoords="offset points",
                        xytext=(10, -14), fontsize=12, fontweight="bold", color=col)

        # --- Info box (top-left corner) ---
        # Shows reading count, area, and current TX estimate at a glance.
        info_lines = [f"Readings: {len(self._history)}"]
        if area is not None:
            info_lines.append(f"Area: {area:.4f} m^2")
        if est:
            info_lines.append(f"TX est: ({est[0]:.2f}, {est[1]:.2f})")
        info_text = "\n".join(info_lines)
        # transform=ax.transAxes makes coordinates relative to the axes
        # (0,0 = bottom-left, 1,1 = top-right) instead of data coordinates.
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                fontsize=9, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="wheat", alpha=0.8))

        # --- Axis labels and formatting ---
        ax.set_aspect("equal")   # 1 meter on X = 1 meter on Y visually
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title("Geolocation Dashboard", fontsize=13)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3)

        # Redraw the canvas to show the changes.
        self.fig.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # --- Utility methods -----------------------------------------------------

    def clear_history(self):
        """Reset the TX estimate history trail."""
        self._history = []

    def save(self, path="dashboard.png", dpi=150):
        """
        Save the current dashboard view to an image file.

        Parameters
        ----------
        path : str
            Output file path (e.g., "dashboard.png").
        dpi : int
            Resolution in dots per inch.
        """
        self.fig.savefig(path, dpi=dpi)

    def close(self):
        """Close the dashboard window."""
        plt.close(self.fig)


# --- Demo: simulate a server sending updates ---------------------------------

if __name__ == "__main__":
    import time

    dash = GeolocationDashboard()

    # Simulate 5 readings with slightly changing angles (as if TX is moving).
    # In real use, these would come from your server/hardware.
    readings = [
        ({"x": 0, "y": 0, "min_angle": 30, "max_angle": 60},
         {"x": 10, "y": 0, "min_angle": 100, "max_angle": 140}),

        ({"x": 0, "y": 0, "min_angle": 35, "max_angle": 65},
         {"x": 10, "y": 0, "min_angle": 105, "max_angle": 135}),

        ({"x": 0, "y": 0, "min_angle": 40, "max_angle": 70},
         {"x": 10, "y": 0, "min_angle": 110, "max_angle": 140}),

        ({"x": 0, "y": 0, "min_angle": 38, "max_angle": 62},
         {"x": 10, "y": 0, "min_angle": 108, "max_angle": 132}),

        ({"x": 0, "y": 0, "min_angle": 42, "max_angle": 58},
         {"x": 10, "y": 0, "min_angle": 112, "max_angle": 128}),
    ]

    for i, (rx1, rx2) in enumerate(readings):
        print(f"\n-- Reading {i + 1} --")
        dash.update(rx1, rx2)
        time.sleep(2)  # wait 2 seconds between updates to see the animation

    dash.save("dashboard.png")
    print("\nDone. Close the window to exit.")
    plt.ioff()    # turn off interactive mode
    plt.show()    # block here until the user closes the window
