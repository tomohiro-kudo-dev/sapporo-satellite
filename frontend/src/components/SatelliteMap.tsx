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
  const overlayRef = useRef<any>(null);

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

  useEffect(() => {
    if (!leafletMapRef.current || !selectedImage) return;

    import("leaflet").then((L) => {
      if (overlayRef.current) {
        overlayRef.current.remove();
        overlayRef.current = null;
      }

      const date = selectedImage.date;
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const tileUrl = `${apiBase}/api/tiles/{z}/{x}/{y}?date=${date}`;

      const layer = L.tileLayer(tileUrl, {
        opacity: opacity,
        attribution: "Google Earth Engine · Copernicus Sentinel-2 © ESA",
        tileSize: 256,
        maxZoom: 18,
      });

      layer.addTo(leafletMapRef.current);
      overlayRef.current = layer;
    });
  }, [selectedImage]);

  useEffect(() => {
    if (overlayRef.current) {
      overlayRef.current.setOpacity(opacity);
    }
  }, [opacity]);

  return (
    <div ref={mapRef} className="w-full h-full" style={{ background: "#0a0f14" }} />
  );
}
