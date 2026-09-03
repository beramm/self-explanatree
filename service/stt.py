import os
import wave
from os import listdir, makedirs, path

from dotenv import load_dotenv

from faster_whisper import WhisperModel

# from .ai import OpenAIHelper
import soundfile as sf
import io

MIN_AUDIO_DURATION_SEC = 0.3
SILENCE_TIMEOUT = 2.0

load_dotenv()



class STT:
    def __init__(self, model_size="medium", device="cpu", compute_type="int8"):
        # model_size bisa diganti small-int8 untuk Pi 2GB
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path):
        is_too_short = self.is_audio_long_enough(audio_path)
        print(is_too_short)
        if is_too_short:
            print("Audio too short, skipping transcription.")
            return ""

        print("Start transcribing")
        segments, info = self.model.transcribe("chunks/"+audio_path, language="id", log_progress=True)
        text = ""
        for segment in segments:
            # print(segment.no_speech_prob)
            if segment.no_speech_prob > 0.5:
                continue
            text += segment.text + " "
            print(text)
        return text.strip()

    def is_audio_long_enough(self, filepath: str):
        try:
            with wave.open(filepath, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return duration >= MIN_AUDIO_DURATION_SEC

        except (wave.Error, EOFError):
            # File tidak valid atau kosong
            return False

        except FileNotFoundError:
            # File tidak ditemukan
            return False

        except Exception as e:
            # Error lain yang tidak terduga
            print("Unexpected error in is_audio_long_enough:", e)
            return False

    def transcribe_bytes(self,audio_bytes: bytes):

        audio_np, sr = sf.read(io.BytesIO(audio_bytes), dtype = "float32")
        
        if not self.is_audio_long_enough_np(audio_np, sr):
            print("Audio too short, skipping transcription.")
            return ""
        
        print("Start transcribing")
        segments,info = self.model.transcribe(
            audio_np,
            language="id",
            log_progress=True
        )
        text = ""
        for segment in segments:
            if segment.no_speech_prob > 0.5:
                continue
            text += segment.text + " "
        return text.strip()
    
    def is_audio_long_enough_np(self, audio_np, sr):
        duration = len(audio_np) / sr
        return duration >= MIN_AUDIO_DURATION_SEC

