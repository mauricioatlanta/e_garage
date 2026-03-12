/**
 * piece-drawer.js - Panel lateral de pieza para mapa de desarme
 * Usa _piece_drawer_desarme: pieza-zona, pieza-vista, pieza-nombre, estado-pills, pieza-precio, pieza-stock, pieza-observaciones
 * POST real a API, actualiza piecesByZone, KPIs y resumen.
 */
(function() {
  'use strict';

  var cfg = window.DESARME_CONFIG || {};
  var piecesByZone = cfg.piecesByZone || {};

  function getPiece(zone, view) {
    if (piecesByZone[zone]) return piecesByZone[zone];
    var key = zone + (view ? '|' + view : '');
    return piecesByZone[key] || null;
  }

  function setPieceLocal(zone, view, data) {
    var key = zone;
    piecesByZone[key] = piecesByZone[key] || {};
    Object.assign(piecesByZone[key], data);
    piecesByZone[key].zone = zone;
    piecesByZone[key].view = view || '';
  }

  function syncFromConfig() {
    piecesByZone = cfg.piecesByZone || {};
  }

  function showToast(msg, type) {
    var el = document.getElementById('toast-desarme');
    if (!el) return;
    el.textContent = msg;
    el.className = 'toast-desarme toast-' + (type || 'info');
    el.classList.add('visible');
    clearTimeout(el._toastTimer);
    el._toastTimer = setTimeout(function() {
      el.classList.remove('visible');
    }, 3000);
  }

  function getEl(id) { return document.getElementById(id); }

  function open(selection) {
    var placeholder = getEl('drawer-placeholder');
    var formWrap = getEl('piece-drawer-form');
    if (!placeholder || !formWrap) return;

    if (!selection || !selection.zone) {
      placeholder.classList.remove('d-none');
      formWrap.classList.add('d-none');
      return;
    }

    placeholder.classList.add('d-none');
    formWrap.classList.remove('d-none');

    var piece = getPiece(selection.zone, selection.view);
    var name = piece ? piece.piece_name : (selection.name || selection.zone.replace(/_/g, ' '));
    var status = piece ? (piece.status || 'unreviewed') : 'unreviewed';
    var price = piece ? (piece.price || '') : '';
    var stock = piece ? (piece.stock != null ? piece.stock : 1) : 1;
    var note = piece ? (piece.note || '') : '';

    var zonaEl = getEl('pieza-zona');
    var vistaEl = getEl('pieza-vista');
    var nombreEl = getEl('pieza-nombre');
    var precioEl = getEl('pieza-precio');
    var stockEl = getEl('pieza-stock');
    var obsEl = getEl('pieza-observaciones');

    if (zonaEl) zonaEl.value = selection.zone;
    if (vistaEl) vistaEl.value = selection.view || '';
    if (nombreEl) nombreEl.value = name;
    if (precioEl) precioEl.value = price;
    if (stockEl) stockEl.value = stock;
    if (obsEl) obsEl.value = note;

    var estadoEl = getEl('pieza-estado');
    if (estadoEl) estadoEl.value = status;

    var pills = document.querySelectorAll('#estado-pills [data-status]');
    for (var i = 0; i < pills.length; i++) {
      var p = pills[i];
      p.classList.toggle('active', (p.getAttribute('data-status') || '') === status);
    }

    formWrap._selection = selection;
  }

  function updateUIFromResponse(data) {
    if (!data) return;
    if (data.piece) {
      setPieceLocal(data.piece.zone, data.piece.view, data.piece);
    }
    if (data.summary) {
      var s = data.summary;
      var ids = ['resumen-disponibles', 'resumen-danadas', 'resumen-scrap', 'resumen-vendidas', 'resumen-reservadas'];
      var keys = ['disponible', 'dañado', 'scrap', 'vendido', 'reservada'];
      for (var i = 0; i < keys.length; i++) {
        var el = getEl(ids[i]);
        if (el) el.textContent = (keys[i] === 'dañado' ? 'Dañadas' : keys[i].charAt(0).toUpperCase() + keys[i].slice(1)) + ': ' + (s[keys[i]] || 0);
      }
      var ft = getEl('footer-total');
      if (ft) ft.textContent = s.total || 0;
      var pt = getEl('progreso-texto');
      if (pt) pt.textContent = (s.piezas_revisadas || 0) + ' / ' + (s.total || 0);
      var pf = getEl('progreso-fill');
      if (pf) pf.style.width = (s.progreso_pct || 0) + '%';
    }
    if (data.kpis) {
      var k = data.kpis;
      var kc = getEl('kpi-costo-val');
      if (kc) kc.textContent = k.costo_total || '0';
      var kr = getEl('kpi-recuperado-val');
      if (kr) kr.textContent = k.ingresos_totales || '0';
      var kres = getEl('kpi-resultado-val');
      if (kres) kres.textContent = k.utilidad_total || '0';
      var kp = getEl('kpi-recuperacion-val');
      if (kp) kp.textContent = k.porcentaje_recuperacion || 0;
      var fi = getEl('footer-ingresos');
      if (fi) fi.textContent = '$' + (parseFloat(k.ingresos_totales || 0)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
      var fc = getEl('footer-chatarra');
      if (fc) fc.textContent = '$' + (parseFloat(k.ingreso_final_chatarra || 0)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
      var fu = getEl('footer-utilidad');
      if (fu) fu.textContent = '$' + (parseFloat(k.utilidad_total || 0)).toLocaleString('es-CL', { maximumFractionDigits: 0 });
      var kresCard = getEl('kpi-resultado');
      if (kresCard) {
        var u = parseFloat(k.utilidad_total || 0);
        kresCard.classList.remove('kpi-positivo', 'kpi-negativo');
        kresCard.classList.add(u >= 0 ? 'kpi-positivo' : 'kpi-negativo');
      }
    }
  }

  function save(saveAndNext) {
    var formWrap = getEl('piece-drawer-form');
    if (!formWrap || !formWrap._selection || !cfg.canEdit) return;

    var sel = formWrap._selection;
    var zonaEl = getEl('pieza-zona');
    var vistaEl = getEl('pieza-vista');
    var nombreEl = getEl('pieza-nombre');
    var precioEl = getEl('pieza-precio');
    var stockEl = getEl('pieza-stock');
    var obsEl = getEl('pieza-observaciones');

    var zone = zonaEl ? zonaEl.value : sel.zone;
    var view = vistaEl ? vistaEl.value : (sel.view || '');
    var pieceName = (nombreEl ? nombreEl.value : '').trim();
    if (!pieceName) {
      showToast('El nombre de la pieza es obligatorio', 'error');
      return;
    }

    var status = 'unreviewed';
    var activePill = document.querySelector('#estado-pills [data-status].active');
    if (activePill) status = activePill.getAttribute('data-status') || 'unreviewed';

    var price = (precioEl ? precioEl.value : '0').replace(/[^\d.,]/g, '').replace(',', '.') || '0';
    var stock = parseInt((stockEl ? stockEl.value : '1'), 10);
    if (isNaN(stock) || stock < 0) stock = 1;
    var note = (obsEl ? obsEl.value : '').trim().slice(0, 500);

    var payload = {
      zone: zone,
      view: view,
      piece_name: pieceName,
      status: status,
      price: price,
      stock: stock,
      note: note,
    };

    var url = cfg.apiPiezaUrl;
    if (!url) {
      showToast('Error: no hay URL de API', 'error');
      return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRFToken', cfg.csrf || '');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onload = function() {
      try {
        var j = JSON.parse(xhr.responseText);
        if (j.ok && j.piece) {
          cfg.piecesByZone = cfg.piecesByZone || {};
          setPieceLocal(j.piece.zone, j.piece.view, j.piece);
          cfg.piecesByZone = piecesByZone;
          if (window.DesarmeMap) window.DesarmeMap.setPiecesByZone(piecesByZone);
          updateUIFromResponse(j);
          showToast('Pieza guardada correctamente', 'success');
          if (saveAndNext) {
            var zones = document.querySelectorAll('.mapa-vista.active .zone');
            var idx = -1;
            for (var i = 0; i < zones.length; i++) {
              if ((zones[i].getAttribute('data-zone') || zones[i].dataset.zone) === zone) {
                idx = i;
                break;
              }
            }
            if (idx >= 0 && idx < zones.length - 1) {
              var next = zones[idx + 1];
              if (window.DesarmeMap) {
                window.DesarmeMap.selectZone({
                  el: next,
                  zone: next.getAttribute('data-zone') || next.dataset.zone,
                  view: next.getAttribute('data-view') || next.dataset.view || '',
                  name: next.getAttribute('data-piece-name') || next.dataset.pieceName || ''
                });
              }
            }
          }
        } else {
          showToast(j.error || 'Error al guardar', 'error');
        }
      } catch (e) {
        showToast('Error al procesar la respuesta', 'error');
      }
    };
    xhr.onerror = function() {
      showToast('Error de conexión', 'error');
    };
    xhr.send(JSON.stringify(payload));
  }

  function markScrap() {
    var pills = document.querySelectorAll('#estado-pills [data-status]');
    for (var i = 0; i < pills.length; i++) {
      pills[i].classList.toggle('active', (pills[i].getAttribute('data-status') || '') === 'scrap');
    }
    var estadoEl = getEl('pieza-estado');
    if (estadoEl) estadoEl.value = 'scrap';
  }

  function init() {
    syncFromConfig();

    var closeBtn = document.querySelector('[data-action="close-drawer"], .btn-close-panel');
    if (closeBtn) closeBtn.addEventListener('click', function() {
      if (window.DesarmeMap) window.DesarmeMap.selectZone(null);
    });

    var pills = document.querySelectorAll('#estado-pills [data-status]');
    for (var i = 0; i < pills.length; i++) {
      (function(p) {
        p.addEventListener('click', function() {
          if (!cfg.canEdit) return;
          for (var j = 0; j < pills.length; j++) pills[j].classList.remove('active');
          p.classList.add('active');
          var estadoEl = getEl('pieza-estado');
          if (estadoEl) estadoEl.value = p.getAttribute('data-status') || '';
        });
      })(pills[i]);
    }

    var form = getEl('form-pieza');
    if (form) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        save(false);
      });
    }

    var saveNextBtn = document.querySelector('[data-submit-mode="save-next"]');
    if (saveNextBtn) saveNextBtn.addEventListener('click', function(e) {
      e.preventDefault();
      save(true);
    });

    var scrapBtn = document.querySelector('[data-action="marcar-scrap"]');
    if (scrapBtn) scrapBtn.addEventListener('click', function(e) {
      e.preventDefault();
      markScrap();
    });

    if (window.DesarmeDrawer) window.DesarmeDrawer.open(null);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.DesarmeDrawer = {
    open: open,
    save: save,
    getPiecesByZone: function() { return piecesByZone; }
  };
})();
