"""
札幌駅新幹線工事 変化ビューア - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api import images


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: dataディレクトリを作成
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/metadata", exist_ok=True)
    yield


app = FastAPI(
    title="札幌駅新幹線工事 変化ビューア API",
    description="Sentinel-2衛星画像を時系列で取得・提供するAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定 (フロントエンドからのアクセスを許可)
app.add_middleware(
    CORSMiddleware,
　　 allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル (衛星画像PNG) を配信
os.makedirs("data", exist_ok=True)
app.mount("/static", StaticFiles(directory="data"), name="static")

# APIルーターを登録
app.include_router(images.router, prefix="/api/images", tags=["images"])


@app.get("/")
def root():
    return {
        "message": "札幌駅新幹線工事 変化ビューア API",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
