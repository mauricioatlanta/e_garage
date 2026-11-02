(function () {
  // --- Utilidades numéricas tolerantes (1.234,56 / $1,234.56) ---
  function toNumber(v) {
    if (v == null) return 0;
    let s = String(v).trim();
    if (!s) return 0;
    // quita moneda y espacios
    s = s.replace(/[^\d,.\-]/g, "");
    // si tiene coma y punto, asume coma decimal (formato CL/ES): 1.234,56 => 1234.56
    if (s.indexOf(",") > -1 && s.indexOf(".") > -1 && s.lastIndexOf(",") > s.lastIndexOf(".")) {
      s = s.replace(/\./g, "").replace(",", ".");
    } else {
      // si solo comas, tratarlas como punto decimal
      const onlyCommas = s.indexOf(",") > -1 && s.indexOf(".") === -1;
      if (onlyCommas) s = s.replace(",", ".");
    }
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  // --- Lectura de país/impuestos desde los partials ---
  const metaCL = document.querySelector("#country-meta-cl");
  const metaUS = document.querySelector("#country-meta-us");
  const isCL = !!metaCL;
  const isUS = !!metaUS;

  // UI de sales tax (solo US, si existe)
  const chkSalesTax = document.querySelector("input[name='apply_sales_tax']");
  const inpTaxRate  = document.querySelector("input[name='sales_tax_rate']");

  // Contenedores de totales (IDs sugeridos)
  const $netoRep = document.querySelector("#neto-repuestos");
  const $netoServ = document.querySelector("#neto-servicios");
  const $netoOtros = document.querySelector("#neto-otros");
  const $tax = document.querySelector("#tax-amount");
  const $total = document.querySelector("#total-doc");

  // Selector generoso para subtotales por línea (añade estas clases/attrs en tus filas)
  // <tr class="linea js-line" data-kind="repuesto|servicio|otro">
  //   <td class="js-subtotal" data-subtotal>...</td>
  // </tr>
  function sumByKind(kind) {
    const nodes = document.querySelectorAll(`.js-line[data-kind="${kind}"] .js-subtotal, .js-subtotal[data-kind="${kind}"]`);
    let acc = 0;
    nodes.forEach(n => acc += toNumber(n.textContent || n.value));
    return acc;
  }

  function calcTax(nRep, nServ) {
    if (isCL) {
      // CL: IVA 19% SOLO repuestos
      return nRep * 0.19;
    }
    // US
    const apply = chkSalesTax ? chkSalesTax.checked : false;
    const ratePct = inpTaxRate && inpTaxRate.value ? toNumber(inpTaxRate.value) : 0;
    const rate = Math.max(0, ratePct) / 100;
    // por defecto, si no marcan el check, impuesto 0
    return apply ? (nRep + nServ) * rate : 0;
  }

  function fmt(n) {
    try {
      // Si tu template ya pasa moneda/locale, ajústalo aquí:
      // Ejemplo rápido sin símbolo:
      return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
    } catch (_) {
      return (Math.round(n * 100) / 100).toFixed(2);
    }
  }

  function recalc() {
    const netoRep = sumByKind("repuesto");
    const netoServ = sumByKind("servicio");
    const netoOtros = sumByKind("otro");
    const tax = calcTax(netoRep, netoServ);
    const total = netoRep + netoServ + netoOtros + tax;

    if ($netoRep)  $netoRep.textContent = fmt(netoRep);
    if ($netoServ) $netoServ.textContent = fmt(netoServ);
    if ($netoOtros)$netoOtros.textContent = fmt(netoOtros);
    if ($tax)      $tax.textContent = fmt(tax);
    if ($total)    $total.textContent = fmt(total);
  }

  // Recalcular cuando cambien cantidades/precios/descuentos o toggles de impuesto
  const changeSelectors = [
    ".js-line input", ".js-line select", ".js-line textarea",
    "input[name='apply_sales_tax']", "input[name='sales_tax_rate']"
  ];
  changeSelectors.forEach(sel => {
    document.addEventListener("input", e => e.target.matches(sel) && recalc(), true);
    document.addEventListener("change", e => e.target.matches(sel) && recalc(), true);
  });

  // Recalcular al cargar
  window.addEventListener("DOMContentLoaded", recalc);
  window.recalcDocumentoTotales = recalc; // por si necesitas invocarlo tras agregar filas por JS
})();
