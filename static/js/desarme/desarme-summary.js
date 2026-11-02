/**
 * Resumen operativo y financiero del mapa de desarme.
 * Usa pieceSummary y kpis de DESARME_CONFIG (json_script).
 */
(function() {
  'use strict';

  function actualizar() {
    var cfg = window.DESARME_CONFIG;
    if (!cfg) return;

    var summary = cfg.pieceSummary || {};
    var kpis = cfg.kpis || {};
    var ids = ['resumen-disponibles', 'resumen-danadas', 'resumen-scrap', 'resumen-vendidas', 'resumen-reservadas'];
    var keys = ['disponible', 'dañado', 'scrap', 'vendido', 'reservada'];
    for (var i = 0; i < keys.length; i++) {
      var el = document.getElementById(ids[i]);
      var label = keys[i] === 'dañado' ? 'Dañadas' : keys[i].charAt(0).toUpperCase() + keys[i].slice(1);
      if (el) el.textContent = label + ': ' + (summary[keys[i]] || 0);
    }
    var pt = document.getElementById('progreso-texto');
    if (pt) pt.textContent = (summary.piezas_revisadas || 0) + ' / ' + (summary.total || 0) + ' piezas';
    var pf = document.getElementById('progreso-fill');
    if (pf) pf.style.width = (summary.progreso_pct || 0) + '%';
    var ft = document.getElementById('footer-total');
    if (ft) ft.textContent = summary.total || 0;
    var fi = document.getElementById('footer-ingresos');
    if (fi && kpis.ingresos_totales) fi.textContent = '$' + (parseFloat(kpis.ingresos_totales)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
    var fc = document.getElementById('footer-chatarra');
    if (fc && kpis.ingreso_final_chatarra) fc.textContent = '$' + (parseFloat(kpis.ingreso_final_chatarra)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
    var fu = document.getElementById('footer-utilidad');
    if (fu && kpis.utilidad_total) fu.textContent = '$' + (parseFloat(kpis.utilidad_total)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
  }

  function init() {
    actualizar();
    window.DesarmeSummary = { actualizar: actualizar };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
