"""
Sentinel-2衛星画像取得スクリプト
"""
import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

LAT = 43.0687
LON = 141.3508
BBOX_HALF = 0.03

BBOX = (
    LON - BBOX_HALF,
    LAT - BBOX_HALF,
    LON + BBOX_HALF,
    LAT + BBOX_HALF,
)

MAX_CLOUD_COVERAGE = 20
START_DATE = "2020-01-01"
COLLECTION = "SENTINEL-2"

IMAGES_DIR = Path("data/images")
METADATA_DIR = Path("data/metadata")

CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_DOWNLOAD_BASE = "https://download.dataspace.copernicus.eu/odata/v1/Products"


def get_access_token(username: str, password: str) -> str:
    resp = requests.post(
        CDSE_TOKEN_URL,
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": "cdse-public",
        },
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("✅ 認証成功")
    return token


def search_sentinel2(token, start_date, end_date, max_cloud=MAX_CLOUD_COVERAGE):
    west, south, east, north = BBOX
    footprint = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
    params = {
        "$filter": (
            f"Collection/Name eq '{COLLECTION}' "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') "
            f"and ContentDate/Start gt {start_date}T00:00:00.000Z "
            f"and ContentDate/Start lt {end_date}T23:59:59.000Z "
            f"and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {max_cloud}) "
            f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')"
        ),
        "$orderby": "ContentDate/Start asc",
        "$top": 50,
        "$expand": "Attributes",
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(CDSE_SEARCH_URL, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    products = resp.json().get("value", [])
    print(f"  🔍 {start_date} ~ {end_date}: {len(products)}件ヒット")
    return products


def download_thumbnail(product_id: str, token: str, save_path: Path) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    urls = [
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/Nodes(QUICKLOOK.jpg)/$value",
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/Nodes(preview.jpg)/$value",
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/Nodes(PREVIEW.JPG)/$value",
        f"{CDSE_DOWNLOAD_BASE}({product_id})/Nodes(QUICKLOOK.jpg)/$value",
    ]
    try:
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=60, stream=True)
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    size = save_path.stat().st_size
                    if size > 1000:
                        print(f"    ✅ ダウンロード完了: {save_path.name} ({size // 1024}KB)")
                        return True
            except Exception:
                continue
        print(f"    ⚠️ QuickLookが見つかりません")
        return False
    except Exception as e:
        print(f"    ❌ ダウンロード失敗: {e}")
        return False


def extract_cloud_coverage(product: dict) -> float:
    attrs = product.get("Attributes", [])
    if isinstance(attrs, dict):
        attrs = attrs.get("OData.CSC.DoubleAttribute", [])
    if not isinstance(attrs, list):
        return 100.0
    for attr in attrs:
        if isinstance(attr, dict) and attr.get("Name") == "cloudCover":
            return round(attr.get("Value", 100), 1)
    return 100.0


def save_metadata(product, date_str, cloud, downloaded):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    meta = {
        "date": date_str,
        "year": dt.year,
        "month": dt.month,
        "product_id": product.get("Id", ""),
        "product_name": product.get("Name", ""),
        "cloud_coverage": cloud,
        "downloaded": downloaded,
        "image_path": f"/static/images/{date_str}.png" if downloaded else None,
        "bbox": {"west": BBOX[0], "south": BBOX[1], "east": BBOX[2], "north": BBOX[3]},
        "center": {"lat": LAT, "lon": LON},
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    json_path = METADATA_DIR / f"{date_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"    📝 メタデータ保存: {json_path.name}")


def fetch_by_month_range(token, start_year, start_month, end_year, end_month, max_cloud):
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    downloaded_count = 0

    while current <= end:
        year, month = current.year, current.month
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        start_str = f"{year}-{month:02d}-01"
        end_str = f"{year}-{month:02d}-{last_day}"

        existing = list(METADATA_DIR.glob(f"{year}-{month:02d}-*.json"))
        if existing:
            print(f"  ⏭️  {year}-{month:02d}: スキップ (既存: {existing[0].name})")
            if month == 12:
                current = datetime(year + 1, 1, 1)
            else:
                current = datetime(year, month + 1, 1)
            continue

        print(f"\n📅 {year}-{month:02d} を処理中...")
        try:
            products = search_sentinel2(token, start_str, end_str, max_cloud)
        except Exception as e:
            print(f"  ❌ 検索エラー: {e}")
            time.sleep(5)
            if month == 12:
                current = datetime(year + 1, 1, 1)
            else:
                current = datetime(year, month + 1, 1)
            continue

        if not products:
            print(f"  ⚠️ {year}-{month:02d}: 雲量{max_cloud}%以下の画像なし")
            if month == 12:
                current = datetime(year + 1, 1, 1)
            else:
                current = datetime(year, month + 1, 1)
            continue

        best = min(products, key=lambda p: extract_cloud_coverage(p))
        cloud = extract_cloud_coverage(best)
        date_str = best["ContentDate"]["Start"][:10]
        print(f"  🛰️  最良候補: {date_str} (雲量: {cloud}%)")

        png_path = IMAGES_DIR / f"{date_str}.png"
        success = download_thumbnail(best["Id"], token, png_path)
        save_metadata(best, date_str, cloud, success)
        if success:
            downloaded_count += 1
        time.sleep(1)

        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)

    return downloaded_count


def main():
    parser = argparse.ArgumentParser(description="Sentinel-2衛星画像取得スクリプト")
    parser.add_argument("--year", type=int, help="取得する年")
    parser.add_argument("--month", type=str, help="取得する年月 (例: 2024-06)")
    parser.add_argument("--max-cloud", type=float, default=MAX_CLOUD_COVERAGE, help="雲量上限(percent)")
    parser.add_argument("--start", type=str, default=START_DATE, help="取得開始日")
    args = parser.parse_args()

    username = os.getenv("CDSE_USER")
    password = os.getenv("CDSE_PASSWORD")

    if not username or not password:
        print("❌ エラー: CDSE_USER と CDSE_PASSWORD を設定してください")
        sys.exit(1)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🛰️  札幌駅新幹線工事エリア Sentinel-2 取得開始")
    print(f"   座標: 緯度{LAT}, 経度{LON}")
    print(f"   雲量上限: {args.max_cloud}%")
    print("=" * 60)

    try:
        token = get_access_token(username, password)
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        sys.exit(1)

    today = datetime.utcnow()
    if args.month:
        year, month = map(int, args.month.split("-"))
        start_year, start_month = year, month
        end_year, end_month = year, month
    elif args.year:
        start_year, start_month = args.year, 1
        end_year, end_month = args.year, 12
    else:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        start_year, start_month = start.year, start.month
        end_year, end_month = today.year, today.month

    count = fetch_by_month_range(token, start_year, start_month, end_year, end_month, args.max_cloud)

    print("\n" + "=" * 60)
    print(f"✅ 完了! ダウンロード成功: {count}枚")
    print(f"   画像フォルダ: {IMAGES_DIR.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
