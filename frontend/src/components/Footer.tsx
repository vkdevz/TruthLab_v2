import React, { useState } from 'react';

export const Footer: React.FC = () => {
  const [activeSnippet, setActiveSnippet] = useState<'CURL' | 'PYTHON'>('CURL');

  const curlSnippet = `# Verify an image with ELA and OCR forensics
curl -X POST "http://localhost:1234/api/v1/verify/image" \\
  -H "accept: application/json" \\
  -F "file=@sample_5g_meme.png;type=image/png"`;

  const pythonSnippet = `import httpx

# Async verification of video clip
async with httpx.AsyncClient() as client:
    with open("news_clip.mp4", "rb") as f:
        response = await client.post(
            "http://localhost:1234/api/v1/verify/video",
            files={"file": ("news_clip.mp4", f, "video/mp4")},
            timeout=30.0
        )
    print(response.json()["overall_veracity"])`;

  const bibtexCitation = `@article{truthlab2026multimodal,
  title={Multimodal Evidence-Aware Misinformation Verification with Calibrated Epistemics},
  author={TruthLab Research Team},
  journal={Major Project Defense Dissertation},
  year={2026},
  institution={TruthLab Research Laboratory},
  url={http://localhost:1234}
}`;

  return (
    <footer id="api" className="border-t border-white/10 bg-[#070a0f] py-16 px-6 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* API Snippets & BibTeX */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* API Snippet */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-xs text-slate-300 font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                API Client Invocation
              </div>
              <div className="flex rounded-md bg-black/40 p-1 border border-white/5 font-mono text-[11px]">
                <button
                  onClick={() => setActiveSnippet('CURL')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    activeSnippet === 'CURL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  cURL
                </button>
                <button
                  onClick={() => setActiveSnippet('PYTHON')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    activeSnippet === 'PYTHON' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Python
                </button>
              </div>
            </div>

            <pre className="p-4 rounded-lg bg-black/60 border border-white/5 font-mono text-[11px] text-sky-300 overflow-x-auto leading-relaxed">
              <code>{activeSnippet === 'CURL' ? curlSnippet : pythonSnippet}</code>
            </pre>
            <div className="mt-3 flex items-center justify-between text-[11px] font-mono">
              <span>Interactive Schema:</span>
              <a
                href="/api/v1/docs"
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:text-indigo-300 underline"
              >
                Open OpenAPI / Swagger Docs ↗
              </a>
            </div>
          </div>

          {/* BibTeX Citation */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-xs text-slate-300 font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                Academic Citation (BibTeX)
              </div>
              <span className="font-mono text-[11px] text-slate-500">Dissertation Defense</span>
            </div>

            <pre className="p-4 rounded-lg bg-black/60 border border-white/5 font-mono text-[11px] text-slate-300 overflow-x-auto leading-relaxed">
              <code>{bibtexCitation}</code>
            </pre>
            <div className="mt-3 flex items-center justify-between text-[11px] font-mono">
              <span>Artifacts:</span>
              <span className="text-slate-400">DATASET_AUDIT.md | RESEARCH_TABLES.md</span>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-slate-500">
          <div>
            TruthLab v2.0 • Multimodal Evidence-Aware Misinformation Verification System
          </div>
          <div className="flex items-center gap-4">
            <a href="#workbench" className="hover:text-slate-300 transition-colors">Top ↑</a>
            <span>•</span>
            <a href="/api/v1/health" target="_blank" rel="noreferrer" className="hover:text-slate-300 transition-colors">System Health</a>
            <span>•</span>
            <span className="text-emerald-400">Operational on :1234</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
