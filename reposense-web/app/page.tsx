"use client";

import { useState } from "react";
import { 
  FolderSearch, 
  ShieldAlert, 
  FileCode, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Layers 
} from "lucide-react";

interface ScanData {
  totals: { total_files?: number; total_lines?: number };
  language_summary: Array<{ language: string; file_count: number; total_lines: number }>;
  onboarding: {
    present: string[];
    missing: string[];
    score?: { pct: number };
  };
  security_stats: {
    total_findings: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  security_findings: Array<{
    file: string;
    line: number;
    category: string;
    label: string;
    snippet: string;
  }>;
}

export default function Home() {
  const [repoPath, setRepoPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanData | null>(null);
  const [error, setError] = useState("");

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath.trim() }),
      });

      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.detail || "Scan request failed");
      }
      setResult(json.data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to FastAPI backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Layers className="h-8 w-8 text-indigo-400" />
            <h1 className="text-3xl font-bold tracking-tight">RepoSense AI</h1>
          </div>
          <p className="text-slate-400">
            Developer Onboarding & Code Quality Intelligence Dashboard
          </p>
        </header>

        {/* Input Bar */}
        <form onSubmit={handleScan} className="flex gap-3">
          <div className="relative flex-1">
            <FolderSearch className="absolute left-3.5 top-3.5 h-5 w-5 text-slate-500" />
            <input
              type="text"
              placeholder="Enter local repository absolute path (e.g. C:/Users/.../kisan-dost)"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-11 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-6 py-3 rounded-lg flex items-center gap-2 transition"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Scan"}
          </button>
        </form>

        {/* Error Notification */}
        {error && (
          <div className="p-4 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Scan Results View */}
        {result && (
          <div className="space-y-6">
            
            {/* Overview Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Files</span>
                <p className="text-2xl font-bold mt-1">{result.totals?.total_files || 0}</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Lines of Code</span>
                <p className="text-2xl font-bold mt-1">{result.totals?.total_lines || 0}</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Security / Quality Findings</span>
                <p className="text-2xl font-bold mt-1 text-amber-400">
                  {result.security_stats?.total_findings || 0}
                </p>
              </div>
            </div>

            {/* Language Breakdown & Onboarding Check */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Languages */}
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <FileCode className="h-5 w-5 text-indigo-400" />
                  Ecosystem & Languages
                </h3>
                <div className="space-y-3">
                  {result.language_summary?.map((lang, idx) => (
                    <div key={idx} className="flex justify-between items-center text-sm border-b border-slate-800 pb-2">
                      <span className="font-medium">{lang.language}</span>
                      <span className="text-slate-400">{lang.file_count} files ({lang.total_lines} lines)</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Onboarding Essential Files */}
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  Onboarding Checklist
                </h3>
                <div className="space-y-2">
                  {result.onboarding?.present?.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm text-emerald-300">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>{item}</span>
                    </div>
                  ))}
                  {result.onboarding?.missing?.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm text-rose-400">
                      <XCircle className="h-4 w-4" />
                      <span>Missing: {item}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Findings & Code Smells */}
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-amber-400" />
                Detected Code Smells & Security Checks
              </h3>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {result.security_findings?.length === 0 ? (
                  <p className="text-sm text-slate-500">No issues detected. Code is clean!</p>
                ) : (
                  result.security_findings?.map((finding, idx) => (
                    <div key={idx} className="p-3 bg-slate-950 rounded border border-slate-800 text-sm space-y-1">
                      <div className="flex justify-between">
                        <span className="font-medium text-indigo-300">{finding.label}</span>
                        <span className="text-xs text-slate-500">Line {finding.line}</span>
                      </div>
                      <p className="text-xs text-slate-400 truncate">{finding.file}</p>
                      <pre className="bg-slate-900 p-2 rounded text-xs text-amber-300 overflow-x-auto mt-1">
                        {finding.snippet}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>
        )}

      </div>
    </main>
  );
}
