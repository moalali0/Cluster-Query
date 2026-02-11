import { useState } from "react";
import { AUTH_ENABLED, isAuthenticated, getAuthHeaders, logout } from "./auth";
import LoginPage from "./components/LoginPage";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function formatJson(value) {
  if (!value) return "-";
  return JSON.stringify(value, null, 2);
}

function parseEventBlock(block) {
  const lines = block.split("\n");
  let event = "message";
  let dataText = "";
  for (const line of lines) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataText += line.slice(5).trim();
  }
  if (!dataText) return null;
  try {
    return { event, payload: JSON.parse(dataText) };
  } catch {
    return null;
  }
}

/* ── Icons (inline SVG) ── */

function SearchIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
    </svg>
  );
}

function SparklesIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
    </svg>
  );
}

function PulseLoader() {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-400" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-400 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-400 [animation-delay:300ms]" />
    </span>
  );
}

/* ── Result Card ── */

function ResultCard({ item, index }) {
  const [expanded, setExpanded] = useState(false);
  const text = item.text_content || "";
  const shortText = text.length > 200 && !expanded ? `${text.slice(0, 200)}...` : text;
  const score = Number(item.relevance_score);
  const pct = Math.round(score * 100);

  return (
    <article
      id={`cluster-${item.id}`}
      className="group animate-slide-up scroll-mt-24 rounded-xl border border-surface-500/50 bg-surface-200 transition-all hover:border-brand-600/40 hover:shadow-glow"
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "both" }}
    >
      {/* Top accent bar */}
      <div className="h-px bg-gradient-to-r from-transparent via-brand-600/50 to-transparent" />

      <div className="p-5">
        {/* Header row */}
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded bg-brand-600 px-2 py-0.5 font-mono text-[10px] font-medium text-white">
            {item.id.slice(0, 8)}
          </span>
          <span className="rounded border border-brand-800/60 bg-brand-950/40 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-400">
            {item.client_id}
          </span>
          <div className="ml-auto flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-500">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-700 to-brand-400 transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-[10px] font-semibold tabular-nums text-brand-400">{pct}%</span>
            </div>
            <span className="text-[10px] text-surface-800">{item.doc_count ?? 0} docs</span>
          </div>
        </div>

        {/* Clause text */}
        <p className="mb-3 text-[13px] leading-relaxed text-surface-900">{shortText}</p>
        {text.length > 200 && (
          <button
            type="button"
            className="mb-4 text-[11px] font-medium text-brand-500 transition-colors hover:text-brand-400"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? "Collapse" : "Read full clause"}
          </button>
        )}

        {/* Data panels */}
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-brand-900/20 bg-surface-100 p-3">
            <div className="mb-2 flex items-center gap-1.5">
              <div className="h-1.5 w-1.5 rounded-full bg-brand-500" />
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-brand-400">Codified Decision</h3>
            </div>
            <pre className="overflow-x-auto font-mono text-[11px] leading-relaxed text-brand-300">{formatJson(item.codified_data)}</pre>
          </div>
          <div className="rounded-lg border border-surface-500/50 bg-surface-100 p-3">
            <div className="mb-2 flex items-center gap-1.5">
              <div className="h-1.5 w-1.5 rounded-full bg-surface-700" />
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-surface-800">Query History</h3>
            </div>
            <pre className="overflow-x-auto font-mono text-[11px] leading-relaxed text-surface-800">{formatJson(item.query_history)}</pre>
          </div>
        </div>
      </div>
    </article>
  );
}

/* ── AI Chat Panel ── */

function ChatPanel({ answer, citations, evidenceFound, streaming }) {
  if (!answer && citations.length === 0 && !streaming) return null;

  return (
    <section className="animate-fade-in mb-6 overflow-hidden rounded-xl border border-brand-800/30 bg-surface-200 shadow-glow">
      <div className="flex items-center gap-2 border-b border-surface-400 bg-surface-300 px-5 py-3">
        <SparklesIcon />
        <h2 className="text-xs font-semibold uppercase tracking-widest text-brand-400">AI Analysis</h2>
        {streaming && <PulseLoader />}
        <div className="ml-auto">
          <span
            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
              evidenceFound
                ? "bg-brand-950/60 text-brand-400 ring-1 ring-brand-800/40"
                : "bg-surface-400 text-surface-800 ring-1 ring-surface-500"
            }`}
          >
            {evidenceFound ? "Evidence Backed" : "No Evidence"}
          </span>
        </div>
      </div>

      <div className="p-5">
        <p className="whitespace-pre-wrap text-[13px] leading-[1.7] text-surface-900">
          {answer || <span className="text-surface-700">Waiting for response...</span>}
        </p>
      </div>

      {citations.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-t border-surface-400 px-5 py-3">
          <span className="text-[10px] font-medium uppercase tracking-wider text-surface-700">Sources</span>
          {citations.map((clusterId, idx) => (
            <a
              key={clusterId}
              href={`#cluster-${clusterId}`}
              className="rounded border border-brand-800/30 bg-surface-300 px-2 py-0.5 font-mono text-[10px] font-medium text-brand-400 transition-colors hover:border-brand-600/50 hover:bg-surface-400"
            >
              [{idx + 1}] {clusterId.slice(0, 8)}
            </a>
          ))}
        </div>
      )}
    </section>
  );
}

/* ── Main App ── */

export default function App() {
  if (AUTH_ENABLED && !isAuthenticated()) return <LoginPage />;

  const [term, setTerm] = useState("");
  const [attribute, setAttribute] = useState("");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatStreaming, setChatStreaming] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [results, setResults] = useState([]);
  const [chatAnswer, setChatAnswer] = useState("");
  const [chatCitations, setChatCitations] = useState([]);
  const [chatEvidenceFound, setChatEvidenceFound] = useState(false);

  const hasInput = term.trim() || attribute.trim() || language.trim().length >= 2;

  function buildBody(extra = {}) {
    const body = {};
    if (term.trim()) body.term = term.trim();
    if (attribute.trim()) body.attribute = attribute.trim();
    if (language.trim()) body.language = language.trim();
    return { ...body, ...extra };
  }

  async function performSearch() {
    const response = await fetch(`${API_BASE}/api/search/structured`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(buildBody({ top_k: 5 })),
    });
    if (!response.ok) {
      const p = await response.json();
      throw new Error(p.detail || "Search failed");
    }
    const payload = await response.json();
    setResults(payload.results || []);
    setNote(payload.note || "");
    return payload;
  }

  async function streamChat() {
    setChatStreaming(true);
    setChatAnswer("");
    setChatCitations([]);
    setChatEvidenceFound(false);

    const response = await fetch(`${API_BASE}/api/chat/structured/stream`, {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(buildBody()),
    });

    if (!response.ok || !response.body) {
      const p = await response.json().catch(() => ({}));
      throw new Error(p.detail || "Streaming chat failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        const parsed = parseEventBlock(block);
        if (!parsed) continue;
        if (parsed.event === "meta") setChatEvidenceFound(Boolean(parsed.payload.evidence_found));
        if (parsed.event === "token") setChatAnswer((prev) => prev + (parsed.payload.token || ""));
        if (parsed.event === "error") setChatAnswer((prev) => prev + `\n[LLM Error: ${parsed.payload.message || "unknown"}]\n`);
        if (parsed.event === "done") {
          setChatCitations(Array.isArray(parsed.payload.citations) ? parsed.payload.citations : []);
          setChatEvidenceFound(Boolean(parsed.payload.evidence_found));
        }
      }
    }

    if (buffer.trim()) {
      const parsed = parseEventBlock(buffer.trim());
      if (parsed?.event === "done") {
        setChatCitations(Array.isArray(parsed.payload.citations) ? parsed.payload.citations : []);
        setChatEvidenceFound(Boolean(parsed.payload.evidence_found));
      }
    }

    setChatStreaming(false);
  }

  async function runSearch(evt) {
    evt.preventDefault();
    setLoading(true);
    setError("");
    try {
      await performSearch();
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function runAskStream() {
    if (!hasInput) return;
    setLoading(true);
    setError("");
    try {
      await performSearch();
      await streamChat();
    } catch (err) {
      setError(err.message || "Unexpected error");
      setChatStreaming(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-50">
      {/* ── Top Nav ── */}
      <header className="sticky top-0 z-50 border-b border-surface-400/80 bg-surface-100/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <span className="text-sm font-bold text-white">C</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white">Contract Precedent AI</h1>
              <p className="text-[10px] text-surface-800">Clause Intelligence Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-1.5 rounded-full border border-surface-500 bg-surface-300 px-3 py-1 sm:flex">
              <div className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse-slow" />
              <span className="text-[10px] font-medium text-surface-900">All Bank Streams</span>
            </div>
            {AUTH_ENABLED ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-full border border-surface-500 bg-surface-300 px-3 py-1 text-[10px] font-medium text-surface-800 transition-colors hover:border-brand-600/40 hover:text-brand-400"
              >
                Sign out
              </button>
            ) : (
              <div className="rounded-full border border-surface-500 bg-surface-300 px-3 py-1">
                <span className="text-[10px] font-medium text-surface-800">demo-analyst</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="mx-auto max-w-7xl px-4 py-6 md:px-8">

        {/* ── Search Form ── */}
        <form onSubmit={runSearch} className="mb-8">
          <div className="overflow-hidden rounded-xl border border-surface-400 bg-surface-200 shadow-card">
            {/* Form header */}
            <div className="border-b border-surface-400 bg-surface-300 px-5 py-3">
              <h2 className="text-[11px] font-semibold uppercase tracking-widest text-brand-400">Structured Query</h2>
            </div>

            {/* Fields */}
            <div className="grid gap-px bg-surface-400 md:grid-cols-3">
              <div className="bg-surface-200 p-4">
                <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-widest text-surface-800">Term</label>
                <input
                  type="text"
                  placeholder="Governing Law"
                  className="h-10 w-full rounded-lg border border-surface-500 bg-surface-100 px-3 text-sm font-medium text-white placeholder-surface-700 outline-none transition-all focus:border-brand-600 focus:ring-1 focus:ring-brand-600/30"
                  value={term}
                  onChange={(e) => setTerm(e.target.value)}
                />
              </div>
              <div className="bg-surface-200 p-4">
                <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-widest text-surface-800">Attribute</label>
                <input
                  type="text"
                  placeholder="Jurisdiction"
                  className="h-10 w-full rounded-lg border border-surface-500 bg-surface-100 px-3 text-sm font-medium text-white placeholder-surface-700 outline-none transition-all focus:border-brand-600 focus:ring-1 focus:ring-brand-600/30"
                  value={attribute}
                  onChange={(e) => setAttribute(e.target.value)}
                />
              </div>
              <div className="bg-surface-200 p-4">
                <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-widest text-surface-800">Language</label>
                <input
                  type="text"
                  placeholder="governed by laws of England"
                  className="h-10 w-full rounded-lg border border-surface-500 bg-surface-100 px-3 text-sm font-medium text-white placeholder-surface-700 outline-none transition-all focus:border-brand-600 focus:ring-1 focus:ring-brand-600/30"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                />
              </div>
            </div>

            {/* Action bar */}
            <div className="flex items-center gap-3 border-t border-surface-400 bg-surface-300 px-5 py-3">
              <button
                type="submit"
                className="inline-flex h-9 items-center gap-2 rounded-lg border border-surface-600 bg-surface-400 px-4 text-xs font-semibold text-surface-900 transition-all hover:border-surface-700 hover:bg-surface-500 disabled:opacity-30"
                disabled={loading || chatStreaming || !hasInput}
              >
                <SearchIcon />
                {loading && !chatStreaming ? "Searching..." : "Search"}
              </button>
              <button
                type="button"
                onClick={runAskStream}
                className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand-600 px-4 text-xs font-semibold text-white transition-all hover:bg-brand-500 hover:shadow-glow disabled:opacity-30"
                disabled={loading || chatStreaming || !hasInput}
              >
                <SparklesIcon />
                {chatStreaming ? "Streaming..." : "Ask AI"}
              </button>
              {note && (
                <p className="ml-auto text-[11px] text-surface-800">{note}</p>
              )}
            </div>
          </div>
        </form>

        {/* ── Error ── */}
        {error && (
          <div className="animate-fade-in mb-6 flex items-center gap-2 rounded-lg border border-red-900/40 bg-red-950/20 px-4 py-2.5">
            <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
            <p className="text-xs text-red-400">{error}</p>
          </div>
        )}

        {/* ── AI Chat ── */}
        <ChatPanel
          answer={chatAnswer}
          citations={chatCitations}
          evidenceFound={chatEvidenceFound}
          streaming={chatStreaming}
        />

        {/* ── Results ── */}
        {results.length > 0 && (
          <div className="mb-4 flex items-center gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-surface-800">Precedents</h2>
            <span className="rounded-full bg-surface-400 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-brand-400">
              {results.length}
            </span>
          </div>
        )}

        <section className="grid gap-3">
          {results.map((item, i) => (
            <ResultCard key={item.id} item={item} index={i} />
          ))}
        </section>

        {!loading && !error && results.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-surface-400 bg-surface-200">
              <SearchIcon />
            </div>
            <p className="mb-1 text-sm font-medium text-surface-800">No precedents yet</p>
            <p className="text-xs text-surface-700">Enter a term, attribute, or language to search</p>
          </div>
        )}
      </main>
    </div>
  );
}
