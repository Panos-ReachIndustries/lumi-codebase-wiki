---
name: Common
description: "Shared Python utilities every monitor and arbiter depends on: stream capture, reporters, Kafka pool, resilience, profiling."
type: common-util
graph_node: common:common
sources:
  - { repo: Lumi-AI-Continuous, path: Common/common.py }
  - { repo: Lumi-AI-Continuous, path: Common/kafka_pool.py }
  - { repo: Lumi-AI-Continuous, path: Common/profiling.py }
  - { repo: Lumi-AI-Continuous, path: Common/resilience.py }
  - { repo: Lumi-AI-Continuous, path: Common/resource_cleanup.py }
tags: [common, util, foundation]
---

# Common

`Common/` is the shared Python foundation for everything in Lumi-AI-Continuous: every monitor, every arbiter, the custom-agent runtime. Five modules, all `Lumi-AI-Continuous/Common/`. Most code you'll touch in this repo subclasses `StreamReporter`, opens a `StreamCapture`, and goes through `kafka_pool` or `resilience` for I/O. Treat this folder as the platform layer — read it once, then trust it.

The graph generator emits one node per file (`common:common`, `common:kafka_pool`, etc.) but they all point to this single page.

## `common.py` — the big one

Stream capture, reporters, error reporting, numpy/cv2 helpers. The base class for every monitor.

### `StreamReporter` (`common.py:171`)

Abstract base class. A monitor instantiates a subclass like `ColourStreamReporter` or `LiquidStreamReporter` and calls `.data(payload)` once per frame. The reporter:

- Throttles output via `force_transmit_interval` (always emit every N seconds) and `changed_data_interval` (emit when payload actually changes).
- Optionally batches and publishes to Kafka via the connection pool (`common.py:204-217`); falls back to stdout `DATA:` lines that [monitor_relay](monitor-relay.md) parses.
- Supports an "archive timeline" for replaying recorded experiments — every reported timestamp gets remapped onto a synthetic timeline anchored on the first processed frame.
- Owns `enable_print` (stdout mode for local dev) and `enable_kafka` (production mode).

Concrete subclasses (`common.py:619-1503`) each override `_data_changed(old, new)` with their domain-specific equality: `ColourStreamReporter` compares dominant colours, `GaugeStreamReporter` compares numeric readings, `LiquidStreamReporter` does field-level comparison and logging, `AnonymiserStreamReporter` does cheap polygon-count comparison, etc. Pick whichever matches your monitor's payload shape.

`ErrorReporter` (`common.py:1692`) is the lightweight cousin — just `produce_error(source, message, severity, additional_info, stacktrace)`, which prints `ERROR:<ts>:<json>` for the relay to forward to `OHDEAR_TOPIC`.

### Stream capture (`common.py:676-1047`)

- `StreamCapture(pipeline, resolution)` — opens a live GStreamer pipeline via OpenCV's `cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)`. Background threads handle reconnection (3-second retry loop) and frame storage. Call `.read()` for `(frame, is_new)`.
- `LocalStreamCapture` — same interface, but reads from a local video file with configurable frame rate, looping, and seek. Used by `--is_local` mode and tests.
- `MultiSourceCapture` — coordinates several capture sources and returns synchronised frame bundles (the multi-camera fleet path).

The default pipeline string at the top of the file (`common.py:20`) — `udpsrc timeout=2000000 ! ... ! appsink` — is the matching half of the `udpsink` that [monitor_relay](monitor-relay.md) builds. Same UDP port both sides; the relay assigns it.

### Numpy / cv2 helpers

`NumpyEncoder`, `convert_numpy_types`, `mask_to_polygons`, `polygons_to_mask`, `_aspect_aware_resize`. Boring but everywhere — anywhere a monitor returns a binary mask, it's been through `mask_to_polygons` first.

### Config helpers (`common.py:1505-1691`)

`load_monitor_config`, `validate_config_structure`, `parse_archive_timestamps`, `create_capture_from_config`. The boilerplate every monitor's `main()` opens with — read the colour monitor for the canonical sequence.

## `kafka_pool.py` — Kafka producer/consumer pooling

```python
from Common.kafka_pool import get_kafka_producer, get_kafka_consumer
```

A process-global pool keyed by `(bootstrap, security_protocol)` for producers and `(bootstrap, group_id, security_protocol)` for consumers (`kafka_pool.py:25-34`). Without this every monitor that emits via Kafka would open its own connection — at fleet scale that exhausts MSK file descriptors fast. `close_all_connections()` flushes and closes everything atexit; `remove_producer` / `remove_consumer` evict broken entries.

Production producer settings live at `kafka_pool.py:57-65` (16 KB batches, 10 ms linger, 100k message in-flight queue).

## `profiling.py` — phase markers for boot timing

```python
from Common.profiling import phase_marker
phase_marker("started")
# ... heavy imports ...
phase_marker("imports_done")
```

Stdlib-only (`profiling.py:30-32`). Each call writes one line `METRICS:<json>` to stdout with phase name, monotonic timestamp, RSS, peak RSS, user/system CPU. The relay's CVM listener filters on the `METRICS:` prefix — see `parseMonitorLogLineAndWriteToMSK` in [monitor_relay](monitor-relay.md). Used by [arbiter v2](arbiters/v2.md) (`arbiter_v2.py:24-27`) and the custom agent to time slow boot phases.

## `resilience.py` — retry / backoff / circuit breaker

`CircuitBreaker` (`resilience.py:25`) with three states (`CLOSED` / `OPEN` / `HALF_OPEN`), thread-safe via an internal lock. Used to wrap S3 and Kafka calls so that a flapping AWS dependency doesn't lock up the arbiter.

Pre-configured singletons:

- `get_s3_circuit_breaker()` — used by the arbiter historians (`protocol_arbiter/historian.py:55-72`).
- `get_kafka_circuit_breaker()` — used by reporters when Kafka init fails.

`retry_with_backoff` is a decorator for one-shot retryable operations.

## `resource_cleanup.py` — temp files and graceful shutdown

`register_temp_file(path)` adds a path to a process-global set; an `atexit` handler removes everything in that set on exit (`resource_cleanup.py:45-64`). `TempFileContext` is the per-call context-manager equivalent. Why it matters: monitors and arbiters write screenshot scratch under `/tmp/`, and OOM-killing or `kill -9` would otherwise leave terabytes behind across a fleet.

## Tests

- `Common/test_common.py` — reporter throttling, stream capture frame loop, helper functions.
- `Common/test_profiling.py` — phase marker line shape.

Run with `pytest Common/ -q`.

## See also

- [colour monitor](monitors/colour.md) — the canonical consumer of `StreamReporter` + `StreamCapture`.
- [monitor_relay](monitor-relay.md) — parses the stdout these reporters produce.
- [V2 arbiter](arbiters/v2.md) — uses `phase_marker`, `ErrorReporter`, and the S3 circuit breaker.
- `Common/Readme.md` — the per-module table reference.
