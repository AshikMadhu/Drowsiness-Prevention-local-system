# Driver Drowsiness Prevention System

An intelligent, real-time driver safety monitoring system that detects driver fatigue (eyes closing, yawning) and distractions (looking away from the road, head dropping) using a standard computer webcam. 

This system uses computer vision to track face landmarks and coordinates safety alarms, voice prompts, and SQLite database logging to keep drivers safe on the road.

---

## Key Features
* **Webcam Processing**: Uses a standard computer camera stream to evaluate the driver in real time.
* **Face Contour outlines**: Draws a thin, futuristic face mask over the driver's face for visual verification.
* **Eye & Blink Detection**: Computes the Eye Aspect Ratio (EAR) to detect blinking, squinting, and closed eyes.
* **Yawn Detection**: Monitors mouth openings using Mouth Aspect Ratio (MAR) to identify repeated yawning.
* **Head Pose & Off-Road Gaze Tracking**: Determines head rotation angles (Pitch, Yaw, Roll) to detect when a driver looks away from the road or drops their head due to micro-sleeps.
* **Multi-Level Alarm Subsystem**: Triggers soft chime warnings, continuous audio beeps, and text-to-speech voice reminders.
* **SQLite Telemetry Database**: Automatically logs driving sessions and alert counts to a local database.
* **Escalation & SMTP Email Alerts**: Automatically captures a screenshot of safety violations and dispatches emergency email alerts if a driver triggers repeated alarms.
* **Streamlit Web Dashboard**: Interactive local web dashboard showing live video feeds, real-time metrics graphs, and threshold adjustment settings.

---

## Project Directory Layout
* `src/`: Core python package directory.
  * `cv_engine/`: Facial mesh contours, head pose direction, eye closure, and yawn detector classes.
  * `core/`: Ingestion loop, camera manager, state database logger, and risk assessment equations.
  * `alert_system/`: Pygame audio mixer player, text-to-speech speaker, and SMTP email services.
  * `db/`: SQLite database tables and data-access code.
  * `ui/`: Streamlit dashboard layout and metric graphs.
* `config/`: System YAML configuration files.
* `data/`: Local storage folder for alarm audio files (`data/audio/`) and trained machine learning files (`data/models/`).
* `tests/`: Integration scripts to verify individual components.
* `requirements.txt`: Project package dependencies list.
* `launcher.py`: A unified command-line tool to run diagnostics, train models, and start the system.
* `main.py`: Entry point helper for launching the Streamlit GUI.
* `cli_runner.py`: Headless command-line monitor loop.
* `train_model.py`: Generates baseline datasets and trains the machine learning fatigue model.

---

## How to Run This Project for the FIRST Time

Follow these steps exactly when setting up the project on a new computer.

### Step 1: Clone the Repository
Open a terminal and clone this repository to your local machine:
```bash
git clone https://github.com/AshikMadhu/Drowsiness-Prevention-local-system.git
cd Drowsiness-Prevention-local-system
```

### Step 2: Create a Python Virtual Environment
Creating a virtual environment ensures that the project libraries do not conflict with your computer's global packages. 
*(Requires Python 3.11 or higher)*

* On Windows (PowerShell):
  ```powershell
  python -m venv .venv
  ```

### Step 3: Activate the Virtual Environment
Activating the environment points your terminal to the isolated folder:

* On Windows (PowerShell):
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### Step 4: Install Required Libraries
Install the stable dependencies declared in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 5: Train and Calibrate the Fatigue Model (Crucial!)
Before launching the system, you must train the machine learning classifier to establish baseline fatigue weights. Run this command:
```powershell
python train_model.py
```
*This creates the necessary model files (`fatigue_model_lr.pkl`, `fatigue_model_rf.pkl`, and `scaler.pkl`) inside the `data/models/` directory.*

### Step 6: Run System Diagnostics
Perform a quick health-check to verify that all packages, folders, audio files, and voice engine drivers are loaded and compatible:
```powershell
python launcher.py -d
```
*If everything is green and says "HEALTH CHECK PASSED", you are ready to start the monitor.*

### Step 7: Launch the System Dashboard
Start the visual web dashboard:
```powershell
python launcher.py -g
```
This will spin up a local web server and open the interface in your default browser automatically. Click **Start Monitor** on the left panel to begin.

---

## How to Run This Project for the Nth Time (Subsequent Runs)

Once the system has been set up once, you only need to run these two commands to launch it again:

1. Open your terminal in the project directory and **activate the environment**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
2. **Start the monitor**:
   ```powershell
   python launcher.py -g
   ```

---

## Alternative Execution (Headless CLI Mode)
If you want to run the system headlessly (console terminal only, without starting a browser dashboard), activate the environment and run:
```powershell
python launcher.py -c
```
This is useful for lower-spec machines or background automation scripts. Press `Ctrl+C` in your terminal to exit.

---

## Configurations & Settings

You can customize threshold settings (such as the default Eye Aspect Ratio limit, Yawning MAR limit, or camera indexes) in two ways:
1. **Interactive Control Panel**: Adjust the sliders on the left sidebar of the browser dashboard and click **Apply & Save Settings** to persist them.
2. **Configuration File**: Edit default system parameters directly inside the YAML file located at: [config/config.yaml](file:///c:/Users/ASHIK/Desktop/Drowsiness%20GitClone/Driver-Drowsiness-Prevention-System/config/config.yaml)
