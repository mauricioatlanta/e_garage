/**
 * Lógica de formulario de documentos (eGarage).
 * Validación, recalc totales, loading. Sin animación typing. Logs solo con window.DEBUG.
 */
(function () {
  'use strict';

  function getDocumentForm() {
    return document.getElementById('document-form') || document.querySelector('form[id="document-form"]');
  }

  function getClienteValue(form) {
    var field = form.querySelector('[name="cliente"]');
    if (!field) return null;
    if (typeof window.jQuery !== 'undefined' && window.jQuery(field).hasClass('select2-hidden-accessible')) {
      return window.jQuery(field).val() || null;
    }
    return field.value || null;
  }

  function init() {
    var form = getDocumentForm();
    if (!form) return;

    form.addEventListener('submit', function (e) {
      if (window.DEBUG) {
        console.log('Document form submit');
        var formData = new FormData(this);
        formData.forEach(function (value, key) {
          console.log('  ' + key + ':', value);
        });
      }

      var clienteVal = getClienteValue(form);
      if (!clienteVal) {
        e.preventDefault();
        var msg = document.documentElement.lang === 'en' || (document.documentElement.getAttribute('lang') || '').indexOf('en') === 0
          ? 'Please select a customer before continuing.'
          : 'Por favor seleccione un cliente antes de continuar.';
        alert(msg);
        return false;
      }

      if (typeof window.recalcTotales === 'function') {
        window.recalcTotales();
      }

      this.classList.add('loading');

      if (window.DEBUG) {
        console.log('Submitting document form');
      }
    });

    var inputs = form.querySelectorAll('.form-input, .form-select, .form-textarea');
    inputs.forEach(function (input) {
      input.addEventListener('change', function () {
        if (window.DEBUG) {
          console.log('Field changed:', this.name);
        }
      });
    });

    var buttons = form.querySelectorAll('.btn-primary, .btn-secondary, .btn-danger');
    buttons.forEach(function (button) {
      button.addEventListener('mouseenter', function () {
        this.style.transform = 'scale(1.05)';
      });
      button.addEventListener('mouseleave', function () {
        this.style.transform = 'scale(1)';
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
