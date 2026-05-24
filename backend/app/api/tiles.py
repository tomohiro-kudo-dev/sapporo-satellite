from fastapi import APIRouter, Response
import requests
import os

router = APIRouter()


def get_access_token():
    client_id = os.getenv("SH_CLIENT_ID")
    client_secret = os.getenv("SH_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        resp = requests.post(
            "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=10,
        )
        print(f"Token status: {resp.status_code}")
        if resp.status_code == 200:
            return resp.json().get("access_token")
        print(f"Token error: {resp.text}")
        return None
    except Exception as e:
        print(f"Token exception: {e}")
        return None


@router.get("/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int, date: str = "2024-06-15"):
    instance_id = os.getenv("SH_INSTANCE_ID", "124a1bf0-7510-4b11-9334-8eec5917c9d7")
    token = get_access_token()
    if not token:
        return Response(status_code=401)
    url = f"https://services.sentinel-hub.com/ogc/wmts/{instance_id}"
    params = {
        "SERVICE": "WMTS",
        "REQUEST": "GetTile",
        "VERSION": "1.0.0",
        "LAYER": "1_TRUE_COLOR",
        "STYLE": "default",
        "FORMAT": "image/jpeg",
        "TILEMATRIXSET": "PopularWebMercator",
        "TIME": date,
        "TILEMATRIX": z,
        "TILEROW": y,
        "TILECOL": x,
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"Tile status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Tile error: {resp.text[:300]}")
            return Response(status_code=resp.status_code)
        return Response(
            content=resp.content,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except Exception as e:
        print(f"Tile exception: {e}")
        return Response(status_code=500)