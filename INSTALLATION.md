# Installation & Configuration Guide

This document provides step-by-step instructions to configure, install, and troubleshoot the **AI-Powered Intelligent Driver Safety & Drowsiness Prevention System** on your local machine.

---

## 📋 System Requirements
* **Operating System**: Windows 10/11 (Intel/AMD/ARM architecture).
* **Python**: Version 3.11.x (highly recommended; verified compatible).
* **Hardware**:
  * Standard USB Webcam or integrated laptop camera.
  * Audio output (speakers, headphones) for alert generation.
  * Internet connection (for email alerts setup and initial library installation).

---

## 🛠️ Step-by-Step Installation

### Step 1: Clone the Repository
Open a terminal (Command Prompt, PowerShell, or Git Bash) and run:
```bash
git clone https://github.com/your-username/drowsiness-prevention-system.git
cd "Drowsiness Prevention System"
```

### Step 2: Configure the Python Environment
Create a clean virtual environment to prevent library version conflicts:
```powershell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Core Dependencies
Upgrade `pip` and install the requirements:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Configuration Setup

### 1. Environmental Overrides (`.env`)
Copy the environment variables template:
```powershell
copy .env.example .env
```
Open `.env` in a text editor and configure your specific local environments:
* **`CAMERA_SOURCE`**: Change from `0` to a specific index (e.g., `1` if using an external USB webcam), or path string to a pre-recorded test MP4 file.
* **`LOG_LEVEL`**: Set to `INFO` for standard runs, or `DEBUG` for verbose CV metrics logging.

### 2. SMTP Emergency Email Configurations
To allow the **Level 4 Emergency Alert** to send email warnings, you must configure SMTP credentials in your `.env` file:
```env
# Example Google SMTP configurations
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.driver.alerts@gmail.com
SMTP_PASSWORD=your_google_app_password
EMERGENCY_RECEIVER_EMAIL=your.emergency.contact@domain.com
```
> [!IMPORTANT]
> If using Gmail, you cannot use your standard account password. You must enable **2-Factor Authentication** on your Google Account and generate an **App Password** (16-digit code) specifically for this application.

### 3. Alarm Audio Assets
Before running safety checks, ensure warning sounds are present. The centralized configuration manager automatically maps sound files:
* Place a soft chime sound file at `data/audio/warning_chime.wav`.
* Place a loud alarm buzzer file at `data/audio/critical_alarm.wav`.

---

## 🔍 Pre-run Verification Diagnostics

Validate that python, library dependencies, database paths, and audio/voice drivers are fully functional before launching the main system:
```bash
python launcher.py --diagnose
```
If any check fails, resolve the warnings according to the troubleshooting guidelines below.

---

## ❌ Troubleshooting Guidelines

### 1. `UnicodeEncodeError` in Windows Command Line
* **Symptom**: Console throws exceptions about encoding character `\u2713` (checkmark icon).
* **Fix**: This issue is fixed by default in our codebase by using safe ASCII tags (`[OK]`, `[FAIL]`). Ensure you are using the updated `launcher.py`.

### 2. `pywintypes.com_error` or speech freezes
* **Symptom**: `pyttsx3` voice synthesizer crashes or hangs during initialization on Windows.
* **Fix**: Ensure `pyttsx3` is initialized *inside* the background worker thread (already implemented in `src/alert_system/voice_alert.py`). If errors persist, verify that the Windows Audio service is running, or verify your default system voice settings inside Windows Settings under **Time & Language > Speech**.

### 3. Pygame Mixer Initialization Fails (`No available audio device`)
* **Symptom**: Pygame mixer throws errors indicating audio drivers are unavailable.
* **Fix**: Ensure your speakers or audio output drivers are connected and set as default. On headless servers or Virtual Machines without audio outputs, the system will gracefully bypass sound alerts and log a warning.

### 4. OpenCV Camera Cannot Open (`Failed to open camera source: 0`)
* **Symptom**: The camera stream shows a black box or diagnostic errors.
* **Fix**:
  * Verify that no other application (e.g., Zoom, Teams, Skype) is currently using your webcam.
  * Check Windows privacy settings: Search for **Camera Privacy Settings** and ensure **"Allow apps to access your camera"** is toggled ON.
  * Try changing `CAMERA_SOURCE` in your `.env` to `1` or `2` to target secondary cameras.
