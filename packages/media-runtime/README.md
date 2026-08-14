# Media runtime

Dependency-free low-latency media primitives for the research prototype.

- `BoundedFrameBuffer` prevents stale-frame buildup.
- `ImageQualityAnalyzer` provides bounded luma-based transport indicators.
- `LiveVideoSession` applies a quality gate and publishes through an injected
  `FrameSink`.
- Frame envelopes are size-bounded and stale/out-of-order sequences are
  rejected before queueing.
- `LatencyController` selects a low-latency, balanced, or detail profile from
  queue depth, RTT, drops, and source quality.

The default sink is synthetic. Add a reviewed WebRTC/LiveKit adapter for real
streaming; do not put credentials, raw captures, or patient data in tests.
