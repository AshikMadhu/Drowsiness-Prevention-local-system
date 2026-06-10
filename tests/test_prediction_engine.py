import sys
import os
import shutil
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Add root folder to python path to resolve imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import config
from src.db.database_manager import DatabaseManager
from src.db.event_logger import EventLogger
from src.ml_engine.fatigue_predictor import FatiguePredictor
from src.ml_engine.prediction_service import PredictionService

def run_prediction_test():
    print("=" * 60)
    print("    FATIGUE PREDICTOR ML INTEGRATION & DIAGNOSTICS   ")
    print("=" * 60)
    
    # Setup temp directories
    temp_dir = BASE_DIR / "data" / "test_prediction_violation"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    test_db_path = temp_dir / "test_driver_safety.db"
    
    # Override configuration
    config.db_path = test_db_path
    
    # ----------------------------------------------------
    # TEST 1: Model Calibration (Quick training)
    # ----------------------------------------------------
    print("\n[*] Test 1: Programmatic Model Calibration & Saving...")
    predictor = FatiguePredictor(model_dir=temp_dir / "models")
    
    # Generate tiny training set for diagnostics speed
    np.random.seed(42)
    X_train = np.random.normal(loc=2.0, scale=1.0, size=(100, 4)) # Normal attentive features
    X_train_fatigue = np.random.normal(loc=10.0, scale=2.0, size=(100, 4)) # Fatigued features
    X = np.vstack([X_train, X_train_fatigue])
    y = np.concatenate([np.zeros(100), np.ones(100)])
    
    # Train scaler and models
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model_lr = LogisticRegression()
    model_lr.fit(X_scaled, y)
    
    model_rf = RandomForestClassifier(n_estimators=10)
    model_rf.fit(X_scaled, y)
    
    # Save weights
    predictor.save_weights(scaler, model_lr, model_rf)
    assert predictor.models_loaded is True, "Failed to load models after saving."
    print("  [OK] Scaler and Scikit-Learn weights successfully calibrated and saved.")

    # ----------------------------------------------------
    # TEST 2: Prediction Service & Feature Engineering
    # ----------------------------------------------------
    print("\n[*] Test 2: Telemetry Feature Engineering & Predictions...")
    db_mgr = DatabaseManager(db_path=test_db_path)
    event_logger = EventLogger(db_mgr)
    pred_service = PredictionService(db_mgr, predictor)
    
    # Setup mock session and write telemetry events to SQLite
    with db_mgr.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES ('test_ml_driver');")
        user_id = cursor.lastrowid
        
        # Insert a session started 2 minutes ago (120 seconds) to verify frequency math
        # strftime('%Y-%m-%d %H:%M:%S', 'datetime("now", "-120 seconds")')
        cursor.execute(
            """
            INSERT INTO sessions (user_id, status, start_time) 
            VALUES (?, 'ACTIVE', datetime('now', '-120 seconds'));
            """, 
            (user_id,)
        )
        session_id = cursor.lastrowid
        
        # Log event violations (10 eye closures, 4 yawns, 2 head drops)
        # 1. 10 Eye closures (drowsiness alerts)
        for _ in range(10):
            cursor.execute(
                """
                INSERT INTO events (session_id, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken)
                VALUES (?, 'DROWSINESS_WARN', 0.16, 0.12, 0.0, 0.0, 'TTS_WARNING');
                """,
                (session_id,)
            )
            
        # 2. 4 Yawns
        for _ in range(4):
            cursor.execute(
                """
                INSERT INTO events (session_id, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken)
                VALUES (?, 'YAWN', 0.28, 0.65, 0.0, 0.0, 'TTS_YAWN_WARNING');
                """,
                (session_id,)
            )
            
        # 3. 2 Head drops (distraction where pitch < -12.0)
        for _ in range(2):
            cursor.execute(
                """
                INSERT INTO events (session_id, event_type, ear_value, mar_value, head_pitch, head_yaw, action_taken)
                VALUES (?, 'DISTRACTION', 0.28, 0.12, -15.0, 0.0, 'TTS_DISTRACTION_WARNING');
                """,
                (session_id,)
            )
            
        # Force a database update
        cursor.execute(
            "UPDATE sessions SET total_drowsiness_alerts = 10, total_distraction_alerts = 2 WHERE id = ?;",
            (session_id,)
        )

    # Execute prediction service evaluation
    pred_res = pred_service.evaluate_session_fatigue(session_id)
    
    assert pred_res["ready"] is True, "Prediction Service reported ready=False."
    
    # Assert frequency calculations:
    # 2 minutes duration -> Freq = Count / 2
    # Blinks: 10 / 2 = 5.0
    # Yawns: 4 / 2 = 2.0
    # Head drops: 2 / 2 = 1.0
    print(f"  Calculated Blink Frequency:    {pred_res['blink_frequency']:.2f} blinks/min (Expected: ~5.0)")
    print(f"  Calculated Yawn Frequency:     {pred_res['yawn_frequency']:.2f} yawns/min (Expected: ~2.0)")
    print(f"  Calculated Head Drop Freq:     {pred_res['head_drop_frequency']:.2f} drops/min (Expected: ~1.0)")
    print(f"  Calculated Avg Session Risk:   {pred_res['avg_historical_risk']:.2f}")
    
    # Check bounds
    assert abs(pred_res["blink_frequency"] - 5.0) < 0.8, "Blink frequency calculation error."
    assert abs(pred_res["yawn_frequency"] - 2.0) < 0.5, "Yawn frequency calculation error."
    assert abs(pred_res["head_drop_frequency"] - 1.0) < 0.5, "Head drop frequency calculation error."
    
    print(f"  Predictor Classification:      {pred_res['prediction_label']}")
    print(f"  Fatigue Probability Score:     {pred_res['fatigue_probability'] * 100:.1f}%")
    print("  [OK] Feature engineering and model probability output pass validation checks.")
    
    # Clean up test directories
    print("\n[*] Cleaning up test directories...")
    try:
        shutil.rmtree(temp_dir)
        print("  [OK] Temporary directory cleaned.")
    except Exception as e:
        print(f"Warning: Failed to clean up: {e}")
        
    print("\n" + "=" * 50)
    print("       PREDICTOR ENGINE DIAGNOSTICS SUCCESSFUL      ")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    run_prediction_test()
