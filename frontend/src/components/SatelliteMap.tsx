"use client";
import { useEffect, useRef } from "react";
import { ImageMetadata } from "@/lib/api";

interface SatelliteMapProps {
  selectedImage: ImageMetadata | null;
  opacity: number;
}

const SAPPORO = { lat: 43.0687, lon: 141.3508 };
const INITIAL_ZOOM = 14;

export default function SatelliteMap({ selectedImage, opacity }: SatelliteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);

  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    import("leaflet").then((L) => {
      const map = L.map(mapRef.current!, {
        center: [SAPPORO.lat, SAPPORO.lon],
        zoom: INITIAL_ZOOM,
      });

      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com">CARTO</a>',
          subdomains: "abcd",
          maxZoom: 20,
        }
      ).addTo(map);

      L.circleMarker([SAPPORO.lat, SAPPORO.lon], {
        radius: 8,
        fillColor: "#00ff88",
        color: "#00ff88",
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.4,
      }).addTo(map).bindTooltip("🚄 北海道新幹線 札幌駅工事エリア");

      leafletMapRef.current = map;
    });

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  const openCopernicus = () => {
    if (!selectedImage) return;
    const date = selectedImage.date;
    const fromTime = `${date}T00:00:00.000Z`;
    const toTime = `${date}T23:59:59.999Z`;
    const url = `https://browser.dataspace.copernicus.eu/?zoom=14&lat=43.0687&lng=141.3508&themeId=DEFAULT-THEME&visualizationUrl=https%3A%2F%2Fsh.dataspace.copernicus.eu%2Fogc%2Fwms%2Fa91f72b5-f393-4320-bc0f-990129bd9e63&datasetId=S2L2A&fromTime=${encodeURIComponent(fromTime)}&toTime=${encodeURIComponent(toTime)}&layerId=1_TRUE_COLOR`;
    window.open(url, "_blank");
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <div ref={mapRef} className="w-full h-full" style={{ background: "#0a0f14" }} />
      {selectedImage && (
        <button
          onClick={openCopernicus}
          style={{
            position: "absolute",
            bottom: "16px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(0, 229, 160, 0.9)",
            color: "#000",
            border: "none",
            borderRadius: "8px",
            padding: "10px 20px",
            fontSize: "13px",
            fontWeight: "600",
            cursor: "pointer",
            zIndex: 1000,
          }}
        >
          🛰️ {selectedImage.date} の衛星画像を見る
        </button>
      )}
    </div>
  );
}
