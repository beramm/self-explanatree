import os
from dotenv import load_dotenv
from vad import VADRecorder

import os
import requests
import sounddevice as sd
import soundfile as sf

load_dotenv()

API_URL = os.getenv("SERVER_IP") + "tree/stt-llm-tts"

# def run():
#     vad = VADRecorder()
#     print("Mulai merekam. Bicara sekarang...")
#     while True :
#         # call function to display its user turn
#         print("Speak Now!!")
#         audio_file,is_saved = vad.record()
#         if is_saved:
#             print("Recorded:", audio_file)
#             # call endpoint  endpoint/tree/stt-llm-tts with audio_file    
         
def play_audio_bytes(audio_bytes: bytes):
    """
    Play WAV audio bytes directly (no temp file needed)
    """
    import io
    with io.BytesIO(audio_bytes) as bio:
        data, samplerate = sf.read(bio, dtype="float32")
        sd.play(data, samplerate)
        sd.wait()   
        
def send_audio(audio_file_path: str):
    with open(audio_file_path, "rb") as f:
        files = {
            "audio": (
                os.path.basename(audio_file_path),
                f,
                "audio/wav"
            )
        }

        response = requests.post(API_URL, files=files, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Request failed {response.status_code}: {response.text}"
        )

    transcript = response.headers.get("X-Transcript", "")
    reply = response.headers.get("X-Reply", "")

    return response.content, transcript, reply


def run():
    vad = VADRecorder()
    print("Mulai merekam. Bicara sekarang...")

    while True:
        print("Speak Now!!")

        audio_file, is_saved = vad.record()

        if not is_saved:
            continue

        print(f"Recorded: {audio_file}")
        audio_file= os.path.join("chunks", audio_file)


        # try:
        #     audio_bytes, transcript, reply = send_audio(audio_file)

        #     print("Transcript:", transcript)
        #     print("Reply:", reply)

        #     play_audio_bytes(audio_bytes)

        # except Exception as e:
        #     print("Error:", e)

        # finally:
        #     try:
        #         os.remove(audio_file)
        #         print(f"Deleted temp file: {audio_file}")
        #     except OSError as e:
        #         print(f"Failed to delete {audio_file}: {e}")  

if __name__ == "__main__":
    run()


