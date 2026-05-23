// ===== 型定義 =====
export interface ImageMetadata {
  date: string;
  year: number;
  month: number;
  product_id: string;
  product_name: string;
  cloud_coverage: number;
  downloaded: boolean;
  is_mock?: boolean;
  image_path: string | null;
  file_size_kb?: number;
  bbox: {
    west: number;
    south: number;
    east: number;
    north: number;
  };
  center: { lat: number; lon: number };
  fetched_at: string;
}

export interface ImagesResponse {
  count: number;
  images: ImageMetadata[];
}

// ===== APIクライアント =====
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchImages(params?: {
  year?: number;
  max_cloud?: number;
}): Promise<ImagesResponse> {
  const url = new URL(`${API_BASE}/api/images`);
  if (params?.year) url.searchParams.set("year", String(params.year));
  if (params?.max_cloud) url.searchParams.set("max_cloud", String(params.max_cloud));

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function fetchLatestImage(): Promise<ImageMetadata> {
  const res = await fetch(`${API_BASE}/api/images/latest`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export function getImageUrl(imagePath: string | null): string | null {
  if (!imagePath) return null;
  // imagePath は "/static/images/2024-06-15.png" 形式
  return `${API_BASE}${imagePath}`;
}
