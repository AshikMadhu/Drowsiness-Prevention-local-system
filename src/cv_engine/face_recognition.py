import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from config import config
from src.utils.logger import logger

class FaceRecognizer:
    """Landmark-based geometric face recognition for driver registration and identification."""
    
    def __init__(self, registry_path: Path = config.db_path.parent / "registered_faces.json"):
        self.registry_path = registry_path
        self.registry: Dict[str, List[float]] = {}
        self.recognition_threshold = 0.065 # Maximum Euclidean distance variance allowed
        self.load_registry()

    def load_registry(self):
        """Loads registered driver face vectors from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as file:
                    self.registry = json.load(file)
                logger.info(f"FaceRecognizer: Mapped {len(self.registry)} registered drivers from JSON.")
            except Exception as e:
                logger.error(f"FaceRecognizer: Failed to load registry: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self):
        """Saves registered driver face vectors to JSON file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.registry_path, 'w') as file:
                json.dump(self.registry, file, indent=4)
            logger.info(f"FaceRecognizer: Saved driver registry updates to: {self.registry_path}")
        except Exception as e:
            logger.error(f"FaceRecognizer: Failed to save registry: {e}")

    def _euclidean_distance_3d(self, p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        """Calculates 3D Euclidean distance between two landmarks."""
        return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2))

    def extract_face_signature(self, landmarks: List[Tuple[int, int, float]]) -> Optional[List[float]]:
        """
        Extracts a normalized 8-dimensional geometric ratio vector representing facial structure.
        Uses normalized coordinate depth to ensure scale invariance.
        
        Key landmarks indices:
          - 10: Forehead Center
          - 152: Chin Center
          - 234: Left Cheek Outer
          - 454: Right Cheek Outer
          - 33: Right Eye Corner Outer (viewer's left)
          - 263: Left Eye Corner Outer (viewer's right)
          - 1: Nose Tip
          - 13: Inner Upper Lip
          - 58: Left Jaw Outer
          - 288: Right Jaw Outer
          - 78: Right Mouth Corner
          - 308: Left Mouth Corner
        """
        if len(landmarks) < 468:
            return None

        try:
            # 1. Base Scale: Forehead to Chin vertical distance (normalization factor)
            base_scale = self._euclidean_distance_3d(landmarks[10], landmarks[152])
            if base_scale < 1e-6:
                return None

            # 2. Extract key distances
            d_cheek_width = self._euclidean_distance_3d(landmarks[234], landmarks[454])
            d_eye_spacing = self._euclidean_distance_3d(landmarks[33], landmarks[263])
            d_nose_to_lip = self._euclidean_distance_3d(landmarks[1], landmarks[13])
            d_mouth_width = self._euclidean_distance_3d(landmarks[78], landmarks[308])
            d_jaw_width = self._euclidean_distance_3d(landmarks[58], landmarks[288])
            
            # Cross-face vertical segments
            d_eye_to_mouth_left = self._euclidean_distance_3d(landmarks[263], landmarks[308])
            d_eye_to_mouth_right = self._euclidean_distance_3d(landmarks[33], landmarks[78])
            d_nose_to_chin = self._euclidean_distance_3d(landmarks[1], landmarks[152])

            # 3. Compute normalized ratios
            feature_vector = [
                d_cheek_width / base_scale,
                d_eye_spacing / base_scale,
                d_nose_to_lip / base_scale,
                d_mouth_width / base_scale,
                d_jaw_width / base_scale,
                d_eye_to_mouth_left / base_scale,
                d_eye_to_mouth_right / base_scale,
                d_nose_to_chin / base_scale
            ]
            return feature_vector
        except Exception as e:
            logger.error(f"FaceRecognizer: Feature extraction error: {e}")
            return None

    def register_driver(self, username: str, landmarks: List[Tuple[int, int, float]]) -> bool:
        """
        Registers a driver's facial structure signature.
        """
        signature = self.extract_face_signature(landmarks)
        if signature is None:
            logger.warning(f"FaceRecognizer: Could not register '{username}'. Facial features invalid.")
            return False
            
        self.registry[username] = signature
        self.save_registry()
        logger.info(f"FaceRecognizer: Driver '{username}' registered successfully.")
        return True

    def identify_driver(self, landmarks: List[Tuple[int, int, float]]) -> str:
        """
        Compares the current face signature against registered profiles.
        
        Returns:
            Registered username if recognized, otherwise returns 'Unknown'.
        """
        current_sig = self.extract_face_signature(landmarks)
        if current_sig is None or not self.registry:
            return "Unknown"

        best_match = "Unknown"
        min_distance = float('inf')

        # Compare signature vectors using Euclidean distance
        for username, reg_sig in self.registry.items():
            dist = float(np.linalg.norm(np.array(current_sig) - np.array(reg_sig)))
            
            if dist < min_distance:
                min_distance = dist
                if dist < self.recognition_threshold:
                    best_match = username

        logger.debug(f"FaceRecognizer: Identification result: '{best_match}' (dist: {min_distance:.4f})")
        return best_match
