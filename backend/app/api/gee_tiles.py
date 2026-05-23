
"""
Google Earth Engine タイルAPI
"""
from fastapi import APIRouter, Response
import ee
import os
import requests

router = APIRouter()

def init_gee():
    """GEEを初期化する"""
    try:
        service_account = os.getenv("GEE_SERVICE_ACCOUNT")
        private_key = os.getenv("GEE_PRIVATE_KEY", "").replace("\\n", "\n")
        
        if not service_account or not private_key:
            return False
        
        credentials = ee.ServiceAccountCredentials(
            service_account,
            key_data=private_key
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        print(f"GEE初期化エラー: {e}")
        return False


@router.get("/{z}/{x}/{y}")
def get_gee_tile(z: int, x: int, y: int, date: str = "2024-06-15"):
    """
    Google Earth EngineからSentinel-2タイルを取得する
    """
    try:
        if not init_gee():
            return Response(status_code=503)

        # 日付範囲（前後15日）
        from datetime import datetime, timedelta
        dt = datetime.strptime(date, "%Y-%m-%d")
        start = (dt - timedelta(days=15)).strftime("%Y-%m-%d")
        end = (dt + timedelta(days=15)).strftime("%Y-%m-%d")

        # Sentinel-2画像を取得
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(ee.Geometry.Point([141.3508, 43.0687]))
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        image = collection.first()

        # RGB表示
        vis_params = {
            "bands": ["B4", "B3", "B2"],
            "min": 0,
            "max": 3000,
            "gamma": 1.4,
        }

        map_id = image.getMapId(vis_params)
        tile_url = map_id["tile_fetcher"].url_format.format(x=x, y=y, z=z)

        resp = requests.get(tile_url, timeout=15)
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        return Response(status_code=resp.status_code)

    except Exception as e:
        print(f"GEEタイルエラー: {e}")
        return Response(status_code=500)
