import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
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
    <article id={`cluster-${item.id}`} className="scroll-mt-24 rounded-2xl border border-accent/30 bg-panel p-5 shadow-card">
      <header className="mb-3 flex flex-wrap items-center gap-3">
        <span className="rounded-md bg-accent px-2 py-1 text-xs font-semibold text-black">{item.id}</span>
        <span className="rounded-md border border-accent/40 px-2 py-1 text-xs font-semibold text-accent-light">{item.client_id}</span>
        <span className="rounded-md border border-accent/20 px-2 py-1 text-xs font-medium text-accent-bright">
          Relevance {Number(item.relevance_score).toFixed(3)}
        </span>
        <span className="rounded-md border border-accent/20 px-2 py-1 text-xs font-medium text-accent-bright">
          Used in {item.doc_count ?? 0} Docs
        </span>
      </header>

      <p className="mb-2 text-sm leading-relaxed text-accent-bright">{shortText}</p>
      {text.length > 220 ? (
        <button
          type="button"
          className="mb-4 text-xs font-semibold text-accent underline"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        <section className="rounded-xl border border-accent/30 bg-black/40 p-3">
          <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-accent-light">Decision</h3>
          <pre className="overflow-x-auto text-xs text-accent-bright">{formatJson(item.codified_data)}</pre>
        </section>

        <section className="rounded-xl border border-accent/20 bg-black/40 p-3">
          <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-accent-light">Context (Query History)</h3>
          <pre className="overflow-x-auto text-xs text-accent-bright/70">{formatJson(item.query_history)}</pre>
        </section>
      </div>
    </article>
  );
}

function ChatPanel({ answer, citations, evidenceFound }) {
  if (!answer && citations.length === 0) return null;

  return (
    <section className="mb-6 rounded-2xl border border-accent/30 bg-panel p-4 shadow-card">
      <h2 className="mb-2 text-sm font-bold uppercase tracking-wide text-accent">Streaming Answer</h2>
      <p className="mb-3 whitespace-pre-wrap text-sm leading-relaxed text-accent-bright">{answer || "..."}</p>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span
          className={`rounded px-2 py-1 font-semibold ${
            evidenceFound ? "bg-accent/20 text-accent-light" : "border border-accent/20 text-accent-bright/60"
          }`}
        >
          {evidenceFound ? "Evidence Found" : "Insufficient Evidence"}
        </span>

        {citations.map((clusterId, idx) => (
          <a
            key={clusterId}
            href={`#cluster-${clusterId}`}
            className="rounded border border-accent/30 px-2 py-1 font-semibold text-accent-light hover:bg-accent/20"
          >
            [{idx + 1}] {clusterId.slice(0, 8)}
          </a>
        ))}
      </div>
    </section>
  );
}

export default function App() {
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

  const hasInput = term.trim() || attribute.trim() || (language.trim().length >= 2);

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
      headers: {
        "Content-Type": "application/json",
        "x-user-id": USER_ID,
      },
      body: JSON.stringify(buildBody({ top_k: 5 })),
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

  async function streamChat() {
    setChatStreaming(true);
    setChatAnswer("");
    setChatCitations([]);
    setChatEvidenceFound(false);

    const response = await fetch(`${API_BASE}/api/chat/structured/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-user-id": USER_ID,
      },
      body: JSON.stringify(buildBody()),
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

        if (parsed.event === "error") {
          setChatAnswer((prev) => prev + `\n[LLM Error: ${parsed.payload.message || "unknown"}]\n`);
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
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 md:px-8">
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold tracking-tight text-accent md:text-2xl">Contract Precedent Search</h1>
        <span className="rounded-lg border border-accent/40 bg-panel px-3 py-2 text-sm font-semibold text-accent-light">
          Scope: All Bank Streams
        </span>
      </div>

      <form onSubmit={runSearch} className="mb-6 rounded-2xl border border-accent/30 bg-panel p-4 shadow-card">
        <div className="mb-3 grid gap-3 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-accent">Term</label>
            <input
              type="text"
              placeholder="e.g. Governing Law"
              className="h-12 w-full rounded-xl border border-accent/40 bg-black px-4 text-sm text-accent-light placeholder-accent/30 outline-none ring-accent/40 focus:border-accent focus:ring"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-accent">Attribute</label>
            <input
              type="text"
              placeholder="e.g. Jurisdiction"
              className="h-12 w-full rounded-xl border border-accent/40 bg-black px-4 text-sm text-accent-light placeholder-accent/30 outline-none ring-accent/40 focus:border-accent focus:ring"
              value={attribute}
              onChange={(e) => setAttribute(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-accent">Language</label>
            <input
              type="text"
              placeholder="e.g. governed by laws of England"
              className="h-12 w-full rounded-xl border border-accent/40 bg-black px-4 text-sm text-accent-light placeholder-accent/30 outline-none ring-accent/40 focus:border-accent focus:ring"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            className="h-12 rounded-xl border border-accent/50 bg-black px-5 text-sm font-semibold text-accent-light transition hover:bg-accent/10 disabled:opacity-40"
            disabled={loading || chatStreaming || !hasInput}
          >
            {loading && !chatStreaming ? "Searching..." : "Search"}
          </button>
          <button
            type="button"
            onClick={runAskStream}
            className="h-12 rounded-xl bg-accent px-5 text-sm font-semibold text-black transition hover:bg-accent-light disabled:opacity-40"
            disabled={loading || chatStreaming || !hasInput}
          >
            {chatStreaming ? "Streaming..." : "Ask AI (Stream)"}
          </button>
        </div>
      </form>

      {note ? <p className="mb-4 text-sm text-accent-bright">{note}</p> : null}
      {error ? <p className="mb-4 rounded-lg border border-red-700/50 bg-red-950/30 px-3 py-2 text-sm text-red-400">{error}</p> : null}

      <ChatPanel answer={chatAnswer} citations={chatCitations} evidenceFound={chatEvidenceFound} />

      <section className="grid gap-4">
        {results.map((item) => (
          <ResultCard key={item.id} item={item} />
        ))}
        {!loading && !error && results.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-accent/20 bg-panel/60 p-8 text-center text-sm text-accent/50">
            No precedents displayed yet. Run a search.
          </div>
        ) : null}
      </section>
    </div>
  );
}
