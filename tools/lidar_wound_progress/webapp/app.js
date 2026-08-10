const STORAGE_KEY = "depthline.numeric-history.v1";
const API_BASE = new URLSearchParams(window.location.search).get("api") || "http://127.0.0.1:8787/api";
const $ = (id) => document.getElementById(id);

const state = {
  depthPayload: null,
  analysis: null,
  cameraStream: null,
  records: loadRecords(),
  capturedImage: null,
  sensorMode: "camera",
  apiAvailable: false,
};

function loadRecords() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(stored) ? stored.map((record) => ({ sensor_mode: "professional_lidar", accuracy_tier: "high", ...record })) : [];
  } catch {
    return [];
  }
}

function persistRecords() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.records));
}

async function initPersistence() {
  try {
    const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!response.ok) throw new Error("local service unavailable");
    const recordsResponse = await fetch(`${API_BASE}/records`, { cache: "no-store" });
    if (!recordsResponse.ok) throw new Error("local records unavailable");
    const payload = await recordsResponse.json();
    state.records = Array.isArray(payload.records) ? payload.records : [];
    state.apiAvailable = true;
    $("persistenceStatus").textContent = "Local SQLite service · no cloud upload";
    renderTrend();
  } catch {
    $("persistenceStatus").textContent = "Browser-local history · no cloud upload";
  }
}

async function saveToPersistence(record) {
  if (!state.apiAvailable) {
    state.records = [...state.records.filter((item) => !(item.wound_id === record.wound_id && item.capture_id === record.capture_id && item.sensor_mode === record.sensor_mode)), record];
    persistRecords();
    return record;
  }
  try {
    const response = await fetch(`${API_BASE}/records`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(record) });
    if (!response.ok) throw new Error("local service rejected the record");
    const saved = await response.json();
    state.records = [...state.records.filter((item) => item.record_id !== saved.record_id && !(item.wound_id === saved.wound_id && item.capture_id === saved.capture_id && item.sensor_mode === saved.sensor_mode)), saved];
    return saved;
  } catch {
    state.apiAvailable = false;
    $("persistenceStatus").textContent = "Local service unavailable · browser history active";
    state.records = [...state.records.filter((item) => !(item.wound_id === record.wound_id && item.capture_id === record.capture_id && item.sensor_mode === record.sensor_mode)), record];
    persistRecords();
    return record;
  }
}

function currentWoundId() {
  return $("woundId")?.value.trim() || state.depthPayload?.wound_id || "local-demo-wound";
}

function currentCaptureId() {
  return $("captureId")?.value.trim() || `browser-${Date.now()}`;
}

function finitePositive(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

function normaliseGrid(rawGrid) {
  if (!Array.isArray(rawGrid) || rawGrid.length === 0 || !Array.isArray(rawGrid[0])) {
    throw new Error("depth_mm must be a non-empty 2D array");
  }
  const width = rawGrid[0].length;
  if (!width || rawGrid.some((row) => !Array.isArray(row) || row.length !== width)) {
    throw new Error("depth_mm must be rectangular");
  }
  const grid = rawGrid.map((row) => row.map(finitePositive));
  if (!grid.some((row) => row.some((value) => value !== null))) {
    throw new Error("depth_mm contains no valid positive samples");
  }
  return grid;
}

function median(values) {
  const ordered = [...values].sort((a, b) => a - b);
  if (!ordered.length) throw new Error("No valid samples");
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
}

function percentile(values, rank) {
  const ordered = [...values].sort((a, b) => a - b);
  const position = (ordered.length - 1) * rank / 100;
  const low = Math.floor(position);
  const high = Math.ceil(position);
  if (low === high) return ordered[low];
  return ordered[low] + (ordered[high] - ordered[low]) * (position - low);
}

function mad(values, centre) {
  return median(values.map((value) => Math.abs(value - centre)));
}

function collectSamples(grid, roi, px, py, includeRoi, ringWidth) {
  const [x0, y0, x1, y1] = roi;
  const height = grid.length;
  const width = grid[0].length;
  const samples = [];
  for (let row = Math.max(0, y0 - ringWidth); row < Math.min(height, y1 + ringWidth); row += 1) {
    for (let column = Math.max(0, x0 - ringWidth); column < Math.min(width, x1 + ringWidth); column += 1) {
      const inside = column >= x0 && column < x1 && row >= y0 && row < y1;
      const value = grid[row][column];
      if (inside === includeRoi && value !== null) samples.push([column * px, row * py, value]);
    }
  }
  return samples;
}

function fitPlane(samples) {
  if (samples.length < 3) throw new Error("At least three valid background samples are required");
  const meanX = samples.reduce((sum, sample) => sum + sample[0], 0) / samples.length;
  const meanY = samples.reduce((sum, sample) => sum + sample[1], 0) / samples.length;
  const meanZ = samples.reduce((sum, sample) => sum + sample[2], 0) / samples.length;
  let sxx = 0; let syy = 0; let sxy = 0; let sxz = 0; let syz = 0;
  samples.forEach(([x, y, z]) => {
    const dx = x - meanX; const dy = y - meanY; const dz = z - meanZ;
    sxx += dx * dx; syy += dy * dy; sxy += dx * dy; sxz += dx * dz; syz += dy * dz;
  });
  const determinant = sxx * syy - sxy * sxy;
  if (Math.abs(determinant) < 1e-12) throw new Error("Background samples do not span a 2D surface");
  const slopeX = (sxz * syy - syz * sxy) / determinant;
  const slopeY = (syz * sxx - sxz * sxy) / determinant;
  return { slopeX, slopeY, intercept: meanZ - slopeX * meanX - slopeY * meanY };
}

function analysePayload(payload) {
  const grid = normaliseGrid(payload.depth_mm);
  const [px, py] = payload.pixel_size_mm || [];
  if (!Number.isFinite(Number(px)) || !Number.isFinite(Number(py)) || Number(px) <= 0 || Number(py) <= 0) {
    throw new Error("pixel_size_mm must contain positive x and y calibration");
  }
  const spacingX = Number(px); const spacingY = Number(py);
  const [x0, y0, x1, y1] = payload.roi || [];
  const width = grid[0].length; const height = grid.length;
  if (![x0, y0, x1, y1].every(Number.isInteger) || !(0 <= x0 && x0 < x1 && x1 <= width && 0 <= y0 && y0 < y1 && y1 <= height)) {
    throw new Error("roi must fit inside the depth grid as x0 y0 x1 y1");
  }
  const ringWidth = Number.isInteger(payload.ring_width_px) && payload.ring_width_px > 0 ? payload.ring_width_px : 2;
  const roiSamples = collectSamples(grid, [x0, y0, x1, y1], spacingX, spacingY, true, ringWidth);
  const backgroundSamples = collectSamples(grid, [x0, y0, x1, y1], spacingX, spacingY, false, ringWidth);
  if (roiSamples.length < 4 || backgroundSamples.length < 3) throw new Error("Not enough valid ROI/background samples");
  const plane = fitPlane(backgroundSamples);
  const offsets = roiSamples.map(([x, y, z]) => z - (plane.slopeX * x + plane.slopeY * y + plane.intercept));
  const positive = offsets.map((value) => Math.max(0, value));
  const backgroundDepths = backgroundSamples.map((sample) => sample[2]);
  const medianOffset = median(offsets);
  const backgroundMedian = median(backgroundDepths);
  const backgroundMad = mad(backgroundDepths, backgroundMedian);
  const roiMad = mad(offsets, medianOffset);
  const expectedRoi = (x1 - x0) * (y1 - y0);
  const expectedBackground = ((x1 - x0) + (2 * ringWidth)) * ((y1 - y0) + (2 * ringWidth)) - expectedRoi;
  const flags = [];
  if (roiSamples.length < expectedRoi) flags.push("missing_roi_samples");
  if (backgroundSamples.length < expectedBackground) flags.push("missing_background_samples");
  if (backgroundSamples.length < 12) flags.push("small_background_sample");
  if (backgroundMad > 2) flags.push("noisy_background_surface");
  if (roiMad > 2) flags.push("variable_roi_surface");
  let quality = 1;
  quality -= Math.min(0.35, 0.35 * (expectedRoi - roiSamples.length) / Math.max(1, expectedRoi));
  quality -= Math.min(0.25, 0.25 * (expectedBackground - backgroundSamples.length) / Math.max(1, expectedBackground));
  if (backgroundSamples.length < 12) quality -= 0.2;
  if (backgroundMad > 2) quality -= 0.15;
  if (roiMad > 2) quality -= 0.15;
  return {
    capture_id: payload.capture_id || currentCaptureId(),
    captured_at: payload.captured_at || new Date().toISOString(),
    wound_id: payload.wound_id || currentWoundId(),
    sensor_mode: payload.sensor_mode || state.sensorMode,
    accuracy_tier: payload.accuracy_tier || (payload.sensor_mode === "professional_lidar" ? "high" : "low"),
    source_label: payload.source_label || (payload.sensor_mode === "professional_lidar" ? "Professional LiDAR" : "Phone / laptop camera estimate"),
    roi: { x0, y0, x1, y1, ring_width_px: ringWidth },
    measurements: {
      median_depth_offset_mm: medianOffset,
      p95_depth_offset_mm: percentile(offsets, 95),
      maximum_depth_offset_mm: Math.max(...offsets),
      mean_positive_depth_offset_mm: positive.reduce((sum, value) => sum + value, 0) / positive.length,
      projected_area_mm2: roiSamples.length * spacingX * spacingY,
      estimated_positive_volume_mm3: positive.reduce((sum, value) => sum + value, 0) * spacingX * spacingY,
      background_median_depth_mm: backgroundMedian,
      background_mad_mm: backgroundMad,
      roi_residual_mad_mm: roiMad,
    },
    quality: {
      engineering_quality_score: Math.max(0, Math.min(1, Number(quality.toFixed(3)))),
      flags: payload.sensor_mode === "camera" ? [...flags, "operator_estimate_not_sensor_depth"] : flags,
      score_definition: "heuristic data-quality indicator; not clinical confidence",
    },
    calibration: { pixel_size_x_mm: spacingX, pixel_size_y_mm: spacingY },
  };
}

function syntheticPayload() {
  const grid = Array.from({ length: 16 }, (_, row) => Array.from({ length: 16 }, (_, column) => {
    return row >= 5 && row < 9 && column >= 6 && column < 10 ? 24 : 20;
  }));
  return { wound_id: "synthetic-demo-wound", capture_id: "synthetic-visit-1", captured_at: new Date().toISOString(), sensor_mode: "professional_lidar", accuracy_tier: "high", source_label: "Synthetic professional LiDAR", pixel_size_mm: [0.8, 0.8], roi: [6, 5, 10, 9], depth_mm: grid };
}

function cameraEstimatePayload() {
  const depth = Number($("approxDepthMm").value);
  const area = Number($("approxAreaMm2").value);
  if (!Number.isFinite(depth) || depth <= 0 || depth > 100) throw new Error("Enter an approximate depth between 0.1 and 100 mm");
  if (!Number.isFinite(area) || area <= 0 || area > 100000) throw new Error("Enter an approximate area between 1 and 100,000 mm²");
  const pixelSize = Math.sqrt(area) / 4;
  const grid = Array.from({ length: 8 }, (_, row) => Array.from({ length: 8 }, (_, column) => {
    return row >= 2 && row < 6 && column >= 2 && column < 6 ? 20 + depth : 20;
  }));
  return {
    wound_id: currentWoundId(), capture_id: currentCaptureId(), captured_at: new Date().toISOString(),
    sensor_mode: "camera", accuracy_tier: "low", source_label: "Phone / laptop camera estimate",
    pixel_size_mm: [pixelSize, pixelSize], roi: [2, 2, 6, 6], depth_mm: grid,
  };
}

function format(value, digits = 1) { return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—"; }

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function setStatus(element, label, neutral = false) {
  element.textContent = label;
  element.classList.toggle("neutral", neutral);
}

function updateSensorUI() {
  const cameraSelected = state.sensorMode === "camera";
  $("cameraOption").classList.toggle("selected", cameraSelected);
  $("lidarOption").classList.toggle("selected", !cameraSelected);
  $("cameraEstimateControls").hidden = !cameraSelected;
  $("dropZone").style.opacity = cameraSelected ? "0.55" : "1";
  $("sensorMessage").textContent = cameraSelected
    ? "Camera mode does not infer millimetres from RGB pixels. Enter an operator estimate after capturing a visual reference."
    : "Professional LiDAR mode expects calibrated depth JSON and blocks comparisons against camera-estimate records.";
}

function setSensorMode(mode) {
  if (!new Set(["camera", "professional_lidar"]).has(mode)) return;
  const changed = state.sensorMode !== mode;
  state.sensorMode = mode;
  if (changed && state.analysis) {
    state.depthPayload = null;
    state.analysis = null;
    $("fileSummary").hidden = true;
    $("reviewBadge").textContent = "No frame loaded";
    $("saveRecord").disabled = true;
    $("downloadRecord").disabled = true;
    $("analysisMessage").textContent = "Load a new frame for the selected measurement route.";
    setStatus($("depthStatus"), "Waiting", true);
  }
  updateSensorUI();
  renderMetrics();
  renderTrend();
}

function renderMetrics() {
  const grid = $("metricGrid");
  if (!state.analysis) {
    grid.innerHTML = `<div class="metric-card empty-metric"><span>Depth offset</span><strong>—</strong><small>mm · plane-relative</small></div><div class="metric-card empty-metric"><span>Estimated volume</span><strong>—</strong><small>mm³ · approximation</small></div><div class="metric-card empty-metric"><span>Surface area</span><strong>—</strong><small>mm² · projected ROI</small></div><div class="metric-card empty-metric"><span>Data quality</span><strong>—</strong><small>engineering indicator</small></div>`;
    return;
  }
  const metrics = state.analysis.measurements;
  const quality = state.analysis.quality.engineering_quality_score;
  grid.innerHTML = `<div class="metric-card"><span>Depth offset</span><strong>${format(metrics.median_depth_offset_mm)}<small> mm</small></strong><small>median · plane-relative</small></div><div class="metric-card"><span>Estimated volume</span><strong>${format(metrics.estimated_positive_volume_mm3)}<small> mm³</small></strong><small>positive residual approximation</small></div><div class="metric-card"><span>Surface area</span><strong>${format(metrics.projected_area_mm2)}<small> mm²</small></strong><small>projected ROI</small></div><div class="metric-card"><span>${state.analysis.accuracy_tier === "high" ? "High-accuracy route" : "Lower-accuracy route"}</span><strong>${Math.round(quality * 100)}<small> / 100</small></strong><small>${escapeHtml(state.analysis.source_label)}</small></div>`;
}

function matchingRecords() {
  const woundId = state.analysis?.wound_id || state.depthPayload?.wound_id || "local-demo-wound";
  const sensorMode = state.analysis?.sensor_mode || state.sensorMode;
  return state.records.filter((record) => record.wound_id === woundId && record.sensor_mode === sensorMode).sort((a, b) => new Date(a.captured_at) - new Date(b.captured_at));
}

function allMatchingWoundRecords() {
  const woundId = state.analysis?.wound_id || state.depthPayload?.wound_id || currentWoundId();
  return state.records.filter((record) => record.wound_id === woundId);
}

function renderTrend() {
  const records = matchingRecords();
  const allWoundRecords = allMatchingWoundRecords();
  const current = state.analysis;
  $("historyList").innerHTML = records.length ? records.map((record) => `<div class="history-item"><span>${new Date(record.captured_at).toLocaleDateString()} · ${escapeHtml(record.capture_id)}</span><strong>${format(record.measurements.estimated_positive_volume_mm3)} mm³</strong></div>`).join("") : "";
  if (!current) {
    $("trendDisplay").innerHTML = `<span class="trend-kicker">Baseline needed</span><strong>—</strong><p>Load a depth frame to review local history.</p>`;
    $("trendDetail").textContent = records.length ? `${records.length} local record${records.length === 1 ? "" : "s"} found for this wound key.` : "No records are stored yet. History uses local browser storage only.";
    return;
  }
  if (!records.length) {
    $("trendDisplay").innerHTML = `<span class="trend-kicker">Baseline needed</span><strong>New</strong><p>Save this numeric record, then compare a later frame on this device.</p>`;
    $("trendDetail").textContent = allWoundRecords.length ? "Previous records exist for this wound key, but another sensor route was selected. Cross-sensor comparisons are blocked." : "No previous record matches this wound key.";
    return;
  }
  const baseline = records[0];
  const latest = current;
  const baseVolume = baseline.measurements.estimated_positive_volume_mm3;
  const volume = latest.measurements.estimated_positive_volume_mm3;
  const changePct = baseVolume > 0 ? ((volume - baseVolume) / baseVolume) * 100 : null;
  const depthBase = baseline.measurements.median_depth_offset_mm;
  const depthChange = Math.abs(depthBase) > 1e-9 ? ((latest.measurements.median_depth_offset_mm - depthBase) / Math.abs(depthBase)) * 100 : null;
  const directions = [changePct, depthChange].map((value) => value === null ? "not_comparable" : value <= -5 ? "decreasing" : value >= 5 ? "increasing" : "stable");
  const signal = latest.quality.engineering_quality_score < 0.6 ? "insufficient_quality" : directions.filter((value) => value === "decreasing").length === 2 ? "decreasing_geometry" : directions.filter((value) => value === "increasing").length === 2 ? "increasing_geometry" : "stable_or_mixed_geometry";
  const changeIndex = baseVolume > 0 ? Math.max(-100, Math.min(100, 100 * (1 - volume / baseVolume))) : null;
  const signalLabel = { decreasing_geometry: "Decreasing geometry", increasing_geometry: "Increasing geometry", stable_or_mixed_geometry: "Stable / mixed", insufficient_quality: "Insufficient quality" }[signal];
  $("trendDisplay").innerHTML = `<span class="trend-kicker">Geometry signal</span><strong>${signalLabel}</strong><p>Compared with ${new Date(baseline.captured_at).toLocaleDateString()} · ${escapeHtml(baseline.capture_id)}</p>`;
  $("trendDetail").innerHTML = `<strong>${changeIndex === null ? "—" : `${changeIndex >= 0 ? "+" : ""}${format(changeIndex, 0)}`}</strong> change index · ${changePct === null ? "volume not comparable" : `${format(changePct, 1)}% volume change`} · not a clinical score.`;
}

function setCurrentPayload(payload, sourceLabel) {
  state.depthPayload = payload;
  state.analysis = analysePayload(payload);
  state.sensorMode = state.analysis.sensor_mode;
  document.querySelector(`input[name="sensorMode"][value="${state.sensorMode}"]`).checked = true;
  updateSensorUI();
  $("woundId").value = state.analysis.wound_id;
  $("captureId").value = state.analysis.capture_id;
  setStatus($("depthStatus"), "Loaded");
  $("fileSummary").hidden = false;
  $("fileSummary").textContent = `${sourceLabel} · ${state.analysis.frame_width_px || payload.depth_mm[0].length}×${state.analysis.frame_height_px || payload.depth_mm.length} grid`;
  $("depthMessage").textContent = "Frame loaded locally. Review the ROI and calibration before saving a numeric record.";
  $("reviewBadge").textContent = "Ready for review";
  $("saveRecord").disabled = false;
  $("downloadRecord").disabled = false;
  $("analysisMessage").textContent = "The values below are geometry measurements. They are not a clinical wound score.";
  renderMetrics();
  renderTrend();
}

function downloadCurrent() {
  const blob = new Blob([JSON.stringify({ ...state.depthPayload, analysis: state.analysis }, null, 2)], { type: "application/json" });
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `${state.analysis.capture_id}-depthline.json`; link.click(); URL.revokeObjectURL(link.href);
}

async function saveCurrent() {
  if (!state.analysis) return;
  const record = { wound_id: state.analysis.wound_id, capture_id: state.analysis.capture_id, captured_at: state.analysis.captured_at, sensor_mode: state.analysis.sensor_mode, accuracy_tier: state.analysis.accuracy_tier, measurements: state.analysis.measurements, quality: state.analysis.quality };
  await saveToPersistence(record);
  renderTrend(); $("analysisMessage").textContent = state.apiAvailable ? "Numeric record saved to the loopback SQLite service. The captured image was not stored." : "Numeric record saved only in this browser. The captured image was not stored.";
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error("This browser does not expose camera access.");
  state.cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
  $("cameraPreview").srcObject = state.cameraStream; $("cameraPlaceholder").hidden = true;
  $("captureStill").disabled = false; $("stopCamera").disabled = false; setStatus($("cameraStatus"), "Live"); $("cameraMessage").textContent = "Visual reference is live locally. It will not be added to the numeric history.";
}

function captureStill() {
  const video = $("cameraPreview"); const canvas = $("cameraCanvas");
  if (!video.videoWidth) return;
  canvas.width = video.videoWidth; canvas.height = video.videoHeight; canvas.getContext("2d").drawImage(video, 0, 0);
  state.capturedImage = canvas.toDataURL("image/jpeg", 0.88); $("capturedStill").src = state.capturedImage; $("capturedStill").hidden = false;
  $("cameraMessage").textContent = "Still captured in memory for visual reference only; it is not persisted.";
}

function stopCamera() {
  state.cameraStream?.getTracks().forEach((track) => track.stop()); state.cameraStream = null; $("cameraPreview").srcObject = null; $("cameraPlaceholder").hidden = false; $("captureStill").disabled = true; $("stopCamera").disabled = true; setStatus($("cameraStatus"), "Off");
}

$("startCamera").addEventListener("click", () => startCamera().catch((error) => { $("cameraMessage").textContent = error.message; }));
$("captureStill").addEventListener("click", captureStill);
$("stopCamera").addEventListener("click", stopCamera);
document.querySelectorAll('input[name="sensorMode"]').forEach((input) => input.addEventListener("change", () => setSensorMode(input.value)));
$("buildCameraEstimate").addEventListener("click", () => { try { setCurrentPayload(cameraEstimatePayload(), "Camera-assisted estimate"); } catch (error) { $("analysisMessage").textContent = error.message; } });
$("loadDemo").addEventListener("click", () => { setSensorMode("professional_lidar"); const payload = syntheticPayload(); setCurrentPayload(payload, "Synthetic demo"); });
$("depthFile").addEventListener("change", (event) => {
  const file = event.target.files?.[0]; if (!file) return;
  const reader = new FileReader(); reader.onload = () => { try { const payload = JSON.parse(reader.result); payload.sensor_mode = "professional_lidar"; payload.accuracy_tier = "high"; payload.source_label = "Professional LiDAR depth JSON"; setCurrentPayload(payload, file.name); } catch (error) { $("depthMessage").textContent = `Could not load frame: ${error.message}`; setStatus($("depthStatus"), "Error", true); } }; reader.readAsText(file);
});
$("dropZone").addEventListener("dragover", (event) => { event.preventDefault(); $("dropZone").classList.add("dragging"); });
$("dropZone").addEventListener("dragleave", () => $("dropZone").classList.remove("dragging"));
$("dropZone").addEventListener("drop", (event) => { event.preventDefault(); $("dropZone").classList.remove("dragging"); const file = event.dataTransfer.files?.[0]; if (file) { $("depthFile").files = event.dataTransfer.files; $("depthFile").dispatchEvent(new Event("change")); } });
$("saveRecord").addEventListener("click", saveCurrent);
$("downloadRecord").addEventListener("click", downloadCurrent);
$("clearHistory").addEventListener("click", async () => { if (!confirm("Clear numeric history from this device?")) return; if (state.apiAvailable) { await Promise.all(state.records.map((record) => fetch(`${API_BASE}/records/${record.record_id}`, { method: "DELETE" }).catch(() => null))); } state.records = []; persistRecords(); renderTrend(); });

updateSensorUI(); renderMetrics(); renderTrend(); initPersistence();
