"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { useImages } from "@/hooks/useImages";
import TimelineSlider from "@/components/TimelineSlider";
import ControlPanel from "@/components/ControlPanel";
import { AlertCircle, Satellite } from "lucide-react";

// LeafletはSSR非対応のためダイナミックインポート
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
{/* ヘッダー */}
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

{/* メインコンテンツ */}
<main className="app-main">
{/* エラー表示 */}
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

{/* 地図エリア */}
<div className="map-area">
<SatelliteMap selectedImage={selectedImage} opacity={opacity} />

{/* 右パネル (コントロール) */}
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

{/* 下部タイムラインスライダー */}
<div className="bottom-bar">
{loading ? (
<div className="bottom-loading">
<div className="pulse-bar" />
<span>衛星画像データを取得中...</span>
</div>
) : images.length === 0 ? (
<div className="bottom-empty">
<p>
画像がありません。バックエンドで{" "}
<code>python generate_mock_data.py</code> を実行してください。
</p>
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

{/* フッター */}
<footer className="app-footer">
<span>© 2026 Sapporo Satellite Viewer</span>
<span>Copernicus Sentinel-2 · ESA</span>
<a
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
