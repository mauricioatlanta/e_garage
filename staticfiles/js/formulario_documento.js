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

    // Genera un número tipo F-001, OT-001, P-001
    const generarNumero = (tipo) => {
        const conf = configPorTipo[tipo] || { prefijo: 'X-' };
        // Generar un número aleatorio de 3 dígitos, siempre con ceros a la izquierda
        const rnd = Math.floor(Math.random() * 999) + 1;
        const num = rnd.toString().padStart(3, '0');
        return conf.prefijo + num;
    };

    function actualizarColor(tipo) {
        if (formContainer) {
            // Quitar colores previos y estilos inline
            formContainer.classList.remove('bg-yellow-100', 'bg-blue-100', 'bg-purple-100', 'border-yellow-400', 'border-blue-400', 'border-purple-400');
            formContainer.style.background = 'transparent';
            formContainer.style.border = 'none';
            // Agregar el nuevo color solo si no es transparente
            if (configPorTipo[tipo]) {
                formContainer.removeAttribute('style');
                formContainer.setAttribute('style', configPorTipo[tipo].style);
            }
        }
    }

    if (tipoDocSelect) {
        tipoDocSelect.addEventListener('change', function () {
            const tipo = tipoDocSelect.value;
            const texto = tipoDocSelect.options[tipoDocSelect.selectedIndex].text.trim();
            console.log('[DEBUG tipo_documento] value:', tipo, '| text:', texto);
            if (numeroInput) {
                numeroInput.value = generarNumero(tipo);
            }
            actualizarColor(tipo);
        });
        // Inicializar color y número al cargar
        const tipoInicial = tipoDocSelect.value;
        const textoInicial = tipoDocSelect.options[tipoDocSelect.selectedIndex].text.trim();
        console.log('[DEBUG tipo_documento] value inicial:', tipoInicial, '| text inicial:', textoInicial);
        actualizarColor(tipoInicial);
        if (numeroInput) {
            numeroInput.value = generarNumero(tipoInicial);
        }
    }

    setTimeout(() => {
        if (window.dal?.widgets?.init) {
            console.log("✅ DAL forzado");
            window.dal.widgets.init();
        } else {
            console.warn("❌ DAL no disponible");
        }
    }, 300);

    // Simulación de base de datos de repuestos (puedes reemplazar por AJAX en producción)
    const REPUESTOS_DB = [
        { partnumber: 'A123', nombre: 'Filtro de Aceite', precio: 8000 },
        { partnumber: 'B456', nombre: 'Bujía NGK', precio: 3500 },
        { partnumber: 'C789', nombre: 'Pastilla de Freno', precio: 12000 },
        { partnumber: 'D111', nombre: 'Aceite 10W40', precio: 15000 },
    ];

    function buscarRepuestoPorPartnumber(partnumber) {
        return REPUESTOS_DB.find(r => r.partnumber.toUpperCase() === partnumber.toUpperCase());
    }

    // Formatea un número como CLP: 120000 => $120.000
    function formatCLP(num) {
        if (isNaN(num)) return '';
        return '$' + num.toLocaleString('es-CL');
    }

window.agregarRepuesto = function() {
    console.log('[DEBUG] agregarRepuesto() ejecutado');
        const tbody = document.querySelector('#tabla-repuestos tbody');
        if (!tbody) return;
        // Crear fila con inputs
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="text" class="partnumber-input w-full border p-1" placeholder="Partnumber" /></td>
            <td><input type="text" class="nombre-input w-full border p-1" placeholder="Nombre" readonly /></td>
            <td><input type="text" inputmode="numeric" pattern="[0-9.]*" class="cantidad-input w-20 border p-1 text-right" min="1" value="1" /></td>
            <td class="relative">
              <span class="absolute left-2 top-1.5 text-gray-500">$</span>
              <input type="text" inputmode="numeric" pattern="[0-9.]*" class="precio-input w-24 border p-1 pl-5 text-right" min="0" value="0" readonly />
            </td>
            <td class="font-bold total-repuesto text-right">$0</td>
            <td><button type="button" class="text-red-600 font-bold remove-repuesto">✕</button></td>
        `;
        tbody.appendChild(tr);
        console.log('[DEBUG] Fila de repuesto agregada al DOM');

        const partInput = tr.querySelector('.partnumber-input');
        const nombreInput = tr.querySelector('.nombre-input');
        const cantidadInput = tr.querySelector('.cantidad-input');
        const precioInput = tr.querySelector('.precio-input');
        const totalTd = tr.querySelector('.total-repuesto');
        const removeBtn = tr.querySelector('.remove-repuesto');

        // Autocompletar nombre y precio al ingresar partnumber
        partInput.addEventListener('input', function() {
            let valor = partInput.value.trim().toUpperCase();
            console.log('[DEBUG] Valor partnumber ingresado:', valor);
            const rep = buscarRepuestoPorPartnumber(valor);
            if (rep) {
                console.log('[DEBUG] Repuesto encontrado:', rep);
                nombreInput.value = rep.nombre;
                precioInput.value = rep.precio;
                precioInput.dispatchEvent(new Event('input'));
                calcularTotal();
            } else {
                console.log('[DEBUG] No se encontró repuesto para:', valor);
                if(valor.length > 0) alert('No se encontró repuesto para: ' + valor);
                nombreInput.value = '';
                precioInput.value = 0;
                totalTd.textContent = '$0';
                calcularGranTotal();
            }
        });

        // Formatear cantidad y precio al escribir
        cantidadInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^\d]/g, '');
            if (this.value) {
                this.value = parseInt(this.value, 10).toLocaleString('es-CL');
            }
            calcularTotal();
        });
        precioInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^\d]/g, '');
            if (this.value) {
                this.value = parseInt(this.value, 10).toLocaleString('es-CL');
            }
            calcularTotal();
        });

        function getIntFromCLP(str) {
            return parseInt((str || '').replace(/[^\d]/g, '')) || 0;
        }

        function calcularTotal() {
            const cantidad = getIntFromCLP(cantidadInput.value);
            const precio = getIntFromCLP(precioInput.value);
            const total = cantidad * precio;
            totalTd.textContent = formatCLP(total);
            calcularGranTotal();
        }

        // Eliminar fila
        removeBtn.addEventListener('click', function() {
            tr.remove();
            calcularGranTotal();
        });

        calcularTotal();
    }

    function calcularGranTotal() {
        let granTotal = 0;
        document.querySelectorAll('.total-repuesto').forEach(td => {
            const valor = parseInt(td.textContent.replace(/[^\d]/g, '')) || 0;
            granTotal += valor;
        });
        document.getElementById('total-repuestos').textContent = formatCLP(granTotal);
    }
});
