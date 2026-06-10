import cv2
import threading
import time
from typing import Tuple, Union, Optional
from src.utils.logger import logger

class CameraManager:
    """Threaded camera capture class to handle non-blocking webcam frame retrieval."""
    
    def __init__(self, source: Union[int, str] = 0, width: int = 640, height: int = 480):
        self.source = source
        self.width = width
        self.height = height
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame: Optional[cv2.Mat] = None
        self.running = False
        self.started = False
        
        # Thread control
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Diagnostics
        self.fps = 0.0
        self.frame_count = 0
        self.last_fps_time = time.time()

    def start(self) -> 'CameraManager':
        """Starts the background thread to read frames from VideoCapture."""
        if self.started:
            logger.warning("CameraManager is already running.")
            return self
            
        logger.info(f"Initializing camera source: {self.source} ({self.width}x{self.height})")
        self.cap = cv2.VideoCapture(self.source)
        
        # Apply configurations
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Check connection
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera source: {self.source}")
            self.running = False
            return self
            
        # Read initial dummy frame to verify feed
        ret, frame = self.cap.read()
        if not ret or frame is None:
            logger.error("Opened camera source but failed to retrieve first frame.")
            self.running = False
            return self
            
        self.frame = frame
        self.running = True
        self.started = True
        
        # Start thread
        self.thread = threading.Thread(target=self._update_loop, name="CameraGrabberThread", daemon=True)
        self.thread.start()
        logger.info("Camera capture background thread started.")
        return self

    def _update_loop(self):
        """Background thread loop that continuously reads frames."""
        consecutive_failures = 0
        max_failures = 30
        
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                logger.warning("Camera device not opened in loop. Attempting reconnect...")
                if not self._reconnect():
                    time.sleep(2.0)
                    continue
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures % 10 == 0:
                    logger.warning(f"Failed to grab frame. Failure count: {consecutive_failures}/{max_failures}")
                
                if consecutive_failures >= max_failures:
                    logger.error("Too many consecutive frame failures. Initiating reconnect...")
                    self._reconnect()
                    consecutive_failures = 0
                time.sleep(0.01)
                continue
                
            consecutive_failures = 0
            
            # Thread-safe frame update
            with self.lock:
                self.frame = frame
                
            # Track frame rate internally
            self.frame_count += 1
            now = time.time()
            elapsed = now - self.last_fps_time
            if elapsed >= 1.0:
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.last_fps_time = now

            # Small sleep to prevent thread from pinning the CPU core
            time.sleep(0.005)

    def _reconnect(self) -> bool:
        """Attempts to reconnect to the webcam source."""
        logger.info(f"Reconnecting to camera source: {self.source}")
        with self.lock:
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
        if self.cap.isOpened():
            logger.info("Reconnection successful.")
            return True
        logger.warning("Reconnection failed.")
        return False

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        """Returns the latest frame retrieved from the camera thread."""
        with self.lock:
            if self.frame is None:
                return False, None
            # Return copy to avoid race conditions during modifications in main thread
            return True, self.frame.copy()

    def get_fps(self) -> float:
        """Returns the current measured capture frame rate."""
        return self.fps

    def stop(self):
        """Stops the camera thread and releases capture objects."""
        logger.info("Stopping camera manager...")
        self.running = False
        self.started = False
        
        if self.thread is not None:
            self.thread.join(timeout=2.0)
            
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.frame = None
            
        logger.info("Camera manager stopped and camera released.")
