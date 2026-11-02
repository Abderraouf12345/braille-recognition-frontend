"use client";

import { useState, useEffect, useCallback } from "react";
import { X, ChevronRight, ChevronLeft, Sparkles } from "lucide-react";

const STORAGE_KEY = "braille_onboarding_done";

interface Step {
  icon: string;
  color: string;
  border: string;
  accent: string;
  dot: string;
  title: string;
  description: string;
  tip: string;
}

const STEPS: Step[] = [
  {
    icon: "📷",
    color: "from-blue-600/20 to-blue-900/20",
    border: "border-blue-500/30",
    accent: "text-blue-400",
    dot: "bg-blue-500",
    title: "Upload a Braille photo",
    description:
      "Tap or drag any clear photo of a Braille document onto the upload area. Supported formats: JPG, PNG, WebP, TIFF, BMP.",
    tip: "Tip: A well-lit, sharp photo gives the best results.",
  },
  {
    icon: "📐",
    color: "from-violet-600/20 to-violet-900/20",
    border: "border-violet-500/30",
    accent: "text-violet-400",
    dot: "bg-violet-500",
    title: "Align the four corner markers",
    description:
      "Four blue handles will appear on your image. Drag each handle to match the exact corners of the Braille page. This corrects perspective distortion for accurate recognition.",
    tip: "Tip: Zoom in for precise alignment on tricky angles.",
  },
  {
    icon: "💡",
    color: "from-amber-600/20 to-amber-900/20",
    border: "border-amber-500/30",
    accent: "text-amber-400",
    dot: "bg-amber-500",
    title: "Set the light angle",
    description:
      "Rotate the dial to match the lighting direction in your photo. This helps distinguish raised dots (recto) from back-side indentations (verso). If the result looks wrong, try rotating by 180°.",
    tip: "Tip: Most photos have light coming from the top — start at 0°.",
  },
  {
    icon: "🌐",
    color: "from-emerald-600/20 to-emerald-900/20",
    border: "border-emerald-500/30",
    accent: "text-emerald-400",
    dot: "bg-emerald-500",
    title: "Choose a language & translate",
    description:
      "Select your target language from the dropdown — Arabic, French, English, Russian, Chinese, and more. Then click \"Extract & Translate\" to start the AI recognition.",
    tip: "Tip: Results appear in real time, character by character.",
  },
  {
    icon: "🔊",
    color: "from-rose-600/20 to-rose-900/20",
    border: "border-rose-500/30",
    accent: "text-rose-400",
    dot: "bg-rose-500",
    title: "Listen, copy or download",
    description:
      "Once the translation is ready, you can play it as audio using text-to-speech, copy the text to your clipboard, or download it as a .txt file to share.",
    tip: "Tip: Use \"New Image\" in the header to start a fresh scan.",
  },
];

const STEP_VISUALS = [
  /* Step 0 — Upload */
  <div key="s0" className="relative flex items-center justify-center w-full h-full">
    <div className="w-28 h-20 rounded-xl border-2 border-dashed border-blue-400/60 flex flex-col items-center justify-center gap-2 bg-blue-950/30">
      <span className="text-3xl">📄</span>
      <div className="flex gap-1">
        {["⠓", "⠑", "⠇", "⠇", "⠕"].map((c, i) => (
          <span key={i} className="text-blue-300 text-sm font-mono">{c}</span>
        ))}
      </div>
    </div>
    <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-blue-500/20 border border-blue-400/40 flex items-center justify-center text-base">
      ⬆️
    </div>
  </div>,

  /* Step 1 — Corner alignment */
  <div key="s1" className="relative flex items-center justify-center w-full h-full">
    <div className="w-28 h-20 relative">
      <div className="absolute inset-0 border-2 border-violet-400/40 rounded-md bg-violet-950/20" />
      {["-top-2 -left-2", "-top-2 -right-2", "-bottom-2 -left-2", "-bottom-2 -right-2"].map((pos, i) => (
        <div key={i} className={`absolute ${pos} w-4 h-4 rounded-full bg-violet-500 border-2 border-white shadow-lg`} />
      ))}
      <div className="absolute inset-0 flex items-center justify-center text-violet-300 text-2xl">⠿</div>
    </div>
  </div>,

  /* Step 2 — Light dial */
  <div key="s2" className="relative flex items-center justify-center w-full h-full">
    <div className="w-20 h-20 rounded-full border-2 border-amber-400/40 bg-amber-950/20 flex items-center justify-center relative">
      <div
        className="absolute bg-amber-400 rounded-full"
        style={{ width: "3px", height: "38%", bottom: "50%", left: "calc(50% - 1.5px)", transformOrigin: "bottom center", transform: "rotate(-35deg)" }}
      />
      <div className="w-3 h-3 rounded-full bg-amber-400 z-10" />
      <span className="absolute top-1 text-base">☀️</span>
    </div>
  </div>,

  /* Step 3 — Language */
  <div key="s3" className="relative flex items-center justify-center w-full h-full">
    <div className="flex flex-col gap-3 items-center">
      <div className="flex gap-2 text-xl">
        {["🇩🇿", "🇫🇷", "🇬🇧", "🇷🇺", "🇨🇳"].map((f, i) => <span key={i}>{f}</span>)}
      </div>
      <div className="bg-emerald-600/80 rounded-xl px-5 py-1.5 text-white text-xs font-semibold shadow-lg shadow-emerald-900/40">
        Extract &amp; Translate
      </div>
    </div>
  </div>,

  /* Step 4 — Output actions */
  <div key="s4" className="relative flex items-center justify-center w-full h-full">
    <div className="flex flex-col items-center gap-3">
      <div className="flex gap-4 text-2xl">
        <span>🔊</span><span>📋</span><span>💾</span>
      </div>
      <div className="text-xs text-rose-300 font-mono bg-rose-950/40 border border-rose-500/20 px-3 py-1.5 rounded-lg tracking-wider">
        ⠓⠑⠇⠇⠕ → مرحبا
      </div>
    </div>
  </div>,
];

interface OnboardingModalProps {
  /** If true, force-show the modal (e.g. triggered by a "How to use?" button) */
  forceShow?: boolean;
  onClose: () => void;
}

export default function OnboardingModal({ forceShow = false, onClose }: OnboardingModalProps) {
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(false);
  const [animating, setAnimating] = useState(false);
  const [slideDir, setSlideDir] = useState<"left" | "right">("right");

  useEffect(() => {
    if (forceShow) {
      setVisible(true);
      setStep(0);
      return;
    }
    const done = localStorage.getItem(STORAGE_KEY);
    if (!done) {
      const t = setTimeout(() => setVisible(true), 700);
      return () => clearTimeout(t);
    }
  }, [forceShow]);

  const close = useCallback(
    (markDone: boolean) => {
      if (markDone && !forceShow) {
        localStorage.setItem(STORAGE_KEY, "1");
      }
      setVisible(false);
      onClose();
    },
    [forceShow, onClose]
  );

  const goTo = (next: number, dir: "left" | "right") => {
    if (animating) return;
    setAnimating(true);
    setSlideDir(dir);
    setTimeout(() => {
      setStep(next);
      setAnimating(false);
    }, 220);
  };

  const prev = () => step > 0 && goTo(step - 1, "left");
  const next = () => {
    if (step < STEPS.length - 1) goTo(step + 1, "right");
    else close(true);
  };

  if (!visible) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.78)", backdropFilter: "blur(6px)" }}
      onClick={() => close(false)}
    >
      <div
        className="relative w-full max-w-md bg-gray-900 border border-gray-700/80 rounded-3xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-300"
        onClick={(e) => e.stopPropagation()}
        style={{ boxShadow: "0 0 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.06)" }}
      >
        {/* Top gradient accent line */}
        <div
          className={`h-[3px] w-full bg-gradient-to-r ${current.color}`}
          style={{ opacity: 0.9 }}
        />

        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-400 font-medium tracking-widest uppercase">
              Quick Start Guide
            </span>
          </div>
          <button
            onClick={() => close(false)}
            className="text-gray-500 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-1.5 rounded-full"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Visual area */}
        <div
          className={`mx-6 mb-5 rounded-2xl border bg-gradient-to-br ${current.color} ${current.border} h-32 flex items-center justify-center overflow-hidden`}
          style={{ transition: "opacity 0.22s ease", opacity: animating ? 0 : 1 }}
        >
          {STEP_VISUALS[step]}
        </div>

        {/* Text content */}
        <div
          className="px-6"
          style={{
            opacity: animating ? 0 : 1,
            transform: animating
              ? `translateX(${slideDir === "right" ? "14px" : "-14px"})`
              : "translateX(0)",
            transition: "opacity 0.22s ease, transform 0.22s ease",
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{current.icon}</span>
            <h2 className="text-base font-bold text-white leading-tight">{current.title}</h2>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">{current.description}</p>
          <p className={`text-xs mt-2.5 font-medium ${current.accent}`}>{current.tip}</p>
        </div>

        {/* Step dots */}
        <div className="flex items-center justify-center gap-1.5 mt-5 mb-4">
          {STEPS.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i, i > step ? "right" : "left")}
              className={`rounded-full transition-all duration-300 ${
                i === step ? `w-6 h-2 ${current.dot}` : "w-2 h-2 bg-gray-700 hover:bg-gray-500"
              }`}
              aria-label={`Go to step ${i + 1}`}
            />
          ))}
        </div>

        {/* Navigation row */}
        <div className="flex items-center justify-between px-6 pb-6 gap-3">
          <button
            onClick={prev}
            disabled={step === 0}
            className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors px-3 py-2 rounded-xl hover:bg-gray-800"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>

          <div className="flex items-center gap-2">
            {!isLast && (
              <button
                onClick={() => close(true)}
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-3 py-2 rounded-xl hover:bg-gray-800"
              >
                Skip tour
              </button>
            )}
            <button
              onClick={next}
              className="flex items-center gap-2 text-sm font-semibold text-white px-5 py-2.5 rounded-xl transition-all bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-900/40"
            >
              {isLast ? "✨ Get Started" : "Next"}
              {!isLast && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Step counter */}
        <div className="absolute bottom-[1.6rem] left-1/2 -translate-x-1/2 pointer-events-none">
          <span className="text-[10px] text-gray-600 font-mono select-none">
            {step + 1} / {STEPS.length}
          </span>
        </div>
      </div>
    </div>
  );
}
