"use strict";

const STORAGE_KEY = "smart-glasses-synthetic-history-v1";
const MAX_HISTORY = 50;
let sequence = 1;
let lastState = null;
let lastEvent = null;

const byId = (id) => document.getElementById(id);

function readHistory() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value.slice(0, MAX_HISTORY) : [];
  } catch (_) {
    return [];
  }
}

function writeHistory(history) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  renderHistory();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function activeCapture(state) {
  if (state.recording_video) return "Video";
  if (state.recording_audio) return "Audio";
  return "None";
}

function renderState(state) {
  lastState = state;
  const connected = state.connection_state === "connected";
  byId("connection").textContent = connected ? "Connected" : "Disconnected";
  byId("battery").textContent = Number.isFinite(state.battery) ? `${state.battery}%` : "—";
  byId("photos").textContent = String(state.photo_count ?? 0);
  byId("capture").textContent = activeCapture(state);
  byId("connection-chip").textContent = connected ? "Connected" : "Disconnected";
  byId("connection-chip").dataset.state = connected ? "connected" : "disconnected";
  byId("capabilities").textContent = `Declared capabilities: ${(state.capabilities || []).join(", ") || "none"}.`;
}

function renderEvent(event) {
  lastEvent = event;
  byId("result").textContent = JSON.stringify(event, null, 2);
  const rejected = event.name === "command.rejected";
  byId("status").textContent = rejected
    ? `Command rejected safely: ${event.payload?.reason || "unknown reason"}.`
    : `Recorded ${event.name} at ${new Date(event.created_at).toLocaleTimeString()}.`;
}

function renderHistory() {
  const history = readHistory();
  const list = byId("history");
  list.replaceChildren();
  for (const item of history) {
    const row = document.createElement("li");
    const text = document.createElement("span");
    const name = document.createElement("strong");
    const detail = document.createElement("small");
    const time = document.createElement("time");
    name.textContent = item.event;
    detail.textContent = `Command: ${item.command} · ID: ${item.commandId}`;
    time.textContent = new Date(item.createdAt).toLocaleString();
    time.dateTime = item.createdAt;
    text.append(name, detail);
    row.append(text, time);
    list.append(row);
  }
  byId("history-count").textContent = `${history.length} ${history.length === 1 ? "event" : "events"}`;
  byId("empty-history").hidden = history.length > 0;
  list.hidden = history.length === 0;
}

async function refreshState() {
  renderState(await api("/api/state"));
}

async function runCommand(event) {
  event.preventDefault();
  const command = byId("command").value;
  const commandId = byId("command-id").value.trim();
  byId("status").textContent = "Running synthetic command…";
  try {
    const response = await api("/api/command", {
      method: "POST",
      body: JSON.stringify({ name: command, command_id: commandId }),
    });
    renderEvent(response.event);
    renderState(response.state);
    writeHistory([{ command, commandId, event: response.event.name, createdAt: response.event.created_at }, ...readHistory()]);
    sequence += 1;
    byId("command-id").value = `browser-command-${sequence}`;
  } catch (error) {
    byId("status").textContent = `No command was applied: ${error.message}`;
  }
}

async function resetSimulator() {
  try {
    const response = await api("/api/reset", { method: "POST", body: "{}" });
    renderState(response.state);
    lastEvent = null;
    byId("result").textContent = "Simulator reset; no event yet.";
    byId("status").textContent = "Simulator reset locally.";
  } catch (error) {
    byId("status").textContent = `Reset failed: ${error.message}`;
  }
}

function downloadHistory() {
  const payload = { generatedAt: new Date().toISOString(), synthetic: true, state: lastState, latestEvent: lastEvent, history: readHistory() };
  const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "smart-glasses-synthetic-review.json";
  link.click();
  URL.revokeObjectURL(url);
}

function markdownBrief() {
  const history = readHistory();
  return `# Smart Glasses synthetic review\n\n- Generated: ${new Date().toISOString()}\n- Connection: ${lastState?.connection_state || "unknown"}\n- Battery: ${lastState?.battery ?? "unknown"}\n- Events retained locally: ${history.length}\n- Latest event: ${lastEvent?.name || "none"}\n\n## Review boundary\n\nSynthetic local state-machine evidence only. No physical-device, patient-data, clinical-benefit, diagnostic, treatment, or surgical-navigation claim.\n\n## Recent events\n\n${history.slice(0, 10).map((item) => `- ${item.createdAt}: \`${item.command}\` → \`${item.event}\``).join("\n") || "- None"}`;
}

async function copyBrief() {
  try {
    await navigator.clipboard.writeText(markdownBrief());
    byId("status").textContent = "Markdown review brief copied.";
  } catch (_) {
    byId("status").textContent = "Clipboard access was unavailable; use Download JSON instead.";
  }
}

byId("command-form").addEventListener("submit", runCommand);
byId("refresh").addEventListener("click", () => refreshState().catch((error) => { byId("status").textContent = error.message; }));
byId("reset").addEventListener("click", resetSimulator);
byId("download").addEventListener("click", downloadHistory);
byId("copy-brief").addEventListener("click", copyBrief);
byId("clear-history").addEventListener("click", () => { localStorage.removeItem(STORAGE_KEY); renderHistory(); byId("status").textContent = "Local history cleared."; });

renderHistory();
refreshState().catch((error) => { byId("status").textContent = `Local gateway unavailable: ${error.message}`; });
