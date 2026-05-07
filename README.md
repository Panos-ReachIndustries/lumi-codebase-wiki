# Lumi Codebase Wiki

A lightweight onboarding companion for the three Lumi repos:

| Repo | What it is |
|------|-----------|
| **Lumi-AI-Continuous** | Python + Go backend — monitors, protocol arbiters, Kafka orchestration |
| **Lumi-AI-Core** | Reusable V2 AI/CV modules (detection, tracking, segmentation, …) |
| **lumi-web-v2** | Next.js web app — experiment dashboard, AI Assist, protocol viewer |

The app is a static site: an interactive **cross-repo knowledge graph**, a **markdown wiki** (90+ pages, all source-backed), and a **Gemini-powered chat** that answers questions about the codebase. No build step, no backend — just a Python file server.

---

## Prerequisites

- Python 3.9+
- The three repos cloned as siblings of this folder:

```
AI_Tooling_workshop/
├── Lumi-AI-Continuous/
├── Lumi-AI-Core/
├── lumi-web-v2/
└── lumi-codebase-wiki/   ← you are here
```

---

## Running the app

### 1. Install dependencies

```bash
pip install -r tools/requirements.txt   # just PyYAML
```

### 2. Build the graph data

```bash
./scripts/rebuild-all.sh
```

This runs four steps in order and prints what it found:

| Step | Script | Output |
|------|--------|--------|
| Structural graph | `tools/build_graph.py` | `app/data/graph.json` — 107 nodes, 77 edges |
| TF-IDF similarity | `tools/build_similarity.py` | `app/data/similarity.json` — 114 similarity edges |
| Wiki index | `tools/build_index.py` | `app/data/wiki-index.json` + `wiki/index.md` |
| Health check | `tools/lint_wiki.py` | Orphan/broken-link report (should say "Wiki is clean.") |

> The generated files in `app/data/` are gitignored. Re-run `rebuild-all.sh` after pulling new repo changes.

### 3. Serve

```bash
./scripts/serve.sh
```

Open **http://localhost:8000/app/** in your browser.

To use a different port:

```bash
PORT=9000 ./scripts/serve.sh
```

### 4. Enable Chat (optional)

The Chat page calls the Gemini API from the browser. Each user provides their own key — nothing is stored server-side.

```bash
cp app/config.example.js app/config.js
# open app/config.js and replace PASTE_YOUR_GEMINI_API_KEY_HERE
# get a key at: https://aistudio.google.com/apikey
```

`app/config.js` is gitignored. The default model is `gemini-2.5-flash` — the entire wiki (~70 k tokens) is sent as context on every turn. Gemini's prompt cache kicks in after turn 1, so follow-up questions are cheap.

---

## What's where

```
lumi-codebase-wiki/
├── app/                   Static viewer (HTML + Cytoscape.js + marked.js + Fuse.js)
│   ├── index.html         Landing page — overview, tour cards, search
│   ├── graph.html         Interactive knowledge graph
│   ├── wiki.html          Markdown reader with sidebar TOC
│   ├── chat.html          Gemini-powered Q&A
│   ├── config.example.js  Template for your Gemini key (copy → config.js)
│   └── data/              Generated JSON (gitignored — rebuilt by scripts)
├── wiki/                  90+ markdown pages — one per repo component
│   ├── overview.md        Start here
│   ├── tour/              day-1 / week-1 / month-1 onboarding paths
│   ├── architecture/      System overview, Kafka topics, repos, deployment
│   ├── ai-continuous/     Monitors, arbiters, monitor-relay, common utils
│   ├── ai-core/           V2 modules + agreed data schema
│   ├── web/               Routes, API domains, Kubb pipeline, components
│   └── concepts/          Monitor, arbiter, protocol, ledger, custom-agent
├── tools/                 Python build scripts
│   ├── build_graph.py     Walks 3 repos → graph.json
│   ├── build_similarity.py  TF-IDF cosine → similarity.json
│   ├── build_index.py     Reads wiki frontmatter → wiki-index.json
│   ├── lint_wiki.py       Orphan/broken-link checker
│   └── merge_relations.py Validates LLM-extracted typed triples → relations.json
├── scripts/
│   ├── rebuild-all.sh     Runs all four build steps in order
│   └── serve.sh           python -m http.server wrapper
└── CLAUDE.md              Wiki conventions — read this before editing any page
```

---

## The graph layers

The graph has three independently toggleable layers (sidebar → Layers):

| Layer | What it shows | How it's built |
|-------|---------------|----------------|
| **Structural** (on by default) | Imports, Kafka pubsub, API contracts, route↔API↔backend bridges | AST + regex walk of all three repos |
| **Similarity** | Pages that talk about the same things — no embeddings, pure TF-IDF cosine mutual top-K | `build_similarity.py` |
| **Relations** | Typed triples: `colour PUBLISHES_TO MONITOR_DATA_TOPIC`, `arbiter:v2 ALTERNATIVE_TO arbiter:v1`, … | LLM-extracted, validated by `merge_relations.py` |

**Graph interactions:**

- **Click** a node → wiki page loads in the side panel
- **Focus 2-hop ⬡** (button in side panel) → hides everything outside 2 connections; sidebar gets a reset button
- **Similarity edges** auto-hide when zoomed out; reappear when zoomed in
- **Relations edge labels** appear on hover only
- Node **size** scales with number of connections (high-degree hubs are visually larger)
- Filter chips in the sidebar toggle by repo, node type, or edge kind

---

## Maintaining the wiki

The wiki follows the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern — Claude writes and revises pages, humans read. See `CLAUDE.md` for page format, naming conventions, and the ingest/lint workflows.

**Adding a page:**

```bash
# 1. Write wiki/your-section/page-name.md with correct frontmatter (see CLAUDE.md)
# 2. Rebuild the index so the sidebar picks it up
python tools/build_index.py
# 3. Optional: re-run the graph if you added a new node-worthy entity
python tools/build_graph.py
```

**Adding relations triples:**

```bash
# Ask Claude to extract triples from a wiki page, save to a file, then:
python tools/merge_relations.py --in extracted.json
# Invalid triples (unknown node IDs, bad predicates, self-loops) are rejected with reasons.
```

Allowed predicates: `USES`, `COMPOSES`, `PUBLISHES_TO`, `SUBSCRIBES_TO`, `DEPENDS_ON`, `IS_A_KIND_OF`, `EXAMPLE_OF`, `ALTERNATIVE_TO`, `MAINTAINED_BY`, `DOCUMENTED_BY`, `REFERENCED_BY`.

---

## Why no embeddings?

TF-IDF + LLM-typed triples gives ~95% of the value of a vector knowledge graph for a single-domain, English-only wiki at this scale — with zero infra and zero API cost for the similarity layer. Embeddings buy synonym tolerance and cross-language semantics; neither matters much for a 100-page onboarding wiki with a small controlled vocabulary.
