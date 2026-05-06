---
name: Activity Log
description: Append-only log of wiki ingests, queries, and lint passes.
type: log
---

# Activity Log

Newest entries at the top. One block per event.

## [2026-05-06] knowledge-graph layers added
Replaced the structural-only graph with three toggleable layers in `app/graph.html`: Structural, Similarity (TF-IDF mutual top-K, 107 edges), Relations (LLM-extracted typed triples, 63 edges). Added `tools/build_similarity.py` and `tools/merge_relations.py`. Dropped `belongs_to` edges from the structural layer (parent compounds already encode it; the explicit edges were collapsing fcose layout into a diagonal chain). Tuned fcose params for better spread.

## [2026-05-06] bootstrap | initial wiki seed
Created skeleton, wiki schema (CLAUDE.md), tools (build_graph, build_index, lint_wiki, gen_stubs), and the static viewer app. Hand-wrote 6 exemplar pages (overview, architecture/system-overview, architecture/kafka-topics, tour/day-1, glossary, ai-continuous/monitors/colour, ai-core/modules/Detection, web/api-domains/devices). Seeded 67 auto-generated stubs from graph.json (~107 nodes, ~144 edges).
