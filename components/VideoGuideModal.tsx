"use client";

import { useEffect, useState, useRef } from "react";
import { X, Play, Video as VideoIcon, Upload, AlertCircle } from "lucide-react";

interface VideoGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  // Can be a local path like "/guide/how-to-use.mp4" or a YouTube link/ID
  videoSource?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT CONFIGURATION:
// Put your video file in `frontend/public/guide/how-to-use.mp4`
// OR put a YouTube link / ID (e.g. "https://www.youtube.com/watch?v=XXXX" or "XXXX")
// ─────────────────────────────────────────────────────────────────────────────
export const DEFAULT_VIDEO_SOURCE = "/guide/how-to-use.mp4";

function extractYouTubeId(urlOrId: string): string | null {
  if (!urlOrId) return null;
  const trimmed = urlOrId.trim();
  
  // Direct 11-char ID
  if (/^[a-zA-Z0-9_-]{11}$/.test(trimmed)) {
    return trimmed;
  }
  
  // youtu.be/<id>
  const shortMatch = trimmed.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/);
  if (shortMatch) return shortMatch[1];
  
  // youtube.com/watch?v=<id>
  const longMatch = trimmed.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
  if (longMatch) return longMatch[1];
  
  // youtube.com/embed/<id>
  const embedMatch = trimmed.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/);
  if (embedMatch) return embedMatch[1];

  return null;
}

export default function VideoGuideModal({
  isOpen,
  onClose,
  videoSource = DEFAULT_VIDEO_SOURCE,
}: VideoGuideModalProps) {
  const [hasError, setHasError] = useState(false);
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Close on Escape key press
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
      setHasError(false);
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const currentSource = localPreviewUrl || videoSource;
  const youtubeId = extractYouTubeId(currentSource);
  const isDirectVideo = !youtubeId && Boolean(currentSource);

  const handleCustomFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (localPreviewUrl) URL.revokeObjectURL(localPreviewUrl);
      const url = URL.createObjectURL(file);
      setLocalPreviewUrl(url);
      setHasError(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col items-center justify-between p-3 sm:p-5 md:p-6 animate-in fade-in duration-200 select-none"
      onClick={onClose}
    >
      {/* ── Top Bar ── */}
      <div
        className="w-full max-w-7xl flex items-center justify-between z-10 shrink-0 pb-2 sm:pb-3"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 text-white">
          <div className="w-8 h-8 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <VideoIcon className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-semibold leading-tight">How to Use — Video Demonstration</h2>
            <p className="text-[11px] sm:text-xs text-gray-400">Full-screen visual walkthrough of Braille Recognition</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800/90 hover:bg-gray-700 text-gray-300 hover:text-white rounded-xl border border-gray-700 transition-all text-xs sm:text-sm font-medium shadow-lg hover:scale-105 active:scale-95"
          title="Close (Esc)"
        >
          <X className="w-4 h-4" />
          <span className="hidden sm:inline">Close</span>
        </button>
      </div>

      {/* ── Main Full-Screen Video Frame ── */}
      <div
        className="relative w-full max-w-7xl flex-1 flex items-center justify-center overflow-hidden rounded-2xl bg-black border border-gray-800 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {youtubeId ? (
          // YouTube Fullscreen Embed
          <iframe
            className="w-full h-full rounded-2xl"
            src={`https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&rel=0&modestbranding=1&playsinline=1`}
            title="How to Use Braille Recognition"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          />
        ) : isDirectVideo && !hasError ? (
          // Native HTML5 Full-screen Video Player
          <video
            ref={videoRef}
            src={currentSource}
            controls
            autoPlay
            playsInline
            onError={() => setHasError(true)}
            className="w-full h-full max-h-[85vh] object-contain rounded-2xl bg-black"
          />
        ) : (
          // Sleek Fallback Placeholder if video file hasn't been added yet
          <div className="flex flex-col items-center justify-center text-center p-6 max-w-md">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4 shadow-[0_0_30px_rgba(59,130,246,0.2)]">
              <Play className="w-8 h-8 sm:w-10 sm:h-10 ml-1 text-blue-400" />
            </div>

            <h3 className="text-base sm:text-lg font-bold text-white mb-1.5">Video Demonstration Ready</h3>
            <p className="text-xs sm:text-sm text-gray-400 leading-relaxed mb-4">
              Place your demonstration video at:
              <br />
              <code className="text-xs text-blue-300 bg-blue-950/60 border border-blue-500/30 px-2 py-0.5 rounded-md mt-1 inline-block">
                frontend/public/guide/how-to-use.mp4
              </code>
              <br />
              or configure a YouTube video link.
            </p>

            <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs sm:text-sm font-medium transition-all shadow-lg shadow-blue-600/20 cursor-pointer">
              <Upload className="w-4 h-4" />
              <span>Select video file from device</span>
              <input
                type="file"
                accept="video/mp4,video/webm,video/ogg,video/quicktime"
                onChange={handleCustomFileSelect}
                className="hidden"
              />
            </label>
          </div>
        )}
      </div>

      {/* ── Bottom Hint ── */}
      <div
        className="w-full max-w-7xl flex items-center justify-between text-[11px] text-gray-500 pt-2 shrink-0 px-1"
        onClick={(e) => e.stopPropagation()}
      >
        <span>Press <kbd className="px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded border border-gray-700">ESC</kbd> or click outside to exit full-screen mode</span>
        <span>Braille Recognition</span>
      </div>
    </div>
  );
}
