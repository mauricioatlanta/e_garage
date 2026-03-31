/**
 * JavaScript para integración de Marketplace en creación de documentos
 * Muestra precios de referencia de casas de repuestos cuando el mecánico escribe un part_number
 */

(function() {
  'use strict';

  // Variable global para el tooltip de marketplace
  window.MarketplaceTooltip = {
    currentTooltip: null,
    currentRow: null,
    currentInputElement: null,  // Track del input actual para cleanup

    /**
     * Muestra un tooltip con precios de referencia del marketplace
     * @param {HTMLElement} inputElement - El input donde se está escribiendo el part_number
     * @param {Array} precios - Array de precios desde la API
     * @param {boolean} notFound - Si es true, muestra mensaje de "no encontrado"
     */
    show: function(inputElement, precios, notFound = false) {
      // Ocultar tooltip anterior si existe
      this.hide();

      // Si no hay precios pero no es "no encontrado", simplemente no mostrar nada
      if ((!precios || precios.length === 0) && !notFound) {
        return;
      }

      // Crear el tooltip
      const tooltip = document.createElement('div');
      tooltip.className = 'marketplace-tooltip';
      tooltip.style.cssText = `
        position: absolute;
        background: rgba(20, 20, 40, 0.98);
        border: 2px solid #00f2fe;
        border-radius: 0.5rem;
        padding: 1rem;
        z-index: 10000;
        min-width: 280px;
        max-width: 400px;
        box-shadow: 0 8px 25px rgba(0, 242, 254, 0.5);
        backdrop-filter: blur(10px);
        font-family: 'Montserrat', 'Segoe UI', sans-serif;
      `;

      // Título del tooltip
      const title = document.createElement('div');
      title.style.cssText = 'color: #00f2fe; font-weight: 700; font-size: 0.875rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;';
      title.textContent = '💰 Precios de Referencia';
      tooltip.appendChild(title);

      // Si no se encontró nada, mostrar mensaje sutil
      if (notFound || !precios || precios.length === 0) {
        const noFoundMsg = document.createElement('div');
        noFoundMsg.style.cssText = `
          padding: 0.75rem;
          background: rgba(100, 100, 120, 0.2);
          border: 1px solid rgba(150, 150, 150, 0.3);
          border-radius: 0.375rem;
          color: #94a3b8;
          font-size: 0.875rem;
          text-align: center;
          font-style: italic;
        `;
        noFoundMsg.textContent = 'Sin referencia externa - Ingreso manual';
        tooltip.appendChild(noFoundMsg);
        
        // Agregar al documento
        const rect = inputElement.getBoundingClientRect();
        tooltip.style.left = (rect.right + 10) + 'px';
        tooltip.style.top = (rect.top + window.scrollY) + 'px';
        
        // Ajustar si se sale de la pantalla
        const tooltipRect = tooltip.getBoundingClientRect();
        if (tooltipRect.right > window.innerWidth) {
          tooltip.style.left = (rect.left - tooltipRect.width - 10) + 'px';
        }
        
        document.body.appendChild(tooltip);
        this.currentTooltip = tooltip;
        this.currentRow = inputElement.closest('.dynamic-element');
        
        // Ocultar después de 3 segundos
        setTimeout(() => this.hide(), 3000);
        return;
      }

      // Lista de precios
      precios.forEach((precio, index) => {
        const item = document.createElement('div');
        item.style.cssText = `
          padding: 0.75rem;
          margin-bottom: ${index < precios.length - 1 ? '0.5rem' : '0'};
          background: rgba(0, 242, 254, 0.1);
          border: 1px solid rgba(0, 242, 254, 0.3);
          border-radius: 0.375rem;
          cursor: pointer;
          transition: all 0.2s ease;
        `;

        item.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="color: #ffffff; font-weight: 600; font-size: 0.875rem; margin-bottom: 0.25rem;">
                ${precio.casa_repuestos}
              </div>
              ${precio.disponible ? 
                '<span style="color: #10b981; font-size: 0.75rem;">✓ Disponible</span>' : 
                '<span style="color: #ef4444; font-size: 0.75rem;">✗ Sin stock</span>'
              }
            </div>
            <div style="text-align: right;">
              <div style="color: #00f2fe; font-weight: 700; font-size: 1rem;">
                ${this.formatPrice(precio.precio_referencia)}
              </div>
            </div>
          </div>
        `;

        // Hover effect
        item.addEventListener('mouseenter', function() {
          this.style.background = 'rgba(0, 242, 254, 0.2)';
          this.style.borderColor = '#00ffff';
          this.style.transform = 'translateX(4px)';
        });

        item.addEventListener('mouseleave', function() {
          this.style.background = 'rgba(0, 242, 254, 0.1)';
          this.style.borderColor = 'rgba(0, 242, 254, 0.3)';
          this.style.transform = 'translateX(0)';
        });

        // Click handler - cargar precio en el campo de costo
        item.addEventListener('click', () => {
          this.selectPrice(precio, inputElement);
          this.hide();
        });

        tooltip.appendChild(item);
      });

      // Posicionar el tooltip
      const rect = inputElement.getBoundingClientRect();
      tooltip.style.left = (rect.right + 10) + 'px';
      tooltip.style.top = (rect.top + window.scrollY) + 'px';

      // Ajustar si se sale de la pantalla
      const tooltipRect = tooltip.getBoundingClientRect();
      if (tooltipRect.right > window.innerWidth) {
        tooltip.style.left = (rect.left - tooltipRect.width - 10) + 'px';
      }

      // Agregar al documento
      document.body.appendChild(tooltip);

      this.currentTooltip = tooltip;
      this.currentRow = inputElement.closest('.dynamic-element');
      this.currentInputElement = inputElement;  // Track del input para cleanup

      // Ocultar al hacer click fuera
      setTimeout(() => {
        document.addEventListener('click', this.handleClickOutside.bind(this), { once: true });
      }, 100);

      // Cleanup: Ocultar al presionar Esc
      const handleEscape = (e) => {
        if (e.key === 'Escape' && this.currentTooltip) {
          this.hide();
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);

      // Cleanup: Ocultar cuando el input pierde el foco definitivamente
      const handleBlur = () => {
        // Delay para permitir clicks en el tooltip
        setTimeout(() => {
          if (this.currentTooltip && document.activeElement !== inputElement) {
            // Verificar que el foco no esté en el tooltip
            if (!this.currentTooltip.contains(document.activeElement)) {
              this.hide();
            }
          }
        }, 200);
      };
      inputElement.addEventListener('blur', handleBlur, { once: true });
    },

    /**
     * Oculta el tooltip actual y limpia todos los recursos
     */
    hide: function() {
      if (this.currentTooltip) {
        this.currentTooltip.remove();
        this.currentTooltip = null;
        this.currentRow = null;
        this.currentInputElement = null;
      }
    },

    /**
     * Maneja clicks fuera del tooltip
     */
    handleClickOutside: function(event) {
      if (this.currentTooltip && !this.currentTooltip.contains(event.target)) {
        this.hide();
      }
    },

    /**
     * Selecciona un precio y lo carga en el campo de costo
     */
    selectPrice: function(precio, inputElement) {
      const row = inputElement.closest('.dynamic-element');
      if (!row) return;

      // Buscar el campo de precio de compra
      const precioCompraField = row.querySelector('.rep-precio-compra');
      if (precioCompraField) {
        // Formatear el precio
        const precioFormateado = this.formatPrice(precio.precio_referencia, true);
        precioCompraField.value = precioFormateado;
        
        // Feedback visual: Animación verde/cian fluida (recompensa visual)
        // Guardar estilos originales para restaurar
        const originalBg = precioCompraField.style.backgroundColor || '';
        const originalBorder = precioCompraField.style.borderColor || '';
        const originalShadow = precioCompraField.style.boxShadow || '';
        
        // Aplicar animación suave
        precioCompraField.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        precioCompraField.style.backgroundColor = 'rgba(0, 242, 254, 0.25)';
        precioCompraField.style.borderColor = '#00f2fe';
        precioCompraField.style.boxShadow = '0 0 20px rgba(0, 242, 254, 0.7), inset 0 0 10px rgba(0, 242, 254, 0.2)';
        precioCompraField.style.transform = 'scale(1.02)';
        
        // Restaurar estilo original después de 800ms con transición suave
        setTimeout(() => {
          precioCompraField.style.transition = 'all 0.3s ease-out';
          precioCompraField.style.backgroundColor = originalBg;
          precioCompraField.style.borderColor = originalBorder;
          precioCompraField.style.boxShadow = originalShadow;
          precioCompraField.style.transform = 'scale(1)';
        }, 800);
        
        // Disparar evento para recalcular
        precioCompraField.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Si hay una función de recalc, llamarla
        if (typeof window.recalcTotales === 'function') {
          window.recalcTotales();
        }

        // Log de éxito con información detallada
        console.log('✅ Precio de referencia cargado exitosamente:', {
          casa_repuestos: precio.casa_repuestos,
          precio_referencia: precio.precio_referencia,
          disponible: precio.disponible,
          timestamp: new Date().toISOString()
        });
      } else {
        console.warn('⚠️ Campo de precio de compra no encontrado en la fila');
      }
    },

    /**
     * Formatea un precio para mostrarlo
     */
    formatPrice: function(precio, forInput = false) {
      if (typeof precio === 'string') {
        precio = parseFloat(precio.replace(/[^\d.-]/g, ''));
      }
      if (isNaN(precio)) precio = 0;

      // Determinar el formato según el país (simplificado)
      const country = window.EG?.cfg?.country || 'CL';
      if (country === 'CL') {
        // Formato chileno: $45.000
        if (forInput) {
          return precio.toLocaleString('es-CL');
        }
        return '$' + precio.toLocaleString('es-CL');
      } else {
        // Formato USA: $45.00
        if (forInput) {
          return precio.toFixed(2);
        }
        return '$' + precio.toFixed(2);
      }
    },

    /**
     * Normaliza un part_number para búsqueda consistente
     * - Trim espacios
     * - Remueve guiones y espacios internos
     * - Convierte a mayúsculas
     * @param {string} partNumber - Part number crudo
     * @returns {string} Part number normalizado
     */
    normalizePartNumber: function(partNumber) {
      if (!partNumber || typeof partNumber !== 'string') {
        return '';
      }
      // Trim, remover guiones y espacios, convertir a mayúsculas
      return partNumber.trim()
        .replace(/[\s\-_]/g, '')  // Remover espacios, guiones y underscores
        .toUpperCase();
    },

    /**
     * Consulta precios del marketplace por part_number
     * @param {string} partNumber - El part number a buscar
     * @param {HTMLElement} inputElement - El input element donde mostrar el tooltip
     */
    consultarPrecios: async function(partNumber, inputElement) {
      // Normalizar part_number antes de validar
      const normalizedPartNumber = this.normalizePartNumber(partNumber);
      
      if (!normalizedPartNumber || normalizedPartNumber.length < 3) {
        this.hide();
        return;
      }

      try {
        // Usar part_number normalizado para la petición
        const url = '/marketplace/api/precios/?part_number=' + encodeURIComponent(normalizedPartNumber);
        
        const response = await fetch(url, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': this.getCSRFToken(),
          },
          credentials: 'same-origin'
        });

        if (!response.ok) {
          console.warn('⚠️ No se pudieron obtener precios del marketplace:', response.status);
          // Mostrar mensaje de "no encontrado" en lugar de ocultar
          this.show(inputElement, [], true);
          return;
        }

        const data = await response.json();
        if (data.precios && data.precios.length > 0) {
          this.show(inputElement, data.precios, false);
        } else {
          // Mostrar mensaje de "no encontrado" en lugar de ocultar
          this.show(inputElement, [], true);
        }
      } catch (error) {
        console.error('❌ Error consultando precios del marketplace:', error);
        // Mostrar mensaje de "no encontrado" en lugar de ocultar
        this.show(inputElement, [], true);
      }
    },
      } } } catch(error) {
        console.error('❌ Error consultando precios del marketplace:', error);
        // Mostrar mensaje de "no encontrado" en lugar de ocultar
        this.show(inputElement, [], true);
      }
    },

    /**
     * Obtiene el token CSRF
     */
    getCSRFToken: function() {
      const name = 'csrftoken';
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue || '';
    }
  };

  // Exponer globalmente
  window.MarketplaceTooltip = window.MarketplaceTooltip || MarketplaceTooltip;

})();
