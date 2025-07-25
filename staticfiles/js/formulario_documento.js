// --- AUTOCOMPLETADO INTELIGENTE DE REPUESTOS Y SERVICIOS ---
function activarAutocompleteRepuesto(tr) {
    const partInput = tr.querySelector('.partnumber-input');
    const nombreInput = tr.querySelector('.nombre-input');
    const precioInput = tr.querySelector('.precio-input');
    if (!partInput) return;
    // Mostrar mensaje si el partnumber no existe
    partInput.addEventListener('blur', function() {
        const valor = partInput.value.trim();
        if (!valor) return;
        $.getJSON('/documentos/autocomplete_repuesto/', {q: valor}, function(data) {
            const existe = data.results.some(r => r.partnumber === valor);
            if (!existe) {
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
            }
        });
    });
    $(partInput).autocomplete({
        source: function(request, response) {
            $.getJSON('/documentos/autocomplete_repuesto/', {q: request.term}, function(data) {
                response(data.results.map(r => ({
                    label: r.partnumber + ' - ' + r.nombre + ' ($' + r.precio + ')',
                    value: r.partnumber,
                    nombre: r.nombre,
                    precio: r.precio
                })));
            });
        },
        minLength: 2,
        select: function(event, ui) {
            if (nombreInput) nombreInput.value = ui.item.nombre;
            if (precioInput) precioInput.value = ui.item.precio;
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
window.agregarRepuesto = function() {
    const tbody = document.querySelector('#tabla-repuestos tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="partnumber-input futurista-input border p-1 rounded w-full" placeholder="Partnumber"></td>
        <td><input type="text" class="nombre-input futurista-input border p-1 rounded w-full" placeholder="Nombre"></td>
        <td><input type="number" class="cantidad-input futurista-input border p-1 rounded w-20" value="1" min="1"></td>
        <td><input type="number" class="precio-input futurista-input border p-1 rounded w-24" value="0" min="0"></td>
        <td class="subtotal-repuesto font-semibold">$0</td>
        <td><button type="button" class="text-red-600 font-bold" onclick="this.closest('tr').remove(); actualizarTotalRepuestos();">✖</button></td>
    `;
    tbody.appendChild(tr);
    activarAutocompleteRepuesto(tr);
    actualizarTotalRepuestos();
    tr.querySelector('.cantidad-input').addEventListener('input', actualizarTotalRepuestos);
    tr.querySelector('.precio-input').addEventListener('input', actualizarTotalRepuestos);
};

window.agregarServicio = function() {
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
};

function actualizarTotalRepuestos() {
    let total = 0;
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
        const cantidad = parseInt(row.querySelector('.cantidad-input')?.value || '1');
        const precio = parseInt(row.querySelector('.precio-input')?.value || '0');
        const subtotal = cantidad * precio;
        row.querySelector('.subtotal-repuesto').textContent = `$${subtotal}`;
        total += subtotal;
    });
    document.getElementById('total-repuestos').textContent = `$${total}`;
    actualizarTotalesDocumento();
}

function actualizarTotalServicios() {
    let total = 0;
    document.querySelectorAll('#tabla-servicios tbody tr').forEach((row) => {
        const precio = parseInt(row.querySelector('.precio-servicio-input')?.value || '0');
        total += precio;
    });
    document.getElementById('total-servicios').textContent = `$${total}`;
    actualizarTotalesDocumento();
}

function actualizarTotalesDocumento() {
    // Sumar totales de repuestos y servicios
    let totalRepuestos = 0;
    let totalServicios = 0;
    document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
        const cantidad = parseInt(row.querySelector('.cantidad-input')?.value || '1');
        const precio = parseInt(row.querySelector('.precio-input')?.value || '0');
        totalRepuestos += cantidad * precio;
    });
    document.querySelectorAll('#tabla-servicios tbody tr').forEach((row) => {
        const precio = parseInt(row.querySelector('.precio-servicio-input')?.value || '0');
        totalServicios += precio;
    });
    const subtotal = totalRepuestos + totalServicios;
    const iva = Math.round(totalRepuestos * 0.19);
    const granTotal = subtotal + iva;
    document.getElementById('subtotal-doc').textContent = `$${subtotal}`;
    document.getElementById('iva-doc').textContent = `$${iva}`;
    document.getElementById('gran-total-doc').textContent = `$${granTotal}`;
}

// Requiere jQuery y jQuery UI para el autocompletado dinámico de partnumber
console.log('[DEBUG] formulario_documento.js cargado');

document.addEventListener('DOMContentLoaded', function () {
    const tipoDocSelect = document.getElementById('id_tipo_documento');
    const numeroInput = document.getElementById('id_numero_documento');
    const formContainer = document.getElementById('form-doc-container');

    const configPorTipo = {
        'Factura': { color: 'bg-yellow-100 border-yellow-400', style: 'background:rgba(255,255,0,0.12);border:2px solid #ffe066;', prefijo: 'F-' },
        'Orden de trabajo': { color: 'bg-blue-100 border-blue-400', style: 'background:rgba(0,180,255,0.12);border:2px solid #4fc3f7;', prefijo: 'OT-' },
        'Presupuesto': { color: 'bg-purple-100 border-purple-400', style: 'background:rgba(128,0,255,0.12);border:2px solid #b39ddb;', prefijo: 'P-' },
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
            formContainer.setAttribute('style', configPorTipo[tipo]?.style || '');
        }
    }

    if (tipoDocSelect) {
        tipoDocSelect.addEventListener('change', function () {
            const tipo = tipoDocSelect.value;
            numeroInput.value = generarNumero(tipo);
            actualizarColor(tipo);
        });

        actualizarColor(tipoDocSelect.value);
        numeroInput.value = generarNumero(tipoDocSelect.value);
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

    document.querySelector('form').addEventListener('submit', function (e) {
        const items = [];

        document.querySelectorAll('#tabla-repuestos tbody tr').forEach((row) => {
            const partnumber = row.querySelector('.partnumber-input')?.value || '';
            const nombre = row.querySelector('.nombre-input')?.value || '';
            const cantidad = parseInt((row.querySelector('.cantidad-input')?.value || '1').replace(/[^\d]/g, '')) || 1;
            const precio = parseInt((row.querySelector('.precio-input')?.value || '0').replace(/[^\d]/g, '')) || 0;

            if (nombre && precio > 0) {
                items.push({
                    tipo: 'repuesto',
                    partnumber: partnumber,
                    nombre: nombre,
                    cantidad: cantidad,
                    precio: precio
                });
            }
        });

        document.querySelectorAll('#tabla-servicios tbody tr').forEach((row) => {
            const nombre = row.querySelector('.nombre-servicio-input')?.value || '';
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
});
