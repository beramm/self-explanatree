import base64
from unittest import result

from fastapi import APIRouter,Response, Request, Depends, File, UploadFile, Form, WebSocket, WebSocketDisconnect
import logging
import asyncio


router = APIRouter(prefix="/tree")
logger = logging.getLogger(__name__)
from service.main import *



@router.post("/stt-llm-tts")
async def stt_llm_tts_endpoint(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()

    result = await asyncio.to_thread(
        process_audio_bytes,
        audio_bytes
    )
    text, reply, audio_wav = result

    return Response(
        content=audio_wav,
        media_type="audio/wav",
        headers={
            "X-Transcript": base64.b64encode((text or "").encode("utf-8")).decode("ascii"),
            "X-Reply": base64.b64encode((reply or "").encode("utf-8")).decode("ascii"),
        }
    )


@router.post("/stt-llm")
async def stt_llm_tts_endpoint(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()

    text, reply = await asyncio.to_thread(
        process_audio_bytes_raw,
        audio_bytes
    )
    
    return {"transcript": text, "reply": reply}

from pydantic import BaseModel

class Tree(BaseModel):
    id: int
    name: str
    status: str

@router.post("/status/{id}")
async def stt_llm_tts_endpoint(id: str):

    tree = Tree(id= 1, name=f"Tree 1", status="happy")    

    return tree
