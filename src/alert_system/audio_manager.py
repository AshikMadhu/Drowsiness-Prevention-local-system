import pygame
from pathlib import Path
from config import config
from src.utils.logger import logger

class AudioManager:
    """Manages playing warning chimes and continuous alarm tones using Pygame Mixer."""
    
    def __init__(self):
        self.mixer_initialized = False
        self.warning_sound = None
        self.critical_sound = None
        
        # Audio tracks channel allocation
        self.warning_channel = None
        self.critical_channel = None
        
        self.current_volume = config.tts_volume
        self.initialize_mixer()

    def initialize_mixer(self):
        """Initializes the pygame audio mixer and pre-loads sound objects."""
        try:
            logger.info("Initializing Pygame Audio Mixer...")
            # Initialize with standard sample rate, bit size, channels, and buffer size
            pygame.mixer.init(44100, -16, 2, 512)
            self.mixer_initialized = True
            
            # Load assets if they exist
            self._load_sounds()
            logger.info("Pygame Audio Mixer successfully initialized.")
        except Exception as e:
            logger.warning(f"Audio Manager: Failed to initialize Pygame Mixer: {e}. Sounds will be bypassed.")
            self.mixer_initialized = False

    def _load_sounds(self):
        """Loads WAV sound files from data directory."""
        if not self.mixer_initialized:
            return
            
        warning_path = config.sound_warning_chime
        critical_path = config.sound_critical_alarm
        
        # Load warning chime
        if warning_path.exists():
            try:
                self.warning_sound = pygame.mixer.Sound(str(warning_path))
                self.warning_sound.set_volume(self.current_volume)
            except Exception as e:
                logger.error(f"Audio Manager: Error loading warning chime '{warning_path}': {e}")
        else:
            logger.warning(f"Audio Manager: Warning chime asset not found at: {warning_path}")

        # Load critical alarm
        if critical_path.exists():
            try:
                self.critical_sound = pygame.mixer.Sound(str(critical_path))
                self.critical_sound.set_volume(self.current_volume)
            except Exception as e:
                logger.error(f"Audio Manager: Error loading critical alarm '{critical_path}': {e}")
        else:
            logger.warning(f"Audio Manager: Critical alarm asset not found at: {critical_path}")

    def play_warning_chime(self):
        """Plays a single warning chime alert."""
        if not self.mixer_initialized or not self.warning_sound:
            return
            
        try:
            # Play warning chime (automatically allocated to any free channel)
            self.warning_sound.play(loops=0)
        except Exception as e:
            logger.error(f"Audio Manager: Failed to play warning sound: {e}")

    def play_critical_alarm(self):
        """Plays the critical alarm tone on loop if not already playing."""
        if not self.mixer_initialized or not self.critical_sound:
            return
            
        try:
            # Check if critical alarm is not already playing to prevent overlapping loops
            if self.critical_sound.get_num_channels() == 0:
                logger.info("Audio Manager: Starting continuous critical alarm loop.")
                self.critical_sound.play(loops=-1)
        except Exception as e:
            logger.error(f"Audio Manager: Failed to play critical sound: {e}")

    def stop_critical_alarm(self):
        """Stops the looping critical alarm."""
        if not self.mixer_initialized or not self.critical_sound:
            return
        try:
            # Stop all channels playing this critical alarm sound
            if self.critical_sound.get_num_channels() > 0:
                logger.info("Audio Manager: Stopping continuous critical alarm loop.")
                self.critical_sound.stop()
        except Exception as e:
            logger.error(f"Audio Manager: Failed to stop critical sound: {e}")

    def stop_all(self):
        """Stops all playing sounds."""
        if not self.mixer_initialized:
            return
        try:
            pygame.mixer.stop()
        except Exception as e:
            logger.error(f"Audio Manager: Failed to stop all sounds: {e}")

    def set_volume(self, volume: float):
        """Updates volume (0.0 to 1.0) dynamically."""
        self.current_volume = max(0.0, min(volume, 1.0))
        if not self.mixer_initialized:
            return
            
        if self.warning_sound:
            self.warning_sound.set_volume(self.current_volume)
        if self.critical_sound:
            self.critical_sound.set_volume(self.current_volume)

    def close(self):
        """Releases Pygame mixer resources."""
        if self.mixer_initialized:
            self.stop_all()
            try:
                pygame.mixer.quit()
                self.mixer_initialized = False
                logger.info("Audio Manager: Closed and released Pygame Mixer.")
            except Exception as e:
                logger.error(f"Audio Manager: Error during shutdown: {e}")
                
    def __del__(self):
        self.close()
