// Wait for DOM to be ready
console.log("📄 JavaScript externo cargado");

// FUNCIÓN PARA ACTUALIZAR NÚMERO DE DOCUMENTO
function updateDocumentNumber() {
  const tipoInput = document.getElementById('tipo') || document.querySelector('input[name="tipo"]');
  const numberDisplay = document.getElementById('document-number');
  
  if (!tipoInput || !numberDisplay) {
    console.log('⚠️ No se encontraron elementos para actualizar número de documento');
    return;
  }
  
  const tipo = tipoInput.value;
  if (!tipo) {
    numberDisplay.textContent = 'Se generará automáticamente';
    return;
  }
  
  // Mapear los valores del formulario a los valores esperados por la API
  const tipoMapping = {
    'FAC': 'FACTURA',
    'COT': 'PRESUPUESTO', 
    'ORD': 'ORDEN DE TRABAJO',
    'REC': 'RECIBO'
  };
  
  const apiTipo = tipoMapping[tipo] || tipo;
  
  // Detectar país desde la URL
  const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
  const apiUrl = `/${countryPrefix}/documentos/api/next-number/?tipo=${apiTipo}`;
  
  console.log('📡 Obteniendo número de documento para tipo:', tipo);
  
  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      if (data.numero) {
        numberDisplay.textContent = data.numero;
        // También llenar el campo del formulario
        const numeroField = document.getElementById('id_numero');
        if (numeroField) {
          numeroField.value = data.numero;
        }
        
        // También llenar el campo numero_documento_db
        const numeroDocumentoField = document.getElementById('id_numero_documento_db');
        if (numeroDocumentoField) {
          numeroDocumentoField.value = data.numero;
        }
        console.log('✅ Número de documento obtenido:', data.numero);
      } else {
        console.error('❌ Error al obtener número:', data.error);
        numberDisplay.textContent = 'Error generating number';
      }
    })
    .catch(error => {
      console.error('❌ Error en la solicitud:', error);
      numberDisplay.textContent = 'Error generating number';
    });
}

// FUNCIONES DE FORMATO DE MONEDA CHILENA
function formatChileanCurrency(value) {
  const numValue = Math.round(parseFloat(value) || 0);
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(numValue);
}

function formatChileanPriceInput(input) {
  const value = input.value.replace(/[^\d]/g, ''); // Solo números
  if (value === '') {
    input.value = '';
    return;
  }
  
  const numValue = parseInt(value);
  const formatted = new Intl.NumberFormat('es-CL', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(numValue);
  
  input.value = formatted;
}

// Función para recalcular totales con formato chileno
function recalcTotalsChilean() {
  let sumRep = 0, sumServ = 0, sumOtros = 0;
  
  // Sumar repuestos
  document.querySelectorAll('.repuesto-line, [data-repuesto-index]').forEach(l => {
    const priceInput = l.querySelector('input[name*="precio_venta"], input[name*="precio_unitario"]');
    const qtyInput = l.querySelector('input[name*="cantidad"]');
    if (priceInput && qtyInput) {
      const price = parseFloat(priceInput.value.replace(/[^\d]/g, '') || 0);
      const qty = parseFloat(qtyInput.value || 0);
      const subtotal = price * qty;
      sumRep += subtotal;
      
      // Actualizar subtotal si existe
      const subtotalEl = l.querySelector('.subtotal, [data-subtotal]');
      if (subtotalEl) {
        subtotalEl.textContent = formatChileanCurrency(subtotal);
      }
    }
  });
  
  // Sumar servicios
  document.querySelectorAll('.servicio-line, [data-servicio-index]').forEach(l => {
    const priceInput = l.querySelector('.servicio-valor, input[name*="precio"], input[name*="valor"]');
    if (priceInput) {
      const price = parseFloat(priceInput.value.replace(/[^\d]/g, '') || 0);
      sumServ += price;
    }
  });
  
  // Sumar otros servicios
  document.querySelectorAll('.otro-servicio-line, [data-otro-servicio-index]').forEach(l => {
    const priceInput = l.querySelector('input[name*="precio"], input[name*="valor"]');
    if (priceInput) {
      const price = parseFloat(priceInput.value.replace(/[^\d]/g, '') || 0);
      sumOtros += price;
      
      // Actualizar subtotal si existe
      const subtotalEl = l.querySelector('.subtotal, [data-subtotal]');
      if (subtotalEl) {
        subtotalEl.textContent = formatChileanCurrency(price);
      }
    }
  });
  
  const subtotal = sumRep + sumServ + sumOtros;
  const taxRate = 0.19; // 19% IVA Chile
  const tax = subtotal * taxRate;
  const total = subtotal + tax;
  
  // Actualizar totales en la página
  const elements = {
    'total-repuestos': sumRep,
    'total-servicios': sumServ,
    'total-otros-servicios': sumOtros,
    'subtotal': subtotal,
    'monto-impuestos': tax,
    'gran-total': total
  };
  
  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id) || document.querySelector(`[data-total="${id}"]`);
    if (element) {
      element.value = formatChileanCurrency(value);
    }
  });
  
  console.log('💰 Totales recalculados:', { sumRep, sumServ, sumOtros, subtotal, tax, total });
}

document.addEventListener('DOMContentLoaded', function() {
  console.log("🔧 Iniciando sistema de formulario mejorado...");
  console.log("🔐 Usuario autenticado:", document.body.dataset.user || "No disponible");
  console.log("🍪 Cookies:", document.cookie);
  console.log("📄 URL actual:", window.location.href);
  
  // Test simple para verificar que el JavaScript se está ejecutando
  console.log("✅ JavaScript cargado correctamente");

  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => c.querySelectorAll(s);
  const on = (el, ev, fn) => el && el.addEventListener(ev, fn);

  // Configuración de endpoints
  const endpointNextNumber = document.body.dataset.endpointNextNumber;
  const endpointClientesSearch = document.body.dataset.endpointClientesSearch;
  const endpointRepuestosSearch = document.body.dataset.endpointRepuestosSearch;
  const endpointServiciosSearch = document.body.dataset.endpointServiciosSearch;
  const endpointOtrosServiciosSearch = document.body.dataset.endpointOtrosServiciosSearch;

  console.log("📡 Endpoints configurados:", {
    nextNumber: endpointNextNumber,
    clientesSearch: endpointClientesSearch,
    repuestosSearch: endpointRepuestosSearch,
    serviciosSearch: endpointServiciosSearch,
    otrosServiciosSearch: endpointOtrosServiciosSearch
  });

  // Elementos del DOM
  const tipoSel = document.getElementById("id_tipo");
  const numeroField = document.getElementById("id_numero");
  const clienteSearch = document.getElementById("id_cliente_search");
  const clienteSelect = document.querySelector("select[name='cliente']");
  const vehiculoSelect = document.querySelector("select[name='vehiculo']");
  const searchResults = document.getElementById("cliente_search_results");

  console.log("🎯 Elementos encontrados:", {
    tipoSel: !!tipoSel,
    numeroField: !!numeroField,
    clienteSearch: !!clienteSearch,
    clienteSelect: !!clienteSelect,
    vehiculoSelect: !!vehiculoSelect,
    searchResults: !!searchResults
  });
  
  // Debug específico para filtrado de vehículos
  console.log("🚗 DEBUG VEHÍCULOS:", {
    clienteSelect: clienteSelect,
    vehiculoSelect: vehiculoSelect,
    clienteSelectId: clienteSelect?.id,
    vehiculoSelectId: vehiculoSelect?.id
  });
  
  // Debug de todos los elementos del DOM
  console.log("🔍 TODOS LOS ELEMENTOS DEL DOM:");
  console.log("  - select[name='cliente']:", document.querySelector("select[name='cliente']"));
  console.log("  - select[name='vehiculo']:", document.querySelector("select[name='vehiculo']"));
  console.log("  - #id_cliente_search:", document.getElementById("id_cliente_search"));
  console.log("  - #cliente_search_results:", document.getElementById("cliente_search_results"));
  
  // Debug adicional - buscar todos los selects
  console.log("🔍 TODOS LOS SELECTS EN LA PÁGINA:");
  console.log("  - Todos los selects:", document.querySelectorAll("select"));
  console.log("  - Selects con name='cliente':", document.querySelectorAll("select[name='cliente']"));
  console.log("  - Selects con name='vehiculo':", document.querySelectorAll("select[name='vehiculo']"));
  
  // Verificar si los elementos existen realmente
  setTimeout(() => {
    console.log("🔍 VERIFICACIÓN DESPUÉS DE 1 SEGUNDO:");
    console.log("  - Cliente select encontrado:", document.querySelectorAll("select[name='cliente']").length > 0);
    console.log("  - Vehículo select encontrado:", document.querySelectorAll("select[name='vehiculo']").length > 0);
    console.log("  - Cliente select elemento:", document.querySelector("select[name='cliente']"));
    console.log("  - Vehículo select elemento:", document.querySelector("select[name='vehiculo']"));
  }, 1000);
  document.querySelectorAll("select").forEach((select, index) => {
    console.log(`  Select ${index}:`, {
      name: select.name,
      id: select.id,
      className: select.className,
      element: select
    });
  });
  

  // Variables para control de búsqueda
  let searchTimeout = null;
  let currentSearchQuery = "";

  // Función para refrescar preview del número
  async function refreshPreview() {
    console.log("🔄 Refrescando preview...");
    const tipo = tipoSel?.value;
    console.log("📋 Tipo seleccionado:", tipo);

    if (!endpointNextNumber) {
      console.error("❌ No hay endpoint configurado para números");
      return;
    }
    if (!tipo) {
      console.warn("⚠️ No hay tipo seleccionado");
      return;
    }
    if (!numeroField) {
      console.error("❌ No se encontró el campo de número");
      return;
    }

    try {
      const url = new URL(endpointNextNumber, window.location.origin);
      url.searchParams.set("tipo", tipo);
      console.log("🌐 Llamando a:", url.toString());

      const res = await fetch(url, { credentials: "same-origin" });
      console.log("📡 Respuesta recibida:", res.status, res.statusText);

      const data = await res.json();
      console.log("📊 Datos recibidos:", data);

      if (data.ok) {
        const numeroValue = data.preview || "";
        numeroField.value = numeroValue;
        
        // También llenar el campo numero_documento_db
        const numeroDocumentoField = document.getElementById('id_numero_documento_db');
        if (numeroDocumentoField) {
          numeroDocumentoField.value = numeroValue;
        }
        
        console.log("✅ Número actualizado:", data.preview);
      } else {
        console.error("❌ Error en respuesta:", data);
        numeroField.value = "";
        
        // También limpiar el campo numero_documento_db
        const numeroDocumentoField = document.getElementById('id_numero_documento_db');
        if (numeroDocumentoField) {
          numeroDocumentoField.value = "";
        }
      }
    } catch (e) {
      console.error("❌ Error en preview:", e);
      numeroField.value = "";
      
      // También limpiar el campo numero_documento_db
      const numeroDocumentoField = document.getElementById('id_numero_documento_db');
      if (numeroDocumentoField) {
        numeroDocumentoField.value = "";
      }
    }
  }

  // Función para buscar clientes
  async function searchClientes(query) {
    console.log("🔍 Buscando clientes:", query);

    if (!endpointClientesSearch) {
      console.error("❌ No hay endpoint configurado para búsqueda de clientes");
      return;
    }

    if (!query || query.length < 2) {
      hideSearchResults();
      return;
    }

    try {
      const url = new URL(endpointClientesSearch, window.location.origin);
      url.searchParams.set("q", query);
      console.log("🌐 Llamando a:", url.toString());

      const res = await fetch(url, { credentials: "same-origin" });
      console.log("📡 Respuesta recibida:", res.status, res.statusText);

      const data = await res.json();
      console.log("📊 Datos recibidos:", data);

      if (data.ok && data.results) {
        showSearchResults(data.results);
        console.log("✅ Resultados mostrados:", data.results.length);
      } else {
        console.error("❌ Error en respuesta:", data);
        hideSearchResults();
      }
    } catch (e) {
      console.error("❌ Error en búsqueda:", e);
      hideSearchResults();
    }
  }

  // Función para mostrar resultados de búsqueda
  function showSearchResults(results) {
    if (!searchResults) return;

    if (results.length === 0) {
      searchResults.innerHTML = '<div class="search-result-item no-results">No se encontraron clientes</div>';
    } else {
      searchResults.innerHTML = results.map(cliente => `
        <div class="search-result-item" data-cliente-id="${cliente.id}">
          <div class="cliente-name">${cliente.text}</div>
          ${cliente.email ? `<div class="cliente-email">${cliente.email}</div>` : ''}
          ${cliente.telefono ? `<div class="cliente-phone">${cliente.telefono}</div>` : ''}
        </div>
      `).join('');
    }

    searchResults.style.display = 'block';

    // Agregar event listeners a los resultados
    searchResults.querySelectorAll('.search-result-item').forEach(item => {
      if (item.dataset.clienteId) {
        item.addEventListener('click', () => selectCliente(item.dataset.clienteId, item.querySelector('.cliente-name').textContent));
      }
    });
  }

  // Función para ocultar resultados de búsqueda
  function hideSearchResults() {
    if (searchResults) {
      searchResults.style.display = 'none';
    }
  }

  // Función para seleccionar un cliente
  function selectCliente(clienteId, clienteName) {
    console.log("👤 Cliente seleccionado:", clienteId, clienteName);

    if (clienteSelect) {
      // Buscar la opción correspondiente en el select
      const option = clienteSelect.querySelector(`option[value="${clienteId}"]`);
      if (option) {
        clienteSelect.value = clienteId;
        console.log("✅ Cliente seleccionado en el select");
        
        // IMPORTANTE: Disparar el evento change para activar el filtrado de vehículos
        const changeEvent = new Event('change', { bubbles: true });
        clienteSelect.dispatchEvent(changeEvent);
        console.log("🔄 Evento change disparado para filtrado de vehículos");
      } else {
        console.warn("⚠️ No se encontró la opción en el select");
      }
    }

    if (clienteSearch) {
      clienteSearch.value = clienteName;
    }

    hideSearchResults();
  }

  // Event listeners
  if (tipoSel) {
    tipoSel.addEventListener("change", refreshPreview);
    console.log("👂 Event listener agregado para cambio de tipo");
  } else {
    console.error("❌ No se pudo agregar event listener - tipoSel no encontrado");
  }

  if (clienteSearch) {
    clienteSearch.addEventListener("input", (e) => {
      const query = e.target.value.trim();
      
      // Cancelar búsqueda anterior si existe
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }

      // Programar nueva búsqueda con delay
      searchTimeout = setTimeout(() => {
        if (query !== currentSearchQuery) {
          currentSearchQuery = query;
          searchClientes(query);
        }
      }, 300); // 300ms de delay
    });

    // Ocultar resultados al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!clienteSearch.contains(e.target) && !searchResults.contains(e.target)) {
        hideSearchResults();
      }
    });

    console.log("👂 Event listeners agregados para búsqueda de clientes");
  } else {
    console.error("❌ No se pudo agregar event listeners - clienteSearch no encontrado");
  }

  // Ejecutar preview inicial
  console.log("🚀 Ejecutando preview inicial...");
  refreshPreview();

  // ===== SISTEMA DE REPUESTOS =====
  console.log("🔧 Iniciando sistema de repuestos...");

  // Variables para control de repuestos
  let repuestoIndex = 0;
  let repuestosContainer = document.getElementById("repuestos-container");
  let btnAddRepuesto = document.querySelector(".btn-add-repuesto");

  // Función para buscar repuestos
  async function searchRepuestos(partNumber, repuestoItem) {
    console.log("🔍 Buscando repuestos:", partNumber);

    if (!endpointRepuestosSearch) {
      console.error("❌ No hay endpoint configurado para búsqueda de repuestos");
      return;
    }

    if (!partNumber || partNumber.length < 2) {
      hideRepuestoSearchResults(repuestoItem);
      return;
    }

    try {
      const url = new URL(endpointRepuestosSearch, window.location.origin);
      url.searchParams.set("part_number", partNumber);
      console.log("🌐 Llamando a:", url.toString());

      const res = await fetch(url, { 
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });
      console.log("📡 Respuesta recibida:", res.status, res.statusText);

      const data = await res.json();
      console.log("📊 Datos recibidos:", data);

      if (data.ok && data.results) {
        showRepuestoSearchResults(data.results, repuestoItem);
        console.log("✅ Resultados mostrados:", data.results.length);
      } else {
        console.error("❌ Error en respuesta:", data);
        hideRepuestoSearchResults(repuestoItem);
      }
    } catch (e) {
      console.error("❌ Error en búsqueda:", e);
      hideRepuestoSearchResults(repuestoItem);
    }
  }

  // Función para mostrar resultados de búsqueda de repuestos
  function showRepuestoSearchResults(results, repuestoItem) {
    const searchResults = repuestoItem.querySelector(".repuesto-search-results");
    if (!searchResults) return;

    if (results.length === 0) {
      searchResults.innerHTML = '<div class="repuesto-search-result-item no-results">No se encontraron repuestos</div>';
    } else {
      searchResults.innerHTML = results.map(repuesto => `
        <div class="repuesto-search-result-item" data-repuesto-id="${repuesto.id}">
          <div class="repuesto-result-part-number">${repuesto.part_number}</div>
          <div class="repuesto-result-nombre">${repuesto.nombre}</div>
          <div class="repuesto-result-precio">Precio: ${formatChileanCurrency(repuesto.precio_venta)} | Stock: ${repuesto.cantidad_stock}</div>
        </div>
      `).join('');
    }

    searchResults.style.display = 'block';

    // Agregar event listeners a los resultados
    searchResults.querySelectorAll('.repuesto-search-result-item').forEach(item => {
      if (item.dataset.repuestoId) {
        item.addEventListener('click', () => {
          const repuestoId = item.dataset.repuestoId;
          const repuesto = results.find(r => r.id == repuestoId);
          if (repuesto) {
            selectRepuesto(repuesto, repuestoItem);
          }
        });
      }
    });
  }

  // Función para ocultar resultados de búsqueda de repuestos
  function hideRepuestoSearchResults(repuestoItem) {
    const searchResults = repuestoItem.querySelector(".repuesto-search-results");
    if (searchResults) {
      searchResults.style.display = 'none';
    }
  }

  // Función para seleccionar un repuesto
  function selectRepuesto(repuesto, repuestoItem) {
    console.log("🔧 Repuesto seleccionado:", repuesto);

    // Llenar los campos del repuesto
    const partNumberField = repuestoItem.querySelector(".repuesto-part-number");
    const nombreField = repuestoItem.querySelector(".repuesto-nombre");
    const precioCompraField = repuestoItem.querySelector(".repuesto-precio-compra");
    const precioVentaField = repuestoItem.querySelector(".repuesto-precio-venta");
    const cantidadField = repuestoItem.querySelector(".repuesto-cantidad");

    console.log("📝 Campos encontrados:", {
      partNumberField: !!partNumberField,
      nombreField: !!nombreField,
      precioCompraField: !!precioCompraField,
      precioVentaField: !!precioVentaField,
      cantidadField: !!cantidadField
    });

    if (partNumberField) partNumberField.value = repuesto.part_number;
    if (nombreField) nombreField.value = repuesto.nombre;
    if (precioCompraField) precioCompraField.value = formatChileanCurrency(repuesto.precio_compra);
    if (precioVentaField) precioVentaField.value = formatChileanCurrency(repuesto.precio_venta);
    if (cantidadField) cantidadField.value = 1;

    console.log("✅ Campos llenados:", {
      partNumber: partNumberField?.value,
      nombre: nombreField?.value,
      precioCompra: precioCompraField?.value,
      precioVenta: precioVentaField?.value,
      cantidad: cantidadField?.value
    });

    // Recalcular totales generales
    if (typeof recalculateAllTotals === 'function') {
      recalculateAllTotals();
    }

    hideRepuestoSearchResults(repuestoItem);
  }

  // Función para calcular el total de un repuesto (eliminada - no se necesita campo Total individual)

  // Función para agregar un nuevo repuesto
  function addRepuesto() {
    repuestoIndex++;
    const newRepuestoHTML = `
      <div class="repuesto-item" data-repuesto-index="${repuestoIndex}">
        <div class="repuesto-fields" style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr 0.5fr 1fr; gap: 10px; align-items: end;">
          <div class="field" style="position: relative;">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Part Number</label>
            <input type="text" class="input repuesto-part-number" placeholder="Part number..." autocomplete="off" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
            <div class="repuesto-search-results" style="display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 1000; background: rgba(30, 41, 59, 0.95); border: 1px solid #00eaff; border-radius: 8px; max-height: 200px; overflow-y: auto;"></div>
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Nombre del Repuesto</label>
            <input type="text" class="input repuesto-nombre" readonly style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Precio Compra</label>
            <input type="text" class="input repuesto-precio-compra" readonly style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Precio Venta</label>
            <input type="text" class="input repuesto-precio-venta" readonly style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Cantidad</label>
            <input type="number" class="input repuesto-cantidad" min="1" max="999" value="1" step="1" maxlength="3" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px; width: 60px;">
          </div>
          
          <div class="field">
            <button type="button" class="btn btn-remove-repuesto" style="font-size: 0.8rem; padding: 6px 12px;">Eliminar</button>
          </div>
        </div>
      </div>
    `;
    
    repuestosContainer.insertAdjacentHTML('beforeend', newRepuestoHTML);
    
    // Configurar event listeners para el nuevo repuesto
    const newRepuestoItem = repuestosContainer.lastElementChild;
    setupRepuestoEventListeners(newRepuestoItem);
    
    // Limitar cantidad a máximo 3 dígitos
    const cantidadInput = newRepuestoItem.querySelector('.repuesto-cantidad');
    if (cantidadInput) {
      cantidadInput.addEventListener('input', function() {
        let value = this.value;
        if (value.length > 3) {
          this.value = value.slice(0, 3);
        }
        if (parseInt(this.value) > 999) {
          this.value = '999';
        }
      });
    }
    
    console.log("✅ Nuevo repuesto agregado:", repuestoIndex);
  }

  // Función para eliminar un repuesto
  function removeRepuesto(repuestoItem) {
    repuestoItem.remove();
    console.log("🗑️ Repuesto eliminado");
  }

  // Función para configurar event listeners de un repuesto
  function setupRepuestoEventListeners(repuestoItem) {
    const partNumberInput = repuestoItem.querySelector(".repuesto-part-number");
    const cantidadInput = repuestoItem.querySelector(".repuesto-cantidad");
    const removeBtn = repuestoItem.querySelector(".btn-remove-repuesto");

    // Búsqueda de repuestos
    if (partNumberInput) {
      let searchTimeout = null;
      
      partNumberInput.addEventListener("input", (e) => {
        const partNumber = e.target.value.trim();
        
        if (searchTimeout) {
          clearTimeout(searchTimeout);
        }

        searchTimeout = setTimeout(() => {
          searchRepuestos(partNumber, repuestoItem);
        }, 300);
      });

      // Ocultar resultados al hacer clic fuera
      document.addEventListener("click", (e) => {
        const searchResults = repuestoItem.querySelector(".repuesto-search-results");
        if (!partNumberInput.contains(e.target) && !searchResults.contains(e.target)) {
          hideRepuestoSearchResults(repuestoItem);
        }
      });
    }

    // Recalcular totales cuando cambia la cantidad
    if (cantidadInput) {
      cantidadInput.addEventListener("input", () => {
        if (typeof recalculateAllTotals === 'function') {
          recalculateAllTotals();
        }
      });
    }

    // Botón de eliminar
    if (removeBtn) {
      removeBtn.addEventListener("click", () => {
        removeRepuesto(repuestoItem);
      });
    }
  }

  // Configurar event listeners para repuestos existentes
  if (repuestosContainer) {
    repuestosContainer.querySelectorAll(".repuesto-item").forEach(repuestoItem => {
      setupRepuestoEventListeners(repuestoItem);
    });

    // Botón para agregar repuestos
    if (btnAddRepuesto) {
      btnAddRepuesto.addEventListener("click", addRepuesto);
    }

    console.log("✅ Sistema de repuestos configurado");
  } else {
    console.error("❌ No se encontró el contenedor de repuestos");
  }

  // ===== SISTEMA DE SERVICIOS =====
  console.log("🔧 Iniciando sistema de servicios...");

  let servicioIndex = 0;
  let serviciosContainer = document.getElementById("servicios-container");
  let btnAddServicio = document.querySelector(".btn-add-servicio");

  async function searchServicios(query, servicioItem) {
    console.log("🔍 Buscando servicios:", query);

    if (!endpointServiciosSearch) {
      console.error("❌ No hay endpoint configurado para búsqueda de servicios");
      return;
    }

    if (!query || query.length < 2) {
      hideServicioSearchResults(servicioItem);
      return;
    }

    try {
      const url = new URL(endpointServiciosSearch, window.location.origin);
      url.searchParams.set("q", query);
      console.log("🌐 Llamando a:", url.toString());

      const res = await fetch(url, { 
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });
      console.log("📡 Respuesta recibida:", res.status, res.statusText);

      const data = await res.json();
      console.log("📊 Datos recibidos:", data);

      if (data.ok && data.results) {
        showServicioSearchResults(data.results, servicioItem);
        console.log("✅ Resultados mostrados:", data.results.length);
      } else {
        console.error("❌ Error en respuesta:", data);
        hideServicioSearchResults(servicioItem);
      }
    } catch (e) {
      console.error("❌ Error en búsqueda:", e);
      hideServicioSearchResults(servicioItem);
    }
  }

  function showServicioSearchResults(results, servicioItem) {
    const searchResults = servicioItem.querySelector(".servicio-search-results");
    console.log("🎯 Mostrando resultados de servicios:", {
      searchResults: !!searchResults,
      resultsCount: results.length,
      servicioItem: !!servicioItem,
      searchResultsElement: searchResults
    });
    
    if (!searchResults) {
      console.error("❌ No se encontró el contenedor de resultados");
      return;
    }

    if (results.length === 0) {
      searchResults.innerHTML = '<div class="servicio-search-result-item no-results" style="padding: 12px; color: #e0faff; background: rgba(30, 41, 59, 0.9);">No se encontraron servicios</div>';
      console.log("📝 Mostrando mensaje de no resultados");
    } else {
      searchResults.innerHTML = results.map(servicio => `
        <div class="servicio-search-result-item" data-servicio-id="${servicio.id}" style="padding: 12px; color: #e0faff; background: rgba(30, 41, 59, 0.9); border-bottom: 1px solid #00eaff; cursor: pointer;">
          <div class="servicio-result-nombre" style="font-weight: 600; margin-bottom: 4px;">${servicio.nombre}</div>
          <div class="servicio-result-descripcion" style="font-size: 0.9rem; color: #8caab5;">${servicio.descripcion || ''}</div>
        </div>
      `).join('');
      console.log("📝 HTML generado:", searchResults.innerHTML);
    }

    searchResults.style.display = 'block';
    searchResults.style.visibility = 'visible';
    searchResults.style.opacity = '1';
    console.log("👁️ Resultados mostrados, display:", searchResults.style.display, "visibility:", searchResults.style.visibility);

    // Agregar event listeners a los resultados
    searchResults.querySelectorAll('.servicio-search-result-item').forEach(item => {
      if (item.dataset.servicioId) {
        item.addEventListener('click', () => {
          const servicioId = parseInt(item.dataset.servicioId);
          const servicio = results.find(s => s.id === servicioId);
          if (servicio) {
            selectServicio(servicio, servicioItem);
          }
        });
      }
    });
  }

  function hideServicioSearchResults(servicioItem) {
    const searchResults = servicioItem.querySelector(".servicio-search-results");
    if (searchResults) {
      searchResults.style.display = 'none';
      searchResults.style.visibility = 'hidden';
      searchResults.style.opacity = '0';
      console.log("🙈 Ocultando resultados de servicios");
    }
  }

  // Función para seleccionar un servicio
  function selectServicio(servicio, servicioItem) {
    console.log("🔧 Servicio seleccionado:", servicio);

    // Llenar los campos del servicio
    const nombreField = servicioItem.querySelector(".servicio-nombre");
    const valorField = servicioItem.querySelector(".servicio-valor");

    console.log("📝 Campos encontrados:", {
      nombreField: !!nombreField,
      valorField: !!valorField
    });

    if (nombreField) nombreField.value = servicio.nombre;
    if (valorField) valorField.value = ""; // El usuario debe ingresar el valor

    console.log("✅ Campos llenados:", {
      nombre: nombreField?.value,
      valor: valorField?.value
    });

    // Recalcular totales generales
    if (typeof recalculateAllTotals === 'function') {
      recalculateAllTotals();
    }

    hideServicioSearchResults(servicioItem);
  }

  // Función para calcular el total de un servicio (eliminada - no se necesita campo Total individual)

  function addServicio() {
    console.log("➕ Agregando nuevo servicio...");
    
    servicioIndex++;
    const newServicioItem = document.createElement('div');
    newServicioItem.className = 'servicio-item';
    newServicioItem.setAttribute('data-servicio-index', servicioIndex);
    
    newServicioItem.innerHTML = `
      <div class="servicio-fields">
        <div class="field" style="position: relative;">
          <label class="label">Buscar Servicio</label>
          <input type="text" class="input servicio-search" placeholder="Ingrese nombre del servicio..." autocomplete="off" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important;">
          <div class="servicio-search-results" style="display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 1000; background: rgba(30, 41, 59, 0.95); border: 1px solid #00eaff; border-radius: 8px; max-height: 200px; overflow-y: auto;"></div>
        </div>
        
        <div class="field">
          <label class="label">Nombre del Servicio</label>
          <input type="text" class="input servicio-nombre" readonly style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important;">
        </div>
        
        <div class="field">
          <label class="label">Valor del Servicio</label>
          <input type="text" class="input servicio-valor" placeholder="$0" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important;">
        </div>
        
        
        <div class="field">
          <button type="button" class="btn btn-remove-servicio">Eliminar</button>
        </div>
      </div>
    `;
    
    serviciosContainer.appendChild(newServicioItem);
    setupServicioEventListeners(newServicioItem);
    
    // Mostrar botón de eliminar en el primer servicio si hay más de uno
    if (servicioIndex > 0) {
      document.querySelectorAll('.btn-remove-servicio').forEach(btn => {
        btn.style.display = 'block';
      });
    }
    
    console.log("✅ Servicio agregado con índice:", servicioIndex);
  }

  function removeServicio(servicioItem) {
    console.log("🗑️ Eliminando servicio...");
    servicioItem.remove();
    
    // Ocultar botones de eliminar si solo queda uno
    const remainingServicios = document.querySelectorAll('.servicio-item');
    if (remainingServicios.length <= 1) {
      document.querySelectorAll('.btn-remove-servicio').forEach(btn => {
        btn.style.display = 'none';
      });
    }
    
    console.log("✅ Servicio eliminado");
  }

  function setupServicioEventListeners(servicioItem) {
    const searchInput = servicioItem.querySelector(".servicio-search");
    const valorInput = servicioItem.querySelector(".servicio-valor");
    const removeBtn = servicioItem.querySelector(".btn-remove-servicio");

    // Búsqueda de servicios con debounce
    let searchTimeout;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        searchServicios(e.target.value, servicioItem);
      }, 300);
    });

    // Ocultar resultados al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!servicioItem.contains(e.target)) {
        hideServicioSearchResults(servicioItem);
      }
    });

    // Formatear y recalcular totales cuando cambie el valor
    valorInput.addEventListener("input", () => {
      // Formatear el input en tiempo real
      formatChileanPriceInput(valorInput);
      
      // Recalcular totales generales
      if (typeof recalculateAllTotals === 'function') {
        recalculateAllTotals();
      }
    });

    // Eliminar servicio
    removeBtn.addEventListener("click", () => removeServicio(servicioItem));
  }

  if (serviciosContainer) {
    // Agregar un servicio inicial si no hay ninguno
    if (document.querySelectorAll(".servicio-item").length === 0) {
      console.log("➕ Agregando servicio inicial...");
      addServicio();
    }
    
    document.querySelectorAll(".servicio-item").forEach(servicioItem => {
      setupServicioEventListeners(servicioItem);
    });

    if (btnAddServicio) {
      btnAddServicio.addEventListener("click", addServicio);
    }

    console.log("✅ Sistema de servicios configurado");
  } else {
    console.error("❌ No se encontró el contenedor de servicios");
  }

  // ===== SISTEMA DE OTROS SERVICIOS =====
  const otrosServiciosContainer = document.getElementById("otros-servicios-container");
  const btnAddOtroServicio = document.querySelector(".btn-add-otro-servicio");

  // Función para buscar otros servicios
  function searchOtrosServicios(query, otroServicioItem) {
    if (!query || query.length < 2) {
      hideOtroServicioSearchResults(otroServicioItem);
      return;
    }

    const endpoint = document.body.dataset.endpointOtrosServiciosSearch;
    if (!endpoint) {
      console.error("❌ Endpoint de otros servicios no encontrado");
      return;
    }

    const url = new URL(endpoint, window.location.origin);
    url.searchParams.set("q", query);

    console.log("🔍 Buscando otros servicios:", query);

    fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin"
    })
    .then(response => response.json())
    .then(data => {
      console.log("📋 Resultados otros servicios:", data);
      if (data.ok && data.results) {
        showOtroServicioSearchResults(data.results, otroServicioItem);
      } else {
        hideOtroServicioSearchResults(otroServicioItem);
      }
    })
    .catch(error => {
      console.error("❌ Error buscando otros servicios:", error);
      hideOtroServicioSearchResults(otroServicioItem);
    });
  }

  // Función para mostrar resultados de búsqueda de otros servicios
  function showOtroServicioSearchResults(results, otroServicioItem) {
    const resultsContainer = otroServicioItem.querySelector(".otro-servicio-search-results");
    console.log("🎯 Mostrando resultados de otros servicios:", {
      resultsContainer: !!resultsContainer,
      resultsCount: results.length,
      otroServicioItem: !!otroServicioItem,
      resultsContainerElement: resultsContainer
    });
    
    if (!resultsContainer) {
      console.error("❌ No se encontró el contenedor de resultados de otros servicios");
      return;
    }

    if (results.length === 0) {
      resultsContainer.innerHTML = '<div class="otro-servicio-search-result-item" style="padding: 12px; color: #e0faff; background: rgba(30, 41, 59, 0.9);">No se encontraron otros servicios</div>';
      console.log("📝 Mostrando mensaje de no resultados para otros servicios");
    } else {
      resultsContainer.innerHTML = results.map(servicio => `
        <div class="otro-servicio-search-result-item" data-servicio-id="${servicio.id}" style="padding: 12px; color: #e0faff; background: rgba(30, 41, 59, 0.9); border-bottom: 1px solid #00eaff; cursor: pointer;">
          <div class="otro-servicio-result-nombre" style="font-weight: 600; margin-bottom: 4px;">${servicio.nombre}</div>
          <div class="otro-servicio-result-descripcion" style="font-size: 0.9rem; color: #8caab5;">${servicio.descripcion || ''}</div>
        </div>
      `).join('');
      console.log("📝 HTML generado para otros servicios:", resultsContainer.innerHTML);
    }

    resultsContainer.style.display = 'block';
    resultsContainer.style.visibility = 'visible';
    resultsContainer.style.opacity = '1';
    console.log("👁️ Resultados de otros servicios mostrados, display:", resultsContainer.style.display, "visibility:", resultsContainer.style.visibility);

    // Agregar event listeners a los resultados
    resultsContainer.querySelectorAll('.otro-servicio-search-result-item').forEach(item => {
      item.addEventListener('click', () => {
        const servicioId = item.dataset.servicioId;
        const servicio = results.find(s => s.id == servicioId);
        if (servicio) {
          selectOtroServicio(servicio, otroServicioItem);
        }
      });
    });
  }

  // Función para ocultar resultados de búsqueda de otros servicios
  function hideOtroServicioSearchResults(otroServicioItem) {
    const resultsContainer = otroServicioItem.querySelector(".otro-servicio-search-results");
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
      resultsContainer.style.visibility = 'hidden';
      resultsContainer.style.opacity = '0';
      console.log("🙈 Ocultando resultados de otros servicios");
    }
  }

  // Función para seleccionar un otro servicio
  function selectOtroServicio(servicio, otroServicioItem) {
    const nombreInput = otroServicioItem.querySelector(".otro-servicio-nombre");
    const searchInput = otroServicioItem.querySelector(".otro-servicio-search");
    
    if (nombreInput) {
      nombreInput.value = servicio.nombre;
    }
    
    if (searchInput) {
      searchInput.value = servicio.nombre;
    }

    hideOtroServicioSearchResults(otroServicioItem);
    // Recalcular totales generales
    if (typeof recalculateAllTotals === 'function') {
      recalculateAllTotals();
    }
    
    console.log("✅ Otro servicio seleccionado:", servicio.nombre);
  }

  // Función para calcular total de otro servicio (eliminada - no se necesita campo Total individual)

  // Función para agregar un nuevo otro servicio
  function addOtroServicio() {
    const container = otrosServiciosContainer;
    if (!container) return;

    const existingItems = document.querySelectorAll('.otro-servicio-item');
    const nextIndex = existingItems.length;

    const nuevoOtroServicioHTML = `
      <div class="otro-servicio-item" data-otro-servicio-index="${nextIndex}">
        <div class="otro-servicio-fields" style="display: grid; grid-template-columns: 2fr 2fr 1fr 1fr auto; gap: 10px; align-items: end;">
          <div class="field" style="position: relative;">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Buscar Otro Servicio</label>
            <input type="text" class="input otro-servicio-search" placeholder="Buscar servicio..." autocomplete="off" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
            <div class="otro-servicio-search-results" style="display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 1000; background: rgba(30, 41, 59, 0.95); border: 1px solid #00eaff; border-radius: 8px; max-height: 200px; overflow-y: auto;"></div>
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Nombre del Servicio</label>
            <input type="text" class="input otro-servicio-nombre" readonly style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
          </div>
          
          <div class="field">
            <label class="label" style="font-size: 0.8rem; margin-bottom: 4px;">Valor</label>
            <input type="text" class="input otro-servicio-valor" placeholder="$0" style="background: rgba(30, 41, 59, 0.85) !important; color: #e0faff !important; border: 1px solid #00eaff !important; font-size: 0.9rem; padding: 6px 8px;">
          </div>
          
          
          <div class="field">
            <button type="button" class="btn btn-remove-otro-servicio" style="font-size: 0.8rem; padding: 6px 12px;">
              Eliminar
            </button>
          </div>
        </div>
      </div>
    `;

    container.insertAdjacentHTML('beforeend', nuevoOtroServicioHTML);

    // Mostrar botones de eliminar si hay más de uno
    document.querySelectorAll('.btn-remove-otro-servicio').forEach(btn => {
      btn.style.display = 'block';
    });

    // Configurar event listeners para el nuevo otro servicio
    const newOtroServicioItem = document.querySelector(`[data-otro-servicio-index="${nextIndex}"]`);
    setupOtroServicioEventListeners(newOtroServicioItem);
    
    console.log("✅ Nuevo otro servicio agregado:", nextIndex);
  }

  // Función para eliminar un otro servicio
  function removeOtroServicio(otroServicioItem) {
    otroServicioItem.remove();
    
    // Ocultar botones de eliminar si solo queda uno
    const remainingOtrosServicios = document.querySelectorAll('.otro-servicio-item');
    if (remainingOtrosServicios.length <= 1) {
      document.querySelectorAll('.btn-remove-otro-servicio').forEach(btn => {
        btn.style.display = 'none';
      });
    }
    
    console.log("🗑️ Otro servicio eliminado");
  }

  function setupOtroServicioEventListeners(otroServicioItem) {
    const searchInput = otroServicioItem.querySelector(".otro-servicio-search");
    const valorInput = otroServicioItem.querySelector(".otro-servicio-valor");
    const removeBtn = otroServicioItem.querySelector(".btn-remove-otro-servicio");

    // Búsqueda de otros servicios con debounce
    let searchTimeout;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        searchOtrosServicios(e.target.value, otroServicioItem);
      }, 300);
    });

    // Ocultar resultados al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!otroServicioItem.contains(e.target)) {
        hideOtroServicioSearchResults(otroServicioItem);
      }
    });

    // Formatear y recalcular totales cuando cambie el valor
    valorInput.addEventListener("input", () => {
      // Formatear el input en tiempo real
      formatChileanPriceInput(valorInput);
      
      // Recalcular totales generales
      if (typeof recalculateAllTotals === 'function') {
        recalculateAllTotals();
      }
    });

    // Eliminar otro servicio
    removeBtn.addEventListener("click", () => removeOtroServicio(otroServicioItem));
  }

  if (otrosServiciosContainer) {
    // Agregar un otro servicio inicial si no hay ninguno
    if (document.querySelectorAll(".otro-servicio-item").length === 0) {
      console.log("➕ Agregando otro servicio inicial...");
      addOtroServicio();
    }
    
    document.querySelectorAll(".otro-servicio-item").forEach(otroServicioItem => {
      setupOtroServicioEventListeners(otroServicioItem);
    });

    if (btnAddOtroServicio) {
      btnAddOtroServicio.addEventListener("click", addOtroServicio);
    }

    console.log("✅ Sistema de otros servicios configurado");
  } else {
    console.error("❌ No se encontró el contenedor de otros servicios");
  }

  // ===== SISTEMA DE TOTALES =====
  console.log("💰 Iniciando sistema de totales...");

  // Elementos de totales
  const totalRepuestos = document.getElementById("total-repuestos");
  const totalServicios = document.getElementById("total-servicios");
  const totalOtrosServicios = document.getElementById("total-otros-servicios");
  const subtotal = document.getElementById("subtotal");
  const incluirImpuestos = document.getElementById("incluir-impuestos");
  const montoImpuestos = document.getElementById("monto-impuestos");
  const granTotal = document.getElementById("gran-total");

  // Configuración de impuestos por país
  const taxRate = window.location.pathname.includes('/cl/') ? 0.19 : 0.0825; // 19% Chile, 8.25% USA

  // Función para calcular total de repuestos
  function calculateTotalRepuestos() {
    let total = 0;
    document.querySelectorAll('.repuesto-item').forEach(item => {
      const precioInput = item.querySelector('.repuesto-precio-venta');
      const cantidadInput = item.querySelector('.repuesto-cantidad');
      
      if (precioInput && cantidadInput) {
        const precio = parseFloat(precioInput.value.replace(/[^\d]/g, '') || 0);
        const cantidad = parseInt(cantidadInput.value || 1);
        total += precio * cantidad;
      }
    });
    
    if (totalRepuestos) {
      totalRepuestos.value = formatChileanCurrency(total);
    }
    
    console.log("🔧 Total repuestos:", total);
    return total;
  }

  // Función para calcular total de servicios
  function calculateTotalServicios() {
    let total = 0;
    document.querySelectorAll('.servicio-valor').forEach(input => {
      const value = parseFloat(input.value.replace(/[^\d]/g, '') || 0);
      total += value;
    });
    
    if (totalServicios) {
      totalServicios.value = formatChileanCurrency(total);
    }
    
    console.log("🔧 Total servicios:", total);
    return total;
  }

  // Función para calcular total de otros servicios
  function calculateTotalOtrosServicios() {
    let total = 0;
    document.querySelectorAll('.otro-servicio-valor').forEach(input => {
      const value = parseFloat(input.value.replace(/[^\d]/g, '') || 0);
      total += value;
    });
    
    if (totalOtrosServicios) {
      totalOtrosServicios.value = formatChileanCurrency(total);
    }
    
    console.log("🔧 Total otros servicios:", total);
    return total;
  }

  // Función para calcular subtotal
  function calculateSubtotal() {
    const totalRep = calculateTotalRepuestos();
    const totalServ = calculateTotalServicios();
    const totalOtros = calculateTotalOtrosServicios();
    
    const subtotalValue = totalRep + totalServ + totalOtros;
    
    if (subtotal) {
      subtotal.value = formatChileanCurrency(subtotalValue);
    }
    
    console.log("💰 Subtotal:", subtotalValue);
    return subtotalValue;
  }

  // Función para calcular impuestos
  function calculateTaxes() {
    const subtotalValue = parseFloat(subtotal.value.replace(/[^\d]/g, '') || 0);
    const taxAmount = subtotalValue * taxRate;
    
    if (montoImpuestos) {
      montoImpuestos.value = formatChileanCurrency(taxAmount);
    }
    
    console.log("💰 Impuestos:", taxAmount, "Tasa:", taxRate);
    return taxAmount;
  }

  // Función para calcular gran total
  function calculateGrandTotal() {
    const subtotalValue = parseFloat(subtotal.value.replace(/[^\d]/g, '') || 0);
    const taxAmount = incluirImpuestos && incluirImpuestos.checked ? calculateTaxes() : 0;
    const grandTotalValue = subtotalValue + taxAmount;
    
    if (granTotal) {
      granTotal.value = formatChileanCurrency(grandTotalValue);
    }
    
    console.log("💰 Gran total:", grandTotalValue);
    return grandTotalValue;
  }

  // Función para recalcular todos los totales
  function recalculateAllTotals() {
    console.log("🔄 Recalculando todos los totales...");
    calculateSubtotal();
    calculateGrandTotal();
  }

  // Event listeners para el checkbox de impuestos
  if (incluirImpuestos) {
    incluirImpuestos.addEventListener('change', () => {
      console.log("📋 Checkbox impuestos cambiado:", incluirImpuestos.checked);
      calculateGrandTotal();
    });
  }

  // Función para configurar event listeners de totales en un elemento
  function setupTotalEventListeners(element) {
    // Buscar todos los inputs de total dentro del elemento
    const totalInputs = element.querySelectorAll('input[class*="total"]');
    
    totalInputs.forEach(input => {
      input.addEventListener('input', () => {
        console.log("📊 Input de total cambiado:", input.className, input.value);
        recalculateAllTotals();
      });
    });
  }

  // Configurar event listeners para elementos existentes
  document.querySelectorAll('.repuesto-item, .servicio-item, .otro-servicio-item').forEach(item => {
    setupTotalEventListeners(item);
  });

  // Función para observar cambios en el DOM (para elementos agregados dinámicamente)
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) { // Element node
          if (node.classList && (node.classList.contains('repuesto-item') || 
                                node.classList.contains('servicio-item') || 
                                node.classList.contains('otro-servicio-item'))) {
            console.log("🆕 Nuevo elemento detectado, configurando totales:", node.className);
            setupTotalEventListeners(node);
            recalculateAllTotals();
          }
        }
      });
    });
  });

  // Observar cambios en los contenedores
  const containers = ['#repuestos-container', '#servicios-container', '#otros-servicios-container'];
  containers.forEach(containerId => {
    const container = document.querySelector(containerId);
    if (container) {
      observer.observe(container, { childList: true, subtree: true });
    }
  });

  // Cálculo inicial
  recalculateAllTotals();

  console.log("✅ Sistema de totales configurado");

  // ========================================
  // FILTRADO DE VEHÍCULOS POR CLIENTE
  // ========================================
  
  function filterVehiclesByClient() {
    console.log("🚗 Inicializando filtrado de vehículos por cliente");
    
    // Buscar elementos por nombre en lugar de ID
    const clienteSelect = document.querySelector("select[name='cliente']");
    const vehiculoSelect = document.querySelector("select[name='vehiculo']");
    
    console.log("🔍 Elementos encontrados:", {
      clienteSelect: clienteSelect,
      vehiculoSelect: vehiculoSelect,
      clienteSelectExists: !!clienteSelect,
      vehiculoSelectExists: !!vehiculoSelect
    });
    
    if (!clienteSelect || !vehiculoSelect) {
      console.log("⚠️ No se encontraron elementos cliente o vehículo");
      console.log("🔍 Cliente select:", clienteSelect);
      console.log("🔍 Vehículo select:", vehiculoSelect);
      return;
    }
    
    // Agregar event listener para cambio de cliente
    clienteSelect.addEventListener('change', function() {
      const clienteId = this.value;
      console.log('🔄 Cliente seleccionado:', clienteId);
      
      if (!clienteId) {
        // Si no hay cliente seleccionado, mostrar todos los vehículos
        loadAllVehicles();
        return;
      }
      
      // Filtrar vehículos por cliente
      loadVehiclesByClient(clienteId);
    });
    
    // Cargar vehículos iniciales si ya hay un cliente seleccionado
    if (clienteSelect && clienteSelect.value) {
      loadVehiclesByClient(clienteSelect.value);
    }
  }

  function loadVehiclesByClient(clienteId) {
    const vehiculoSelect = document.querySelector("select[name='vehiculo']");
    if (!vehiculoSelect) return;
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/vehiculos-por-cliente/?cliente=${clienteId}`;
    
    console.log('📡 Cargando vehículos para cliente:', clienteId);
    
    // Mostrar loading
    vehiculoSelect.innerHTML = '<option value="">Cargando vehículos...</option>';
    
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('📊 Vehículos recibidos:', data);
        vehiculoSelect.innerHTML = '<option value="">Seleccione un vehículo...</option>';
        
        if (data.vehiculos && data.vehiculos.length > 0) {
          data.vehiculos.forEach(vehiculo => {
            const option = document.createElement('option');
            option.value = vehiculo.id;
            option.textContent = `${vehiculo.marca} ${vehiculo.modelo} - ${vehiculo.patente || vehiculo.placa}`;
            vehiculoSelect.appendChild(option);
          });
          console.log(`✅ Cargados ${data.vehiculos.length} vehículos`);
        } else {
          vehiculoSelect.innerHTML = '<option value="">No hay vehículos para este cliente</option>';
          console.log('❌ No hay vehículos para este cliente');
        }
      })
      .catch(error => {
        console.error('💥 Error cargando vehículos:', error);
        vehiculoSelect.innerHTML = '<option value="">Error cargando vehículos</option>';
      });
  }

  function loadAllVehicles() {
    const vehiculoSelect = document.querySelector("select[name='vehiculo']");
    if (!vehiculoSelect) return;
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/todos-vehiculos/`;
    
    console.log('📡 Cargando todos los vehículos');
    
    // Mostrar loading
    vehiculoSelect.innerHTML = '<option value="">Cargando vehículos...</option>';
    
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('📊 Todos los vehículos recibidos:', data);
        vehiculoSelect.innerHTML = '<option value="">Seleccione un vehículo...</option>';
        
        if (data.vehiculos && data.vehiculos.length > 0) {
          data.vehiculos.forEach(vehiculo => {
            const option = document.createElement('option');
            option.value = vehiculo.id;
            option.textContent = `${vehiculo.marca} ${vehiculo.modelo} - ${vehiculo.patente || vehiculo.placa}`;
            vehiculoSelect.appendChild(option);
          });
          console.log(`✅ Cargados ${data.vehiculos.length} vehículos`);
        } else {
          vehiculoSelect.innerHTML = '<option value="">No hay vehículos disponibles</option>';
          console.log('❌ No hay vehículos disponibles');
        }
      })
      .catch(error => {
        console.error('💥 Error cargando todos los vehículos:', error);
        vehiculoSelect.innerHTML = '<option value="">Error cargando vehículos</option>';
      });
  }

  // Inicializar filtrado de vehículos
  filterVehiclesByClient();

  // Event listeners para recálculo de totales y formato de precios
  document.addEventListener('input', function(e) {
    // Formatear inputs de precios en tiempo real para Chile
    if (e.target.matches('input[name*="precio"], input[name*="valor"], input[name*="costo"]')) {
      formatChileanPriceInput(e.target);
    }
    
    // Recalcular totales cuando cambien precios o cantidades
    if (e.target.matches('input[name*="precio"], input[name*="valor"], input[name*="cantidad"], input[name*="costo"]')) {
      setTimeout(recalcTotalsChilean, 100); // Pequeño delay para que se actualice el valor
    }
  });

  // Recalcular totales inicial
  setTimeout(recalcTotalsChilean, 500);

  // Event listeners para los botones de tipo de documento
  const tipoButtons = document.querySelectorAll('.btn-type, [data-tipo]');
  const tipoInput = document.getElementById('tipo') || document.querySelector('input[name="tipo"]');
  
  console.log('🔘 Botones de tipo encontrados:', tipoButtons.length);
  console.log('📝 Input tipo encontrado:', !!tipoInput);
  
  tipoButtons.forEach(button => {
    button.addEventListener('click', function() {
      console.log('🖱️ Botón de tipo clickeado:', this.dataset.tipo);
      
      // Remover clase active de todos los botones
      tipoButtons.forEach(btn => btn.classList.remove('active'));
      // Agregar clase active al botón clickeado
      this.classList.add('active');
      
      // Actualizar el valor del input hidden
      const tipo = this.dataset.tipo;
      if (tipoInput) {
        tipoInput.value = tipo;
        console.log('📝 Tipo actualizado a:', tipo);
      }
      
      // Actualizar el número de documento
      updateDocumentNumber();
    });
  });

  // Actualizar número de documento inicial
  setTimeout(updateDocumentNumber, 100);

  console.log("✅ Sistema de formulario mejorado inicializado");
}); // End of DOMContentLoaded
