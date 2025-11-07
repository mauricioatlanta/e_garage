// eGarage · numero_preview.js — robusto + TTL + debounce + invalidate hook
(function () {
  const start = () => {
    console.log("🔢 Iniciando sistema de numeración…");

    const $ = (s, c = document) => c.querySelector(s);
    const getDataEl = () => $("#doc-data") || document.body;

    // Lee endpoint desde #doc-data o body
    const dataEl = getDataEl();
    let endpoint = dataEl?.dataset?.endpointNextNumber || "";
    const tipoSel  = $("#id_tipo");
    const prev     = $("#numero_preview");

    console.log("🎯 Elementos:", { endpoint, tipoSel: !!tipoSel, prev: !!prev, tipoValue: tipoSel?.value });

    // Normaliza endpoint (admite relativo tipo "/api/..."; o "api/..."; o absoluto)
    function resolveEndpoint(raw) {
      if (!raw) return "";
      try {
        // absoluto
        new URL(raw);
        return raw;
      } catch {
        // relativo
        if (raw.startsWith("/")) return raw;
        return `${location.origin}/${raw.replace(/^\/+/, "")}`;
      }
    }
    endpoint = resolveEndpoint(endpoint);

    // Cache simple por tipo con TTL
    const TTL_MS = 30_000; // 30s: balance entre UX y consistencia
    const cache = new Map(); // tipo -> { value, ts }
    let currentCtrl = null;

    // Tiny debounce
    const debounce = (fn, wait = 150) => {
      let t;
      return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), wait); };
    };

    // Helper fetch JSON robusto
    async function fetchJSON(url, opts = {}) {
      const res = await fetch(url, { credentials: "same-origin", ...opts });

      const ct = (res.headers.get("content-type") || "").toLowerCase();
      // Detección básica de redirect a HTML/login
      if (ct.includes("text/html")) {
        const head = (await res.text()).slice(0, 160);
        throw new Error(`Respuesta HTML (posible login/302). Head: ${head}`);
      }

      if (!res.ok) {
        if (ct.includes("application/json")) {
          const err = await res.json().catch(()=>({}));
          throw new Error(`HTTP ${res.status} ${res.statusText} ${JSON.stringify(err)}`);
        }
        const head = (await res.text()).slice(0, 160);
        throw new Error(`HTTP ${res.status} non-JSON. Head: ${head}`);
      }

      // 204 o cuerpo vacío
      if (res.status === 204) return {};
      if (!ct.includes("application/json")) {
        const txt = (await res.text()).trim();
        if (!txt) return {};
        try { return JSON.parse(txt); } catch {
          const head = txt.slice(0, 160);
          throw new Error(`Non-JSON response (ct=${ct}). Head: ${head}`);
        }
      }
      return res.json();
    }

    function setPreview(text) {
      if (prev) prev.textContent = text;
    }

    function getCached(tipo) {
      const hit = cache.get(tipo);
      if (!hit) return null;
      if (Date.now() - hit.ts > TTL_MS) { cache.delete(tipo); return null; }
      return hit.value;
    }

    function putCache(tipo, value) {
      cache.set(tipo, { value, ts: Date.now() });
    }

    async function refreshPreviewCore() {
      const tipo = tipoSel?.value;
      if (!endpoint) { console.error("❌ No hay endpoint configurado"); return; }
      if (!tipo)     { console.warn("⚠️ No hay tipo seleccionado");   setPreview("—"); return; }
      if (!prev)     { console.error("❌ No se encontró #numero_preview"); return; }

      // Cache TTL
      const cached = getCached(tipo);
      if (cached) {
        setPreview(cached);
        return;
      }

      // Cancelar solicitud anterior
      if (currentCtrl) currentCtrl.abort();
      currentCtrl = new AbortController();
      const { signal } = currentCtrl;

      // Timeout de 7s
      const to = setTimeout(() => currentCtrl.abort(), 7000);

      try {
        setPreview("…"); // loading
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.set("tipo", tipo);
        console.log("🌐 solicitando preview:", url.toString());

        const data = await fetchJSON(url.toString(), { signal });
        // Acepta { ok:true, preview:"" } o { preview:"" } o {numero:"" }
        const ok = data.ok === undefined ? true : !!data.ok;
        const preview = data.preview || data.numero || "—";
        if (!ok) throw new Error(`Respuesta no OK: ${JSON.stringify(data)}`);

        putCache(tipo, preview);
        setPreview(preview);
        console.log("✅ Preview actualizado:", preview);
      } catch (e) {
        if (e.name === "AbortError") {
          console.warn("⏹️ Solicitud cancelada");
        } else {
          console.error("❌ Error preview:", e);
          setPreview("Error");
        }
      } finally {
        clearTimeout(to);
        currentCtrl = null;
      }
    }

    const refreshPreview = debounce(refreshPreviewCore, 120);

    if (tipoSel) {
      tipoSel.addEventListener("change", refreshPreview);
      // también al enfocar (caso navegar con teclado/edición rápida)
      tipoSel.addEventListener("focusout", refreshPreview);
    } else {
      console.error("❌ No se pudo agregar listener: #id_tipo no encontrado");
    }

    // inicial (si ya hay tipo seleccionado)
    refreshPreview();
    console.log("✅ Sistema de numeración inicializado");

    // Exponer un hook global opcional para invalidar cache desde otros módulos
    window.egNumero = {
      invalidate(tipo = null) {
        if (tipo) cache.delete(tipo);
        else cache.clear();
        refreshPreviewCore(); // sin debounce, para reflejar inmediatamente
      }
    };
  };

  // Asegurar DOM listo
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();