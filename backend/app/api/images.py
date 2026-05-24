"""
画像APIエンドポイント
GET /api/images        - 画像一覧
GET /api/images/latest - 最新画像
GET /api/images/{date} - 指定日の画像
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import json
import os
from pathlib import Path

router = APIRouter()

METADATA_DIR = Path("data/metadata")
IMAGES_DIR = Path("data/images")


def load_all_metadata() -> list[dict]:
    """全メタデータJSONを読み込み、日付降順でソートして返す"""
    entries = []
    if not METADATA_DIR.exists():
        return entries
    for json_file in sorted(METADATA_DIR.glob("*.json"), reverse=True):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                entry = json.load(f)
                entry.pop("is_mock", None)
                entries.append(entry)
        except Exception:
            continue
    return entries

@router.get("")
def list_images(
    year: Optional[int] = None,
    month: Optional[int] = None,
    max_cloud: Optional[float] = None,
):
    """
    取得済み衛星画像の一覧を返す。
    クエリパラメータでフィルタ可能:
      - year: 年
      - month: 月
      - max_cloud: 雲量上限(%)
    """
    entries = load_all_metadata()

    if year is not None:
        entries = [e for e in entries if e.get("year") == year]
    if month is not None:
        entries = [e for e in entries if e.get("month") == month]
    if max_cloud is not None:
        entries = [e for e in entries if e.get("cloud_coverage", 100) <= max_cloud]

    return {
        "count": len(entries),
        "images": entries,
    }


@router.get("/latest")
def get_latest_image():
    """最新（最も日付が新しい）画像のメタデータを返す"""
    entries = load_all_metadata()
    if not entries:
        raise HTTPException(status_code=404, detail="画像がまだありません。まず fetch_images.py を実行してください。")
    return entries[0]


@router.get("/{date}")
def get_image_by_date(date: str):
    """
    指定日の画像メタデータを返す。
    date形式: YYYY-MM-DD
    """
    json_path = METADATA_DIR / f"{date}.json"
    if not json_path.exists():
        # 近い日付を探す
        entries = load_all_metadata()
        close = [e for e in entries if e.get("date", "").startswith(date[:7])]
        if close:
            raise HTTPException(
                status_code=404,
                detail=f"{date} の画像はありません。同月の候補: {[e['date'] for e in close]}"
            )
        raise HTTPException(status_code=404, detail=f"{date} の画像が見つかりません")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/{date}/file")
def download_image_file(date: str):
    """指定日のPNGファイルを直接返す"""
    png_path = IMAGES_DIR / f"{date}.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail=f"{date}.png が見つかりません")
    return FileResponse(str(png_path), media_type="image/png")
