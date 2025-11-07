/* static/taller/common/js/documentos_form.js
   eGarage — Documento Form Controller (canónico)
   - Inicializa Select2/DAL (si está presente)
   - Forward cliente -> vehículo (limpieza + re-carga)
   - Genera número de documento al cambiar tipo
   - Gestiona Payment Status (poblar/mostrar si existe)
   - Totales: IVA solo sobre repuestos (CL 19%, US 0%)
   - Subtotales por fila + eliminar filas (CRUD dinámico)
*/
(() => {
  "use strict";

  // --- Guardas de entorno
  const win = window || {};
  const EG = (win.EG = win.EG || {});
  const cfg = EG.config || {};
  const doc = document;

  // --- Country & Currency
  const COUNTRY =
    cfg.COUNTRY ||
    (doc.documentElement && doc.documentElement.getAttribute("data-country")) ||
    (doc.body && doc.body.getAttribute("data-country")) ||
    win.COUNTRY || // compatibilidad hacia atrás
    "CL";

  const CURRENCY = COUNTRY === "US" ? "USD" : "CLP";
  const VAT_PCT = COUNTRY === "US" ? 0 : 19;

  // --- Utils
  const $ = (sel, ctx) => (ctx || doc).querySelector(sel);
  const $$ = (sel, ctx) => Array.from((ctx || doc).querySelectorAll(sel));
  const parseNumber = (x) => Number(String(x || "0").replace(/[^\d.-]/g, "")) || 0;

  const formatMoney = (value) => {
    const n = Number(value || 0);
    try {
      return new Intl.NumberFormat(COUNTRY === "US" ? "en-US" : "es-CL", {
        style: "currency",
        currency: CURRENCY,
        maximumFractionDigits: 0,
      }).format(n);
    } catch {
      return (CURRENCY === "USD" ? "$" : "$") + n.toLocaleString();
    }
  };

  const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

  // --- Endpoints (data-* del form > EG.endpoints > fallback)
  const endpoints = EG.endpoints || {};
  const getEndpoint = (key, fallback) => {
    const holder = $("#document-form") || doc.body;
    const val = holder?.dataset?.[key] || endpoints[key];
    return val || fallback || "";
  };

  // --- Nodos clave
  const $form = $("#document-form");
  const $tipo = $("#id_tipo");
  const $numero = $("#id_numero_documento") || $("#id_numero");
  const $cliente = $("#id_cliente");
  const $vehiculo = $("#id_vehiculo");
  const $pagadoToggle = $("#id_pagado");
  const $paymentStatus = $("#id_payment_status") || $("#id_estado_pago");

  // Totales (elementos KPI)
  const $tRep = $("#t_rep, #t_repuestos");
  const $tServ = $("#t_serv, #t_servicios");
  const $tOtros = $("#t_otros, #t_otro_servicio, #t_externos");
  const $tIva = $("#t_iva");
  const $tTotal = $("#t_total");

  console.log("🚀 Inicializando documento form... COUNTRY=", COUNTRY, "VAT=", VAT_PCT);

  // --- Payment Status (poblar si viene vacío y mostrar grupo)
  const ensurePaymentStatus = () => {
    if (!$paymentStatus) return;
    if ($paymentStatus.options && $paymentStatus.options.length <= 1) {
      const opts = [
        { v: "pending", en: "Pending", es: "Pendiente" },
        { v: "paid", en: "Paid", es: "Pagado" },
        { v: "partial", en: "Partial", es: "Parcial" },
        { v: "canceled", en: "Canceled", es: "Anulado" },
      ];
      $paymentStatus.innerHTML = "";
      opts.forEach((o) => {
        const op = doc.createElement("option");
        op.value = o.v;
        op.textContent = COUNTRY === "US" ? o.en : o.es;
        $paymentStatus.appendChild(op);
      });
    }
    const group = $paymentStatus.closest(".form-row") || $paymentStatus.parentElement;
    if (group && getComputedStyle(group).display === "none") group.style.display = "";
  };

  // --- Cliente -> Vehículo (limpia y dispara refresh en DAL/Select2)
  const wireClienteVehiculo = () => {
    if (!$cliente || !$vehiculo) return;
    on($cliente, "change", () => {
      try {
        if ($vehiculo.tagName === "SELECT") {
          $vehiculo.value = "";
        }
        const ev = new Event("change", { bubbles: true });
        $vehiculo.dispatchEvent(ev);
      } catch (e) {
        console.warn("wireClienteVehiculo error:", e);
      }
    });
  };

  // --- Numeración automática al cambiar tipo
  const wireAutoNumber = () => {
    if (!$tipo || !$numero) return;

    const fetchNext = async (tipo) => {
      const url =
        getEndpoint("docNextNumberUrl") ||
        getEndpoint("nextNumber") ||
        "/documentos/api/next-number/";
      if (!url) return null;
      try {
        const resp = await fetch(`${url}?tipo=${encodeURIComponent(tipo)}`, {
          credentials: "same-origin",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!resp.ok) return null;
        const data = await resp.json();
        return data?.numero || data?.next || null;
      } catch {
        return null;
      }
    };

    const handler = async () => {
      const tipoVal = $tipo.value || "";
      if (!tipoVal) return;
      const next = await fetchNext(tipoVal);
      if (next && $numero) {
        $numero.value = next;
        const ev = new Event("change", { bubbles: true });
        $numero.dispatchEvent(ev);
      }
    };

    on($tipo, "change", handler);
    handler(); // inicial
  };

  // --- Cálculo de totales (expuesto más abajo)
  const calcTotals = () => {
    const lines = $$("[data-linea-documento]");
    let sumRep = 0, sumServ = 0, sumOtros = 0;

    if (lines.length) {
      lines.forEach((ln) => {
        const t = ln.getAttribute("data-type");
        const s = parseNumber(ln.getAttribute("data-subtotal"));
        if (t === "repuesto") sumRep += s;
        else if (t === "servicio") sumServ += s;
        else sumOtros += s;
      });
    } else {
      // Fallback por si el template no usa datasets (opcional)
      sumRep = parseNumber($tRep && $tRep.textContent);
      sumServ = parseNumber($tServ && $tServ.textContent);
      sumOtros = parseNumber($tOtros && $tOtros.textContent);
    }

    const iva = Math.round((sumRep * VAT_PCT) / 100); // IVA solo repuestos
    const total = sumRep + sumServ + sumOtros + iva;

    if ($tRep) $tRep.textContent = formatMoney(sumRep);
    if ($tServ) $tServ.textContent = formatMoney(sumServ);
    if ($tOtros) $tOtros.textContent = formatMoney(sumOtros);
    if ($tIva) $tIva.textContent = formatMoney(iva);
    if ($tTotal) $tTotal.textContent = formatMoney(total);
  };

  // --- Hooks de "Agregar ítems": si hay botones, engancha y recalcula
  const wireAddButtons = () => {
    const $addRep = $("#btn-add-repuesto");
    const $addServ = $("#btn-add-servicio");
    const $addOtro = $("#btn-add-otro-servicio");

    const afterAdd = () => {
      // Si tu template inserta filas con data-linea-documento,
      // el observer de más abajo las inicializa y recalcula totales.
      calcTotals();
    };

    on($addRep, "click", () => setTimeout(afterAdd, 0));
    on($addServ, "click", () => setTimeout(afterAdd, 0));
    on($addOtro, "click", () => setTimeout(afterAdd, 0));

    // Recalcula al editar inputs típicos (qty/price)
    on(doc, "change", (e) => {
      const t = e.target;
      if (!t) return;
      if (t.matches("[data-role='qty'], [data-role='price'], [data-subtotal]")) {
        setTimeout(calcTotals, 0);
      }
    });
    on(doc, "input", (e) => {
      const t = e.target;
      if (!t) return;
      if (t.matches("[data-role='qty'], [data-role='price']")) {
        setTimeout(calcTotals, 0);
      }
    });
  };

  // --- Inicialización principal
  const init = () => {
    ensurePaymentStatus();
    wireClienteVehiculo();
    wireAutoNumber();
    wireAddButtons();
    calcTotals();

    if ($pagadoToggle && $paymentStatus) {
      on($pagadoToggle, "change", () => {
        if ($pagadoToggle.checked) {
          $paymentStatus.value = "paid";
        } else if ($paymentStatus.value === "paid") {
          $paymentStatus.value = "pending";
        }
      });
    }

    console.log("✅ Documento form listo:", { COUNTRY, CURRENCY, VAT_PCT });
  };

  if (doc.readyState === "loading") {
    on(doc, "DOMContentLoaded", init);
  } else {
    init();
  }

  // --- Mini-API pública para que otros scripts invoquen el recálculo
  win.EG = win.EG || {};
  win.EG.doc = Object.assign(win.EG.doc || {}, {
    recalcTotals: typeof calcTotals === "function" ? calcTotals : () => {},
  });

  // === Subtotales por fila + eliminar filas (delegación de eventos) ===
  (function () {
    const parseNum = (x) => Number(String(x || "0").replace(/[^\d.-]/g, "")) || 0;

    function computeRowSubtotal(tr) {
      if (!tr) return 0;
      const type = tr.getAttribute("data-type");
      let subtotal = 0;

      if (type === "repuesto" || type === "servicio") {
        const qty = parseNum(tr.querySelector("[data-role='qty']")?.value ?? 1);
        const price = parseNum(tr.querySelector("[data-role='price']")?.value ?? 0);
        subtotal = Math.max(0, Math.round(qty * price));
        } else {
        // "otro" / externo: usamos el precio al cliente como subtotal
        const priceCustomer = parseNum(tr.querySelector("[data-role='price-customer']")?.value ?? 0);
        subtotal = Math.max(0, Math.round(priceCustomer));
      }

      tr.setAttribute("data-subtotal", String(subtotal));
      const out = tr.querySelector("[data-role='subtotal']");
      if (out) out.textContent = subtotal.toLocaleString();
      return subtotal;
    }

    function maybeRecalcRow(target) {
      const tr = target.closest("tr[data-linea-documento]");
      if (!tr) return;
      const roles = ["qty", "price", "price-customer", "price-internal"];
      const isPriceInput = roles.some((r) => target.matches?.(`[data-role='${r}']`));
      if (!isPriceInput) return;
      computeRowSubtotal(tr);
      win.EG?.doc?.recalcTotals?.();
    }

    document.addEventListener("input", (e) => maybeRecalcRow(e.target), true);
    document.addEventListener("change", (e) => maybeRecalcRow(e.target), true);

    document.addEventListener(
      "click",
      (e) => {
        const btn = e.target.closest?.("[data-action='remove-line']");
        if (!btn) return;
        const tr = btn.closest?.("tr[data-linea-documento]");
        if (!tr) return;
        tr.remove();
        win.EG?.doc?.recalcTotals?.();
      },
      true
    );

    const observer = new MutationObserver((mutations) => {
      let touched = false;
      for (const m of mutations) {
        m.addedNodes?.forEach((node) => {
          if (node.nodeType === 1 && node.matches?.("tr[data-linea-documento]")) {
            computeRowSubtotal(node);
            touched = true;
          }
        });
      }
      if (touched) win.EG?.doc?.recalcTotals?.();
    });

    ["#repuestos-body", "#servicios-body", "#otros-body"]
      .map((sel) => document.querySelector(sel))
      .filter(Boolean)
      .forEach((tb) => observer.observe(tb, { childList: true }));
  })();
})();