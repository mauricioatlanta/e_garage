// eGarage documentos_form_new.js · v9-rescue
(() => {
  const version = "v9-rescue-" + new Date().toISOString();
  console.log("documentos_form_new.js", version);

  const $  = (s, c=document) => c.querySelector(s);
  const trail = (u) => (u && !u.endsWith("/") ? u + "/" : u);

  function getDataset() {
    const el = $("#doc-data");
    return el ? el.dataset : (document.body ? document.body.dataset : {});
  }
  const fromDataset = (() => {
    const ds = getDataset();
    return {
      clientes: ds.endpointClientes,
      vehiculosCliente: ds.endpointVehiculosCliente,
      repuestos: ds.endpointRepuestos,
      servicios: ds.endpointServicios,
      otros: ds.endpointOtros,
      nextNumber: ds.endpointNextNumber,
      saveUrl: ds.saveUrl,
      country: ds.country,
      taxRate: ds.taxRate,
    };
  })();

  function inferByPath() {
    const m = location.pathname.match(/^(.*?\/documentos)\//);
    if (!m) return {};
    const pref = m[1] + "/api";
    return {
      clientes:        `${pref}/clientes/`,
      vehiculosCliente:`${pref}/vehiculos-cliente/0/`,
      repuestos:       `${pref}/repuestos/`,
      servicios:       `${pref}/servicios/`,
      otros:           `${pref}/otros-servicios/`,
      nextNumber:      `${pref}/next-number/`,
      saveUrl:         `${pref}/save/`,
      country:         "US",
      taxRate:         "",
    };
  }

  let CFG = { ...inferByPath(), ...fromDataset, ...window.__DOC_CFG__ };
  ["clientes","vehiculosCliente","repuestos","servicios","otros","nextNumber"].forEach(k=>{
    CFG[k] = trail(CFG[k] || "");
  });
  window.__DOC_CFG__ = CFG;
  console.table(CFG);

  (function mirrorCFGtoDataset() {
    function ensureDocData() {
      let el = $("#doc-data");
      if (!el) { el = document.createElement("div"); el.id = "doc-data"; document.body.appendChild(el); }
      return el;
    }
    const targets = [document.body, ensureDocData()];
    targets.forEach((t) => {
      if (!t || !t.dataset) return;
      t.dataset.endpointClientes = CFG.clientes || "";
      t.dataset.endpointVehiculosCliente = CFG.vehiculosCliente || "";
      t.dataset.endpointRepuestos = CFG.repuestos || "";
      t.dataset.endpointServicios = CFG.servicios || "";
      t.dataset.endpointOtros = CFG.otros || "";
      t.dataset.endpointNextNumber = CFG.nextNumber || "";
      t.dataset.saveUrl = CFG.saveUrl || "";
      t.dataset.country = CFG.country || "";
      t.dataset.taxRate = CFG.taxRate || "";
    });
  })();

  async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, { headers: { Accept: "application/json" }, ...opts });
    const ct = res.headers.get("content-type") || "";
    if (!res.ok) {
      if (ct.includes("application/json")) {
        const err = await res.json().catch(() => ({}));
        throw new Error(`HTTP ${res.status} ${res.statusText} ${JSON.stringify(err)}`);
      } else {
        const head = (await res.text()).slice(0, 160);
        throw new Error(`HTTP ${res.status} non-JSON. Head: ${head}`);
      }
    }
    if (!ct.includes("application/json")) {
      const head = (await res.text()).slice(0, 160);
      throw new Error(`Non-JSON response (ct=${ct}). Head: ${head}`);
    }
    return res.json();
  }
  const asArray = (d) => (Array.isArray(d) ? d : d && Array.isArray(d.results) ? d.results : []);

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
    return (data && (data.next || data.numero || data.id)) || "";
  }

  window.__api = {
    fetchJSON, asArray,
    buscarClientes, buscarVehiculosCliente,
    buscarRepuestos, buscarServicios, buscarOtros,
    pedirNextNumber,
    async testAll() {
      const urls = [
        CFG.clientes + "?q=a",
        CFG.vehiculosCliente,
        CFG.repuestos + "?q=a",
        CFG.servicios + "?q=a",
        CFG.otros + "?q=a",
        CFG.nextNumber,
      ];
      for (const u of urls) {
        try {
          const r = await fetch(u, { headers: { Accept: "application/json" } });
          const ct = r.headers.get("content-type") || "";
          const head = (await r.text()).slice(0, 140);
          console.log("→", u, r.status, ct, "|", head);
        } catch (e) {
          console.error("X", u, e.message);
        }
      }
    },
  };
})();
