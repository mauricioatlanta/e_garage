/**
 * vehicle-map.js - Mapa interactivo de vehículo para desarme
 * Hover, tooltip, selección, tabs de vista, pintado de estados
 */
(function() {
  'use strict';

  var cfg = window.DESARME_CONFIG || {};
  if (!cfg.piecesByZone) cfg.piecesByZone = {};
  var piecesByZone = cfg.piecesByZone;
  var tooltipEl = null;
  var selectedZone = null;

  function getStatus(zone, view) {
    var key = zone;
    if (piecesByZone[key]) return piecesByZone[key].status || '';
    var v = view || '';
    for (var k in piecesByZone) {
      if (k === zone || (piecesByZone[k].zone === zone && piecesByZone[k].view === v)) {
        return piecesByZone[k].status || '';
      }
    }
    return '';
  }

  function applyStatusClasses(svg) {
    if (!svg) return;
    var zones = svg.querySelectorAll('.zone');
    for (var i = 0; i < zones.length; i++) {
      var z = zones[i];
      var zone = z.getAttribute('data-zone') || z.dataset.zone;
      var view = z.getAttribute('data-view') || z.dataset.view || '';
      var status = getStatus(zone, view);
      z.classList.remove('status-unreviewed', 'status-available', 'status-damaged', 'status-scrap', 'status-reserved', 'status-sold');
      if (status) {
        z.classList.add('status-' + status);
      } else {
        z.classList.add('status-unreviewed');
      }
      z.classList.toggle('selected', selectedZone && selectedZone.el === z);
    }
  }

  function showTooltip(evt, zone) {
    if (!tooltipEl) {
      tooltipEl = document.getElementById('zone-tooltip');
      if (!tooltipEl) {
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'zone-tooltip';
        tooltipEl.className = 'zone-tooltip';
        tooltipEl.setAttribute('role', 'tooltip');
        tooltipEl.setAttribute('aria-hidden', 'true');
        document.body.appendChild(tooltipEl);
      }
    }
    var pieceName = zone.getAttribute('data-piece-name') || zone.dataset.pieceName || zone.getAttribute('data-zone') || zone.dataset.zone || 'Pieza';
    var zoneId = zone.getAttribute('data-zone') || zone.dataset.zone;
    var view = zone.getAttribute('data-view') || zone.dataset.view || '';
    var status = getStatus(zoneId, view);
    var statusLabel = { available: 'Disponible', damaged: 'Dañada', scrap: 'Scrap', reserved: 'Reservada', sold: 'Vendida', unreviewed: '' }[status] || (status ? status : 'No revisada');
    tooltipEl.innerHTML = '<div class="tooltip-name">' + pieceName + '</div><div class="tooltip-status">' + statusLabel + '</div>';
    tooltipEl.classList.add('visible');
    tooltipEl.style.left = (evt.clientX + 12) + 'px';
    tooltipEl.style.top = (evt.clientY + 12) + 'px';
  }

  function hideTooltip() {
    if (tooltipEl) {
      tooltipEl.classList.remove('visible');
    }
  }

  function selectZone(zone) {
    selectedZone = zone ? { el: zone, zone: zone.getAttribute('data-zone') || zone.dataset.zone, view: zone.getAttribute('data-view') || zone.dataset.view || '', name: zone.getAttribute('data-piece-name') || zone.dataset.pieceName || '' } : null;
    document.querySelectorAll('.zone').forEach(function(z) { z.classList.remove('selected'); });
    if (zone) zone.classList.add('selected');
    document.querySelectorAll('.mapa-vista').forEach(function(v) { applyStatusClasses(v.querySelector('.mapa-vehiculo-svg')); });
    if (window.DesarmeDrawer) window.DesarmeDrawer.open(selectedZone);
  }

  function initViewTabs() {
    document.querySelectorAll('.view-tab').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var view = btn.getAttribute('data-view') || btn.dataset.view;
        document.querySelectorAll('.view-tab').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        document.querySelectorAll('.mapa-vista').forEach(function(v) {
          var vView = v.getAttribute('data-view') || v.dataset.view;
          v.classList.toggle('hidden', vView !== view);
          v.classList.toggle('active', vView === view);
        });
        var activePanel = document.querySelector('.mapa-vista.active');
        if (activePanel) applyStatusClasses(activePanel.querySelector('.mapa-vehiculo-svg'));
      });
    });
  }

  function initZones() {
    document.querySelectorAll('.mapa-vista').forEach(function(panel) {
      var svg = panel.querySelector('.mapa-vehiculo-svg');
      if (!svg) return;
      applyStatusClasses(svg);
      var zones = svg.querySelectorAll('.zone');
      for (var i = 0; i < zones.length; i++) {
        (function(zone) {
          zone.addEventListener('mouseenter', function(e) {
            showTooltip(e, zone);
          });
          zone.addEventListener('mousemove', function(e) {
            if (tooltipEl && tooltipEl.classList.contains('visible')) {
              tooltipEl.style.left = (e.clientX + 12) + 'px';
              tooltipEl.style.top = (e.clientY + 12) + 'px';
            }
          });
          zone.addEventListener('mouseleave', function() {
            hideTooltip();
          });
          zone.addEventListener('click', function(e) {
            e.stopPropagation();
            selectZone(zone);
          });
        })(zones[i]);
      }
    });
  }

  function paintAll() {
    document.querySelectorAll('.mapa-vista').forEach(function(panel) {
      applyStatusClasses(panel.querySelector('.mapa-vehiculo-svg'));
    });
  }

  function init() {
    initViewTabs();
    initZones();
    if (window.DesarmeDrawer) window.DesarmeDrawer.open(null);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.DesarmeMap = {
    paintZones: paintAll,
    getStatus: getStatus,
    setPiecesByZone: function(data) { piecesByZone = data || {}; paintAll(); },
    getPiecesByZone: function() { return piecesByZone; },
    selectZone: selectZone
  };
})();
