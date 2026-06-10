import sys
import time
from pathlib import Path

# Add root folder to python path to resolve imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.alert_system.audio_manager import AudioManager
from src.alert_system.voice_alert import VoiceAlert
from src.alert_system.email_service import EmailService
from src.alert_system.notification_service import NotificationService
from src.utils.logger import logger

def run_alert_framework_test():
    print("=" * 60)
    print("    DRIVER SAFETY ALERT FRAMEWORK VERIFICATION RUNNER    ")
    print("=" * 60)
    
    logger.info("Initializing components...")
    
    # Initialize the framework components
    audio_mgr = AudioManager()
    voice_alert = VoiceAlert()
    email_service = EmailService()
    
    notifier = NotificationService(audio_mgr, voice_alert, email_service)
    
    driver_name = "Test_Diagnostics_Driver"
    
    try:
        # Step 1: Simulate Safe State
        print("\n[*] Step 1: Simulating SAFE State...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Safe", 
            indicators={"eye_closure": False, "yawn": False, "distraction": False},
            ear=0.28, mar=0.15, pitch=0.0, yaw=0.0
        )
        time.sleep(2.0)
        
        # Step 2: Simulate Warning State (Yawning)
        print("\n[*] Step 2: Simulating YAWNING Warning State (Level 1)...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Warning", 
            indicators={"eye_closure": False, "yawn": True, "distraction": False},
            ear=0.28, mar=0.62, pitch=0.0, yaw=0.0
        )
        time.sleep(3.0) # Allow sound and TTS to execute
        
        # Step 3: Simulate Warning State (Gaze Distraction)
        print("\n[*] Step 3: Simulating GAZE DISTRACTION Warning State (Level 2)...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Warning", 
            indicators={"eye_closure": False, "yawn": False, "distraction": True},
            ear=0.28, mar=0.12, pitch=0.0, yaw=20.0
        )
        time.sleep(3.0)
        
        # Step 4: Simulate Danger State (Level 3 - Continuous Alarm Loop)
        print("\n[*] Step 4: Simulating DANGER State (Level 3 - Continuous Buzzer)...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Danger", 
            indicators={"eye_closure": True, "yawn": False, "distraction": False},
            ear=0.14, mar=0.12, pitch=-5.0, yaw=0.0
        )
        time.sleep(4.0) # Listen to continuous beep loop
        
        # Step 5: Simulate Critical State (Starts at Level 3, escalates to Level 4)
        print("\n[*] Step 5: Simulating CRITICAL State (Timer Escalation to Level 4)...")
        
        # Frame 1: Critical start (Escalation timer starts)
        print("  - Entering Critical risk state...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Critical", 
            indicators={"eye_closure": True, "yawn": False, "distraction": True},
            ear=0.12, mar=0.12, pitch=-16.0, yaw=18.0
        )
        time.sleep(2.0) # Still under 4-second escalation threshold
        
        # Frame 2: Critical continue (Past 4 seconds, triggers Level 4 email alert)
        print("  - Remaining Critical (Past 4 seconds threshold)...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Critical", 
            indicators={"eye_closure": True, "yawn": False, "distraction": True},
            ear=0.11, mar=0.12, pitch=-16.0, yaw=18.0
        )
        time.sleep(4.0) # Allow SMTP thread to attempt connection/logs
        
        # Step 6: Simulate Driver Recovery (Safe State)
        print("\n[*] Step 6: Simulating Driver Recovery (SAFE State - Silence Alarms)...")
        notifier.process_risk_state(
            driver_name, 
            risk_level="Safe", 
            indicators={"eye_closure": False, "yawn": False, "distraction": False},
            ear=0.28, mar=0.15, pitch=0.0, yaw=0.0
        )
        time.sleep(2.5) # Wait to confirm silent state
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    finally:
        # Release mixer and stop speech threads
        logger.info("Shutting down alert framework test...")
        notifier.close()
        print("\n" + "=" * 50)
        print("      ALERT FRAMEWORK DIAGNOSTICS COMPLETED       ")
        print("=" * 50 + "\n")

if __name__ == "__main__":
    run_alert_framework_test()
