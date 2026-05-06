#!/usr/bin/env python3
"""
Health-check the Lumi Codebase Wiki.

Reports:
- Pages missing frontmatter
- Broken [[wikilinks]] and broken relative .md links
- Graph nodes whose `wiki:` path doesn't exist on disk
- Pages with no inbound link from any other page or graph node (orphans)

Run:
    python tools/lint_wiki.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
GRAPH_JSON = ROOT / "app" / "data" / "graph.json"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\]\(([^)]+\.md)(?:#[^)]+)?\)")


def main() -> int:
    if not WIKI.exists():
        print("No wiki/ directory found.")
        return 1

    pages = sorted(WIKI.rglob("*.md"))
    page_paths = {p.relative_to(ROOT).as_posix() for p in pages}

    issues = {
        "missing_frontmatter": [],
        "broken_links": [],
        "graph_to_missing_wiki": [],
        "orphans": [],
    }

    inbound: dict[str, set[str]] = {p: set() for p in page_paths}

    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        try:
            text = page.read_text(encoding="utf-8")
        except Exception as exc:
            issues["broken_links"].append(f"{rel}: cannot read ({exc})")
            continue

        m = FRONTMATTER_RE.match(text)
        if not m:
            issues["missing_frontmatter"].append(rel)
        else:
            try:
                yaml.safe_load(m.group(1))
            except yaml.YAMLError as exc:
                issues["missing_frontmatter"].append(f"{rel}: invalid YAML ({exc})")

        # markdown links to other .md files
        for target in MD_LINK_RE.findall(text):
            if target.startswith(("http://", "https://")):
                continue
            target_path = (page.parent / target).resolve()
            try:
                target_rel = target_path.relative_to(ROOT).as_posix()
            except ValueError:
                continue
            if target_rel.startswith("wiki/") and target_rel not in page_paths:
                issues["broken_links"].append(f"{rel} → {target}")
            elif target_rel in inbound:
                inbound[target_rel].add(rel)

        # wikilinks
        for raw in WIKILINK_RE.findall(text):
            slug = raw.strip().split("|", 1)[0]
            if not any(p.endswith(f"/{slug}.md") or Path(p).stem == slug for p in page_paths):
                issues["broken_links"].append(f"{rel} → [[{raw}]]")

    # graph -> wiki path validation
    if GRAPH_JSON.exists():
        try:
            graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
            for n in graph.get("nodes", []):
                wp = n.get("wiki")
                if not wp:
                    continue
                wp_clean = wp.split("#", 1)[0]
                if wp_clean not in page_paths:
                    issues["graph_to_missing_wiki"].append(f"{n['id']} → {wp_clean}")
                elif wp_clean in inbound:
                    inbound[wp_clean].add(f"graph:{n['id']}")
        except Exception as exc:
            print(f"Could not load graph.json: {exc}")
    else:
        print(f"Note: {GRAPH_JSON.relative_to(ROOT)} not found. Run build_graph.py first.")

    # orphans
    for p, sources in inbound.items():
        if not sources and Path(p).name not in {"index.md", "log.md", "overview.md"}:
            issues["orphans"].append(p)

    total = sum(len(v) for v in issues.values())
    if total == 0:
        print("Wiki is clean.")
        return 0

    for category, items in issues.items():
        if not items:
            continue
        print(f"\n[{category}] ({len(items)})")
        for it in items[:50]:
            print(f"  - {it}")
        if len(items) > 50:
            print(f"  ... and {len(items) - 50} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
