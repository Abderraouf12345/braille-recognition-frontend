"use client";

import { useState } from "react";
import { 
  Award, 
  X, 
  Calendar, 
  User, 
  FileText, 
  ShieldCheck, 
  ExternalLink, 
  Check, 
  Copy, 
  Maximize2,
  Building2,
  Sparkles
} from "lucide-react";

interface LabelModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LabelModal({ isOpen, onClose }: LabelModalProps) {
  const [activeTab, setActiveTab] = useState<"certificate" | "cover" | "details">("certificate");
  const [copied, setCopied] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);

  if (!isOpen) return null;

  const labelNumber = "30092623702";

  const handleCopy = () => {
    navigator.clipboard.writeText(labelNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-black/80 backdrop-blur-md transition-all animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="relative bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 border border-emerald-500/30 rounded-2xl sm:rounded-3xl shadow-[0_0_50px_rgba(16,185,129,0.15)] w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden text-gray-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Glow Accent Bar */}
        <div className="h-1.5 w-full bg-gradient-to-r from-emerald-500 via-teal-400 to-blue-500 shrink-0" />

        {/* Modal Header */}
        <div className="flex items-start justify-between p-4 sm:p-6 border-b border-gray-800 bg-gray-900/60 shrink-0">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="w-11 h-11 sm:w-13 sm:h-13 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              <Award className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-400" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg sm:text-xl md:text-2xl font-bold bg-gradient-to-r from-emerald-300 via-teal-200 to-white bg-clip-text text-transparent">
                  Label "Projet Innovant"
                </h2>
                <span className="text-xs sm:text-sm font-arabic font-semibold text-emerald-400/90 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  علامة مشروع مبتكر
                </span>
              </div>
              <p className="text-xs sm:text-sm text-gray-400 mt-1 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>اللجنة الوطنية لمنح علامة مؤسسة ناشئة ومشروع مبتكر · الجزائر</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 p-2 rounded-xl border border-gray-700 shrink-0"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-4 sm:px-6 pt-3 pb-2 border-b border-gray-800 bg-gray-950/50 shrink-0 overflow-x-auto custom-scrollbar">
          <button
            onClick={() => setActiveTab("certificate")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all shrink-0 ${
              activeTab === "certificate"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 border border-transparent"
            }`}
          >
            <FileText className="w-4 h-4 text-emerald-400" />
            <span>Official Decree (القرار الرسمي)</span>
          </button>

          <button
            onClick={() => setActiveTab("cover")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all shrink-0 ${
              activeTab === "cover"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 border border-transparent"
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Accreditation Folder (غلاف العلامة)</span>
          </button>

          <button
            onClick={() => setActiveTab("details")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all shrink-0 ${
              activeTab === "details"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 border border-transparent"
            }`}
          >
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Legal Details &amp; Summary</span>
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 custom-scrollbar space-y-6">
          
          {/* Top Quick Highlights Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
            {/* Card 1: Project Name */}
            <div className="p-3 bg-gray-900/80 rounded-xl border border-gray-800">
              <span className="text-[11px] text-gray-400 uppercase tracking-wider block font-medium">Project Name</span>
              <span className="text-sm font-bold text-white mt-0.5 block truncate">BrailleVision</span>
              <span className="text-[10px] text-emerald-400 block font-arabic mt-0.5">مشروع BrailleVision</span>
            </div>

            {/* Card 2: Label Number */}
            <div className="p-3 bg-gray-900/80 rounded-xl border border-gray-800 relative group">
              <span className="text-[11px] text-gray-400 uppercase tracking-wider block font-medium">Label Number</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-xs sm:text-sm font-mono font-bold text-emerald-300">{labelNumber}</span>
                <button 
                  onClick={handleCopy}
                  title="Copy registration number"
                  className="text-gray-500 hover:text-emerald-300 transition-colors p-1"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
              <span className="text-[10px] text-gray-500 block font-arabic mt-0.5">رقم العلامة المعتمد</span>
            </div>

            {/* Card 3: Validity */}
            <div className="p-3 bg-gray-900/80 rounded-xl border border-gray-800">
              <span className="text-[11px] text-gray-400 uppercase tracking-wider block font-medium">Validity Period</span>
              <span className="text-xs sm:text-sm font-semibold text-white mt-0.5 block">2026 – 2028</span>
              <span className="text-[10px] text-emerald-400 block mt-0.5">2 Years (Renewable)</span>
            </div>

            {/* Card 4: Status */}
            <div className="p-3 bg-emerald-950/30 rounded-xl border border-emerald-500/30">
              <span className="text-[11px] text-emerald-400 uppercase tracking-wider block font-medium flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Accreditation
              </span>
              <span className="text-xs sm:text-sm font-bold text-emerald-300 mt-0.5 block">Officially Certified</span>
              <span className="text-[10px] text-gray-400 block font-arabic mt-0.5">ممنوحة رسمياً وسارية</span>
            </div>
          </div>

          {/* Tab 1: Certificate Document Viewer */}
          {activeTab === "certificate" && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-emerald-950/30 rounded-xl border border-emerald-500/20 text-xs sm:text-sm text-gray-300">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>
                    Official Ministerial Decision signed by the President of the National Startup Committee.
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <a
                    href="/label/certificate.png"
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 underline font-medium"
                  >
                    <span>Open Full Resolution</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>

              {/* Document Image Frame */}
              <div className="relative rounded-2xl overflow-hidden border border-gray-800 bg-gray-950 flex items-center justify-center group shadow-xl">
                <img
                  src="/label/certificate.png"
                  alt="Official Decision - Label Projet Innovant (BrailleVision)"
                  className="w-full h-auto max-h-[550px] object-contain rounded-xl transition-transform duration-300 cursor-zoom-in"
                  onClick={() => setIsZoomed(true)}
                />
                
                <button
                  onClick={() => setIsZoomed(true)}
                  className="absolute bottom-4 right-4 bg-gray-900/90 hover:bg-gray-800 text-white px-3 py-1.5 rounded-xl border border-gray-700 text-xs flex items-center gap-1.5 shadow-lg opacity-90 group-hover:opacity-100 transition-opacity"
                >
                  <Maximize2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Click to Expand</span>
                </button>
              </div>
            </div>
          )}

          {/* Tab 2: Accreditation Cover */}
          {activeTab === "cover" && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-emerald-950/30 rounded-xl border border-emerald-500/20 text-xs sm:text-sm text-gray-300">
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>
                    National Startup Committee (Algeria) — Label "Projet Innovant" Folder.
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <a
                    href="/label/label-cover.png"
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 underline font-medium"
                  >
                    <span>Open Full Resolution</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>

              {/* Cover Image Frame */}
              <div className="relative rounded-2xl overflow-hidden border border-gray-800 bg-gray-950 flex items-center justify-center group shadow-xl">
                <img
                  src="/label/label-cover.png"
                  alt="Label Projet Innovant - National Startup Committee Cover"
                  className="w-full h-auto max-h-[550px] object-contain rounded-xl transition-transform duration-300 cursor-zoom-in"
                  onClick={() => setIsZoomed(true)}
                />
                
                <button
                  onClick={() => setIsZoomed(true)}
                  className="absolute bottom-4 right-4 bg-gray-900/90 hover:bg-gray-800 text-white px-3 py-1.5 rounded-xl border border-gray-700 text-xs flex items-center gap-1.5 shadow-lg opacity-90 group-hover:opacity-100 transition-opacity"
                >
                  <Maximize2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Click to Expand</span>
                </button>
              </div>
            </div>
          )}

          {/* Tab 3: Detailed Legal Articles & Project Details */}
          {activeTab === "details" && (
            <div className="space-y-4">
              {/* Project & Holders Box */}
              <div className="p-4 bg-gray-900/70 rounded-2xl border border-gray-800 space-y-3">
                <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Project Leadership &amp; Authors (أصحاب المشروع)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                    <span className="text-xs text-gray-500 block">Lead Researcher &amp; Engineer</span>
                    <span className="font-semibold text-white">BENMOHIEDDINE Abderraouf</span>
                    <span className="text-xs text-gray-400 block mt-0.5">École Nationale Polytechnique (ENP)</span>
                  </div>
                  <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                    <span className="text-xs text-gray-500 block">Lead Researcher &amp; Engineer</span>
                    <span className="font-semibold text-white">AMELLAL Abderraouf</span>
                    <span className="text-xs text-gray-400 block mt-0.5">École Nationale Polytechnique (ENP)</span>
                  </div>
                </div>
              </div>

              {/* Official Decree Content (Arabic & English) */}
              <div className="p-4 bg-gray-900/70 rounded-2xl border border-gray-800 space-y-3">
                <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  Key Legal Provisions (نص القرار الرسمي)
                </h3>

                <div className="space-y-3 text-xs sm:text-sm">
                  {/* Article 1 */}
                  <div className="p-3 rounded-xl bg-gray-950/70 border border-gray-800/80">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-emerald-400">المادة الأولى (Article 1)</span>
                      <span className="text-[11px] text-gray-500">منح العلامة</span>
                    </div>
                    <p className="font-arabic text-gray-300 text-right leading-relaxed" dir="rtl">
                      تمنح علامة <strong>"مشروع مبتكر"</strong> صالحة لمدة سنتين (2) قابلة للتجديد مرتين (2)، طبقاً للمادة 19 من المرسوم التنفيذي رقم 20-254 المؤرخ في 15 سبتمبر سنة 2020، إلى المشروع: <strong>BrailleVision</strong>.
                    </p>
                    <p className="text-gray-400 mt-2 text-xs border-t border-gray-800 pt-2">
                      Awarded the "Innovative Project" label valid for two (2) years, renewable twice, in accordance with Article 19 of Executive Decree No. 20-254, to the project: <strong>BrailleVision</strong>.
                    </p>
                  </div>

                  {/* Article 2 */}
                  <div className="p-3 rounded-xl bg-gray-950/70 border border-gray-800/80">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-emerald-400">المادة الثانية (Article 2)</span>
                      <span className="text-[11px] text-gray-500">مدة الصلاحية</span>
                    </div>
                    <p className="font-arabic text-gray-300 text-right leading-relaxed" dir="rtl">
                      تسري علامة "مشروع مبتكر" ابتداءً من تاريخ <strong>30 سبتمبر 2026</strong> إلى غاية <strong>30 سبتمبر 2028</strong>.
                    </p>
                    <p className="text-gray-400 mt-2 text-xs border-t border-gray-800 pt-2">
                      Effective from <strong>September 30, 2026</strong> through <strong>September 30, 2028</strong>.
                    </p>
                  </div>

                  {/* Legal Authority */}
                  <div className="p-3 rounded-xl bg-gray-950/70 border border-gray-800/80 flex items-start gap-3">
                    <Calendar className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                    <div className="text-xs text-gray-300 space-y-1">
                      <p>
                        <strong>Issuing Authority:</strong> National Startup Committee · Ministry of Knowledge Economy, Startups and Micro-enterprises (Algeria).
                      </p>
                      <p className="text-gray-400">
                        <strong>Signatory:</strong> Chemseddine BEMMOUSSAT, President of the National Committee for Labeling Startups &amp; Innovative Projects.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-5 border-t border-gray-800 bg-gray-900/90 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>National Startup Committee Registration: <strong className="text-emerald-300 font-mono">30092623702</strong></span>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <a
              href="/label/certificate.png"
              download="BrailleVision-Label-Projet-Innovant-30092623702.png"
              className="flex-1 sm:flex-none px-3.5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs sm:text-sm font-medium rounded-xl border border-gray-700 transition-colors flex items-center justify-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Download Document
            </a>
            <button
              onClick={onClose}
              className="flex-1 sm:flex-none px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-lg shadow-emerald-600/20 transition-colors"
            >
              Done
            </button>
          </div>
        </div>

      </div>

      {/* Lightbox / Zoom Overlay */}
      {isZoomed && (
        <div 
          className="fixed inset-0 z-[60] bg-black/95 flex items-center justify-center p-2 sm:p-4 cursor-zoom-out animate-in fade-in duration-200"
          onClick={() => setIsZoomed(false)}
        >
          <button
            onClick={() => setIsZoomed(false)}
            className="absolute top-4 right-4 text-white bg-gray-800/80 hover:bg-gray-700 p-2.5 rounded-full z-10 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
          <img
            src={activeTab === "cover" ? "/label/label-cover.png" : "/label/certificate.png"}
            alt="Expanded Document View"
            className="max-w-[96vw] max-h-[96vh] object-contain rounded-lg shadow-2xl"
          />
        </div>
      )}
    </div>
  );
}
