import cv2
import time
import sys
import numpy as np
from pathlib import Path

# Add root folder to python path to resolve imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import config
from src.core.camera_manager import CameraManager
from src.cv_engine.face_detector import FaceDetector
from src.cv_engine.landmark_extractor import LandmarkExtractor
from src.cv_engine.eye_detector import EyeDetector
from src.cv_engine.yawn_detector import YawnDetector
from src.cv_engine.head_pose_detector import HeadPoseDetector
from src.utils.logger import logger

def run_drowsiness_detectors_test():
    """Real-time validation loop for Eye Closure, Yawn, and Head Pose metrics."""
    logger.info("Initializing Drowsiness & Distraction Metrics Diagnostic Runner...")
    
    # Initialize components with configuration values
    cam_mgr = CameraManager(
        source=config.camera_source,
        width=config.frame_width,
        height=config.frame_height
    )
    detector = FaceDetector()
    extractor = LandmarkExtractor()
    
    # Load thresholds from configuration manager
    ear_th = config.ear_threshold
    mar_th = config.mar_threshold
    gaze_th = config.gaze_threshold
    
    eye_dec = EyeDetector(ear_threshold=ear_th)
    yawn_dec = YawnDetector(mar_threshold=mar_th)
    pose_dec = HeadPoseDetector(deviation_threshold=gaze_th)
    
    # Start Camera thread
    cam_mgr.start()
    
    # Window properties
    window_name = "Drowsiness & Distraction Verification Dashboard"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Performance telemetry metrics tracker
    telemetry = {
        "start_time": time.time(),
        "total_frames": 0,
        "max_eye_closure_sec": 0.0,
        "max_yawn_sec": 0.0,
        "distracted_frame_count": 0,
        "drowsy_frame_count": 0,
        "yawn_frame_count": 0,
        "loop_times": []
    }
    
    logger.info(f"Loaded Thresholds - EAR Threshold: {ear_th}, MAR Threshold: {mar_th}")
    logger.info("Starting frame evaluation loop. Press 'q' or 'ESC' to exit.")
    
    try:
        while True:
            loop_start = time.time()
            
            # Read webcam frame
            ret, frame = cam_mgr.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            h, w, _ = frame.shape
            telemetry["total_frames"] += 1
            
            # 1. Process frame with face mesh
            results = detector.process_frame(frame)
            
            # 2. Extract landmark features
            if results and results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                features = extractor.extract(face_landmarks, w, h)
                
                if features:
                    # 3. Evaluate Eye closure
                    eye_results = eye_dec.process(features["left_eye"], features["right_eye"])
                    avg_ear = eye_results["avg_ear"]
                    is_closed = eye_results["is_closed"]
                    closure_dur = eye_results["closure_duration"]
                    
                    # Update max eye closure record
                    if closure_dur > telemetry["max_eye_closure_sec"]:
                        telemetry["max_eye_closure_sec"] = closure_dur
                    if is_closed:
                        telemetry["drowsy_frame_count"] += 1
                        
                    # 4. Evaluate Yawning
                    yawn_results = yawn_dec.process(features["mouth"])
                    mar = yawn_results["mar"]
                    is_yawning = yawn_results["is_yawning"]
                    yawn_dur = yawn_results["yawn_duration"]
                    
                    # Update max yawn record
                    if yawn_dur > telemetry["max_yawn_sec"]:
                        telemetry["max_yawn_sec"] = yawn_dur
                    if is_yawning:
                        telemetry["yawn_frame_count"] += 1
                        
                    # 5. Evaluate Head Pose
                    pose_results = pose_dec.process(features["head_pose_points"], w, h)
                    pitch = pose_results["pitch"]
                    yaw = pose_results["yaw"]
                    roll = pose_results["roll"]
                    is_distracted = pose_results["is_distracted"]
                    p1 = pose_results["nose_tip_center"]
                    p2 = pose_results["nose_projected_tip"]
                    
                    if is_distracted:
                        telemetry["distracted_frame_count"] += 1

                    # --- Visual Render Overlays ---
                    # Draw a premium, futuristic face mask (contour outline + iris circles) using thin custom styling
                    import mediapipe as mp
                    mp_drawing = mp.solutions.drawing_utils
                    mp_face_mesh = mp.solutions.face_mesh

                    contour_spec = mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1, circle_radius=1)
                    iris_spec = mp_drawing.DrawingSpec(color=(0, 140, 255), thickness=1, circle_radius=1)

                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=contour_spec
                    )
                    
                    if hasattr(face_landmarks, "landmark") and len(face_landmarks.landmark) >= 478:
                        mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_IRISES,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=iris_spec
                        )
                        
                    # Draw Head Pose Direction Vector
                    if p1 and p2:
                        cv2.line(frame, p1, p2, (0, 255, 255), 2)
                        cv2.circle(frame, p1, 3, (0, 0, 255), -1)
                    
                    # Dashboard Status Boxes
                    # Eyes closed status
                    eye_color = (0, 0, 255) if is_closed else (0, 255, 0)
                    eye_text = f"EYES CLOSED: YES ({closure_dur:.1f}s)" if is_closed else "EYES CLOSED: NO"
                    cv2.putText(frame, eye_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)
                    
                    # Yawning status
                    yawn_color = (0, 0, 255) if is_yawning else (0, 255, 0)
                    yawn_text = f"YAWNING: YES ({yawn_dur:.1f}s)" if is_yawning else "YAWNING: NO"
                    cv2.putText(frame, yawn_text, (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, yawn_color, 2)

                    # Distraction status
                    dist_color = (0, 0, 255) if is_distracted else (0, 255, 0)
                    dist_text = "GAZE DISTRACTED: YES" if is_distracted else "GAZE DISTRACTED: NO"
                    cv2.putText(frame, dist_text, (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, dist_color, 2)

                    # Draw metric numbers
                    cv2.putText(frame, f"EAR: {avg_ear:.3f} (Th: {ear_th})", (20, 200), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"MAR: {mar:.3f} (Th: {mar_th})", (20, 220), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"Pitch: {pitch:.1f} Yaw: {yaw:.1f} Roll: {roll:.1f}", (20, 240), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            else:
                cv2.putText(frame, "No Face Detected", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Performance loop measurement
            loop_end = time.time()
            loop_elapsed = loop_end - loop_start
            telemetry["loop_times"].append(loop_elapsed)
            
            # FPS Overlay
            avg_loop_time = np.mean(telemetry["loop_times"][-30:]) if telemetry["loop_times"] else 0.01
            loop_fps = 1.0 / avg_loop_time if avg_loop_time > 0 else 0.0
            
            cv2.putText(frame, f"CV Loop Rate: {loop_fps:.1f} FPS", (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Camera Thread: {cam_mgr.get_fps():.1f} FPS", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Display image
            cv2.imshow(window_name, frame)
            
            # Key checks
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                logger.info("Exit request detected from user.")
                break
                
    except Exception as e:
        logger.error(f"Error in metrics validator loop: {e}")
        
    finally:
        # Clean resources
        logger.info("Cleaning metrics diagnostic resources...")
        cam_mgr.stop()
        detector.close()
        cv2.destroyAllWindows()
        
        # Display performance evaluation report
        run_duration = time.time() - telemetry["start_time"]
        avg_latency_ms = np.mean(telemetry["loop_times"]) * 1000.0 if telemetry["loop_times"] else 0.0
        
        print("\n" + "=" * 50)
        print("    METRICS VALIDATION ENGINE PERFORMANCE REPORT    ")
        print("=" * 50)
        print(f"Total session run time:       {run_duration:.1f} seconds")
        print(f"Total processed frames:       {telemetry['total_frames']}")
        print(f"Average loop latency:         {avg_latency_ms:.2f} ms")
        print(f"Calculated loop frame rate:   {1000.0 / avg_latency_ms:.1f} FPS" if avg_latency_ms > 0 else "N/A")
        print("-" * 50)
        print(f"Max Eye Closure Duration:     {telemetry['max_eye_closure_sec']:.2f} seconds")
        print(f"Max Yawn Duration:            {telemetry['max_yawn_sec']:.2f} seconds")
        print(f"Drowsy frame ratio:           {telemetry['drowsy_frame_count'] / max(1, telemetry['total_frames']) * 100:.1f}%")
        print(f"Yawning frame ratio:          {telemetry['yawn_frame_count'] / max(1, telemetry['total_frames']) * 100:.1f}%")
        print(f"Distracted frame ratio:       {telemetry['distracted_frame_count'] / max(1, telemetry['total_frames']) * 100:.1f}%")
        print("=" * 50 + "\n")

if __name__ == "__main__":
    run_drowsiness_detectors_test()
