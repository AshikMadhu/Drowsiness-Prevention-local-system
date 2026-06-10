import sys
import os
import shutil
import numpy as np
from pathlib import Path

# Add root folder to python path to resolve imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import config
from src.db.database_manager import DatabaseManager
from src.db.event_logger import EventLogger
from src.cv_engine.face_recognition import FaceRecognizer
from src.core.evidence_manager import EvidenceManager
from src.utils.report_generator import ReportGenerator

# Define a mock facial landmark list representing a face structure (468 points)
def generate_mock_landmarks(scale_factor: float = 1.0) -> list:
    landmarks = []
    # Seed 3D coordinate tuples: (x, y, z)
    # Standard indices: 10, 152, 234, 454, 33, 263, 1, 13, 58, 288, 78, 308
    # We populate all 468 landmarks with dummy coordinates, adjusting keys for scale variance
    for idx in range(480):
        # Default coordinates
        x, y, z = 0.5, 0.5, 0.0
        
        # Override specific key indices to build a geometric pattern
        if idx == 10:  # Forehead
            y = 0.2
        elif idx == 152: # Chin
            y = 0.8 * scale_factor
        elif idx == 234: # Left Cheek
            x = 0.3
        elif idx == 454: # Right Cheek
            x = 0.7 * scale_factor
        elif idx == 33:  # Right Eye
            x = 0.4
            y = 0.35
        elif idx == 263: # Left Eye
            x = 0.6
            y = 0.35
        elif idx == 1:   # Nose
            x = 0.5
            y = 0.5
        elif idx == 13:  # Mouth center
            x = 0.5
            y = 0.6
            
        landmarks.append((x, y, z))
        
    return landmarks

def run_advanced_features_test():
    print("=" * 60)
    print("    ADVANCED FEATURES INTEGRATION & DIAGNOSTICS RUNNER   ")
    print("=" * 60)
    
    # Setup temp paths
    temp_dir = BASE_DIR / "data" / "test_advanced_violation"
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to clear old temp dir: {e}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    test_db_path = temp_dir / "test_driver_safety.db"
    test_json_path = temp_dir / "registered_faces.json"
    
    # Override config path
    config.db_path = test_db_path
    
    # ----------------------------------------------------
    # TEST 1: Driver Face Recognition
    # ----------------------------------------------------
    print("\n[*] Test 1: Driver Face Recognition Verification...")
    recognizer = FaceRecognizer(registry_path=test_json_path)
    
    # Generate signature landmarks
    driver_a_landmarks = generate_mock_landmarks(scale_factor=1.0)
    driver_b_landmarks = generate_mock_landmarks(scale_factor=1.15) # scaled cheek/chin distance
    
    # Register Driver A
    reg_success = recognizer.register_driver("driver_alpha", driver_a_landmarks)
    assert reg_success is True, "Failed to register driver_alpha."
    
    # Identify using same coordinates
    match_1 = recognizer.identify_driver(driver_a_landmarks)
    assert match_1 == "driver_alpha", f"Expected 'driver_alpha', got '{match_1}'"
    print("  [OK] Registered face signature correctly identified.")
    
    # Identify using different coordinates (unregistered face)
    match_2 = recognizer.identify_driver(driver_b_landmarks)
    assert match_2 == "Unknown", f"Expected 'Unknown' (unregistered face spacing), got '{match_2}'"
    print("  [OK] Unregistered / different face structure correctly classified as 'Unknown'.")

    # ----------------------------------------------------
    # TEST 2: Screenshot Evidence Capture
    # ----------------------------------------------------
    print("\n[*] Test 2: Screenshot Evidence Capture Verification...")
    evidence_dir = temp_dir / "evidence"
    evidence_mgr = EvidenceManager(evidence_dir=evidence_dir)
    
    # Create dummy black BGR image frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Capture incident screenshots
    violation_path = evidence_mgr.capture_evidence(
        dummy_frame, 
        session_id=99, 
        event_type="DROWSINESS_ALARM", 
        ear_value=0.14, 
        mar_value=0.12, 
        risk_level="Critical"
    )
    
    assert violation_path is not None, "Failed to capture/write screenshot evidence."
    assert violation_path.exists(), f"Violation file does not exist at: {violation_path}"
    print(f"  [OK] Telemetry overlays processed. Violation file saved: {violation_path.name}")

    # ----------------------------------------------------
    # TEST 3: SQLite Statistics Report Compilation
    # ----------------------------------------------------
    print("\n[*] Test 3: Session Report Compilation (PDF/HTML)...")
    db_mgr = DatabaseManager(db_path=test_db_path)
    event_logger = EventLogger(db_mgr)
    report_gen = ReportGenerator(db_mgr, reports_dir=temp_dir / "reports")
    
    # Register mock session and event logs in database
    with db_mgr.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES ('diagnostic_driver_A');")
        user_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO sessions (user_id, status) VALUES (?, 'COMPLETED');", (user_id,))
        session_id = cursor.lastrowid
        
        cursor.execute(
            """
            INSERT INTO events (session_id, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken)
            VALUES (?, 'DROWSINESS_WARN', 0.18, 0.15, 0.0, 0.0, 'TTS_WARNING');
            """,
            (session_id,)
        )
        cursor.execute(
            """
            INSERT INTO events (session_id, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken)
            VALUES (?, 'DISTRACTION', 0.28, 0.12, 0.0, 22.0, 'TTS_DISTRACTION');
            """,
            (session_id,)
        )
        cursor.execute(
            """
            UPDATE sessions 
            SET total_drowsiness_alerts = 1, total_distraction_alerts = 1, end_time = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (session_id,)
        )
        
    # Generate report
    report_path = report_gen.generate_report(session_id)
    assert report_path is not None, "Report generation returned None."
    assert report_path.exists(), f"Report file does not exist at: {report_path}"
    print(f"  [OK] Report compiled successfully. File saved: {report_path.name}")
    
    # Clean up test directories
    print("\n[*] Cleaning up test directories...")
    try:
        shutil.rmtree(temp_dir)
        print("  [OK] Temporary directory cleaned.")
    except Exception as e:
        print(f"Warning: Failed to clean up: {e}")
        
    print("\n" + "=" * 50)
    print("      ADVANCED FEATURES TESTS COMPLETED SUCCESSFULLY    ")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    run_advanced_features_test()
