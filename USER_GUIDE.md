# System User Guide

This guide explains how to operate the **AI-Powered Intelligent Driver Safety & Drowsiness Prevention System**, configure thresholds, register drivers, and export session reports.

---

## 🖥️ Operational Interfaces

The system supports two distinct runtime modes:

### 1. The Streamlit Web Dashboard (GUI Mode)
Optimized for developers, fleet managers, and presentations. It renders video feeds with overlays, graphs telemetry, manages configurations, and shows session history.
* **Launch command**:
  ```bash
  python launcher.py --gui
  ```

### 2. Low-Latency Headless Client (CLI Mode)
Optimized for embedded dashboard modules, car microcomputers, or background execution.
* **Launch command**:
  ```bash
  python launcher.py --cli
  ```

---

## 🧑‍✈️ Driver Verification & Face Registration

The system uses geometric signatures of the driver's face to verify their profile:

### How it works:
1. When you enter a username (e.g. `driver_alpha`) in the dashboard sidebar, the system checks if the face is already registered in `data/registered_faces.json`.
2. **First-time registration**:
   - Start the dashboard with `python launcher.py --gui`.
   - Click the **Start Monitor** button in the sidebar.
   - Look straight at the camera. If the face is not recognized, the system will automatically log the face as `"Unknown"`.
   - To register the face under your profile, run the registration script (or let the system seed it via the SQLite database connection, which automatically registers new user profiles on start).

---

## ⚙️ Calibration & Threshold Adjustments

Drivers have different facial characteristics (resting eye height, blink speeds). The sidebar provides sliders to customize thresholds:

### 1. Eye Aspect Ratio (EAR) Threshold
* **Default**: `0.22`
* **Calibration**: If the system generates false positives (detecting eyes closed while you are looking at the road), decrease the threshold to `0.20` or `0.18`. If it misses eye closures, increase it to `0.24`.

### 2. Mouth Aspect Ratio (MAR) Yawn Threshold
* **Default**: `0.50`
* **Calibration**: If standard talking triggers yawn warnings, increase the MAR threshold to `0.55` or `0.60`. If yawning is not detected, lower it to `0.45`.

### 3. Gaze Distraction Yaw Angle
* **Default**: `15.0` degrees
* **Calibration**: Determines how far you can turn your head left or right before triggering a distraction warning. Set higher (e.g. `20.0`) for wide dashboards, or lower (e.g. `10.0`) for focused setups.

---

## 📂 Accessing Evidence & Violation Logs

When the driver enters **Danger** or **Critical** fatigue states, the system saves screenshots of the face frame:

### Finding the Screenshots:
1. Open the folder: `data/evidence/`
2. Screenshots are named following this template:
   `evidence_session_{session_id}_{timestamp}_{event_type}.jpg`
3. Each screenshot contains a semi-transparent telemetry box overlayed at the top, showing:
   * Event Type (e.g., `DROWSINESS_ALARM`).
   * Ratios: EAR value, MAR value.
   * Gaze angles: Pitch, Yaw.
   * Action taken (e.g., voice alert, email alert).

---

## 📄 Generating PDF Session Reports

To export a driving session summary:
1. When you stop monitoring by clicking **Stop Monitor** in the sidebar, the session ends.
2. The report generator compiles session logs from SQLite.
3. Open the folder: `data/reports/`
4. Find your report: `session_report_{session_id}.pdf` (or `.html` fallback).
5. The report lists metadata (driver profile, duration, alert counters) and a table of logged violations.
