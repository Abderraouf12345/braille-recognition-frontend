"use client";

import { useState } from "react";
import axios from "axios";
import ImageWorkspace from "@/components/ImageWorkspace";
import LightDial from "@/components/LightDial";
import ResultsPanel from "@/components/ResultsPanel";
import { Loader2 } from "lucide-react";

export default function Dashboard() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [corners, setCorners] = useState<{x: number, y: number}[]>([]);
  const [lightAngle, setLightAngle] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState("arabic");

  const [results, setResults] = useState({
    braille: "",
    arabic: "",
    gemini: ""
  });

  const handleProcess = async () => {
    if (!imageFile || corners.length !== 4) return;
    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", imageFile);
    formData.append("corners", JSON.stringify(corners));
    formData.append("lightAngle", lightAngle.toString());
    formData.append("language", language);

    try {
      // Assuming FastAPI runs on 8000 locally
      const response = await axios.post("http://localhost:8000/process", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      if (response.data.success) {
        setResults({
          braille: response.data.braille,
          arabic: response.data.arabic,
          gemini: response.data.gemini
        });
      } else {
        setError(response.data.error || "An unknown error occurred on the server.");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to process image.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 flex flex-col font-sans selection:bg-blue-500/30">
      <header className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Braille Translator Pro
        </h1>
        <p className="text-gray-500 mt-2">Advanced structural analysis & generative correction</p>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row gap-8 min-h-0">
        
        {/* Left Side: Workspace */}
        <div className="flex-1 flex flex-col min-h-[500px] lg:min-h-0 relative">
          <ImageWorkspace 
            imageFile={imageFile} 
            setImageFile={setImageFile} 
            corners={corners} 
            setCorners={setCorners} 
          />
        </div>

        {/* Right Side: Controls & Results */}
        <div className="w-full lg:w-[450px] xl:w-[500px] flex flex-col shrink-0 overflow-y-auto pr-2 custom-scrollbar">
          
          <LightDial angle={lightAngle} setAngle={setLightAngle} />
          
          <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700 shadow-xl mt-6">
            <h3 className="text-gray-400 text-sm font-medium mb-3">Translation Language</h3>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-xl focus:ring-blue-500 focus:border-blue-500 block p-3 outline-none"
            >
              <option value="arabic">Arabic — عربي</option>
              <option value="french">French — Français</option>
              <option value="english_g1">English G1 — Grade 1 (literal)</option>
              <option value="english_g2">English G2 — Grade 2 (contrac.)</option>
              <option value="russian">Russian — Русский</option>
            </select>
          </div>
          
          <div className="mt-6">
            <button 
              onClick={handleProcess}
              disabled={!imageFile || isProcessing || corners.length !== 4}
              className="w-full relative overflow-hidden group bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-4 rounded-2xl shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all font-semibold text-lg flex items-center justify-center space-x-3"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>Processing Pipeline...</span>
                </>
              ) : (
                <span>Extract & Translate</span>
              )}
            </button>
            {error && (
              <p className="text-red-400 text-sm mt-3 bg-red-900/20 p-3 rounded-lg border border-red-800">
                {error}
              </p>
            )}
          </div>

          <ResultsPanel 
            braille={results.braille} 
            arabic={results.arabic} 
            gemini={results.gemini}
            language={language}
          />

        </div>
      </div>
    </div>
  );
}
