import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from src.utils.logger import logger

# Landmark indices mapping in MediaPipe Face Mesh (468/478 landmarks)
# 6-point Left Eye EAR indices
LEFT_EYE_INDICES = [362, 385, 386, 263, 374, 380] # Corner1, Top1, Top2, Corner2, Bottom1, Bottom2
# 6-point Right Eye EAR indices
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]   # Corner1, Top1, Top2, Corner2, Bottom1, Bottom2

# Inner lip indices for Yawn Detection (MAR)
MOUTH_INDICES = [78, 81, 13, 311, 308, 178, 14, 402] # LeftCorner, TopLeft, TopCenter, TopRight, RightCorner, BottomRight, BottomCenter, BottomLeft

# Iris tracking indices (requires refine_landmarks=True)
LEFT_IRIS_INDICES = [474, 475, 476, 477]
RIGHT_IRIS_INDICES = [469, 470, 471, 472]

# Key points for 3D Head Pose estimation (6 points)
# 1. Nose Tip (1)
# 2. Chin (152)
# 3. Left Eye Outer Corner (263)
# 4. Right Eye Outer Corner (33)
# 5. Left Mouth Corner (308)
# 6. Right Mouth Corner (78)
HEAD_POSE_INDICES = [1, 152, 263, 33, 308, 78]

class LandmarkExtractor:
    """Extracts and organizes facial landmarks from MediaPipe results into pixel coordinates."""
    
    @staticmethod
    def to_pixel_coords(landmark: Any, img_width: int, img_height: int) -> Tuple[int, int, float]:
        """Converts normalized landmark coordinates into absolute pixel coordinates."""
        px = min(int(landmark.x * img_width), img_width - 1)
        py = min(int(landmark.y * img_height), img_height - 1)
        pz = landmark.z  # Keep depth coordinate as-is
        return (px, py, pz)

    def extract(self, face_landmarks: Any, img_width: int, img_height: int) -> Optional[Dict[str, Any]]:
        """
        Parses Face Mesh landmarks and extracts subgroups for eyes, mouth, iris, and head pose.
        
        Args:
            face_landmarks: MediaPipe normalized face landmarks
            img_width: Width of the processed frame
            img_height: Height of the processed frame
            
        Returns:
            Dictionary containing mapped feature groups, or None if input landmarks are invalid.
        """
        if face_landmarks is None:
            return None
            
        try:
            landmarks_list = face_landmarks.landmark
            num_landmarks = len(landmarks_list)
            
            # Extract all coordinates as pixel integers/floats
            all_pixels = [
                self.to_pixel_coords(lm, img_width, img_height) for lm in landmarks_list
            ]
            
            # Helper to map a list of indices to pixel coordinate points
            def map_indices(indices: List[int]) -> List[Tuple[int, int]]:
                coords = []
                for idx in indices:
                    if idx < num_landmarks:
                        # Extract x, y from pixel tuple
                        coords.append((all_pixels[idx][0], all_pixels[idx][1]))
                return coords

            # Build extracted features map
            features = {
                "all_landmarks": all_pixels,
                "left_eye": map_indices(LEFT_EYE_INDICES),
                "right_eye": map_indices(RIGHT_EYE_INDICES),
                "mouth": map_indices(MOUTH_INDICES),
                "head_pose_points": map_indices(HEAD_POSE_INDICES)
            }
            
            # Extract irises if available (MediaPipe Face Mesh Refine Landmarks mode)
            if num_landmarks >= 478:
                features["left_iris"] = map_indices(LEFT_IRIS_INDICES)
                features["right_iris"] = map_indices(RIGHT_IRIS_INDICES)
                
                # Calculate pupil centers as the centroid of iris landmarks
                features["left_pupil"] = self._calculate_centroid(features["left_iris"])
                features["right_pupil"] = self._calculate_centroid(features["right_iris"])
            else:
                features["left_iris"] = []
                features["right_iris"] = []
                features["left_pupil"] = None
                features["right_pupil"] = None
                
            return features
            
        except Exception as e:
            logger.error(f"Error extracting landmarks: {e}")
            return None

    def _calculate_centroid(self, points: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Calculates the center point of a group of coordinates."""
        if not points:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (int(sum(xs) / len(points)), int(sum(ys) / len(points)))
