import io
import wave
import numpy as np
import sounddevice

def list_audio_devices():
    """Tampilkan daftar semua audio devices"""
    print("\n=== Audio Devices ===")
    devices = sounddevice.query_devices()
    for i, dev in enumerate(devices):
        print(f"[{i}] {dev['name']}")
        print(f"    Max Output Channels: {dev['max_output_channels']}")
        print(f"    Max Input Channels: {dev['max_input_channels']}")
        print(f"    Default Sample Rate: {dev['default_samplerate']}")
    print(f"\nDefault Output Device: {sounddevice.default.device[1]}")
    print(f"Default Input Device: {sounddevice.default.device[0]}")
    print("=" * 40 + "\n")

def play_wav_bytes(wav_bytes: bytes, label: str = "audio", device=None):
    """
    Mainkan WAV dari bytes
    
    Args:
        wav_bytes: Data WAV dalam bentuk bytes
        label: Label untuk logging
        device: Device ID untuk output (None = default, atau nomor device)
    """
    print(f"[INFO] Playing {label}...")
    if device is not None:
        print(f"[INFO] Using device: {device}")

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
    sounddevice.play(audio, samplerate=sr, device=device)
    sounddevice.wait()

    print(f"[INFO] Done playing {label}")

def play_wav_file(file_path: str, device=None):
    """
    Baca file WAV dari disk dan mainkan
    
    Args:
        file_path: Path ke file WAV
        device: Device ID untuk output (None = default, atau nomor device)
    """
    print(f"[INFO] Loading WAV file: {file_path}")
    with open(file_path, "rb") as f:
        wav_bytes = f.read()
    play_wav_bytes(wav_bytes, label=file_path, device=device)

if __name__ == "__main__":
    # Tampilkan daftar audio devices
    list_audio_devices()
    
    print("[INFO] System is ready. You can start speaking now.")
    
    # Cara 1: Mainkan dengan device default
    # play_wav_file("sistem-siap.wav")
    
    # Cara 2: Mainkan dengan device tertentu (uncomment dan ganti nomor device)
    play_wav_file("sistem-siap.wav", device=2)  # ganti 1 dengan nomor device yang diinginkan