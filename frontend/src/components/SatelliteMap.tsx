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
      delete (L.Icon.Default.prototype as any)._getIconUrl;

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
      const fromTime = `${date}T00:00:00.000Z`;
      const toTime = `${date}T23:59:59.999Z`;
      
      const wmsUrl = "https://services.sentinel-hub.com/ogc/wms/";

      const wmsLayer = L.tileLayer.wms(
        `https://catalogue.dataspace.copernicus.eu/ogc/wms?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=TRUE-COLOR-S2L2A&STYLES=&FORMAT=image/jpeg&TIME=${date}&MAXCC=100`,
        {
          layers: "TRUE-COLOR-S2L2A",
          format: "image/jpeg",
          transparent: false,
          version: "1.3.0",
          opacity: opacity,
          attribution: "Copernicus Sentinel-2 © ESA",
        } as any
      );

      wmsLayer.addTo(leafletMapRef.current);
      overlayRef.current = wmsLayer;
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
