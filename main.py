from fastapi import FastAPI
from dotenv import load_dotenv
from routers import *


load_dotenv()

app = FastAPI()


app.include_router(tree_router)

@app.get("/")
def read_root():
    return {"message": "FastAPI + uv 🚀"}

