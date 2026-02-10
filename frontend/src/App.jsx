import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USER_ID = "demo-analyst";

function formatJson(value) {
  if (!value) return "-";
  return JSON.stringify(value, null, 2);
}

function parseEventBlock(block) {
  const lines = block.split("\n");
  let event = "message";
  let dataText = "";

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataText += line.slice(5).trim();
    }
  }

  if (!dataText) return null;
  try {
    return { event, payload: JSON.parse(dataText) };
  } catch {
    return null;
  }
}

function ResultCard({ item }) {
  const [expanded, setExpanded] = useState(false);
  const text = item.text_content || "";
  const shortText = text.length > 220 && !expanded ? `${text.slice(0, 220)}...` : text;

  return (
    <article id={`cluster-${item.id}`} className="scroll-mt-24 rounded-2xl border border-slate-200 bg-panel p-5 shadow-card">
      <header className="mb-3 flex flex-wrap items-center gap-3">
        <span className="rounded-md bg-slate-900 px-2 py-1 text-xs font-semibold text-white">{item.id}</span>
        <span className="rounded-md bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-900">{item.client_id}</span>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium">
          Relevance {Number(item.relevance_score).toFixed(3)}
        </span>
        <span className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-900">
          Used in {item.doc_count ?? 0} Docs
        </span>
      </header>

      <p className="mb-2 text-sm leading-relaxed text-slate-800">{shortText}</p>
      {text.length > 220 ? (
        <button
          type="button"
          className="mb-4 text-xs font-semibold text-slate-600 underline"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
          <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-emerald-900">Decision</h3>
          <pre className="overflow-x-auto text-xs text-emerald-900">{formatJson(item.codified_data)}</pre>
        </section>

        <section className="rounded-xl border border-amber-200 bg-amber-50 p-3">
          <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-amber-900">Context (Query History)</h3>
          <pre className="overflow-x-auto text-xs text-amber-900">{formatJson(item.query_history)}</pre>
        </section>
      </div>
    </article>
  );
}

function ChatPanel({ answer, citations, evidenceFound }) {
  if (!answer && citations.length === 0) return null;

  return (
    <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
      <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-700">Streaming Answer</h2>
      <p className="mb-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-800">{answer || "..."}</p>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span
          className={`rounded px-2 py-1 font-semibold ${
            evidenceFound ? "bg-emerald-100 text-emerald-900" : "bg-amber-100 text-amber-900"
          }`}
        >
          {evidenceFound ? "Evidence Found" : "Insufficient Evidence"}
        </span>

        {citations.map((clusterId, idx) => (
          <a
            key={clusterId}
            href={`#cluster-${clusterId}`}
            className="rounded bg-slate-100 px-2 py-1 font-semibold text-slate-700 hover:bg-slate-200"
          >
            [{idx + 1}] {clusterId.slice(0, 8)}
          </a>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatStreaming, setChatStreaming] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [results, setResults] = useState([]);
  const [chatAnswer, setChatAnswer] = useState("");
  const [chatCitations, setChatCitations] = useState([]);
  const [chatEvidenceFound, setChatEvidenceFound] = useState(false);

  async function performSearch(activeQuery) {
    const response = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-user-id": USER_ID,
      },
      body: JSON.stringify({ query: activeQuery, top_k: 5 }),
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || "Search failed");
    }

    const payload = await response.json();
    setResults(payload.results || []);
    setNote(payload.note || "");
    return payload;
  }

  async function streamChat(activeQuery) {
    setChatStreaming(true);
    setChatAnswer("");
    setChatCitations([]);
    setChatEvidenceFound(false);

    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-user-id": USER_ID,
      },
      body: JSON.stringify({ query: activeQuery }),
    });

    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Streaming chat failed");
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

        if (parsed.event === "meta") {
          setChatEvidenceFound(Boolean(parsed.payload.evidence_found));
        }

        if (parsed.event === "token") {
          setChatAnswer((prev) => prev + (parsed.payload.token || ""));
        }

        if (parsed.event === "done") {
          setChatCitations(Array.isArray(parsed.payload.citations) ? parsed.payload.citations : []);
          setChatEvidenceFound(Boolean(parsed.payload.evidence_found));
        }
      }
    }

    if (buffer.trim().length > 0) {
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
      await performSearch(query.trim());
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function runAskStream() {
    if (query.trim().length < 2) return;

    setLoading(true);
    setError("");

    try {
      await performSearch(query.trim());
      await streamChat(query.trim());
    } catch (err) {
      setError(err.message || "Unexpected error");
      setChatStreaming(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 md:px-8">
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold tracking-tight text-ink md:text-2xl">Contract Precedent Search</h1>
        <span className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700">
          Scope: All Bank Streams
        </span>
      </div>

      <form onSubmit={runSearch} className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            type="text"
            placeholder="Ask: How was Governing Law treated for similar text?"
            className="h-12 flex-1 rounded-xl border border-slate-300 px-4 text-sm outline-none ring-slate-200 focus:ring"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
          />
          <button
            type="submit"
            className="h-12 rounded-xl bg-slate-900 px-5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60"
            disabled={loading || chatStreaming || query.trim().length < 2}
          >
            {loading && !chatStreaming ? "Searching..." : "Search"}
          </button>
          <button
            type="button"
            onClick={runAskStream}
            className="h-12 rounded-xl bg-teal-700 px-5 text-sm font-semibold text-white transition hover:bg-teal-600 disabled:opacity-60"
            disabled={loading || chatStreaming || query.trim().length < 2}
          >
            {chatStreaming ? "Streaming..." : "Ask (Stream)"}
          </button>
        </div>
      </form>

      {note ? <p className="mb-4 text-sm text-slate-700">{note}</p> : null}
      {error ? <p className="mb-4 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <ChatPanel answer={chatAnswer} citations={chatCitations} evidenceFound={chatEvidenceFound} />

      <section className="grid gap-4">
        {results.map((item) => (
          <ResultCard key={item.id} item={item} />
        ))}
        {!loading && !error && results.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-400 bg-white/60 p-8 text-center text-sm text-slate-600">
            No precedents displayed yet. Run a search.
          </div>
        ) : null}
      </section>
    </div>
  );
}
