import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Base Directory definition
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class ConfigurationError(Exception):
    """Exception raised for errors in configuration loading."""
    pass

class Config:
    """Centralized configuration manager supporting YAML & Environment overrides."""
    
    def __init__(self, yaml_path: Path = BASE_DIR / "config" / "config.yaml"):
        self.yaml_path = yaml_path
        self._config_data = {}
        
        # Load from YAML if exists
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r') as file:
                    self._config_data = yaml.safe_load(file) or {}
            except Exception as e:
                raise ConfigurationError(f"Failed to parse configuration YAML: {e}")
        else:
            # Fallback configuration
            self._config_data = {
                "system": {"debug_mode": True, "log_level": "INFO", "camera_source": 0},
                "cv_engine": {"mediapipe": {"min_detection_confidence": 0.5}},
                "algorithms": {"calibration_frames": 100, "eye_closure_warn_time": 1.2, "eye_closure_alarm_time": 2.2},
                "audio": {"sound": {}, "tts": {"rate": 150, "volume": 1.0}},
                "database": {"db_path": "data/driver_safety.db"}
            }

        self._initialize_directories()
        self._apply_env_overrides()

    def _initialize_directories(self):
        """Pre-creates directories for log, database, and asset storage if they do not exist."""
        directories = [
            BASE_DIR / "logs",
            BASE_DIR / "data",
            BASE_DIR / "data" / "models",
            BASE_DIR / "data" / "audio"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _apply_env_overrides(self):
        """Applies environment variables overrides on top of loaded YAML."""
        # Camera overrides
        env_camera = os.getenv("CAMERA_SOURCE")
        if env_camera is not None:
            # Try to convert to int if it represents an index
            try:
                self._config_data["system"]["camera_source"] = int(env_camera)
            except ValueError:
                self._config_data["system"]["camera_source"] = env_camera

        # Logging level
        env_log_level = os.getenv("LOG_LEVEL")
        if env_log_level:
            self._config_data["system"]["log_level"] = env_log_level
            
        # Log path
        env_log_path = os.getenv("LOG_FILE_PATH")
        if env_log_path:
            self._config_data["system"]["log_file_path"] = env_log_path

        # Database path
        env_db_path = os.getenv("DATABASE_PATH")
        if env_db_path:
            self._config_data["database"]["db_path"] = env_db_path

        # Thresholds & Calibration
        env_calib = os.getenv("CALIBRATION_FRAMES")
        if env_calib:
            self._config_data["algorithms"]["calibration_frames"] = int(env_calib)

    @property
    def debug_mode(self) -> bool:
        return bool(self._config_data.get("system", {}).get("debug_mode", True))

    @property
    def log_level(self) -> str:
        return str(self._config_data.get("system", {}).get("log_level", "INFO"))

    @property
    def log_file_path(self) -> Path:
        path_str = self._config_data.get("system", {}).get("log_file_path", "logs/driver_safety.log")
        return BASE_DIR / path_str

    @property
    def camera_source(self):
        source = self._config_data.get("system", {}).get("camera_source", 0)
        return source

    @property
    def frame_width(self) -> int:
        return int(self._config_data.get("system", {}).get("frame_width", 640))

    @property
    def frame_height(self) -> int:
        return int(self._config_data.get("system", {}).get("frame_height", 480))

    @property
    def db_path(self) -> Path:
        path_str = self._config_data.get("database", {}).get("db_path", "data/driver_safety.db")
        return BASE_DIR / path_str

    @db_path.setter
    def db_path(self, value):
        if "database" not in self._config_data:
            self._config_data["database"] = {}
        # If it's a Path object, convert it to a string.
        # If it is absolute, try to store it relative to BASE_DIR if possible, otherwise store as absolute string.
        if isinstance(value, Path):
            try:
                self._config_data["database"]["db_path"] = str(value.relative_to(BASE_DIR))
            except ValueError:
                self._config_data["database"]["db_path"] = str(value)
        else:
            self._config_data["database"]["db_path"] = str(value)

    @property
    def calibration_frames(self) -> int:
        return int(self._config_data.get("algorithms", {}).get("calibration_frames", 100))

    @property
    def ear_threshold(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("ear_threshold", 0.22))

    @property
    def mar_threshold(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("mar_threshold", 0.50))

    @property
    def gaze_threshold(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("gaze_threshold", 15.0))

    @property
    def eye_closure_warn_time(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("eye_closure_warn_time", 1.2))

    @property
    def eye_closure_alarm_time(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("eye_closure_alarm_time", 2.2))

    @property
    def yawn_warn_time(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("yawn_warn_time", 2.5))

    @property
    def distraction_warn_time(self) -> float:
        return float(self._config_data.get("algorithms", {}).get("distraction_warn_time", 3.0))

    @property
    def sound_warning_chime(self) -> Path:
        path_str = self._config_data.get("audio", {}).get("sound", {}).get("warning_chime", "data/audio/warning_chime.wav")
        return BASE_DIR / path_str

    @property
    def sound_critical_alarm(self) -> Path:
        path_str = self._config_data.get("audio", {}).get("sound", {}).get("critical_alarm", "data/audio/critical_alarm.wav")
        return BASE_DIR / path_str

    @property
    def tts_rate(self) -> int:
        return int(self._config_data.get("audio", {}).get("tts", {}).get("rate", 150))

    @property
    def tts_volume(self) -> float:
        return float(self._config_data.get("audio", {}).get("tts", {}).get("volume", 1.0))

    @property
    def tts_voice_index(self) -> int:
        return int(self._config_data.get("audio", {}).get("tts", {}).get("voice_index", 0))

    @property
    def mediapipe_settings(self) -> dict:
        return self._config_data.get("cv_engine", {}).get("mediapipe", {})

# Instantiate global configuration object
config = Config()
