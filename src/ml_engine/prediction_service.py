import time
from typing import Dict, Any, Optional
from src.db.database_manager import DatabaseManager
from src.ml_engine.fatigue_predictor import FatiguePredictor
from src.utils.logger import logger

class PredictionService:
    """Computes real-time driver biometrics frequencies from database logs and executes fatigue predictions."""
    
    def __init__(self, db_manager: DatabaseManager, predictor: FatiguePredictor):
        self.db = db_manager
        self.predictor = predictor

    def evaluate_session_fatigue(self, session_id: int) -> Dict[str, Any]:
        """
        Queries telemetry logs for the active session, engineers frequency features, and returns predictions.
        
        Returns:
            Dictionary containing prediction labels, probabilities, and engineered features.
        """
        default_res = {
            "fatigue_probability": 0.0,
            "prediction_label": "Unknown",
            "blink_frequency": 0.0,
            "yawn_frequency": 0.0,
            "head_drop_frequency": 0.0,
            "avg_historical_risk": 0.0,
            "ready": False
        }

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                
                # 1. Fetch Session Start Time to calculate duration
                cursor.execute("SELECT start_time FROM sessions WHERE id = ?;", (session_id,))
                row = cursor.fetchone()
                if not row:
                    return default_res
                    
                # Calculate elapsed session minutes (clamp minimum to 1.0 to avoid division spikes at start)
                start_time_str = row["start_time"]
                # SQLite timestamp is in UTC standard or localized format. We approximate elapsed duration in memory.
                # Since we don't have python-datetime parsing issues, we query directly:
                cursor.execute(
                    "SELECT (strftime('%s', 'now') - strftime('%s', start_time)) FROM sessions WHERE id = ?;", 
                    (session_id,)
                )
                duration_sec_row = cursor.fetchone()
                duration_sec = float(duration_sec_row[0]) if duration_sec_row and duration_sec_row[0] else 1.0
                minutes = max(1.0, duration_sec / 60.0)
                
                # 2. Count Blinks (Drowsiness alerts)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM events 
                    WHERE session_id = ? AND event_type IN ('DROWSINESS_WARN', 'DROWSINESS_ALARM');
                    """,
                    (session_id,)
                )
                blink_count = cursor.fetchone()[0]
                
                # 3. Count Yawns
                cursor.execute(
                    "SELECT COUNT(*) FROM events WHERE session_id = ? AND event_type = 'YAWN';",
                    (session_id,)
                )
                yawn_count = cursor.fetchone()[0]
                
                # 4. Count Head Drops (Distractions where pitch is deflected down)
                cursor.execute(
                    "SELECT COUNT(*) FROM events WHERE session_id = ? AND event_type = 'DISTRACTION' AND head_pitch < -12.0;",
                    (session_id,)
                )
                headdrop_count = cursor.fetchone()[0]
                
                # 5. Calculate Average Historical Risk Score
                # We can calculate average risk score by weighting event categories:
                # Normal = 0, Distraction/Yawn = 1, Drowsiness Warn = 2, Drowsiness Alarm = 4
                cursor.execute(
                    """
                    SELECT event_type, COUNT(*) as cnt FROM events 
                    WHERE session_id = ? GROUP BY event_type;
                    """,
                    (session_id,)
                )
                event_counts = {r["event_type"]: r["cnt"] for r in cursor.fetchall()}
                
                total_events = sum(event_counts.values())
                if total_events > 0:
                    weight_sum = (
                        event_counts.get("NORMAL", 0) * 0 +
                        event_counts.get("YAWN", 0) * 1 +
                        event_counts.get("DISTRACTION", 0) * 1 +
                        event_counts.get("DROWSINESS_WARN", 0) * 2 +
                        event_counts.get("DROWSINESS_ALARM", 0) * 4
                    )
                    avg_risk = weight_sum / total_events
                else:
                    avg_risk = 0.0

            # 6. Feature Engineering (convert counts to frequencies per minute)
            blink_freq = blink_count / minutes
            yawn_freq = yawn_count / minutes
            headdrop_freq = headdrop_count / minutes
            
            # 7. Run ML Predictor
            pred_res = self.predictor.predict(blink_freq, yawn_freq, headdrop_freq, avg_risk)
            
            return {
                "fatigue_probability": pred_res["fatigue_probability"],
                "prediction_label": pred_res["prediction_label"],
                "blink_frequency": blink_freq,
                "yawn_frequency": yawn_freq,
                "head_drop_frequency": headdrop_freq,
                "avg_historical_risk": avg_risk,
                "ready": pred_res["ready"]
            }
            
        except Exception as e:
            logger.error(f"PredictionService: Error evaluating session fatigue: {e}")
            return default_res
