"use client";
import { useState, useEffect, useCallback } from "react";
import { fetchImages, ImageMetadata } from "@/lib/api";

export function useImages() {
  const [images, setImages] = useState<ImageMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchImages({ max_cloud: 100 });
      // 日付昇順でソート
      const sorted = [...data.images].sort((a, b) =>
        a.date.localeCompare(b.date)
      );
      setImages(sorted);
      // 最新(末尾)を初期選択
      if (sorted.length > 0) setSelectedIndex(sorted.length - 1);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "APIに接続できません。バックエンドが起動しているか確認してください。"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const selectedImage = images[selectedIndex] ?? null;

  const goNext = () => {
    if (selectedIndex < images.length - 1) setSelectedIndex((i) => i + 1);
  };

  const goPrev = () => {
    if (selectedIndex > 0) setSelectedIndex((i) => i - 1);
  };

  return {
    images,
    loading,
    error,
    selectedIndex,
    setSelectedIndex,
    selectedImage,
    goNext,
    goPrev,
    refresh: load,
  };
}
