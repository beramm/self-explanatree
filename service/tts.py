import numpy as np
import sounddevice as sd
from piper import PiperVoice, SynthesisConfig
import time
import soundfile as sf
import io

class PiperTTS:
    def __init__(self, model=".models/id_ID-news_tts-medium.onnx", use_cuda=False):
        self.tts = PiperVoice.load(model, use_cuda=use_cuda)

    def speak(self, text) -> float | None:
        start_tts = time.time()
        # voice.synthesize() mengembalikan generator, ubah ke list dulu
        results = self.tts.synthesize(text)
        audio_chunks = []
        for result in results:
            # cek apakah objek memiliki atribut audio_float_array
            if hasattr(result, "audio_float_array"):
                audio_chunks.append(result.audio_float_array)
            else:
                print(f"Skipped unknown result: {result}")
        if not audio_chunks:
            print("No audio data generated.")
            return None

        end_tts = time.time()

        audio = np.concatenate(audio_chunks)
        
        sd.play(audio, samplerate=22050)
        sd.wait()

        return end_tts-start_tts

    def synthesize_wav(self, text) -> bytes | None :
        print("Synthesizing audio . . .")
        syn_config = SynthesisConfig(
            # volume=0.5,  # half as loud
            length_scale=0.1,  # twice as slow
            noise_scale=1.0,  # more audio variation
            noise_w_scale=1.0,  # more speaking variation
            # normalize_audio=False, # use raw audio from voice
        )
        results = self.tts.synthesize(text)
        audio_chunks = []
        for result in results: 
            if hasattr(result, "audio_float_array"):
                audio_chunks.append(result.audio_float_array)
        if not audio_chunks:
            print("No audio data generated.")
            return None
        
        audio = np.concatenate(audio_chunks)
        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio,
            samplerate=22050,
            format="WAV",
            subtype="PCM_16"
        )
        
        return buffer.getvalue()
    
    
# if __name__ == "__main__":

#     tts = PiperTTS()
#     tts.speak("Halo, ini adalah contoh penggunaan PiperTTS.")
