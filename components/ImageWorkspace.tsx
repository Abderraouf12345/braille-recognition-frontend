"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload, Loader2, Move, MousePointerClick, RotateCcw, Check } from "lucide-react";
import { optimizeImageForUpload } from "../utils/imageCompressor";

interface Point {
  x: number;
  y: number;
}

interface ImageWorkspaceProps {
  imageFile: File | null;
  setImageFile: (file: File | null) => void;
  corners: Point[];
  setCorners: (corners: Point[]) => void;
  overlayImage?: string | null;
  onClearOverlay?: () => void;
  isLocked?: boolean;
}

const CORNER_NAMES = [
  "Top-Left (↖)",
  "Top-Right (↗)",
  "Bottom-Right (↘)",
  "Bottom-Left (↙)",
];

export default function ImageWorkspace({
  imageFile,
  setImageFile,
  corners,
  setCorners,
  overlayImage,
  onClearOverlay,
  isLocked,
}: ImageWorkspaceProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [selectionMode, setSelectionMode] = useState<"drag" | "click">("drag");
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setImageUrl(null);
      setImgSize({ width: 0, height: 0 });
      setSelectionMode("drag");
    }
  }, [imageFile]);

  useEffect(() => {
    const handleResize = () => setImgSize((prev) => ({ ...prev }));
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setImgSize({ width: naturalWidth, height: naturalHeight });

    // Initialize corners to image boundaries if in drag mode
    if (corners.length === 0 && selectionMode === "drag") {
      setCorners([
        { x: 0, y: 0 },
        { x: naturalWidth, y: 0 },
        { x: naturalWidth, y: naturalHeight },
        { x: 0, y: naturalHeight },
      ]);
    }
  };

  const handleModeSwitch = (mode: "drag" | "click") => {
    if (mode === selectionMode || isLocked) return;
    setSelectionMode(mode);

    if (mode === "click") {
      // Clear corners so user can click all 4 points sequentially
      setCorners([]);
    } else {
      // If switching back to drag mode and corners aren't complete, restore full bounds
      if (corners.length !== 4 && imgSize.width > 0 && imgSize.height > 0) {
        setCorners([
          { x: 0, y: 0 },
          { x: imgSize.width, y: 0 },
          { x: imgSize.width, y: imgSize.height },
          { x: 0, y: imgSize.height },
        ]);
      }
    }
  };

  const handleResetClickCorners = () => {
    if (isLocked) return;
    setCorners([]);
  };

  const handleImageClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (selectionMode !== "click" || isLocked) return;
    if (corners.length >= 4) return; // 4 corners already set

    const imgEl = document.getElementById("braille-preview-img") as HTMLImageElement;
    if (!imgEl || imgSize.width === 0 || imgSize.height === 0) return;

    const rect = imgEl.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Allow clicking slightly outside (margin of 20px) and clamp to image bounds
    const margin = 20;
    if (
      clickX < -margin ||
      clickX > rect.width + margin ||
      clickY < -margin ||
      clickY > rect.height + margin
    ) {
      return;
    }

    const clampedX = Math.max(0, Math.min(rect.width, clickX));
    const clampedY = Math.max(0, Math.min(rect.height, clickY));

    const naturalX = Math.round((clampedX / rect.width) * imgSize.width);
    const naturalY = Math.round((clampedY / rect.height) * imgSize.height);

    setCorners([...corners, { x: naturalX, y: naturalY }]);
  };

  return (
    <div className="w-full h-full min-h-0 flex flex-col bg-gray-900 rounded-2xl overflow-visible border border-gray-800 shadow-2xl relative p-2 sm:p-3">
      {isOptimizing ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mb-4" />
          <span className="text-gray-200 font-medium text-lg">Optimizing image...</span>
          <span className="text-gray-500 text-sm mt-1">Scaling safely under upload limits</span>
        </div>
      ) : !imageUrl ? (
        <label className="flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-800/50 transition-colors rounded-xl border border-dashed border-gray-800 hover:border-gray-700">
          <Upload className="w-12 h-12 text-gray-500 mb-4" />
          <span className="text-gray-300 font-medium">Click to upload Braille Image</span>
          <span className="text-gray-600 text-sm mt-2">JPG, PNG, WebP, TIFF, BMP</span>
          <input
            type="file"
            className="hidden"
            accept="image/jpeg,image/jpg,image/png,image/webp,image/tiff,image/bmp"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              if (!file) return;

              if (!file.type.startsWith("image/")) {
                alert(
                  `❌ Invalid file type: "${file.type || "unknown"}"\n\n` +
                    "Only image files are accepted (JPG, PNG, WebP, TIFF, BMP)."
                );
                return;
              }

              setIsOptimizing(true);
              try {
                const optimized = await optimizeImageForUpload(file);
                setImageFile(optimized);
              } catch {
                setImageFile(file);
              } finally {
                setIsOptimizing(false);
              }
            }}
          />
        </label>
      ) : overlayImage ? (
        <div className="relative w-full flex items-center justify-center bg-black p-4 rounded-xl border border-gray-800 shadow-2xl">
          <div className="relative w-full flex flex-col items-center justify-center">
            <img
              src={overlayImage}
              alt="Overlay Confirmation"
              className="w-full h-auto object-contain pointer-events-none select-none rounded-lg"
            />
            {onClearOverlay && (
              <button
                onClick={onClearOverlay}
                className="self-end mt-4 bg-gray-800/90 hover:bg-gray-700 text-white px-4 py-2 rounded-xl border border-gray-700 shadow-md transition-all text-sm font-medium hover:scale-105 active:scale-95"
              >
                Edit Corners
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col min-h-0 w-full h-full relative">
          {/* ── Selection Mode Control Bar ── */}
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2 px-1 shrink-0 z-20">
            {/* Mode Toggle Buttons */}
            <div className="flex items-center gap-1 bg-gray-800/95 p-1 rounded-xl border border-gray-700 shadow-md">
              <button
                type="button"
                onClick={() => handleModeSwitch("drag")}
                disabled={isLocked}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectionMode === "drag"
                    ? "bg-blue-600 text-white shadow-sm font-semibold"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-700/50"
                }`}
                title="Drag the 4 corner handles to adjust the area"
              >
                <Move className="w-3.5 h-3.5" />
                <span>Drag Corners</span>
              </button>

              <button
                type="button"
                onClick={() => handleModeSwitch("click")}
                disabled={isLocked}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectionMode === "click"
                    ? "bg-blue-600 text-white shadow-sm font-semibold"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-700/50"
                }`}
                title="Click on the image to select the 4 corners sequentially"
              >
                <MousePointerClick className="w-3.5 h-3.5" />
                <span>Click 4 Corners</span>
              </button>
            </div>

            {/* Click Mode Interactive Guidance */}
            {selectionMode === "click" && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-blue-300 bg-blue-950/70 border border-blue-500/30 px-2.5 py-1 rounded-lg font-medium flex items-center gap-1.5 shadow-sm">
                  {corners.length === 0 && "① Click Top-Left ↖"}
                  {corners.length === 1 && "② Click Top-Right ↗"}
                  {corners.length === 2 && "③ Click Bottom-Right ↘"}
                  {corners.length === 3 && "④ Click Bottom-Left ↙"}
                  {corners.length === 4 && (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-300">All 4 corners set (drag to fine-tune)</span>
                    </>
                  )}
                </span>

                {corners.length > 0 && !isLocked && (
                  <button
                    type="button"
                    onClick={handleResetClickCorners}
                    className="flex items-center gap-1 text-xs text-gray-300 hover:text-red-400 bg-gray-800/90 hover:bg-gray-700/90 border border-gray-700 px-2.5 py-1 rounded-lg transition-colors shadow-sm"
                    title="Clear points and re-click"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Reset</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* ── Image Workspace Canvas ── */}
          <div
            ref={containerRef}
            onClick={handleImageClick}
            className={`relative flex-1 w-full h-full min-h-0 flex items-center justify-center overflow-visible bg-black rounded-xl select-none ${
              selectionMode === "click" && corners.length < 4 && !isLocked
                ? "cursor-crosshair"
                : ""
            }`}
          >
            <div className="relative w-full h-full flex items-center justify-center overflow-visible">
              <img
                src={imageUrl}
                alt="Preview"
                className="max-w-full max-h-full object-contain pointer-events-none select-none"
                onLoad={handleImageLoad}
                id="braille-preview-img"
              />

              {/* Connecting lines / Polygon */}
              {corners.length > 0 && imgSize.width > 0 && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  style={{ zIndex: 5 }}
                >
                  {(() => {
                    const imgEl = document.getElementById(
                      "braille-preview-img"
                    ) as HTMLImageElement;
                    if (!imgEl || !containerRef.current) return null;

                    const imgRect = imgEl.getBoundingClientRect();
                    const containerRect =
                      containerRef.current.getBoundingClientRect();

                    const renderW = imgRect.width;
                    const renderH = imgRect.height;
                    const offsetX = imgRect.left - containerRect.left;
                    const offsetY = imgRect.top - containerRect.top;

                    const pointsString = corners
                      .map((c) => {
                        const px = offsetX + (c.x / imgSize.width) * renderW;
                        const py = offsetY + (c.y / imgSize.height) * renderH;
                        return `${px},${py}`;
                      })
                      .join(" ");

                    if (corners.length === 4) {
                      return (
                        <polygon
                          points={pointsString}
                          fill="rgba(59, 130, 246, 0.2)"
                          stroke="#3b82f6"
                          strokeWidth="2"
                        />
                      );
                    }

                    return (
                      <polyline
                        points={pointsString}
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="2"
                        strokeDasharray="6 4"
                      />
                    );
                  })()}
                </svg>
              )}

              {/* Corner Points & Drag Handles */}
              {corners.map((corner, i) => {
                if (!containerRef.current || imgSize.width === 0) return null;
                const imgEl = document.getElementById(
                  "braille-preview-img"
                ) as HTMLImageElement;
                if (!imgEl) return null;

                const imgRect = imgEl.getBoundingClientRect();
                const containerRect =
                  containerRef.current.getBoundingClientRect();

                const renderW = imgRect.width;
                const renderH = imgRect.height;
                const offsetX = imgRect.left - containerRect.left;
                const offsetY = imgRect.top - containerRect.top;

                const x = offsetX + (corner.x / imgSize.width) * renderW;
                const y = offsetY + (corner.y / imgSize.height) * renderH;

                const handleLocalDrag = (info: any) => {
                  const scaleX = imgSize.width / renderW;
                  const scaleY = imgSize.height / renderH;

                  const newCorners = [...corners];
                  newCorners[i] = {
                    x: Math.max(
                      0,
                      Math.min(imgSize.width, newCorners[i].x + info.delta.x * scaleX)
                    ),
                    y: Math.max(
                      0,
                      Math.min(imgSize.height, newCorners[i].y + info.delta.y * scaleY)
                    ),
                  };
                  setCorners(newCorners);
                };

                return (
                  <motion.div
                    key={i}
                    drag={!isLocked}
                    dragMomentum={false}
                    onDrag={(_, info) => handleLocalDrag(info)}
                    onClick={(e) => e.stopPropagation()}
                    initial={false}
                    animate={{ x, y }}
                    transition={{ type: "tween", duration: 0 }}
                    className="absolute top-0 left-0 w-7 h-7 -ml-3.5 -mt-3.5 bg-blue-500 hover:bg-blue-400 rounded-full cursor-grab active:cursor-grabbing border-2 border-white shadow-xl pointer-events-auto flex items-center justify-center text-[11px] font-bold text-white select-none transition-transform hover:scale-110 active:scale-95"
                    style={{ zIndex: 10 }}
                    title={CORNER_NAMES[i] || `Corner ${i + 1}`}
                  >
                    {i + 1}
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
