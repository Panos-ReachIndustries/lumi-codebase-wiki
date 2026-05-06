---
name: Repository Summaries
description: One card per Lumi repo — what it is, what to read first, where its docs live.
type: architecture
tags: [architecture, repos]
---

# Repository Summaries

Three repos cloned locally, plus a fourth (`lumi-API`) referenced but not in this checkout. Read [system-overview.md](system-overview.md) first to see how they fit together; this page is the concrete tour of each tree.

## Lumi-AI-Continuous

`Reach-Industries/Lumi-AI-Continuous` — Python + Go.

The runtime workhorse. A distributed AI monitoring platform that consumes live lab video, runs CV/ML monitors against it, and arbitrates protocols. Per its `Lumi-AI-Continuous/README.md`, it bundles ~13 monitor types, a Go relay that owns WebRTC and child-process supervision, and three side-by-side protocol-arbiter implementations.

**Day 1 directories:**

| Path | Purpose |
|------|---------|
| `monitor_relay/` | Go service. WebRTC ingress, GStreamer pipeline, spawns/supervises monitor subprocesses. |
| `monitors/` | One folder per AI capability (`colour`, `dial`, `hands`, `liquids/*`, `text`, `custom`, …). Each is a standalone Python process. |
| `protocol_arbiter/`, `protocol_arbiter_v2/`, `protocol_arbiter_v3/` | v1 (legacy stage/step/action), v2 (current default; flat instruction-IDs), v3 (domain-only, in progress). |
| `Common/` | Shared Python: `kafka_pool.py`, `resilience.py`, `profiling.py`, `resource_cleanup.py`. Imported by every monitor. |
| `Lumi-AI-Core/` | Empty submodule placeholder — the real Core is the sibling repo. Don't `git submodule update`. |
| `Docs/` | Repo-internal architecture, flowcharts, design docs. Linked from the README. |
| `agent_definition_templates/`, `protocols/`, `ledgers/` | Sample JSON for the custom-agent and arbiter. |

**Run locally:** `python run_dev.py` (spawns relay + arbiter with stdout prefixes), or `docker compose up -d --build` for the full stack. Monitor smoke: `python monitors/colour/colour.py --config configs/colour.json --is_local --video <path>`.

**Docs:** `Lumi-AI-Continuous/Docs/README.md` (architecture, flowcharts, guides) and `Lumi-AI-Continuous/docs/` (lower-case sibling). Top-level READMEs `MULTI_AGENT_REDESIGN.md` and `DEV_DOCKER_TESTING.md` are also worth reading once.

**Agent setup:** No `CLAUDE.md` at the repo root.

**Notable choices:** Python 3.11; Go 1.22 for the relay; OpenCV is built from source against GStreamer (see `Dockerfile.opencv`); each monitor gets its own Python venv inside the image to keep ML deps from colliding (see `Dockerfile.ai`); pre-commit runs `isort` + `flake8` (134 col).

## Lumi-AI-Core

`Reach-Industries/Lumi-AI-Core` — Python.

The CV/ML class libraries. Per `Lumi-AI-Core/README.md`: V2-only — every module lives under `V2/`. Lumi-AI-Continuous imports these modules; nothing in Core knows about Kafka, monitors, or arbiters.

**Day 1 directories:**

| Path | Purpose |
|------|---------|
| `V2/BasicOps/`, `V2/Utils/`, `V2/ModelInference/` | Infrastructure used everywhere. |
| `V2/Detection/`, `V2/Tracking/`, `V2/SegmentAnything/` | Vision primitives. |
| `V2/Vessels/`, `V2/Pipetting/`, `V2/LabContainerTracking/`, `V2/WellPlate/` | Task-specific lab logic. |
| `V2/Machine/Text/`, `V2/Machine/GaugeReader/`, `V2/Machine/Screens/` | Instrument-reading modules. |
| `weights/` | Model checkpoints baked into the AI image at build time. |
| `agreedDataSchema.md` | The contract between modules — read this before adding a new one. |

**Run locally:** No "app" to run. Tests via Docker: `docker compose -f docker-compose.pytest.yml run --rm test-runner` (full suite ≈30 min on first build), or `-e PYTEST_ARGS="V2/CameraViewAnalyzer"` for a subset.

**Docs:** Per-module `V2/<Module>/README.md` files. `agreedDataSchema.md` for the cross-module contract.

**Agent setup:** No `CLAUDE.md`.

**Notable choices:** Python 3.11; numpy pinned `<2`; CPU-only torch (`torch==2.1.0`) to keep CI runners cheap; mmcv 2.1.0 from openmmlab CDN; mediapipe 0.10.21 forces protobuf 4.x.

## lumi-web-v2

`Reach-Industries/lumi-web-v2` — TypeScript.

The web app. Next.js 15 (App Router, Turbopack), React 19, Tailwind v4, shadcn/ui. Per `lumi-web-v2/CLAUDE.md` and `README.md`: it's the operator UI for device management, experiment tracking, and live video monitoring. Talks to `lumi-API` over HTTPS + WSS — never to Kafka directly.

**Day 1 directories:**

| Path | Purpose |
|------|---------|
| `src/app/(authenticated)/`, `src/app/(public)/` | Next.js routes (38 total). |
| `src/api/<domain>/` | TanStack Query hooks. 16 domains: `devices`, `experiments`, `protocols`, `aiAgents`, `aiSingular`, `imageMoments`, `notebook`, `organisation`, `projects`, `records`, `user`, `workspaces`, … |
| `src/components/ui/` | shadcn/ui primitives. Storybook on `:6006`. |
| `src/types/generated/` | **Generated** by Kubb from the OpenAPI spec. Don't hand-edit. |
| `src/consts/gatewayRoutes.ts` | Single source of truth for API paths — always import from here, never inline. |
| `docs/` | Repo guides (agentic-development, mocks, releasing, type-generation, testing, styling, responsive, analytics). |
| `test/` | Playwright E2E suites. |

**Run locally:** `nvm use 22 && yarn install && yarn dev` (HTTPS, Turbopack). `yarn use-env dev|mocks` swaps `.env.local` between gateway-dev and the local mocks server. `yarn generate-api-types` regenerates types after the OpenAPI spec changes.

**Docs:** `lumi-web-v2/docs/` covers everything operational. Top-level `README.md` for setup.

**Agent setup:** `lumi-web-v2/CLAUDE.md` exists and is the most thorough of the three — read it before touching this repo.

**Notable choices:** Yarn 4 via Corepack (do **not** install Yarn through npm); Node 22 strictly; Tailwind v4; **Kubb** codegen reading `../lumi-API/src/output/full-api.yml`; Husky pre-commit (`npx lint-staged`) + pre-push (`yarn knip || true && yarn build && yarn test`); ESLint + Prettier + simple-import-sort.

## lumi-API (external) — `repo:lumi-api`

Not cloned in this checkout. The HTTPS + WSS gateway between the Kafka-side runtime and the web app. lumi-web-v2's Kubb config (`kubb.config.ts`) reads its OpenAPI spec from `../lumi-API/src/output/full-api.yml` — so if you regenerate types, you need lumi-API as a sibling directory. Appears in the wiki graph as a greyed-out node `repo:lumi-api`. See [system-overview.md](system-overview.md) for where it sits in the data flow.
