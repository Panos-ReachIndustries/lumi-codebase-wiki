---
name: Deployment
description: Docker, CI/CD, and deploy targets across the three Lumi repos.
type: architecture
tags: [architecture, deployment, docker, ci]
---

# Deployment

Three repos, one deploy target (AWS ECR), Docker everywhere. This page is the practical map: what each Dockerfile builds, what each compose stack runs, what each workflow triggers, and where the actual deploy goes. Cross-link: [system-overview.md](system-overview.md), [repos.md](repos.md), [kafka-topics.md](kafka-topics.md).

## Containers

| Image | What it builds | When used |
|-------|----------------|-----------|
| `Lumi-AI-Continuous/Dockerfile` | Ubuntu 22.04 base; builds OpenCV from source against GStreamer; per-monitor virtualenvs (`/src/base`, `/src/colour`, `/src/liquids`, `/src/text`, `/src/dial`, `/src/hands`, `/src/detector`); Go relay binary; weights from `reach-ml-weights` S3. Entrypoint: `monitor_relay`. | Original monolithic image. Largely superseded by the `opencv` + `app` + `ai` split below. |
| `Lumi-AI-Continuous/Dockerfile.opencv` | Stage 0/1/2: Debian 12 base → builds an OpenCV-with-GStreamer wheel → installs it into a clean runtime layer. Tagged `opencv-base:latest`. | Cached base image consumed by `Dockerfile.ai`. |
| `Lumi-AI-Continuous/Dockerfile.app` | Multi-stage Go build (golang:1.25.7-bookworm) → `FROM scratch` final containing just the `monitor_relay` binary. Uses `LUMI_GO_LIBS_PAT` build-arg for private modules. | Cached base image consumed by `Dockerfile.ai`. |
| `Lumi-AI-Continuous/Dockerfile.ai` | Composes `opencv-base` + `app-base`. Two venvs: `base` (light: arbiter, colour, homogeneity) and `ml` (everything else — Paddle/Mediapipe/Detection/Vessels/CodeReaders/Tracking/Pipetting/GridTracker/MMOCR). Patches mmocr and mmengine on the way through. Bakes weights and source. Entrypoint: `monitor_relay`. | The production AI image. |
| `Lumi-AI-Continuous/Dockerfile.relay` | python:3.11-slim with GStreamer; runs `tests/services/relay/app.py`. | Local-dev relay stub used by `docker-compose.dev.yml`. |
| `Lumi-AI-Continuous/Dockerfile.relay-e2e` | Two-stage golang:1.25.7 → debian:12-slim. Builds `monitor_relay` + `fake_agent`. Target ~200 MB. | E2E tests — relay against a fake CVM agent over UDP. |
| `Lumi-AI-Continuous/Dockerfile.dev` | python:3.11-slim with GStreamer + `Common/` deps + headless OpenCV + CPU torch. | Local-dev container for relay/frontend in `docker-compose.dev.yml`. |
| `Lumi-AI-Continuous/Dockerfile.pytest` | python:3.11-slim, repo-level test deps only, mocks Lumi-AI-Core via root `conftest.py`. | Repo-level pytest in CI and locally. |
| `Lumi-AI-Core/Dockerfile` | python:3.11-slim-bookworm; CPU torch 2.1.0; mediapipe, mmcv 2.1.0, mmdet, mmpose; bind-mounts every `V2/**/requirements.txt` and installs them. | Lumi-AI-Core test runner. |
| `lumi-web-v2/Dockerfile` | node:22.14-slim + Corepack/Yarn 4. `yarn install && yarn build` with ~20 `NEXT_PUBLIC_*` build-args (gateway URLs, feature flags). Runs `yarn start`. | Production web image. |
| `lumi-web-v2/Dockerfile.checks` | node:22.14-slim + Yarn deps + Playwright Chrome. | CI quality-checks container; runs `scripts/quality_checks.sh`. |

## Compose stacks

| File | Purpose |
|------|---------|
| `Lumi-AI-Continuous/docker-compose.yml` | Builds `opencv-base` then the AI image (linux/amd64). Minimal — just the base build graph. |
| `Lumi-AI-Continuous/docker-compose.dev.yml` | Full local dev: KRaft Kafka (`confluentinc/cp-kafka:7.5.0`), `relay` container (with stubbed services), and `frontend` running `run_field_viewer.py`. Sets `IS_LOCAL=true`, mounts the repo into `/app`, wires all `*_TOPIC` env vars. |
| `Lumi-AI-Continuous/docker-compose.test.yml` | Builds opencv → app → ai-core, runs `colour_monitor` against a mounted `configs/colour.json` with `IS_LOCAL` semantics. Smoke test for the production image. |
| `Lumi-AI-Continuous/docker-compose.pytest.yml` | Repo-level pytest (no submodule). 2 CPU / 2 GB cap. Defaults `PYTEST_ARGS` to every monitor + `Common` + `protocol_arbiter_v2`. |
| `Lumi-AI-Core/docker-compose.pytest.yml` | Full V2 test runner. 2 CPU / 4 GB. Override `PYTEST_ARGS` for subsets (`V2/CameraViewAnalyzer`) or rerun-failed (`--lf`). |
| `lumi-web-v2/docker-compose.yml` | Single `ci` service running `Dockerfile.checks` + `scripts/quality_checks.sh` against mocks URLs. |

## CI

**Lumi-AI-Continuous/.github/workflows/**

- `ci.yml` — on PR/push to `dev`/`main`. Three jobs: `Python_Linter` (flake8 on changed files), `Python_Tests` (matrix on Python 3.11; computes test paths from changed files), `Monitor_Schema_Validation` (`scripts/validate_monitor_schemas.py`).
- `deploy.yml` — `workflow_call` only. Jobs: `validate-env` → `build-opencv` → `build-go-apps` → `build-ai`. Each pushes to ECR via OIDC. Required secrets: `LUMI_AI_CORE_PAT`, `LUMI_GO_LIBS_PAT`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.
- `trigger_dev.yml` — on push to `dev`, calls `deploy.yml` with `environment: dev`.
- `trigger_main.yml` — on push to `main`, calls `deploy.yml` with `environment: prod`.

**Lumi-AI-Core/.github/workflows/**

- `ci.yml` — PR + `workflow_dispatch`. Two jobs: `Python_Linter` (flake8 on changed `.py`) and `Tests` (Python 3.11). No deploy workflow — Lumi-AI-Core ships as source consumed by Lumi-AI-Continuous.

**lumi-web-v2/.github/workflows/**

- `ci_checks.yml` — reusable. Runs lint, prettier-check, jest, type-check, `yarn npm audit`. Mocks gateway URLs in env.
- `trigger_pr.yml` — on PR to `dev`, calls `ci_checks.yml`.
- `deploy_dev.yml` — on push to `dev`. Runs CI then builds + pushes `lumi-dev/web2` to ECR with dev-flavoured `NEXT_PUBLIC_*` build-args.
- `deploy_main.yml` — on push to `main`. Same shape, pushes `lumi-prod/web2`.
- `dependency_audit.yml` — Mondays 09:00 UTC + manual. `yarn npm audit --severity high`.
- `publish-storybook.yml` — on PRs labelled `Chromatic`.

## Deploy targets

Per `Lumi-AI-Continuous/.github/DEPLOY-GITHUB-SETUP.md` and the `deploy_*` workflows in lumi-web-v2:

- **Registry:** AWS ECR at `116931054135.dkr.ecr.eu-west-2.amazonaws.com`, region `eu-west-2`.
- **Auth:** GitHub OIDC → `arn:aws:iam::116931054135:role/GitHubActionsECRRole`.
- **Image namespaces:** `lumi-dev/*` for `dev` branch, `lumi-prod/*` for `main`. Sub-images: `opencv`, `go-apps`, `ai`, `web2`.
- **Runtime target:** Not specified in the workflow files — they push images and stop. ECS / Kubernetes pull-and-deploy is **unclear from the workflow files alone**; check the infra repo (not in this checkout) for the consumer side.

## Local dev paths

| Repo | Command |
|------|---------|
| Lumi-AI-Continuous | `python run_dev.py` (relay + arbiter, prefixed stdout). For full Kafka: `docker compose -f docker-compose.dev.yml up`. |
| Lumi-AI-Core | `docker compose -f docker-compose.pytest.yml run --rm test-runner` (or `-e PYTEST_ARGS="V2/<Module>"`). |
| lumi-web-v2 | `nvm use 22 && yarn install && yarn dev`. Switch envs with `yarn use-env dev|mocks`. |

## Pre-commit / hooks

- **Lumi-AI-Continuous/.pre-commit-config.yaml** and **Lumi-AI-Core/.pre-commit-config.yaml** — identical: `pre-commit-hooks` (trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files), `isort 5.13.2`, `flake8 7.0.0` with `--max-line-length=134`. Install once with `pip install pre-commit && pre-commit install`.
- **lumi-web-v2/.husky/** — `pre-commit` runs `npx lint-staged`; `pre-push` runs `yarn knip || true && yarn build && yarn test`; `post-checkout` and `post-merge` also exist. Per `lumi-web-v2/CLAUDE.md`: do **not** create commits unless explicitly asked — leave that to the developer.

## CD freeze / safety notes

- Pushes to `dev` and `main` deploy automatically (`trigger_dev.yml`, `trigger_main.yml`, `deploy_dev.yml`, `deploy_main.yml`). Treat both branches as protected; if you need to land code without shipping it, merge into a feature branch first and let the PR-checks workflow gate it.
- The Lumi-AI-Continuous deploy is sequential (`build-opencv → build-go-apps → build-ai`) and the AI build is heavy — expect 30–60 minutes end-to-end and don't stack pushes on top of each other.
- `Lumi-AI-Continuous/Lumi-AI-Core/` is an empty submodule placeholder. Don't `git submodule update` unless you actually want to re-pin to a commit; the deploy workflow does its own checkout with `submodules: recursive` and `LUMI_AI_CORE_PAT`.
