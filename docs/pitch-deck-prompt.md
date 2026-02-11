# Contract Precedent AI — Client Pitch Deck

Generate a professional, modern PowerPoint presentation (16:9) with a dark theme (black/charcoal background, orange accents, white text). Style: fintech, minimal, clean. Use the brand colour #ea580c (orange) for accents, highlights, and key callouts. Sans-serif font (Inter or Helvetica Neue).

---

## Slide 1 — Title

**Contract Precedent AI**
Clause Intelligence Platform

Subtitle: Structured retrieval and AI-powered analysis of contract clause precedents across multi-bank streams.

Small footer: Confidential | [Date] | [Your Firm Name]

---

## Slide 2 — The Problem

Title: **The Challenge**

Three pain points (icon + short description each):

1. **Manual Clause Comparison** — Analysts spend hours cross-referencing clause language across agreements and counterparties. No single source of truth.

2. **Unstructured Knowledge** — Precedent decisions are scattered across emails, spreadsheets, and individual memory. Critical institutional knowledge is at risk.

3. **Inconsistent Codification** — Different teams codify the same clause terms differently. No standardised taxonomy across bank streams.

Bottom callout box (orange border):
> "For a single Governing Law query, an analyst may need to check 15+ agreements across 3 bank streams — a process that takes 2–4 hours today."

---

## Slide 3 — Our Solution

Title: **Contract Precedent AI**

Three pillars (horizontal, icon + heading + 1-liner each):

1. **Structured Search** — Query by Term, Attribute, and Language across codified JSONB data with sub-second retrieval.

2. **Cross-Bank Intelligence** — Search precedents across all bank streams simultaneously with row-level security ensuring data isolation.

3. **AI-Powered Analysis** — LLM summarises retrieved precedents in natural language, citing cluster IDs and highlighting cross-bank patterns.

---

## Slide 4 — User Experience

Title: **How It Works — User View**

**[PLACEHOLDER: Figma Diagram — User Flow]**
*(Full-width placeholder for Figma embed/screenshot showing: 3-field search form → results cards → AI streaming answer with citations)*

Dimensions: ~80% of slide width, centered.

Caption below diagram: "Analysts query by structured fields (Term, Attribute, Language) and receive both raw precedent data and an AI-generated summary with cited evidence."

---

## Slide 5 — Technical Architecture

Title: **System Architecture**

**[PLACEHOLDER: Figma Diagram — Technical Architecture]**
*(Full-width placeholder for Figma embed/screenshot showing: Frontend → FastAPI Backend → PostgreSQL/pgvector + Ollama/Llama → SSE streaming response)*

Dimensions: ~80% of slide width, centered.

Caption below diagram: "Containerised stack with row-level security, vector similarity search, and local LLM inference via Ollama — no data leaves the infrastructure."

---

## Slide 6 — Structured Retrieval Deep Dive

Title: **Intelligent Query Engine**

Left column — **JSONB Filtering**:
- Term-level key existence (`"Governing Law"`)
- Nested attribute matching (`"Jurisdiction"`, `"Exclusive"`)
- Case-insensitive matching across all keys
- GIN-indexed for sub-millisecond lookups

Right column — **Vector Similarity**:
- Embedding-based semantic search on clause language
- Cosine similarity scoring with configurable threshold
- Combined with JSONB filters for precision + recall
- Results ranked by relevance across all bank streams

Bottom stat bar (4 metrics in orange boxes):
| 18 Clusters | 3 Bank Streams | <50ms Query Time | 384-dim Embeddings |

---

## Slide 7 — AI Analysis Layer

Title: **LLM-Powered Summarisation**

Left side — bullet points:
- Powered by Llama 3.2 (local) / Llama 3 8B Instruct (production)
- Runs entirely on-premises via Ollama — **zero data exfiltration**
- Streaming response via Server-Sent Events (SSE)
- System prompt constrains output to retrieved evidence only
- Cites cluster IDs and highlights cross-bank differences
- Graceful fallback to template answers if LLM unavailable

Right side — example output box (dark card, monospace-style):
```
Based on the retrieved precedents:

• English Law is the dominant jurisdiction across Bank_A
  and Bank_C clusters [7a4638ab] [4f69faca]
• Bank_B shows preference for New York Law in ISDA
  agreements [c133f827] and French Law in CSA agreements
  [f7f2b230]
• Exclusive jurisdiction is specified in 12 of 18 clusters
• Process agents vary: Maples & Calder (Ireland),
  Law Society of Scotland, Allen & Gledhill (Singapore)
```

---

## Slide 8 — Security & Compliance

Title: **Enterprise-Grade Security**

Four quadrants:

1. **Row-Level Security** — PostgreSQL RLS policies enforce client-level data isolation. No cross-contamination between bank streams.

2. **On-Premises LLM** — Llama runs locally via Ollama. No API calls to external AI services. All inference happens within your infrastructure.

3. **Role-Based Access** — Separate database roles for application (read-only) and ingestion (write). Audit logging on every query.

4. **Audit Trail** — Every search and AI interaction is logged with user ID, query text, result count, relevance scores, and response time.

---

## Slide 9 — Deployment Options

Title: **Flexible Deployment**

Two columns:

**Local Development**
- Docker Compose (3 containers)
- Ollama with Llama 3.2 (3B params)
- pgvector on PostgreSQL 16
- Hot-reload frontend (Vite)
- Single `docker compose up` to start

**Production (AWS)**
- g4dn.xlarge (T4 GPU) for Llama 3 8B Instruct
- RDS PostgreSQL with pgvector extension
- ECS/Fargate for backend + frontend
- ALB with TLS termination
- CloudWatch monitoring + alerts

Bottom note: "Toggle between local and production LLM models with a single environment variable (`OLLAMA_MODEL`)."

---

## Slide 10 — Data Model

Title: **Codification Schema**

Show a simplified representation:

```
mock_codification.csv
├── Cluster ID    → Groups related datapoints
├── Tags          → Bank stream + agreement type (Bank_A;ISDA;2002)
├── Term          → Top-level category (Governing Law)
├── Attribute     → Specific field (Jurisdiction, Exclusive, Court)
├── Value         → Codified answer (English Law, Yes, Paris Court of Appeal)
└── Text          → Original clause language
```

Arrow pointing to:

```
clusters table (PostgreSQL)
├── codified_data  → {"Governing Law": {"Jurisdiction": "English Law", "Exclusive": "Yes"}}
├── text_content   → Full clause text
├── embedding      → 384-dim vector for semantic search
└── query_history  → Analyst/client dialogue trail
```

---

## Slide 11 — Roadmap

Title: **What's Next**

Timeline (horizontal, left to right):

**Phase 0 (Current)** — Structured search + AI chatbot. Hash-based embeddings. 18 clusters, 3 banks. Local Ollama inference.

**Phase 1** — Production embeddings (sentence-transformers). Expanded dataset (500+ clusters). User authentication + RBAC. Feedback loop on AI answers.

**Phase 2** — Multi-term search (Governing Law + Netting + Credit Support). Auto-codification suggestions from raw clause text. Comparison view across jurisdictions.

**Phase 3** — Full negotiation assistant. Draft clause suggestions based on precedent. Anomaly detection for non-standard terms. Integration with document management systems.

---

## Slide 12 — Demo & Next Steps

Title: **See It In Action**

Center content:

Live demo available at: `http://localhost:5173`

Three next steps (numbered, orange circles):

1. **Try it** — We'll walk through a live search for "Governing Law" precedents across all bank streams.

2. **Your data** — Provide a sample codification export and we'll ingest it within 24 hours.

3. **Pilot scope** — Define 2-3 priority clause terms and a target bank stream for a 4-week proof of concept.

Bottom contact bar:
[Your Name] | [Email] | [Your Firm Name]

---

## Design Notes for Generator

- All slides: black (#0a0a0a) background, white (#f5f5f5) body text, orange (#ea580c / #f97316) accents
- Slide numbers in bottom-right, small, orange
- No clip art — use simple line icons (Heroicons style) if needed
- Code/data examples in monospace font on slightly lighter dark cards (#141414)
- Minimal text per slide — favour visuals and whitespace
- Slides 4 and 5 should have large, clearly labelled placeholder boxes for Figma diagrams
- Consistent 80px left/right padding feel
- Title text: 28-32pt bold, white. Body: 14-16pt, light gray (#d4d4d4). Labels: 10-11pt uppercase tracking-wide, orange.
