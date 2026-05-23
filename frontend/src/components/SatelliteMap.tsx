"use client";
import { ImageMetadata } from "@/lib/api";

interface SatelliteMapProps {
  selectedImage: ImageMetadata | null;
  opacity: number;
}

export default function SatelliteMap({ selectedImage, opacity }: SatelliteMapProps) {
  const date = selectedImage?.date ?? "2024-06-15";
  const fromTime = `${date}T00:00:00.000Z`;
  const toTime = `${date}T23:59:59.999Z`;

  const src = `https://browser.dataspace.copernicus.eu/?zoom=14&lat=43.0687&lng=141.3508&themeId=DEFAULT-THEME&visualizationUrl=https%3A%2F%2Fsh.dataspace.copernicus.eu%2Fogc%2Fwms%2Fa91f72b5-f393-4320-bc0f-990129bd9e63&evalscript=&datasetId=S2L2A&fromTime=${encodeURIComponent(fromTime)}&toTime=${encodeURIComponent(toTime)}&layerId=1_TRUE_COLOR`;

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <iframe
        src={src}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          opacity: opacity,
        }}
        allowFullScreen
        title="Copernicus Sentinel-2 衛星画像"
      />
    </div>
  );
}
