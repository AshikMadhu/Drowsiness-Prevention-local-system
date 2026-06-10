from datetime import datetime
from typing import Dict, Any, Optional
from src.db.database_manager import DatabaseManager
from src.utils.logger import logger

class EventLogger:
    """Handles persistence of driver sessions, alert events, and telemetry logs in SQLite."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def start_session(self, user_id: int) -> Optional[int]:
        """
        Registers a new driver session in the database.
        
        Returns:
            The unique integer session_id, or None if creation fails.
        """
        query = "INSERT INTO sessions (user_id, status) VALUES (?, 'ACTIVE');"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id,))
                session_id = cursor.lastrowid
                logger.info(f"Database: Started active driving session ID: {session_id} for user ID: {user_id}")
                return session_id
        except Exception as e:
            logger.error(f"Database: Failed to start session for user {user_id}: {e}")
            return None

    def end_session(self, session_id: int, status: str = "COMPLETED") -> bool:
        """
        Marks an active session as completed or aborted, logging the current timestamp.
        """
        query = "UPDATE sessions SET end_time = CURRENT_TIMESTAMP, status = ? WHERE id = ?;"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (status, session_id))
                logger.info(f"Database: Closed driving session ID: {session_id} with status: {status}")
                return True
        except Exception as e:
            logger.error(f"Database: Failed to close session ID {session_id}: {e}")
            return False

    def log_event(
        self,
        session_id: int,
        event_type: str,
        ear_value: float,
        mar_value: float,
        pitch: float,
        yaw: float,
        roll: float,
        action_taken: str,
        confidence_score: float = 1.0
    ) -> Optional[int]:
        """
        Logs a single safety/drowsiness alert event with facial telemetry.
        """
        query = """
        INSERT INTO events (
            session_id, event_type, confidence_score, ear_value, mar_value, 
            head_pitch, head_yaw, head_roll, action_taken
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (session_id, event_type, confidence_score, ear_value, mar_value,
                     pitch, yaw, roll, action_taken)
                )
                event_id = cursor.lastrowid
                
                # Automatically increment session alert counters
                self._update_session_counters(cursor, session_id, event_type)
                
                return event_id
        except Exception as e:
            logger.error(f"Database: Failed to log alert event for session ID {session_id}: {e}")
            return None

    def _update_session_counters(self, cursor: Any, session_id: int, event_type: str):
        """Internal helper to increment alert statistics inside SQLite transaction."""
        if event_type in ("DROWSINESS_WARN", "DROWSINESS_ALARM"):
            query = "UPDATE sessions SET total_drowsiness_alerts = total_drowsiness_alerts + 1 WHERE id = ?;"
            cursor.execute(query, (session_id,))
        elif event_type == "DISTRACTION":
            query = "UPDATE sessions SET total_distraction_alerts = total_distraction_alerts + 1 WHERE id = ?;"
            cursor.execute(query, (session_id,))

    def get_session_stats(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves aggregated stats and telemetry details of a single session.
        """
        query = """
        SELECT 
            id, user_id, start_time, end_time, 
            total_drowsiness_alerts, total_distraction_alerts, status
        FROM sessions WHERE id = ?;
        """
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (session_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Database: Failed to fetch statistics for session ID {session_id}: {e}")
            return None
