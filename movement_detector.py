"""
movement_detector.py - Detect human movement from WiFi signal variance.
Reads recent RSSI samples from data.csv and monitors for fluctuations.

Physical basis: Human bodies absorb/reflect 2.4/5 GHz waves. Movement
causes RSSI to fluctuate — high variance → likely movement detected.

Usage: python3 movement_detector.py
Deps:  numpy
"""

import csv, sys, time, os
import numpy as np

CSV_FILE           = "data.csv"
SAMPLE_WINDOW      = 10     # last N readings to analyse
VARIANCE_THRESHOLD = 15.0   # dBm² — raise to reduce sensitivity
POLL_INTERVAL      = 3      # seconds between checks


def load_recent_signals(path, n=SAMPLE_WINDOW):
    """Read the last N RSSI values from data.csv. Returns list of floats."""
    if not os.path.exists(path):
        print(f"[ERROR] {path} not found. Run scanner.py first."); sys.exit(1)
    sigs = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                sigs.append(float(row["signal"]))
            except (ValueError, KeyError):
                continue
    return sigs[-n:]


def detect_movement(signals, threshold=VARIANCE_THRESHOLD):
    """
    Compute population variance of recent RSSI samples.
    High variance = signal instability = possible movement.
    Returns (variance: float, movement_detected: bool).
    """
    if len(signals) < 2:
        return 0.0, False
    var = float(np.var(np.array(signals, dtype=float)))
    return var, var > threshold


def print_status(variance, movement, n):
    """Print a compact status bar with variance and detection result."""
    filled = min(int((variance / (VARIANCE_THRESHOLD * 2)) * 20), 20)
    bar    = "█" * filled + "░" * (20 - filled)
    status = "⚠  MOVEMENT DETECTED" if movement else "✔  ROOM STABLE"
    print(f"[{bar}] Var: {variance:6.2f} dBm²  Samples: {n:>2}  |  {status}")


def main():
    print("=== WiFi Signal Mapper — Movement Detector ===")
    print(f"File: {CSV_FILE} | Window: {SAMPLE_WINDOW} | Threshold: {VARIANCE_THRESHOLD} dBm²")
    print(f"Polling every {POLL_INTERVAL}s. Press Ctrl+C to stop.\n")
    try:
        while True:
            sigs = load_recent_signals(CSV_FILE, SAMPLE_WINDOW)
            if len(sigs) < 2:
                print("[WAIT] Need at least 2 samples in data.csv.")
            else:
                var, moved = detect_movement(sigs)
                print_status(var, moved, len(sigs))
                print("       >>> MOVEMENT DETECTED <<<" if moved else "           ROOM STABLE")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[INFO] Detector stopped.")

if __name__ == "__main__":
    main()
