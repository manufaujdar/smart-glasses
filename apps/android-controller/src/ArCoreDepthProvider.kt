package com.smartglasses.depth

import com.google.ar.core.Frame
import com.google.ar.core.Session
import java.nio.ByteOrder

/**
 * Small ARCore boundary for true depth frames.
 *
 * The app must configure ARCore with DepthMode.AUTOMATIC after checking
 * isDepthModeSupported. The returned Image is owned by the caller and must be
 * closed promptly (for example with use { ... }). Values in a DEPTH16 image
 * are millimetres. This file is an integration seam, not a complete Android
 * app or a clinical measurement implementation.
 */
data class NativeDepthFrame(
    val timestampNs: Long,
    val width: Int,
    val height: Int,
    val depthMm: ShortArray,
    val focalLengthX: Float,
    val focalLengthY: Float,
    val principalPointX: Float,
    val principalPointY: Float,
    val sensorName: String = "ARCore Depth API",
)

class ArCoreDepthProvider(private val session: Session) {
    fun isSupported(): Boolean = session.isDepthModeSupported(com.google.ar.core.Config.DepthMode.AUTOMATIC)

    /**
     * Reads one frame. Returns null when ARCore has not produced a valid depth
     * image yet. The caller should invoke this from the AR frame loop.
     */
    fun read(frame: Frame): NativeDepthFrame? {
        if (!isSupported()) return null
        return try {
            frame.acquireDepthImage16Bits().use { image ->
                val buffer = image.planes[0].buffer.order(ByteOrder.nativeOrder()).asShortBuffer()
                val values = ShortArray(image.width * image.height)
                buffer.get(values)
                val intrinsics = frame.camera.imageIntrinsics
                NativeDepthFrame(
                    timestampNs = frame.timestamp,
                    width = image.width,
                    height = image.height,
                    depthMm = values,
                    focalLengthX = intrinsics.focalLength[0],
                    focalLengthY = intrinsics.focalLength[1],
                    principalPointX = intrinsics.principalPoint[0],
                    principalPointY = intrinsics.principalPoint[1],
                )
            }
        } catch (_: com.google.ar.core.exceptions.NotYetAvailableException) {
            null
        }
    }
}
