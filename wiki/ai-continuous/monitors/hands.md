---
name: hands monitor
description: Per-frame hand pose detection via MediaPipe — landmarks, handedness, no cross-frame tracking.
type: monitor
graph_node: monitors:hands
sources:
  - { repo: Lumi-AI-Continuous, path: monitors/hands/hand_tracker.py }
  - { repo: Lumi-AI-Core, path: V2/ModelInference/Models/Pose/Mediapipe/MediapipePoseInference.py }
tags: [monitor]
---

# hands monitor

The `hands` monitor publishes hand pose landmarks for every frame using MediaPipe via `V2.ModelInference.Models.Pose.Mediapipe.MediapipePoseInference.detect_hand_pose`. Despite the entry file being named `hand_tracker.py`, it does **not** track identity across frames — each frame is processed independently and hands are keyed by their index in the MediaPipe response (`hand_tracker.py:204-211`). For identity-stable tracking you need a downstream consumer.

It feeds gesture-aware monitors and arbiters that need to know "is a hand near the vessel right now?" or "did a pipette interaction happen?".

## Where the code lives

- **Process entry:** `Lumi-AI-Continuous/monitors/hands/hand_tracker.py`
- **Per-frame call:** `hand_tracker.py:196` (`pose_inference.detect_hand_pose({"frame": frame})`)
- **Tests:** `Lumi-AI-Continuous/monitors/hands/test_hand_tracker.py`

## How it runs

```bash
# Local
python monitors/hands/hand_tracker.py --config path/to/config.json --is_local

# Production
python monitors/hands/hand_tracker.py --config path/to/config.json
```

## Inputs

- Standard `monitorId`, `pipeline`, `connection.resolution_h/_w`.
- `args.ai.conf` (default `0.1`) — used as both `minDetectionConfidence` and `minTrackingConfidence` (`hand_tracker.py:130, 137`).
- `args.ai.num_hands` (default `4`) — clamped to MediaPipe's supported range `[1, 2]` (`hand_tracker.py:139`). Note the public knob says 4 but only up to 2 hands are ever returned.
- Archive-mode timestamps (`startTimestamp` / `processFromTimestamp` / `processToTimestamp`) supported.

## Outputs

Per frame, via `HandTrackerStreamReporter.data(...)` (`hand_tracker.py:212`):

```json
{
  "streamOffline": false,
  "hands": {
    "0": {
      "landmarks": [{"x": 0.41, "y": 0.62, "z": -0.02, "visibility": 0.9}, ...],
      "last_seen": 142,
      "handedness": "Left",
      "confidence": 0.94
    }
  }
}
```

`last_seen` is the local frame counter — useful as a recency marker only, not as a persistent track id. On V2 errors the payload becomes `{"hands": {}}` and an error is reported (`hand_tracker.py:197-199`).

## V2 modules used

- [V2.ModelInference](../../ai-core/modules/ModelInference.md) — `Models.Pose.Mediapipe.MediapipePoseInference`.

## Common utilities used

- `Common.common.StreamCapture` / `LocalStreamCapture`
- `Common.common.HandTrackerStreamReporter`

## Kafka topics published

- [`MONITOR_DATA_TOPIC`](../../architecture/kafka-topics.md)

## Tests

- `Lumi-AI-Continuous/monitors/hands/test_hand_tracker.py`

## When it goes wrong

- **`"hands": {}` every frame** — confidence threshold too high or the operator is wearing gloves that confuse MediaPipe; try lowering `ai.conf`.
- **Indices flip between frames** — expected: there is no tracker. Don't rely on `0` always meaning the same hand.
- **`num_hands: 4` doesn't return 4 hands** — MediaPipe's `maxNumHands` is silently capped at 2 by the clamp.
- **Detected landmarks land outside the frame** — MediaPipe returns normalised `[0..1]` coordinates; multiply by frame size in the consumer.
- **Process exits with `Failed to initialise hand tracker`** — `MediapipePoseInference` couldn't load; usually a missing MediaPipe install in the runtime image.

## See also

- [V2.ModelInference](../../ai-core/modules/ModelInference.md)
- [V2.Gestures](../../ai-core/modules/Gestures.md) — typical downstream consumer.
- [Kafka topics](../../architecture/kafka-topics.md)
- [monitor_relay](../monitor-relay.md)
