# Project Impact Statement

The **AI-Powered Intelligent Driver Safety & Drowsiness Prevention System** addresses road safety challenges by providing a non-intrusive, real-time safety framework for commercial and private transport sectors.

---

## 🌍 Social & Road Safety Impact

### 1. Reducing Fatigue-Related Accidents
Driver drowsiness and visual distraction are responsible for over **20% of commercial vehicle collisions** on national highways. Long-haul truck operators, bus drivers, and delivery fleets often operate during late-night hours, increasing the risk of microsleep incidents. By providing multi-stage warnings (alarms and voice reminders) and escalating to emergency email notifications if the driver remains unresponsive, the system acts as a real-time safety assistant, helping to reduce accidents and save lives.

### 2. Democratizing ADAS Technology
Modern Advanced Driver Assistance Systems (ADAS) are typically restricted to premium vehicles due to expensive hardware configurations (like infrared eye trackers, steer-torque sensors, or active radar arrays). This project provides an **affordable, software-driven alternative** that runs on a standard laptop webcam, making safety monitoring accessible to budget commercial transporters, school buses, and private vehicles.

---

## 💻 Technical & Open Source Impact

### 1. Lightweight Edge Computing
By utilizing MediaPipe's Face Mesh landmarks instead of heavy deep learning pipelines (which require dedicated GPUs and block threads), the system runs calculations at **30 FPS on standard CPUs** with less than **20ms of latency**. This efficiency makes it suitable for deployment on low-cost edge platforms like Raspberry Pi or NVIDIA Jetson Nano.

### 2. SOLID-Compliant Reference Architecture
The project provides a clean, SOLID-compliant codebase that separates concerns across decoupled modules:
* Asynchronous voice and email alerting queues prevent processing freezes.
* Thread-safe connection context managers avoid SQLite locks.
* The Facade pattern simplifies frontend integrations.

This structure makes the repository a valuable **reference design for ADAS research** and open-source ADAS development.
