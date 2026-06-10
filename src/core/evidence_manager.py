import cv2
import time
from pathlib import Path
from typing import Optional, Dict
from config import config
from src.utils.logger import logger

class EvidenceManager:
    """Captures and persists annotated image frames as safety violation evidence during danger states."""
    
    def __init__(self, evidence_dir: Path = config.db_path.parent / "evidence"):
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Throttling and capping parameters
        self.max_images_per_session = 5
        self.cooldown_seconds = 10.0 # Time buffer between capturing violations
        
        self.session_capture_counts: Dict[int, int] = {}
        self.last_capture_timestamps: Dict[int, float] = {}

    def capture_evidence(
        self,
        frame: cv2.Mat,
        session_id: int,
        event_type: str,
        ear_value: float,
        mar_value: float,
        risk_level: str,
        force: bool = False
    ) -> Optional[Path]:
        """
        Captures, overlays telemetry text, and writes aViolation frame screenshot to disk.
        
        Returns:
            The file Path where the image was saved, or None if skipped (throttled/capped).
        """
        if frame is None or frame.size == 0:
            return None
            
        now = time.time()
        
        # 1. Throttling and session limits checks
        session_count = self.session_capture_counts.get(session_id, 0)
        if not force and session_count >= self.max_images_per_session:
            return None # Capped to save disk space
            
        last_time = self.last_capture_timestamps.get(session_id, 0.0)
        if not force and now - last_time < self.cooldown_seconds:
            return None # Throttled
            
        try:
            # 2. Draw annotations on frame copy
            annotated_frame = frame.copy()
            h, w, _ = annotated_frame.shape
            
            # Semi-transparent overlay block for telemetry readability
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 85), (15, 15, 15), -1)
            cv2.addWeighted(overlay, 0.65, annotated_frame, 0.35, 0, annotated_frame)
            
            # Telemetry text overlay
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated_frame, f"SAFETY VIOLATION CAPTURE - SESSION #{session_id}", (15, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 69, 255), 2, cv2.LINE_AA) # Orange-red header
            
            cv2.putText(annotated_frame, f"Time: {timestamp_str} | Event: {event_type}", (15, 42), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.putText(annotated_frame, f"EAR: {ear_value:.3f} | MAR: {mar_value:.3f} | Risk State: {risk_level.upper()}", (15, 62), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Highlight state boundaries in corner
            state_color = (0, 0, 255) if risk_level == "Critical" else (0, 140, 255)
            cv2.rectangle(annotated_frame, (w - 120, 15), (w - 15, 50), state_color, 2)
            cv2.putText(annotated_frame, risk_level.upper(), (w - 110, 38), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, state_color, 2, cv2.LINE_AA)

            # 3. Write image file to disk
            filename = f"evidence_session_{session_id}_{int(now)}_{event_type}.jpg"
            filepath = self.evidence_dir / filename
            
            success = cv2.imwrite(str(filepath), annotated_frame)
            if success:
                # Update trackers
                self.session_capture_counts[session_id] = session_count + 1
                self.last_capture_timestamps[session_id] = now
                logger.info(f"EvidenceManager: Saved incident screenshot to: {filepath}")
                return filepath
                
            logger.error("EvidenceManager: Failed to write screenshot image file.")
            return None
            
        except Exception as e:
            logger.error(f"EvidenceManager: Screenshot capture error: {e}")
            return None

    def reset_session(self, session_id: int):
        """Clears session violation thresholds tracker."""
        if session_id in self.session_capture_counts:
            del self.session_capture_counts[session_id]
        if session_id in self.last_capture_timestamps:
            del self.last_capture_timestamps[session_id]
