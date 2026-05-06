---
name: V2.Visualiser
description: A Flask-based web debugger that renders pipeline outputs (detections, tracks, poses, polygons, masks) live in a browser. Used heavily by the custom agent.
type: module
graph_node: core:Visualiser
sources:
  - { repo: Lumi-AI-Core, path: V2/Visualiser/WebViewer.py }
  - { repo: Lumi-AI-Core, path: V2/Visualiser/visualisation_handler.py }
  - { repo: Lumi-AI-Core, path: V2/Visualiser/visualisation_utils.py }
tags: [v2-module]
---

# V2.Visualiser

`Visualiser` is the V2 module that turns a black-box pipeline into a web page you can stare at while it runs. It is the debugging surface most engineers reach for first when a custom-agent pipeline misbehaves — open `http://localhost:5000`, watch frames + a sidebar of events.

## What it does

Two pieces:

- **`WebViewer`** (`Lumi-AI-Core/V2/Visualiser/WebViewer.py:1`) — a Flask server that streams frames as MJPEG, with a side panel for colour-coded log entries (info / warning / error / success). Optional Kafka subscription (`confluent_kafka`) lets it consume frames from a topic instead of an in-process source. It also tries to import `MultiSourceCapture` from the root `Common` module for multi-camera setups.
- **`VisualisationUtils`** (`visualisation_utils.py`) — pure drawing helpers: `draw_object_detections`, `draw_text_regions`, `draw_polygons`, `draw_depth_map`, `draw_segmentation_masks`, `draw_human_pose`, `draw_hand_landmarks`. Each takes a dict `{"frame", ...method-specific keys}` and returns `{"frame": annotated}` or an error dict.

`visualisation_handler.py` defines `VisualisationHandler` (`Lumi-AI-Core/V2/Visualiser/visualisation_handler.py:7`) and per-output-type subclasses (`DetectionsVisualisationHandler`, `TracksVisualisationHandler`, `HandPoseVisualisationHandler`, `PolygonVisualisationHandler`, `DepthMapVisualisationHandler`, `SegmentationVisualisationHandler`, `GestureTextVisualisationHandler`). Each handler tells `WebViewer` "I can draw this block's output" via `block_output_matches_handler`, then `visualise_block_output` does the actual annotation.

## Public API

- `WebViewer(port=5000, title=..., max_logs=100)` then `.start()`.
- `viewer.visualize_agent_outputs(frame, agent_outputs, frame_count=None)` — main entry point during a pipeline loop; matches outputs to handlers automatically.
- `viewer.update_frame(frame)`, `viewer.add_log(message, level)`.
- `VisualisationUtils.draw_*({"frame", ...})` — call directly when you don't need the web server.

## Input / output

In: a BGR `np.ndarray` frame plus a list of "block outputs" (the dict each pipeline step emits). Out: an annotated frame (returned and pushed to the browser) plus log entries.

## Dependencies on other V2 modules

- None *required* on the import path — handlers consume the agreed output shapes documented in [agreedDataSchema.md](../data-schema.md), so it indirectly depends on whatever module produced those.
- External: `flask`, `opencv-python`, `numpy`, optional `confluent-kafka`.

## Used by

The **custom agent** in Lumi-AI-Continuous (`Lumi-AI-Continuous/monitors/custom/custom_agent.py`) and its tests (`test_custom_agent.py`, `test_kafka_publish_filter.py`, `test_webviewer_standalone.py` in `protocol_arbiter/Testing/`). Whenever someone wires up a new pipeline JSON, this is what they point at to see frames.

## Tests

- `Lumi-AI-Core/V2/Visualiser/test_visualiser.py`

## Gotchas

- The Common-module import dance at the top of `WebViewer.py:30` is real — `MultiSourceCapture` lives in the *root-level* `Common`, not `Lumi-AI-Core/Common`. If you see "MultiSourceCapture not found", check your `sys.path`.
- Kafka support is optional; if `confluent_kafka` isn't installed, the import is silently skipped and Kafka subscription disabled.
- Drawing helpers expect specific keys (`detections`, `polygonDetections`, `handPoseLandmarks`, etc.) — feeding the wrong key returns an error dict rather than raising.

## See also

- [V2.Detection](Detection.md) — what `DetectionsVisualisationHandler` consumes
- [V2.Tracking](Tracking.md) — what `TracksVisualisationHandler` consumes
- [agreedDataSchema.md](../data-schema.md)
