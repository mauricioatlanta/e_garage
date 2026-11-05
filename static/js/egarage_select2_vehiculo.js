/*
 * eGarage - Motor y Caja con Select2 (formulario de vehiculos) - v3
 *
 * 1. Carga las opciones desde /<pais>/<idioma>/vehiculos/ajax/ si el select
 *    quedo con 1 opcion o menos. Primero con modelo_id; si viene vacio,
 *    con el catalogo completo del pais.
 * 2. Monta Select2 con tags:true, busqueda y placeholder.
 * 3. Un MutationObserver vigila #id_motor y #id_caja: si otro script los
 *    vacia (por ejemplo al elegir modelo), los vuelve a cargar y a montar.
 *
 * API publica:
 *   window.egarageAddOption('id_motor', '3.5 V6', '3.5 V6')
 *   document.dispatchEvent(new CustomEvent('egarage:option-created',
 *       { detail: { field: 'motor', id: '3.5 V6', text: '3.5 V6' } }))
 */
(function (window, document) {
  'use strict';

  var $ = window.jQuery;
  if (!$) {
    console.error('[eGarage] jQuery no esta cargado');
    return;
  }
  if (!$.fn || !$.fn.select2) {
    console.error('[eGarage] select2 no esta registrado en este jQuery');
    return;
  }

  var FIELDS = [
    { id: 'id_motor', endpoint: 'motores-por-modelo/' },
    { id: 'id_caja', endpoint: 'cajas-por-modelo/' }
  ];
  var MAX_ATTEMPTS = 15;
  var attempts = {};

  function getSelect(id) {
    return $(document.getElementById(id));
  }

  function ajaxBase() {
    var m = window.location.pathname.match(/^\/([a-z]{2})\/([a-z]{2})\//);
    var prefix = m ? '/' + m[1] + '/' + m[2] : '/us/en';
    return prefix + '/vehiculos/ajax/';
  }

  function fetchList(endpoint, withModel) {
    var url = ajaxBase() + endpoint;
    var modeloId = $('#id_modelo').val();
    if (withModel && modeloId) {
      url += '?modelo_id=' + encodeURIComponent(modeloId);
    }
    return fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (r) { return r.json(); });
  }

  function fillOptions($el, data) {
    var current = $el.val();
    // Quita opciones de estado ("Cargando...", "Selecciona un modelo primero")
    // y deja una unica opcion vacia con el placeholder.
    $el.find('option').each(function () {
      if (this.value === '') { $(this).remove(); }
    });
    $el.prepend(new Option($el.attr('data-placeholder') || '', '', false, false));

    data.forEach(function (item) {
      var value = (item.id !== undefined && item.id !== null) ? item.id : item.nombre;
      var text = item.nombre || item.text || String(value);
      var exists = false;
      $el.find('option').each(function () {
        if (this.value === String(value)) { exists = true; }
      });
      if (!exists) { $el.append(new Option(text, value, false, false)); }
    });
    if (current) { $el.val(current); }
  }

  function hydrate(field) {
    var $el = getSelect(field.id);
    if (!$el.length || $el.find('option').length > 1) {
      return Promise.resolve();
    }
    return fetchList(field.endpoint, true)
      .then(function (data) {
        if (Array.isArray(data) && data.length) { return data; }
        return $("#id_modelo").val() ? [] : fetchList(field.endpoint, false);
      })
      .then(function (data) {
        if (Array.isArray(data) && data.length) { fillOptions($el, data); }
      })
      .catch(function (err) {
        console.warn('[eGarage] no se pudo cargar ' + field.endpoint, err);
      });
  }

  function mountSelect2($el) {
    if (!$el.length) { return; }
    var current = $el.val();

    if ($el.hasClass('select2-hidden-accessible') || $el.data('select2')) {
      try { $el.select2('destroy'); } catch (e) { /* ya desmontado */ }
    }
    $el.next('.select2-container').remove();

    $el.select2({
      width: '100%',
      tags: true,
      allowClear: true,
      placeholder: $el.attr('data-placeholder') || '',
      minimumResultsForSearch: 0,
      createTag: function (params) {
        var term = $.trim(params.term);
        if (term === '') { return null; }
        return { id: term, text: term, newTag: true };
      }
    });

    if (current) { $el.val(current).trigger('change.select2'); }
  }

  function ensureMounted(field) {
    var $el = getSelect(field.id);
    if (!$el.length) { return; }
    var mounted = $el.next('.select2-container').length > 0 &&
                  $el.hasClass('select2-hidden-accessible');
    if (!mounted) { mountSelect2($el); }
  }

  function run() {
    FIELDS.forEach(function (field) {
      hydrate(field).then(function () { ensureMounted(field); });
    });
  }

  function watch(field) {
    var el = document.getElementById(field.id);
    if (!el || el.__egWatch || !window.MutationObserver) { return; }
    el.__egWatch = true;
    var timer = null;
    new MutationObserver(function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        if (el.options.length > 1) { ensureMounted(field); return; }
        attempts[field.id] = (attempts[field.id] || 0) + 1;
        if (attempts[field.id] > MAX_ATTEMPTS) { return; }
        hydrate(field).then(function () { ensureMounted(field); });
      }, 700);
    }).observe(el, { childList: true });
  }

  function addOption(selectId, value, text) {
    var $el = getSelect(selectId);
    if (!$el.length || value === undefined || value === null || value === '') {
      return false;
    }
    value = String(value);
    text = text ? String(text) : value;
    var exists = false;
    $el.find('option').each(function () {
      if (this.value === value) { exists = true; }
    });
    if (!exists) { $el.append(new Option(text, value, true, true)); }
    $el.val(value).trigger('change');
    return true;
  }

  window.egarageAddOption = addOption;

  document.addEventListener('egarage:option-created', function (ev) {
    var d = ev.detail || {};
    var map = { motor: 'id_motor', caja: 'id_caja', transmision: 'id_caja' };
    addOption(map[d.field] || d.field, d.id, d.text);
  });

  $(function () {
    FIELDS.forEach(watch);
    run();
    setTimeout(run, 300);
    setTimeout(run, 1200);
    setTimeout(run, 3000);
    // Nuevo modelo/marca: reinicia el contador de intentos
    $('#id_modelo, #id_marca').on('change', function () { attempts = {}; });
  });
  $(window).on('load', function () {
    FIELDS.forEach(watch);
    run();
  });

  console.log('[eGarage] select2 motor/caja v3 listo');
})(window, document);


    // Encadenamiento dinámico Modelo -> Motor y Caja
    $(document).on('change', '#id_modelo', function() {
        var modeloId = $(this).val();
        var $motor = $('#id_motor');
        var $caja = $('#id_caja');

        var urlMotores = (window.urlMotoresPorModelo || '/us/en/vehiculos/ajax/motores-por-modelo/') + (modeloId ? ('?modelo_id=' + encodeURIComponent(modeloId)) : '');
        var urlCajas = (window.urlCajasPorModelo || '/us/en/vehiculos/ajax/cajas-por-modelo/') + (modeloId ? ('?modelo_id=' + encodeURIComponent(modeloId)) : '');

        // Recargar Motores
        if ($motor.length) {
            fetch(urlMotores)
                .then(r => r.json())
                .then(data => {
                    var valActual = $motor.val();
                    $motor.empty().append(new Option('Select or type engine...', '', false, false));
                    if (Array.isArray(data)) {
                        data.forEach(function(item) {
                            var opt = new Option(item.nombre || item.text, item.id, false, String(item.id) === String(valActual));
                            $motor.append(opt);
                        });
                    }
                    $motor.trigger('change.select2');
                });
        }

        // Recargar Cajas
        if ($caja.length) {
            fetch(urlCajas)
                .then(r => r.json())
                .then(data => {
                    var valActual = $caja.val();
                    $caja.empty().append(new Option('Select or type transmission...', '', false, false));
                    if (Array.isArray(data)) {
                        data.forEach(function(item) {
                            var opt = new Option(item.nombre || item.text, item.id, false, String(item.id) === String(valActual));
                            $caja.append(opt);
                        });
                    }
                    $caja.trigger('change.select2');
                });
        }
    });
    