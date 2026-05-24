"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { useImages } from "@/hooks/useImages";
import TimelineSlider from "@/components/TimelineSlider";
import ControlPanel from "@/components/ControlPanel";
import { AlertCircle, Satellite } from "lucide-react";

const SatelliteMap = dynamic(() => import("@/components/SatelliteMap"), {
  ssr: false,
  loading: () => (
    <div className="map-loading">
      <div className="map-loading-inner">
        <div className="orbit-ring" />
        <span>地図を読み込み中...</span>
      </div>
    </div>
  ),
});

export default function HomePage() {
  const { images, loading, error, selectedIndex, setSelectedIndex, selectedImage, goNext, goPrev, refresh } =
    useImages();
  const [opacity, setOpacity] = useState(0.75);

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-left">
          <div className="header-icon-wrap">
            <Satellite size={20} className="header-icon" />
          </div>
          <div>
            <h1 className="header-title">札幌駅新幹線工事 変化ビューア</h1>
            <p className="header-sub">北海道新幹線延伸工事エリア · Sentinel-2 衛星観測</p>
          </div>
        </div>
        <div className="header-right">
          {loading && <div className="loading-dot" />}
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <AlertCircle size={16} />
            <div>
              <strong>APIエラー:</strong> {error}
              <br />
              <small>
                バックエンドを起動してください:{" "}
                <code>cd backend && uvicorn app.main:app --reload</code>
              </small>
            </div>
          </div>
        )}

        <div className="map-area">
          <SatelliteMap selectedImage={selectedImage} opacity={opacity} />
          <div className="side-panel">
            <ControlPanel
              opacity={opacity}
              onOpacityChange={setOpacity}
              selectedImage={selectedImage}
              totalCount={images.length}
              onRefresh={refresh}
              loading={loading}
            />
          </div>
        </div>

        <div className="bottom-bar">
          {loading ? (
            <div className="bottom-loading">
              <div className="pulse-bar" />
              <span>衛星画像データを取得中...</span>
            </div>
          ) : images.length === 0 ? (
            <div className="bottom-empty">
              <p>データがありません。</p>
            </div>
          ) : (
            <TimelineSlider
              images={images}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
              onPrev={goPrev}
              onNext={goNext}
            />
          )}
        </div>
      </main>

      <footer className="app-footer">
        <span>© {new Date().getFullYear()} Sapporo Satellite Viewer</span>
        <span>Copernicus Sentinel-2 · ESA</span>
        
          href="https://github.com/tomohiro-kudo-dev/sapporo-satellite"
          target="_blank"
          rel="noreferrer"
          className="footer-link"
        >
          GitHub
        </a>
      </footer>
    </div>
  );
}
