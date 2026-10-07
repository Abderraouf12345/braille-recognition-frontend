"use client";

import { useState, useEffect, useRef } from "react";
import { Download, Volume2, Loader2, Play, Pause, FastForward, Rewind, X } from "lucide-react";
import axios from "axios";

interface ResultsPanelProps {
  braille: string;
  arabic: string;
  language?: string;
}

export default function ResultsPanel({ braille, arabic, language = "arabic" }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<"braille" | "arabic">("arabic");

  // Format Braille text to ensure every line is left-justified while preserving vertical gaps
  const formattedBraille = braille ? braille.split('\n').map(line => line.replace(/^[\s\u2800]+/, '')).join('\n') : "";

  // TTS State
  const [voicesByLang, setVoicesByLang] = useState<Record<string, { label: string, value: string }[]>>({});
  const [langs, setLangs] = useState<string[]>([]);
  const [selectedLang, setSelectedLang] = useState<string>("Arabic");
  const [selectedVoice, setSelectedVoice] = useState<string>("");
  const [isTtsLoading, setIsTtsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Audio Player State
  const [showPlayer, setShowPlayer] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const formatTime = (time: number) => {
    if (isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    // Fetch voices
    const fetchVoices = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes("hf.space")
          ? process.env.NEXT_PUBLIC_API_URL
          : "/api";
        const response = await axios.get(`${API_URL}/voices`);
        if (response.data.success) {
          setVoicesByLang(response.data.voices);
          setLangs(response.data.languages);

          const defaultLang = response.data.languages.includes("Arabic") ? "Arabic" : response.data.languages[0];
          setSelectedLang(defaultLang);

          const defaultVoices = response.data.voices[defaultLang] || [];
          if (defaultVoices.length > 0) {
            const algVoice = defaultVoices.find((v: any) => v.label.includes("Algeria"));
            setSelectedVoice(algVoice ? algVoice.value : defaultVoices[0].value);
          }
        }
      } catch (err) {
        console.error("Failed to fetch voices:", err);
      }
    };
    fetchVoices();
  }, []);

  useEffect(() => {
    if (selectedLang && voicesByLang[selectedLang]) {
      const available = voicesByLang[selectedLang];
      if (available.length > 0) {
        const algVoice = available.find((v: any) => v.label.includes("Algeria"));
        setSelectedVoice(algVoice ? algVoice.value : available[0].value);
      } else {
        setSelectedVoice("");
      }
    }
  }, [selectedLang, voicesByLang]);

  const handlePlayAudio = async () => {
    let content = "";
    if (activeTab === "braille") content = formattedBraille;
    else content = arabic;

    if (!content.trim() || !selectedVoice) return;

    setIsTtsLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes("hf.space")
        ? process.env.NEXT_PUBLIC_API_URL
        : "/api";
      const response = await axios.post(`${API_URL}/tts`, {
        text: content,
        voice: selectedVoice
      }, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data], { type: "audio/mpeg" }));

      if (audioUrl) {
        window.URL.revokeObjectURL(audioUrl);
      }

      setAudioUrl(url);
      setShowPlayer(true);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = url;
        audioRef.current.play().catch(e => console.error("Auto-play failed:", e));
        setIsPlaying(true);
      }
    } catch (err) {
      console.error("Failed to generate TTS:", err);
    } finally {
      setIsTtsLoading(false);
    }
  };

  const handleDownload = () => {
    let content = "";
    if (activeTab === "braille") content = formattedBraille;
    else content = arabic;

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `braille_result_${activeTab}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const currentContent = activeTab === "braille" ? formattedBraille : arabic;

  return (
    <div className="flex-1 bg-gray-800 rounded-2xl flex flex-col border border-gray-700 shadow-xl overflow-hidden mt-6">
      {/* Tabs Header */}
      <div className="flex border-b border-gray-700">
        <button
          onClick={() => setActiveTab("arabic")}
          className={`flex-1 py-4 text-sm font-medium transition-colors ${activeTab === "arabic" ? "text-blue-400 border-b-2 border-blue-400 bg-gray-800" : "text-gray-400 hover:text-gray-200 hover:bg-gray-700"
            }`}
        >
          Translated Text
        </button>
        <button
          onClick={() => setActiveTab("braille")}
          className={`flex-1 py-4 text-sm font-medium transition-colors ${activeTab === "braille" ? "text-blue-400 border-b-2 border-blue-400 bg-gray-800" : "text-gray-400 hover:text-gray-200 hover:bg-gray-700"
            }`}
        >
          Braille Unicode
        </button>
      </div>

      {/* Content Area */}
      <div
        className={`flex-1 p-6 overflow-y-auto overflow-x-auto max-h-[500px] bg-gray-900 font-mono text-lg text-gray-200 leading-relaxed ${activeTab === 'braille' ? 'text-left whitespace-pre' : 'text-start whitespace-pre-wrap'}`}
        dir={activeTab !== "braille" && language === "arabic" ? "rtl" : "ltr"}
      >
        {activeTab === "braille" && (formattedBraille || "No braille decoded yet.")}
        {activeTab === "arabic" && (
          language === "raw"
            ? <span className="text-gray-500 italic">Translation disabled in Raw Mode. Switch to a language to enable translation.</span>
            : (arabic || "No translated text yet.")
        )}
      </div>

      {/* TTS Controls */}
      <div className="p-4 border-t border-gray-700 bg-gray-800 flex flex-col space-y-3">
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 text-gray-200 text-xs rounded-xl focus:ring-blue-500 focus:border-blue-500 p-2 outline-none"
          >
            {langs.map(l => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>

          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 text-gray-200 text-xs rounded-xl focus:ring-blue-500 focus:border-blue-500 p-2 outline-none"
          >
            {(voicesByLang[selectedLang] || []).map(v => (
              <option key={v.value} value={v.value}>{v.label}</option>
            ))}
          </select>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handlePlayAudio}
            disabled={!currentContent || !selectedVoice || isTtsLoading}
            className="flex-1 flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white py-3 rounded-xl transition-all font-medium"
          >
            {isTtsLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Volume2 className="w-5 h-5" />}
            <span>{isTtsLoading ? "Generating..." : "Play Audio"}</span>
          </button>

          <button
            onClick={handleDownload}
            disabled={!braille}
            className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white py-3 rounded-xl transition-all font-medium"
          >
            <Download className="w-5 h-5" />
            <span>Download</span>
          </button>
        </div>

        {/* Custom Audio Player */}
        {showPlayer && (
          <div className="mt-4 bg-gray-900 border border-gray-700 rounded-xl p-4 flex flex-col space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-emerald-400 flex items-center gap-2">
                <Volume2 className="w-4 h-4" />
                Audio Player
              </span>
              <button 
                onClick={() => { 
                  setShowPlayer(false); 
                  if (audioRef.current) audioRef.current.pause(); 
                }} 
                className="text-gray-400 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-1 rounded-full"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-400 w-10 text-right font-mono">{formatTime(currentTime)}</span>
              <input 
                type="range" 
                min={0} 
                max={duration || 100} 
                value={currentTime} 
                onChange={(e) => {
                  if (audioRef.current) {
                    audioRef.current.currentTime = Number(e.target.value);
                  }
                }}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <span className="text-xs text-gray-400 w-10 font-mono">{formatTime(duration)}</span>
            </div>

            <div className="flex justify-center items-center space-x-6">
              <button 
                onClick={() => { if (audioRef.current) audioRef.current.currentTime -= 5; }}
                className="text-gray-300 hover:text-emerald-400 transition-colors p-2 bg-gray-800 rounded-full hover:bg-gray-700 active:scale-95"
                title="Rewind 5 seconds"
              >
                <Rewind className="w-5 h-5 fill-current" />
              </button>
              
              <button 
                onClick={() => {
                  if (audioRef.current) {
                    if (isPlaying) audioRef.current.pause();
                    else audioRef.current.play();
                  }
                }}
                className="text-white bg-emerald-600 hover:bg-emerald-500 transition-all p-3 rounded-full shadow-lg hover:scale-105 active:scale-95 flex items-center justify-center"
              >
                {isPlaying ? <Pause className="w-6 h-6 fill-current" /> : <Play className="w-6 h-6 fill-current ml-1" />}
              </button>
              
              <button 
                onClick={() => { if (audioRef.current) audioRef.current.currentTime += 5; }}
                className="text-gray-300 hover:text-emerald-400 transition-colors p-2 bg-gray-800 rounded-full hover:bg-gray-700 active:scale-95"
                title="Fast forward 5 seconds"
              >
                <FastForward className="w-5 h-5 fill-current" />
              </button>
            </div>
          </div>
        )}

        <audio 
          ref={audioRef} 
          className="hidden" 
          onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onEnded={() => setIsPlaying(false)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
      </div>
    </div>
  );
}
