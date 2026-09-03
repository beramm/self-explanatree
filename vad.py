import datetime
import wave
from os import makedirs, path
import os

import noisereduce as nr
import numpy as np
import pyaudio
import webrtcvad
from matplotlib import pyplot as plt
from scipy.signal import butter, sosfilt
from dotenv import load_dotenv

load_dotenv()


def highpass(data, sr, cutoff=150):
    sos = butter(4, cutoff / (sr / 2), btype='highpass', output='sos')
    filtered = sosfilt(sos, data)
    return filtered


def fft_magnitude(samples, sr, max_freq=6000):
    # windowing untuk mengurangi spectral leakage
    windowed = samples * np.hanning(len(samples))
    fft = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(len(samples), d=1/sr)

    # ambil sampai max_freq
    fft_sel = fft[freqs <= max_freq]
    mag = np.abs(fft_sel)
    return mag

class VADRecorder:
    def __init__(self, aggressiveness=3, rate=os.getenv("SAMPLE_RATE"), chunk=320):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.rate = rate
        self.chunk = chunk  # 20ms frames
        self.format = pyaudio.paInt16
        self.channels = 1
        self.frames = []

    def reduce_noise(self, input_path, output_path):
        data, rate = sf.read(input_path)

        reduced = nr.reduce_noise(y=data, sr=rate)

        sf.write(output_path, reduced, rate)
        return output_path

    def record(self, timeout=5):
        self.frames=[]
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

        stream_out = p.open(
            format=pyaudio.paInt16,  # format 16-bit PCM
            channels=1,              # mono
            rate=16000,              # sample rate
            output=True              # untuk playback
        )

        print("Listening...")
        silent_chunks = 0
        buffer_frames = []
        max_silence_chunks = 10
        while True:
            data = stream.read(self.chunk, exception_on_overflow=False)

            samples = np.frombuffer(data, dtype=np.int16)

            # amplification_factor = 1.0
            # amplified_samples = samples * amplification_factor
            # # Clip to int16 range to avoid overflow
            # amplified_samples = np.clip(amplified_samples, -32768, 32767).astype(
            #     np.int16
            # )
            #
            #
            samples = samples.astype(np.float32)

            # samples = highpass(amplified_samples.astype(np.float32), self.rate)

            # Convert ke float32 karena noisereduce butuh float
            # float_samples = filtered.astype(np.float32)

            rms_1 = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

            text = f'rms_1: {rms_1:.2f}'

            mag = fft_magnitude(samples, 16000)
            n_fft = (len(mag) - 1) * 2
            freqs = np.fft.rfftfreq(n_fft, d=1/16000)

            # print("samples:", len(samples))
            # print("mag:", len(mag))
            # print("freqs:", len(freqs))
                        
            speech_band = mag[(freqs >= 300) & (freqs <= 3400)]
            energy = np.sum(speech_band)

            # threshold bisa disesuaikan
            threshold = 1000
            is_speech = energy > threshold

            text += f', energy: {energy:.2f}'

            # Noise reduction
            # samples = nr.reduce_noise(y=samples, sr=self.rate)

            # rms_2 = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            # text += f', rms_2: {rms_2:.2f}'

            # Kembalikan ke int16
            samples_int16 = np.clip(samples, -32768, 32767).astype(np.int16)
            audio_bytes = samples_int16.tobytes()
            stream_out.write(audio_bytes)

            print(text)


            # Konversi ke bytes untuk VAD


            rms = np.sqrt(np.mean(samples_int16.astype(np.float32) ** 2))

            clean_bytes = samples_int16.tobytes()

            is_speech = self.vad.is_speech(clean_bytes, self.rate)
            # print(f"speech: {is_speech}, peak: {peak}, RMS: {rms}", rms)

            if is_speech:
                self.frames.append(clean_bytes)
                silent_chunks = 0
            else:
                if self.frames:
                    silent_chunks += 1
                    if silent_chunks > 10:  # ~0.2s silent
                        break

        stream.stop_stream()
        stream.close()
        p.terminate()

        print(len(self.frames))

        if len(self.frames) < 10:
            print("Audio is too short, not saving.")
            return (None, False)

        # Check if audio is silent - do not save if silent
        if not self.frames:
            print("No speech detected, nothing saved.")
            return (None, False)

        # Calculate average energy of frames to detect silence (very low energy means silence)
        def frame_energy(frame):
            # 16 bit audio, so two bytes per sample
            count = len(frame) // 2
            shorts = wave.struct.unpack("<" + ("h" * count), frame)
            energy = sum(abs(sample) for sample in shorts) / count
            return energy

        avg_energy = sum(frame_energy(f) for f in self.frames) / len(self.frames)

        SILENCE_THRESHOLD = 150  # You can tweak this threshold as per your needs
        if avg_energy < SILENCE_THRESHOLD:
            print("Audio detected as silence, not saving.")
            return (None, False)

        # Save audio chunk since it's not silent
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        save_dir = "chunks"

        if not path.exists(save_dir):
            makedirs(save_dir)

        wf = wave.open(path.join(save_dir, f"chunk_{timestamp}.wav"), "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        print(f"Saved as chunk_{timestamp}.wav")
        self.frames = []
        return (f"chunk_{timestamp}.wav", True)


if __name__ == "__main__":
    # vad = VADRecorder()
    while True:
        vad = VADRecorder()
        audio_file = vad.record()
        # print("Audio saved as", audio_file)
