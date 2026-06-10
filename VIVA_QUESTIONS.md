# Oral Examination (Viva) Preparation Guide

This document contains standard Viva/Q&A questions and technical answers to help you prepare for your IIIT Internship Presentation.

---

## 👁️ Section 1: Computer Vision & Mathematics

### Q1: What is the Eye Aspect Ratio (EAR) and how does it help detect drowsiness?
* **Answer**: The EAR is a geometric ratio calculated from 6 coordinates surrounding the eye. It measures the vertical distance between the eyelids divided by the horizontal width:
  $$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2.0 \cdot ||p_1 - p_4||}$$
  When eyes are open, this value is high (approx `0.26` to `0.30`). When closed, it drops towards `0.15`. By checking if the average EAR remains below a threshold (e.g. `0.22`) for consecutive frames, we can distinguish standard blinks (which last 100-400ms) from microsleep events (lasting longer than 1.5 seconds).

### Q2: Why did you use inner lip coordinates for Yawn Detection (MAR) instead of outer lips?
* **Answer**: The outer lips move significantly during normal conversation, singing, or smiling, which often generates false positives. The inner lip coordinates (MAR calculation) change only when the mouth is wide open (apertures exceeding `0.50`), which happens during yawning, making the yawn detector more accurate.

### Q3: Explain how Head Pose Estimation works using `solvePnP`.
* **Answer**: `solvePnP` (Perspective-n-Point) is an OpenCV algorithm that calculates the relative rotation ($\mathbf{R}$) and translation ($\mathbf{t}$) of a 3D object from its 2D camera projections. We define a standard set of 3D facial feature coordinates (chin, nose, eye corners, mouth corners) and align them with the 2D pixel coordinates extracted by MediaPipe. The algorithm solves the perspective equations, yielding a rotation vector. Converting this vector to a rotation matrix using `cv2.Rodrigues` allows us to extract Pitch (vertical nodding), Yaw (horizontal look-away), and Roll (tilt), which tell us if the driver is distracted.

---

## 💻 Section 2: Software Design & Architecture

### Q4: Why did you implement a threaded `CameraManager` instead of using `cv2.VideoCapture` directly in the main loop?
* **Answer**: Standard OpenCV camera reading (`cap.read()`) is an I/O-bound blocking operation. If called on the main processing thread, the system must wait for the camera hardware to return a frame, which limits execution speed to the camera's default frame rate (often dropping to 10-15 FPS if computational loads are high). 
  By running the capture loop on a separate background daemon thread, frames are grabbed continuously and saved in a buffer. The main thread simply reads the latest frame copy via a thread lock, freeing up the CPU and allowing the main loop to run at a stable 30 FPS.

### Q5: How did you solve the blocking issue of Text-to-Speech (TTS) voice alerts?
* **Answer**: `pyttsx3` is a synchronous library; calling `.say()` and `.runAndWait()` freezes execution until speech completes, dropping the frame rate of the system. 
  To solve this, we implemented `VoiceAlert` with a background worker thread. When the system needs to speak, it pushes the text to a thread-safe `queue.Queue` in 1 millisecond. The background thread monitors this queue, initializes its own COM voice context, and handles speech output asynchronously, ensuring the main camera loop is never blocked.

### Q6: Why did you choose SQLite for data storage instead of a JSON file or csv?
* **Answer**: A driver monitoring system generates frequent, structured telemetry events (ratios, gaze directions, times). A CSV or JSON file requires reading and rewriting the entire file for updates, which slows down the system and can corrupt data if the app crashes. SQLite is a lightweight, serverless relational database. It supports ACID transactions, SQL indexing (allowing the dashboard to query past sessions in milliseconds), and safe concurrent read/writes.

---

## 🧠 Section 3: Machine Learning & Analytics

### Q7: What is the purpose of the Fatigue Prediction Engine (Phase 8) if you already have real-time detectors?
* **Answer**: Real-time detectors (EAR/MAR thresholds) identify *immediate* safety violations (e.g. eyes closed right now). The Fatigue Prediction Engine predicts *impending* fatigue. It analyzes the frequencies of driver behaviors (blinks, yawns, head drops) and historical risk scores over the past minutes. Using Logistic Regression and Random Forest ensembles, it calculates the probability that the driver is becoming fatigued, alerting them to take a rest *before* they fall into microsleep.

### Q8: What features were engineered for training the fatigue classifiers?
* **Answer**: We engineered four features from the raw database events:
  1. **Blink Frequency**: Number of eye closures per minute.
  2. **Yawn Frequency**: Number of yawning events per minute.
  3. **Head Drop Frequency**: Number of head tilts forward per minute.
  4. **Avg Historical Risk**: A running weighted mean of session safety alerts.
  These frequency-based features are scale-invariant and represent long-term behavioral trends rather than single-frame spikes.
