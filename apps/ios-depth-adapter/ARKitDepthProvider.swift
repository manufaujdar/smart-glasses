import ARKit
import CoreVideo

/// Immutable references to one ARKit scene-depth sample.
///
/// The host app should copy the pixel buffers if the frame needs to outlive
/// the ARSession callback. ARKit and LiDAR are platform capabilities, not
/// open-source dependencies, and are available only on supported devices.
public struct NativeDepthFrame {
    public let timestamp: TimeInterval
    public let depthMap: CVPixelBuffer
    public let confidenceMap: CVPixelBuffer?
    public let cameraIntrinsics: simd_float3x3
    public let sensorName: String
}

public final class ARKitDepthProvider: NSObject, ARSessionDelegate {
    public let session = ARSession()
    public private(set) var latest: NativeDepthFrame?

    public func start() throws {
        guard ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) else {
            throw NSError(domain: "Depthline.ARKit", code: 1, userInfo: [NSLocalizedDescriptionKey: "This device does not expose ARKit scene depth."])
        }
        let configuration = ARWorldTrackingConfiguration()
        configuration.frameSemantics.insert(.sceneDepth)
        session.delegate = self
        session.run(configuration)
    }

    public func pause() {
        session.pause()
        latest = nil
    }

    public func session(_ session: ARSession, didUpdate frame: ARFrame) {
        guard let sceneDepth = frame.sceneDepth else { return }
        latest = NativeDepthFrame(
            timestamp: frame.timestamp,
            depthMap: sceneDepth.depthMap,
            confidenceMap: sceneDepth.confidenceMap,
            cameraIntrinsics: frame.camera.intrinsics,
            sensorName: "ARKit sceneDepth"
        )
    }
}
