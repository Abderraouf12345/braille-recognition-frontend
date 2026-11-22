"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  Loader2,
  RotateCcw,
  Maximize2,
  Check,
  MousePointer,
  Undo2,
} from "lucide-react";
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

const CORNER_LABELS = [
  "Top-Left (↖)",
  "Top-Right (↗)",
  "Bottom-Right (↘)",
  "Bottom-Left (↙)",
];

/**
 * Geometric sorting function:
 * Takes any 4 points clicked in arbitrary order, computes centroid,
 * orders them clockwise, and normalizes so index 0 is Top-Left (smallest x+y).
 * Output is guaranteed to be: [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
 */
function sortQuadCorners(pts: Point[]): Point[] {
  if (pts.length !== 4) return pts;

  // 1. Compute centroid
  const center = pts.reduce(
    (acc, p) => ({ x: acc.x + p.x / 4, y: acc.y + p.y / 4 }),
    { x: 0, y: 0 }
  );

  // 2. Sort clockwise by polar angle around centroid
  const clockwise = [...pts].sort((a, b) => {
    const angleA = Math.atan2(a.y - center.y, a.x - center.x);
    const angleB = Math.atan2(b.y - center.y, b.x - center.x);
    return angleA - angleB;
  });

  // 3. Find top-left (point closest to origin / minimal x+y sum)
  let tlIndex = 0;
  let minSum = Infinity;
  for (let i = 0; i < 4; i++) {
    const sum = clockwise[i].x + clockwise[i].y;
    if (sum < minSum) {
      minSum = sum;
      tlIndex = i;
    }
  }

  // 4. Return in order [TL, TR, BR, BL]
  return [
    clockwise[tlIndex],
    clockwise[(tlIndex + 1) % 4],
    clockwise[(tlIndex + 2) % 4],
    clockwise[(tlIndex + 3) % 4],
  ];
}

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
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  // Magnifier Loupe State
  const [loupe, setLoupe] = useState<{
    visible: boolean;
    x: number; // screen pixel X relative to container
    y: number; // screen pixel Y relative to container
    naturalX: number; // exact coordinate on full-res image
    naturalY: number;
    index: number;
  }>({
    visible: false,
    x: 0,
    y: 0,
    naturalX: 0,
    naturalY: 0,
    index: -1,
  });

  const loupeCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setImageUrl(null);
      setImgSize({ width: 0, height: 0 });
      setLoupe((prev) => ({ ...prev, visible: false }));
    }
  }, [imageFile]);

  useEffect(() => {
    const handleResize = () => setImgSize((prev) => ({ ...prev }));
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Update canvas magnification loupe whenever loupe position changes
  useEffect(() => {
    if (!loupe.visible || !loupeCanvasRef.current) return;
    const imgEl = document.getElementById(
      "braille-preview-img"
    ) as HTMLImageElement;
    if (!imgEl) return;

    const canvas = loupeCanvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const LOUPE_DIAMETER = 120;
    const ZOOM = 2.5;
    const sampleSize = LOUPE_DIAMETER / ZOOM;

    ctx.clearRect(0, 0, LOUPE_DIAMETER, LOUPE_DIAMETER);

    // Draw circular mask
    ctx.save();
    ctx.beginPath();
    ctx.arc(
      LOUPE_DIAMETER / 2,
      LOUPE_DIAMETER / 2,
      LOUPE_DIAMETER / 2,
      0,
      Math.PI * 2
    );
    ctx.clip();

    // Draw zoomed portion from source image
    ctx.drawImage(
      imgEl,
      loupe.naturalX - sampleSize / 2,
      loupe.naturalY - sampleSize / 2,
      sampleSize,
      sampleSize,
      0,
      0,
      LOUPE_DIAMETER,
      LOUPE_DIAMETER
    );

    // Crosshairs inside the loupe
    ctx.strokeStyle = "rgba(59, 130, 246, 0.9)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    // Horizontal crosshair
    ctx.moveTo(LOUPE_DIAMETER / 2 - 14, LOUPE_DIAMETER / 2);
    ctx.lineTo(LOUPE_DIAMETER / 2 + 14, LOUPE_DIAMETER / 2);
    // Vertical crosshair
    ctx.moveTo(LOUPE_DIAMETER / 2, LOUPE_DIAMETER / 2 - 14);
    ctx.lineTo(LOUPE_DIAMETER / 2, LOUPE_DIAMETER / 2 + 14);
    ctx.stroke();

    ctx.restore();
  }, [loupe]);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setImgSize({ width: naturalWidth, height: naturalHeight });
    // In Stage 1, we start with empty corners so user taps the 4 corners cleanly.
  };

  // Reset to full default margins or clear to tap fresh
  const handleResetToFit = () => {
    if (isLocked || imgSize.width === 0) return;
    const marginX = Math.round(imgSize.width * 0.04);
    const marginY = Math.round(imgSize.height * 0.04);
    setCorners([
      { x: marginX, y: marginY },
      { x: imgSize.width - marginX, y: marginY },
      { x: imgSize.width - marginX, y: imgSize.height - marginY },
      { x: marginX, y: imgSize.height - marginY },
    ]);
  };

  const handleClearToRetap = () => {
    if (isLocked) return;
    setCorners([]);
  };

  const handleUndoLastPoint = () => {
    if (isLocked || corners.length === 0) return;
    setCorners(corners.slice(0, -1));
  };

  // Stage 1 click handler: tap the 4 corners in any order
  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isLocked) return;
    // When 4 corners are already selected, we are in Stage 2 (Fine-tuning / Drag handles active)
    if (corners.length >= 4) return;

    const imgEl = document.getElementById(
      "braille-preview-img"
    ) as HTMLImageElement;
    if (!imgEl || imgSize.width === 0 || imgSize.height === 0) return;

    const rect = imgEl.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Allow clicking slightly outside (margin of 25px) and clamp to bounds
    const margin = 25;
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

    const newPoints = [...corners, { x: naturalX, y: naturalY }];

    // As soon as the 4th corner is tapped, auto-sort geometrically into [TL, TR, BR, BL]!
    if (newPoints.length === 4) {
      const sorted = sortQuadCorners(newPoints);
      setCorners(sorted);
    } else {
      setCorners(newPoints);
    }
  };

  return (
    <div className="w-full h-full min-h-0 flex flex-col bg-gray-900 rounded-2xl overflow-visible border border-gray-800 shadow-2xl relative p-2 sm:p-3">
      {isOptimizing ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mb-4" />
          <span className="text-gray-200 font-medium text-lg">
            Optimizing image...
          </span>
          <span className="text-gray-500 text-sm mt-1">
            Scaling safely under upload limits
          </span>
        </div>
      ) : !imageUrl ? (
        <label className="flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-800/50 transition-colors rounded-xl border border-dashed border-gray-800 hover:border-gray-700">
          <Upload className="w-12 h-12 text-gray-500 mb-4" />
          <span className="text-gray-300 font-medium">
            Click to upload Braille Image
          </span>
          <span className="text-gray-600 text-sm mt-2">
            JPG, PNG, WebP, TIFF, BMP
          </span>
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
          {/* ── Unified Smart Toolbar ── */}
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2 px-1 shrink-0 z-20">
            {/* Context Status & Helper */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-blue-200 bg-blue-950/70 border border-blue-500/30 px-3 py-1.5 rounded-xl font-medium flex items-center gap-2 shadow-sm">
                {corners.length === 0 && (
                  <>
                    <MousePointer className="w-3.5 h-3.5 text-blue-400" />
                    <span>Stage 1: Tap the 4 corners in any order (0 of 4)</span>
                  </>
                )}
                {corners.length > 0 && corners.length < 4 && (
                  <>
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                    <span>
                      Corner {corners.length + 1} of 4: Tap next corner
                    </span>
                  </>
                )}
                {corners.length === 4 && (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-300">
                      Stage 2: Drag handles to fine-tune
                    </span>
                  </>
                )}
              </span>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-1.5">
              {corners.length > 0 && corners.length < 4 && (
                <button
                  type="button"
                  onClick={handleUndoLastPoint}
                  disabled={isLocked}
                  className="flex items-center gap-1 text-xs text-amber-300 hover:text-amber-200 bg-amber-950/60 hover:bg-amber-900/70 border border-amber-600/40 px-2.5 py-1.5 rounded-xl transition-all shadow-sm"
                  title="Undo previous corner tap"
                >
                  <Undo2 className="w-3 h-3 text-amber-400" />
                  <span>Undo</span>
                </button>
              )}

              {corners.length < 4 && (
                <button
                  type="button"
                  onClick={handleResetToFit}
                  disabled={isLocked}
                  className="flex items-center gap-1 text-xs text-gray-300 hover:text-white bg-gray-800/90 hover:bg-gray-700/90 border border-gray-700/80 px-2.5 py-1.5 rounded-xl transition-all shadow-sm"
                  title="Auto-fit corners to default page margins"
                >
                  <Maximize2 className="w-3 h-3 text-gray-400" />
                  <span className="hidden sm:inline">Auto Borders</span>
                </button>
              )}

              {corners.length === 4 && (
                <button
                  type="button"
                  onClick={handleClearToRetap}
                  disabled={isLocked}
                  className="flex items-center gap-1 text-xs text-gray-300 hover:text-red-400 bg-gray-800/90 hover:bg-gray-700/90 border border-gray-700/80 px-2.5 py-1.5 rounded-xl transition-all shadow-sm"
                  title="Clear all points and re-tap 4 corners from scratch"
                >
                  <RotateCcw className="w-3 h-3 text-gray-400" />
                  <span>Re-tap Corners</span>
                </button>
              )}
            </div>
          </div>

          {/* ── Image Workspace Canvas ── */}
          <div
            ref={containerRef}
            onClick={handleCanvasClick}
            className={`relative flex-1 w-full h-full min-h-0 flex items-center justify-center overflow-visible bg-black rounded-xl select-none ${
              corners.length < 4 && !isLocked ? "cursor-crosshair" : ""
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
                          fill="rgba(59, 130, 246, 0.22)"
                          stroke="#3b82f6"
                          strokeWidth="2.5"
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

                  const newX = Math.max(
                    0,
                    Math.min(imgSize.width, corner.x + info.delta.x * scaleX)
                  );
                  const newY = Math.max(
                    0,
                    Math.min(imgSize.height, corner.y + info.delta.y * scaleY)
                  );

                  const updatedCorners = [...corners];
                  updatedCorners[i] = { x: newX, y: newY };

                  // If all 4 are present, keep them sorted correctly
                  if (updatedCorners.length === 4) {
                    setCorners(sortQuadCorners(updatedCorners));
                  } else {
                    setCorners(updatedCorners);
                  }

                  // Update Loupe position during drag
                  const currentScreenX =
                    offsetX + (newX / imgSize.width) * renderW;
                  const currentScreenY =
                    offsetY + (newY / imgSize.height) * renderH;

                  setLoupe({
                    visible: true,
                    x: currentScreenX,
                    y: currentScreenY,
                    naturalX: newX,
                    naturalY: newY,
                    index: i,
                  });
                };

                // In Stage 1 (less than 4 points), points are just stationary tap markers
                // In Stage 2 (all 4 points placed), handles become draggable and interactive
                const isStage2 = corners.length === 4;

                return (
                  <motion.div
                    key={i}
                    drag={isStage2 && !isLocked}
                    dragMomentum={false}
                    onDrag={isStage2 ? (_, info) => handleLocalDrag(info) : undefined}
                    onDragStart={
                      isStage2
                        ? () => {
                            setLoupe({
                              visible: true,
                              x,
                              y,
                              naturalX: corner.x,
                              naturalY: corner.y,
                              index: i,
                            });
                          }
                        : undefined
                    }
                    onDragEnd={
                      isStage2
                        ? () => {
                            setLoupe((prev) => ({ ...prev, visible: false }));
                          }
                        : undefined
                    }
                    onClick={(e) => e.stopPropagation()}
                    initial={false}
                    animate={{ x, y }}
                    transition={{ type: "tween", duration: 0 }}
                    className={`absolute top-0 left-0 w-7 h-7 -ml-3.5 -mt-3.5 rounded-full border-2 border-white pointer-events-auto flex items-center justify-center text-[11px] font-bold text-white select-none transition-transform ${
                      isStage2
                        ? "bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 cursor-grab active:cursor-grabbing shadow-[0_0_15px_rgba(59,130,246,0.6)] hover:scale-125 active:scale-95"
                        : "bg-blue-600 shadow-[0_0_10px_rgba(59,130,246,0.8)] animate-in zoom-in-75 duration-150"
                    }`}
                    style={{ zIndex: 10 }}
                    title={
                      isStage2
                        ? `${CORNER_LABELS[i] || `Corner ${i + 1}`} (Drag to adjust)`
                        : `Corner ${i + 1} of 4`
                    }
                  >
                    {i + 1}
                  </motion.div>
                );
              })}

              {/* ── High-Precision Zoom Magnifier Loupe ── */}
              {loupe.visible && (
                <div
                  className="absolute pointer-events-none rounded-full shadow-[0_0_25px_rgba(0,0,0,0.8),0_0_15px_rgba(59,130,246,0.6)] border-2 border-blue-400 bg-gray-950 overflow-hidden flex items-center justify-center animate-in fade-in zoom-in duration-100"
                  style={{
                    zIndex: 40,
                    width: "120px",
                    height: "120px",
                    left: `${loupe.x}px`,
                    top: `${loupe.y - 85}px`,
                    transform: "translate(-50%, -50%)",
                  }}
                >
                  <canvas
                    ref={loupeCanvasRef}
                    width={120}
                    height={120}
                    className="w-full h-full"
                  />
                  {/* Badge displaying coordinate info */}
                  <span className="absolute bottom-1 bg-black/75 text-blue-300 text-[9px] px-1.5 py-0.5 rounded-full font-mono border border-blue-500/30">
                    2.5× Zoom
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
