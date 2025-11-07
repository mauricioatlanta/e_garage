// eGarage documentos_form.v8 ✅ (robusto, sin depender de dataset)
console.log("eGarage documentos_form.v8 ✅");

(function () {
  const $  = (s, c=document) => c.querySelector(s);
  const $$ = (s, c=document) => Array.from(c.querySelectorAll(s));

  // 1) Tomar CFG de window o inferir por ruta si falta
  const trail = u => (u && !u.endsWith("/")) ? (u + "/") : u;
  (function ensureCFG() {
    const existing = window.__DOC_CFG__ || {};
    if (!existing.clientes || !existing.repuestos || !existing.servicios) {
      const m = location.pathname.match(/^(.*?\/documentos)\//); // /us/documentos/form/
      const pref = m ? m[1] + "/api" : "";
      window.__DOC_CFG__ = {
        clientes:        trail(existing.clientes || (pref ? `${pref}/clientes/` : "")),
        vehiculosCliente:trail(existing.vehiculosCliente || (pref ? `${pref}/vehiculos-cliente/0/` : "")),
        repuestos:       trail(existing.repuestos || (pref ? `${pref}/repuestos/` : "")),
        servicios:       trail(existing.servicios || (pref ? `${pref}/servicios/` : "")),
        otros:           trail(existing.otros || `/api/otros-servicios/`),
        nextNumber:      trail(existing.nextNumber || (pref ? `${pref}/next-number/` : "")),
        saveUrl:         existing.saveUrl || (pref ? `${pref}/save/` : ""),
        country:         existing.country || "US",
        taxRate:         existing.taxRate || ""
      };
    } else {
      window.__DOC_CFG__ = { ...existing, // normaliza trailing slash
        clientes:        trail(existing.clientes),
        vehiculosCliente: trail(existing.vehiculosCliente),
        repuestos:       trail(existing.repuestos),
        servicios:       trail(existing.servicios),
        otros:           trail(existing.otros),
        nextNumber:      trail(existing.nextNumber),
      };
    }
  })();

  let CFG = window.__DOC_CFG__;
  window.__setDocCFG = (obj)=>{ CFG = { ...CFG, ...obj }; window.__DOC_CFG__ = CFG; console.table(CFG); };
  console.table(CFG);

  // 2) Fetch robusto (evita "Unexpected token <")
  async function fetchJSON(url, opts={}) {
    const res = await fetch(url, { headers: { "Accept": "application/json" }, ...opts });
    const ct  = res.headers.get("content-type") || "";
    if (!res.ok) {
      if (ct.includes("application/json")) {
        const err = await res.json().catch(()=>({}));
        throw new Error(`HTTP ${res.status} ${res.statusText} ${JSON.stringify(err)}`);
      } else {
        const head = (await res.text()).slice(0,160);
        throw new Error(`HTTP ${res.status} no-JSON. Posible login/HTML. Head: ${head}`);
      }
    }
    if (!ct.includes("application/json")) {
      const head = (await res.text()).slice(0,160);
      throw new Error(`Respuesta no JSON (ct=${ct}). Head: ${head}`);
    }
    return res.json();
  }
  const asArray = (data) => Array.isArray(data) ? data : (data && Array.isArray(data.results) ? data.results : []);

  // 3) Ejemplos de búsquedas (usa esto en tus autocompletados)
  async function buscarClientes(q) {
    const url = new URL(CFG.clientes, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString()));
  }
  async function buscarVehiculosCliente(clienteId) {
    const base = CFG.vehiculosCliente.replace(/\/0\/?$/, `/${clienteId}/`);
    return asArray(await fetchJSON(base));
  }
  async function buscarRepuestos(q) {
    const url = new URL(CFG.repuestos, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString()));
  }
  async function buscarServicios(q) {
    const url = new URL(CFG.servicios, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString()));
  }
  async function buscarOtros(q) {
    const url = new URL(CFG.otros, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString()));
  }
  async function pedirNextNumber() {
    const data = await fetchJSON(CFG.nextNumber);
    return data && (data.next || data.numero || data.id || "");
  }

  // 4) Wire mínimo para que puedas validar en consola
  window.__fetchJSON = fetchJSON;
  window.__asArray   = asArray;
  window.__api = {
    buscarClientes, buscarVehiculosCliente, buscarRepuestos, buscarServicios, buscarOtros, pedirNextNumber
  };

  // 5) (Opcional) Auto-test al cargar (comenta si molesta)
  (async () => {
    try {
      console.log("Ping clientes:", await buscarClientes("da"));
    } catch(e){ console.warn("Ping clientes FAIL:", e.message); }
    try {
      console.log("Ping repuestos:", await buscarRepuestos("fi"));
    } catch(e){ console.warn("Ping repuestos FAIL:", e.message); }
  })();

  // 6) A partir de aquí, tu código de UI debe usar SIEMPRE CFG.* y __api.*
  //    Ejemplo pseudo:
  // const $cli = $("#client-search"), $res = $("#client-results");
  // $cli.addEventListener("input", debounce(async (e)=>{
  //   const items = await __api.buscarClientes(e.target.value);
  //   renderDropdown($res, items);
  // }, 250));
})();
