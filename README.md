# Lumi Codebase Wiki

A lightweight onboarding companion for the three Lumi repos:

- **Lumi-AI-Continuous** — Python + Go backend, monitors, arbiters, Kafka
- **Lumi-AI-Core** — V2 AI/CV class libraries
- **lumi-web-v2** — Next.js web app

It pairs an **interactive cross-repo knowledge graph** with an LLM-maintained markdown wiki and a **conversational layer** powered by Gemini, all served as static files. No build step. No backend. Just open `index.html`.

The graph has three independently toggleable layers:

| Layer | What it shows | How it's built |
|------|---------------|----------------|
| **Structural** | Imports, Kafka pubsub, OpenAPI contracts, route ↔ API ↔ backend bridges | `tools/build_graph.py` walks the three repos, parses ASTs / regexes / YAMLs |
| **Similarity** | Pages that talk about the same thing (no embeddings — pure TF-IDF cosine, mutual top-K) | `tools/build_similarity.py` |
| **Relations** | LLM-extracted typed triples like `colour PUBLISHES_TO MONITOR_DATA_TOPIC`, `arbiter:v2 ALTERNATIVE_TO arbiter:v1` | A Claude session extracts triples; `tools/merge_relations.py` validates and merges them |

You toggle the layers in the graph sidebar.

The **Chat** tab lets you ask questions against the entire knowledge graph + wiki using Gemini 2.5 Flash. Answers are grounded in the wiki and cite pages by path; clicking a citation jumps into the wiki reader.

## Quick start (new hires)

Sit next to the three cloned repos:

```
AI_Tooling_workshop/
├── Lumi-AI-Continuous/
├── Lumi-AI-Core/
├── lumi-web-v2/
└── lumi-codebase-wiki/   ← you are here
```

Run once to build the graph:

```bash
pip install -r tools/requirements.txt
python tools/build_graph.py        # → app/data/graph.json    (structural layer)
python tools/build_similarity.py   # → app/data/similarity.json (TF-IDF layer)
python tools/build_index.py        # → app/data/wiki-index.json
# relations.json is optional — see "Expanding the relations layer" below
```

Serve the app:

```bash
./scripts/serve.sh
# → open http://localhost:8000/app/
```

That's it. The landing page has a Day 1 / Week 1 / Month 1 tour. The graph view is one click away.

## What's where

| Path | What it is |
|------|------------|
| `app/` | The static viewer (HTML + Cytoscape.js + marked.js + Fuse.js) |
| `app/data/` | Generated `graph.json` and `wiki-index.json` (gitignored) |
| `wiki/` | Markdown knowledge base — Claude maintains, humans read |
| `tools/` | Python scripts that walk the three repos and rebuild the graph + index |
| `scripts/serve.sh` | Wrapper around `python -m http.server 8000` |
| `CLAUDE.md` | The wiki schema — page conventions and ingest/lint workflows for Claude |

## How the wiki gets maintained

The intent is the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern: the wiki is a **persistent, compounding artifact**. You don't write it by hand — Claude writes and revises it as new docs, code changes, or questions come in. See `CLAUDE.md` for the conventions.

## Adding your first page

1. Read `CLAUDE.md` for the page format
2. Write a markdown file under `wiki/` with proper frontmatter
3. Run `python tools/build_index.py` so the sidebar picks it up
4. (Optional) Re-run `python tools/build_graph.py` if you've added a new node-worthy entity

## Setting up the chat layer

The Chat page calls the Gemini API directly from the browser. To enable it:

```bash
cp app/config.example.js app/config.js
# edit app/config.js — paste your key from https://aistudio.google.com/apikey
```

`app/config.js` is gitignored. The browser reads it via a `<script>` tag, so no server-side setup is needed. Each user (each browser) provides their own key.

By default the chat uses `gemini-2.5-flash` with the entire wiki (~70k tokens) sent on every turn. Gemini 2.5's implicit prompt caching kicks in automatically and discounts the repeated context after turn 1, so a chat session costs roughly **2¢ for the first message and ~½¢ per follow-up**.

Switch to `gemini-2.5-pro` in `config.js` if you want heavier reasoning at higher cost.

## Expanding the relations layer

The shipped `app/data/relations.json` covers ~63 typed triples extracted from the 11 hand-written exemplar pages. Adding more is a 3-step Claude Code session:

1. Pick a wiki page (or a batch). Open it in Claude.
2. Ask: *"Extract typed triples from this page using the predicate whitelist in `tools/merge_relations.py`. Return a JSON object with a `triples` array. Use only graph-node IDs from `app/data/graph.json`."* Pipe Claude's JSON to a file.
3. Run `python tools/merge_relations.py --in extracted.json`. Invalid triples (unknown nodes, bad predicates, self-loops) are rejected with reasons.

Allowed predicates: `USES`, `COMPOSES`, `PUBLISHES_TO`, `SUBSCRIBES_TO`, `DEPENDS_ON`, `IS_A_KIND_OF`, `EXAMPLE_OF`, `ALTERNATIVE_TO`, `MAINTAINED_BY`, `DOCUMENTED_BY`, `REFERENCED_BY`.

## Why no embeddings?

The TF-IDF + LLM-triples combo gets you ~95% of the value of a vector-embedding knowledge graph for an English-only, single-domain wiki of this size, with **zero infra and zero API cost** for the deterministic similarity layer. Embeddings buy you cross-language semantics and synonym tolerance — neither matter much for a 100-page onboarding wiki where the controlled vocabulary is small.

## Known gaps in v1

- Stubs for ~70 graph nodes; only ~6 pages are hand-written
- The 4th repo `lumi-API` (used by Kubb codegen) is referenced but not cloned locally — it shows up as a "missing" node
- No live LLM Q&A in the app yet (deliberately — keeps it static and credentials-free)
