const REFRESH_MS = 7500;
const MAX_HISTORY = 8;
let kpiHistory = [];

function updateSparkline(history) {
  const svg = document.getElementById("cdm-sparkline");
  if (!svg) return;
  const poly = svg.querySelector("polyline");
  if (history.length < 2) { poly.setAttribute("points", ""); return; }
  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;
  const points = history.map((v, i) => {
    const x = (i / (history.length - 1)) * 100;
    const y = 22 - ((v - min) / range) * 18;
    return `${x},${y}`;
  }).join(" ");
  poly.setAttribute("points", points);
}

async function pollKpi() {
  try {
    const res = await fetch("live-feed/");
    if (!res.ok) return;
    const data = await res.json();
    const count = data.kpis.en_taller;
    const el = document.getElementById("cdm-live-count");
    if (el) el.textContent = count;
    kpiHistory.push(count);
    if (kpiHistory.length > MAX_HISTORY) kpiHistory.shift();
    updateSparkline(kpiHistory);
  } catch (e) {
    console.error("kpi poll error", e);
  }
}

pollKpi();
setInterval(pollKpi, REFRESH_MS);
