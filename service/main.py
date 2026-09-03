import os

from dotenv import load_dotenv

from .gemini import GeminiAIHelper
from .stt import STT
from .tts import PiperTTS
from service.ai import OpenAIHelper

load_dotenv()

DEVICE_STT = os.getenv("DEVICE_STT")
TTS_USE_CUDA = os.getenv("DEVICE_TTS").lower() == "cuda"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

stt_engine = STT(model_size="medium", device=DEVICE_STT)
ai_helper = GeminiAIHelper(api_key=GEMINI_API_KEY)
openai_helper = OpenAIHelper(api_key=os.getenv("OPENAI_API_KEY"))

models_tts = os.path.join(".models", "id_ID-news_tts-medium.onnx")
tts = PiperTTS(model=models_tts, use_cuda=TTS_USE_CUDA)


# def process_audio(audioFile):
#     # call function to display ai thinking state
#     stt_engine = STT(model_size="medium")
#     ai_helper = GeminiAIHelper(api_key=os.getenv("GEMINI_API_KEY"))
#     models = os.path.join(".models", "id_ID-news_tts-medium.onnx")
#     tts = PiperTTS(model=models)

#     print("self explanation runner . . . ")
#     text = stt_engine.transcribe(audioFile)
#     print(f"Transcribed Text: {text}")

#     tree_identity = "lorem ipsum"

#     reply = openai_helper.ask_ai(text, tree_identity)
            
#     # call function to display its model turn

#     print("AI:", reply)
#     tts.speak(reply)


def process_audio_bytes(audio_bytes: bytes):

    text = stt_engine.transcribe_bytes(audio_bytes)
    print(f"Transcribed Text: {text}")

    if not text:
        print("failed to identify speech")
        return "","",None
    
    tree_identity ="lorem ipsum"
    
    # reply = ai_helper.ask_ai(text, tree_identity)
    reply = openai_helper.ask_ai(text,tree_identity)
    print("AI:", reply)
    audio_wav = tts.synthesize_wav(reply)

    return text, reply, audio_wav


def process_audio_bytes_raw(audio_bytes: bytes) -> tuple[str|None, str|None]:

    text = stt_engine.transcribe_bytes(audio_bytes)
    print(f"Transcribed Text: {text}")

    if not text:
        return None, None

    tree_identity = "lorem ipsum"

    reply = openai_helper.ask_ai(text, tree_identity)
    print("AI:", reply)

    return text, reply
