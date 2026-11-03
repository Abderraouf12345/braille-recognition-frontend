"use client";

import { useState, useRef } from "react";
import { Info, X, Mail, Loader2, RotateCcw, HelpCircle } from "lucide-react";
import ImageWorkspace from "@/components/ImageWorkspace";
import LightDial from "@/components/LightDial";
import ResultsPanel from "@/components/ResultsPanel";
import OnboardingModal from "@/components/OnboardingModal";
import InteractiveTour from "@/components/InteractiveTour";
import GuideChoiceModal from "@/components/GuideChoiceModal";
import { optimizeImageForUpload } from "@/utils/imageCompressor";
import { getOrCreateDeviceId } from "@/lib/clientDevice";

export default function Dashboard() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [corners, setCorners] = useState<{x: number, y: number}[]>([]);
  const [lightAngle, setLightAngle] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState("arabic");

  const [results, setResults] = useState({
    braille: "",
    arabic: ""
  });
  const [overlayImage, setOverlayImage] = useState<string | null>(null);
  const [showAbout, setShowAbout] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingForced, setOnboardingForced] = useState(false);
  const [showGuideChoice, setShowGuideChoice] = useState(false);
  const [showInteractiveTour, setShowInteractiveTour] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Four-corner selection fits screen; Result overlay allows full-page scrolling
  const isCornerSelectionMode = Boolean(imageFile && !overlayImage);

  const handleReset = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsProcessing(false);
    setImageFile(null);
    setCorners([]);
    setLightAngle(0);
    setResults({ braille: "", arabic: "" });
    setOverlayImage(null);
    setError(null);
  };

  // Pre-load demo state for the interactive tour
  const handleStartTourDemo = async () => {
    try {
      const response = await fetch("/guide/step-2.jpg");
      const blob = await response.blob();
      const demoFile = new File([blob], "sample_braille_exam.jpg", { type: "image/jpeg" });
      setImageFile(demoFile);
      setLanguage("english_g1");
      setResults({
        braille: "⠠⠞⠓⠑ ⠋⠊⠗⠎⠞ ⠑⠝⠛⠇⠊⠎⠓ ⠑⠭⠁⠍\n⠠⠛⠕⠕⠙ ⠍⠕⠗⠝⠊⠝⠛⠂ ⠍⠽ ⠝⠁⠍⠑ ⠊⠎ ⠠⠎⠓⠁⠍\n⠠⠊ ⠁⠍ ⠝⠊⠝⠑ ⠽⠑⠁⠗⠎ ⠕⠇⠙",
        arabic: "The first english exam\nGood morning, my name is Sham.\nI am nine years old."
      });
      setError(null);
    } catch (e) {
      console.error("Failed to load demo image for tour:", e);
    }
  };

  const handleEndTourDemo = () => {
    handleReset();
  };

  const handleProcess = async () => {
    if (!imageFile || corners.length !== 4) return;
    setIsProcessing(true);
    setError(null);
    setResults({ braille: "", arabic: "" });
    setOverlayImage(null);

    let uploadFile = imageFile;
    if (imageFile.size > 3.5 * 1024 * 1024) {
      try {
        uploadFile = await optimizeImageForUpload(imageFile);
      } catch {
        uploadFile = imageFile;
      }
    }

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("corners", JSON.stringify(corners));
    formData.append("lightAngle", lightAngle.toString());
    formData.append("language", language);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes("hf.space")
        ? process.env.NEXT_PUBLIC_API_URL
        : "/api";
      const response = await fetch(`${API_URL}/process-stream`, {
        method: "POST",
        headers: {
          "x-device-id": getOrCreateDeviceId(),
        },
        body: formData,
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream not supported by browser/server.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep partial chunk in buffer

        for (const block of lines) {
          if (!block.trim()) continue;
          
          let eventType = "message";
          let dataStr = "";

          const eventMatch = block.match(/^event:\s*(.+)$/m);
          if (eventMatch) eventType = eventMatch[1].trim();

          const dataMatch = block.match(/^data:\s*(.+)$/m);
          if (dataMatch) dataStr = dataMatch[1].trim();

          if (eventType === "result" && dataStr) {
            try {
              const parsed = JSON.parse(dataStr);
              setResults({
                braille: parsed.braille_text || "",
                arabic: parsed.translated_text || ""
              });
              if (parsed.overlay_image) {
                setOverlayImage(`data:image/jpeg;base64,${parsed.overlay_image}`);
              }
            } catch (err) {
              console.error("JSON parse error:", err);
            }
          } else if (eventType === "error") {
            setError(dataStr || "Processing failed");
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        return;
      }
      console.error(err);
      setError(err.message || "Failed to process image");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`min-h-screen bg-gray-950 text-gray-100 p-4 sm:p-5 lg:p-6 flex flex-col font-sans selection:bg-blue-500/30 ${
      isCornerSelectionMode ? "lg:h-screen lg:max-h-screen lg:overflow-hidden" : ""
    }`}>
      {/* ── Top Header ── */}
      <header className="mb-4 flex items-start justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Braille Recognition
            </h1>
          </div>
          <p className="text-gray-500 text-xs sm:text-sm mt-1">AI-powered Braille recognition &amp; multi-language translation</p>
        </div>
        
        <div className="flex items-center gap-2">
          {imageFile && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 transition-colors bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-2 rounded-xl shrink-0"
              title="Clear image and start over"
            >
              <RotateCcw className="w-4 h-4" />
              New Image
            </button>
          )}

          <button
            onClick={() => setShowGuideChoice(true)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-purple-400 transition-colors bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-2 rounded-xl shrink-0"
            title="How to use this app"
          >
            <HelpCircle className="w-4 h-4" />
            How to use?
          </button>

          <button
            onClick={() => setShowAbout(true)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-blue-400 transition-colors bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-2 rounded-xl shrink-0"
          >
            <Info className="w-4 h-4" />
            About
          </button>
        </div>
      </header>

      <div className={`flex-1 flex flex-col lg:flex-row gap-6 min-h-0 ${
        isCornerSelectionMode ? "lg:overflow-hidden" : ""
      }`}>
        
        {/* Left Side: Workspace */}
        <div 
          id="tour-workspace"
          className={`flex-1 flex flex-col relative ${
            isCornerSelectionMode ? "min-h-[420px] lg:min-h-0 h-full" : "min-h-[500px]"
          }`}
        >
          <ImageWorkspace 
            imageFile={imageFile} 
            setImageFile={(file) => {
              setImageFile(file);
              if (!file) setOverlayImage(null);
            }} 
            corners={corners} 
            setCorners={setCorners} 
            overlayImage={overlayImage}
            onClearOverlay={() => setOverlayImage(null)}
            isLocked={isProcessing}
          />
        </div>

        {/* Right Side: Controls & Results */}
        <div className={`w-full lg:w-[420px] xl:w-[460px] flex flex-col gap-2.5 sm:gap-3 lg:gap-[1.5vh] shrink-0 pr-1 lg:pr-2 custom-scrollbar ${
          isCornerSelectionMode ? "lg:h-full lg:overflow-y-auto" : ""
        }`}>
          
          <div id="tour-light-dial">
            <LightDial angle={lightAngle} setAngle={setLightAngle} />
          </div>
          
          <div id="tour-controls" className="flex flex-col gap-2.5 sm:gap-3 lg:gap-[1.5vh]">
            <div className="bg-gray-800 p-3 sm:p-4 lg:p-[1.5vh] rounded-2xl border border-gray-700 shadow-xl shrink-0">
              <h3 className="text-gray-400 text-xs sm:text-sm font-medium mb-2 sm:mb-2.5 lg:mb-[1vh]">Translation Language</h3>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 text-gray-200 text-xs sm:text-sm rounded-xl focus:ring-blue-500 focus:border-blue-500 block p-2.5 sm:p-3 lg:p-[1.2vh] outline-none"
              >
                <option value="arabic">Arabic — عربي</option>
                <option value="french">French — Français</option>
                <option value="english_g1">English G1 — Grade 1 (literal)</option>
                <option value="english_g2">English G2 — Grade 2 (contrac.)</option>
                <option value="russian">Russian — Русский</option>
                <option value="chinese">Chinese — 中文</option>
                <option value="shuangpin">Shuangpin — 汉语双拼盲文</option>
                <option value="raw">Braille Unicode Only (No Dictionary)</option>
              </select>
            </div>
            
            <div className="shrink-0">
              <button 
                onClick={handleProcess}
                disabled={!imageFile || isProcessing || corners.length !== 4}
                className="w-full relative overflow-hidden group bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2.5 sm:py-3 lg:py-[1.4vh] rounded-2xl shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all font-semibold text-sm sm:text-base lg:text-lg flex items-center justify-center space-x-3"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span>Extracting & Translating...</span>
                  </>
                ) : (
                  <span>Extract & Translate</span>
                )}
              </button>
              {error && (
                <p className="text-red-400 text-sm mt-2 bg-red-900/20 p-2.5 rounded-lg border border-red-800">
                  {error}
                </p>
              )}
            </div>
          </div>

          <div id="tour-results" className="flex-1 flex flex-col min-h-0">
            <ResultsPanel 
              braille={results.braille} 
              arabic={results.arabic}
              language={language}
            />
          </div>

        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="mt-3 pt-3 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-600 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2"><span>© {new Date().getFullYear()} Braille Recognition — All rights reserved.</span><span className="text-gray-700 hidden sm:inline">·</span><span>Awarded the &ldquo;Innovative Project&rdquo; label by the National Committee for Labeling Startups &amp; Innovative Projects (Algeria).</span></div>
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <a
            href="mailto:abderraouf.benmohieddine@g.enp.edu.dz"
            className="flex items-center gap-1.5 text-gray-500 hover:text-blue-400 transition-colors"
          >
            <Mail className="w-3.5 h-3.5" />
            abderraouf.benmohieddine@g.enp.edu.dz
          </a>
          <span className="text-gray-700 hidden sm:inline">·</span>
          <a
            href="mailto:abderraouf.amellal@g.enp.edu.dz"
            className="flex items-center gap-1.5 text-gray-500 hover:text-blue-400 transition-colors"
          >
            <Mail className="w-3.5 h-3.5" />
            abderraouf.amellal@g.enp.edu.dz
          </a>
        </div>
      </footer>

      {/* ── About / How-It-Works Modal ── */}
      {showAbout && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={() => setShowAbout(false)}
        >
          <div
            className="relative bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-800">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⠿</span>
                <div>
                  <h2 className="text-lg font-bold text-white">About Braille Recognition</h2>
                  <p className="text-xs text-gray-500 mt-0.5">AI-powered Braille recognition &amp; translation</p>
                </div>
              </div>
              <button
                onClick={() => setShowAbout(false)}
                className="text-gray-500 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-1.5 rounded-full"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* What it does */}
            <div className="p-6 border-b border-gray-800">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">What is this?</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                This application uses deep learning to automatically recognize Braille characters from a photo
                and translate them into multiple languages in real time. Simply upload a photo of any
                Braille document, define the page corners, set the lighting direction, and get an
                instant translation.
              </p>
            </div>

            {/* How to use */}
            <div className="p-6 border-b border-gray-800">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">How to use</h3>
              <ol className="flex flex-col gap-4">
                {[
                  { step: "1", icon: "📷", title: "Upload a Braille image", desc: "Click the upload area and select a clear photo of a Braille page (JPG, PNG, WebP, TIFF or BMP)." },
                  { step: "2", icon: "📐", title: "Adjust the corner markers", desc: "Drag the four blue corner handles to align with the edges of the Braille page for accurate perspective correction." },
                  { 
                    step: "3", 
                    icon: "💡", 
                    title: "Set light angle (Recto / Verso separation)", 
                    desc: "This feature is only intended to help distinguish the <strong>recto</strong> (front raised dots) from the <strong>verso</strong> (back indentations) on double-sided Braille documents. It is a basic, non-deterministic heuristic rather than an exact light detector: if selecting an angle (e.g. 0°) incorrectly captures the verso layer, rotating by <strong>180°</strong> will invert the classification to retrieve the recto layer." 
                  },
                  { step: "4", icon: "🌐", title: "Choose a language &amp; translate", desc: "Select your target language and click Extract &amp; Translate. Results appear in real time." },
                  { step: "5", icon: "🔊", title: "Listen, copy or download", desc: "Use the audio player to hear the translation read aloud, copy it to your clipboard, or download it as a text file." },
                ].map(({ step, icon, title, desc }) => (
                  <li key={step} className="flex gap-4">
                    <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 text-blue-400 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {step}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-200">{icon} {title}</p>
                      <p className="text-xs text-gray-500 mt-0.5 leading-relaxed" dangerouslySetInnerHTML={{ __html: desc }} />
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            {/* Supported Languages */}
            <div className="p-6 border-b border-gray-800">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Supported languages</h3>
              <div className="flex flex-wrap gap-2">
                {["Arabic", "French", "English G1", "English G2", "Russian", "Chinese", "Shuangpin"].map((lang) => (
                  <span key={lang} className="text-xs bg-gray-800 border border-gray-700 text-gray-300 px-2.5 py-1 rounded-full">
                    {lang}
                  </span>
                ))}
              </div>
            </div>

            {/* Contact */}
            <div className="p-6">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Contact</h3>
              <a
                href="mailto:abderraouf.benmohieddine@g.enp.edu.dz"
                className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm"
              >
                <Mail className="w-4 h-4" />
                abderraouf.benmohieddine@g.enp.edu.dz
              </a>
              <a
                href="mailto:abderraouf.amellal@g.enp.edu.dz"
                className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors text-sm mt-2"
              >
                <Mail className="w-4 h-4" />
                abderraouf.amellal@g.enp.edu.dz
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ── Guide Choice Dialog ── */}
      <GuideChoiceModal
        isOpen={showGuideChoice}
        onClose={() => setShowGuideChoice(false)}
        onSelectInteractiveTour={() => setShowInteractiveTour(true)}
        onSelectVisualGuide={() => {
          setOnboardingForced(true);
          setShowOnboarding(true);
        }}
      />

      {/* ── Interactive Live Spotlight Tour ── */}
      <InteractiveTour
        isOpen={showInteractiveTour}
        onClose={() => setShowInteractiveTour(false)}
        onStartDemo={handleStartTourDemo}
        onEndDemo={handleEndTourDemo}
        onOpenVisualGuide={() => {
          setOnboardingForced(true);
          setShowOnboarding(true);
        }}
      />

      {/* ── First-visit Visual Guide Modal (Screenshots & Video) ── */}
      <OnboardingModal
        forceShow={onboardingForced && showOnboarding}
        onClose={() => {
          setShowOnboarding(false);
          setOnboardingForced(false);
        }}
        onStartInteractiveTour={() => setShowInteractiveTour(true)}
      />
    </div>
  );
}
