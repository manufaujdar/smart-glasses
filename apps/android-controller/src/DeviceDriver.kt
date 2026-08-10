package health.smartglasses.device

/** Vendor-neutral boundary. Clinical features must depend on this interface only. */
interface DeviceDriver {
    val driverId: String
    suspend fun discover(timeoutMillis: Long): List<DiscoveredDevice>
    suspend fun connect(deviceId: String): DeviceSnapshot
    suspend fun disconnect()
    suspend fun execute(command: DeviceCommand): DeviceResult
}

data class DiscoveredDevice(val id: String, val name: String?, val rssi: Int?)

data class DeviceSnapshot(
    val deviceId: String,
    val connected: Boolean,
    val batteryPercent: Int?,
    val capabilities: Set<String>,
    val firmwareVersion: String? = null,
)

data class DeviceCommand(
    val id: String,
    val name: String,
    val payload: Map<String, String> = emptyMap(),
)

sealed interface DeviceResult {
    val commandId: String
    data class Success(override val commandId: String, val event: String, val data: Map<String, String> = emptyMap()) : DeviceResult
    data class Rejected(override val commandId: String, val reason: String) : DeviceResult
    data class Unknown(override val commandId: String, val reason: String) : DeviceResult
}

