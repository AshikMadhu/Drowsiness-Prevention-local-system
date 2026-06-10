import cv2
import mediapipe as mp
from typing import Optional, NamedTuple
from config import config
from src.utils.logger import logger

class FaceDetector:
    """Wraps MediaPipe Face Mesh to perform real-time facial landmark detection."""
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Load settings from global configuration
        mp_config = config.mediapipe_settings
        self.static_image_mode = mp_config.get("static_image_mode", False)
        self.max_num_faces = mp_config.get("max_num_faces", 1)
        self.refine_landmarks = mp_config.get("refine_landmarks", True)
        self.min_detection_confidence = mp_config.get("min_detection_confidence", 0.5)
        self.min_tracking_confidence = mp_config.get("min_tracking_confidence", 0.5)
        
        self.face_mesh: Optional[mp.solutions.face_mesh.FaceMesh] = None
        self._initialize_mesh()

    def _initialize_mesh(self):
        """Initializes the MediaPipe Face Mesh object."""
        try:
            logger.info("Initializing MediaPipe Face Mesh engine...")
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=self.static_image_mode,
                max_num_faces=self.max_num_faces,
                refine_landmarks=self.refine_landmarks,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            logger.info("MediaPipe Face Mesh successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Face Mesh: {e}")
            raise

    def process_frame(self, frame: cv2.Mat) -> Optional[NamedTuple]:
        """
        Processes a BGR image frame and returns detected face mesh landmarks.
        
        Args:
            frame: cv2.Mat (BGR format OpenCV frame)
            
        Returns:
            MediaPipe face mesh detection output structure, or None if error/no detection.
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty or invalid frame passed to FaceDetector.")
            return None
            
        if self.face_mesh is None:
            logger.error("Face Mesh engine is not initialized.")
            return None

        try:
            # MediaPipe processes images in RGB format. Convert BGR to RGB.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Lock the prediction step inside MediaPipe process call
            results = self.face_mesh.process(rgb_frame)
            return results
        except Exception as e:
            logger.error(f"Error during MediaPipe frame processing: {e}")
            return None

    def close(self):
        """Closes the MediaPipe Face Mesh resource."""
        if self.face_mesh is not None:
            logger.info("Releasing MediaPipe Face Mesh resources...")
            try:
                self.face_mesh.close()
                self.face_mesh = None
                logger.info("MediaPipe Face Mesh resources released.")
            except Exception as e:
                logger.error(f"Error while closing Face Mesh: {e}")
                
    def __del__(self):
        # Fallback to make sure resources are freed
        self.close()
