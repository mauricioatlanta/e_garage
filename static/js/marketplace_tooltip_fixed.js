/**
 * JavaScript para integración de Marketplace en creación de documentos
 * Versión fija - Evita errores de sintaxis en modo estricto
 */

// Usar una función auto-ejecutable sin 'use strict' problemático
(function() {
  
  // Variable global para el tooltip de marketplace
  var MarketplaceTooltip = {
    currentTooltip: null,
    currentRow: null,
    currentInputElement: null,

    // Muestra un tooltip con precios de referencia
    show: function(inputElement, precios, notFound) {
      // Valor por defecto para notFound
      if (typeof notFound === 'undefined') notFound = false;
      
      // Ocultar tooltip anterior si existe
      this.hide();

      // Si no hay precios pero no es "no encontrado", simplemente no mostrar nada
      if ((!precios || precios.length === 0) && !notFound) {
        return;
      }

      // Crear el tooltip
      var tooltip = document.createElement('div');
      tooltip.className = 'marketplace-tooltip';
      tooltip.style.cssText = [
        'position: absolute;',
        'background: rgba(20, 20, 40, 0.98);',
        'border: 2px solid #00f2fe;',
        'border-radius: 0.5rem;',
        'padding: 1rem;',
        'z-index: 10000;',
        'min-width: 280px;',
        'max-width: 400px;',
        'box-shadow: 0 8px 25px rgba(0, 242, 254, 0.5);',
        'backdrop-filter: blur(10px);',
        'font-family: "Montserrat", "Segoe UI", sans-serif;'
      ].join(' ');

      // Título del tooltip
      var title = document.createElement('div');
      title.style.cssText = 'color: #00f2fe; font-weight: 700; font-size: 0.875rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;';
      title.textContent = '💰 Precios de Referencia';
      tooltip.appendChild(title);

      // Si no se encontró nada, mostrar mensaje sutil
      if (notFound || !precios || precios.length === 0) {
        var noFoundMsg = document.createElement('div');
        noFoundMsg.style.cssText = [
          'padding: 0.75rem;',
          'background: rgba(100, 100, 120, 0.2);',
          'border: 1px solid rgba(150, 150, 150, 0.3);',
          'border-radius: 0.375rem;',
          'color: #94a3b8;',
          'font-size: 0.875rem;',
          'text-align: center;',
          'font-style: italic;'
        ].join(' ');
        noFoundMsg.textContent = 'Sin referencia externa - Ingreso manual';
        tooltip.appendChild(noFoundMsg);
        
        // Agregar al documento
        var rect = inputElement.getBoundingClientRect();
        tooltip.style.left = (rect.right + 10) + 'px';
        tooltip.style.top = (rect.top + window.scrollY) + 'px';
        
        // Ajustar si se sale de la pantalla
        var tooltipRect = tooltip.getBoundingClientRect();
        if (tooltipRect.right > window.innerWidth) {
          tooltip.style.left = (rect.left - tooltipRect.width - 10) + 'px';
        }
        
        document.body.appendChild(tooltip);
        this.currentTooltip = tooltip;
        this.currentRow = inputElement.closest('.dynamic-element');
        
        // Ocultar después de 3 segundos
        var self = this;
        setTimeout(function() { self.hide(); }, 3000);
        return;
      }

      // Lista de precios
      for (var i = 0; i < precios.length; i++) {
        var precio = precios[i];
        var item = document.createElement('div');
        item.style.cssText = [
          'padding: 0.75rem;',
          'margin-bottom: ' + (i < precios.length - 1 ? '0.5rem' : '0') + ';',
          'background: rgba(0, 242, 254, 0.1);',
          'border: 1px solid rgba(0, 242, 254, 0.3);',
          'border-radius: 0.375rem;',
          'cursor: pointer;',
          'transition: all 0.2s ease;'
        ].join(' ');

        var disponibleHtml = precio.disponible ? 
          '<span style="color: #10b981; font-size: 0.75rem;">✓ Disponible</span>' : 
          '<span style="color: #ef4444; font-size: 0.75rem;">✗ Sin stock</span>';
        
        item.innerHTML = [
          '<div style="display: flex; justify-content: space-between; align-items: center;">',
          '  <div>',
          '    <div style="color: #ffffff; font-weight: 600; font-size: 0.875rem; margin-bottom: 0.25rem;">',
          '      ' + (precio.casa_repuestos || '') + '',
          '    </div>',
          '    ' + disponibleHtml + '',
          '  </div>',
          '  <div style="text-align: right;">',
          '    <div style="color: #00f2fe; font-weight: 700; font-size: 1rem;">',
          '      ' + this.formatPrice(precio.precio_referencia) + '',
          '    </div>',
          '  </div>',
          '</div>'
        ].join('');

        // Hover effect
        (function(itemElement) {
          itemElement.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(0, 242, 254, 0.2)';
            this.style.borderColor = '#00ffff';
            this.style.transform = 'translateX(4px)';
          });

          itemElement.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(0, 242, 254, 0.1)';
            this.style.borderColor = 'rgba(0, 242, 254, 0.3)';
            this.style.transform = 'translateX(0)';
          });
        })(item);

        // Click handler
        (function(precioObj, inputEl, selfObj) {
          item.addEventListener('click', function() {
            selfObj.selectPrice(precioObj, inputEl);
            selfObj.hide();
          });
        })(precio, inputElement, this);

        tooltip.appendChild(item);
      }

      // Posicionar el tooltip
      var rect = inputElement.getBoundingClientRect();
      tooltip.style.left = (rect.right + 10) + 'px';
      tooltip.style.top = (rect.top + window.scrollY) + 'px';

      // Ajustar si se sale de la pantalla
      var tooltipRect = tooltip.getBoundingClientRect();
      if (tooltipRect.right > window.innerWidth) {
        tooltip.style.left = (rect.left - tooltipRect.width - 10) + 'px';
      }

      // Agregar al documento
      document.body.appendChild(tooltip);

      this.currentTooltip = tooltip;
      this.currentRow = inputElement.closest('.dynamic-element');
      this.currentInputElement = inputElement;

      // Ocultar al hacer click fuera
      var self = this;
      setTimeout(function() {
        document.addEventListener('click', function(event) {
          if (self.currentTooltip && !self.currentTooltip.contains(event.target)) {
            self.hide();
          }
        }, { once: true });
      }, 100);

      // Cleanup: Ocultar al presionar Esc
      var handleEscape = function(e) {
        if (e.key === 'Escape' && self.currentTooltip) {
          self.hide();
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);

      // Cleanup: Ocultar cuando el input pierde el foco
      var handleBlur = function() {
        setTimeout(function() {
          if (self.currentTooltip && document.activeElement !== inputElement) {
            if (!self.currentTooltip.contains(document.activeElement)) {
              self.hide();
            }
          }
        }, 200);
      };
      inputElement.addEventListener('blur', handleBlur, { once: true });
    },

    // Oculta el tooltip actual
    hide: function() {
      if (this.currentTooltip) {
        this.currentTooltip.remove();
        this.currentTooltip = null;
        this.currentRow = null;
        this.currentInputElement = null;
      }
    },

    // Selecciona un precio y lo carga en el campo de costo
    selectPrice: function(precio, inputElement) {
      var row = inputElement.closest('.dynamic-element');
      if (!row) return;

      var precioCompraField = row.querySelector('.rep-precio-compra');
      if (precioCompraField) {
        var precioFormateado = this.formatPrice(precio.precio_referencia, true);
        precioCompraField.value = precioFormateado;
        
        // Feedback visual
        var originalBg = precioCompraField.style.backgroundColor || '';
        var originalBorder = precioCompraField.style.borderColor || '';
        var originalShadow = precioCompraField.style.boxShadow || '';
        
        precioCompraField.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        precioCompraField.style.backgroundColor = 'rgba(0, 242, 254, 0.25)';
        precioCompraField.style.borderColor = '#00f2fe';
        precioCompraField.style.boxShadow = '0 0 20px rgba(0, 242, 254, 0.7), inset 0 0 10px rgba(0, 242, 254, 0.2)';
        precioCompraField.style.transform = 'scale(1.02)';
        
        var self = this;
        setTimeout(function() {
          precioCompraField.style.transition = 'all 0.3s ease-out';
          precioCompraField.style.backgroundColor = originalBg;
          precioCompraField.style.borderColor = originalBorder;
          precioCompraField.style.boxShadow = originalShadow;
          precioCompraField.style.transform = 'scale(1)';
        }, 800);
        
        precioCompraField.dispatchEvent(new Event('input', { bubbles: true }));
        
        if (typeof window.recalcTotales === 'function') {
          window.recalcTotales();
        }

        console.log('✅ Precio de referencia cargado exitosamente');
      } else {
        console.warn('⚠️ Campo de precio de compra no encontrado en la fila');
      }
    },

    // Formatea un precio para mostrarlo
    formatPrice: function(precio, forInput) {
      if (typeof forInput === 'undefined') forInput = false;
      
      if (typeof precio === 'string') {
        precio = parseFloat(precio.replace(/[^\d.-]/g, ''));
      }
      if (isNaN(precio)) precio = 0;

      var country = (window.EG && window.EG.cfg && window.EG.cfg.country) || 'CL';
      if (country === 'CL') {
        if (forInput) {
          return precio.toLocaleString('es-CL');
        }
        return '$' + precio.toLocaleString('es-CL');
      } else {
        if (forInput) {
          return precio.toFixed(2);
        }
        return '$' + precio.toFixed(2);
      }
    },

    // Normaliza un part_number para búsqueda consistente
    normalizePartNumber: function(partNumber) {
      if (!partNumber || typeof partNumber !== 'string') {
        return '';
      }
      return partNumber.trim()
        .replace(/[\s\-_]/g, '')
        .toUpperCase();
    },

    // Consulta precios del marketplace por part_number
    consultarPrecios: function(partNumber, inputElement) {
      var self = this;
      var normalizedPartNumber = this.normalizePartNumber(partNumber);
      
      if (!normalizedPartNumber || normalizedPartNumber.length < 3) {
        this.hide();
        return;
      }

      var url = '/marketplace/api/precios/?part_number=' + encodeURIComponent(normalizedPartNumber);
      
      fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'same-origin'
      })
      .then(function(response) {
        if (!response.ok) {
          console.warn('⚠️ No se pudieron obtener precios del marketplace:', response.status);
          self.show(inputElement, [], true);
          return Promise.reject(new Error('HTTP ' + response.status));
        }
        return response.json();
      })
      .then(function(data) {
        if (data.precios && data.precios.length > 0) {
          self.show(inputElement, data.precios, false);
        } else {
          self.show(inputElement, [], true);
        }
      })
      .catch(function(error) {
        console.error('❌ Error consultando precios del marketplace:', error);
        self.show(inputElement, [], true);
      });
    },

    // Obtiene el token CSRF
    getCSRFToken: function() {
      var name = 'csrftoken';
      var cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
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
  if (typeof window !== 'undefined') {
    window.MarketplaceTooltip = window.MarketplaceTooltip || MarketplaceTooltip;
  }

})();