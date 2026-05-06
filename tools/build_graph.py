#!/usr/bin/env python3
"""
Build a cross-repo code graph for the Lumi Codebase Wiki.

Walks Lumi-AI-Continuous, Lumi-AI-Core, and lumi-web-v2 (sibling folders by
default) and emits app/data/graph.json with the shape:

    {
      "nodes": [{ "id", "label", "type", "repo", "file", "wiki", "summary" }, ...],
      "edges": [{ "source", "target", "kind", "label" }, ...],
      "meta":  { "generated_at", "counts" }
    }

The graph is intentionally module-level so it stays legible (~70 nodes).
File-level drill-in is computed lazily by app/assets/js/graph.js.

Run:
    python tools/build_graph.py
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT.parent
CONTINUOUS = WORKSHOP / "Lumi-AI-Continuous"
CORE = WORKSHOP / "Lumi-AI-Core"
WEB = WORKSHOP / "lumi-web-v2"
OUT = ROOT / "app" / "data" / "graph.json"

REPO_COLORS = {
    "Lumi-AI-Continuous": "#3b82f6",  # blue
    "Lumi-AI-Core": "#8b5cf6",         # violet
    "lumi-web-v2": "#10b981",          # emerald
    "external": "#9ca3af",             # gray
}


@dataclass
class Node:
    id: str
    label: str
    type: str
    repo: str
    file: str | None = None
    wiki: str | None = None
    summary: str | None = None
    color: str | None = None
    parent: str | None = None  # for cytoscape compound grouping


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    label: str | None = None


@dataclass
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    _node_ids: set[str] = field(default_factory=set)

    def add_node(self, node: Node) -> None:
        if node.id in self._node_ids:
            return
        if node.color is None:
            node.color = REPO_COLORS.get(node.repo, "#9ca3af")
        self.nodes.append(node)
        self._node_ids.add(node.id)

    def add_edge(self, edge: Edge) -> None:
        # Skip edges to nodes we never created
        if edge.source not in self._node_ids or edge.target not in self._node_ids:
            return
        if edge.source == edge.target:
            return
        self.edges.append(edge)


# --------------------------------------------------------------------------- #
# Repo anchors + groups
# --------------------------------------------------------------------------- #
def add_anchors(g: Graph) -> None:
    g.add_node(Node(
        id="repo:continuous", label="Lumi-AI-Continuous", type="repo",
        repo="Lumi-AI-Continuous",
        summary="Distributed AI monitoring platform: monitors, arbiters, monitor relay.",
        wiki="wiki/ai-continuous/README.md",
    ))
    g.add_node(Node(
        id="repo:core", label="Lumi-AI-Core", type="repo",
        repo="Lumi-AI-Core",
        summary="V2 AI/CV class libraries: detection, tracking, vessels, gestures, …",
        wiki="wiki/ai-core/README.md",
    ))
    g.add_node(Node(
        id="repo:web", label="lumi-web-v2", type="repo",
        repo="lumi-web-v2",
        summary="Next.js 15 web app for lab device management and experiments.",
        wiki="wiki/web/README.md",
    ))
    g.add_node(Node(
        id="repo:lumi-api", label="lumi-API (external)", type="repo-missing",
        repo="external",
        summary="Backend gateway repo. Referenced via Kubb codegen but not cloned locally.",
        wiki="wiki/web/kubb-pipeline.md",
    ))


# --------------------------------------------------------------------------- #
# Lumi-AI-Continuous
# --------------------------------------------------------------------------- #
MONITOR_BLURBS = {
    "3DCalc": "3D pose / dimension estimation (YOLO + depth).",
    "colour": "Dominant colour analysis in regions of interest.",
    "custom": "Configurable multi-capability AI pipeline (custom_agent.py).",
    "dial": "Analogue gauge / dial reading.",
    "hands": "Hand tracking and gesture recognition.",
    "homogeneity": "Liquid homogeneity and contrast analysis.",
    "liquids": "Liquid volume, description, precipitation, phase analysis.",
    "object": "Object detection with anonymisation.",
    "object_list": "Visible object list detection.",
    "objects": "Multi-object tracking.",
    "text": "OCR / text recognition (MMOCR).",
}


def scan_continuous(g: Graph) -> None:
    if not CONTINUOUS.exists():
        return

    monitors_dir = CONTINUOUS / "monitors"
    if monitors_dir.exists():
        for d in sorted(p for p in monitors_dir.iterdir() if p.is_dir()):
            name = d.name
            if name.startswith("__") or name.startswith("."):
                continue
            entry = next((d / f"{name}.py" for f in [name] if (d / f"{name}.py").exists()), None)
            if entry is None:
                pys = sorted(d.glob("*.py"))
                entry = pys[0] if pys else None
            g.add_node(Node(
                id=f"monitors:{name}",
                label=f"{name} (monitor)",
                type="monitor",
                repo="Lumi-AI-Continuous",
                file=str(entry.relative_to(WORKSHOP)) if entry else f"Lumi-AI-Continuous/monitors/{name}",
                wiki=f"wiki/ai-continuous/monitors/{name}.md",
                summary=MONITOR_BLURBS.get(name, "AI monitor."),
                parent="repo:continuous",
            ))
            # parent compound encodes belonging; no explicit edge needed

    for arb_id, arb_dir, blurb in [
        ("arbiter:v1", "protocol_arbiter",
         "V1 protocol arbiter: nested stage / step / action hierarchy."),
        ("arbiter:v2", "protocol_arbiter_v2",
         "V2 protocol arbiter: flat instruction-ID model; in production alongside v1."),
        ("arbiter:v3", "protocol_arbiter_v3",
         "V3 (in progress): pure state-machine domain layer; no I/O yet."),
    ]:
        path = CONTINUOUS / arb_dir
        if path.exists():
            g.add_node(Node(
                id=arb_id, label=arb_id.split(":")[1].upper() + " arbiter",
                type="arbiter", repo="Lumi-AI-Continuous",
                file=f"Lumi-AI-Continuous/{arb_dir}",
                wiki=f"wiki/ai-continuous/arbiters/{arb_id.split(':')[1]}.md",
                summary=blurb, parent="repo:continuous",
            ))
            # parent compound encodes belonging

    if (CONTINUOUS / "monitor_relay").exists():
        g.add_node(Node(
            id="monitor_relay", label="monitor_relay (Go)",
            type="service", repo="Lumi-AI-Continuous",
            file="Lumi-AI-Continuous/monitor_relay",
            wiki="wiki/ai-continuous/monitor-relay.md",
            summary="Go service: WebRTC ↔ GStreamer ↔ monitor processes ↔ Kafka.",
            parent="repo:continuous",
        ))
        # parent compound encodes belonging

    common_dir = CONTINUOUS / "Common"
    if common_dir.exists():
        for py in sorted(common_dir.glob("*.py")):
            if py.name.startswith("__"):
                continue
            stem = py.stem
            g.add_node(Node(
                id=f"common:{stem}", label=f"Common.{stem}",
                type="common-util", repo="Lumi-AI-Continuous",
                file=str(py.relative_to(WORKSHOP)),
                wiki="wiki/ai-continuous/common.md",
                summary=f"Shared utility: {stem}.",
                parent="repo:continuous",
            ))


# --------------------------------------------------------------------------- #
# Lumi-AI-Core
# --------------------------------------------------------------------------- #
def scan_core(g: Graph) -> None:
    v2 = CORE / "V2"
    if not v2.exists():
        return
    for d in sorted(p for p in v2.iterdir() if p.is_dir()):
        name = d.name
        if name.startswith("__") or name.startswith("."):
            continue
        readme = d / "README.md"
        summary = ""
        if readme.exists():
            try:
                lines = [
                    line.strip() for line in readme.read_text(
                        encoding="utf-8", errors="ignore"
                    ).splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
                if lines:
                    summary = lines[0][:160]
            except Exception:
                pass
        g.add_node(Node(
            id=f"core:{name}", label=name,
            type="v2-module", repo="Lumi-AI-Core",
            file=f"Lumi-AI-Core/V2/{name}",
            wiki=f"wiki/ai-core/modules/{name}.md",
            summary=summary or f"V2 module: {name}.",
            parent="repo:core",
        ))
        # parent compound encodes belonging


# --------------------------------------------------------------------------- #
# lumi-web-v2
# --------------------------------------------------------------------------- #
ROUTE_GROUPS = {
    "overview": "Overview dashboard",
    "lab-ops": "Lab ops dashboard",
    "notifications-dashboard": "Notifications",
    "notebook": "Notebook",
    "organisation": "Organisation settings",
    "profile": "User profile",
    "assist": "Assistant / AI helper",
    "project": "Projects",
    "experiment": "Experiments",
    "workspace": "Workspaces",
    "record": "Records",
    "device": "Devices",
    "protocol": "Protocols (v1)",
    "protocol-version": "Protocol versions",
    "moment": "Moments",
    "public": "Public routes (login, invite, stream)",
}


def scan_web(g: Graph) -> None:
    if not WEB.exists():
        return

    # API domains
    api_dir = WEB / "src" / "api"
    if api_dir.exists():
        for d in sorted(p for p in api_dir.iterdir() if p.is_dir()):
            name = d.name
            count = sum(1 for _ in d.glob("*.ts*"))
            g.add_node(Node(
                id=f"web:api:{name}",
                label=f"api/{name}",
                type="api-domain",
                repo="lumi-web-v2",
                file=f"lumi-web-v2/src/api/{name}",
                wiki=f"wiki/web/api-domains/{name}.md",
                summary=f"{count} TanStack Query hooks for the {name} domain.",
                parent="repo:web",
            ))
            # parent compound encodes belonging

    # Route groups (collapse 38 routes into ~16 groups)
    for slug, label in ROUTE_GROUPS.items():
        g.add_node(Node(
            id=f"web:route:{slug}",
            label=label,
            type="route-group",
            repo="lumi-web-v2",
            file=f"lumi-web-v2/src/app/(authenticated)/{slug}" if slug != "public" else "lumi-web-v2/src/app/(public)",
            wiki=f"wiki/web/routes.md#{slug}",
            summary=f"Route group: {label}.",
            parent="repo:web",
        ))
        # parent compound encodes belonging

    # Kubb pipeline node
    g.add_node(Node(
        id="web:kubb", label="Kubb codegen",
        type="pipeline", repo="lumi-web-v2",
        file="lumi-web-v2/kubb.config.ts",
        wiki="wiki/web/kubb-pipeline.md",
        summary="Generates TS types from lumi-API's full-api.yml into src/types/generated/.",
        parent="repo:web",
    ))
    # parent compound encodes belonging
    g.add_edge(Edge("web:kubb", "repo:lumi-api", "consumes_api",
                    label="reads full-api.yml"))


# --------------------------------------------------------------------------- #
# Cross-repo edges (auto-detected + curated)
# --------------------------------------------------------------------------- #
V2_IMPORT_PATTERNS = [
    re.compile(r"(?:from|import)\s+V2\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"['\"]Lumi-AI-Core\.V2\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"['\"]V2\.([A-Za-z_][A-Za-z0-9_]*)"),
]


def scan_monitor_v2_imports(g: Graph) -> None:
    """Edge: monitor → V2 module whenever the monitor imports from V2.X
    (statically or via importlib.import_module)."""
    monitors_dir = CONTINUOUS / "monitors"
    if not monitors_dir.exists():
        return
    for d in monitors_dir.iterdir():
        if not d.is_dir():
            continue
        monitor_id = f"monitors:{d.name}"
        seen: set[str] = set()
        for py in d.rglob("*.py"):
            try:
                src = py.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in V2_IMPORT_PATTERNS:
                for m in pat.finditer(src):
                    module = m.group(1)
                    if module in seen:
                        continue
                    seen.add(module)
                    g.add_edge(Edge(monitor_id, f"core:{module}",
                                    "imports", label="uses"))
        # Also scan custom-agent JSON templates which reference V2 modules by name
        # (this covers the dynamic-config use case)
        templates = CONTINUOUS / "agent_definition_templates"
        if templates.exists():
            for tpl in templates.glob(f"{d.name}*.json"):
                try:
                    txt = tpl.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for pat in V2_IMPORT_PATTERNS:
                    for m in pat.finditer(txt):
                        module = m.group(1)
                        if module not in seen:
                            seen.add(module)
                            g.add_edge(Edge(monitor_id, f"core:{module}",
                                            "imports", label="config-uses"))


# --------------------------------------------------------------------------- #
# Kafka topics
# --------------------------------------------------------------------------- #
TOPIC_VAR_RE = re.compile(r"([A-Z][A-Z0-9_]*_TOPIC)\b")
TOPIC_BLURBS = {
    "MONITOR_DATA_TOPIC": "Monitors publish structured detections / readings.",
    "ERROR_TOPIC": "Component error reports.",
    "PROTOCOL_ARBITER_COMMANDS_TOPIC": "External commands sent to arbiter (start, stop, advance).",
    "PROTOCOL_ARBITER_STATUS_TOPIC": "Arbiter publishes current protocol state.",
    "PROTOCOL_ARBITER_HISTORY_TOPIC": "Arbiter publishes append-only history of decisions.",
    "PROTOCOL_ARBITER_RESPONSES_TOPIC": "Arbiter responses to commands.",
    "AGENT_PROTOCOL_SYNC_TOPIC": "Custom-agent protocol sync heartbeat.",
    "AGENT_LIFECYCLE_COMMANDS_TOPIC": "Lifecycle commands for custom agents.",
    "AGENT_STATE_MANIFEST_COMMANDS_TOPIC": "State manifest commands for custom agents.",
    "AGENT_DEVICE_CONNECTIONS_TOPIC": "Device connection state events.",
    "AI_AGENT_RESULTS_TOPIC": "Custom agent results stream.",
}


def scan_kafka_topics(g: Graph) -> None:
    topics: dict[str, list[Path]] = {}
    for repo_root in (CONTINUOUS, CORE):
        if not repo_root.exists():
            continue
        for ext in ("*.py", "*.go"):
            for path in repo_root.rglob(ext):
                if any(part.startswith(".") for part in path.parts):
                    continue
                try:
                    src = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for var in set(TOPIC_VAR_RE.findall(src)):
                    topics.setdefault(var, []).append(path)

    for var, paths in topics.items():
        g.add_node(Node(
            id=f"topic:{var}", label=var,
            type="kafka-topic", repo="Lumi-AI-Continuous",
            file=str(paths[0].relative_to(WORKSHOP)) if paths else None,
            wiki="wiki/architecture/kafka-topics.md",
            summary=TOPIC_BLURBS.get(var, "Kafka topic."),
            color="#f59e0b",  # amber for topics
        ))
        # Naive direction inference: if the topic appears in a monitor file,
        # assume monitor → topic; arbiter → topic; etc.
        for p in paths:
            rel = p.relative_to(WORKSHOP).as_posix()
            if "/monitors/" in rel:
                monitor_name = rel.split("/monitors/", 1)[1].split("/", 1)[0]
                g.add_edge(Edge(f"monitors:{monitor_name}", f"topic:{var}",
                                "pubsub"))
            elif "/protocol_arbiter_v2/" in rel:
                g.add_edge(Edge("arbiter:v2", f"topic:{var}", "pubsub"))
            elif "/protocol_arbiter_v3/" in rel:
                g.add_edge(Edge("arbiter:v3", f"topic:{var}", "pubsub"))
            elif "/protocol_arbiter/" in rel:
                g.add_edge(Edge("arbiter:v1", f"topic:{var}", "pubsub"))
            elif "/monitor_relay/" in rel:
                g.add_edge(Edge("monitor_relay", f"topic:{var}", "pubsub"))


# --------------------------------------------------------------------------- #
# OpenAPI contracts
# --------------------------------------------------------------------------- #
def scan_openapi(g: Graph) -> None:
    api_dir = CONTINUOUS / "api"
    if not api_dir.exists():
        return
    for spec in api_dir.rglob("openapi.yaml"):
        rel_parts = spec.relative_to(api_dir).parts
        if not rel_parts:
            continue
        monitor = rel_parts[0]
        # Edge: monitor → contract (visible only as a tooltip; we don't add
        # a contract node, the OpenAPI file is implicit via the monitor's wiki).
        g.add_edge(Edge(f"monitors:{monitor}", f"monitors:{monitor}",
                        "openapi", label=str(spec.relative_to(WORKSHOP))))


# --------------------------------------------------------------------------- #
# Curated cross-repo bridges
# --------------------------------------------------------------------------- #
CURATED_EDGES: list[tuple[str, str, str, str]] = [
    # web ↔ backend high-value bridges
    ("web:api:aiAgents", "monitors:custom", "consumes_api", "drives custom_agent"),
    ("web:api:aiSingular", "monitors:dial", "consumes_api", "one-shot inference"),
    ("web:api:aiSingular", "monitors:object", "consumes_api", "one-shot inference"),
    ("web:route:protocol", "arbiter:v1", "depends_on", "v1 UI"),
    ("web:route:protocol", "arbiter:v2", "depends_on", "v2 UI"),
    ("web:route:device", "monitor_relay", "depends_on", "device CRUD"),
    ("web:route:experiment", "arbiter:v2", "depends_on", "live experiment status"),
    ("web:route:experiment", "topic:PROTOCOL_ARBITER_STATUS_TOPIC", "depends_on", "live status feed"),
    ("web:api:devices", "monitor_relay", "consumes_api", "device CRUD"),
    ("web:api:experiments", "arbiter:v2", "consumes_api", "experiment lifecycle"),
    ("web:api:protocols", "arbiter:v1", "consumes_api", "protocol CRUD"),
    ("web:api:protocols", "arbiter:v2", "consumes_api", "protocol CRUD"),
    # submodule
    ("repo:continuous", "repo:core", "submodule", "Lumi-AI-Core"),
]


def add_curated(g: Graph) -> None:
    for src, tgt, kind, label in CURATED_EDGES:
        g.add_edge(Edge(src, tgt, kind, label))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    g = Graph()
    add_anchors(g)
    scan_continuous(g)
    scan_core(g)
    scan_web(g)
    scan_monitor_v2_imports(g)
    scan_kafka_topics(g)
    scan_openapi(g)
    add_curated(g)

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "counts": {
                "nodes": len(g.nodes),
                "edges": len(g.edges),
                "by_type": _count_by(g.nodes, "type"),
                "by_repo": _count_by(g.nodes, "repo"),
            },
            "repo_colors": REPO_COLORS,
        },
        "nodes": [asdict(n) for n in g.nodes],
        "edges": [asdict(e) for e in g.edges],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    counts = payload["meta"]["counts"]
    print(f"Wrote {OUT.relative_to(ROOT)}: {counts['nodes']} nodes, "
          f"{counts['edges']} edges")
    print("  by type:", counts["by_type"])
    print("  by repo:", counts["by_repo"])


def _count_by(items: Iterable, attr: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for it in items:
        key = getattr(it, attr)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


if __name__ == "__main__":
    main()
