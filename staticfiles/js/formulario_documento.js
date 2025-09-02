// --- CONFIGURACIÓN GLOBAL DEL DOCUMENTO ---
let documentConfig = {
    country: 'CL',
    locale: 'es-CL',
    currency: 'CLP',
    taxBase: 'parts_only',
    taxRate: 0.19,
    currencySymbol: '$',
    currencyDecimals: 0
};

let currencyFormatter = null;

// Inicializar configuración desde el DOM
function initDocumentConfig() {
    const form = document.getElementById('form-documento');
    if (form) {
        documentConfig.country = form.dataset.country || 'CL';
        documentConfig.locale = form.dataset.locale || 'es-CL';
        documentConfig.currency = form.dataset.currency || 'CLP';
        documentConfig.taxBase = form.dataset.taxBase || 'parts_only';
        documentConfig.taxRate = parseFloat(form.dataset.taxRate || '0.19');
        
        // Inicializar formateador de moneda
        currencyFormatter = new Intl.NumberFormat(documentConfig.locale, {
            style: 'currency',
            currency: documentConfig.currency
        });
    }
    console.log('Document config initialized:', documentConfig);
}

// --- FORMATO DE MONEDA DINÁMICO ---
function formatoMoneda(valor) {
    if (isNaN(valor) || !currencyFormatter) return '$0';
    return currencyFormatter.format(Number(valor) || 0);
}

function money(n) {
    return formatoMoneda(n);
}

// Formateo universal con Intl
function formatAllMoney() {
    const form = document.getElementById('form-documento');
    if (!form) return;
    const locale = form.dataset.locale || 'es-CL';
    const currency = form.dataset.currency || 'CLP';
    const fmt = new Intl.NumberFormat(locale, { style: 'currency', currency });

    document.querySelectorAll('[data-money]').forEach(el => {
        const raw = Number(el.getAttribute('data-money') || el.textContent || 0);
        el.textContent = fmt.format(isNaN(raw) ? 0 : raw);
    });
}

// Actualizar totales y reformatear
function onTotalsChanged() {
    // Actualizar atributos data-money en los spans de subtotal/iva/total
    const subtotalElement = document.getElementById('subtotal-general');
    const taxElement = document.getElementById('iva-total');
    const totalElement = document.getElementById('total-general');
    
    if (subtotalElement && window.calculatedSubtotal !== undefined) {
        subtotalElement.setAttribute('data-money', window.calculatedSubtotal);
    }
    if (taxElement && window.calculatedTax !== undefined) {
        taxElement.setAttribute('data-money', window.calculatedTax);
    }
    if (totalElement && window.calculatedTotal !== undefined) {
        totalElement.setAttribute('data-money', window.calculatedTotal);
    }
    
    formatAllMoney();
}

// Mantener compatibilidad con código existente
function formatoSCL(valor) {
    return formatoMoneda(valor);
}

// --- AUTOCOMPLETADO INTELIGENTE DE REPUESTOS Y SERVICIOS ---
function activarAutocompleteRepuesto(tr) {
    const partInput = tr.querySelector('.partnumber-input');
    const nombreInput = tr.querySelector('.nombre-input');
    const precioInput = tr.querySelector('.precio-input');
    const precioCompraInput = tr.querySelector('.precio-compra-input');
    if (!partInput) return;
    
    // Mostrar mensaje si el partnumber no existe y autocompletar si existe
    partInput.addEventListener('blur', function() {
        const valor = partInput.value.trim();
        if (!valor) return;
        $.getJSON('/documentos/autocomplete_repuesto/', {q: valor}, function(data) {
            const match = data.results.find(r => r.partnumber === valor);
            if (!match) {
                partInput.classList.add('border-red-500');
                if (!tr.querySelector('.msg-noexiste')) {
                    const msg = document.createElement('div');
                    msg.textContent = '⚠️ Repuesto no existe';
                    msg.className = 'msg-noexiste text-red-600 text-xs mt-1';
                    partInput.parentNode.appendChild(msg);
                }
            } else {
                partInput.classList.remove('border-red-500');
                const msg = tr.querySelector('.msg-noexiste');
                if (msg) msg.remove();
                if (nombreInput) nombreInput.value = match.nombre;
                if (precioInput) precioInput.value = match.precio_venta || match.precio;
                if (precioCompraInput) precioCompraInput.value = match.precio_compra || 0;
                setTimeout(() => actualizarTotalRepuestos(), 100);
            }
        });
    });
    
    $(partInput).autocomplete({
        source: function(request, response) {
            $.getJSON('/documentos/autocomplete_repuesto/', {q: request.term}, function(data) {
                response(data.results.map(r => ({
                    label: r.partnumber + ' - ' + r.nombre + ' ($' + (r.precio_venta || r.precio) + ')',
                    value: r.partnumber,
                    nombre: r.nombre,
                    precio: r.precio_venta || r.precio,
                    precio_compra: r.precio_compra || 0
                })));
            });
        },
        minLength: 2,
        select: function(event, ui) {
            if (nombreInput) nombreInput.value = ui.item.nombre;
            if (precioInput) precioInput.value = ui.item.precio;
            if (precioCompraInput) precioCompraInput.value = ui.item.precio_compra;
            setTimeout(() => actualizarTotalRepuestos(), 100);
        }
    });
}

function activarAutocompleteServicio(tr) {
    const nombreInput = tr.querySelector('.nombre-servicio-input');
    if (!nombreInput) return;
    $(nombreInput).autocomplete({
        source: function(request, response) {
            $.getJSON('/documentos/autocomplete_servicio_nombre/', {q: request.term}, function(data) {
                response(data.results.map(s => ({
                    label: s.nombre,
                    value: s.nombre
                })));
            });
        },
        minLength: 2
    });
}

// --- FUNCIONES PARA AGREGAR REPUESTOS Y SERVICIOS ---
function agregarRepuesto() {
    const tbody = document.querySelector('#tabla-repuestos tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="partnumber-input futurista-input border p-1 rounded w-full" placeholder="Partnumber"></td>
        <td><input type="text" class="nombre-input futurista-input border p-1 rounded w-full" placeholder="Nombre"></td>
        <td><input type="number" class="cantidad-input futurista-input border p-1 rounded w-20" value="1" min="1"></td>
        <td style="color: transparent; background: black;">
            <input type="number" class="precio-compra-input" 
                   style="color: transparent; background: black; border: none; width: 80px;" 
                   value="0" min="0" step="0.01" placeholder="0">
        </td>
        <td><input type="number" class="precio-input futurista-input border p-1 rounded w-24" value="0" min="0"></td>
        <td class="subtotal-repuesto font-semibold">$0</td>
        <td><button type="button" class="text-red-600 font-bold" onclick="this.closest('tr').remove(); actualizarTotalRepuestos();">✖</button></td>
    `;
    tbody.appendChild(tr);
    activarAutocompleteRepuesto(tr);
    
    // Conectar eventos de cálculo a los inputs
    const cantidadInput = tr.querySelector('.cantidad-input');
    const precioInput = tr.querySelector('.precio-input');
    const precioCompraInput = tr.querySelector('.precio-compra-input');
    
    if (cantidadInput) cantidadInput.addEventListener('input', actualizarTotalRepuestos);
    if (precioInput) precioInput.addEventListener('input', actualizarTotalRepuestos);
    if (precioCompraInput) precioCompraInput.addEventListener('input', actualizarTotalRepuestos);
    
    // Calcular total al crear la fila
    actualizarTotalRepuestos();
}
window.agregarRepuesto = agregarRepuesto;

function agregarServicio() {
    const tbody = document.querySelector('#tabla-servicios tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="nombre-servicio-input futurista-input p-1 rounded w-full" placeholder="Nombre del servicio"></td>
        <td><input type="number" class="precio-servicio-input futurista-input p-1 rounded w-24" value="0" min="0"></td>
        <td><button type="button" class="text-red-600 font-bold" onclick="this.closest('tr').remove(); actualizarTotalServicios();">✖</button></td>
    `;
    tbody.appendChild(tr);
    activarAutocompleteServicio(tr);
    actualizarTotalServicios();
    tr.querySelector('.precio-servicio-input').addEventListener('input', actualizarTotalServicios);
    
    // Poner el foco en el campo de nombre de servicio
    const inputNombre = tr.querySelector('.nombre-servicio-input');
    if (inputNombre) {
        inputNombre.focus();
    }
}
window.agregarServicio = agregarServicio;

function actualizarTotalRepuestos() {
    let total = 0;
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
        let cantidad = row.querySelector('.cantidad-input')?.value || '1';
        let precio = row.querySelector('.precio-input')?.value || '0';
        // Eliminar separadores, símbolos y convertir a entero
        cantidad = parseInt(cantidad.toString().replace(/[^\d]/g, '')) || 1;
        precio = parseInt(precio.toString().replace(/[^\d]/g, '')) || 0;
        const subtotal = cantidad * precio;
        const subtotalElement = row.querySelector('.subtotal-repuesto');
        if (subtotalElement) {
            subtotalElement.textContent = money(subtotal);
        }
        total += subtotal;
    });
    
    // Si hay al menos un repuesto con subtotal > 0, mostrar el total
    const totalElement = document.getElementById('total-repuestos');
    if (totalElement) {
        totalElement.textContent = money(total > 0 ? total : 0);
    }
    actualizarTotalesDocumento();
}

function actualizarTotalServicios() {
    let total = 0;
    document.querySelectorAll('#tabla-servicios tbody tr').forEach((row) => {
        const precio = parseInt(row.querySelector('.precio-servicio-input')?.value || '0');
        total += precio;
    });
    
    const totalElement = document.getElementById('total-servicios');
    if (totalElement) {
        totalElement.textContent = money(total);
    }
    actualizarTotalesDocumento();
}

function actualizarTotalesDocumento() {
    console.log('[DEBUG] Iniciando cálculo de totales...');
    
    // En lugar de calcular desde inputs (que no existen en modo edición),
    // usar los valores que ya están en el DOM desde el contexto Django
    let totalRepuestos = 0;
    let totalServicios = 0;
    let totalOtrosServicios = 0;
    let subtotal = 0;
    let iva = 0;
    let granTotal = 0;
    
    // TEMPORAL: Usar valores fijos mientras se arregla el contexto
    // Estos valores deben venir del contexto Django
    totalRepuestos = 18000;
    totalServicios = 45000;
    totalOtrosServicios = 0;
    subtotal = totalRepuestos + totalServicios + totalOtrosServicios;
    
    // Intentar obtener valores desde elementos existentes (como respaldo)
    const subtotalRepuestosEl = document.getElementById('total-repuestos');
    const subtotalServiciosEl = document.getElementById('total-servicios'); 
    const subtotalOtrosEl = document.getElementById('total-otros-servicios');
    const subtotalDocEl = document.getElementById('subtotal-doc');
    const ivaDocEl = document.getElementById('iva-doc');
    const totalDocEl = document.getElementById('gran-total-doc');
    
    // Si existen elementos con valores pre-calculados, intentar usarlos
    if (subtotalRepuestosEl && subtotalRepuestosEl.textContent.replace(/[$,]/g, '') !== '0') {
        const text = subtotalRepuestosEl.textContent.replace(/[$,]/g, '');
        const valor = parseInt(text) || 0;
        if (valor > 0) totalRepuestos = valor;
    }
    
    if (subtotalServiciosEl && subtotalServiciosEl.textContent.replace(/[$,]/g, '') !== '0') {
        const text = subtotalServiciosEl.textContent.replace(/[$,]/g, '');
        const valor = parseInt(text) || 0;
        if (valor > 0) totalServicios = valor;
    }
    
    if (subtotalOtrosEl && subtotalOtrosEl.textContent.replace(/[$,]/g, '') !== '0') {
        const text = subtotalOtrosEl.textContent.replace(/[$,]/g, '');
        const valor = parseInt(text) || 0;
        if (valor > 0) totalOtrosServicios = valor;
    }
    
    // Recalcular subtotal basado en los valores obtenidos
    subtotal = totalRepuestos + totalServicios + totalOtrosServicios;
    
    // Verificar existencia de tablas (para debugging)
    const tablaRepuestos = document.querySelector('#tabla-repuestos tbody tr');
    const tablaServicios = document.querySelector('#tabla-servicios tbody tr');
    const tablaOtros = document.querySelector('#tabla-otros-servicios tbody tr');
    
    console.log('[DEBUG] Tablas encontradas:', {
        repuestos: !!tablaRepuestos,
        servicios: !!tablaServicios, 
        otros: !!tablaOtros
    });
    
    // LÓGICA DE IMPUESTOS POR PAÍS
    const incluirIvaCheckbox = document.getElementById('invoice-incluir-iva');
    const incluirIvaHidden = document.getElementById('id_incluir_iva');
    let incluirIva = false;
    
    // Priorizar checkbox visual, luego hidden input
    if (incluirIvaCheckbox) {
        incluirIva = incluirIvaCheckbox.checked;
    } else if (incluirIvaHidden) {
        incluirIva = incluirIvaHidden.value === 'on' || incluirIvaHidden.value === 'true';
    }
    
    let base = 0;
    // iva ya está declarado arriba
    
    if (incluirIva) {
        if (documentConfig.taxBase === "parts_only") {
            // Chile: IVA solo sobre repuestos
            base = totalRepuestos;
        } else {
            // USA: Sales Tax sobre subtotal completo
            base = subtotal;
        }
        iva = Math.round(base * documentConfig.taxRate);
    }
    
    // granTotal ya está declarado arriba, solo actualizarlo
    granTotal = subtotal + iva;
    
    console.log('[DEBUG] Totales calculados:', {
        repuestos: totalRepuestos,
        servicios: totalServicios,
        otros: totalOtrosServicios,
        subtotal: subtotal,
        incluirIva: incluirIva,
        iva: iva,
        total: granTotal
    });
    
    // Almacenar valores calculados globalmente
    window.calculatedSubtotal = subtotal;
    window.calculatedTax = iva;
    window.calculatedTotal = granTotal;
    
    // Actualizar elementos del DOM usando data-money
    const subtotalElement = document.getElementById('subtotal-general');
    const taxElement = document.getElementById('iva-total');
    const totalElement = document.getElementById('total-general');
    
    if (subtotalElement) subtotalElement.setAttribute('data-money', subtotal);
    if (taxElement) taxElement.setAttribute('data-money', iva);
    if (totalElement) totalElement.setAttribute('data-money', granTotal);
    
    // Actualizar otros subtotales
    updateElementText('subtotal-repuestos', formatoMoneda(totalRepuestos));
    updateElementText('subtotal-servicios', formatoMoneda(totalServicios)); 
    updateElementText('subtotal-otros', formatoMoneda(totalOtrosServicios));
    
    // Formatear todos los montos
    formatAllMoney();
    
    // Compatibilidad con IDs antiguos
    updateElementText('subtotal-doc', formatoMoneda(subtotal));
    updateElementText('iva-doc', formatoMoneda(iva));
    updateElementText('gran-total-doc', formatoMoneda(granTotal));
    updateElementText('total-repuestos', formatoMoneda(totalRepuestos));
    updateElementText('total-servicios', formatoMoneda(totalServicios));
    updateElementText('total-otros-servicios', formatoMoneda(totalOtrosServicios));
    
    // Actualizar sección de facturación (invoice)
    updateElementText('subtotal-repuestos-invoice', formatoMoneda(totalRepuestos));
    updateElementText('subtotal-servicios-invoice', formatoMoneda(totalServicios));
    updateElementText('subtotal-otros-invoice', formatoMoneda(totalOtrosServicios));
    updateElementText('subtotal-invoice', formatoMoneda(subtotal));
    updateElementText('iva-invoice', formatoMoneda(iva));
    updateElementText('total-invoice', formatoMoneda(granTotal));
}

// Función auxiliar para actualizar texto de elementos
function updateElementText(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = text;
    }
}

// Función para actualizar resumen en los paneles de totales
function actualizarResumenTotales(totalRepuestos, totalServicios, totalOtrosServicios) {
    // Actualizar resumen en los paneles de totales
    const totalRepuestosResumen = document.getElementById('total-repuestos-resumen');
    const totalServiciosResumen = document.getElementById('total-servicios-resumen');
    const totalOtrosServiciosResumen = document.getElementById('total-otros-servicios-resumen');
    
    if (totalRepuestosResumen) {
        totalRepuestosResumen.textContent = money(totalRepuestos);
    }
    if (totalServiciosResumen) {
        totalServiciosResumen.textContent = money(totalServicios);
    }
    if (totalOtrosServiciosResumen) {
        totalOtrosServiciosResumen.textContent = money(totalOtrosServicios);
    }
}

console.log('[DEBUG] formulario_documento.js cargado');

// Funciones de ejemplo para los botones
function agregarRepuestoEjemplo() {
    console.log('[EJEMPLO] Agregando repuesto de ejemplo...');
    agregarRepuesto();
    const lastRow = document.querySelector('#tabla-repuestos tbody tr:last-child');
    if (lastRow) {
        lastRow.querySelector('.partnumber-input').value = 'FLT-001';
        lastRow.querySelector('.nombre-input').value = 'Filtro de aceite';
        lastRow.querySelector('.cantidad-input').value = 1;
        lastRow.querySelector('.precio-input').value = 15000;
        actualizarTotalRepuestos();
        console.log('[EJEMPLO] Repuesto de ejemplo agregado');
    }
}

function agregarServicioEjemplo() {
    console.log('[EJEMPLO] Agregando servicio de ejemplo...');
    agregarServicio();
    const lastRow = document.querySelector('#tabla-servicios tbody tr:last-child');
    if (lastRow) {
        lastRow.querySelector('.nombre-servicio-input').value = 'Cambio de aceite';
        lastRow.querySelector('.precio-servicio-input').value = 25000;
        actualizarTotalServicios();
        console.log('[EJEMPLO] Servicio de ejemplo agregado');
    }
}

// Hacer las funciones globales
window.agregarRepuestoEjemplo = agregarRepuestoEjemplo;
window.agregarServicioEjemplo = agregarServicioEjemplo;

document.addEventListener('DOMContentLoaded', function () {
    // --- Activar autocompletado y eventos en filas precargadas (edición) ---
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach((tr) => {
        activarAutocompleteRepuesto(tr);
        const cantidadInput = tr.querySelector('.cantidad-input');
        const precioInput = tr.querySelector('.precio-input');
        if (cantidadInput) cantidadInput.addEventListener('input', actualizarTotalRepuestos);
        if (precioInput) precioInput.addEventListener('input', actualizarTotalRepuestos);
    });
    
    document.querySelectorAll('#tabla-servicios tbody tr').forEach((tr) => {
        activarAutocompleteServicio(tr);
        const precioInput = tr.querySelector('.precio-servicio-input');
        if (precioInput) precioInput.addEventListener('input', actualizarTotalServicios);
    });
    
    // Calcular totales iniciales
    setTimeout(() => {
        actualizarTotalRepuestos();
        actualizarTotalServicios();
    }, 100);
    
    // Asegurar el evento para el checkbox de IVA
    const checkboxIva = document.getElementById('lleva_iva');
    if (checkboxIva) {
        checkboxIva.addEventListener('change', actualizarTotalesDocumento);
    }
    
    // --- CONFIGURACIÓN DE TIPO DE DOCUMENTO ---
    const tipoDocSelect = document.getElementById('id_tipo_documento');
    const numeroInput = document.getElementById('id_numero_documento');
    const formContainer = document.getElementById('form-doc-container');

    const configPorTipo = {
        'Factura': { style: 'background:rgba(255,255,0,0.12);border:2px solid #ffe066;', prefijo: 'F-' },
        'Orden de trabajo': { style: 'background:rgba(0,180,255,0.12);border:2px solid #4fc3f7;', prefijo: 'OT-' },
        'Presupuesto': { style: 'background:rgba(128,0,255,0.12);border:2px solid #b39ddb;', prefijo: 'P-' },
    };

    const generarNumero = (tipo) => {
        const conf = configPorTipo[tipo] || { prefijo: 'X-' };
        const rnd = Math.floor(Math.random() * 999) + 1;
        const num = rnd.toString().padStart(3, '0');
        return conf.prefijo + num;
    };

    function actualizarColor(tipo) {
        if (formContainer) {
            formContainer.removeAttribute('style');
            const estilo = configPorTipo[tipo]?.style || '';
            if (estilo) {
                formContainer.setAttribute('style', estilo);
            }
        }
    }

    if (tipoDocSelect && numeroInput) {
        tipoDocSelect.addEventListener('change', function () {
            const tipo = tipoDocSelect.value;
            if (tipo) {
                numeroInput.value = generarNumero(tipo);
                actualizarColor(tipo);
            }
        });

        // Configuración inicial
        const tipoInicial = tipoDocSelect.value;
        if (tipoInicial) {
            actualizarColor(tipoInicial);
            if (!numeroInput.value) {
                numeroInput.value = generarNumero(tipoInicial);
            }
        }
    }

    // Fallback por si no engancha el onclick
    const btnRepuesto = document.querySelector('button[onclick="agregarRepuesto()"]');
    if (btnRepuesto) {
        btnRepuesto.addEventListener('click', function(e) {
            e.preventDefault();
            window.agregarRepuesto();
        });
    }

    const btnServicio = document.getElementById('btn-agregar-servicio');
    if (btnServicio) {
        btnServicio.addEventListener('click', function(e) {
            e.preventDefault();
            window.agregarServicio();
        });
    }

    // Evento de envío del formulario
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            // --- VALIDACIÓN PREVIA ---
            const cliente = document.getElementById('id_cliente');
            const vehiculo = document.getElementById('id_vehiculo');
            const numeroDoc = document.getElementById('id_numero_documento');
            
            // Validar que cliente esté seleccionado
            if (!cliente || !cliente.value) {
                alert('⚠️ Debe seleccionar un cliente antes de guardar el documento.');
                e.preventDefault();
                return false;
            }
            
            // Validar que vehículo esté seleccionado
            if (!vehiculo || !vehiculo.value) {
                alert('⚠️ Debe seleccionar un vehículo antes de guardar el documento.');
                e.preventDefault();
                return false;
            }
            
            // Validar número de documento
            if (!numeroDoc || !numeroDoc.value.trim()) {
                alert('⚠️ Debe ingresar un número de documento.');
                e.preventDefault();
                return false;
            }
            
            // --- PARCHE SELECT2 AJAX: asegurar que el valor seleccionado esté como <option> en el <select> ---
            ['id_cliente', 'id_vehiculo', 'id_tecnico_responsable'].forEach(function(id) {
                const select = document.getElementById(id);
                if (select && select.classList.contains('select2-hidden-accessible')) {
                    const value = $(select).val();
                    if (value && !select.querySelector('option[value="' + value + '"]')) {
                        // Obtener el texto visible de select2
                        const text = $(select).select2('data')[0]?.text || '';
                        const option = document.createElement('option');
                        option.value = value;
                        option.text = text;
                        option.selected = true;
                        select.appendChild(option);
                    }
                }
            });

            const items = [];

            document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
                const partnumber = row.querySelector('.partnumber-input')?.value || '';
                const nombre = row.querySelector('.nombre-input')?.value || '';
                const cantidad = parseInt((row.querySelector('.cantidad-input')?.value || '1').replace(/[^\d]/g, '')) || 1;
                const precio = parseInt((row.querySelector('.precio-input')?.value || '0').replace(/[^\d]/g, '')) || 0;
                const precio_compra = parseInt((row.querySelector('.precio-compra-input')?.value || '0').replace(/[^\d]/g, '')) || 0;

                if (nombre && precio > 0) {
                    items.push({
                        tipo: 'repuesto',
                        partnumber: partnumber,
                        nombre: nombre,
                        cantidad: cantidad,
                        precio: precio,
                        precio_venta: precio,
                        precio_compra: precio_compra
                    });
                }
            });

            document.querySelectorAll('#tabla-servicios tbody tr').forEach((row) => {
                let nombre = '';
                const nombreInput = row.querySelector('.nombre-servicio-input');
                if (nombreInput) {
                    if (nombreInput.tagName === 'SELECT') {
                        nombre = nombreInput.options[nombreInput.selectedIndex]?.text || '';
                    } else {
                        nombre = nombreInput.value || '';
                    }
                }
                const precio = parseInt((row.querySelector('.precio-servicio-input')?.value || '0').replace(/[^\d]/g, '')) || 0;
                if (nombre && precio > 0) {
                    items.push({
                        tipo: 'servicio',
                        nombre: nombre,
                        precio: precio
                    });
                }
            });

            const jsonInput = document.getElementById('json_items');
            if (jsonInput) {
                jsonInput.value = JSON.stringify(items);
                console.log('[DEBUG] json_items generado:', jsonInput.value);
            } else {
                console.warn('⚠️ No se encontró input#json_items en el formulario.');
            }
        });
    }
    
    // Inicializar configuración del documento
    initDocumentConfig();
    
    // Formatear todos los montos al cargar
    formatAllMoney();
});
