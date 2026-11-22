"use client";

import { useRef, useState, useEffect } from "react";
import { Sun, Info } from "lucide-react";

interface LightDialProps {
  angle: number;
  setAngle: (angle: number) => void;
}

export default function LightDial({ angle, setAngle }: LightDialProps) {
  const dialRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const calculateAngle = (e: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent) => {
    if (!dialRef.current) return;
    const rect = dialRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    let clientX, clientY;
    if ('touches' in e) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = (e as React.MouseEvent).clientX;
      clientY = (e as React.MouseEvent).clientY;
    }

    const dx = clientX - centerX;
    const dy = clientY - centerY;
    
    // Calculate angle in degrees (0 is top, 90 is right)
    let theta = (Math.atan2(dy, dx) * (180 / Math.PI)) + 90;
    if (theta < 0) theta += 360;
    if (theta >= 360) theta -= 360;
    
    setAngle(Math.round(theta));
  };

  const handlePointerDown = (e: React.MouseEvent | React.TouchEvent) => {
    setIsDragging(true);
    calculateAngle(e);
  };

  useEffect(() => {
    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      if (isDragging) {
        calculateAngle(e);
      }
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener("mousemove", handlePointerMove);
      window.addEventListener("mouseup", handlePointerUp);
      window.addEventListener("touchmove", handlePointerMove);
      window.addEventListener("touchend", handlePointerUp);
    }

    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
      window.removeEventListener("touchmove", handlePointerMove);
      window.removeEventListener("touchend", handlePointerUp);
    };
  }, [isDragging]);

  return (
    <div className="bg-gray-800 p-3 sm:p-4 lg:p-[1.8vh] rounded-2xl flex flex-col items-center justify-center border border-gray-700 shadow-xl shrink-0">
      <div className="w-full flex items-center justify-between mb-2 sm:mb-2.5">
        <h3 className="text-gray-300 font-medium text-xs sm:text-sm">Light Direction</h3>
        <span className="text-[10px] text-blue-400 bg-blue-950/70 border border-blue-500/30 px-2 py-0.5 rounded-full font-medium">
          Single Light Source
        </span>
      </div>
      
      <div 
        ref={dialRef}
        className="relative w-24 h-24 sm:w-28 sm:h-28 lg:w-[13vh] lg:h-[13vh] max-w-[128px] max-h-[128px] min-w-[80px] min-h-[80px] rounded-full border-4 border-gray-700 bg-gray-900 cursor-pointer shadow-inner touch-none"
        onMouseDown={handlePointerDown}
        onTouchStart={handlePointerDown}
      >
        {/* Indicator Line */}
        <div 
          className="absolute top-1/2 left-1/2 w-1/2 h-0.5 bg-blue-500/50 origin-left pointer-events-none"
          style={{ transform: `translateY(-50%) rotate(${angle - 90}deg)` }}
        />
        
        {/* Lamp Icon Wrapper */}
        <div 
          className="absolute top-1/2 left-1/2 w-full h-full pointer-events-none"
          style={{ transform: `translate(-50%, -50%) rotate(${angle - 90}deg)` }}
        >
          <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 bg-blue-500 p-1.5 sm:p-2 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.6)]">
            <Sun className="w-3.5 h-3.5 sm:w-4 sm:h-4 lg:w-4 lg:h-4 text-white" />
          </div>
        </div>
      </div>
      
      <div className="mt-2 text-lg sm:text-xl font-bold text-blue-400 font-mono">
        {angle}°
      </div>

      {/* Clear Guidance Banner */}
      <div className="mt-2 w-full bg-gray-900/80 border border-gray-700/80 rounded-xl p-2 sm:p-2.5 text-center flex items-start gap-1.5 text-left">
        <Info className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
        <p className="text-[11px] leading-tight text-gray-300">
          Light can come from <span className="text-white font-medium">any angle</span>, but must be from <strong className="text-amber-300 font-semibold">one consistent direction</strong> for accurate dot shadow detection.
        </p>
      </div>
    </div>
  );
}
