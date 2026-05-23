"use client";
import { ImageMetadata } from "@/lib/api";
import { ChevronLeft, ChevronRight, Cloud } from "lucide-react";

interface TimelineSliderProps {
  images: ImageMetadata[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  onPrev: () => void;
  onNext: () => void;
}

export default function TimelineSlider({
  images,
  selectedIndex,
  onSelect,
  onPrev,
  onNext,
}: TimelineSliderProps) {
  if (images.length === 0) return null;

  const selected = images[selectedIndex];

  return (
    <div className="timeline-panel">
      {/* 日付表示 */}
      <div className="date-display">
        <span className="date-label">観測日</span>
        <span className="date-value">{selected?.date ?? "---"}</span>
        {selected && (
          <span className="cloud-badge">
            <Cloud size={12} />
            {selected.cloud_coverage.toFixed(1)}%
            {selected.is_mock && <span className="mock-badge">MOCK</span>}
          </span>
        )}
      </div>

      {/* スライダー操作エリア */}
      <div className="slider-row">
        <button
          onClick={onPrev}
          disabled={selectedIndex === 0}
          className="nav-btn"
          aria-label="前の画像"
        >
          <ChevronLeft size={18} />
        </button>

        {/* レンジスライダー */}
        <div className="slider-track">
          <input
            type="range"
            min={0}
            max={images.length - 1}
            value={selectedIndex}
            onChange={(e) => onSelect(Number(e.target.value))}
            className="range-input"
            aria-label="時系列スライダー"
          />
          {/* 目盛り: 年ラベル */}
          <div className="tick-labels">
            {getYearTicks(images).map(({ label, pct }) => (
              <span
                key={label}
                className="tick"
                style={{ left: `${pct}%` }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>

        <button
          onClick={onNext}
          disabled={selectedIndex === images.length - 1}
          className="nav-btn"
          aria-label="次の画像"
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* 進捗バー */}
      <div className="progress-info">
        <span>{images[0]?.date?.slice(0, 7)}</span>
        <span className="progress-count">
          {selectedIndex + 1} / {images.length}
        </span>
        <span>{images[images.length - 1]?.date?.slice(0, 7)}</span>
      </div>
    </div>
  );
}

function getYearTicks(images: ImageMetadata[]) {
  if (images.length === 0) return [];
  const years = new Set(images.map((img) => img.year));
  return Array.from(years).map((year) => {
    const firstIdx = images.findIndex((img) => img.year === year);
    return {
      label: String(year),
      pct: (firstIdx / (images.length - 1)) * 100,
    };
  });
}
