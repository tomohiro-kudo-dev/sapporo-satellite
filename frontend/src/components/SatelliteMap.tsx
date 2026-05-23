"use client";
import { useEffect, useRef } from "react";
import { getImageUrl, ImageMetadata } from "@/lib/api";

interface SatelliteMapProps {
  selectedImage: ImageMetadata | null;
  opacity: number;
}

const SAPPORO = { lat: 43.0687, lon: 141.3508 };
const INITIAL_ZOOM = 14;

export default function SatelliteMap({ selectedImage, opacity }: SatelliteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const leafletMapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const overlayRef = useRef<any>(null);

  // マップ初期化 (クライアントサイドのみ)
  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    // Leafletをダイナミックインポート (SSR回避)
    import("leaflet").then((L) => {
      // デフォルトアイコンのパス修正
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "/leaflet/marker-icon-2x.png",
        iconUrl: "/leaflet/marker-icon.png",
        shadowUrl: "/leaflet/marker-shadow.png",
      });

      const map = L.map(mapRef.current!, {
        center: [SAPPORO.lat, SAPPORO.lon],
        zoom: INITIAL_ZOOM,
        zoomControl: true,
      });

      // ベースマップ: OSM (ダークスタイル)
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com">CARTO</a>',
          subdomains: "abcd",
          maxZoom: 20,
        }
      ).addTo(map);

      // 札幌駅マーカー
      const marker = L.circleMarker([SAPPORO.lat, SAPPORO.lon], {
        radius: 8,
        fillColor: "#00ff88",
        color: "#00ff88",
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.4,
      }).addTo(map);

      marker.bindTooltip("🚄 北海道新幹線 札幌駅工事エリア", {
        permanent: false,
        direction: "top",
      });

      leafletMapRef.current = map;
    });

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  // 衛星画像オーバーレイの更新
  useEffect(() => {
    if (!leafletMapRef.current) return;

    import("leaflet").then((L) => {
      // 既存オーバーレイを削除
      if (overlayRef.current) {
        overlayRef.current.remove();
        overlayRef.current = null;
      }

      if (!selectedImage?.image_path || !selectedImage.bbox) return;

      const imageUrl = getImageUrl(selectedImage.image_path);
      if (!imageUrl) return;

      const { west, south, east, north } = selectedImage.bbox;
      const bounds = L.latLngBounds([south, west], [north, east]);

      const overlay = L.imageOverlay(imageUrl, bounds, {
        opacity: opacity,
        interactive: false,
      });

      overlay.addTo(leafletMapRef.current);
      overlayRef.current = overlay;
    });
  }, [selectedImage]);

  // 透明度だけを更新 (画像再ロード不要)
  useEffect(() => {
    if (overlayRef.current) {
      overlayRef.current.setOpacity(opacity);
    }
  }, [opacity]);

  return (
    <div
      ref={mapRef}
      className="w-full h-full"
      style={{ background: "#0a0f14" }}
    />
  );
}
