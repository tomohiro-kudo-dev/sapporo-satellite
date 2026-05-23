"""
札幌駅新幹線工事 変化ビューア - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os
import subprocess

from app.api import images, tiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/metadata", exist_ok=True)
    metadata_dir = Path("data/metadata")
    if not list(metadata_dir.glob("*.json")):
        subprocess.run(
            ["python", "generate_mock_data.py"],
            cwd="/opt/render/project/src/backend"
        )
    yield


app = FastAPI(
    title="札幌駅新幹線工事 変化ビューア API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data", exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")

app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(tiles.router, prefix="/api/tiles", tags=["tiles"])


@app.get("/")
def root():
    return {"message": "札幌駅新幹線工事 変化ビューア API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
