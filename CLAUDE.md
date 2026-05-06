# CLAUDE.md — Lumi Codebase Wiki schema

This file tells future Claude sessions how this wiki is structured and maintained. Read it first; it's short.

## What this repo is

A static, single-folder onboarding tool that sits next to the three Lumi repos. Two pieces:

1. **`wiki/`** — markdown knowledge base. Claude writes and edits these files. Humans read.
2. **`app/`** — a tiny HTML viewer (Cytoscape.js graph + markdown reader + search). No build step. Cosmetic only — all the meaning lives in `wiki/` and the graph data.

The wiki is meant to be a **compounding artifact** in the spirit of Karpathy's "LLM Wiki" pattern. Update existing pages when new info comes in; don't just add new ones.

## Page format

Every markdown file under `wiki/` MUST start with this frontmatter:

```markdown
---
name: Short page title
description: One-line description used in the index and search results
type: overview | tour | architecture | repo | monitor | arbiter | module | api-domain | route-group | concept | glossary | log
tags: [optional, free-form, tags]
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/colour/colour.py }   # optional, but encouraged
graph_node: monitors:colour                                          # optional, links page ↔ graph node
---
```

Body conventions:

- **Lead with the answer.** First sentence should make sense to a new hire who has only read `wiki/overview.md`.
- **Cross-link generously.** Use either standard markdown links (`[text](path/to/page.md)`) or `[[wikilink]]` syntax — the viewer resolves both.
- **Keep prose tight.** 200–600 words per page. Long enough to be useful, short enough to read on a coffee break.
- **Cite the source.** When a fact comes from code, include a `repo:path/to/file.py:LINE` reference in-line.
- **No duplication.** If the per-repo `README.md` or `Docs/` already covers something, link to it. Summarise in one paragraph; don't paste.

## Directory layout

```
wiki/
├── overview.md           # the front door — what is Lumi, in 200 words
├── index.md              # auto-generated catalog (do NOT hand-edit)
├── log.md                # append-only ingest/update log
├── glossary.md
├── tour/                 # day-1 / week-1 / month-1 onboarding paths
├── architecture/         # cross-cutting system pages
├── ai-continuous/        # one folder per repo
├── ai-core/
├── web/
└── concepts/             # cross-cutting domain ideas
```

When adding a page, place it under the most specific folder that applies. If unsure, prefer the per-repo folder.

## Workflows

### Ingest workflow (a new doc, code change, or question landed)

1. Read the source.
2. Identify which existing wiki pages it touches. Update them in place — don't create duplicates.
3. If a genuinely new entity needs a page (e.g. a new monitor was added), create the page with full frontmatter.
4. Cross-link from related pages. Update `architecture/` summaries if the change crosses repos.
5. If the change adds a new node or edge worth surfacing, re-run `python tools/build_graph.py`.
6. Append a one-line entry to `wiki/log.md`:
   ```markdown
   ## [YYYY-MM-DD] ingest | <source name>
   Touched: pageA.md, pageB.md. Added: pageC.md.
   ```

### Query workflow (a human asked a question)

1. Read `wiki/index.md` to find candidate pages.
2. Read those pages. If they answer the question, cite them by file path and quote the relevant lines.
3. If the answer is non-trivial and worth keeping, file the answer back into the wiki (either as a new page or as additions to existing ones). Explorations should compound — don't let useful synthesis disappear into chat history.
4. Append to `wiki/log.md`:
   ```markdown
   ## [YYYY-MM-DD] query | <one-line question>
   Answered using: pageA.md, pageB.md. Filed back into: pageC.md.
   ```

### Knowledge-graph workflow (extracting typed relations)

The graph viewer has three layers: structural (auto-detected), similarity (TF-IDF), and **relations** (LLM-extracted triples). The relations layer is opt-in and grows over time.

To extract relations from a page:

1. Read the target wiki page(s).
2. Identify graph-node IDs from `app/data/graph.json` that the page asserts relationships about. Stick to the **whitelist of node IDs** — never invent new IDs.
3. Emit a JSON object on stdout with this exact shape:

   ```json
   {
     "triples": [
       {
         "subject":   "<node-id>",
         "predicate": "<one of: USES | COMPOSES | PUBLISHES_TO | SUBSCRIBES_TO | DEPENDS_ON | IS_A_KIND_OF | EXAMPLE_OF | ALTERNATIVE_TO | MAINTAINED_BY | DOCUMENTED_BY | REFERENCED_BY>",
         "object":    "<node-id>",
         "evidence":  "wiki/<path>.md"
       }
     ]
   }
   ```

4. The user runs `python tools/merge_relations.py --in <file>.json`. Invalid triples (bad predicates, unknown IDs, self-loops, duplicates) are rejected.
5. Append a one-line entry to `wiki/log.md`: `## [YYYY-MM-DD] relations | <pages> → +N triples`.

Quality rules:
- Prefer fewer high-confidence triples over many speculative ones.
- Never invent triples the page doesn't actually state.
- Skip facts already covered by the structural layer (`monitors:colour USES core:Colours` is auto-detected from imports — no value re-asserting it) UNLESS the page makes the relationship explicit and adds context.
- Use `EXAMPLE_OF` for "this is held up as an exemplar of X", `ALTERNATIVE_TO` for sibling implementations (e.g. arbiter v1/v2/v3).

### Lint workflow (periodic health check)

Run `python tools/lint_wiki.py`. It reports:
- Pages missing frontmatter
- Broken `[[wikilinks]]`
- Orphan pages (no inbound links and no graph node)
- Graph nodes whose `wiki:` path doesn't exist on disk
- Topics surfaced in code but not yet in `wiki/architecture/kafka-topics.md`

Fix what's fixable, then append a single log line.

## Naming conventions

- Files: `kebab-case.md` for prose pages, `PascalCase.md` only for V2 modules (matches their folder names: `Detection.md`, `Vessels.md`).
- Frontmatter `name` is human-readable, doesn't need to match the filename.
- `graph_node` IDs use `category:identifier` format: `monitors:colour`, `core:Detection`, `web:api:devices`, `topic:MONITOR_DATA_TOPIC`.

## Glossary upkeep rule

Whenever you write a new term that a new hire wouldn't know, add a one-line entry to `wiki/glossary.md` the same session. The graph viewer will surface glossary entries as tooltips on node hover.

## What lives outside this wiki (and shouldn't be re-documented)

- Per-repo `README.md` and `CLAUDE.md` — link to them, don't paraphrase
- `Lumi-AI-Continuous/Docs/` and `Lumi-AI-Continuous/docs/`
- `Lumi-AI-Core/agreedDataSchema.md`
- `lumi-web-v2/docs/`

The wiki's job is to *connect* the three repos and *summarise for new hires*, not to re-author per-repo documentation.

## Don'ts

- Do NOT hand-edit `wiki/index.md` — it's regenerated by `tools/build_index.py`.
- Do NOT commit `app/data/graph.json` or `app/data/wiki-index.json` — they're generated and gitignored.
- Do NOT delete a page silently. If a page is obsolete, replace its body with a one-line redirect note and a stub frontmatter, or update it in place.
