// ubicacion/static/ubicacion/js/ubicacion.js
// JS para formularios de ubicación con API unificada multi-país

document.addEventListener("DOMContentLoaded", () => {
  const estadoSelect = document.getElementById("id_estado");
  const ciudadSelect = document.getElementById("id_ciudad");
  const zipInput = document.getElementById("id_zip_code");

  if (!estadoSelect || !ciudadSelect) return;

  // Intenta sacar country desde data-attr o fallback CL
  const country = estadoSelect.dataset.country || "CL";

  async function fetchJSON(url) {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  function resetSelect(select, placeholder) {
    select.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    select.appendChild(opt);
  }

  // Cargar estados por país (si el select viene vacío)
  async function loadStatesIfNeeded() {
    if (estadoSelect.options.length > 1) return;

    resetSelect(estadoSelect, "Seleccione un estado...");
    try {
      const data = await fetchJSON(`/api/locations/states/?country=${encodeURIComponent(country)}`);
      (data.states || []).forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        estadoSelect.appendChild(opt);
      });
    } catch (e) {
      console.error("Error cargando estados:", e);
    }
  }

  async function loadCities(stateId) {
    resetSelect(ciudadSelect, "Seleccione una ciudad...");
    if (zipInput) zipInput.value = "";

    if (!stateId) return;

    try {
      const data = await fetchJSON(`/api/locations/cities/?state_id=${encodeURIComponent(stateId)}`);
      (data.cities || []).forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.name;
        // Guardar zip_code en dataset si existe
        if (c.zip_code) {
          opt.dataset.zip = c.zip_code;
        }
        ciudadSelect.appendChild(opt);
      });
      ciudadSelect.disabled = false;
    } catch (e) {
      console.error("Error cargando ciudades:", e);
      ciudadSelect.disabled = true;
    }
  }

  estadoSelect.addEventListener("change", () => {
    loadCities(estadoSelect.value);
  });

  if (ciudadSelect && zipInput) {
    ciudadSelect.addEventListener("change", () => {
      const selected = ciudadSelect.options[ciudadSelect.selectedIndex];
      if (selected && selected.dataset.zip) {
        zipInput.value = selected.dataset.zip;
      }
    });
  }

  // Init
  loadStatesIfNeeded().then(() => {
    // Si ya hay estado seleccionado (editar), carga ciudades
    if (estadoSelect.value) {
      loadCities(estadoSelect.value);
    } else {
      resetSelect(ciudadSelect, "Seleccione una ciudad...");
      ciudadSelect.disabled = true;
    }
  });
});
