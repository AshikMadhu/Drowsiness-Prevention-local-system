# Live Demonstration Script

This script provides a step-by-step guide for presenting a live demonstration of the Driver Safety & Drowsiness Prevention System during your academic review.

---

## 🛠️ Demo Setup
1. Ensure your webcam is connected and the room has adequate lighting.
2. Activate your virtual environment and start the dashboard server:
   ```bash
   python launcher.py --gui
   ```
3. Open the browser to `http://localhost:8501`.
4. Fill in a test driver username in the sidebar (e.g., `IIIT_Panel_Demo`).
5. Ensure speaker volume is enabled on your laptop so the panel can hear the alerts.

---

## 🎬 Step-by-Step Demo Flow

| Step | Presenter Action | System Output | Talking Points |
| :--- | :--- | :--- | :--- |
| **1. Startup** | - Enter username.<br>- Click **Start Monitor**. | - Webcam feed opens.<br>- Facial mesh overlay renders.<br>- Telemetry gauges show safe baselines (EAR ~0.28, MAR ~0.12). | *"We start by entering a username and starting monitoring. The system initializes the threaded frame grabber, opens the webcam, and overlays the 468-point face mesh. As you can see, in my alert state, the risk indicators show SAFE."* |
| **2. Gaze Distraction** | - Turn your head left or right, looking away from the camera. | - Yellow direction vector line deflects.<br>- Status changes to: `GAZE DISTRACTED: YES`.
- Risk transitions to: `Warning` after 3.0s.<br>- Soft warning chime plays. | *"Now, I will simulate looking away at a GPS screen or side mirror. Up to 35 seconds is permitted without buzzer alarms to check mirrors. If I hold this distraction for longer than 35.0 seconds, the system registers a DANGER alarm and prompts me to focus on the road."* |
| **3. Yawning Fatigue** | - Look back, open your mouth wide (simulating a yawn). | - Orange markers highlight mouth shape.<br>- MAR graph rises above `0.50` threshold.<br>- Plays soft warning chime at 1.5s.<br>- At 3.0s, triggers continuous critical alarm. | *"Next, I will simulate a yawn. The inner-lip landmark extractor measures the Mouth Aspect Ratio. As it rises above 0.50, the risk state registers a Warning and issues a voice break warning. If the yawn is sustained for more than 3.0 seconds, a continuous alarm sounds."* |
| **4. Drowsiness Alarm** | - Close your eyes for 3.0 seconds. | - EAR graph drops below `0.22` threshold.<br>- Closed eyes timer starts.<br>- Risk transitions to: `Danger` after 3.0s.<br>- Continuous alarm buzzer plays. | *"Now I will simulate nodding off by closing my eyes. Once eye closure exceeds 3.0 seconds, the risk level escalates to DANGER. A continuous alarm buzzer sounds to wake the driver immediately."* |
| **5. Email SOS Escalation** | - Repeat the eye closed alarm 4 times in a session. | - 4th eye closure alarm triggers.<br>- Threat screenshot is captured.<br>- SMTP thread sends emergency email alert to ashiksjc2025@gmail.com. | *"To demonstrate emergency dispatch, I will trigger the eye-closed alarm four times. On the 4th repeat alarm, the system automatically captures a screenshot, queries the database for session stats, and dispatches an emergency email to ashiksjc2025@gmail.com on a background thread."* |
| **6. Driver Recovery** | - Open eyes and look straight at the camera. | - Alarms silence.<br>- Telemetry returns to nominal values.<br>- Voice alert states: *"System normal. Drive safely."* | *"Once I open my eyes and look back at the road, the system automatically silences the alarms, resets all metrics to nominal values, and logs the session recovery."* |
| **7. Historic Statistics** | - Click **Stop Monitor** in the sidebar. | - Webcam releases.<br>- Dataframe displays session stats and past logs. | *"Upon stopping monitoring, the SQLite database compiles the session stats. The dashboard renders historical records, allowing managers to inspect cumulative alerts and violations."* |
