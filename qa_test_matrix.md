# Runtime Validation Checklist & QA Test Matrix

This document provides a professional QA Test Matrix for verifying all fourteen modules of the **Driver Safety & Drowsiness Prevention System**.

---

## 📊 QA Test Matrix & Validation Cases

### 1. Webcam Streamer
* **Manual Test Case**: Verify threaded webcam capture starts and returns frames.
* **Input Action**: Run `python launcher.py --cli` (or start the dashboard monitor).
* **Expected Output**: Log output shows `Initializing camera source: 0`. Frame retrieval is successful at 30 FPS.
* **Failure Conditions**: `cv2.VideoCapture` fails to open the source; loop drops frame grab rates below 15 FPS.
* **Pass/Fail Criteria**:
  * **Pass**: Thread starts, and the camera feed opens.
  * **Fail**: Thread hangs, or no frames are read.

### 2. Face Detection
* **Manual Test Case**: Verify MediaPipe landmarks extraction on frames.
* **Input Action**: Present face to camera in front of standard lighting.
* **Expected Output**: 468/478 landmarks are extracted, returning a non-empty coordinates list.
* **Failure Conditions**: Landmarker returns empty results for a visible face due to tracking confidence thresholds.
* **Pass/Fail Criteria**:
  * **Pass**: Landmark coordinate list is returned for a face.
  * **Fail**: Face is present but landmarks are not extracted.

### 3. Eye Closure Detection
* **Manual Test Case**: Validate Eye Aspect Ratio (EAR) calculations and duration.
* **Input Action**: Close eyes for 2 seconds.
* **Expected Output**: EAR drops below `0.22`, and the closure timer increments.
* **Failure Conditions**: EAR remains high ($>0.22$) during closure, or the closure duration counter fails to start.
* **Pass/Fail Criteria**:
  * **Pass**: Eyes closed triggers a timer increment.
  * **Fail**: Eye closure is not detected.

### 4. Yawn Detection
* **Manual Test Case**: Validate Mouth Aspect Ratio (MAR) yawn tracking.
* **Input Action**: Open mouth wide (yawning) for 3 seconds.
* **Expected Output**: MAR rises above `0.50`, and the yawn duration timer increments.
* **Failure Conditions**: MAR remains low ($<0.50$) during mouth opening, or the yawn timer is not triggered.
* **Pass/Fail Criteria**:
  * **Pass**: Wide mouth opening triggers a yawn timer increment.
  * **Fail**: Yawning is not detected.

### 5. Head Pose Detection
* **Manual Test Case**: Verify `solvePnP` head pose calculations.
* **Input Action**: Tilt head up, down, left, and right.
* **Expected Output**: Pitch, Yaw, and Roll values change relative to head rotation.
* **Failure Conditions**: Output values remain fixed at 0.0, or calculation throws exceptions.
* **Pass/Fail Criteria**:
  * **Pass**: Pitch, Yaw, and Roll values change with head movements.
  * **Fail**: Head pose values are fixed or throw exceptions.

### 6. Distraction Detection
* **Manual Test Case**: Verify look-away alerts are triggered.
* **Input Action**: Turn head to the left/right (yaw $>15.0$ degrees) for 3 seconds.
* **Expected Output**: Status changes to `GAZE DISTRACTED: YES` and a warning is triggered.
* **Failure Conditions**: Head deflection beyond 15 degrees is ignored.
* **Pass/Fail Criteria**:
  * **Pass**: Gaze deviation triggers a distraction warning.
  * **Fail**: Gaze deviation is ignored.

### 7. Risk Intelligence Engine
* **Manual Test Case**: Verify risk score calculation and risk level transitions.
* **Input Action**: Simulate closed eyes (score +2) and distraction (score +1) simultaneously.
* **Expected Output**: Risk score updates to 3, and the risk level transitions to `Warning`.
* **Failure Conditions**: Scores are calculated incorrectly, or the level fails to transition.
* **Pass/Fail Criteria**:
  * **Pass**: Risk level transitions based on the calculated score.
  * **Fail**: Risk level transitions fail or calculate incorrectly.

### 8. Pygame Audio Alerts
* **Manual Test Case**: Verify warning chimes and critical alarms play.
* **Input Action**: Transition risk level to `Danger`.
* **Expected Output**: Continuous alarm buzzer plays.
* **Failure Conditions**: Sound card fails to initialize, or the alarm fails to play.
* **Pass/Fail Criteria**:
  * **Pass**: Danger state plays a continuous alarm.
  * **Fail**: Danger state remains silent.

### 9. Voice Alerts
* **Manual Test Case**: Verify asynchronous text-to-speech warnings.
* **Input Action**: Trigger a distraction warning.
* **Expected Output**: Voice alert states: *"Please keep your eyes on the road."*
* **Failure Conditions**: TTS blocks the main loop, causing the frame rate to drop.
* **Pass/Fail Criteria**:
  * **Pass**: TTS speaks the warning without dropping the frame rate.
  * **Fail**: TTS blocks the main loop or fails to speak.

### 10. Email Notifications
* **Manual Test Case**: Verify Level 4 emergency email notifications.
* **Input Action**: Maintain `Critical` risk state for 5 seconds.
* **Expected Output**: SMTP thread sends a notification email to emergency contacts.
* **Failure Conditions**: Email thread blocks the camera stream, or fails to send the email.
* **Pass/Fail Criteria**:
  * **Pass**: Email is sent asynchronously when the threshold is crossed.
  * **Fail**: Email fails to send, or blocks the camera stream.

### 11. SQLite Logging
* **Manual Test Case**: Verify session telemetry and alerts are logged.
* **Input Action**: Start a session, trigger a warning, and stop the session.
* **Expected Output**: Data is logged to `driver_safety.db` and the warning count increments.
* **Failure Conditions**: SQLite database remains empty, or throws locking errors.
* **Pass/Fail Criteria**:
  * **Pass**: Telemetry data is logged to the database.
  * **Fail**: Database remains empty or throws locking errors.

### 12. Dashboard UI
* **Manual Test Case**: Verify the Streamlit dashboard renders metrics and video streams.
* **Input Action**: Run `python launcher.py --gui`.
* **Expected Output**: Dashboard opens in a browser, rendering the camera feed and telemetry charts.
* **Failure Conditions**: Streamlit server crashes, or placeholders fail to update.
* **Pass/Fail Criteria**:
  * **Pass**: Dashboard opens and renders metrics in real-time.
  * **Fail**: Dashboard crashes or fails to render.

### 13. PDF Session Reports
* **Manual Test Case**: Verify session report PDF generation.
* **Input Action**: Click **Stop Monitor** to end a session.
* **Expected Output**: A PDF report is generated in `data/reports/`.
* **Failure Conditions**: Report fails to generate, or crashes the application.
* **Pass/Fail Criteria**:
  * **Pass**: Report is generated successfully.
  * **Fail**: Report fails to generate.

### 14. Fatigue Prediction
* **Manual Test Case**: Verify Scikit-Learn fatigue probability predictions.
* **Input Action**: Run the active monitoring loop.
* **Expected Output**: The dashboard displays the live fatigue forecast probability.
* **Failure Conditions**: Probability remains at 0.0, or throws exceptions.
* **Pass/Fail Criteria**:
  * **Pass**: Forecast probability updates based on features.
  * **Fail**: Forecast remains static or throws exceptions.
