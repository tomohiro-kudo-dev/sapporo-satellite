"""
Sentinel-2衛星画像取得スクリプト
Copernicus Data Space Ecosystem (CDSE) APIを使用

使い方:
  python fetch_images.py                    # 全期間取得
  python fetch_images.py --year 2024        # 年指定
  python fetch_images.py --month 2024-06    # 月指定
  python fetch_images.py --max-cloud 15     # 雲量15%以下

事前準備:
  1. https://dataspace.copernicus.eu/ でアカウント作成 (無料)
  2. .envファイルに CDSE_USER と CDSE_PASSWORD を設定
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

# ========== 設定 ==========
LAT = 43.0687        # 札幌駅 緯度
LON = 141.3508       # 札幌駅 経度
BBOX_HALF = 0.03     # 表示範囲 (約3km)

BBOX = (
    LON - BBOX_HALF,  # west
    LAT - BBOX_HALF,  # south
    LON + BBOX_HALF,  # east
    LAT + BBOX_HALF,  # north
)

MAX_CLOUD_COVERAGE = 20   # 雲量上限 (%)
START_DATE = "2020-01-01" # 取得開始日
COLLECTION = "SENTINEL-2"

IMAGES_DIR = Path("data/images")
METADATA_DIR = Path("data/metadata")

CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_DOWNLOAD_BASE = "https://download.dataspace.copernicus.eu/odata/v1/Products"

# ==========================


def get_access_token(username: str, password: str) -> str:
    """CopernicusのOAuth2トークンを取得"""
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


def search_sentinel2(
    token: str,
    start_date: str,
    end_date: str,
    max_cloud: float = MAX_CLOUD_COVERAGE,
) -> list[dict]:
    """
    Sentinel-2画像をCDSEカタログで検索する
    """
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
    """
    サムネイル画像(Quick Look PNG)をダウンロードする。
    フルシーンではなくサムネイルを使用して容量を抑える。
    """
    url = f"{CDSE_DOWNLOAD_BASE}({product_id})/Nodes"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # ノード一覧を取得してQuickLookを探す
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        nodes = resp.json().get("value", [])

        # QuickLookまたはPREVIEWファイルを探す
        ql_node = None
        for node in nodes:
            name = node.get("Name", "").upper()
            if "QUICKLOOK" in name or "PREVIEW" in name or name.endswith(".JPG") or name.endswith(".PNG"):
                ql_node = node
                break

        if not ql_node:
            # サムネイルAPIを試す
            thumb_url = f"{CDSE_DOWNLOAD_BASE}({product_id})/Nodes/GRANULE"
            print(f"    ⚠️ QuickLookが見つかりません (product_id={product_id[:8]}...)")
            return False

        # ダウンロード
        dl_url = f"{CDSE_DOWNLOAD_BASE}({product_id})/Nodes({ql_node['Name']})/$value"
        dl_resp = requests.get(dl_url, headers=headers, timeout=120, stream=True)
        dl_resp.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"    ✅ ダウンロード完了: {save_path.name} ({save_path.stat().st_size // 1024}KB)")
        return True

    except Exception as e:
        print(f"    ❌ ダウンロード失敗: {e}")
        return False


def extract_cloud_coverage(product: dict) -> float:
    """プロダクトのメタデータから雲量を取得"""
    attrs = product.get("Attributes", {}).get("OData.CSC.DoubleAttribute", [])
    for attr in attrs:
        if attr.get("Name") == "cloudCover":
            return round(attr.get("Value", 100), 1)
    return 100.0


def save_metadata(product: dict, date_str: str, cloud: float, downloaded: bool):
    """メタデータをJSONファイルに保存"""
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
        "bbox": {
            "west": BBOX[0], "south": BBOX[1],
            "east": BBOX[2], "north": BBOX[3],
        },
        "center": {"lat": LAT, "lon": LON},
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }

    json_path = METADATA_DIR / f"{date_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"    📝 メタデータ保存: {json_path.name}")


def fetch_by_month_range(
    token: str,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    max_cloud: float,
):
    """月ごとに1枚（最も雲量が少ない）を取得"""
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    downloaded_count = 0

    while current <= end:
        year, month = current.year, current.month

        # 月末日を計算
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day

        start_str = f"{year}-{month:02d}-01"
        end_str = f"{year}-{month:02d}-{last_day}"

        # 既にダウンロード済みか確認
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

        # 最も雲量が少ないものを選ぶ
        best = min(products, key=lambda p: extract_cloud_coverage(p))
        cloud = extract_cloud_coverage(best)
        date_str = best["ContentDate"]["Start"][:10]

        print(f"  🛰️  最良候補: {date_str} (雲量: {cloud}%)")

        # PNG画像をダウンロード
        png_path = IMAGES_DIR / f"{date_str}.png"
        success = download_thumbnail(best["Id"], token, png_path)
        save_metadata(best, date_str, cloud, success)

        if success:
            downloaded_count += 1

        time.sleep(1)  # APIレート制限対策

        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)

    return downloaded_count


def main():
    parser = argparse.ArgumentParser(description="Sentinel-2衛星画像取得スクリプト")
    parser.add_argument("--year", type=int, help="取得する年 (例: 2024)")
    parser.add_argument("--month", type=str, help="取得する年月 (例: 2024-06)")
    parser.add_argument("--max-cloud", type=float, default=MAX_CLOUD_COVERAGE, help="雲量上限(percent)")
    parser.add_argument("--start", type=str, default=START_DATE, help="取得開始日 (YYYY-MM-DD)")
    args = parser.parse_args()

    # 認証情報
    username = os.getenv("CDSE_USER")
    password = os.getenv("CDSE_PASSWORD")

    if not username or not password:
        print("❌ エラー: .envファイルに CDSE_USER と CDSE_PASSWORD を設定してください")
        print("   https://dataspace.copernicus.eu/ でアカウント作成(無料)")
        sys.exit(1)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🛰️  札幌駅新幹線工事エリア Sentinel-2 取得開始")
    print(f"   座標: 緯度{LAT}, 経度{LON}")
    print(f"   雲量上限: {args.max_cloud}%")
    print("=" * 60)

    # トークン取得
    try:
        token = get_access_token(username, password)
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        sys.exit(1)

    # 期間設定
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

    count = fetch_by_month_range(
        token,
        start_year, start_month,
        end_year, end_month,
        args.max_cloud,
    )

    print("\n" + "=" * 60)
    print(f"✅ 完了! ダウンロード成功: {count}枚")
    print(f"   画像フォルダ: {IMAGES_DIR.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
