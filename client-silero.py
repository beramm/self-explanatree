import base64
import io
import json
import os
import threading
import time
import wave
from collections import deque
from datetime import datetime

import numpy as np
import requests
import sounddevice
import soundfile as sf
import torch
import torchaudio

from dotenv import load_dotenv

from led_control import EyeAnimation

load_dotenv()

model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    # force_reload=True,
)

(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

# SAMPLE_RATE = 48000

DEVICE_SAMPLE_RATE = int(os.getenv("DEVICE_SAMPLE_RATE", 48000))
VAD_SAMPLE_RATE = int(os.getenv("VAD_SAMPLE_RATE", 16000))
CHUNK_DURATION_MS = int(os.getenv("CHUNK_DURATION_MS", 32))

CHUNK_SIZE = int(DEVICE_SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
VAD_CHUNK_SIZE = int(VAD_SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

THRESHOLD = float(os.getenv("THRESHOLD", 0.5))
MIN_SILENCE_DURATION_MS = int(os.getenv("MIN_SILENCE_DURATION_MS", 500))
SPEECH_PAD_MS = int(os.getenv("SPEECH_PAD_MS", 30))

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_HOST = os.getenv("API_HOST", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))

API_URL = f"{API_HOST}/tree/stt-llm-tts"

DEBUG_SAVE_AUDIO = os.getenv("DEBUG_SAVE_AUDIO", "False").lower() == "true"
DEBUG_PLAY_AUDIO = os.getenv("DEBUG_PLAY_AUDIO", "False").lower() == "true"

vad_iterator = VADIterator(
    model,
    threshold=THRESHOLD,
    sampling_rate=VAD_SAMPLE_RATE,
    min_silence_duration_ms=MIN_SILENCE_DURATION_MS,
    speech_pad_ms=SPEECH_PAD_MS,
)

is_speaking = False
speech_buffer = []
audio_queue = deque()
lock = threading.Lock()
vad_paused = threading.Event()
vad_paused.set()


def save_to_wav(audio: np.ndarray, prefix="speech"):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = os.path.join(OUTPUT_DIR, f"{prefix}_{timestamp}.wav")

    sf.write(filename, audio, VAD_SAMPLE_RATE)
    print(f"[INFO] Audio saved: {filename}")
    return filename


def on_speech_start(start_sample):
    global is_speaking
    is_speaking = True

    t = start_sample / VAD_SAMPLE_RATE
    print(f"\n[SPEECH START] @ {t:.2f}s")


def on_speech_end(end_sample, audio_data: list[np.ndarray]):
    global is_speaking
    is_speaking = False
    duration = len(audio_data) * VAD_CHUNK_SIZE / VAD_SAMPLE_RATE

    t = end_sample / VAD_SAMPLE_RATE
    print(
        f"[SPEECH END] @ {t:.2f}s | duration: {duration:.2f}s | length: {len(audio_data)}"
    )

    threading.Thread(target=handle_speech_end, args=(audio_data,), daemon=True).start()


def handle_speech_end(audio_data: list[np.ndarray]):
    global is_speaking

    vad_paused.clear()

    print(
        f"\n[INFO] Processing speech segment... duration: {len(audio_data) * VAD_CHUNK_SIZE / VAD_SAMPLE_RATE:.2f}s"
    )

    transcribe, reply, wav_audio = send_to_server(audio_data)

    if transcribe:
        print(f"[INFO] Transcript: {transcribe}")
    else:
        print("[INFO] No transcript or failed to get transcript.")

    if reply:
        print(f"[INFO] AI Response: {reply}")
    else:
        print("[INFO] No response or failed to get response.")

    if wav_audio:
        print(
            f"[INFO] Playing AI response audio... size: {len(wav_audio) / 1024:.2f} KB"
        )
        play_wav_bytes(wav_audio, label="AI Response", device=2)
    else:
        print("[INFO] No audio response to play.")

    vad_iterator.reset_states()

    audio_queue.clear()
    is_speaking = False
    vad_paused.set()

    print("\n[INFO] listening . . .")


def numpy_to_wav_bytes(audio: np.ndarray, sr: int = VAD_SAMPLE_RATE) -> bytes:
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    buf.seek(0)
    return buf.getvalue()


def play_wav_bytes(wav_bytes: bytes, label: str = "audio"):
    print(f"[INFO] Playing {label}...")

    # Baca WAV bytes → numpy array
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    # Convert ke float32
    dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
    dtype = dtype_map.get(sampwidth, np.int16)
    audio = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    audio /= np.iinfo(dtype).max  # normalize ke -1.0 ~ 1.0

    # Reshape kalau stereo
    if channels > 1:
        audio = audio.reshape(-1, channels)

    # Play — blocking sampai selesai
    sounddevice.play(audio, samplerate=sr, device=2)
    sounddevice.wait()

    print(f"[INFO] Done playing {label}")


def send_to_server(
    audio_chunk: list[np.ndarray],
) -> tuple[str | None, str | None, bytes | None]:
    full_audio = np.concatenate(audio_chunk)
    wav_bytes = numpy_to_wav_bytes(full_audio)
    duration = len(full_audio) / VAD_SAMPLE_RATE

    if DEBUG_SAVE_AUDIO:
        file_path = save_to_wav(full_audio, prefix="speech")
        size_kb = os.path.getsize(file_path) / 1024
        print(f"[DEBUG] Saved full audio to {file_path} ({size_kb:.2f} KB)")

    if DEBUG_PLAY_AUDIO:
        try:
            full_audio_float32 = full_audio.astype(np.float32)
            print(
                f"[DEBUG] Playing back audio for debugging... duration: {duration:.2f}s"
            )
            sounddevice.play(full_audio_float32, VAD_SAMPLE_RATE)
            sounddevice.wait()
        except Exception as e:
            print(f"[ERROR] Failed to play audio: {e}")

    try:
        print(f"[INFO] Sending audio to server... duration: {duration:.2f}s")

        response = requests.post(
            API_URL,
            files={"audio": ("speech.wav", wav_bytes, "audio/wav")},
            data={"language": "id"},
            timeout=API_TIMEOUT,
        )

        response.raise_for_status()

        transcribe = response.headers.get("X-Transcript")
        transcribe = base64.b64decode(transcribe).decode("utf-8") if transcribe else ""
        reply = response.headers.get("X-Reply")
        reply = base64.b64decode(reply).decode("utf-8") if reply else ""

        wav_audio = response.content  # langsung WAV bytes

        return transcribe, reply, wav_audio

    except requests.exceptions.ConnectionError:
        print("[ERROR] Failed to connect to server.")
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out.")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e.response.status_code} - {e.response.text}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Failed to parse response: {e}")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")

    return None, None, None


def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"\n[WARN] {status}")

    if vad_paused.is_set():
        audio_chunk = indata[:, 0].copy()
        audio_queue.append(audio_chunk)


def vad_loop():
    global speech_buffer
    sample_offset = 0

    while True:
        if not audio_queue:
            time.sleep(0.001)
            continue

        with lock:
            chunk = audio_queue.popleft()

        tensor = torch.from_numpy(chunk).float()


        resampler = torchaudio.transforms.Resample(
            orig_freq=48000,
            new_freq=16000
        )

        audio_vad = resampler(tensor)

        speech_dict = vad_iterator(audio_vad, return_seconds=False)

        if speech_dict:
            if "start" in speech_dict:
                speech_buffer = [audio_vad.numpy()]
                on_speech_start(sample_offset + speech_dict["start"])

            elif "end" in speech_dict:
                speech_buffer.append(audio_vad.numpy())
                on_speech_end(sample_offset + speech_dict["end"], speech_buffer)
                speech_buffer = []

        elif is_speaking:
            speech_buffer.append(audio_vad.numpy())

        sample_offset += VAD_CHUNK_SIZE


def main():
    print("=" * 50)
    print("  Silero VAD Realtime — tekan Ctrl+C untuk stop")
    print(f"  Device sample rate : {DEVICE_SAMPLE_RATE} Hz")
    print(f"  VAD sample rate : {VAD_SAMPLE_RATE} Hz")
    print(f"  Chunk size  : {CHUNK_SIZE} samples ({CHUNK_DURATION_MS}ms)")
    print(f"  Threshold   : {THRESHOLD}")
    print("=" * 50)

    vad_thread = threading.Thread(target=vad_loop, daemon=True)
    vad_thread.start()

    eyes = EyeAnimation()
    eyes.start()

    with sounddevice.InputStream(
        samplerate=DEVICE_SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        callback=audio_callback,
    ):
        try:
            print("[INFO] listening . . .")
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[INFO] Stopping...")
            vad_iterator.reset_states()


if __name__ == "__main__":
    main()
