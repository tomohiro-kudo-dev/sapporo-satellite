"""
Sentinel Hub WMS タイルプロキシ
"""
from fastapi import APIRouter, Response
import requests
import os

router = APIRouter()

def get_access_token():
    """Sentinel HubのOAuthトークンを取得"""
    client_id = os.getenv("SH_CLIENT_ID")
    client_secret = os.getenv("SH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return None
    
    resp = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


@router.get("/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int, date: str = "2024-06-15"):
    """Sentinel Hub WMSタイルをプロキシして返す"""
    instance_id = os.getenv("SH_INSTANCE_ID", "60de79ca-16a7-4afd-bcbd-0261bf0156fa")
    
    token = get_access_token()
    
    url = f"https://services.sentinel-hub.com/ogc/wmts/{instance_id}"
    params = {
        "SERVICE": "WMTS",
        "REQUEST": "GetTile",
        "VERSION": "1.0.0",
        "LAYER": "TRUE-COLOR-S2L2A",
        "STYLE": "",
        "FORMAT": "image/jpeg",
        "TILEMATRIXSET": "PopularWebMercator",
        "TIME": date,
        "TILEMATRIX": z,
        "TILEROW": y,
        "TILECOL": x,
    }
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        return Response(status_code=resp.status_code)
    except Exception as e:
        print(f"タイルエラー: {e}")
        return Response(status_code=500)
