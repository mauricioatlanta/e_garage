// Integración entre el sistema existente y el nuevo sistema de totales por país
(function () {
  'use strict';

  // Función que conecta el sistema existente con el nuevo
  function integrarTotalesPorPais() {

    // Cuando se actualicen los totales en el sistema existente, también actualizar el nuevo
    const originalActualizarTotales = window.actualizarTotalesDocumento;

    window.actualizarTotalesDocumento = function() {
      // Ejecutar la función original primero
      if (originalActualizarTotales) {
        originalActualizarTotales();
      }

      // Luego ejecutar el nuevo sistema
      if (window.recalcDocumentoTotales) {
        window.recalcDocumentoTotales();
      }
    };

    // También conectar los totales específicos
    const originalRepuestos = window.actualizarTotalRepuestos;
    window.actualizarTotalRepuestos = function() {
      if (originalRepuestos) {
        originalRepuestos();
      }
      if (window.recalcDocumentoTotales) {
        window.recalcDocumentoTotales();
      }
    };

    const originalServicios = window.actualizarTotalServicios;
    window.actualizarTotalServicios = function() {
      if (originalServicios) {
        originalServicios();
      }
      if (window.recalcDocumentoTotales) {
        window.recalcDocumentoTotales();
      }
    };
  }

  // Función para agregar clases necesarias a filas existentes que no las tengan
  function agregarClasesAFilas() {
    // Repuestos
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach(tr => {
      if (!tr.classList.contains('js-line')) {
        tr.classList.add('js-line');
        tr.setAttribute('data-kind', 'repuesto');

        const subtotalCell = tr.querySelector('.subtotal-repuesto');
        if (subtotalCell && !subtotalCell.classList.contains('js-subtotal')) {
          subtotalCell.classList.add('js-subtotal');
          subtotalCell.setAttribute('data-subtotal', '');
        }
      }
    });

    // Servicios
    document.querySelectorAll('#tabla-servicios tbody tr').forEach(tr => {
      if (!tr.classList.contains('js-line')) {
        tr.classList.add('js-line');
        tr.setAttribute('data-kind', 'servicio');

        const precioInput = tr.querySelector('.precio-servicio-input');
        if (precioInput && !precioInput.classList.contains('js-subtotal')) {
          precioInput.classList.add('js-subtotal');
          precioInput.setAttribute('data-subtotal', '');
        }
      }
    });
  }

  // Configurar observers para filas dinámicas
  function configurarObservers() {
    const tablaRepuestos = document.querySelector('#tabla-repuestos tbody');
    const tablaServicios = document.querySelector('#tabla-servicios tbody');

    if (tablaRepuestos) {
      const observer = new MutationObserver(() => {
        agregarClasesAFilas();
      });
      observer.observe(tablaRepuestos, { childList: true });
    }

    if (tablaServicios) {
      const observer = new MutationObserver(() => {
        agregarClasesAFilas();
      });
      observer.observe(tablaServicios, { childList: true });
    }
  }

  // Inicializar cuando el DOM esté listo
  document.addEventListener('DOMContentLoaded', function() {
    // Dar tiempo a que se cargue el sistema existente
    setTimeout(() => {
      integrarTotalesPorPais();
      agregarClasesAFilas();
      configurarObservers();

      // Forzar un recálculo inicial
      if (window.actualizarTotalesDocumento) {
        window.actualizarTotalesDocumento();
      }
    }, 500);
  });
})();
