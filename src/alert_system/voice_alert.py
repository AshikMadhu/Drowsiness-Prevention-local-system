import queue
import threading
import time
from typing import Optional
import pyttsx3
from config import config
from src.utils.logger import logger

class VoiceAlert:
    """Asynchronous text-to-speech voice alerting system that operates in a background thread."""
    
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.running = True
        
        # Thread control
        self.worker_thread = threading.Thread(target=self._speech_worker, name="TTSWorkerThread", daemon=True)
        self.worker_thread.start()
        logger.info("VoiceAlert: Background speech worker thread started.")

    def _speech_worker(self):
        """Worker loop that initializes the engine and processes queued speech texts."""
        # Initialize the pyttsx3 engine inside the thread to avoid COM apartment thread issues on Windows
        engine = None
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', config.tts_rate)
            engine.setProperty('volume', config.tts_volume)
            
            # Select voice index if available
            voices = engine.getProperty('voices')
            voice_index = config.tts_voice_index
            if voices and 0 <= voice_index < len(voices):
                engine.setProperty('voice', voices[voice_index].id)
                
        except Exception as e:
            logger.error(f"VoiceAlert: Failed to initialize pyttsx3 voice engine in worker thread: {e}")
            self.running = False
            return

        while self.running:
            try:
                # Wait for a speech request (with timeout to check self.running flag)
                text = self.speech_queue.get(timeout=1.0)
                
                # Check for shutdown signal
                if text is None:
                    self.speech_queue.task_done()
                    break
                    
                # Execute speech blocks
                try:
                    logger.info(f"VoiceAlert speaking: '{text}'")
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"VoiceAlert: Speech engine execution error: {e}")
                finally:
                    self.speech_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"VoiceAlert: Worker loop exception: {e}")
                time.sleep(1.0)

        # Cleanup
        try:
            del engine
            logger.info("VoiceAlert: Speech worker cleanup complete.")
        except Exception as e:
            logger.error(f"VoiceAlert: Error deleting speech engine: {e}")

    def speak(self, text: str, clear_queue: bool = True):
        """
        Enqueues a text string to be spoken asynchronously.
        
        Args:
            text: The alert message string to speak
            clear_queue: If True, flushes all pending speech requests before speaking the new one
        """
        if not self.running:
            return
            
        if clear_queue:
            # Drain queue elements
            try:
                while True:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
            except queue.Empty:
                pass
                
        self.speech_queue.put(text)

    def stop(self):
        """Stops the speech worker thread and cancels pending requests."""
        logger.info("VoiceAlert: Initiating voice alert shutdown...")
        self.running = False
        # Push shutdown signal to unblock queue
        self.speech_queue.put(None)
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
            
    def __del__(self):
        self.stop()
