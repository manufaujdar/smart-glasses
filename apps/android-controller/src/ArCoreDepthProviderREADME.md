# ARCore depth boundary

`ArCoreDepthProvider.kt` is the native Android adapter for true depth. It
requires an Android project with the licensed Google ARCore dependency and a
runtime permission flow owned by the host app. ARCore depth is device-dependent,
disabled until configured, and may combine motion-derived depth with hardware
depth. The host must check support, guide the operator through a stable capture,
record calibration metadata, and reject frames with insufficient coverage.

Do not treat an ARCore frame as clinically accurate just because it is a native
depth frame. Compare the sensor against a traceable phantom and an independent
reference before using it for research validation.
