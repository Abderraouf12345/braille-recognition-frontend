"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Upload } from "lucide-react";

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

export default function ImageWorkspace({ imageFile, setImageFile, corners, setCorners, overlayImage, onClearOverlay, isLocked }: ImageWorkspaceProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (imageFile) {
      const url = URL.createObjectURL(imageFile);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [imageFile]);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setImgSize({ width: naturalWidth, height: naturalHeight });
    
    // Initialize corners to image boundaries
    if (corners.length === 0) {
      setCorners([
        { x: 0, y: 0 },
        { x: naturalWidth, y: 0 },
        { x: naturalWidth, y: naturalHeight },
        { x: 0, y: naturalHeight }
      ]);
    }
  };

  const handleDrag = (index: number, info: any) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const scaleX = imgSize.width / rect.width;
    const scaleY = imgSize.height / rect.height;

    const newCorners = [...corners];
    // Convert local component position back to image natural coordinates
    newCorners[index] = {
      x: Math.max(0, Math.min(imgSize.width, newCorners[index].x + info.delta.x * scaleX)),
      y: Math.max(0, Math.min(imgSize.height, newCorners[index].y + info.delta.y * scaleY))
    };
    setCorners(newCorners);
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 rounded-2xl overflow-visible border border-gray-800 shadow-2xl relative">
      {!imageUrl ? (
        <label className="flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-800/50 transition-colors">
          <Upload className="w-12 h-12 text-gray-500 mb-4" />
          <span className="text-gray-300 font-medium">Click to upload Braille Image</span>
          <span className="text-gray-600 text-sm mt-2">JPG, PNG, TIFF</span>
          <input 
            type="file" 
            className="hidden" 
            accept="image/*"
            onChange={(e) => {
              if (e.target.files?.[0]) setImageFile(e.target.files[0]);
            }}
          />
        </label>
      ) : overlayImage ? (
        <div className="relative flex-1 w-full h-full flex items-center justify-center overflow-hidden bg-black p-4">
          <div className="relative w-full h-full flex items-center justify-center">
            <img 
              src={overlayImage} 
              alt="Overlay Confirmation" 
              className="max-w-full max-h-full object-contain pointer-events-none select-none"
            />
            {onClearOverlay && (
              <button
                onClick={onClearOverlay}
                className="absolute bottom-4 right-4 bg-gray-800/90 hover:bg-gray-700 text-white px-4 py-2 rounded-xl border border-gray-700 shadow-md transition-all text-sm font-medium hover:scale-105 active:scale-95"
              >
                Edit Corners
              </button>
            )}
          </div>
        </div>
      ) : (
        <div 
          ref={containerRef}
          className="relative flex-1 w-full h-full flex items-center justify-center overflow-visible bg-black"
        >
          <div className="relative w-full h-full flex items-center justify-center overflow-visible">
            {/* The image acts as the coordinate space reference */}
            <img 
              src={imageUrl} 
              alt="Preview" 
              className="max-w-full max-h-full object-contain pointer-events-none select-none"
              onLoad={handleImageLoad}
              id="braille-preview-img"
            />
            
            {corners.length === 4 && imgSize.width > 0 && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 5 }}>
                {(() => {
                  const imgEl = document.getElementById('braille-preview-img') as HTMLImageElement;
                  if (!imgEl) return null;
                  
                  // Calculate the actual rendered size and offsets of the object-contain image
                  const imgRect = imgEl.getBoundingClientRect();
                  const containerRect = containerRef.current?.getBoundingClientRect();
                  if (!containerRect) return null;
                  
                  const renderW = imgRect.width;
                  const renderH = imgRect.height;
                  const offsetX = imgRect.left - containerRect.left;
                  const offsetY = imgRect.top - containerRect.top;

                  const pointsString = corners.map(c => {
                    const px = offsetX + (c.x / imgSize.width) * renderW;
                    const py = offsetY + (c.y / imgSize.height) * renderH;
                    return `${px},${py}`;
                  }).join(" ");

                  return (
                    <polygon 
                      points={pointsString}
                      fill="rgba(59, 130, 246, 0.2)"
                      stroke="#3b82f6"
                      strokeWidth="2"
                    />
                  );
                })()}
              </svg>
            )}

            {corners.map((corner, i) => {
              if (!containerRef.current || imgSize.width === 0) return null;
              const imgEl = document.getElementById('braille-preview-img') as HTMLImageElement;
              if (!imgEl) return null;
              
              const imgRect = imgEl.getBoundingClientRect();
              const containerRect = containerRef.current.getBoundingClientRect();
              
              const renderW = imgRect.width;
              const renderH = imgRect.height;
              const offsetX = imgRect.left - containerRect.left;
              const offsetY = imgRect.top - containerRect.top;

              // Calculate current screen coordinates for the Framer motion initial value
              const x = offsetX + (corner.x / imgSize.width) * renderW;
              const y = offsetY + (corner.y / imgSize.height) * renderH;

              const handleLocalDrag = (info: any) => {
                // Determine new natural coordinates based on drag delta
                const scaleX = imgSize.width / renderW;
                const scaleY = imgSize.height / renderH;

                const newCorners = [...corners];
                newCorners[i] = {
                  x: Math.max(0, Math.min(imgSize.width, newCorners[i].x + info.delta.x * scaleX)),
                  y: Math.max(0, Math.min(imgSize.height, newCorners[i].y + info.delta.y * scaleY))
                };
                setCorners(newCorners);
              };

              return (
                <motion.div
                  key={i}
                  drag={!isLocked}
                  dragMomentum={false}
                  onDrag={(_, info) => handleLocalDrag(info)}
                  initial={false}
                  animate={{ x, y }}
                  transition={{ type: "tween", duration: 0 }}
                  className="absolute top-0 left-0 w-6 h-6 -ml-3 -mt-3 bg-blue-500 rounded-full cursor-grab active:cursor-grabbing border-2 border-white shadow-lg pointer-events-auto"
                  style={{ zIndex: 10 }}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
