// eGarage documentos_form_patch.js · Hotfix mejorado (debounce + CSRF + dropdown + nextNumber)
console.log("🔥 documentos_form_patch.js cargado");

(function () {
  const DEBUG = true; // pon false en prod para silenciar logs

  const $  = (s, c=document) => c.querySelector(s);
  const $$ = (s, c=document) => Array.from(c.querySelectorAll(s));
  const on = (el, ev, fn) => el && el.addEventListener(ev, fn);
  const log = (...a) => DEBUG && console.log(...a);
  const warn = (...a) => DEBUG && console.warn(...a);
  const err = (...a) => console.error(...a);

  // --- CSRF helpers (Django) ---
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : "";
  }
  const CSRF = getCookie('csrftoken');

  // --- Fetch JSON con abort + CSRF ---
  function fetchJSON(url, { signal } = {}) {
    return fetch(url, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": CSRF },
      credentials: "same-origin",
      signal,
    }).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status} @ ${url}`);
      return r.json().catch(() => ({}));
    });
  }

  // --- Debounce ---
  function debounce(fn, wait = 250) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), wait);
    };
  }

  // --- Estado global mínimo ---
  const state = {
    selectedClientId: null,
    controllers: {
      clientes: null,
      vehiculos: null,
      repuestos: null,
      servicios: null,
      otros: null,
    },
  };

  // --- Config/Endpoints desde data-* del <body> ---
  const body = document.body;
  const cfg = {
    clientes:   body.dataset.endpointClientes || "",
    vehiculos:  body.dataset.endpointVehiculosCliente || "",
    repuestos:  body.dataset.endpointRepuestos || "",
    servicios:  body.dataset.endpointServicios || "",
    otros:      body.dataset.endpointOtros || "",
    nextNumber: body.dataset.endpointNextNumber || "",
    saveUrl:    body.dataset.saveUrl || "",
  };
  log("⚙️ PATCH init cfg:", cfg);

  // --- Elementos del DOM (IDs reales del template) ---
  const inpCliente  = $("#client-search");
  const ddCliente   = $("#client-results");
  const inpVehiculo = $("#vehicle-search");
  const ddVehiculo  = $("#vehicle-results");

  const inpRep      = $("#quick-rep-search");
  const ddRep       = $("#quick-rep-results");
  const inpServ     = $("#quick-serv-search");
  const ddServ      = $("#quick-serv-results");
  const inpOtros    = $("#quick-otros-search");
  const ddOtros     = $("#quick-otros-results");

  const selTipo     = $("#id_tipo");
  const numeroPrev  = $("#numero_preview"); // span/div donde mostramos el próximo número
  const fechaInput  = $("#id_fecha_emision"); // asegúrate que exista; setea fecha hoy por defecto

  log("⌨️ inputs:", { inpCliente, inpVehiculo, inpRep, inpServ, inpOtros, selTipo, numeroPrev });

  // --- Utils de Dropdown mínimo ---
  function renderList(container, items, { label = "name", sublabel = null } = {}, onPick) {
    if (!container) return;
    container.innerHTML = "";
    container.classList.add("eg-dd-open"); // usa esta clase para mostrar/ocultar con CSS

    const ul = document.createElement("ul");
    ul.className = "eg-dd";
    items.forEach((it) => {
      const li = document.createElement("li");
      li.tabIndex = 0;
      li.className = "eg-dd-item";
      li.innerHTML = `
        <div class="eg-dd-title">${(it[label] ?? "").toString()}</div>
        ${sublabel && it[sublabel] ? `<div class="eg-dd-sub">${(it[sublabel] ?? "").toString()}</div>` : ""}
      `;
      li.addEventListener("click", () => onPick && onPick(it));
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter") onPick && onPick(it);
      });
      ul.appendChild(li);
    });
    container.appendChild(ul);

    // Cerrar si clic fuera
    const onDocClick = (e) => {
      if (!container.contains(e.target)) {
        container.classList.remove("eg-dd-open");
        document.removeEventListener("click", onDocClick);
      }
    };
    setTimeout(() => document.addEventListener("click", onDocClick), 0);
  }

  function closeList(container) {
    if (container) container.classList.remove("eg-dd-open");
  }

  // --- Handlers de búsqueda genéricos ---
  function makeSearchHandler({ input, dropdown, endpointKey, queryParam = "q", extraParams = () => ({}) , itemShape, onPick }) {
    if (!input || !dropdown) return () => {};
    const doSearch = debounce(async () => {
      const q = input.value.trim();
      if (!q) { closeList(dropdown); return; }

      const endpoint = cfg[endpointKey];
      if (!endpoint) { warn(`No endpoint for ${endpointKey}`); return; }

      // cancelar búsqueda previa
      if (state.controllers[endpointKey]) state.controllers[endpointKey].abort();
      const controller = new AbortController();
      state.controllers[endpointKey] = controller;

      const params = new URLSearchParams({ [queryParam]: q, ...extraParams() });
      const url = `${endpoint}?${params.toString()}`;
      log(`🌐 ${endpointKey} ->`, url);

      try {
        const data = await fetchJSON(url, { signal: controller.signal });
        const items = Array.isArray(data?.results) ? data.results : (Array.isArray(data) ? data : []);
        renderList(dropdown, items, itemShape, onPick);
      } catch (e) {
        if (e.name !== "AbortError") err(`❌ ${endpointKey} search`, e);
      }
    }, 250);

    on(input, "input", doSearch);
    on(input, "keydown", (e) => {
      if (e.key === "Escape") closeList(dropdown);
    });

    return doSearch; // por si quieres disparar manualmente
  }

  // --- Cliente: al seleccionar, guardamos ID y limpiamos vehículo ---
  const searchClientes = makeSearchHandler({
    input: inpCliente,
    dropdown: ddCliente,
    endpointKey: "clientes",
    itemShape: { label: "name", sublabel: "rut" }, // ajusta a tu JSON (name/rut/email/etc.)
    onPick: (item) => {
      state.selectedClientId = item.id;
      inpCliente.value = item.name || "";
      closeList(ddCliente);
      // limpiar vehículo cuando cambia cliente
      if (inpVehiculo) inpVehiculo.value = "";
      if (ddVehiculo) closeList(ddVehiculo);
      log("👤 Cliente seleccionado:", item);
    },
  });

  // --- Vehículo: filtra por cliente seleccionado (si hay) ---
  const searchVehiculos = makeSearchHandler({
    input: inpVehiculo,
    dropdown: ddVehiculo,
    endpointKey: "vehiculos",
    extraParams: () => (state.selectedClientId ? { cliente_id: state.selectedClientId } : {}),
    itemShape: { label: "display", sublabel: "patente" }, // ajusta a tu JSON (display/patente/vin/etc.)
    onPick: (item) => {
      inpVehiculo.value = item.display || item.patente || item.vin || "";
      closeList(ddVehiculo);
      log("🚗 Vehículo seleccionado:", item);
    },
  });

  // --- Repuestos / Servicios / Otros ---
  const searchRep = makeSearchHandler({
    input: inpRep, dropdown: ddRep, endpointKey: "repuestos",
    itemShape: { label: "name", sublabel: "part_number" },
    onPick: (item) => {
      inpRep.value = "";
      closeList(ddRep);
      // TODO: aquí insertar la línea en la tabla (tu función existente addRepuesto(item))
      log("🔩 Repuesto elegido:", item);
    },
  });

  const searchServ = makeSearchHandler({
    input: inpServ, dropdown: ddServ, endpointKey: "servicios",
    itemShape: { label: "name", sublabel: "categoria" },
    onPick: (item) => {
      inpServ.value = "";
      closeList(ddServ);
      // TODO: insertar línea de servicio (addServicio(item))
      log("🛠️ Servicio elegido:", item);
    },
  });

  const searchOtros = makeSearchHandler({
    input: inpOtros, dropdown: ddOtros, endpointKey: "otros",
    itemShape: { label: "name", sublabel: "empresa_externa" },
    onPick: (item) => {
      inpOtros.value = "";
      closeList(ddOtros);
      // TODO: insertar línea de otro servicio (addOtroServicio(item))
      log("🤝 Otro servicio elegido:", item);
    },
  });

  // --- Fecha por defecto (hoy) si está vacío ---
  (function ensureToday() {
    if (!fechaInput) return;
    if (!fechaInput.value) {
      const now = new Date();
      const y = now.getFullYear();
      const m = String(now.getMonth() + 1).padStart(2, "0");
      const d = String(now.getDate()).padStart(2, "0");
      fechaInput.value = `${y}-${m}-${d}`;
      log("📆 fecha_emision seteada:", fechaInput.value);
    }
  })();

  // --- Next Number preview al cambiar el tipo ---
  async function refreshNumeroPreview() {
    if (!selTipo || !numeroPrev || !cfg.nextNumber) return;
    const tipo = selTipo.value;
    if (!tipo) return;
    const url = `${cfg.nextNumber}?tipo=${encodeURIComponent(tipo)}`;
    log("🔢 nextNumber ->", url);
    try {
      const data = await fetchJSON(url);
      // espera { "numero": "EST-001" } o similar
      numeroPrev.textContent = data?.numero || "—";
    } catch (e) {
      warn("No se pudo obtener nextNumber", e);
      numeroPrev.textContent = "—";
    }
  }
  on(selTipo, "change", refreshNumeroPreview);
  // primer render si ya hay tipo seleccionado
  if (selTipo && selTipo.value) refreshNumeroPreview();

  // --- Smoke test opcional de endpoints ---
  (function smoke() {
    log("🧪 Testing endpoints...");
    const tests = [
      ["clientes", "clientes"],
      ["repuestos", "repuestos"],
      ["servicios", "servicios"],
      ["otros", "otros"],
    ];
    tests.forEach(([key, name]) => {
      if (!cfg[key]) return;
      const url = `${cfg[key]}?q=test`;
      fetch(url, { credentials: "same-origin", headers: {"X-Requested-With":"XMLHttpRequest"} })
        .then(r => log(`✅ ${name}`, r.status, r.headers.get("content-type")))
        .catch(e => err(`❌ ${name}`, e));
    });
  })();

})();
