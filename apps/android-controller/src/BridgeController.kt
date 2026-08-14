package health.smartglasses.bridge

import health.smartglasses.device.DeviceCommand
import health.smartglasses.device.DeviceDriver
import health.smartglasses.device.DeviceResult

/**
 * Transport-neutral controller for the local `/bridge/v1` HTTP wrapper.
 * An Android host supplies authentication, JSON serialization, TLS/network
 * policy, lifecycle ownership, and the separately licensed vendor binding.
 */
class BridgeController(private val driver: DeviceDriver) {
    suspend fun connect(commandId: String, deviceId: String?): DeviceResult {
        if (deviceId.isNullOrBlank()) return DeviceResult.Rejected(commandId, "device_id_required")
        return try {
            val snapshot = driver.connect(deviceId)
            DeviceResult.Success(
                commandId,
                "device.connected",
                mapOf(
                    "device_id" to snapshot.deviceId,
                    "capabilities" to snapshot.capabilities.sorted().joinToString(","),
                    "battery" to (snapshot.batteryPercent?.toString() ?: "unknown"),
                    "firmware" to (snapshot.firmwareVersion ?: "unknown"),
                ),
            )
        } catch (error: Exception) {
            DeviceResult.Unknown(commandId, error.message ?: "connect_failed")
        }
    }

    suspend fun disconnect(commandId: String): DeviceResult = try {
        driver.disconnect()
        DeviceResult.Success(commandId, "device.disconnected")
    } catch (error: Exception) {
        DeviceResult.Unknown(commandId, error.message ?: "disconnect_failed")
    }

    suspend fun execute(command: DeviceCommand): DeviceResult = when (command.name) {
        "device.connect" -> connect(command.id, command.payload["device_id"])
        "device.disconnect" -> disconnect(command.id)
        else -> driver.execute(command)
    }
}
