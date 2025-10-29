import React, { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Maximize2, X } from "lucide-react";
// Use images from project img/ folder (bundled by Vite)
import step3ChatInput from "../../img/step3-chat-input.png";
import step3Generating from "../../img/step3-generating.png";
import step3ResultDrag from "../../img/step3-result-drag.png";

/**
 * Step3Carousel
 * - Left-column friendly carousel with lightbox for Step 3 showcase.
 * - Defaults to images under frontend/img imported via Vite bundling
 *
 * Props:
 * - images: Array<{ src: string, alt: string, badge?: string }>
 */
export default function Step3Carousel({ images = defaultSlides }) {
  const [idx, setIdx] = useState(0);
  const [open, setOpen] = useState(false);

  const prev = () => setIdx((i) => (i - 1 + images.length) % images.length);
  const next = () => setIdx((i) => (i + 1) % images.length);

  // Keyboard nav when lightbox is open
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="relative rounded-[1.8rem] border bg-white shadow overflow-hidden">
      <div className="relative w-full bg-neutral-50" style={{ aspectRatio: "4/5" }}>
        <img
          src={images[idx].src}
          alt={images[idx].alt}
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
        />
        {/* badge */}
        {images[idx].badge && (
          <div className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-black/60 text-white text-xs px-3 py-1">
            <span className="font-medium">{images[idx].badge}</span>
          </div>
        )}
        {/* controls */}
        {images.length > 1 && (
          <>
            <button
              aria-label="이전"
              onClick={prev}
              className="absolute left-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-white/85 text-neutral-800 shadow hover:bg-white"
            >
              <ChevronLeft className="mx-auto" />
            </button>
            <button
              aria-label="다음"
              onClick={next}
              className="absolute right-3 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-white/85 text-neutral-800 shadow hover:bg-white"
            >
              <ChevronRight className="mx-auto" />
            </button>
          </>
        )}
        {/* dots */}
        {images.length > 1 && (
          <div className="absolute inset-x-0 bottom-3 flex justify-center">
            <div className="bg-white/80 rounded-full px-2 py-1 shadow">
              {images.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setIdx(i)}
                  className={`mx-1 h-2 w-2 rounded-full ${i === idx ? "bg-neutral-900" : "bg-neutral-400"}`}
                  aria-label={`슬라이드 ${i + 1}`}
                />
              ))}
            </div>
          </div>
        )}
        {/* enlarge */}
        <button
          onClick={() => setOpen(true)}
          className="absolute right-3 top-3 h-9 px-3 rounded-full bg-white/85 text-neutral-800 shadow hover:bg-white text-xs inline-flex items-center gap-1"
        >
          <Maximize2 className="size-4" /> 자세히 보기
        </button>
      </div>

      {/* Lightbox */}
      {open && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm">
          <button
            onClick={() => setOpen(false)}
            className="absolute right-6 top-6 h-10 w-10 rounded-full bg-white/90 text-neutral-800 shadow border"
            aria-label="닫기"
          >
            <X className="mx-auto" />
          </button>
          <div className="h-full w-full grid place-items-center p-6">
            <div className="relative w-full max-w-5xl aspect-video bg-black rounded-xl overflow-hidden">
              <img
                src={images[idx].src}
                alt={images[idx].alt}
                className="absolute inset-0 w-full h-full object-contain bg-black"
              />
              <button
                onClick={prev}
                className="absolute left-3 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-white/90 text-neutral-800 shadow"
                aria-label="이전"
              >
                <ChevronLeft className="mx-auto" />
              </button>
              <button
                onClick={next}
                className="absolute right-3 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-white/90 text-neutral-800 shadow"
                aria-label="다음"
              >
                <ChevronRight className="mx-auto" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const defaultSlides = [
  { src: step3ChatInput, alt: "채팅 입력 화면", badge: "프롬프트 입력" },
  { src: step3Generating, alt: "생성 대기 화면", badge: "생성 대기" },
  { src: step3ResultDrag, alt: "결과 드래그 화면", badge: "프리뷰로 드래그" },
];
