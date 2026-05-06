#!/usr/bin/env python3
"""
Validate + merge LLM-extracted typed relations into app/data/relations.json.

The extraction step is done in a Claude Code session (see CLAUDE.md →
"Knowledge graph workflow"). Claude returns a JSON object on stdout; this
tool validates triples against the current graph and merges them into the
existing relations.json (deduping by (subject, predicate, object)).

Input format (JSON on stdin OR via --in path):

    {
      "triples": [
        {
          "subject": "monitors:colour",
          "predicate": "PUBLISHES_TO",
          "object":   "topic:MONITOR_DATA_TOPIC",
          "evidence": "wiki/ai-continuous/monitors/colour.md"
        },
        ...
      ]
    }

Allowed predicates (whitelist — keeps the graph readable):
    USES, COMPOSES, PUBLISHES_TO, SUBSCRIBES_TO, DEPENDS_ON,
    IS_A_KIND_OF, EXAMPLE_OF, ALTERNATIVE_TO, MAINTAINED_BY,
    DOCUMENTED_BY, REFERENCED_BY

Run:
    cat extracted.json | python tools/merge_relations.py
    python tools/merge_relations.py --in extracted.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_JSON = ROOT / "app" / "data" / "graph.json"
OUT = ROOT / "app" / "data" / "relations.json"

ALLOWED_PREDICATES = {
    "USES", "COMPOSES", "PUBLISHES_TO", "SUBSCRIBES_TO", "DEPENDS_ON",
    "IS_A_KIND_OF", "EXAMPLE_OF", "ALTERNATIVE_TO", "MAINTAINED_BY",
    "DOCUMENTED_BY", "REFERENCED_BY",
}


def load_node_ids() -> set[str]:
    if not GRAPH_JSON.exists():
        sys.exit("graph.json not found. Run tools/build_graph.py first.")
    g = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    return {n["id"] for n in g["nodes"]}


def load_existing() -> dict:
    if OUT.exists():
        try:
            return json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"meta": {}, "edges": []}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default=None,
                    help="Path to JSON file. If omitted, reads stdin.")
    ap.add_argument("--replace", action="store_true",
                    help="Discard existing relations rather than merge.")
    args = ap.parse_args()

    raw = (Path(args.infile).read_text() if args.infile else sys.stdin.read())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"Could not parse JSON: {exc}")

    triples = data.get("triples", [])
    if not isinstance(triples, list):
        sys.exit("'triples' must be a list.")

    node_ids = load_node_ids()
    existing = load_existing() if not args.replace else {"meta": {}, "edges": []}
    existing_keys = {(e["source"], e["kind"], e["target"]) for e in existing["edges"]}

    accepted, rejected = [], []
    for t in triples:
        s, p, o = t.get("subject"), t.get("predicate"), t.get("object")
        if not (s and p and o):
            rejected.append(("missing-field", t)); continue
        if p not in ALLOWED_PREDICATES:
            rejected.append((f"bad-predicate:{p}", t)); continue
        if s not in node_ids:
            rejected.append((f"unknown-subject:{s}", t)); continue
        if o not in node_ids:
            rejected.append((f"unknown-object:{o}", t)); continue
        if s == o:
            rejected.append(("self-loop", t)); continue
        kind = f"rel:{p}"
        key = (s, kind, o)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        accepted.append({
            "source": s, "target": o, "kind": kind,
            "predicate": p, "label": p.replace("_", " ").lower(),
            "evidence": t.get("evidence", ""),
        })

    existing["edges"].extend(accepted)
    existing["meta"]["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    existing["meta"]["edge_count"] = len(existing["edges"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    print(f"Accepted {len(accepted)} new triples (total now {len(existing['edges'])}).")
    if rejected:
        print(f"Rejected {len(rejected)}:")
        for reason, t in rejected[:10]:
            print(f"  {reason}: {t.get('subject')} → {t.get('object')}")
        if len(rejected) > 10:
            print(f"  ... and {len(rejected) - 10} more")
    print(f"  → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
