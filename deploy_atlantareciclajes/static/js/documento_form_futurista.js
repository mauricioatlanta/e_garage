console.log('🚀 DOC-JS-ATTACHED (from documento_form_futurista.js)');
console.log('🔥 VERSIÓN ACTUALIZADA - ' + new Date().toLocaleTimeString());
console.log('✅ JAVASCRIPT FUTURISTA CARGADO CORRECTAMENTE');

// CONFIGURACIÓN GLOBAL
const colors = {
  FAC: 'from-slate-900 to-slate-800',
  COT: 'from-indigo-950 to-indigo-800',
  ORD: 'from-emerald-950 to-emerald-800'
};

const country = window.country || 'CL';
let repuestoCounter = 0;
let servicioCounter = 0;
let otroServicioCounter = 0;
let currentPaletteTab = 'repuestos';

// UTILIDADES
function formatCurrency(n) {
  if (country === 'US') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(n || 0);
  } else {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(n || 0);
  }
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Animación de entrada
  setTimeout(() => toast.style.transform = 'translateX(0)', 10);

  // Remover después de 3 segundos
  setTimeout(() => {
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function applyBg(tipo) {
  const body = document.body;
  const gradientClass = colors[tipo] || colors['COT'];
  body.className = `min-h-screen bg-gradient-to-b ${gradientClass} text-white touch-lg`;
  console.log(`🎨 Fondo cambiado a: ${tipo}`);
}

// INICIALIZACIÓN DE TIPO DE DOCUMENTO
function initTipoDocumento() {
  const hidden = document.getElementById('tipo');
  if (!hidden) {
    console.warn('⚠️ Campo hidden "tipo" no encontrado');
    return;
  }

  const currentTipo = hidden.value || 'COT';
  applyBg(currentTipo);

  // Activar botón correspondiente
  document.querySelectorAll('#doc-type-switch .btn-type').forEach(b => {
    if (b.dataset.tipo === currentTipo) {
      b.classList.add('active');
    }

    b.addEventListener('click', (e) => {
      e.preventDefault();
      const tipo = b.dataset.tipo;

      // Actualizar hidden input
      hidden.value = tipo;

      // Actualizar clase active
      document.querySelectorAll('#doc-type-switch .btn-type').forEach(x => x.classList.remove('active'));
      b.classList.add('active');

      // Cambiar fondo
      applyBg(tipo);

      // Efecto visual
      b.style.transform = 'scale(0.95)';
      setTimeout(() => b.style.transform = 'scale(1)', 150);

      showToast(`Tipo cambiado a: ${tipo}`, 'info');
    });
  });
}

// BÚSQUEDA DE CLIENTES
async function searchClientes(q) {
  console.log('🔍 BUSCANDO CLIENTES:', q);
  try {
    const url = `/cl/documentos/autocomplete/cliente/?q=${encodeURIComponent(q)}`;
    console.log('📡 URL de búsqueda:', url);
    const response = await fetch(url);
    console.log('📥 Respuesta de API:', response.status, response.statusText);
    if (!response.ok) {
      console.error('❌ Error HTTP:', response.status, response.statusText);
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    console.log('✅ DATOS RECIBIDOS:', data);
    console.log('✅ NUMERO DE RESULTADOS:', data.results ? data.results.length : 0);
    return data;
  } catch (e) {
    console.error('❌ ERROR AL BUSCAR CLIENTES:', e);
    showToast('Error al buscar clientes', 'error');
    return { results: [] };
  }
}

function initClienteSearch() {
  console.log('🚀 INICIALIZANDO BÚSQUEDA DE CLIENTES...');
  const clienteSearch = document.getElementById('cliente-search');
  const clienteSelect = document.getElementById('cliente');
  const vehiculoSelect = document.getElementById('vehiculo');

  console.log('🔎 ELEMENTOS ENCONTRADOS:', {
    clienteSearch: !!clienteSearch,
    clienteSelect: !!clienteSelect,
    vehiculoSelect: !!vehiculoSelect
  });

  if (!clienteSearch || !clienteSelect || !vehiculoSelect) {
    console.error('❌ ELEMENTOS DE BÚSQUEDA DE CLIENTE NO ENCONTRADOS');
    console.log('🔍 DOM Elements disponibles:');
    console.log('   - cliente-search:', document.getElementById('cliente-search'));
    console.log('   - cliente:', document.getElementById('cliente'));
    console.log('   - vehiculo:', document.getElementById('vehiculo'));
    return;
  }

  console.log('✅ TODOS LOS ELEMENTOS ENCONTRADOS, CONFIGURANDO EVENT LISTENERS...');
  let searchTimeout;

  clienteSearch.addEventListener('input', () => {
    console.log('⌨️ CLIENTE SEARCH INPUT DETECTADO');
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      const q = clienteSearch.value.trim();
      console.log('⏰ EJECUTANDO BUSQUEDA DESPUÉS DE TIMEOUT:', q);
      if (q.length < 2) {
        console.log('🔤 Query muy corto, reseteando select');
        clienteSelect.innerHTML = '<option value="">Seleccione un cliente...</option>';
        return;
      }

      console.log('🔄 INICIANDO BUSQUEDA DE CLIENTES...');
      clienteSelect.classList.add('loading');
      const data = await searchClientes(q);
      clienteSelect.classList.remove('loading');

      console.log('🏗️ CONSTRUYENDO OPTIONS CON:', data.results);
      clienteSelect.innerHTML = '<option value="">Seleccione...</option>' +
        data.results.map(c =>
          `<option value="${c.id}">${c.nombre} — ${c.identificador}</option>`
        ).join('');

      if (data.results.length > 0) {
        console.log('🎉 MOSTRANDO TOAST CON RESULTADOS');
        showToast(`${data.results.length} cliente(s) encontrado(s)`, 'info');
      } else {
        console.log('😔 NO HAY RESULTADOS');
      }
    }, 250);
  });

  // CARGAR VEHÍCULOS AL SELECCIONAR CLIENTE
  clienteSelect.addEventListener('change', async () => {
    const id = clienteSelect.value;
    vehiculoSelect.innerHTML = '<option value="">Cargando...</option>';

    if (!id) {
      vehiculoSelect.innerHTML = '<option value="">Seleccione un cliente primero…</option>';
      return;
    }

    try {
      vehiculoSelect.classList.add('loading');
      const response = await fetch(`/api/v1/vehiculos/${id}/`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      vehiculoSelect.classList.remove('loading');

      vehiculoSelect.innerHTML = data.length ?
        '<option value="">Seleccione vehículo...</option>' +
        data.map(v =>
          `<option value="${v.id}">${v.patente || v.vin} — ${v.marca} ${v.modelo}</option>`
        ).join('') :
        '<option value="">(Sin vehículos)</option>';

      if (data.length > 0) {
        showToast(`${data.length} vehículo(s) encontrado(s)`, 'info');
      }
    } catch (e) {
      console.error('Error al cargar vehículos:', e);
      vehiculoSelect.classList.remove('loading');
      showToast('Error al cargar vehículos', 'error');
      vehiculoSelect.innerHTML = '<option value="">(Error al cargar)</option>';
    }
  });
}

// CREACIÓN DE LÍNEAS DE REPUESTOS
function createRepuestoLine() {
  repuestoCounter++;
  const line = document.createElement('div');
  line.className = 'repuesto-line item-line grid grid-responsive gap-3 items-center slide-in';
  line.innerHTML = `
    <input class="col-span-2 futurista-input part-code"
           placeholder="Código" name="repuestos[${repuestoCounter}][codigo]">
    <input class="col-span-3 futurista-input part-name"
           placeholder="Nombre" readonly name="repuestos[${repuestoCounter}][nombre]">
    <input class="col-span-2 futurista-input part-cost hidden-cost"
           placeholder="Costo (oculto)" name="repuestos[${repuestoCounter}][precio_compra]">
    <input class="col-span-2 futurista-input part-price"
           placeholder="Precio venta" name="repuestos[${repuestoCounter}][precio_venta]" type="number" step="0.01">
    <input class="col-span-1 futurista-input part-qty"
           placeholder="Cant." value="1" name="repuestos[${repuestoCounter}][cantidad]" type="number" step="0.01">
    <div class="col-span-1 text-right font-semibold subtotal text-cyan-400">$0</div>
    <label class="col-span-1 flex items-center gap-2 text-sm">
      <input type="checkbox" class="adhoc-toggle" name="repuestos[${repuestoCounter}][ad_hoc]">
      <span class="text-cyan-200">Ad-hoc</span>
    </label>
    <button type="button" class="col-span-1 text-red-400 hover:text-red-300 transition p-2 rounded" onclick="removeRepuestoLine(this)" title="Eliminar línea">
      🗑️
    </button>
  `;
  return line;
}

function createServicioLine() {
  servicioCounter++;
  const line = document.createElement('div');
  line.className = 'serv-line item-line grid grid-responsive gap-3 items-center slide-in';
  line.innerHTML = `
    <input class="col-span-5 futurista-input serv-search"
           placeholder="Buscar servicio (nombre, categoría)">
    <input class="col-span-3 futurista-input serv-name"
           placeholder="Nombre" name="servicios[${servicioCounter}][nombre]">
    <input class="col-span-3 futurista-input serv-price"
           placeholder="Valor servicio" name="servicios[${servicioCounter}][precio]" type="number" step="0.01">
    <div class="col-span-1 text-right font-semibold serv-subtotal text-cyan-400">$0</div>
    <button type="button" class="col-span-1 text-red-400 hover:text-red-300 transition p-2 rounded" onclick="removeServicioLine(this)" title="Eliminar línea">
      🗑️
    </button>
  `;
  return line;
}

function createOtroServicioLine() {
  otroServicioCounter++;
  const line = document.createElement('div');
  line.className = 'otro-serv-line item-line grid grid-responsive gap-3 items-center slide-in';
  line.innerHTML = `
    <input class="col-span-3 futurista-input prov-name"
           placeholder="Proveedor externo" name="otros_servicios[${otroServicioCounter}][proveedor]">
    <input class="col-span-4 futurista-input otro-serv-search"
           placeholder="Buscar/Nombre servicio" name="otros_servicios[${otroServicioCounter}][nombre]">
    <input class="col-span-2 futurista-input costo-interno"
           placeholder="Costo interno" name="otros_servicios[${otroServicioCounter}][costo_interno]" type="number" step="0.01">
    <input class="col-span-2 futurista-input precio-cliente"
           placeholder="Precio cliente" name="otros_servicios[${otroServicioCounter}][precio_cliente]" type="number" step="0.01">
    <div class="col-span-1 text-right font-semibold ganancia text-cyan-400">$0</div>
    <button type="button" class="col-span-1 text-red-400 hover:text-red-300 transition p-2 rounded" onclick="removeOtroServicioLine(this)" title="Eliminar línea">
      🗑️
    </button>
  `;
  return line;
}

// FUNCIONES DE ELIMINACIÓN
function removeRepuestoLine(btn) {
  const line = btn.closest('.repuesto-line');
  line.style.opacity = '0';
  line.style.transform = 'scale(0.9)';
  setTimeout(() => {
    line.remove();
    recalcTotals();
  }, 200);
}

function removeServicioLine(btn) {
  const line = btn.closest('.serv-line');
  line.style.opacity = '0';
  line.style.transform = 'scale(0.9)';
  setTimeout(() => {
    line.remove();
    recalcTotals();
  }, 200);
}

function removeOtroServicioLine(btn) {
  const line = btn.closest('.otro-serv-line');
  line.style.opacity = '0';
  line.style.transform = 'scale(0.9)';
  setTimeout(() => {
    line.remove();
    recalcTotals();
  }, 200);
}

// EVENTOS DE AGREGAR LÍNEAS
function initAddButtons() {
  const addRepuestoBtn = document.getElementById('add-repuesto');
  const addServBtn = document.getElementById('add-serv');
  const addOtroServBtn = document.getElementById('add-otro-serv');

  if (addRepuestoBtn) {
    addRepuestoBtn.addEventListener('click', () => {
      const container = document.getElementById('repuestos-container');
      if (container) {
        const line = createRepuestoLine();
        container.appendChild(line);
        line.querySelector('.part-code').focus();
        showToast('Línea de repuesto agregada', 'success');
      }
    });
  }

  if (addServBtn) {
    addServBtn.addEventListener('click', () => {
      const container = document.getElementById('servicios-container');
      if (container) {
        const line = createServicioLine();
        container.appendChild(line);
        line.querySelector('.serv-search').focus();
        showToast('Línea de servicio agregada', 'success');
      }
    });
  }

  if (addOtroServBtn) {
    addOtroServBtn.addEventListener('click', () => {
      const container = document.getElementById('otros-servicios-container');
      if (container) {
        const line = createOtroServicioLine();
        container.appendChild(line);
        line.querySelector('.prov-name').focus();
        showToast('Línea de otro servicio agregada', 'success');
      }
    });
  }
}

// AUTOCOMPLETE DE REPUESTOS
async function searchRepuesto(code) {
  try {
    const response = await fetch(`/api/v1/repuestos/by-code?code=${encodeURIComponent(code)}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error al buscar repuesto:', error);
    return null;
  }
}

// RECÁLCULO DE TOTALES
function recalcTotals() {
  let sumRep = 0, sumServ = 0, sumOtros = 0;

  // Sumar repuestos
  document.querySelectorAll('.repuesto-line').forEach(l => {
    const price = parseFloat(l.querySelector('.part-price').value || 0);
    const qty = parseFloat(l.querySelector('.part-qty').value || 0);
    const subtotal = price * qty;
    sumRep += subtotal;
    l.querySelector('.subtotal').textContent = formatCurrency(subtotal);
  });

  // Sumar servicios
  document.querySelectorAll('.serv-line').forEach(l => {
    const price = parseFloat(l.querySelector('.serv-price').value || 0);
    sumServ += price;
    l.querySelector('.serv-subtotal').textContent = formatCurrency(price);
  });

  // Sumar otros servicios
  document.querySelectorAll('.otro-serv-line').forEach(l => {
    const ci = parseFloat(l.querySelector('.costo-interno').value || 0);
    const pc = parseFloat(l.querySelector('.precio-cliente').value || 0);
    sumOtros += pc;
    l.querySelector('.ganancia').textContent = formatCurrency(pc - ci);
  });

  const rateInput = document.getElementById('tax-rate');
  const includeInput = document.getElementById('include-tax');

  let taxAmt = 0;
  if (rateInput && includeInput) {
    const rate = parseFloat(rateInput.value || 0) / 100;
    const include = includeInput.checked;

    // CHILE: impuesto solo sobre repuestos. USA: ajustar según configuración
    const taxBase = country === 'CL' ? sumRep : (sumRep + sumServ + sumOtros);
    taxAmt = include ? taxBase * rate : 0;
  }

  const total = sumRep + sumServ + sumOtros + taxAmt;

  // Actualizar displays
  const elements = {
    'sum-rep': sumRep,
    'sum-serv': sumServ,
    'sum-otros': sumOtros,
    'tax-amt': taxAmt,
    'grand-total': total
  };

  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = formatCurrency(value);
    }
  });

  // Efecto holograma suave
  const totalElement = document.getElementById('grand-total');
  if (totalElement) {
    totalElement.parentElement.classList.add('glow-effect');
    setTimeout(() => totalElement.parentElement.classList.remove('glow-effect'), 300);
  }
}

// EVENT LISTENERS PRINCIPALES
function initEventListeners() {
  // Input events para cálculos
  document.addEventListener('input', async (e) => {
    // Autocomplete de repuestos
    if (e.target.classList.contains('part-code')) {
      const code = e.target.value.trim();
      if (code.length >= 2) {
        const line = e.target.closest('.repuesto-line');
        const repuesto = await searchRepuesto(code);

        if (repuesto) {
          line.querySelector('.part-name').value = repuesto.nombre || '';
          line.querySelector('.part-cost').value = repuesto.precio_compra || '';
          line.querySelector('.part-price').value = repuesto.precio_venta_sugerido || '';

          // Mostrar stock si no es ad-hoc
          const adhocToggle = line.querySelector('.adhoc-toggle');
          if (!adhocToggle.checked && repuesto.stock !== undefined) {
            if (repuesto.stock <= 0) {
              showToast(`⚠️ Sin stock para ${repuesto.nombre}. Marque como ad-hoc.`, 'error');
            } else {
              showToast(`📦 Stock disponible: ${repuesto.stock}`, 'info');
            }
          }

          recalcTotals();
        }
      }
    }

    // Cálculos en tiempo real
    if (['part-price', 'part-qty', 'serv-price', 'costo-interno', 'precio-cliente'].some(c => e.target.classList.contains(c))) {
      recalcTotals();
    }
  });

  // Change events
  document.addEventListener('change', (e) => {
    if (e.target.id === 'include-tax' || e.target.id === 'tax-rate') {
      recalcTotals();
    }
  });
}

// ATAJOS DE TECLADO
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Alt+R: Agregar repuesto
    if (e.altKey && e.key === 'r') {
      e.preventDefault();
      const btn = document.getElementById('add-repuesto');
      if (btn) btn.click();
      return;
    }

    // Alt+S: Agregar servicio
    if (e.altKey && e.key === 's') {
      e.preventDefault();
      const btn = document.getElementById('add-serv');
      if (btn) btn.click();
      return;
    }

    // Ctrl+K: Abrir command palette
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      openCommandPalette();
      return;
    }

    // Escape: Cerrar command palette
    if (e.key === 'Escape') {
      closeCommandPalette();
      return;
    }
  });
}

// COMMAND PALETTE
function openCommandPalette() {
  const palette = document.getElementById('command-palette');
  if (palette) {
    palette.classList.add('show');
    const search = document.getElementById('palette-search');
    if (search) search.focus();
  }
}

function closeCommandPalette() {
  const palette = document.getElementById('command-palette');
  if (palette) {
    palette.classList.remove('show');
    const search = document.getElementById('palette-search');
    if (search) search.value = '';
    const results = document.getElementById('palette-results');
    if (results) results.innerHTML = '';
  }
}

// INICIALIZACIÓN PRINCIPAL
function initDocumentoForm() {
  console.log('🔧 Inicializando formulario de documento...');

  // Inicializar componentes
  initTipoDocumento();
  initClienteSearch();
  initAddButtons();
  initEventListeners();
  initKeyboardShortcuts();

  // Agregar primera línea de repuesto si el contenedor está vacío
  setTimeout(() => {
    const container = document.getElementById('repuestos-container');
    if (container && container.children.length === 0) {
      const addBtn = document.getElementById('add-repuesto');
      if (addBtn) addBtn.click();
    }
  }, 100);

  // Recalcular totales inicial
  setTimeout(recalcTotals, 200);

  console.log('✅ Formulario de documento inicializado correctamente');
}

// CAPTURA GLOBAL DE ERRORES
window.addEventListener('error', (e) => {
  showToast(`Error JS: ${e.message}`, 'error');
  console.error('Error capturado:', e);
});

// INICIALIZACIÓN AL CARGAR EL DOM
document.addEventListener('DOMContentLoaded', initDocumentoForm);

// Exportar funciones globales necesarias
window.removeRepuestoLine = removeRepuestoLine;
window.removeServicioLine = removeServicioLine;
window.removeOtroServicioLine = removeOtroServicioLine;
window.openCommandPalette = openCommandPalette;
window.closeCommandPalette = closeCommandPalette;

console.log('📋 documento_form_futurista.js cargado exitosamente');
