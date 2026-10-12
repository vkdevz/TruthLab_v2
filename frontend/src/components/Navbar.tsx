import React from 'react';

export const Navbar: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-[#0a0d14]/90 border-b border-white/10 px-6 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-sky-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
            TL
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-tight text-white text-lg">TruthLab</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                v2.0 Research
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono hidden sm:block">
              Multimodal Evidence-Aware Misinformation Adjudication
            </p>
          </div>
        </div>

        {/* Telemetry Indicator */}
        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900/80 border border-white/5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>API Online :1234</span>
            <span className="text-slate-600">|</span>
            <span className="text-sky-400">T = 1.85</span>
            <span className="text-slate-600">|</span>
            <span className="text-emerald-400">ECE: 0.048</span>
          </div>

          {/* Quick Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <a
              href="#workbench"
              className="px-2.5 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-sans text-xs font-medium"
            >
              Workbench
            </a>
            <a
              href="#pipeline"
              className="px-2.5 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-sans text-xs font-medium hidden md:block"
            >
              Pipeline
            </a>
            <a
              href="#forensics"
              className="px-2.5 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-sans text-xs font-medium hidden md:block"
            >
              Forensics
            </a>
            <a
              href="#benchmarks"
              className="px-2.5 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-sans text-xs font-medium"
            >
              Benchmarks
            </a>
            <a
              href="#glossary"
              className="px-2.5 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors font-sans text-xs font-medium hidden lg:block"
            >
              Glossary
            </a>
            <a
              href="/api/v1/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-sans text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
            >
              <span>Swagger API</span>
              <span className="text-[10px]">↗</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};
