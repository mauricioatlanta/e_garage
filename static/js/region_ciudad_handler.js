/**
 * Handler robusto para región/estado → ciudad
 * Funciona en PC y móvil, con o sin Select2
 */

(function() {
  'use strict';

  /**
   * Inicializa el comportamiento región/estado → ciudad
   * Funciona tanto en PC como en móvil, con o sin Select2
   */
  function initEstadoCiudad() {
    // Detectar qué selects están presentes en el formulario
    const regionSelect = document.getElementById('id_region');
    const estadoSelect = document.getElementById('id_estado') || document.getElementById('id_estado_usa');
    const ciudadSelect = document.getElementById('id_ciudad') || document.getElementById('id_ciudad_usa');

    // Determinar qué par de selects usar
    let sourceSelect, targetSelect, paramName, ajaxUrl;

    if (estadoSelect && ciudadSelect) {
      // USA o países con estados
      sourceSelect = estadoSelect;
      targetSelect = ciudadSelect;
      paramName = 'estado_id';
      // URL del AJAX: obtener desde data-attribute o usar default
      ajaxUrl = estadoSelect.dataset.ciudadesUrl || 
                estadoSelect.dataset['ciudades-url'] || 
                '/taller/clientes/ajax/ciudades_usa/';
    } else if (regionSelect && ciudadSelect) {
      // Chile o países con regiones
      sourceSelect = regionSelect;
      targetSelect = ciudadSelect;
      paramName = 'region_id';
      // URL del AJAX: obtener desde data-attribute o usar default
      ajaxUrl = regionSelect.dataset.ciudadesUrl || 
                regionSelect.dataset['ciudades-url'] || 
                '/taller/clientes/ajax/ciudades/';
    } else {
      // No hay elementos, salir silenciosamente
      console.log('[RegionCiudad] No se encontraron selectores necesarios en esta página.');
      return;
    }

    console.log('[RegionCiudad] Inicializando con:', {
      sourceSelect: sourceSelect.id,
      targetSelect: targetSelect.id,
      paramName: paramName,
      ajaxUrl: ajaxUrl
    });

    // Limpiar y deshabilitar ciudades al inicio
    resetTargetSelect(targetSelect);

    // 🔑 EVENTO CRÍTICO: Funciona en PC + celular, con o sin Select2
    // Este evento 'change' es disparado tanto por select nativo como por Select2
    sourceSelect.addEventListener('change', function() {
      const sourceId = this.value;

      console.log(`[RegionCiudad] Cambio detectado: ${paramName}=${sourceId}`);

      // Si no hay selección, vaciar ciudades
      if (!sourceId) {
        resetTargetSelect(targetSelect);
        return;
      }

      // Mostrar estado de carga
      targetSelect.disabled = true;
      targetSelect.innerHTML = '<option value="">Cargando ciudades...</option>';

      // Construir URL con parámetro
      const url = `${ajaxUrl}?${paramName}=${encodeURIComponent(sourceId)}`;

      console.log(`[RegionCiudad] Solicitando: ${url}`);

      // Hacer petición AJAX
      fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          console.log(`[RegionCiudad] Ciudades recibidas:`, data);

          // Habilitar select
          targetSelect.disabled = false;

          // Limpiar y agregar opción por defecto
          targetSelect.innerHTML = '<option value="">Selecciona una ciudad</option>';

          // Verificar si data es array o tiene propiedad .ciudades
          const ciudades = Array.isArray(data) ? data : (data.ciudades || []);

          if (ciudades.length === 0) {
            targetSelect.innerHTML = '<option value="">No hay ciudades disponibles</option>';
            console.warn('[RegionCiudad] No se encontraron ciudades para:', sourceId);
            return;
          }

          // Agregar las ciudades
          ciudades.forEach(function(ciudad) {
            const option = document.createElement('option');
            option.value = ciudad.id;
            option.textContent = ciudad.nombre;
            targetSelect.appendChild(option);
          });

          console.log(`[RegionCiudad] ${ciudades.length} ciudades cargadas exitosamente`);

          // Si Select2 está activo, disparar su actualización
          if (window.jQuery && jQuery.fn.select2) {
            if (jQuery(targetSelect).hasClass('select2-hidden-accessible')) {
              jQuery(targetSelect).trigger('change.select2');
            }
          }
        })
        .catch(error => {
          console.error('[RegionCiudad] Error cargando ciudades:', error);

          targetSelect.disabled = false;
          targetSelect.innerHTML = '<option value="">Error al cargar ciudades</option>';

          // Mostrar error visible al usuario
          alert('Error al cargar las ciudades. Por favor, intenta de nuevo o recarga la página.');
        });
    });

    console.log('[RegionCiudad] Handler configurado exitosamente');
  }

  /**
   * Resetea el select de ciudades a su estado inicial
   */
  function resetTargetSelect(select) {
    select.disabled = true;
    select.innerHTML = '<option value="">Selecciona primero una región/estado</option>';
  }

  // ===== INICIALIZACIÓN =====
  document.addEventListener('DOMContentLoaded', function() {
    console.log('[RegionCiudad] DOM cargado, inicializando...');
    
    // 1) Siempre enganchar el handler (PC + móvil)
    initEstadoCiudad();

    // 2) Opcional: activar Select2 solo en pantallas grandes
    // NOTA: Esta parte es OPCIONAL y NO afecta la funcionalidad básica
    if (window.jQuery && jQuery.fn.select2) {
      // Verificar si estamos en desktop (opcional mejorar UX)
      const isDesktop = window.innerWidth > 768;
      
      if (isDesktop) {
        console.log('[RegionCiudad] Pantalla grande detectada, inicializando Select2...');
        
        const selects = ['#id_region', '#id_estado', '#id_estado_usa', '#id_ciudad', '#id_ciudad_usa'];
        
        selects.forEach(function(selector) {
          const $select = jQuery(selector);
          
          if ($select.length && !$select.hasClass('select2-hidden-accessible')) {
            $select.select2({ 
              width: '100%',
              language: 'es'
            });
            console.log(`[RegionCiudad] Select2 aplicado a ${selector}`);
          }
        });
      } else {
        console.log('[RegionCiudad] Pantalla móvil detectada, usando selectores nativos');
      }
    }
  });

  // Hacer disponible globalmente si se necesita
  window.initEstadoCiudad = initEstadoCiudad;

})();











