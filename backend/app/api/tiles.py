from fastapi import APIRouter, Response
import requests
import os

router = APIRouter()

def get_access_token():
    client_id = os.getenv("SH_CLIENT_ID")
    client_secret = os.getenv("SH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ SH_CLIENT_ID または SH_CLIENT_SECRET が未設定")
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
    print(f"🔑 トークン取得: {resp.status_code}")
    if resp.status_code == 200:
        return resp.json().get("access_token")
    print(f"❌ トークンエラー: {resp.text}")
    return None


@router.get("/{z}/{x}/{y}")
def get_tile(z: int, x: int, y: int, date: str = "2024-06-15"):
    instance_id = os.getenv("SH_INSTANCE_ID", "124a1bf0-7510-4b11-9334-8eec5917c9d7")
    
    token = get_access_token()
    if not token:
