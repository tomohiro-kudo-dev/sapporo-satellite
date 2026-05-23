"""
衛星画像タイルプロキシ
CopernicusのWMTSタイルをバックエンド経由で配信する
"""
from fastapi import APIRouter, Response
import requests

router = APIRouter()

@router.get("/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int, date: str = "2024-06-15"):
    url = (
        f"https://catalogue.dataspace.copernicus.eu/ogc/wmts/SENTINEL-2"
        f"?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
        f"&LAYER=TRUE-COLOR-S2L2A&STYLE=&FORMAT=image/jpeg"
        f"&TILEMATRIXSET=PopularWebMercator"
        f"&TIME={date}"
        f"&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}"
    )
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 SatelliteViewer/1.0"
        })
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        return Response(status_code=resp.status_code)
    except Exception:
        return Response(status_code=500)
