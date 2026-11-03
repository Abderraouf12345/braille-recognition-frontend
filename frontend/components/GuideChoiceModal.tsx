"use client";

import { X, Sparkles, Navigation, BookOpen, Play } from "lucide-react";

interface GuideChoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectInteractiveTour: () => void;
  onSelectVisualGuide: () => void;
}

export default function GuideChoiceModal({
  isOpen,
  onClose,
  onSelectInteractiveTour,
  onSelectVisualGuide,
}: GuideChoiceModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg bg-gray-900 border border-gray-700/80 rounded-3xl shadow-2xl overflow-hidden p-6 text-gray-100"
        onClick={(e) => e.stopPropagation()}
        style={{ boxShadow: "0 0 70px rgba(0, 0, 0, 0.8), 0 0 30px rgba(59, 130, 246, 0.15)" }}
      >
        {/* Top Accent Gradient */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">How would you like to explore?</h2>
              <p className="text-xs text-gray-400">Choose the guide format that suits you best</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-1.5 rounded-full"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Choice Cards */}
        <div className="grid grid-cols-1 gap-3.5 mt-5">
          {/* Option 1: Interactive Live Walkthrough */}
          <button
            onClick={() => {
              onClose();
              onSelectInteractiveTour();
            }}
            className="group text-left p-4 rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-950/40 via-gray-900 to-indigo-950/30 hover:border-blue-400/60 hover:from-blue-950/60 transition-all shadow-lg hover:shadow-blue-900/30 cursor-pointer relative overflow-hidden"
          >
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0 group-hover:scale-110 transition-transform">
                <Navigation className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm sm:text-base font-bold text-white group-hover:text-blue-300 transition-colors">
                    Interactive Walkthrough
                  </h3>
                  <span className="text-[10px] uppercase tracking-wider font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40 px-2 py-0.5 rounded-full">
                    Recommended
                  </span>
                </div>
                <p className="text-xs text-gray-300 mt-1.5 leading-relaxed">
                  Spotlight guidance directly on the live interface with an automatically loaded sample Braille document.
                </p>
              </div>
            </div>
          </button>

          {/* Option 2: Visual Guide with Screenshots */}
          <button
            onClick={() => {
              onClose();
              onSelectVisualGuide();
            }}
            className="group text-left p-4 rounded-2xl border border-gray-800 bg-gray-900/80 hover:bg-gray-800/80 hover:border-gray-700 transition-all cursor-pointer"
          >
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400 shrink-0 group-hover:scale-110 transition-transform">
                <BookOpen className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm sm:text-base font-bold text-white group-hover:text-purple-300 transition-colors">
                  Visual Guide &amp; Demo Video
                </h3>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  Browse step-by-step screenshots, read detailed explanations, and watch video demonstrations at your own pace.
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
          <span>You can re-open this anytime from the header</span>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
}
