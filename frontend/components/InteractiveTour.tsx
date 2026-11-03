"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { 
  X, 
  ChevronRight, 
  ChevronLeft, 
  Check, 
  Sparkles, 
  RotateCcw, 
  HelpCircle,
  Eye,
  Sliders,
  Languages,
  FileCheck
} from "lucide-react";

export interface TourStep {
  targetId?: string;
  title: string;
  badge: string;
  description: string;
  tip?: string;
  accentColor: string;
  glowColor: string;
  position?: "bottom" | "top" | "left" | "right" | "center";
}

const TOUR_STEPS: TourStep[] = [
  {
    targetId: "tour-workspace",
    title: "1. Upload Your Braille Image",
    badge: "Step 1 of 5",
    accentColor: "from-blue-500 to-indigo-500",
    glowColor: "rgba(59, 130, 246, 0.5)",
    position: "right",
    description:
      "This is your main document workspace. In normal use, you simply drag-and-drop or click here to upload any clear photo of a Braille page (JPG, PNG, WebP).",
    tip: "💡 We have automatically loaded a sample Braille exam paper so you can follow along live!",
  },
  {
    targetId: "tour-workspace",
    title: "2. Adjust Corner Markers",
    badge: "Step 2 of 5",
    accentColor: "from-violet-500 to-purple-500",
    glowColor: "rgba(168, 85, 247, 0.5)",
    position: "right",
    description:
      "Notice the 4 blue circular handles and the translucent shaded boundary. You can drag each circle to precisely align with the physical corners of the paper.",
    tip: "💡 Correcting the corners removes perspective tilt and camera angles for maximum AI accuracy.",
  },
  {
    targetId: "tour-light-dial",
    title: "3. Set the Light Angle",
    badge: "Step 3 of 5",
    accentColor: "from-amber-500 to-orange-500",
    glowColor: "rgba(245, 158, 11, 0.5)",
    position: "left",
    description:
      "Braille dots create tiny highlights and shadows. Rotate this dial so the sun matches the lighting direction of your photograph.",
    tip: "💡 Heuristic tip: If dots appear inverted (back-page verso), rotating by 180° flips the classification to the front page (recto).",
  },
  {
    targetId: "tour-controls",
    title: "4. Choose Language & Translate",
    badge: "Step 4 of 5",
    accentColor: "from-emerald-500 to-teal-500",
    glowColor: "rgba(16, 185, 129, 0.5)",
    position: "left",
    description:
      "Choose your translation language (Arabic, English G1/G2, French, Russian, Chinese, or Raw Braille). Then click 'Extract & Translate' to start recognition.",
    tip: "💡 The AI streams the results character-by-character in real time so you don't have to wait.",
  },
  {
    targetId: "tour-results",
    title: "5. Speech, Copy & Export",
    badge: "Step 5 of 5",
    accentColor: "from-rose-500 to-pink-500",
    glowColor: "rgba(244, 63, 94, 0.5)",
    position: "left",
    description:
      "Your translation is ready here! Switch tabs to see raw Braille Unicode, tap 'Play Audio' to hear natural text-to-speech, or use Copy and Download to save.",
    tip: "💡 Multiple regional accents and natural voices are available for each language.",
  },
  {
    title: "✨ You're Ready to Begin!",
    badge: "Completed",
    accentColor: "from-emerald-400 to-blue-500",
    glowColor: "rgba(16, 185, 129, 0.5)",
    position: "center",
    description:
      "You've learned the complete workflow. When you finish this tour, we'll clear the demo document so you can start with your own Braille photos.",
    tip: "💡 Click 'How to use?' in the header whenever you want to revisit this walkthrough.",
  },
];

interface InteractiveTourProps {
  isOpen: boolean;
  onClose: () => void;
  onStartDemo: () => void;
  onEndDemo: () => void;
  onOpenVisualGuide?: () => void;
}

export default function InteractiveTour({
  isOpen,
  onClose,
  onStartDemo,
  onEndDemo,
  onOpenVisualGuide,
}: InteractiveTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [windowDimensions, setWindowDimensions] = useState({ width: 0, height: 0 });

  // Start demo data when tour opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      onStartDemo();
    }
  }, [isOpen, onStartDemo]);

  // Track window size
  useEffect(() => {
    const updateDimensions = () => {
      setWindowDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Update spotlight rect when step or layout changes
  const updateRect = useCallback(() => {
    if (!isOpen) return;
    const step = TOUR_STEPS[currentStep];
    if (!step.targetId) {
      setTargetRect(null);
      return;
    }

    const el = document.getElementById(step.targetId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
      setTimeout(() => {
        const rect = el.getBoundingClientRect();
        setTargetRect(rect);
      }, 120);
    } else {
      setTargetRect(null);
    }
  }, [isOpen, currentStep]);

  useEffect(() => {
    updateRect();
    window.addEventListener("resize", updateRect);
    window.addEventListener("scroll", updateRect, true);
    return () => {
      window.removeEventListener("resize", updateRect);
      window.removeEventListener("scroll", updateRect, true);
    };
  }, [updateRect]);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleFinish = () => {
    onEndDemo();
    onClose();
  };

  if (!isOpen) return null;

  const step = TOUR_STEPS[currentStep];
  const isFinalStep = currentStep === TOUR_STEPS.length - 1;
  const isCenter = step.position === "center" || !targetRect;

  // Compute Popover Position relative to target rect
  const getPopoverStyle = () => {
    if (isCenter || !targetRect) {
      return {
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      };
    }

    const margin = 18;
    const popoverWidth = Math.min(380, windowDimensions.width - 32);

    // Desktop: Left or Right positioning
    if (windowDimensions.width >= 1024) {
      if (step.position === "left") {
        // Position to the left of the target element
        const left = Math.max(16, targetRect.left - popoverWidth - margin);
        const top = Math.min(
          windowDimensions.height - 350,
          Math.max(16, targetRect.top + targetRect.height / 2 - 140)
        );
        return { top: `${top}px`, left: `${left}px`, width: `${popoverWidth}px` };
      } else if (step.position === "right") {
        // Position to the right of the target element
        const left = Math.min(
          windowDimensions.width - popoverWidth - 16,
          targetRect.right + margin
        );
        const top = Math.min(
          windowDimensions.height - 350,
          Math.max(16, targetRect.top + 30)
        );
        return { top: `${top}px`, left: `${left}px`, width: `${popoverWidth}px` };
      }
    }

    // Default mobile or bottom fallback
    const top = Math.min(
      windowDimensions.height - 320,
      targetRect.bottom + margin
    );
    const left = Math.max(
      16,
      Math.min(
        windowDimensions.width - popoverWidth - 16,
        targetRect.left + (targetRect.width - popoverWidth) / 2
      )
    );

    return {
      top: `${top}px`,
      left: `${left}px`,
      width: `${popoverWidth}px`,
    };
  };

  return (
    <div className="fixed inset-0 z-[80] overflow-hidden select-none">
      {/* ── Background Dark Overlay with Cutout Spotlight ── */}
      {targetRect && !isCenter ? (
        <div
          className="fixed pointer-events-none transition-all duration-300 ease-out"
          style={{
            top: targetRect.top - 8,
            left: targetRect.left - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
            borderRadius: "1.25rem",
            boxShadow: `0 0 0 9999px rgba(3, 7, 18, 0.82), 0 0 35px ${step.glowColor}`,
            border: "2px solid rgba(59, 130, 246, 0.9)",
          }}
        />
      ) : (
        <div className="fixed inset-0 bg-gray-950/85 backdrop-blur-sm transition-opacity duration-300 pointer-events-none" />
      )}

      {/* ── Click blocker (prevents interaction with page during tour) ── */}
      <div 
        className="fixed inset-0 cursor-default"
        onClick={(e) => e.stopPropagation()} 
      />

      {/* ── Floating Popover Tooltip Card ── */}
      <div
        className="fixed z-[90] bg-gray-900 border border-gray-700/90 rounded-2xl shadow-2xl p-5 text-gray-100 flex flex-col gap-3.5 transition-all duration-300 animate-in fade-in zoom-in-95"
        style={{
          ...getPopoverStyle(),
          boxShadow: `0 20px 45px -10px rgba(0, 0, 0, 0.8), 0 0 25px ${step.glowColor}`,
        }}
      >
        {/* Top colored accent indicator line */}
        <div className={`h-1.5 w-full -mt-5 -mx-5 px-5 rounded-t-2xl bg-gradient-to-r ${step.accentColor} shrink-0`} />

        {/* Popover Header */}
        <div className="flex items-center justify-between gap-2 pt-1">
          <span className="text-[11px] font-bold tracking-wider uppercase text-blue-400 bg-blue-950/60 border border-blue-500/30 px-2.5 py-1 rounded-full">
            {step.badge}
          </span>
          <button
            onClick={handleFinish}
            className="text-gray-400 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-1 rounded-lg"
            title="Exit tour"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Popover Title & Description */}
        <div>
          <h3 className="text-base font-bold text-white leading-snug">{step.title}</h3>
          <p className="text-xs sm:text-sm text-gray-300 mt-2 leading-relaxed">{step.description}</p>
        </div>

        {/* Contextual Tip */}
        {step.tip && (
          <div className="bg-gray-800/80 border border-gray-700/60 rounded-xl p-2.5 text-xs text-gray-300">
            {step.tip}
          </div>
        )}

        {/* Progress Dots */}
        <div className="flex items-center justify-between pt-1 border-t border-gray-800">
          <div className="flex items-center gap-1.5">
            {TOUR_STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === currentStep
                    ? "w-5 bg-blue-500"
                    : i < currentStep
                    ? "w-2 bg-emerald-500/70"
                    : "w-1.5 bg-gray-700"
                }`}
              />
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {currentStep > 0 && !isFinalStep && (
              <button
                onClick={handlePrev}
                className="text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Back
              </button>
            )}

            {!isFinalStep ? (
              <button
                onClick={handleNext}
                className="flex items-center gap-1.5 text-xs font-semibold text-white px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 transition-all shadow-md shadow-blue-900/40"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleFinish}
                className="flex items-center gap-1.5 text-xs font-semibold text-white px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 transition-all shadow-md shadow-emerald-900/40"
              >
                <Check className="w-4 h-4" />
                Start Using App
              </button>
            )}
          </div>
        </div>

        {/* Switch to static visual guide link */}
        {onOpenVisualGuide && !isFinalStep && (
          <div className="text-center pt-0.5">
            <button
              onClick={() => {
                handleFinish();
                onOpenVisualGuide();
              }}
              className="text-[11px] text-gray-500 hover:text-gray-300 underline transition-colors"
            >
              Prefer screenshots & video? Open visual guide
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

