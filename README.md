# 📶 wifi-signal-mapper

A lightweight terminal-based Python tool for mapping indoor WiFi signal strength (RSSI), generating visual heatmaps, and detecting potential human movement from signal disturbances.

Designed for low-end Ubuntu laptops — no heavy frameworks, no GUI, minimal dependencies.

---

## Project Structure

```
wifi-signal-mapper/
├── scanner.py           # Collect WiFi RSSI → data.csv
├── heatmap.py           # Generate wifi_heatmap.png from data.csv
├── movement_detector.py # Detect movement via signal variance
├── data.csv             # Collected readings (auto-created by scanner.py)
├── locations.json       # Room coordinate map for location labels
└── README.md            # This file
```

---

## Requirements

**OS:** Linux (Ubuntu recommended)  
**Python:** 3.7+  
**System package:** `wireless-tools` (provides `iwconfig`)

```bash
sudo apt install wireless-tools
```

**Python packages:**

```bash
pip install numpy matplotlib scipy
```

> `scipy` is optional — if not installed, `heatmap.py` automatically falls back to a numpy-based Inverse Distance Weighting (IDW) interpolation.

---

## Setup

### 1. Define Room Locations

Edit [`locations.json`](locations.json) to map location labels to physical (x, y) coordinates in your room (units: meters):

```json
{
    "A": [0, 0],
    "B": [2, 0],
    "C": [4, 0],
    "D": [0, 2],
    "E": [2, 2],
    "F": [4, 2]
}
```

Place yourself at each labeled spot when scanning.

---

## Usage

### Step 1 — Scan WiFi Signal

```bash
python3 scanner.py
```

- Prompts for a location label (e.g. `A`)
- Runs `iwconfig`, extracts RSSI, applies 5-sample moving average
- Appends readings to `data.csv` every 3 seconds
- Press **Ctrl+C** to stop

**CSV format:**
```
timestamp,location,signal
12:21:03,A,-42
12:21:06,A,-43
```

Move to each room position and restart the scanner with the corresponding label.

---

### Step 2 — Generate Heatmap

```bash
python3 heatmap.py
```

- Reads `data.csv` and `locations.json`
- Interpolates signal across a 2D grid
- Saves **`wifi_heatmap.png`** in the current directory

**Color scale:**  
🔴 Red = strong signal | 🔵 Blue = weak signal

---

### Step 3 — Detect Movement

```bash
python3 movement_detector.py
```

- Reads the last 10 RSSI samples from `data.csv` every 3 seconds
- Computes signal **variance**
- Prints status to terminal:

```
[████████████░░░░░░░░] Variance:  18.40 dBm²  |  Samples: 10  |  ⚠  MOVEMENT DETECTED
       >>> MOVEMENT DETECTED <<<

[░░░░░░░░░░░░░░░░░░░░] Variance:   2.10 dBm²  |  Samples: 10  |  ✔  ROOM STABLE
           ROOM STABLE
```

> **How it works:** Human bodies absorb and reflect 2.4/5 GHz radio waves. Movement in the signal path causes fluctuation. Variance > 15 dBm² triggers the alert (adjustable in [`movement_detector.py`](movement_detector.py#L22)).

---

## Configuration

| Parameter | File | Default | Description |
|---|---|---|---|
| `SCAN_INTERVAL` | `scanner.py` | `3` s | Time between scans |
| `MOVING_AVG_WINDOW` | `scanner.py` | `5` | Smoothing window size |
| `SAMPLE_WINDOW` | `movement_detector.py` | `10` | Samples for variance |
| `VARIANCE_THRESHOLD` | `movement_detector.py` | `15.0` | Movement detection sensitivity |
| `GRID_RESOLUTION` | `heatmap.py` | `200` | Heatmap pixel density |

---

## Example Output

After scanning all 6 positions (A–F), run `python3 heatmap.py` to produce:

```
=== WiFi Signal Mapper — Heatmap Generator ===
[INFO] Loaded 6 locations from data.csv
[INFO] Locations used: ['A', 'B', 'C', 'D', 'E', 'F']
[INFO] Heatmap saved to: wifi_heatmap.png
```

The image shows the room grid with colour-coded signal intensity and labeled measurement points.

---

## Troubleshooting

**`iwconfig` not found:**  
```bash
sudo apt install wireless-tools
```

**No Signal level in iwconfig output:**  
Ensure your WiFi interface is connected. Run `iwconfig` manually to verify output format.

**`scipy` not installed:**  
`heatmap.py` will use numpy IDW fallback automatically — no action needed.

**Permission denied on iwconfig:**  
Try running with `sudo python3 scanner.py` or check interface permissions.

---

## Technical Notes

- **Moving Average Filter** — reduces RSSI noise from transient interference by averaging the last N samples before saving.
- **Signal Interpolation** — fills the gaps between discrete measurement points using cubic interpolation (scipy) or IDW (numpy). This simulates a continuous signal map across the room.
- **Variance-Based Detection** — a low-cost statistical method requiring no machine learning. Population variance of recent RSSI values detects instability caused by physical obstruction.
- **Headless rendering** — matplotlib uses the `Agg` backend so no display server is required.

---

## License

MIT — free to use and modify.
