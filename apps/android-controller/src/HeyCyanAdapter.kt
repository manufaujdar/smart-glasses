package health.smartglasses.heycyan

import health.smartglasses.device.*

/**
 * Clean adapter around a separately licensed vendor SDK.
 * This class contains no proprietary packet data or copied implementation.
 */
class HeyCyanAdapter(private val vendor: HeyCyanVendorApi) : DeviceDriver {
    override val driverId = "heycyan-licensed-sdk"

    override suspend fun discover(timeoutMillis: Long) = vendor.scan(timeoutMillis)

    override suspend fun connect(deviceId: String): DeviceSnapshot {
        vendor.connect(deviceId)
        val info = vendor.readStatus()
        return DeviceSnapshot(
            deviceId = deviceId,
            connected = true,
            batteryPercent = info.batteryPercent,
            firmwareVersion = info.firmwareVersion,
            capabilities = setOf(
                "device.battery", "device.version", "camera.photo", "camera.video",
                "audio.recording", "media.list", "media.transfer"
            ),
        )
    }

    override suspend fun disconnect() = vendor.disconnect()

    override suspend fun execute(command: DeviceCommand): DeviceResult = try {
        when (command.name) {
            "device.get_battery" -> DeviceResult.Success(command.id, "device.battery", mapOf("level" to vendor.battery().toString()))
            "camera.take_photo" -> DeviceResult.Success(command.id, "camera.photo_requested", mapOf("request" to vendor.takePhoto()))
            "camera.start_video" -> { vendor.startVideo(); DeviceResult.Success(command.id, "camera.video_started") }
            "camera.stop_video" -> { vendor.stopVideo(); DeviceResult.Success(command.id, "camera.video_stopped") }
            "audio.start_recording" -> { vendor.startAudio(); DeviceResult.Success(command.id, "audio.recording_started") }
            "audio.stop_recording" -> { vendor.stopAudio(); DeviceResult.Success(command.id, "audio.recording_stopped") }
            else -> DeviceResult.Rejected(command.id, "unsupported_command")
        }
    } catch (error: Exception) {
        DeviceResult.Unknown(command.id, error.message ?: "vendor_sdk_error")
    }
}

/** Implement this interface in the licensed-SDK module only. */
interface HeyCyanVendorApi {
    suspend fun scan(timeoutMillis: Long): List<DiscoveredDevice>
    suspend fun connect(deviceId: String)
    suspend fun disconnect()
    suspend fun readStatus(): HeyCyanStatus
    suspend fun battery(): Int
    suspend fun takePhoto(): String
    suspend fun startVideo()
    suspend fun stopVideo()
    suspend fun startAudio()
    suspend fun stopAudio()
}

data class HeyCyanStatus(val batteryPercent: Int?, val firmwareVersion: String?)

