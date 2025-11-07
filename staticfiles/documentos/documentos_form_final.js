// eGarage documentos_form_final.js · v12-final
(() => {
  const version = "v12-final-" + new Date().toISOString();
  console.log("🔥 documentos_form_final.js v12 cargado (token C1)");

  // ===== DEBUG HOOKS =====
  window.addEventListener('error', (e) => {
    console.error('🟥 window.onerror', e.message, e.filename, e.lineno, e.colno, e.error);
  });
  window.addEventListener('unhandledrejection', (e) => {
    console.error('🟧 unhandledrejection', e.reason);
  });

  // Fuerza DOM ready + init con retry
  (function ensureInit() {
    const start = () => {
      console.log('⚙️ init() start guard');
      if (typeof window.__startDocumentoUI === 'function') return window.__startDocumentoUI();
      if (typeof window.init === 'function') return window.init();
      setTimeout(() => {
        if (typeof window.__startDocumentoUI === 'function') return window.__startDocumentoUI();
        if (typeof window.init === 'function') return window.init();
        console.warn('⚠️ No encuentro __startDocumentoUI() ni init() tras retry');
      }, 300);
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start);
    } else {
      start();
    }
  })();

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
    if (!m) {
      console.warn('No se pudo inferir prefijo de documentos desde path:', location.pathname);
      return {};
    }
    const pref = m[1] + "/api";
    return {
      clientes:        `${pref}/clientes/`,
      vehiculosCliente:`${pref}/vehiculos-cliente/0/`,
      repuestos:       `${pref}/repuestos/`,
      servicios:       `${pref}/servicios/`,
      otros:           `${pref}/otros-servicios/`,
      nextNumber:      `${pref}/next-number/`,
      saveUrl:         `${pref}/save/`,
      country:         (location.pathname.startsWith('/cl/') ? 'CL' : 'US'),
      taxRate:         "",
    };
  }

  let CFG = { ...inferByPath(), ...fromDataset, ...window.__DOC_CFG__ };
  ["clientes","vehiculosCliente","repuestos","servicios","otros","nextNumber"].forEach(k=>{
    CFG[k] = trail(CFG[k] || "");
  });
  
  // Saneamiento de country y taxRate
  CFG.country = (CFG.country || 'US').toUpperCase();
  CFG.taxRate = Number(CFG.taxRate || 0) || 0;
  
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
    const status = res.status;
    const ct = (res.headers.get("content-type") || "").toLowerCase();

    if (status === 204) return {}; // ✅ No Content aceptado

    if (!res.ok) {
      if (ct.includes("application/json")) {
        const err = await res.json().catch(() => ({}));
        throw new Error(`HTTP ${status} ${res.statusText} ${JSON.stringify(err)}`);
      }
      const head = (await res.text()).slice(0, 160);
      throw new Error(`HTTP ${status} non-JSON. Head: ${head}`);
    }

    // Algunos backends devuelven 'application/json; charset=utf-8'
    if (!ct.includes("application/json")) {
      const text = (await res.text()).trim();
      // si viene vacío, lo tomamos como {}
      if (!text) return {};
      // si luce a JSON a pesar del content-type, intentamos parsear
      try { return JSON.parse(text); } catch (_) {
        const head = text.slice(0, 160);
        throw new Error(`Non-JSON response (ct=${ct}). Head: ${head}`);
      }
    }
    return res.json();
  }
  const asArray = (d) => {
    if (!d) return [];
    if (Array.isArray(d)) return d;
    if (Array.isArray(d.results)) return d.results;
    if (d.results && typeof d.results === 'object') return Object.values(d.results);
    return [];
  };

  // CSRF helper para POST
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  const CSRF = getCookie('csrftoken');

  async function postJSON(url, body) {
    return fetchJSON(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF,
        Accept: 'application/json',
      },
      body: JSON.stringify(body || {}),
    });
  }

  // Debounce + cancelación en búsquedas
  function makeSearcher(endpointFn) {
    let ctrl = null;
    return async function(q) {
      if (ctrl) ctrl.abort();
      ctrl = new AbortController();
      try {
        const res = await endpointFn(q, { signal: ctrl.signal });
        return res;
      } finally {
        ctrl = null;
      }
    };
  }

  const buscarClientesSafe = makeSearcher(async (q, opts={}) => {
    const url = new URL(CFG.clientes, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString(), opts));
  });
  async function buscarVehiculosCliente(clienteId) {
    const base = new URL(CFG.vehiculosCliente, location.origin);
    // si el path termina con /0/ lo reemplazamos; si no, agregamos `${clienteId}/`
    const parts = base.pathname.replace(/\/+$/,'').split('/');
    if (parts[parts.length - 1] === '0') {
      parts[parts.length - 1] = String(clienteId);
      base.pathname = parts.join('/') + '/';
    } else {
      if (!base.pathname.endsWith('/')) base.pathname += '/';
      base.pathname += String(clienteId) + '/';
    }
    return asArray(await fetchJSON(base.toString()));
  }
  const buscarRepuestosSafe = makeSearcher(async (q, opts={}) => {
    const url = new URL(CFG.repuestos, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString(), opts));
  });
  const buscarServiciosSafe = makeSearcher(async (q, opts={}) => {
    const url = new URL(CFG.servicios, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString(), opts));
  });
  const buscarOtrosSafe = makeSearcher(async (q, opts={}) => {
    const url = new URL(CFG.otros, location.origin);
    url.searchParams.set("q", q || "");
    return asArray(await fetchJSON(url.toString(), opts));
  });
  async function pedirNextNumber() {
    const data = await fetchJSON(CFG.nextNumber);
    return (data && (data.next || data.numero || data.id)) || "";
  }

  window.__api = {
    fetchJSON, asArray, postJSON,
    buscarClientes: buscarClientesSafe, buscarVehiculosCliente,
    buscarRepuestos: buscarRepuestosSafe, buscarServicios: buscarServiciosSafe, buscarOtros: buscarOtrosSafe,
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

  console.log("✅ eGarage documentos_form_final.js cargado correctamente");

  // Hook de fetch solo si debugFetch está habilitado
  (function hookFetch(){
    if (!CFG?.debugFetch) return;
    const ofetch = window.fetch;
    window.fetch = async function(...args){
      try {
        console.log('🌐 fetch -->', args[0]);
        const res = await ofetch.apply(this, args);
        console.log('🌐 fetch <--', res.status, res.headers.get('content-type'), args[0]);
        return res;
      } catch (err) {
        console.error('🌐 fetch error', args[0], err);
        throw err;
      }
    };
  })();

  // Dispara autocompletados visualmente (para saber que el keyup se engancha)
  ['quick-client-search','quick-rep-search','quick-serv-search','quick-otros-search'].forEach(id=>{
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', (e)=> console.log(`⌨️ input#${id}:`, e.target.value));
    } else {
      console.warn('🔸 Falta input:', id);
    }
  });

  // ===== SCROLL FUNCTIONALITY =====
  (function() {
    console.log('🔄 Initializing scroll functionality...');
    
    const scrollTopBtn = document.getElementById('btn-scroll-top');
    const scrollBottomBtn = document.getElementById('btn-scroll-bottom');
    
    console.log('🔍 Scroll buttons found:', {
      top: !!scrollTopBtn,
      bottom: !!scrollBottomBtn
    });
    
    if (scrollTopBtn) {
      scrollTopBtn.addEventListener('click', () => {
        console.log('🔼 Scroll to top clicked');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
    
    if (scrollBottomBtn) {
      scrollBottomBtn.addEventListener('click', () => {
        console.log('🔽 Scroll to bottom clicked');
        const maxScroll = Math.max(
          document.body.scrollHeight,
          document.documentElement.scrollHeight,
          document.body.offsetHeight,
          document.documentElement.offsetHeight,
          document.body.clientHeight,
          document.documentElement.clientHeight
        );
        window.scrollTo({ top: maxScroll, behavior: 'smooth' });
      });
    }
    
    // Mostrar/ocultar botones según posición del scroll
    function toggleScrollButtons() {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const windowHeight = window.innerHeight;
      const documentHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      
      const isScrollable = documentHeight > windowHeight;
      
      if (scrollTopBtn) {
        if (isScrollable && scrollTop > 100) {
          scrollTopBtn.style.display = 'block';
          scrollTopBtn.style.opacity = '1';
        } else {
          scrollTopBtn.style.display = 'none';
          scrollTopBtn.style.opacity = '0';
        }
      }
      
      if (scrollBottomBtn) {
        if (isScrollable && (scrollTop + windowHeight) < (documentHeight - 100)) {
          scrollBottomBtn.style.display = 'block';
          scrollBottomBtn.style.opacity = '1';
        } else {
          scrollBottomBtn.style.display = 'none';
          scrollBottomBtn.style.opacity = '0';
        }
      }
      
      // Debug info
      if (scrollTop % 100 === 0) { // Log every 100px of scroll
        console.log('📜 Scroll position:', {
          scrollTop,
          windowHeight,
          documentHeight,
          isScrollable,
          topVisible: scrollTopBtn?.style.display === 'block',
          bottomVisible: scrollBottomBtn?.style.display === 'block'
        });
      }
    }
    
    // Escuchar eventos de scroll solo si existen botones
    if (scrollTopBtn || scrollBottomBtn) {
      window.addEventListener('scroll', toggleScrollButtons);
      setTimeout(() => {
        toggleScrollButtons();
        console.log('🔄 Scroll buttons initialized and toggled');
      }, 100);
    }
    
    // Force make page scrollable if it's not
    setTimeout(() => {
      const documentHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      const windowHeight = window.innerHeight;
      
      if (documentHeight <= windowHeight) {
        console.log('⚠️ Page is not scrollable, adding extra height...');
        document.body.style.minHeight = (windowHeight + 500) + 'px';
        toggleScrollButtons();
      }
    }, 500);
    
  })();

})();
