#!/usr/bin/env python3
"""
Build a TF-IDF similarity graph over the nodes in app/data/graph.json.

For each graph node, we assemble a "document" from:
  - its wiki page body (frontmatter stripped)
  - its source path's README.md (if present)
  - the head (first ~400 lines) of its main source file (if present)

Then we compute pairwise cosine similarity over TF-IDF vectors and emit a
"mutual top-K" similarity graph: an edge (a, b) exists iff b is in a's top-K
AND a is in b's top-K. This gives clean, threshold-free similarity edges.

Pure stdlib — no scikit-learn dependency, no embeddings, no API calls.

Output: app/data/similarity.json
    {
      "edges": [
        { "source", "target", "kind": "similar", "weight": 0.34,
          "shared_terms": ["vessel", "liquid", "tracking"] },
        ...
      ],
      "meta": { "k", "doc_count", "term_count", "generated_at" }
    }

Run:
    python tools/build_similarity.py [--k 4]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
GRAPH_JSON = ROOT / "app" / "data" / "graph.json"
OUT = ROOT / "app" / "data" / "similarity.json"
FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

# A small, conservative stopword list. We avoid pulling in nltk to keep this
# pure-stdlib. Domain-specific terms (monitor, arbiter, V2, kafka) stay in.
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "and",
    "or", "but", "of", "to", "in", "on", "at", "for", "with", "as", "by",
    "this", "that", "these", "those", "it", "its", "from", "into", "out",
    "if", "when", "while", "where", "what", "which", "who", "how", "why",
    "do", "does", "did", "doing", "have", "has", "had", "having",
    "can", "could", "will", "would", "should", "may", "might",
    "not", "no", "any", "all", "some", "more", "most", "less", "many",
    "one", "two", "three",
    "i", "you", "we", "they", "he", "she", "him", "her", "them", "us",
    "your", "our", "their", "his", "hers",
    "my", "me", "mine",
    "so", "also", "just", "only", "very", "much", "such",
    "see", "use", "used", "using", "uses", "make", "makes", "made", "get",
    "gets", "got", "let", "lets", "go", "goes", "going",
    "page", "pages", "section", "sections", "file", "files", "doc", "docs",
    "todo", "stub",
    # markdown / code noise
    "md", "py", "tsx", "ts", "json", "yaml", "yml", "html", "css", "js",
    "https", "http", "www", "com",
    "true", "false", "none", "null",
    "self", "def", "class", "import", "return", "from", "raise",
    "function", "const", "let", "var", "interface", "type",
    "exports", "default", "export",
}

# Tokens: alphanumeric words >= 3 chars; preserve underscores (for things
# like MONITOR_DATA_TOPIC) and CamelCase (split before re-joining).
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")


def split_camel(token: str) -> Iterable[str]:
    """Yield the original token AND its camelCase / PascalCase parts."""
    yield token.lower()
    parts = re.findall(r"[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z])|[A-Z]+|[a-z]+", token)
    if len(parts) > 1:
        for p in parts:
            if len(p) >= 3:
                yield p.lower()


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for raw in TOKEN_RE.findall(text):
        for t in split_camel(raw):
            if t not in STOPWORDS and len(t) >= 3 and not t.isdigit():
                out.append(t)
    return out


def load_graph() -> dict:
    return json.loads(GRAPH_JSON.read_text(encoding="utf-8"))


def read_safe(path: Path, head_lines: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    if head_lines:
        return "\n".join(text.splitlines()[:head_lines])
    return text


def assemble_doc(node: dict, shared_wikis: set[str], shared_files: set[str]) -> str:
    """Build the corpus text for a single node.

    If the node's wiki page or source file is shared with siblings (e.g. all
    Kafka topic nodes pointing at the same kafka-topics.md, all route groups
    pointing at routes.md), we skip the shared body to avoid spurious 1.0
    similarities. The label + summary still distinguish them.
    """
    pieces: list[str] = []
    # Label tokens repeated to give them more weight
    label = node.get("label", "")
    pieces.append(label)
    pieces.append(label)
    pieces.append(node.get("summary", ""))
    pieces.append(node.get("type", ""))
    # Embed the node id (it carries category + name)
    pieces.append(node.get("id", "").replace(":", " "))

    wiki_rel = (node.get("wiki") or "").split("#", 1)[0]
    if wiki_rel and wiki_rel not in shared_wikis:
        wiki_path = ROOT / wiki_rel
        if wiki_path.exists():
            text = read_safe(wiki_path)
            text = FRONTMATTER_RE.sub("", text, count=1)
            pieces.append(text)

    file_rel = node.get("file")
    if file_rel and file_rel not in shared_files:
        src = WORKSHOP / file_rel
        if src.is_dir():
            readme = src / "README.md"
            if readme.exists():
                pieces.append(read_safe(readme))
            for ext in (".py", ".ts", ".tsx", ".go"):
                for fp in sorted(src.glob(f"*{ext}"))[:2]:
                    pieces.append(read_safe(fp, head_lines=200))
                    break
        elif src.is_file():
            pieces.append(read_safe(src, head_lines=400))
            readme = src.parent / "README.md"
            if readme.exists():
                pieces.append(read_safe(readme))

    return "\n".join(p for p in pieces if p)


def find_shared(nodes: list[dict], key: str) -> set[str]:
    """Return the set of values for `key` that appear on more than one node."""
    seen: Counter = Counter()
    for n in nodes:
        v = (n.get(key) or "").split("#", 1)[0]
        if v:
            seen[v] += 1
    return {v for v, c in seen.items() if c > 1}


def compute_tfidf(docs: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    df: Counter = Counter()
    for tokens in docs.values():
        df.update(set(tokens))
    n_docs = max(len(docs), 1)
    idf = {t: math.log((n_docs + 1) / (df_t + 1)) + 1.0
           for t, df_t in df.items()}

    tfidf: dict[str, dict[str, float]] = {}
    for doc_id, tokens in docs.items():
        if not tokens:
            tfidf[doc_id] = {}
            continue
        tf = Counter(tokens)
        # log-scaled tf to avoid frequent terms dominating
        vec = {t: (1.0 + math.log(tf_t)) * idf[t] for t, tf_t in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        tfidf[doc_id] = {t: v / norm for t, v in vec.items()}
    return tfidf


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(av * b.get(t, 0.0) for t, av in a.items())


def shared_top_terms(a: dict[str, float], b: dict[str, float], k: int = 5) -> list[str]:
    common = {t: a[t] * b[t] for t in a if t in b}
    return [t for t, _ in sorted(common.items(), key=lambda x: -x[1])[:k]]


def mutual_top_k_edges(tfidf: dict[str, dict[str, float]], k: int = 4,
                       min_score: float = 0.10) -> list[dict]:
    ids = list(tfidf.keys())
    top: dict[str, list[tuple[str, float]]] = {}
    # O(n^2) — fine for ~100 docs
    for a in ids:
        scored = []
        for b in ids:
            if a == b:
                continue
            s = cosine(tfidf[a], tfidf[b])
            if s >= min_score:
                scored.append((b, s))
        scored.sort(key=lambda x: -x[1])
        top[a] = scored[:k]

    seen = set()
    edges: list[dict] = []
    for a, peers in top.items():
        peer_lookup = {p: s for p, s in peers}
        for b, s in peers:
            if a in {p for p, _ in top.get(b, [])}:
                key = tuple(sorted([a, b]))
                if key in seen:
                    continue
                seen.add(key)
                edges.append({
                    "source": key[0],
                    "target": key[1],
                    "kind": "similar",
                    "weight": round(s, 3),
                    "shared_terms": shared_top_terms(tfidf[a], tfidf[b]),
                })
    return sorted(edges, key=lambda e: -e["weight"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=4,
                    help="Top-K peers per node (mutual). Default 4.")
    ap.add_argument("--min-score", type=float, default=0.10,
                    help="Drop similarity edges below this cosine score.")
    args = ap.parse_args()

    graph = load_graph()
    shared_wikis = find_shared(graph["nodes"], "wiki")
    shared_files = find_shared(graph["nodes"], "file")
    if shared_wikis:
        print(f"Skipping shared wiki bodies for: {sorted(shared_wikis)[:5]}{' …' if len(shared_wikis) > 5 else ''}")
    raw_docs: dict[str, str] = {}
    for n in graph["nodes"]:
        raw_docs[n["id"]] = assemble_doc(n, shared_wikis, shared_files)

    tokenised: dict[str, list[str]] = {nid: tokenize(text) for nid, text in raw_docs.items()}
    avg_len = sum(len(t) for t in tokenised.values()) / max(len(tokenised), 1)
    print(f"Built {len(tokenised)} docs, avg {avg_len:.0f} tokens.")

    tfidf = compute_tfidf(tokenised)
    edges = mutual_top_k_edges(tfidf, k=args.k, min_score=args.min_score)
    print(f"Computed {len(edges)} mutual top-{args.k} similarity edges "
          f"(min score {args.min_score}).")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "k": args.k,
            "min_score": args.min_score,
            "doc_count": len(tokenised),
            "term_count": sum(len(v) for v in tfidf.values()),
        },
        "edges": edges,
    }, indent=2), encoding="utf-8")
    print(f"  → {OUT.relative_to(ROOT)}")

    # Print top-10 strongest edges so you can sanity-check the layer
    print("\nTop 10 strongest similarity edges:")
    for e in edges[:10]:
        print(f"  {e['weight']:.3f}  {e['source']:<28} ↔ {e['target']:<28} "
              f"shared: {', '.join(e['shared_terms'][:3])}")


if __name__ == "__main__":
    main()
