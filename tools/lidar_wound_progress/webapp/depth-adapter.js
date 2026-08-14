/**
 * Capability-only WebXR depth boundary.
 *
 * This module never asks for camera/AR permissions during page load. A native
 * workflow may call requestWebXRDepthSession() after an explicit user action,
 * but WebXR support and depth accuracy remain browser/device dependent.
 */

export async function getWebXRDepthCapability() {
  if (!navigator.xr?.isSessionSupported) return { supported: false, reason: "WebXR is unavailable" };
  try {
    const supported = await navigator.xr.isSessionSupported("immersive-ar");
    return supported && globalThis.XRFrame?.prototype?.getDepthInformation
      ? { supported: true, reason: "WebXR immersive AR and depth sensing are exposed" }
      : { supported: false, reason: supported ? "WebXR AR is available without depth sensing" : "WebXR immersive AR is unavailable" };
  } catch {
    return { supported: false, reason: "WebXR capability check failed" };
  }
}

export async function requestWebXRDepthSession() {
  if (!navigator.xr?.requestSession) throw new Error("This browser does not expose WebXR");
  return navigator.xr.requestSession("immersive-ar", {
    requiredFeatures: ["local"],
    optionalFeatures: ["depth-sensing"],
    depthSensing: { usagePreference: ["cpu-optimized"], dataFormatPreference: ["float32"] },
  });
}

export function readWebXRDepth(frame, view) {
  if (!frame?.getDepthInformation || !view) return null;
  const information = frame.getDepthInformation(view);
  if (!information) return null;
  return {
    width: information.width,
    height: information.height,
    rawValueToMeters: information.rawValueToMeters,
    texture: information.texture,
    depthUnit: "m",
    source: "WebXR Depth Sensing",
  };
}
