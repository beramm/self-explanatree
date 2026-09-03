import serial
import subprocess
import io
import wave
import numpy as np
import sounddevice

bt = serial.Serial("/dev/serial0", 9600, timeout=1)

# ================= WIFI FUNCTIONS =================

def scan_wifi():
    subprocess.run(["nmcli", "dev", "wifi", "rescan"])
    cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stdout.strip().split("\n"):
        if line:
            ssid, signal, sec = line.split(":")
            bt.write(f"WIFI,{ssid},{signal},{sec}\n".encode())
    bt.write(b"ENDSCAN\n")

def get_wifi_security(ssid):
    cmd = ["nmcli", "-t", "-f", "SSID,SECURITY", "dev", "wifi"]
    out = subprocess.check_output(cmd).decode()

    for line in out.splitlines():
        if line.startswith(ssid + ":"):
            return line.split(":")[1]
    return None


def connect_wifi(ssid, password=None):
    sec = get_wifi_security(ssid)
    print(f"[INFO] SSID={ssid}, SECURITY={sec}")

    if sec is None:
        print("[ERROR] SSID tidak ditemukan")
        return False

    # ================= OPEN WIFI =================
    if sec == "--" or sec == "":
        print("[INFO] Open WiFi (no password)")
        cmd = ["sudo", "nmcli", "dev", "wifi", "connect", ssid]

    # ================= WPA2 / WPA1 =================
    elif "WPA" in sec and "WPA3" not in sec and "802.1X" not in sec:
        print("[INFO] WPA2/WPA1 detected")
        cmd = [
            "sudo", "nmcli", "connection", "add",
            "type", "wifi", "ifname", "wlan0",
            "con-name", ssid,
            "ssid", ssid,
            "wifi-sec.key-mgmt", "wpa-psk",
            "wifi-sec.psk", password
        ]

    # ================= WPA3 SAE =================
    elif "WPA3" in sec:
        print("[INFO] WPA3 detected")
        cmd = [
            "sudo", "nmcli", "connection", "add",
            "type", "wifi", "ifname", "wlan0",
            "con-name", ssid,
            "ssid", ssid,
            "wifi-sec.key-mgmt", "sae",
            "wifi-sec.psk", password
        ]

    # ================= ENTERPRISE (NOT SUPPORTED) =================
    elif "802.1X" in sec:
        print("[ERROR] Enterprise WiFi not supported in auto mode")
        return False

    # ================= UNKNOWN =================
    else:
        print("[ERROR] Unknown security mode:", sec)
        return False

    # Delete old profile (prevent conflict)
    subprocess.run(["sudo", "nmcli", "connection", "delete", ssid],
                   stderr=subprocess.DEVNULL)

    # Run connect command
    subprocess.run(cmd, check=True)

    # Bring connection up
    subprocess.run(["sudo", "nmcli", "connection", "up", ssid], check=True)

    print("[OK] Connected to", ssid)
    bt.write(b"OK,CONNECTED\n")
    status_wifi()
    return True

# def connect_wifi(ssid, pwd):
#     cmd = ["nmcli", "dev", "wifi", "connect", ssid, "password", pwd]
#     res = subprocess.run(cmd, capture_output=True, text=True)
#     if res.returncode == 0:
#         bt.write(b"OK,CONNECTED\n")
#     else:
#         bt.write(f"ERROR,{res.stderr}\n".encode())

def disconnect_wifi():
    subprocess.run(["nmcli", "dev", "disconnect", "wlan0"])
    bt.write(b"OK,DISCONNECTED\n")

def status_wifi():
    ssid = subprocess.getoutput("iwgetid -r")
    ip = subprocess.getoutput("hostname -I | awk '{print $1}'")
    bt.write(f"STATUS,{ssid},{ip}\n".encode())

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

print("Bluetooth WiFi Simple Server Ready")

play_wav_file("sistem-siap.wav", device=2)

# ================= MAIN LOOP =================

while True:
    if bt.in_waiting:
        cmd = bt.readline().decode(errors="ignore").strip()
        print("RX:", cmd)

        if cmd == "PING":
            bt.write(b"PONG\n")

        elif cmd == "SCAN":
            scan_wifi()

        elif cmd.startswith("CONNECT,"):
            try:
                _, ssid, pwd = cmd.split(",", 2)
                connect_wifi(ssid, pwd)
            except:
                bt.write(b"ERROR,FORMAT\n")

        elif cmd == "STATUS":
            status_wifi()

        elif cmd == "DISCONNECT":
            disconnect_wifi()

        else:
            bt.write(b"ERROR,UNKNOWN_CMD\n")