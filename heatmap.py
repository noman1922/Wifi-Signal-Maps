"""
heatmap.py - Generate a WiFi signal heatmap from data.csv + locations.json.
Output: wifi_heatmap.png  (Red = strong signal, Blue = weak signal)
Usage:  python3 heatmap.py
Deps:   numpy, matplotlib; scipy optional (falls back to numpy IDW if absent)
"""

import csv, json, sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")   # headless — no display required
import matplotlib.pyplot as plt

# Optional scipy: smooth cubic interpolation; numpy IDW used if absent
try:
    from scipy.interpolate import griddata as scipy_griddata
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

CSV_FILE       = "data.csv"
LOCATIONS_FILE = "locations.json"
OUTPUT_FILE    = "wifi_heatmap.png"
GRID_RES       = 200   # interpolation grid resolution (pixels per axis)


def load_locations(path):
    """Load {label: [x,y]} coordinate map from locations.json."""
    if not os.path.exists(path):
        print(f"[ERROR] {path} not found."); sys.exit(1)
    with open(path) as f:
        return json.load(f)


def load_data(path):
    """Read data.csv, return {location: mean_rssi} dict."""
    if not os.path.exists(path):
        print(f"[ERROR] {path} not found. Run scanner.py first."); sys.exit(1)
    sigs = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                sigs.setdefault(row["location"].strip().upper(), []).append(float(row["signal"]))
            except (ValueError, KeyError):
                continue
    if not sigs:
        print("[ERROR] No valid data in data.csv."); sys.exit(1)
    return {loc: np.mean(vals) for loc, vals in sigs.items()}


def idw_interpolate(pts, vals, gx, gy, power=2):
    """
    Inverse Distance Weighting — numpy-only fallback interpolation.
    Each grid cell receives a weighted average of known RSSI values,
    weighted by 1/distance^power so closer points have greater influence.
    """
    out = np.zeros(gx.shape)
    for i in range(gx.shape[0]):
        for j in range(gx.shape[1]):
            d = np.sqrt((pts[:,0]-gx[i,j])**2 + (pts[:,1]-gy[i,j])**2)
            if np.any(d == 0):
                out[i,j] = vals[d==0][0]
            else:
                w = 1.0 / d**power
                out[i,j] = np.dot(w, vals) / w.sum()
    return out


def interpolate_grid(pts, vals, gx, gy):
    """
    Interpolate RSSI values onto a 2D grid.
    Uses scipy cubic (+ linear/nearest fallback) when available;
    otherwise falls back to numpy IDW interpolation.
    """
    if SCIPY_AVAILABLE:
        z = scipy_griddata(pts, vals, (gx, gy), method="cubic")
        if np.any(np.isnan(z)):
            zl = scipy_griddata(pts, vals, (gx, gy), method="linear")
            z  = np.where(np.isnan(z), zl, z)
        if np.any(np.isnan(z)):
            zn = scipy_griddata(pts, vals, (gx, gy), method="nearest")
            z  = np.where(np.isnan(z), zn, z)
        return z
    print("[INFO] scipy unavailable — using numpy IDW interpolation.")
    return idw_interpolate(pts, vals, gx, gy)


def generate_heatmap(sig_data, locations, out_path):
    """Build interpolated heatmap image and save as PNG."""
    # Match labels present in both CSV and locations.json
    labels = [l for l in locations if l in sig_data]
    if not labels:
        print("[ERROR] No matching labels between data.csv and locations.json."); sys.exit(1)

    pts  = np.array([locations[l] for l in labels], dtype=float)
    vals = np.array([sig_data[l]  for l in labels], dtype=float)
    print(f"[INFO] Locations: {labels}")

    # Build grid over room extent with small margin
    m = 0.5
    xi = np.linspace(pts[:,0].min()-m, pts[:,0].max()+m, GRID_RES)
    yi = np.linspace(pts[:,1].min()-m, pts[:,1].max()+m, GRID_RES)
    gx, gy = np.meshgrid(xi, yi)
    gz = interpolate_grid(pts, vals, gx, gy)

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    # RdYlBu_r: blue=weak(low dBm), red=strong(high dBm)
    im = ax.imshow(gz, extent=[xi[0], xi[-1], yi[0], yi[-1]],
                   origin="lower", cmap="RdYlBu_r", aspect="auto",
                   alpha=0.85, interpolation="bilinear")

    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("Signal Strength (dBm)", color="white", fontsize=11)
    plt.setp(cb.ax.yaxis.get_ticklabels(), color="white")

    # Label each measurement point
    for lbl, (x, y), v in zip(labels, pts, vals):
        ax.scatter(x, y, s=80, color="white", zorder=5, edgecolors="black", linewidths=0.8)
        ax.annotate(f"{lbl}\n{v:.0f} dBm", xy=(x,y), xytext=(0,10),
                    textcoords="offset points", ha="center",
                    fontsize=9, color="white", fontweight="bold")

    ax.set_title("Indoor WiFi Signal Map", color="white", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("X Position (m)", color="white", fontsize=10)
    ax.set_ylabel("Y Position (m)", color="white", fontsize=10)
    ax.tick_params(colors="white")
    for sp in ax.spines.values():
        sp.set_edgecolor("white")
    tag = "scipy cubic" if SCIPY_AVAILABLE else "numpy IDW"
    ax.text(0.99, 0.01, f"Interp: {tag}", transform=ax.transAxes,
            fontsize=7, color="gray", ha="right", va="bottom")

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[INFO] Saved: {out_path}")


def main():
    print("=== WiFi Signal Mapper — Heatmap Generator ===")
    locs = load_locations(LOCATIONS_FILE)
    data = load_data(CSV_FILE)
    print(f"[INFO] {len(data)} location(s) loaded from {CSV_FILE}")
    generate_heatmap(data, locs, OUTPUT_FILE)

if __name__ == "__main__":
    main()
