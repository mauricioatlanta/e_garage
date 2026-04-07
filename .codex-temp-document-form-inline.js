
window.egEncodeDocumentFormNext = function egEncodeDocumentFormNext() {
  return encodeURIComponent(window.location.pathname + (window.location.search || ''));
};

(function() {
  'use strict';

  function getPathContext() {
    var pathParts = (window.location.pathname || '/cl/es/documentos/form/')
      .split('/')
      .filter(function(part) { return !!part; });

    var countryPrefix = pathParts[0] || 'cl';
    var langPrefix = 'es';

    if (pathParts[1] === 'es' || pathParts[1] === 'en') {
      langPrefix = pathParts[1];
    } else if (countryPrefix === 'us') {
      langPrefix = 'en';
    }

    return {
      countryPrefix: countryPrefix,
      langPrefix: langPrefix
    };
  }

  function getSelectedClienteId() {
    var clienteSelect = document.getElementById('id_cliente');
    if (!clienteSelect) {
      return '';
    }

    if (window.jQuery) {
      var $clienteSelect = window.jQuery(clienteSelect);
      if ($clienteSelect.hasClass('select2-hidden-accessible')) {
        return $clienteSelect.val() || '';
      }
    }

    return clienteSelect.value || '';
  }

  function redirectTo(pathname, extraQuery) {
    var context = getPathContext();
    var url = '/' + context.countryPrefix + '/' + context.langPrefix + pathname +
      '?next=' + window.egEncodeDocumentFormNext();

    if (extraQuery) {
      url += '&' + extraQuery;
    }

    window.location.href = url;
  }

  function openClienteModal() {
    try {
      redirectTo('/clientes/crear/');
    } catch (error) {
      console.error('Error al abrir cliente:', error);
      window.alert('Error al abrir la pagina de crear cliente.');
    }
  }

  function openVehiculoModal() {
    try {
      var clienteId = getSelectedClienteId();
      var extraQuery = clienteId ? 'cliente_id=' + encodeURIComponent(clienteId) : '';
      redirectTo('/vehiculos/crear/', extraQuery);
    } catch (error) {
      console.error('Error al abrir vehiculo:', error);
      window.alert('Error al abrir la pagina de crear vehiculo.');
    }
  }

  function handleNuevoVehiculoClick(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    openVehiculoModal();
    return false;
  }

  function submitLanguageDoc(lang) {
    var input = document.getElementById('language-input-doc');
    var form = document.getElementById('language-form-doc');
    if (!input || !form) {
      return;
    }
    input.value = lang;
    form.submit();
  }

  function updatePaymentStatusBadge() {
    var sel = document.getElementById('id_payment_status');
    var badge = document.getElementById('payment-status-badge');
    if (!sel || !badge) {
      return;
    }

    badge.classList.remove(
      'doc-console-payment-paid',
      'doc-console-payment-pending',
      'doc-console-payment-partial'
    );

    var value = (sel.value || '').toUpperCase();
    if (value === 'PAGADO' || value === 'PAID') {
      badge.classList.add('doc-console-payment-paid');
    } else if (value === 'PARCIAL' || value === 'PARTIAL') {
      badge.classList.add('doc-console-payment-partial');
    } else {
      badge.classList.add('doc-console-payment-pending');
    }
  }

  window.openClienteModal = openClienteModal;
  window.openVehiculoModal = openVehiculoModal;
  window.handleNuevoVehiculoClick = handleNuevoVehiculoClick;
  window.submitLanguageDoc = submitLanguageDoc;

  document.addEventListener('DOMContentLoaded', function() {
    var obs = document.getElementById('id_observaciones');
    var paymentStatus = document.getElementById('id_payment_status');

    if (obs) {
      obs.setAttribute('rows', '2');
    }

    updatePaymentStatusBadge();

    if (paymentStatus) {
      paymentStatus.addEventListener('change', updatePaymentStatusBadge);
    }
  });
})();

