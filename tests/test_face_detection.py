import cv2
import time
import sys
from pathlib import Path

# Add root folder to python path to resolve imports when running from within tests directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import config
from src.core.camera_manager import CameraManager
from src.cv_engine.face_detector import FaceDetector
from src.cv_engine.landmark_extractor import LandmarkExtractor
from src.utils.logger import logger

from typing import Any

def draw_features(frame: cv2.Mat, face_landmarks: Any):
    """Draws a premium, futuristic face mask (contour outline + iris circles) using thin custom styling."""
    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_face_mesh = mp.solutions.face_mesh

    # Beautiful light neon cyan specs for facial contours
    contour_spec = mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1, circle_radius=1)
    # Beautiful vibrant neon orange specs for irises
    iris_spec = mp_drawing.DrawingSpec(color=(0, 140, 255), thickness=1, circle_radius=1)

    # Draw Face Outline Contours
    mp_drawing.draw_landmarks(
        image=frame,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_CONTOURS,
        landmark_drawing_spec=None,
        connection_drawing_spec=contour_spec
    )
    
    # Draw Irises (eye centers)
    if hasattr(face_landmarks, "landmark") and len(face_landmarks.landmark) >= 478:
        mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_IRISES,
            landmark_drawing_spec=None,
            connection_drawing_spec=iris_spec
        )

def run_face_detection_test():
    """Main visualization test loop for real-time face detection validation."""
    logger.info("Initializing Face Detection Test Runner...")
    
    # Initialize components
    cam_mgr = CameraManager(
        source=config.camera_source,
        width=config.frame_width,
        height=config.frame_height
    )
    detector = FaceDetector()
    extractor = LandmarkExtractor()
    
    # Start Camera thread
    cam_mgr.start()
    
    # Setup window properties
    window_name = "Real-Time Face Landmark Detection Diagnostic"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Timing variables for loop FPS calculations
    last_time = time.time()
    frame_count = 0
    display_fps = 0.0
    
    logger.info("Starting frame processing loop. Press 'q' or 'ESC' to exit.")
    
    try:
        while True:
            # Retrieve frame from threaded camera buffer
            ret, frame = cam_mgr.read()
            if not ret or frame is None:
                # Thread might still be warming up or capturing
                time.sleep(0.01)
                continue
                
            h, w, _ = frame.shape
            
            # Process frame for landmarks
            results = detector.process_frame(frame)
            
            # Extract landmarks if a face mesh is found
            if results and results.multi_face_landmarks:
                # Process the first detected face mesh
                face_landmarks = results.multi_face_landmarks[0]
                features = extractor.extract(face_landmarks, w, h)
                
                if features:
                    # Draw extracted coordinates on top of original BGR frame
                    draw_features(frame, face_landmarks)
                    cv2.putText(frame, "Face Detected", (20, 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "NO Face Detected", (20, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Calculate actual loop processing FPS
            frame_count += 1
            now = time.time()
            elapsed = now - last_time
            if elapsed >= 1.0:
                display_fps = frame_count / elapsed
                frame_count = 0
                last_time = now

            # Overlay performance metrics on display
            camera_fps = cam_mgr.get_fps()
            cv2.putText(frame, f"Processing Loop FPS: {display_fps:.1f}", (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Camera Cap FPS: {camera_fps:.1f}", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

            # Display the rendered output
            cv2.imshow(window_name, frame)
            
            # Check key presses (Wait 1ms)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27: # 27 is ESC key
                logger.info("Exit command detected from user.")
                break
                
    except Exception as e:
        logger.error(f"Unexpected error in test runner: {e}")
        
    finally:
        # Clean resources
        logger.info("Cleaning up face detection test resources...")
        cam_mgr.stop()
        detector.close()
        cv2.destroyAllWindows()
        logger.info("Diagnostics test run closed successfully.")

if __name__ == "__main__":
    run_face_detection_test()
