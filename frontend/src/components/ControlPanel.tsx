"use client";
import { Layers, RefreshCw, Info, Satellite } from "lucide-react";
import { ImageMetadata } from "@/lib/api";

interface ControlPanelProps {
  opacity: number;
  onOpacityChange: (v: number) => void;
  selectedImage: ImageMetadata | null;
  totalCount: number;
  onRefresh: () => void;
  loading: boolean;
}

export default function ControlPanel({
  opacity,
  onOpacityChange,
  selectedImage,
  totalCount,
  onRefresh,
  loading,
}: ControlPanelProps) {
  return (
    <div className="control-panel">
      {/* タイトル */}
      <div className="panel-header">
        <Satellite size={16} className="icon-accent" />
        <span className="panel-title">Sentinel-2 ビューア</span>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="refresh-btn"
          aria-label="再読み込み"
        >
          <RefreshCw size={14} className={loading ? "spinning" : ""} />
        </button>
      </div>

      {/* 衛星画像透明度 */}
      <div className="control-section">
        <div className="control-label">
          <Layers size={13} />
          <span>衛星画像の透明度</span>
          <span className="control-value">{Math.round(opacity * 100)}%</span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={opacity}
          onChange={(e) => onOpacityChange(Number(e.target.value))}
          className="range-input opacity-slider"
        />
      </div>

      {/* 画像情報 */}
      {selectedImage && (
        <div className="control-section">
          <div className="control-label">
            <Info size={13} />
            <span>画像情報</span>
          </div>
          <div className="info-grid">
            <InfoRow label="観測日" value={selectedImage.date} />
            <InfoRow label="雲量" value={`${selectedImage.cloud_coverage.toFixed(1)}%`} />
            <InfoRow label="取得済" value={`${totalCount}枚`} />
            {selectedImage.is_mock && (
              <InfoRow label="種別" value="モックデータ" accent />
            )}
          </div>
        </div>
      )}

      {/* データソース */}
      <div className="data-source">
        <span>データ: Copernicus Sentinel-2</span>
        <span>© ESA {new Date().getFullYear()}</span>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="info-row">
      <span className="info-label">{label}</span>
      <span className={`info-value ${accent ? "accent" : ""}`}>{value}</span>
    </div>
  );
}
