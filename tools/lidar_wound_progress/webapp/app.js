import { getWebXRDepthCapability } from "./depth-adapter.js";

const HISTORY_KEY = "depthline.paired-photo-history.v1";
const GRID_WIDTH = 160;
const GRID_HEIGHT = 120;
const $ = (id) => document.getElementById(id);

const state = {
  images: { baseline: null, followup: null },
  result: null,
  history: loadHistory(),
};

function loadHistory() {
  try {
    const value = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function saveHistory() { localStorage.setItem(HISTORY_KEY, JSON.stringify(state.history)); }

function numberValue(id, fallback = null) {
  const value = Number($(id).value);
  return Number.isFinite(value) ? value : fallback;
}

function format(value, digits = 1) { return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—"; }

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return 0;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function mad(values, centre) { return median(values.map((value) => Math.abs(value - centre))); }

function roiConfig() {
  const roi = { x: numberValue("roiX", 20), y: numberValue("roiY", 20), width: numberValue("roiWidth", 60), height: numberValue("roiHeight", 60) };
  if (![roi.x, roi.y, roi.width, roi.height].every(Number.isFinite) || roi.x < 0 || roi.y < 0 || roi.width < 10 || roi.height < 10 || roi.x + roi.width > 100 || roi.y + roi.height > 100) {
    throw new Error("The wound region must fit inside the photo and be at least 10% wide and high.");
  }
  return roi;
}

function createImageBitmapFromFile(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);
    image.onload = () => { resolve({ image, src: url, name: file.name, width: image.naturalWidth, height: image.naturalHeight }); };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error("The selected image could not be read.")); };
    image.src = url;
  });
}

function drawPhotoPreview(kind) {
  const entry = state.images[kind];
  const preview = $(`${kind}Preview`);
  const empty = $(`${kind}Empty`);
  const stateLabel = $(`${kind}State`);
  if (!entry) {
    preview.hidden = true; empty.hidden = false; stateLabel.textContent = "Waiting"; stateLabel.classList.remove("ready");
    return;
  }
  preview.src = entry.src;
  preview.hidden = false; empty.hidden = true; stateLabel.textContent = "Ready"; stateLabel.classList.add("ready");
  $(`${kind}Meta`).textContent = `${entry.name} · ${entry.width}×${entry.height}px · kept in memory only`;
}

async function loadPhoto(kind, file) {
  try {
    if (state.images[kind]?.src) URL.revokeObjectURL(state.images[kind].src);
    state.images[kind] = await createImageBitmapFromFile(file);
    $("scaleConfirmed").checked = false; $("reviewedMask").checked = false;
    drawPhotoPreview(kind);
    updateForm();
    if (state.images.baseline && state.images.followup) runAutoSetup();
  } catch (error) {
    $(`${kind}Meta`).textContent = error.message;
  }
}

function sampleImage(entry) {
  const canvas = document.createElement("canvas");
  canvas.width = GRID_WIDTH; canvas.height = GRID_HEIGHT;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(entry.image, 0, 0, GRID_WIDTH, GRID_HEIGHT);
  const pixels = context.getImageData(0, 0, GRID_WIDTH, GRID_HEIGHT).data;
  const grayscale = [];
  let sum = 0; let sumSquared = 0;
  for (let index = 0; index < pixels.length; index += 4) {
    const r = pixels[index] / 255; const g = pixels[index + 1] / 255; const b = pixels[index + 2] / 255;
    const value = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    grayscale.push(value); sum += value; sumSquared += value * value;
  }
  const mean = sum / grayscale.length;
  const contrast = Math.sqrt(Math.max(0, sumSquared / grayscale.length - mean * mean));
  return { pixels, grayscale, mean, contrast };
}

function normalizedRgb(r, g, b) {
  const total = r + g + b || 1;
  return [r / total, g / total, b / total];
}

function pixelDistance(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }

function segmentPhoto(entry, roi, sensitivity) {
  const sample = sampleImage(entry);
  const x0 = Math.floor(roi.x / 100 * GRID_WIDTH); const y0 = Math.floor(roi.y / 100 * GRID_HEIGHT);
  const x1 = Math.min(GRID_WIDTH, Math.ceil((roi.x + roi.width) / 100 * GRID_WIDTH)); const y1 = Math.min(GRID_HEIGHT, Math.ceil((roi.y + roi.height) / 100 * GRID_HEIGHT));
  const ring = Math.max(2, Math.round(Math.min(x1 - x0, y1 - y0) * 0.12));
  const background = []; const backgroundLuma = [];
  for (let y = Math.max(0, y0 - ring); y < Math.min(GRID_HEIGHT, y1 + ring); y += 1) {
    for (let x = Math.max(0, x0 - ring); x < Math.min(GRID_WIDTH, x1 + ring); x += 1) {
      if (x >= x0 && x < x1 && y >= y0 && y < y1) continue;
      const index = (y * GRID_WIDTH + x) * 4;
      const rgb = normalizedRgb(sample.pixels[index], sample.pixels[index + 1], sample.pixels[index + 2]);
      background.push(rgb); backgroundLuma.push(sample.grayscale[y * GRID_WIDTH + x]);
    }
  }
  if (background.length < 8) throw new Error("The wound region needs a larger periwound border.");
  const reference = [0, 1, 2].map((channel) => median(background.map((rgb) => rgb[channel])));
  const referenceLuma = median(backgroundLuma);
  const backgroundDistances = background.map((rgb, index) => pixelDistance(rgb, reference) * 1.6 + Math.abs(backgroundLuma[index] - referenceLuma) * .8);
  const threshold = Math.max(.035, median(backgroundDistances) + sensitivity * Math.max(.012, 1.4826 * mad(backgroundDistances, median(backgroundDistances))));
  const rawMask = Array.from({ length: GRID_HEIGHT }, () => Array(GRID_WIDTH).fill(false));
  for (let y = y0; y < y1; y += 1) {
    for (let x = x0; x < x1; x += 1) {
      const index = (y * GRID_WIDTH + x) * 4;
      const rgb = normalizedRgb(sample.pixels[index], sample.pixels[index + 1], sample.pixels[index + 2]);
      const luma = sample.grayscale[y * GRID_WIDTH + x];
      const distance = pixelDistance(rgb, reference) * 1.6 + Math.abs(luma - referenceLuma) * .8;
      rawMask[y][x] = distance > threshold;
    }
  }
  const mask = keepLargestComponent(rawMask, x0, y0, x1, y1);
  const scale = numberValue(entry === state.images.baseline ? "baselineMarkerPx" : "followupMarkerPx", 0);
  const markerWidth = numberValue("markerWidthMm", 25);
  const mmPerPixel = scale > 0 && markerWidth > 0 ? markerWidth / scale : null;
  const metricScale = mmPerPixel ? [mmPerPixel * entry.width / GRID_WIDTH, mmPerPixel * entry.height / GRID_HEIGHT] : [1, 1];
  return { ...sample, mask, roi: { x0, y0, x1, y1 }, threshold, metricScale, mmPerPixel, colorFractions: colorFractions(sample, mask) };
}

function keepLargestComponent(mask, x0, y0, x1, y1) {
  const visited = Array.from({ length: GRID_HEIGHT }, () => Array(GRID_WIDTH).fill(false));
  const components = [];
  for (let y = y0; y < y1; y += 1) for (let x = x0; x < x1; x += 1) {
    if (!mask[y][x] || visited[y][x]) continue;
    const queue = [[x, y]]; const points = []; visited[y][x] = true;
    while (queue.length) {
      const [cx, cy] = queue.pop(); points.push([cx, cy]);
      [[cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1]].forEach(([nx, ny]) => {
        if (nx >= x0 && nx < x1 && ny >= y0 && ny < y1 && mask[ny][nx] && !visited[ny][nx]) { visited[ny][nx] = true; queue.push([nx, ny]); }
      });
    }
    components.push(points);
  }
  const minimum = Math.max(4, Math.floor((x1 - x0) * (y1 - y0) * .003));
  const largest = components.filter((component) => component.length >= minimum).sort((a, b) => b.length - a.length)[0] || [];
  const result = Array.from({ length: GRID_HEIGHT }, () => Array(GRID_WIDTH).fill(false));
  largest.forEach(([x, y]) => { result[y][x] = true; });
  return result;
}

function maskMetrics(mask, metricScale) {
  const [px, py] = metricScale; const points = []; const pointSet = new Set();
  mask.forEach((row, y) => row.forEach((value, x) => { if (value) { points.push([x, y]); pointSet.add(`${x},${y}`); } }));
  let perimeter = 0;
  points.forEach(([x, y]) => { if (!pointSet.has(`${x - 1},${y}`)) perimeter += py; if (!pointSet.has(`${x + 1},${y}`)) perimeter += py; if (!pointSet.has(`${x},${y - 1}`)) perimeter += px; if (!pointSet.has(`${x},${y + 1}`)) perimeter += px; });
  if (!points.length) return { areaPx: 0, areaMm2: 0, perimeterMm: 0, longestMm: 0, widestMm: 0, circularity: null };
  const width = (Math.max(...points.map(([x]) => x)) - Math.min(...points.map(([x]) => x)) + 1) * px;
  const height = (Math.max(...points.map(([, y]) => y)) - Math.min(...points.map(([, y]) => y)) + 1) * py;
  const area = points.length * px * py;
  return { areaPx: points.length, areaMm2: area, perimeterMm: perimeter, longestMm: Math.max(width, height), widestMm: Math.min(width, height), circularity: perimeter ? 4 * Math.PI * area / (perimeter * perimeter) : null };
}

function colorFractions(sample, mask) {
  const counts = { red: 0, yellow: 0, dark: 0, other: 0 }; let total = 0;
  mask.forEach((row, y) => row.forEach((value, x) => { if (!value) return; const index = (y * GRID_WIDTH + x) * 4; const r = sample.pixels[index] / 255; const g = sample.pixels[index + 1] / 255; const b = sample.pixels[index + 2] / 255; const luma = sample.grayscale[y * GRID_WIDTH + x]; total += 1; if (luma < .22) counts.dark += 1; else if (r > g * 1.18 && r > b * 1.18) counts.red += 1; else if (r > b * 1.15 && g > b * 1.15) counts.yellow += 1; else counts.other += 1; }));
  return Object.fromEntries(Object.entries(counts).map(([key, value]) => [key, total ? value / total : 0]));
}

function imageSignal(first, second, roi, alignment = { dx: 0, dy: 0 }) {
  const a = []; const b = [];
  for (let y = Math.floor(roi.y / 100 * GRID_HEIGHT); y < Math.ceil((roi.y + roi.height) / 100 * GRID_HEIGHT); y += 1) for (let x = Math.floor(roi.x / 100 * GRID_WIDTH); x < Math.ceil((roi.x + roi.width) / 100 * GRID_WIDTH); x += 1) {
    const alignedX = x + alignment.dx; const alignedY = y + alignment.dy;
    if (alignedX < 0 || alignedX >= GRID_WIDTH || alignedY < 0 || alignedY >= GRID_HEIGHT) continue;
    a.push(first.grayscale[y * GRID_WIDTH + x]); b.push(second.grayscale[alignedY * GRID_WIDTH + alignedX]);
  }
  if (!a.length) return { ssim: 0, meanAbsoluteDifference: 1, changedFraction: 1, alignment };
  const meanA = a.reduce((sum, value) => sum + value, 0) / a.length; const meanB = b.reduce((sum, value) => sum + value, 0) / b.length;
  const varianceA = a.reduce((sum, value) => sum + (value - meanA) ** 2, 0) / Math.max(1, a.length - 1); const varianceB = b.reduce((sum, value) => sum + (value - meanB) ** 2, 0) / Math.max(1, b.length - 1);
  const covariance = a.reduce((sum, value, index) => sum + (value - meanA) * (b[index] - meanB), 0) / Math.max(1, a.length - 1); const c1 = .0001; const c2 = .0009;
  const denominator = (meanA ** 2 + meanB ** 2 + c1) * (varianceA + varianceB + c2); const ssim = denominator ? ((2 * meanA * meanB + c1) * (2 * covariance + c2)) / denominator : 1;
  const difference = a.map((value, index) => Math.abs(value - b[index]));
  return { ssim: Math.max(-1, Math.min(1, ssim)), meanAbsoluteDifference: difference.reduce((sum, value) => sum + value, 0) / difference.length, changedFraction: difference.filter((value) => value > .05).length / difference.length, alignment };
}

function lightingScore(first, second) {
  return Math.max(0, Math.min(1, 1 - Math.abs(first.mean - second.mean) * 4 - Math.abs(first.contrast - second.contrast) * 4));
}

function candidateMask(sample) {
  const border = [];
  for (let y = 4; y < GRID_HEIGHT - 4; y += 1) for (let x = 4; x < GRID_WIDTH - 4; x += 1) {
    if (x < 14 || x >= GRID_WIDTH - 14 || y < 10 || y >= GRID_HEIGHT - 10) {
      const index = (y * GRID_WIDTH + x) * 4;
      border.push({ rgb: normalizedRgb(sample.pixels[index], sample.pixels[index + 1], sample.pixels[index + 2]), luma: sample.grayscale[y * GRID_WIDTH + x] });
    }
  }
  const reference = [0, 1, 2].map((channel) => median(border.map((pixel) => pixel.rgb[channel])));
  const referenceLuma = median(border.map((pixel) => pixel.luma));
  const distances = border.map((pixel) => pixelDistance(pixel.rgb, reference) * 1.6 + Math.abs(pixel.luma - referenceLuma) * .8);
  const centre = median(distances); const threshold = Math.max(.045, centre + 2.2 * Math.max(.01, 1.4826 * mad(distances, centre)));
  const rawMask = Array.from({ length: GRID_HEIGHT }, () => Array(GRID_WIDTH).fill(false));
  for (let y = 5; y < GRID_HEIGHT - 5; y += 1) for (let x = 5; x < GRID_WIDTH - 5; x += 1) {
    const index = (y * GRID_WIDTH + x) * 4;
    const rgb = normalizedRgb(sample.pixels[index], sample.pixels[index + 1], sample.pixels[index + 2]);
    rawMask[y][x] = pixelDistance(rgb, reference) * 1.6 + Math.abs(sample.grayscale[y * GRID_WIDTH + x] - referenceLuma) * .8 > threshold;
  }
  return keepLargestComponent(rawMask, 5, 5, GRID_WIDTH - 5, GRID_HEIGHT - 5);
}

function maskBounds(mask) {
  const points = [];
  mask.forEach((row, y) => row.forEach((value, x) => { if (value) points.push([x, y]); }));
  if (points.length < 12) return null;
  return { x0: Math.min(...points.map(([x]) => x)), y0: Math.min(...points.map(([, y]) => y)), x1: Math.max(...points.map(([x]) => x)) + 1, y1: Math.max(...points.map(([, y]) => y)) + 1 };
}

function autoRegion(first, second) {
  const bounds = [maskBounds(candidateMask(first)), maskBounds(candidateMask(second))].filter(Boolean);
  if (!bounds.length) return { roi: roiConfig(), detected: false };
  const marginX = Math.max(5, Math.round((Math.max(...bounds.map((box) => box.x1 - box.x0)) * .18)));
  const marginY = Math.max(5, Math.round((Math.max(...bounds.map((box) => box.y1 - box.y0)) * .18)));
  let x0 = Math.max(5, Math.min(...bounds.map((box) => box.x0)) - marginX); let y0 = Math.max(5, Math.min(...bounds.map((box) => box.y0)) - marginY);
  let x1 = Math.min(GRID_WIDTH - 5, Math.max(...bounds.map((box) => box.x1)) + marginX); let y1 = Math.min(GRID_HEIGHT - 5, Math.max(...bounds.map((box) => box.y1)) + marginY);
  const minWidth = 16; const minHeight = 12;
  if (x1 - x0 < minWidth) { const centre = (x0 + x1) / 2; x0 = Math.max(5, Math.round(centre - minWidth / 2)); x1 = Math.min(GRID_WIDTH - 5, x0 + minWidth); }
  if (y1 - y0 < minHeight) { const centre = (y0 + y1) / 2; y0 = Math.max(5, Math.round(centre - minHeight / 2)); y1 = Math.min(GRID_HEIGHT - 5, y0 + minHeight); }
  return { roi: { x: x0 / GRID_WIDTH * 100, y: y0 / GRID_HEIGHT * 100, width: (x1 - x0) / GRID_WIDTH * 100, height: (y1 - y0) / GRID_HEIGHT * 100 }, detected: true };
}

function findTranslation(first, second, roi) {
  const x0 = Math.floor(roi.x / 100 * GRID_WIDTH); const y0 = Math.floor(roi.y / 100 * GRID_HEIGHT); const x1 = Math.ceil((roi.x + roi.width) / 100 * GRID_WIDTH); const y1 = Math.ceil((roi.y + roi.height) / 100 * GRID_HEIGHT);
  let best = { dx: 0, dy: 0, error: Infinity };
  for (let dy = -10; dy <= 10; dy += 2) for (let dx = -10; dx <= 10; dx += 2) {
    let error = 0; let count = 0;
    for (let y = y0; y < y1; y += 2) for (let x = x0; x < x1; x += 2) {
      const alignedX = x + dx; const alignedY = y + dy;
      if (alignedX < 0 || alignedX >= GRID_WIDTH || alignedY < 0 || alignedY >= GRID_HEIGHT) continue;
      const difference = first.grayscale[y * GRID_WIDTH + x] - second.grayscale[alignedY * GRID_WIDTH + alignedX]; error += difference * difference; count += 1;
    }
    if (count && error / count < best.error) best = { dx, dy, error: error / count };
  }
  return { dx: best.dx, dy: best.dy, score: Math.max(0, Math.min(1, 1 - best.error * 4)) };
}

function translateMask(mask, alignment) {
  const registered = Array.from({ length: GRID_HEIGHT }, () => Array(GRID_WIDTH).fill(false));
  mask.forEach((row, y) => row.forEach((value, x) => {
    if (!value) return;
    const baselineX = x - alignment.dx; const baselineY = y - alignment.dy;
    if (baselineX >= 0 && baselineX < GRID_WIDTH && baselineY >= 0 && baselineY < GRID_HEIGHT) registered[baselineY][baselineX] = true;
  }));
  return registered;
}

function suggestedMarkerPixels(entry, sample) {
  const points = [];
  for (let y = 4; y < GRID_HEIGHT * .45; y += 1) for (let x = 4; x < GRID_WIDTH * .48; x += 1) {
    const index = (y * GRID_WIDTH + x) * 4; const r = sample.pixels[index] / 255; const g = sample.pixels[index + 1] / 255; const b = sample.pixels[index + 2] / 255;
    if (Math.min(r, g, b) > .82 && Math.max(r, g, b) - Math.min(r, g, b) < .18) points.push([x, y]);
  }
  if (points.length < 30) return null;
  const x0 = Math.min(...points.map(([x]) => x)); const y0 = Math.min(...points.map(([, y]) => y)); const x1 = Math.max(...points.map(([x]) => x)); const y1 = Math.max(...points.map(([, y]) => y)); const width = x1 - x0 + 1; const height = y1 - y0 + 1;
  if (width < 5 || width / Math.max(1, height) < 1.4 || width / Math.max(1, height) > 12) return null;
  return Math.round(width * entry.width / GRID_WIDTH);
}

function runAutoSetup() {
  if (!state.images.baseline || !state.images.followup) { $("autoSetupStatus").textContent = "Add both photos to start."; return; }
  try {
    const first = sampleImage(state.images.baseline); const second = sampleImage(state.images.followup); const region = autoRegion(first, second);
    ["roiX", "roiY", "roiWidth", "roiHeight"].forEach((id, index) => { $(id).value = [region.roi.x, region.roi.y, region.roi.width, region.roi.height][index].toFixed(1); });
    const alignment = findTranslation(first, second, region.roi); const suggestedBaseline = suggestedMarkerPixels(state.images.baseline, first); const suggestedFollowup = suggestedMarkerPixels(state.images.followup, second);
    if (suggestedBaseline) $("baselineMarkerPx").value = suggestedBaseline; if (suggestedFollowup) $("followupMarkerPx").value = suggestedFollowup; $("scaleConfirmed").checked = false;
    const regionLabel = region.detected ? "region found" : "using the advanced region"; const scaleLabel = suggestedBaseline && suggestedFollowup ? "scale suggested—confirm it below" : "scale marker pixels still need entry";
    $("autoSetupStatus").textContent = `${regionLabel} · alignment ${Math.round(alignment.score * 100)}% · ${scaleLabel}.`;
    updateForm();
  } catch (error) { $("autoSetupStatus").textContent = `Automatic setup needs help: ${error.message}`; }
}

function qualityReport(first, second, alignment) {
  const components = { scaleMarker: first.mmPerPixel && second.mmPerPixel && $("scaleConfirmed").checked ? 1 : 0, poseAlignment: alignment.score, lightingConsistency: lightingScore(first, second), segmentationReviewed: $("reviewedMask").checked ? 1 : 0, imageQuality: Math.min(imageQuality(first), imageQuality(second)) };
  const score = Object.values(components).reduce((sum, value) => sum + value, 0) / Object.values(components).length;
  const flags = []; if (!components.scaleMarker) flags.push("scale_not_confirmed"); if (components.poseAlignment < .75) flags.push("pose_not_comparable"); if (components.lightingConsistency < .75) flags.push("lighting_not_comparable"); if (!components.segmentationReviewed) flags.push("segmentation_not_reviewed"); if (components.imageQuality < .6) flags.push("low_image_quality");
  return { score, components, flags, usable: !flags.length && score >= .75 };
}

function imageQuality(sample) { return sample.mean > .06 && sample.mean < .94 && sample.contrast > .035 ? 1 : .45; }

function comparePair() {
  if (!state.images.baseline || !state.images.followup) throw new Error("Add both photos first.");
  const roi = roiConfig(); const sensitivity = numberValue("sensitivity", 1); const first = segmentPhoto(state.images.baseline, roi, sensitivity); const second = segmentPhoto(state.images.followup, roi, sensitivity);
  const alignment = findTranslation(first, second, roi); const registeredSecondMask = translateMask(second.mask, alignment); const secondColorFractions = colorFractions(second, registeredSecondMask); const firstMetrics = maskMetrics(first.mask, first.metricScale); const secondMetrics = maskMetrics(registeredSecondMask, second.metricScale); const areaReduction = firstMetrics.areaMm2 ? (firstMetrics.areaMm2 - secondMetrics.areaMm2) / firstMetrics.areaMm2 * 100 : null; const meanPerimeter = (firstMetrics.perimeterMm + secondMetrics.perimeterMm) / 2; const linearChange = meanPerimeter ? (firstMetrics.areaMm2 - secondMetrics.areaMm2) / meanPerimeter : null; const daysBetween = numberValue("daysBetween", null); const areaReductionPerWeekPercent = areaReduction !== null && daysBetween > 0 ? areaReduction * 7 / daysBetween : null;
  const signal = imageSignal(first, second, roi, alignment); const quality = qualityReport(first, second, alignment); const tissue = { baseline: first.colorFractions, followup: secondColorFractions }; const result = { capturedAt: new Date().toISOString(), roi, baseline: { name: state.images.baseline.name, width: state.images.baseline.width, height: state.images.baseline.height, metrics: firstMetrics, colorFractions: first.colorFractions, mmPerPixel: first.mmPerPixel }, followup: { name: state.images.followup.name, width: state.images.followup.width, height: state.images.followup.height, metrics: secondMetrics, colorFractions: secondColorFractions, mmPerPixel: second.mmPerPixel }, change: { areaReductionMm2: firstMetrics.areaMm2 - secondMetrics.areaMm2, areaReductionPercent: areaReduction, areaReductionPerWeekPercent, perimeterPercent: firstMetrics.perimeterMm ? (secondMetrics.perimeterMm - firstMetrics.perimeterMm) / firstMetrics.perimeterMm * 100 : null, linearEdgeChangeMm: linearChange, daysBetween }, imageSignal: signal, alignment, quality, tissue, sensitivity };
  state.result = result; renderResult(result, first, second); return result;
}

function renderResult(result, first, second) {
  $("resultsSection").hidden = false; const usable = result.quality.usable; const area = result.change.areaReductionPercent; const stateLabel = $("resultState"); stateLabel.textContent = usable ? "Comparable with review" : "Review required"; stateLabel.classList.toggle("ready", usable);
  $("summaryTitle").textContent = usable ? (area !== null && area >= 5 ? "Area is smaller in the later photo" : area !== null && area <= -5 ? "Area is larger in the later photo" : "No clear area change") : "The pair needs review before interpretation";
  $("summaryText").textContent = usable ? "The calibrated photo measurements show a change in wound geometry. Confirm the outlines and interpret alongside the clinical assessment." : `The result is provisional because ${result.quality.flags.join(", ").replaceAll("_", " ")}.`;
  $("areaReduction").textContent = result.change.areaReductionPercent === null ? "—" : `${result.change.areaReductionPercent >= 0 ? "−" : "+"}${format(Math.abs(result.change.areaReductionPercent), 1)}%`;
  $("areaReductionUnit").textContent = result.baseline.metrics.areaMm2 ? `${format(result.change.areaReductionMm2, 1)} mm² baseline → later` : "outline not detected";
  $("metricArea").textContent = `${format(result.baseline.metrics.areaMm2, 1)} → ${format(result.followup.metrics.areaMm2, 1)}`; $("metricAreaDetail").textContent = result.change.areaReductionPerWeekPercent === null ? "mm² · earlier → later" : `mm² · ${format(result.change.areaReductionPerWeekPercent, 1)}% / week`;
  $("metricPerimeter").textContent = `${format(result.baseline.metrics.perimeterMm, 1)} → ${format(result.followup.metrics.perimeterMm, 1)} mm`; $("metricLongest").textContent = `${format(result.baseline.metrics.longestMm, 1)} → ${format(result.followup.metrics.longestMm, 1)} mm`; $("metricLinear").textContent = result.change.linearEdgeChangeMm === null ? "—" : `${result.change.linearEdgeChangeMm >= 0 ? "−" : "+"}${format(Math.abs(result.change.linearEdgeChangeMm), 1)} mm`;
  $("ssimValue").textContent = format(result.imageSignal.ssim, 2); $("ssimDetail").textContent = format(result.imageSignal.ssim, 2); $("changedFraction").textContent = `${format(result.imageSignal.changedFraction * 100, 1)}%`; $("circularityDetail").textContent = `${format(result.baseline.metrics.circularity, 2)} → ${format(result.followup.metrics.circularity, 2)}`; $("colorMixDetail").textContent = `${format(result.baseline.colorFractions.red * 100, 0)}% red → ${format(result.followup.colorFractions.red * 100, 0)}%`; $("qualityScore").textContent = `${Math.round(result.quality.score * 100)} / 100`; $("qualityScore").classList.toggle("ready", usable);
  const qualityLabels = { scaleMarker: "Scale reference", poseAlignment: "Frame alignment", lightingConsistency: "Lighting consistency", segmentationReviewed: "Outline review", imageQuality: "Photo quality" };
  $("qualityList").replaceChildren(...Object.entries(result.quality.components).map(([key, value]) => { const item = document.createElement("div"); item.className = `quality-item ${value < .75 ? "warn" : ""}`; const label = document.createElement("span"); label.textContent = qualityLabels[key] || key; const score = document.createElement("strong"); score.textContent = `${Math.round(value * 100)}%`; item.append(label, score); return item; }));
  drawOverlay("baselineCanvas", state.images.baseline.image, first); drawOverlay("followupCanvas", state.images.followup.image, second); $("resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
}

function drawOverlay(canvasId, image, segmentation) {
  const canvas = $(canvasId); const context = canvas.getContext("2d"); context.clearRect(0, 0, canvas.width, canvas.height); context.drawImage(image, 0, 0, canvas.width, canvas.height); const cellWidth = canvas.width / GRID_WIDTH; const cellHeight = canvas.height / GRID_HEIGHT; context.fillStyle = "rgba(239, 118, 109, .36)"; context.strokeStyle = "rgba(255, 180, 170, .95)"; context.lineWidth = 1;
  segmentation.mask.forEach((row, y) => row.forEach((value, x) => { if (value) context.fillRect(x * cellWidth, y * cellHeight, cellWidth + .5, cellHeight + .5); }));
  context.strokeRect(segmentation.roi.x0 * cellWidth, segmentation.roi.y0 * cellHeight, (segmentation.roi.x1 - segmentation.roi.x0) * cellWidth, (segmentation.roi.y1 - segmentation.roi.y0) * cellHeight);
}

function updateForm() { $("comparePair").disabled = !(state.images.baseline && state.images.followup); $("formMessage").textContent = state.images.baseline && state.images.followup ? "Ready. Confirm scale, compare, then review both outlines." : "Add both photos to begin."; }

function saveResult() {
  if (!state.result) return; const record = { id: `pair-${Date.now()}`, captured_at: state.result.capturedAt, earlier_image: state.result.baseline.name, later_image: state.result.followup.name, change: state.result.change, image_signal: state.result.imageSignal, quality: state.result.quality, tissue: state.result.tissue, context: { exudate: $("exudate").value, tissue: $("tissueContext").value, periwound: $("periwound").value } }; state.history = [record, ...state.history].slice(0, 20); saveHistory(); renderHistory(); $("formMessage").textContent = "Numeric result saved locally. Images were not saved.";
}

function downloadResult() { if (!state.result) return; const blob = new Blob([JSON.stringify({ ...state.result, context: { exudate: $("exudate").value, tissue: $("tissueContext").value, periwound: $("periwound").value } }, null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "depthline-paired-comparison.json"; link.click(); URL.revokeObjectURL(link.href); }

function renderHistory() { const list = $("historyList"); if (!state.history.length) { list.replaceChildren(Object.assign(document.createElement("p"), { className: "helper", textContent: "No numeric comparisons saved on this device." })); return; } list.replaceChildren(...state.history.map((record) => { const item = document.createElement("div"); item.className = "history-item"; const label = document.createElement("span"); label.textContent = `${new Date(record.captured_at).toLocaleDateString()} · ${record.earlier_image} → ${record.later_image}`; const value = document.createElement("strong"); value.textContent = record.change.areaReductionPercent === null ? "uncalibrated" : `${format(record.change.areaReductionPercent, 1)}% area`; item.append(label, value); return item; })); }

function resetPair() { Object.values(state.images).forEach((entry) => { if (entry?.src) URL.revokeObjectURL(entry.src); }); state.images = { baseline: null, followup: null }; state.result = null; $("baselineFile").value = ""; $("followupFile").value = ""; $("scaleConfirmed").checked = false; $("reviewedMask").checked = false; $("autoSetupStatus").textContent = "Add both photos to start."; $("resultsSection").hidden = true; drawPhotoPreview("baseline"); drawPhotoPreview("followup"); updateForm(); window.scrollTo({ top: 0, behavior: "smooth" }); }

function syntheticImage(woundScale) {
  const canvas = document.createElement("canvas"); canvas.width = 640; canvas.height = 480; const context = canvas.getContext("2d"); context.fillStyle = "#c98f76"; context.fillRect(0, 0, canvas.width, canvas.height); context.fillStyle = "rgba(230, 167, 142, .45)"; context.fillRect(0, 0, canvas.width, canvas.height); context.strokeStyle = "#faf4d2"; context.lineWidth = 10; context.strokeRect(44, 34, 100, 42); context.fillStyle = "#9f443d"; context.beginPath(); context.ellipse(330, 260, 100 * woundScale, 75 * woundScale, -.16, 0, Math.PI * 2); context.fill(); context.fillStyle = "#d1a34e"; context.beginPath(); context.ellipse(315, 245, 36 * woundScale, 21 * woundScale, .2, 0, Math.PI * 2); context.fill(); return canvas.toDataURL("image/png");
}

function loadSyntheticPair() { Promise.all([createImageBitmapFromFile(dataUrlToFile(syntheticImage(1), "synthetic-earlier.png")), createImageBitmapFromFile(dataUrlToFile(syntheticImage(.72), "synthetic-later.png"))]).then(([baseline, followup]) => { Object.values(state.images).forEach((entry) => { if (entry?.src) URL.revokeObjectURL(entry.src); }); state.images = { baseline, followup }; $("baselineMarkerPx").value = 100; $("followupMarkerPx").value = 100; $("roiX").value = 20; $("roiY").value = 20; $("roiWidth").value = 60; $("roiHeight").value = 60; $("scaleConfirmed").checked = true; $("reviewedMask").checked = false; drawPhotoPreview("baseline"); drawPhotoPreview("followup"); updateForm(); runAutoSetup(); $("scaleConfirmed").checked = true; }).catch((error) => { $("formMessage").textContent = error.message; }); }

function dataUrlToFile(dataUrl, name) { const [header, body] = dataUrl.split(","); const bytes = atob(body); const array = new Uint8Array(bytes.length); for (let index = 0; index < bytes.length; index += 1) array[index] = bytes.charCodeAt(index); return new File([array], name, { type: header.match(/:(.*?);/)[1] }); }

async function updateDepthApiStatus() { const status = $("depthApiStatus"); try { const capability = await getWebXRDepthCapability(); status.textContent = capability.supported ? "Device depth available" : "Photo mode · local only"; status.title = capability.reason; status.classList.toggle("available", capability.supported); } catch { status.textContent = "Photo mode · local only"; } }

$("baselineFile").addEventListener("change", (event) => { if (event.target.files?.[0]) loadPhoto("baseline", event.target.files[0]); });
$("followupFile").addEventListener("change", (event) => { if (event.target.files?.[0]) loadPhoto("followup", event.target.files[0]); });
$("loadDemo").addEventListener("click", loadSyntheticPair);
$("autoSetup").addEventListener("click", runAutoSetup);
$("comparePair").addEventListener("click", () => { try { comparePair(); $("formMessage").textContent = "Outline generated locally. Review it before saving."; } catch (error) { $("formMessage").textContent = error.message; } });
$("sensitivity").addEventListener("input", (event) => { $("sensitivityValue").textContent = Number(event.target.value).toFixed(1); if (state.result) { try { comparePair(); } catch { /* keep the last valid result visible */ } } });
["scaleConfirmed", "reviewedMask", "markerWidthMm", "baselineMarkerPx", "followupMarkerPx", "daysBetween", "roiX", "roiY", "roiWidth", "roiHeight"].forEach((id) => $(id).addEventListener("change", () => { updateForm(); if (state.result) { try { comparePair(); } catch { /* keep the last valid result visible */ } } }));
$("saveResult").addEventListener("click", saveResult); $("downloadResult").addEventListener("click", downloadResult); $("resetPair").addEventListener("click", resetPair);
$("clearHistory").addEventListener("click", () => { if (!confirm("Clear saved numeric comparisons from this device?")) return; state.history = []; saveHistory(); renderHistory(); });

renderHistory(); drawPhotoPreview("baseline"); drawPhotoPreview("followup"); updateForm(); updateDepthApiStatus();
