"use client";

import { useRef, useState, useEffect } from "react";
import { Sun } from "lucide-react";

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
    <div className="bg-gray-800 p-6 rounded-2xl flex flex-col items-center justify-center border border-gray-700 shadow-xl">
      <h3 className="text-gray-300 font-medium mb-6">Light Direction</h3>
      
      <div 
        ref={dialRef}
        className="relative w-32 h-32 rounded-full border-4 border-gray-700 bg-gray-900 cursor-pointer shadow-inner touch-none"
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
          <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 bg-blue-500 p-2 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.6)]">
            <Sun className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>
      
      <div className="mt-6 text-2xl font-bold text-blue-400 font-mono">
        {angle}°
      </div>
    </div>
  );
}
