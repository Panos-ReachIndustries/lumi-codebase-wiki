# Lumi Codebase Wiki

Built by Panos and Aaron through a shared brainstorming and planning effort, with each contributing complementary strengths to the mini-project:

Aaron focused on the foundational approach and initial solution design through [onboarding_buddy_ai_tooling_exercise](https://github.com/Reach-Industries/onboarding_buddy_ai_tooling_exercise)
Panos then used, expanded and evolved that foundation into this repository, using Aaron’s implementation as a stepping stone/backbone while driving the UI design, application serving layer, graph viewer, wiki reader, chat interface, and overall static-site experience.

---

A lightweight onboarding companion for the three Lumi repos:

| Repo | What it is |
|------|-----------|
| **Lumi-AI-Continuous** | Python + Go backend — monitors, protocol arbiters, Kafka orchestration |
| **Lumi-AI-Core** | Reusable V2 AI/CV modules (detection, tracking, segmentation, …) |
| **lumi-web-v2** | Next.js web app — experiment dashboard, AI Assist, protocol viewer |

The app is a static site: an interactive **cross-repo knowledge graph**, a **markdown wiki** (90+ pages, all source-backed), and a **Gemini-powered chat** that answers questions about the codebase. No build step, no backend — just a Python file server.

---

## Getting started

### Step 0 — Folder layout

This repo must sit next to the three Lumi repos:

```
AI_Tooling_workshop/
├── Lumi-AI-Continuous/      ← must exist
├── Lumi-AI-Core/            ← must exist
├── lumi-web-v2/             ← must exist
└── lumi-codebase-wiki/      ← you are here
```

If any of the three repos is missing the build scripts will warn you (they do not crash — the missing repo simply produces no nodes).

### Step 1 — Install Python dependencies

```bash
# From inside lumi-codebase-wiki/
pip install -r tools/requirements.txt
```

Only `PyYAML` is required. Python 3.9+ works.

### Step 2 — Build the data files

The graph, similarity, and search index are generated from the live repo state and are **not committed** (they live in `app/data/` which is gitignored). You must generate them at least once before opening the app.

```bash
./scripts/rebuild-all.sh
```

Expected output:

```
→ build_graph.py
Wrote app/data/graph.json: 107 nodes, 77 edges

→ build_similarity.py
Computed 114 mutual top-4 similarity edges (min score 0.1).
  → app/data/similarity.json

→ build_index.py
Indexed 89 pages. 0 missing frontmatter.
  → wiki/index.md
  → app/data/wiki-index.json

→ lint_wiki.py
Wiki is clean.
```

Re-run `rebuild-all.sh` any time you pull changes to the three repos.

### Step 3 — Start the server

```bash
./scripts/serve.sh
```

Then open **[http://localhost:8000/app/](http://localhost:8000/app/)** in your browser.

To use a different port:

```bash
PORT=9000 ./scripts/serve.sh
```

The server is just `python3 -m http.server` — it has no state and no API. Stopping it with Ctrl-C is safe.

### Step 4 — Enable Chat (optional)

The Chat tab requires a Gemini API key. Each person provides their own — nothing is stored server-side.

```bash
cp app/config.example.js app/config.js
```

Open `app/config.js` and replace `PASTE_YOUR_GEMINI_API_KEY_HERE` with a real key. Get one free at **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.

```js
window.LUMI_GEMINI = {
  apiKey: "AIza...",            // ← your key
  model:  "gemini-2.5-flash",   // or "gemini-2.5-pro" for heavier reasoning
  temperature: 0.4,
  maxOutputTokens: 4096,
};
```

`app/config.js` is gitignored so your key is never committed. The entire wiki (~70 k tokens) is sent as context on every turn; Gemini's prompt cache discounts it after the first message, making follow-ups cheap.

---

## Full run summary (copy-paste)

```bash
# One-time setup
pip install -r tools/requirements.txt
cp app/config.example.js app/config.js   # then paste your Gemini key

# Every time (after cloning, or after pulling repo changes)
./scripts/rebuild-all.sh

# Start the app
./scripts/serve.sh
# → open http://localhost:8000/app/
```

---

## What's where

```
lumi-codebase-wiki/
├── app/                    Static viewer (Cytoscape.js + marked.js + Fuse.js)
│   ├── index.html          Landing page — overview + tour cards
│   ├── graph.html          Interactive knowledge graph
│   ├── wiki.html           Markdown reader with sidebar TOC
│   ├── chat.html           Gemini-powered Q&A
│   ├── config.example.js   Template — copy to config.js and add your key
│   └── data/               Generated JSON files (gitignored)
│       ├── graph.json       Structural graph (nodes + edges)
│       ├── similarity.json  TF-IDF cosine edges
│       ├── relations.json   LLM-extracted typed triples (committed)
│       └── wiki-index.json  Search index
├── wiki/                   90+ markdown pages
│   ├── overview.md         Start here — what is Lumi in 200 words
│   ├── tour/               day-1 / week-1 / month-1 reading paths
│   ├── architecture/       System overview, Kafka topics, repos, deployment
│   ├── ai-continuous/      Monitors, arbiters, monitor-relay, common utils
│   ├── ai-core/            V2 modules + agreed data schema
│   ├── web/                Routes, API domains, Kubb pipeline, components
│   └── concepts/           Monitor, arbiter, protocol, ledger, custom-agent
├── tools/
│   ├── build_graph.py      Walks 3 repos → graph.json
│   ├── build_similarity.py TF-IDF cosine → similarity.json
│   ├── build_index.py      Reads wiki frontmatter → wiki-index.json + index.md
│   ├── lint_wiki.py        Orphan/broken-link checker
│   └── merge_relations.py  Validates LLM-extracted triples → relations.json
├── scripts/
│   ├── rebuild-all.sh      Runs all four build steps in order
│   └── serve.sh            python -m http.server wrapper (respects $PORT)
└── CLAUDE.md               Wiki schema — read before editing any page
```

---

## Using the graph

The graph has three independently toggleable layers (sidebar → **Layers**):

| Layer | What it shows | How it's built |
|-------|---------------|----------------|
| **Structural** (default on) | Imports, Kafka pubsub, API contracts, route↔backend bridges | AST + regex walk of all three repos |
| **Similarity** | Components that talk about the same things (no embeddings — pure TF-IDF) | `build_similarity.py` |
| **Relations** | Typed triples: `colour PUBLISHES_TO MONITOR_DATA_TOPIC`, `arbiter:v2 ALTERNATIVE_TO arbiter:v1`, … | LLM-extracted, validated by `merge_relations.py` |

**Interactions:**

| Action | Effect |
|--------|--------|
| Click a node | Wiki page appears in the right panel |
| Click **Focus 2-hop ⬡** (panel button) | Hides everything beyond 2 connections; sidebar shows a reset button |
| Scroll / pinch | Zoom — similarity edges auto-hide below 0.55× zoom to reduce clutter |
| Hover a Relations edge | Predicate label appears (hidden otherwise) |
| Filter chips (sidebar) | Toggle visibility by repo, node type, or edge kind |
| Click empty space | Clear highlight and reset dim |

Node **size** reflects the number of connections — the most-connected hubs (like `core:Detection` and `topic:MONITOR_DATA_TOPIC`) are visually larger.

---

## Maintaining the wiki

The wiki follows the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern — Claude writes and revises pages, humans read. See `CLAUDE.md` for page format, naming conventions, and ingest/lint workflows.

**After adding or editing a wiki page:**

```bash
python tools/build_index.py        # updates search index + sidebar
python tools/build_graph.py        # only needed if you added a new node-worthy entity
```

**Adding typed relation triples:**

```bash
# Ask Claude to extract triples from a wiki page → save to extracted.json, then:
python tools/merge_relations.py --in extracted.json
# Unknown node IDs, bad predicates, self-loops are rejected with explanations.
```

Allowed predicates: `USES` · `COMPOSES` · `PUBLISHES_TO` · `SUBSCRIBES_TO` · `DEPENDS_ON` · `IS_A_KIND_OF` · `EXAMPLE_OF` · `ALTERNATIVE_TO` · `MAINTAINED_BY` · `DOCUMENTED_BY` · `REFERENCED_BY`
