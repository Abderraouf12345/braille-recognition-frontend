"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  Loader2,
  Maximize2,
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
  setCorners: React.Dispatch<React.SetStateAction<Point[]>>;
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

  // Active dragging index to prevent re-sorting mid-drag
  const [activeDragIndex, setActiveDragIndex] = useState<number | null>(null);

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
    // Initially position the four corners at the extreme edges of the image
    if (corners.length !== 4) {
      setCorners([
        { x: 0, y: 0 },
        { x: naturalWidth, y: 0 },
        { x: naturalWidth, y: naturalHeight },
        { x: 0, y: naturalHeight },
      ]);
    }
  };

  // Reset to extreme image edges
  const handleResetToFit = () => {
    if (isLocked || imgSize.width === 0) return;
    setCorners([
      { x: 0, y: 0 },
      { x: imgSize.width, y: 0 },
      { x: imgSize.width, y: imgSize.height },
      { x: 0, y: imgSize.height },
    ]);
  };

  // Move point and update loupe
  const updateCornerPosition = useCallback(
    (index: number, naturalX: number, naturalY: number) => {
      if (imgSize.width === 0 || imgSize.height === 0) return;
      const imgEl = document.getElementById("braille-preview-img") as HTMLImageElement;
      if (!imgEl || !containerRef.current) return;

      const imgRect = imgEl.getBoundingClientRect();
      const containerRect = containerRef.current.getBoundingClientRect();
      const renderW = imgRect.width;
      const renderH = imgRect.height;
      const offsetX = imgRect.left - containerRect.left;
      const offsetY = imgRect.top - containerRect.top;

      const currentScreenX = offsetX + (naturalX / imgSize.width) * renderW;
      const currentScreenY = offsetY + (naturalY / imgSize.height) * renderH;

      setCorners((prev) => {
        const next = [...prev];
        next[index] = { x: naturalX, y: naturalY };
        return next;
      });

      setLoupe({
        visible: true,
        x: currentScreenX,
        y: currentScreenY,
        naturalX,
        naturalY,
        index,
      });
    },
    [imgSize, setCorners]
  );

  // Global mousemove/touchmove and mouseup/touchend for quadrant click-and-drag
  useEffect(() => {
    if (activeDragIndex === null) return;

    const getNaturalCoords = (clientX: number, clientY: number) => {
      const imgEl = document.getElementById("braille-preview-img") as HTMLImageElement;
      if (!imgEl || imgSize.width === 0 || imgSize.height === 0) return null;

      const rect = imgEl.getBoundingClientRect();
      const clickX = clientX - rect.left;
      const clickY = clientY - rect.top;

      const clampedX = Math.max(0, Math.min(rect.width, clickX));
      const clampedY = Math.max(0, Math.min(rect.height, clickY));

      const naturalX = Math.round((clampedX / rect.width) * imgSize.width);
      const naturalY = Math.round((clampedY / rect.height) * imgSize.height);
      return { naturalX, naturalY };
    };

    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
      const coords = getNaturalCoords(clientX, clientY);
      if (coords) {
        updateCornerPosition(activeDragIndex, coords.naturalX, coords.naturalY);
      }
    };

    const handlePointerUp = () => {
      setActiveDragIndex(null);
      setLoupe((prev) => ({ ...prev, visible: false }));
      setCorners((prev) => sortQuadCorners(prev));
    };

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);
    window.addEventListener("touchmove", handlePointerMove);
    window.addEventListener("touchend", handlePointerUp);

    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
      window.removeEventListener("touchmove", handlePointerMove);
      window.removeEventListener("touchend", handlePointerUp);
    };
  }, [activeDragIndex, imgSize, setCorners, updateCornerPosition]);

  // Quadrant Section Click Handler:
  // Divides image into 4 sections (TL: 0, TR: 1, BR: 2, BL: 3).
  // When pressing down anywhere in a quadrant, that quadrant's corner jumps to cursor
  // and immediately attaches for continuous drag until release.
  const handleCanvasPointerDown = (e: React.MouseEvent<HTMLDivElement> | React.TouchEvent<HTMLDivElement>) => {
    if (isLocked) return;

    const imgEl = document.getElementById("braille-preview-img") as HTMLImageElement;
    if (!imgEl || imgSize.width === 0 || imgSize.height === 0) return;

    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    const rect = imgEl.getBoundingClientRect();
    const clickX = clientX - rect.left;
    const clickY = clientY - rect.top;

    // Check bounds with small margin tolerance
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

    // Determine quadrant based on center of image:
    // Section 0 (Top-Left): x < midX && y < midY
    // Section 1 (Top-Right): x >= midX && y < midY
    // Section 2 (Bottom-Right): x >= midX && y >= midY
    // Section 3 (Bottom-Left): x < midX && y >= midY
    const midX = imgSize.width / 2;
    const midY = imgSize.height / 2;

    let targetIndex = 0;
    if (naturalX < midX && naturalY < midY) {
      targetIndex = 0; // Top-Left
    } else if (naturalX >= midX && naturalY < midY) {
      targetIndex = 1; // Top-Right
    } else if (naturalX >= midX && naturalY >= midY) {
      targetIndex = 2; // Bottom-Right
    } else {
      targetIndex = 3; // Bottom-Left
    }

    // Instantly jump the corresponding corner to cursor and attach it for active drag
    setActiveDragIndex(targetIndex);
    updateCornerPosition(targetIndex, naturalX, naturalY);
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
          {/* ── Toolbar Actions ── */}
          <div className="flex items-center justify-end gap-2 mb-2 px-1 shrink-0 z-20">
            <button
              type="button"
              onClick={handleResetToFit}
              disabled={isLocked}
              className="flex items-center gap-1.5 text-xs text-gray-300 hover:text-white bg-gray-800/90 hover:bg-gray-700/90 border border-gray-700/80 px-2.5 py-1.5 rounded-xl transition-all shadow-sm"
              title="Reset corners to extreme outer boundaries"
            >
              <Maximize2 className="w-3.5 h-3.5 text-gray-400" />
              <span>Reset to Edges</span>
            </button>
          </div>

          {/* ── Image Workspace Canvas ── */}
          <div
            ref={containerRef}
            onMouseDown={handleCanvasPointerDown}
            onTouchStart={handleCanvasPointerDown}
            className="relative flex-1 w-full h-full min-h-0 flex items-center justify-center overflow-visible bg-black rounded-xl select-none cursor-crosshair touch-none"
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

                  // Crucial for smoothness: DO NOT sort while actively dragging!
                  // Sorting mid-drag changes array indices on the fly, which flips handles under the cursor
                  // and causes jarring stutter/glitches. Sorting is smoothly applied onDragEnd.
                  setCorners(updatedCorners);

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

                return (
                  <motion.div
                    key={i}
                    drag={!isLocked}
                    dragMomentum={false}
                    dragElastic={0}
                    onDrag={(_, info) => handleLocalDrag(info)}
                    onDragStart={() => {
                      setActiveDragIndex(i);
                      setLoupe({
                        visible: true,
                        x,
                        y,
                        naturalX: corner.x,
                        naturalY: corner.y,
                        index: i,
                      });
                    }}
                    onDragEnd={() => {
                      setActiveDragIndex(null);
                      setLoupe((prev) => ({ ...prev, visible: false }));
                      // Sort once user finishes dragging, ensuring stable final order
                      setCorners((prev) => sortQuadCorners(prev));
                    }}
                    onClick={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                    onTouchStart={(e) => e.stopPropagation()}
                    initial={false}
                    animate={{ x, y }}
                    transition={{ duration: 0 }}
                    className="absolute top-0 left-0 w-7 h-7 -ml-3.5 -mt-3.5 rounded-full border-2 border-white pointer-events-auto flex items-center justify-center text-[11px] font-bold text-white select-none bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 cursor-grab active:cursor-grabbing shadow-[0_0_15px_rgba(59,130,246,0.6)]"
                    style={{ zIndex: activeDragIndex === i ? 25 : 10 }}
                    title={`${CORNER_LABELS[i] || `Corner ${i + 1}`} (Drag to adjust)`}
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
