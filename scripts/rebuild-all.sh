#!/usr/bin/env bash
# Rebuild every generated artifact in one shot.
#
#   1. Structural graph        → app/data/graph.json
#   2. TF-IDF similarity layer → app/data/similarity.json
#   3. Wiki index + search     → wiki/index.md, app/data/wiki-index.json
#   4. Health check            → console
#
# The relations layer is intentionally NOT rebuilt — it's LLM-extracted and
# manually curated via tools/merge_relations.py.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "→ build_graph.py"
python3 tools/build_graph.py

echo ""
echo "→ build_similarity.py"
python3 tools/build_similarity.py

echo ""
echo "→ build_index.py"
python3 tools/build_index.py

echo ""
echo "→ lint_wiki.py"
python3 tools/lint_wiki.py || true

echo ""
echo "Done. Open the app:"
echo "  ./scripts/serve.sh"
