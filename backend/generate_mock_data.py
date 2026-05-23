"""
開発用モックデータ生成スクリプト
Copernicus アカウントなしでもアプリを動かせます。

実行方法:
  python generate_mock_data.py

生成物:
  - data/metadata/YYYY-MM-DD.json  (2020年〜現在の月次データ)
  - data/images/YYYY-MM-DD.png     (グレースケールのダミー画像)
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

METADATA_DIR = Path("data/metadata")
IMAGES_DIR = Path("data/images")
LAT = 43.0687
LON = 141.3508
BBOX_HALF = 0.03


def generate_mock_image(date_str: str, cloud_coverage: float) -> Path:
    """工事進捗を模したダミー衛星画像を生成"""
    width, height = 512, 512

    # 年月から工事進捗度を計算 (2020年=0%, 2028年=100%)
    year, month, *_ = map(int, date_str.split("-"))
    progress = max(0, min(1, (year - 2020 + month / 12) / 8.0))

    # ベースの都市画像 (グレーの碁盤状)
    img = Image.new("RGB", (width, height), color=(30, 35, 40))
    draw = ImageDraw.Draw(img)

    # 背景: 建物ブロック
    random.seed(hash(date_str) % 10000)
    for _ in range(80):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        w = random.randint(10, 40)
        h = random.randint(10, 40)
        shade = random.randint(60, 120)
        draw.rectangle([x, y, x + w, y + h], fill=(shade, shade, shade - 5))

    # 道路網 (グリッド)
    for i in range(0, width, 40):
        draw.line([(i, 0), (i, height)], fill=(50, 55, 60), width=3)
    for j in range(0, height, 40):
        draw.line([(0, j), (width, j)], fill=(50, 55, 60), width=3)

    # 工事エリア (中央) - 進捗によって変化
    cx, cy = width // 2, height // 2
    site_size = int(80 + progress * 60)

    # 工事前: 茶色い土地
    draw.rectangle(
        [cx - site_size, cy - site_size // 2, cx + site_size, cy + site_size // 2],
        fill=(int(100 + progress * 40), int(80 + progress * 20), 50),
    )

    # 進捗に応じてコンクリート構造物を追加
    if progress > 0.2:
        # 基礎工事
        draw.rectangle(
            [cx - 60, cy - 20, cx + 60, cy + 20],
            fill=(150, 150, 145),
        )
    if progress > 0.5:
        # ホームの骨格
        for rail in [-30, 0, 30]:
            draw.rectangle(
                [cx - 80, cy + rail - 4, cx + 80, cy + rail + 4],
                fill=(180, 180, 175),
            )
    if progress > 0.8:
        # 駅舎
        draw.rectangle(
            [cx - 50, cy - 40, cx + 50, cy + 40],
            fill=(200, 200, 195),
        )

    # 雲 (雲量に応じてオーバーレイ)
    if cloud_coverage > 5:
        cloud_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cloud_draw = ImageDraw.Draw(cloud_overlay)
        random.seed(hash(date_str + "cloud") % 10000)
        for _ in range(int(cloud_coverage / 5)):
            cx2 = random.randint(0, width)
            cy2 = random.randint(0, height)
            r = random.randint(20, 80)
            alpha = random.randint(80, 180)
            cloud_draw.ellipse(
                [cx2 - r, cy2 - r // 2, cx2 + r, cy2 + r // 2],
                fill=(240, 240, 245, alpha),
            )
        img = Image.alpha_composite(img.convert("RGBA"), cloud_overlay).convert("RGB")

    # 日付ウォーターマーク
    draw2 = ImageDraw.Draw(img)
    draw2.text((8, 8), f"S2 {date_str}", fill=(0, 255, 100))
    draw2.text((8, 24), f"Cloud: {cloud_coverage:.1f}%", fill=(0, 200, 80))
    draw2.text((8, height - 20), "MOCK DATA", fill=(255, 100, 0))

    save_path = IMAGES_DIR / f"{date_str}.png"
    img.save(save_path)
    return save_path


def main():
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("🛰️  モックデータ生成開始...")

    start = datetime(2020, 1, 1)
    end = datetime.utcnow()
    current = start
    count = 0

    while current <= end:
        year, month = current.year, current.month

        # ランダムな雲量 (北海道の季節性を模倣)
        # 冬は雲が多い傾向
        base_cloud = 25 if month in [11, 12, 1, 2] else 12
        cloud = max(0, min(100, random.gauss(base_cloud, 8)))

        # 月の中旬頃の日付
        day = random.randint(10, 20)
        try:
            date = datetime(year, month, day)
        except ValueError:
            date = datetime(year, month, 15)

        date_str = date.strftime("%Y-%m-%d")

        # 既存チェック
        if (METADATA_DIR / f"{date_str}.json").exists():
            pass
        else:
            # 画像生成
            try:
                png_path = generate_mock_image(date_str, cloud)
                size_kb = png_path.stat().st_size // 1024

                # メタデータ保存
                meta = {
                    "date": date_str,
                    "year": year,
                    "month": month,
                    "product_id": f"MOCK_{date_str.replace('-', '')}",
                    "product_name": f"S2A_MSIL2A_{date_str.replace('-', '')}_MOCK",
                    "cloud_coverage": round(cloud, 1),
                    "downloaded": True,
                    "is_mock": True,
                    "image_path": f"/static/images/{date_str}.png",
                    "file_size_kb": size_kb,
                    "bbox": {
                        "west": LON - 0.03, "south": LAT - 0.03,
                        "east": LON + 0.03, "north": LAT + 0.03,
                    },
                    "center": {"lat": LAT, "lon": LON},
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                }

                with open(METADATA_DIR / f"{date_str}.json", "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

                count += 1
                print(f"  ✅ {date_str}: 雲量{cloud:.1f}% ({size_kb}KB)")

            except Exception as e:
                print(f"  ❌ {date_str}: {e}")

        # 次の月へ
        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)

    print(f"\n✅ 完了! {count}件のモックデータを生成しました")
    print(f"   メタデータ: {METADATA_DIR.absolute()}")
    print(f"   画像: {IMAGES_DIR.absolute()}")


if __name__ == "__main__":
    main()
