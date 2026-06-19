const REFRESH_MS = 7500;

function initials(nombre) {
  return (nombre || "").split(" ").filter(Boolean).slice(0, 2)
    .map(p => p[0].toUpperCase()).join("");
}

function elapsed(isoTs) {
  const s = Math.floor((Date.now() - new Date(isoTs)) / 1000);
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function renderList(containerId, items, showTimer) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!items.length) {
    el.innerHTML = '<p class="cdm-empty">Sin registros</p>';
    return;
  }
  el.innerHTML = items.map(doc => {
    const tag = doc.url ? "a" : "div";
    const href = doc.url ? `href="${doc.url}"` : "";
    return `<${tag} ${href} class="cdm-card${doc.url ? " cdm-card--link" : ""}" data-ts="${doc.creado_en}">
      <p class="cdm-card-vehiculo">${doc.vehiculo || doc.patente || "—"}</p>
      <p class="cdm-card-patente">${doc.patente || ""}</p>
      <div class="cdm-card-footer">
        <span class="cdm-avatar">${initials(doc.tecnico)}</span>
        ${showTimer
          ? `<span class="cdm-elapsed">${elapsed(doc.creado_en)}</span>`
          : '<span class="cdm-check">&#10003;</span>'}
      </div>
    </${tag}>`;
  }).join("");
}

async function fetchLiveFeed() {
  try {
    const res = await fetch("../live-feed/");
    if (!res.ok) return;
    const data = await res.json();
    renderList("en-taller-list", data.en_taller, true);
    renderList("entregados-list", data.entregados_hoy, false);
    const kpiTaller = document.getElementById("kpi-en-taller");
    const kpiEntregados = document.getElementById("kpi-entregados");
    if (kpiTaller) kpiTaller.textContent = data.kpis.en_taller;
    if (kpiEntregados) kpiEntregados.textContent = data.kpis.entregados_hoy;
  } catch (e) {
    console.error("live-feed error", e);
  }
}

function tickElapsed() {
  document.querySelectorAll("#en-taller-list .cdm-elapsed").forEach(el => {
    el.textContent = elapsed(el.closest(".cdm-card").dataset.ts);
  });
}

fetchLiveFeed();
setInterval(fetchLiveFeed, REFRESH_MS);
setInterval(tickElapsed, 1000);
