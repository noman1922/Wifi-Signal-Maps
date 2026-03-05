"""
scanner.py - Collect WiFi RSSI using iwconfig, apply moving average, save to data.csv.
Usage: python3 scanner.py
Requires: wireless-tools (sudo apt install wireless-tools)
"""

import subprocess, csv, re, time, sys
from datetime import datetime
from collections import deque

CSV_FILE = "data.csv"
SCAN_INTERVAL = 3        # seconds between scans
MOVING_AVG_WINDOW = 5    # sliding window size for noise reduction


def get_rssi():
    """Run iwconfig and extract Signal level (RSSI) in dBm. Returns int or None."""
    try:
        out = subprocess.check_output(["iwconfig"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
        match = re.search(r"Signal level[=:](-?\d+)", out)
        return int(match.group(1)) if match else None
    except FileNotFoundError:
        print("[ERROR] iwconfig not found. Run: sudo apt install wireless-tools")
        sys.exit(1)
    except subprocess.CalledProcessError:
        return None


def moving_average(buf):
    """Return rounded integer mean of a deque — simple noise smoothing filter."""
    return round(sum(buf) / len(buf)) if buf else None


def init_csv(path):
    """Create CSV with header row if file does not exist yet."""
    try:
        with open(path, "x", newline="") as f:
            csv.writer(f).writerow(["timestamp", "location", "signal"])
    except FileExistsError:
        pass


def save_reading(path, ts, loc, sig):
    """Append one timestamped reading row to data.csv."""
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([ts, loc.upper(), sig])


def get_location_label():
    """Prompt for a single A-Z location label; loop until valid."""
    while True:
        label = input("Enter location label (e.g. A, B, C): ").strip().upper()
        if len(label) == 1 and label.isalpha():
            return label
        print("[WARN] Enter a single letter A-Z.")


def main():
    print("=== WiFi Signal Mapper — Scanner ===")
    print(f"Saving to: {CSV_FILE}  |  Press Ctrl+C to stop\n")
    init_csv(CSV_FILE)
    location = get_location_label()
    buf = deque(maxlen=MOVING_AVG_WINDOW)   # rolling buffer for moving average
    print(f"\nScanning at '{location}' every {SCAN_INTERVAL}s ...\n")
    try:
        while True:
            raw = get_rssi()
            if raw is not None:
                buf.append(raw)
                smoothed = moving_average(buf)
                ts = datetime.now().strftime("%H:%M:%S")
                save_reading(CSV_FILE, ts, location, smoothed)
                print(f"[{ts}] {location} | Raw: {raw} dBm | Smoothed: {smoothed} dBm")
            else:
                print("[WARN] No signal data — skipping scan.")
            time.sleep(SCAN_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[INFO] Stopped. Data saved to {CSV_FILE}.")

if __name__ == "__main__":
    main()
