#!/usr/bin/env python3
"""
Generate a stub markdown page for every graph node whose `wiki:` path
doesn't exist yet. Existing pages are never overwritten.

Run after `build_graph.py` whenever new nodes appear:
    python tools/build_graph.py
    python tools/gen_stubs.py
    python tools/build_index.py
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GRAPH_JSON = ROOT / "app" / "data" / "graph.json"

TYPE_TO_FRONTMATTER_TYPE = {
    "monitor": "monitor",
    "arbiter": "arbiter",
    "service": "service",
    "common-util": "common-util",
    "v2-module": "module",
    "api-domain": "api-domain",
    "route-group": "route-group",
    "kafka-topic": "concept",
    "pipeline": "pipeline",
    "repo": "repo",
    "repo-missing": "repo",
}

BODY_TEMPLATE = """\
# {name}

> **Stub.** This page was auto-generated. Tell Claude what you'd like to know about this and the page will be filled in.

## Summary

{description}

## Where the code lives

`{file_path}`

## See also

- [System overview]({prefix}architecture/system-overview.md)
- [Day 1 tour]({prefix}tour/day-1.md)
"""


def main() -> None:
    if not GRAPH_JSON.exists():
        print("graph.json not found — run tools/build_graph.py first.")
        return
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    created = 0
    for node in graph["nodes"]:
        wiki_rel = node.get("wiki")
        if not wiki_rel or "#" in wiki_rel:
            continue
        wiki_path = ROOT / wiki_rel
        if wiki_path.exists():
            continue
        wiki_path.parent.mkdir(parents=True, exist_ok=True)

        depth = len(Path(wiki_rel).relative_to("wiki").parts) - 1
        prefix = "../" * depth if depth > 0 else ""

        name = node.get("label", node["id"])
        description = node.get("summary") or "TODO: fill in."
        file_path = node.get("file") or "n/a"
        repo = node.get("repo", "unknown")

        frontmatter = {
            "name": name,
            "description": description,
            "type": TYPE_TO_FRONTMATTER_TYPE.get(node.get("type", ""), "concept"),
            "graph_node": node["id"],
            "sources": [{"repo": repo, "path": file_path}],
            "tags": ["stub"],
        }
        fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip()
        body = BODY_TEMPLATE.format(
            name=name,
            description=description,
            file_path=file_path,
            prefix=prefix,
        )

        wiki_path.write_text(f"---\n{fm_yaml}\n---\n\n{body}", encoding="utf-8")
        created += 1

    print(f"Created {created} stub pages.")


if __name__ == "__main__":
    main()
