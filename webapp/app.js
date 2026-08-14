"use strict";

const STORAGE_KEY = "fieldline-integration-history-v2";
const MAX_HISTORY = 80;
const byId = (id) => document.getElementById(id);
let sequence = 1;
let adapters = [];
let state = null;
let latestEvent = null;
let browserStream = null;
let browserRecorder = null;
let recordedChunks = [];
let recognition = null;
let pendingVoiceCommand = null;

const voiceCommands = new Map([
  ["connect device", "device.connect"], ["disconnect device", "device.disconnect"],
  ["take photo", "camera.take_photo"], ["capture photo", "camera.take_photo"],
  ["start video", "camera.start_video"], ["stop video", "camera.stop_video"],
  ["start audio", "audio.start_recording"], ["stop audio", "audio.stop_recording"],
  ["start streaming", "stream.start"], ["stop streaming", "stream.stop"],
  ["clear view", "ui.clear_view"],
]);
const confirmationRequired = new Set(["camera.take_photo", "camera.start_video", "audio.start_recording", "stream.start"]);

function readHistory() {
  try { const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); return Array.isArray(value) ? value.slice(0, MAX_HISTORY) : []; }
  catch (_) { return []; }
}
function writeHistory(items) { localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_HISTORY))); renderHistory(); }
function nextId(prefix = "web") { sequence += 1; return `${prefix}-${Date.now()}-${sequence}`; }

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "content-type": "application/json", ...(options.headers || {}) } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || body.detail?.[0]?.msg || `Request failed (${response.status})`);
  return body;
}

function adapterFor(id) { return adapters.find((item) => item.adapter_id === id); }
function selectedAdapter() { return adapterFor(byId("adapter").value); }
function setStatus(message, tone = "normal") { byId("status").textContent = message; byId("status").dataset.tone = tone; }

function renderAdapters(data) {
  adapters = data.adapters || [];
  const select = byId("adapter");
  select.replaceChildren();
  for (const adapter of adapters) {
    const option = document.createElement("option");
    option.value = adapter.adapter_id;
    option.textContent = `${adapter.name}${adapter.available ? "" : " · setup required"}`;
    option.disabled = !adapter.available;
    option.selected = adapter.active;
    select.append(option);
  }
  renderAdapterInfo();
}

function renderAdapterInfo() {
  const adapter = selectedAdapter();
  if (!adapter) return;
  byId("adapter-mode").textContent = adapter.mode.replaceAll("_", " ");
  byId("adapter-info").textContent = `${adapter.transport}. ${adapter.evidence} ${adapter.limitations.join(" ")}`;
}

function renderState(nextState) {
  state = nextState;
  const connected = state.connection_state === "connected";
  byId("connection-chip").textContent = connected ? "Connected" : (state.connection_state || "Disconnected");
  byId("connection-chip").dataset.state = connected ? "connected" : "disconnected";
  byId("battery").textContent = Number.isFinite(state.battery) ? `${state.battery}%` : "—";
  byId("photos").textContent = String(state.photo_count ?? 0);
  byId("videos").textContent = String(state.video_count ?? 0);
  byId("audio").textContent = String(state.audio_count ?? 0);
  byId("recording").textContent = state.recording_video ? "Video" : state.recording_audio ? "Audio" : "None";
  byId("stream").textContent = state.streaming ? "On" : "Off";
  byId("connect").disabled = connected;
  byId("disconnect").disabled = !connected;
  const capabilities = new Set(state.capabilities || []);
  byId("capabilities").textContent = `Adapter: ${state.adapter_id || "legacy simulator"}. Declared capabilities: ${[...capabilities].join(", ") || "none"}.`;
  document.querySelectorAll("[data-capability]").forEach((button) => { button.disabled = !connected || !capabilities.has(button.dataset.capability); });
}

function renderEvent(event) {
  latestEvent = event;
  byId("result").textContent = JSON.stringify(event, null, 2);
  const rejected = event.name === "command.rejected";
  if (event.name === "media.list" && Array.isArray(event.payload?.items)) {
    const select = byId("media-item"); select.replaceChildren();
    for (const item of event.payload.items) { const option = document.createElement("option"); option.value = item.media_id; option.textContent = `${item.kind || "media"} · ${item.media_id}`; select.append(option); }
    if (!event.payload.items.length) { const option = document.createElement("option"); option.value = ""; option.textContent = "No media available"; select.append(option); }
    byId("transfer-media").disabled = !event.payload.items.length;
  }
  setStatus(rejected ? `Command rejected safely: ${event.payload?.reason || "unknown reason"}.` : `Recorded ${event.name}.`, rejected ? "warning" : "normal");
}

function renderHistory() {
  const history = readHistory();
  const list = byId("history"); list.replaceChildren();
  for (const item of history) {
    const row = document.createElement("li"); const text = document.createElement("span");
    const name = document.createElement("strong"); name.textContent = item.event;
    const detail = document.createElement("small"); detail.textContent = `${item.command} · ${item.adapter || "unknown adapter"}`;
    const time = document.createElement("time"); time.textContent = new Date(item.createdAt).toLocaleString(); time.dateTime = item.createdAt;
    text.append(name, detail); row.append(text, time); list.append(row);
  }
  byId("history-count").textContent = `${history.length} ${history.length === 1 ? "event" : "events"}`;
  byId("empty-history").hidden = history.length > 0; list.hidden = history.length === 0;
}

async function refreshAll() {
  const [adapterData, nextState] = await Promise.all([api("/api/adapters"), api("/api/state")]);
  renderAdapters(adapterData); renderState(nextState); byId("gateway-status").textContent = "Local gateway ready";
}

async function selectAdapter() {
  try { const result = await api("/api/adapters/select", { method: "POST", body: JSON.stringify({ adapter_id: byId("adapter").value }) }); renderState(result.state); setStatus(`Using ${result.active_adapter}.`); }
  catch (error) { setStatus(error.message, "warning"); await refreshAll(); }
}

async function discover() {
  byId("discovery-status").textContent = "Discovering…";
  try {
    const result = await api("/api/discover", { method: "POST", body: JSON.stringify({ timeout_seconds: 5 }) });
    const select = byId("device"); select.replaceChildren();
    for (const device of result.devices) { const option = document.createElement("option"); option.value = device.device_id; option.textContent = `${device.name || "Unnamed device"}${device.synthetic ? " · synthetic" : ""}`; select.append(option); }
    if (!result.devices.length) { const option = document.createElement("option"); option.value = ""; option.textContent = "No devices found"; select.append(option); }
    byId("discovery-status").textContent = `${result.devices.length} device${result.devices.length === 1 ? "" : "s"} found.`;
  } catch (error) { byId("discovery-status").textContent = error.message; }
}

async function runCommand(name, payload = {}) {
  setStatus(`Running ${name}…`);
  const commandPayload = name === "device.connect" ? { device_id: byId("device").value, ...payload } : payload;
  try {
    const response = await api("/api/command", { method: "POST", body: JSON.stringify({ name, command_id: nextId("command"), payload: commandPayload }) });
    renderEvent(response.event); renderState(response.state);
    writeHistory([{ command: name, event: response.event.name, adapter: response.state.adapter_id, createdAt: response.event.created_at || new Date().toISOString() }, ...readHistory()]);
    return response;
  } catch (error) { setStatus(`No action was applied: ${error.message}`, "warning"); throw error; }
}

async function openBrowserPreview() {
  try {
    browserStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: true });
    byId("preview").srcObject = browserStream; await byId("preview").play(); byId("preview-empty").hidden = true;
    byId("preview-chip").textContent = "Browser source on"; byId("start-preview").disabled = true;
    ["stop-preview", "capture-browser", "record-browser"].forEach((id) => { byId(id).disabled = false; });
    setStatus("Browser camera and microphone opened locally. This is not a glasses feed.");
  } catch (error) { setStatus(`Browser media unavailable: ${error.message}`, "warning"); }
}

function stopBrowserPreview() {
  if (browserRecorder?.state === "recording") browserRecorder.stop();
  browserStream?.getTracks().forEach((track) => track.stop()); browserStream = null; byId("preview").srcObject = null;
  byId("preview-empty").hidden = false; byId("preview-chip").textContent = "Off"; byId("start-preview").disabled = false;
  ["stop-preview", "capture-browser", "record-browser", "stop-browser-recording"].forEach((id) => { byId(id).disabled = true; });
}

function downloadBlob(blob, name) { const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function captureBrowserSnapshot() {
  const video = byId("preview"); const canvas = byId("snapshot"); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0); canvas.toBlob((blob) => { if (blob) downloadBlob(blob, `fieldline-browser-snapshot-${Date.now()}.png`); }, "image/png");
}
function startBrowserRecording() {
  if (!browserStream || typeof MediaRecorder === "undefined") { setStatus("Local browser recording is unavailable.", "warning"); return; }
  recordedChunks = []; browserRecorder = new MediaRecorder(browserStream);
  browserRecorder.ondataavailable = (event) => { if (event.data.size) recordedChunks.push(event.data); };
  browserRecorder.onstop = () => { if (recordedChunks.length) downloadBlob(new Blob(recordedChunks, { type: browserRecorder.mimeType }), `fieldline-browser-recording-${Date.now()}.webm`); };
  browserRecorder.start(); byId("record-browser").disabled = true; byId("stop-browser-recording").disabled = false; byId("preview-chip").textContent = "Recording locally";
}
function stopBrowserRecording() { if (browserRecorder?.state === "recording") browserRecorder.stop(); byId("record-browser").disabled = false; byId("stop-browser-recording").disabled = true; byId("preview-chip").textContent = "Browser source on"; }

function clearView() { byId("preview-shell").classList.toggle("clear-view", true); setStatus("Clear view enabled. Recording and stream state were not silently changed."); setTimeout(() => byId("preview-shell").classList.remove("clear-view"), 2500); }
async function processVoice(text) {
  const normalized = text.trim().toLowerCase().replace(/[.!?]/g, ""); const command = voiceCommands.get(normalized);
  if (!command) { setStatus("Voice phrase was not in the exact allowlist.", "warning"); return; }
  if (command === "ui.clear_view") { clearView(); return; }
  if (confirmationRequired.has(command)) { pendingVoiceCommand = command; byId("voice-pending").textContent = `Confirm voice command: ${normalized}`; byId("voice-confirm").hidden = false; return; }
  await runCommand(command);
}

function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { setStatus("This browser does not provide push-to-talk speech recognition.", "warning"); return; }
  recognition = new SpeechRecognition(); recognition.continuous = false; recognition.interimResults = false; recognition.lang = "en-US";
  recognition.onstart = () => { byId("voice-chip").textContent = "Listening"; byId("listen").disabled = true; byId("stop-listen").disabled = false; };
  recognition.onresult = (event) => { const text = event.results[0][0].transcript; byId("transcript").textContent = text; processVoice(text).catch((error) => setStatus(error.message, "warning")); };
  recognition.onerror = (event) => setStatus(`Voice recognition stopped: ${event.error}.`, "warning");
  recognition.onend = () => { byId("voice-chip").textContent = "Idle"; byId("listen").disabled = false; byId("stop-listen").disabled = true; };
  recognition.start();
}

function connectSocket() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:"; const socket = new WebSocket(`${protocol}//${location.host}/ws/events`);
  socket.onopen = () => { byId("socket-status").textContent = "Realtime events connected"; socket.send("ready"); };
  socket.onmessage = (message) => { const data = JSON.parse(message.data); if (data.state) renderState(data.state); if (data.event) renderEvent(data.event); };
  socket.onclose = () => { byId("socket-status").textContent = "Realtime events reconnecting…"; setTimeout(connectSocket, 2000); };
}

function downloadHistory() { downloadBlob(new Blob([JSON.stringify({ generatedAt: new Date().toISOString(), researchOnly: true, state, latestEvent, history: readHistory() }, null, 2)], { type: "application/json" }), "fieldline-integration-review.json"); }
function reviewBrief() { return `# Fieldline integration review\n\n- Generated: ${new Date().toISOString()}\n- Adapter: ${state?.adapter_id || "unknown"}\n- Mode: ${state?.adapter_mode || "unknown"}\n- Connection: ${state?.connection_state || "unknown"}\n- Events retained in browser: ${readHistory().length}\n\nResearch integration evidence only. No physical-device or clinical claim unless separately validated.`; }

byId("adapter").addEventListener("change", renderAdapterInfo); byId("select-adapter").addEventListener("click", selectAdapter); byId("discover").addEventListener("click", discover);
byId("connect").addEventListener("click", () => runCommand("device.connect").catch(() => {})); byId("disconnect").addEventListener("click", () => runCommand("device.disconnect").catch(() => {}));
document.querySelectorAll("[data-command]").forEach((button) => button.addEventListener("click", () => runCommand(button.dataset.command).catch(() => {})));
byId("transfer-media").addEventListener("click", () => { const mediaId = byId("media-item").value; if (mediaId) runCommand("media.transfer", { media_id: mediaId }).catch(() => {}); });
byId("start-preview").addEventListener("click", openBrowserPreview); byId("stop-preview").addEventListener("click", stopBrowserPreview); byId("capture-browser").addEventListener("click", captureBrowserSnapshot); byId("record-browser").addEventListener("click", startBrowserRecording); byId("stop-browser-recording").addEventListener("click", stopBrowserRecording);
byId("listen").addEventListener("click", startListening); byId("stop-listen").addEventListener("click", () => recognition?.stop());
byId("confirm-voice").addEventListener("click", () => { const command = pendingVoiceCommand; pendingVoiceCommand = null; byId("voice-confirm").hidden = true; if (command) runCommand(command).catch(() => {}); });
byId("cancel-voice").addEventListener("click", () => { pendingVoiceCommand = null; byId("voice-confirm").hidden = true; setStatus("Voice command cancelled."); });
byId("refresh").addEventListener("click", () => refreshAll().catch((error) => setStatus(error.message, "warning"))); byId("download").addEventListener("click", downloadHistory);
byId("copy-brief").addEventListener("click", () => navigator.clipboard.writeText(reviewBrief()).then(() => setStatus("Review brief copied.")).catch(() => setStatus("Clipboard unavailable.", "warning")));
byId("reset").addEventListener("click", () => api("/api/reset", { method: "POST", body: "{}" }).then((result) => { renderState(result.state); setStatus("Simulator reset."); }).catch((error) => setStatus(error.message, "warning")));
byId("clear-history").addEventListener("click", () => { localStorage.removeItem(STORAGE_KEY); renderHistory(); });
window.addEventListener("beforeunload", () => browserStream?.getTracks().forEach((track) => track.stop()));

renderHistory(); refreshAll().then(() => discover()).catch((error) => { byId("gateway-status").textContent = "Gateway unavailable"; setStatus(error.message, "warning"); }); connectSocket();
