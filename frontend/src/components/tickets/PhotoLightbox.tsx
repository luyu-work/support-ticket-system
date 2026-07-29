"use client";

import { useEffect } from "react";

interface PhotoLightboxProps {
  src: string | null;
  alt?: string;
  onClose: () => void;
}

export function PhotoLightbox({ src, alt = "Просмотр фото", onClose }: PhotoLightboxProps) {
  useEffect(() => {
    if (!src) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [src, onClose]);

  if (!src) return null;

  return (
    <div className="photo-lightbox">
      <div className="photo-lightbox-backdrop" onClick={onClose} />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="photo-lightbox-image" src={src} alt={alt} />
      <button
        type="button"
        className="icon-button photo-lightbox-close"
        aria-label="Закрыть фото"
        onClick={onClose}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <path
            d="M12 12L8.00001 8.00001M8.00001 8.00001L4 4M8.00001 8.00001L12 4M8.00001 8.00001L4 12"
            stroke="#F1F5FF"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}
