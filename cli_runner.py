import cv2
import time
import sys
from pathlib import Path

# Add root folder to python path to resolve imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Core config
from config import config

# CV Engine
from src.core.camera_manager import CameraManager
from src.cv_engine.face_detector import FaceDetector
from src.cv_engine.landmark_extractor import LandmarkExtractor
from src.cv_engine.eye_detector import EyeDetector
from src.cv_engine.yawn_detector import YawnDetector
from src.cv_engine.head_pose_detector import HeadPoseDetector

# Risk & Database
from src.db.database_manager import DatabaseManager
from src.db.event_logger import EventLogger
from src.core.risk_engine import RiskEngine
from src.core.state_manager import StateManager

# Alerts
from src.alert_system.audio_manager import AudioManager
from src.alert_system.voice_alert import VoiceAlert
from src.alert_system.email_service import EmailService
from src.alert_system.notification_service import NotificationService
from src.utils.logger import logger

def run_headless_monitoring():
    logger.info("=" * 60)
    print("    DRIVER SAFETY HEADLESS RUNNER (CLI MONITORING MODE)    ")
    logger.info("=" * 60)
    
    # 1. Initialize Database & States
    db_mgr = DatabaseManager()
    event_logger = EventLogger(db_mgr)
    state_mgr = StateManager(db_mgr, event_logger)
    
    username = "cli_default_driver"
    logger.info(f"Initializing driver profile: '{username}'")
    if not state_mgr.initialize_driver(username):
        logger.error("Failed to initialize driver profile. Exiting.")
        return
        
    user_settings = state_mgr.user_settings
    
    # 2. Initialize CV Detectors
    detector = FaceDetector()
    extractor = LandmarkExtractor()
    
    eye_dec = EyeDetector(ear_threshold=user_settings.get("ear_threshold", 0.22))
    yawn_dec = YawnDetector(mar_threshold=user_settings.get("mar_threshold", 0.50))
    pose_dec = HeadPoseDetector(deviation_threshold=user_settings.get("gaze_threshold", 15.0))
    
    # 3. Initialize Risk Engine
    risk_engine = RiskEngine(
        window_size=12,
        head_drop_threshold=-12.0,
        distraction_threshold=user_settings.get("gaze_threshold", 15.0)
    )
    
    # 4. Initialize Alerts Framework
    audio_mgr = AudioManager()
    audio_mgr.set_volume(user_settings.get("alert_volume", 0.8))
    
    voice_alert = VoiceAlert()
    email_service = EmailService()
    notifier = NotificationService(audio_mgr, voice_alert, email_service, db_manager=db_mgr)
    
    # 5. Initialize Camera Manager
    cam_mgr = CameraManager(
        source=config.camera_source,
        width=config.frame_width,
        height=config.frame_height
    )
    
    # Start stream and DB session
    cam_mgr.start()
    session_id = state_mgr.start_session()
    if not session_id:
        logger.error("Failed to register driving session. Exiting.")
        cam_mgr.stop()
        notifier.close()
        return
        
    logger.info(f"Monitoring active. Session ID: {session_id}. Press Ctrl+C to stop.")
    
    last_print_time = 0.0
    
    try:
        while True:
            # Grab frame
            ret, frame = cam_mgr.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            h, w, _ = frame.shape
            
            # Process face mesh
            results = detector.process_frame(frame)
            
            risk_level = "Safe"
            raw_score = 0
            
            if results and results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                features = extractor.extract(face_landmarks, w, h)
                
                if features:
                    # Calculations
                    eye_res = eye_dec.process(features["left_eye"], features["right_eye"])
                    yawn_res = yawn_dec.process(features["mouth"])
                    pose_res = pose_dec.process(features["head_pose_points"], w, h)
                    
                    # Risk evaluation
                    risk_res = risk_engine.process(
                        eye_res["closure_duration"], yawn_res["yawn_duration"], 
                        pose_res["head_down_duration"], pose_res["yaw_distraction_duration"]
                    )
                    raw_score = risk_res["raw_score"]
                    
                    # Update DB States
                    risk_level = state_mgr.update_risk_state(
                        risk_res, eye_res["avg_ear"], yawn_res["mar"],
                        pose_res["pitch"], pose_res["yaw"], pose_res["roll"]
                    )
                    
                    # Trigger alert outputs (Level 0-4)
                    notifier.process_risk_state(
                        username, risk_level, risk_res["indicators"],
                        eye_res["avg_ear"], yawn_res["mar"],
                        pose_res["pitch"], pose_res["yaw"],
                        frame=frame, session_id=session_id
                    )
                    
                    # Periodic console logging (throttled to 1 second)
                    now = time.time()
                    if now - last_print_time >= 1.0:
                        print(
                            f"State: {risk_level:<10} | Raw Score: {raw_score} | "
                            f"EAR: {eye_res['avg_ear']:.3f} | MAR: {yawn_res['mar']:.3f} | "
                            f"Pitch: {pose_res['pitch']:>5.1f} | Loop Rate: {cam_mgr.get_fps():.1f} FPS",
                            end="\r", flush=True
                        )
                        last_print_time = now
            else:
                # Reset notifier to safe if driver's face is missing
                notifier.process_risk_state(
                    username, "Safe", {"eye_closure": False, "yawn": False, "distraction": False},
                    0.28, 0.12, 0.0, 0.0
                )
                
            time.sleep(0.01) # keep thread yield
            
    except KeyboardInterrupt:
        logger.info("\nShutdown command detected from keyboard.")
    except Exception as e:
        logger.error(f"\nHeadless runner runtime exception: {e}")
    finally:
        logger.info("Releasing system resources...")
        state_mgr.end_session()
        cam_mgr.stop()
        notifier.close()
        logger.info("Headless runner successfully shutdown.")

if __name__ == "__main__":
    run_headless_monitoring()
