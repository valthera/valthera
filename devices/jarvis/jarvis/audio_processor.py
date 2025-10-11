#!/usr/bin/env python3

import logging
import os
import sys
import time
import threading
import wave
import io
from typing import Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available")

try:
    from openwakeword.model import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError as e:
    OPENWAKEWORD_AVAILABLE = False
    print(f"Warning: OpenWakeWord not available: {e}")

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: Vosk not available")

# Configure logging
logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, model_path: str = "/app/jarvis/models/vosk-model-small/vosk-model-small-en-us-0.15"):
        self.model_path = model_path
        self.wake_model = None
        self.vosk_model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        self.is_running = False
        self.thread = None
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        
        # Wake word detection
        self.wake_word_detected = False
        self.recording_duration = 3.0  # Record for 3 seconds after wake word
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize OpenWakeWord and Vosk models"""
        try:
            # Initialize OpenWakeWord for wake word detection
            if OPENWAKEWORD_AVAILABLE:
                try:
                    # Use built-in "hey_jarvis" wake word model
                    self.wake_model = Model(wakeword_models=["hey_jarvis"])
                    logger.info("[AUDIO] OpenWakeWord wake word detection initialized with 'hey_jarvis'")
                except Exception as e:
                    logger.warning(f"[AUDIO] OpenWakeWord initialization failed: {e}")
                    self.wake_model = None
            else:
                logger.warning("[AUDIO] OpenWakeWord not available - wake word detection disabled")
            
            # Initialize Vosk for speech-to-text
            if VOSK_AVAILABLE and os.path.exists(self.model_path):
                self.vosk_model = vosk.Model(self.model_path)
                self.recognizer = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
                logger.info("[AUDIO] Vosk speech-to-text model loaded")
            else:
                logger.warning(f"[AUDIO] Vosk model not found at {self.model_path} - speech-to-text disabled")
            
            # Initialize PyAudio
            if PYAUDIO_AVAILABLE:
                self.audio = pyaudio.PyAudio()
                logger.info("[AUDIO] PyAudio initialized")
            else:
                logger.error("[AUDIO] PyAudio not available - audio capture disabled")
                
        except Exception as e:
            logger.error(f"[AUDIO] Error initializing audio models: {e}")
    
    def _find_microphone(self):
        """Find available microphone device"""
        if not PYAUDIO_AVAILABLE or not self.audio:
            return None
        
        try:
            # Try to find a USB microphone or default input device
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    logger.info(f"[AUDIO] Found input device: {device_info['name']} (index: {i})")
                    return i
            return None
        except Exception as e:
            logger.error(f"[AUDIO] Error finding microphone: {e}")
            return None
    
    def _start_audio_stream(self):
        """Start audio input stream"""
        if not PYAUDIO_AVAILABLE or not self.audio:
            return False
        
        try:
            device_index = self._find_microphone()
            if device_index is None:
                logger.error("[AUDIO] No microphone device found")
                return False
            
            # Try different sample rates if the default doesn't work
            sample_rates = [16000, 44100, 48000, 22050, 11025]
            
            for rate in sample_rates:
                try:
                    self.stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=self.chunk_size
                    )
                    self.sample_rate = rate  # Update the sample rate
                    logger.info(f"[AUDIO] Audio stream started with sample rate {rate}Hz")
                    return True
                except Exception as e:
                    logger.warning(f"[AUDIO] Failed to start audio stream with {rate}Hz: {e}")
                    continue
            
            logger.error("[AUDIO] Could not start audio stream with any sample rate")
            return False
            
        except Exception as e:
            logger.error(f"[AUDIO] Error starting audio stream: {e}")
            return False
    
    def _stop_audio_stream(self):
        """Stop audio input stream"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.info("[AUDIO] Audio stream stopped")
            except Exception as e:
                logger.error(f"[AUDIO] Error stopping audio stream: {e}")
    
    def _detect_wake_word(self, audio_data):
        """Detect wake word in audio data using OpenWakeWord or fallback"""
        if OPENWAKEWORD_AVAILABLE and self.wake_model:
            try:
                import numpy as np
                # Convert audio bytes to numpy int16 array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Get predictions from OpenWakeWord
                predictions = self.wake_model.predict(audio_array)
                
                # Check if any wake word was detected with confidence > 0.5
                for model_name, confidence in predictions.items():
                    if confidence > 0.5:
                        logger.info(f"[AUDIO] Wake word '{model_name}' detected with confidence: {confidence:.2f}")
                        return True
                
                return False
            except Exception as e:
                logger.error(f"[AUDIO] Error detecting wake word with OpenWakeWord: {e}")
                # Fall back to voice activity detection
                return self._detect_voice_activity(audio_data)
        else:
            # Fall back to voice activity detection
            return self._detect_voice_activity(audio_data)
    
    def _detect_voice_activity(self, audio_data):
        """Simple voice activity detection as fallback - now with basic keyword detection"""
        try:
            import numpy as np
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Check for valid audio data
            if len(audio_array) == 0:
                return False
            
            # Calculate RMS energy with safety checks
            mean_squared = np.mean(audio_array**2)
            if mean_squared <= 0:
                return False
            
            rms = np.sqrt(mean_squared)
            
            # Very sensitive threshold for voice detection
            threshold = 20  # Very sensitive threshold for voice detection
            is_voice = rms > threshold
            
            # Debug logging every 100 frames (about every 2-3 seconds)
            if hasattr(self, '_frame_count'):
                self._frame_count += 1
            else:
                self._frame_count = 1
                
            if self._frame_count % 100 == 0:
                logger.info(f"[AUDIO] Voice activity check - RMS: {rms:.1f}, threshold: {threshold}, voice detected: {is_voice}")
            
            return is_voice
        except Exception as e:
            logger.error(f"[AUDIO] Error in voice activity detection: {e}")
            return False
    
    def _transcribe_audio(self, audio_data):
        """Transcribe audio data using Vosk"""
        if not VOSK_AVAILABLE or not self.recognizer:
            return "Speech-to-text not available"
        
        try:
            import json
            # Convert audio data to numpy array for resampling
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Resample from current sample rate to 16kHz if needed
            if self.sample_rate != 16000:
                from scipy import signal
                # Calculate resampling ratio
                resample_ratio = 16000 / self.sample_rate
                new_length = int(len(audio_array) * resample_ratio)
                audio_array = signal.resample(audio_array, new_length).astype(np.int16)
                logger.info(f"[AUDIO] Resampled audio from {self.sample_rate}Hz to 16kHz")
            
            # Convert back to bytes
            audio_bytes = audio_array.tobytes()
            
            if self.recognizer.AcceptWaveform(audio_bytes):
                result = self.recognizer.Result()
                result_dict = json.loads(result)
                return result_dict.get('text', '').strip()
            else:
                partial = self.recognizer.PartialResult()
                partial_dict = json.loads(partial)
                return partial_dict.get('partial', '').strip()
        except Exception as e:
            logger.error(f"[AUDIO] Error transcribing audio: {e}")
            return f"Transcription error: {e}"
    
    def _record_after_wake_word(self):
        """Record audio for a few seconds after wake word detection"""
        if not self.stream:
            return
        
        logger.info("[AUDIO] Voice activity detected! Recording...")
        frames = []
        frames_to_record = int(self.recording_duration * self.sample_rate / self.chunk_size)
        
        for _ in range(frames_to_record):
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                logger.error(f"[AUDIO] Error recording audio: {e}")
                break
        
        if frames:
            # Combine all audio frames
            audio_data = b''.join(frames)
            
            # Transcribe the recorded audio
            transcription = self._transcribe_audio(audio_data)
            if transcription:
                logger.info(f"[AUDIO] Transcription: \"{transcription}\"")
                
                # Check if transcription contains "Jarvis" or similar
                transcription_lower = transcription.lower()
                wake_phrases = ["jarvis", "hey jarvis", "hi jarvis", "hello jarvis"]
                
                for phrase in wake_phrases:
                    if phrase in transcription_lower:
                        logger.info(f"[AUDIO] 🎯 WAKE WORD DETECTED! Found '{phrase}' in: \"{transcription}\"")
                        return
                
                logger.info("[AUDIO] No wake word detected in transcription")
            else:
                logger.info("[AUDIO] No speech detected in recording")
    
    def _audio_loop(self):
        """Main audio processing loop"""
        logger.info("[AUDIO] Starting audio processing loop...")
        
        while self.is_running:
            try:
                if not self.stream:
                    time.sleep(0.1)
                    continue
                
                # Read audio data
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Check for wake word
                if self._detect_wake_word(audio_data):
                    self._record_after_wake_word()
                
            except Exception as e:
                logger.error(f"[AUDIO] Error in audio loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start audio processing"""
        if self.is_running:
            logger.warning("[AUDIO] Audio processor already running")
            return
        
        if not PYAUDIO_AVAILABLE:
            logger.error("[AUDIO] Cannot start - PyAudio not available")
            return
        
        if not self.audio:
            logger.error("[AUDIO] Cannot start - PyAudio not initialized")
            return
        
        if not self._start_audio_stream():
            logger.error("[AUDIO] Cannot start - failed to initialize audio stream")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.thread.start()
        logger.info("[AUDIO] Audio processor started")
    
    def stop(self):
        """Stop audio processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_audio_stream()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("[AUDIO] Audio processor stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        
        if self.audio:
            try:
                self.audio.terminate()
                self.audio = None
            except Exception as e:
                logger.error(f"[AUDIO] Error cleaning up PyAudio: {e}")
        
        if self.wake_model:
            try:
                self.wake_model = None
            except Exception as e:
                logger.error(f"[AUDIO] Error cleaning up OpenWakeWord: {e}")


def main():
    """Test the audio processor"""
    logging.basicConfig(level=logging.INFO)
    
    processor = AudioProcessor()
    
    try:
        processor.start()
        logger.info("[AUDIO] Listening for 'Hey Jarvis'... Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("[AUDIO] Stopping audio processor...")
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()
