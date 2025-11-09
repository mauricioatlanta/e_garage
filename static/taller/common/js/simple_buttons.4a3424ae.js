// Script ultra-simple para botones
console.log('🔥 SIMPLE_BUTTONS.JS CARGADO');

// Función para agregar línea de repuesto
function addRepuestoLine() {
    const container = document.getElementById('repuestos-container');
    if (!container) {
        console.error('❌ Contenedor repuestos no encontrado');
        return;
    }

    const lineNumber = container.children.length;
    const newLine = document.createElement('div');
    newLine.className = 'repuesto-row grid grid-cols-1 md:grid-cols-6 gap-4 mb-4 p-4 bg-gray-700/30 rounded-lg border border-gray-600';
    newLine.innerHTML = `
        <div>
            <label class="block text-cyan-200 text-sm mb-1">Código</label>
            <input type="text" name="rep-${lineNumber}-codigo" class="form-control" placeholder="Código">
        </div>
        <div class="md:col-span-2">
            <label class="block text-cyan-200 text-sm mb-1">Descripción</label>
            <input type="text" name="rep-${lineNumber}-nombre" class="form-control" placeholder="Descripción">
        </div>
        <div>
            <label class="block text-cyan-200 text-sm mb-1">Cantidad</label>
            <input type="number" name="rep-${lineNumber}-cantidad" class="form-control" placeholder="1" min="0" step="1" value="1">
        </div>
        <div>
            <label class="block text-cyan-200 text-sm mb-1">Precio Unitario</label>
            <input type="number" name="rep-${lineNumber}-precio_unitario" class="form-control" placeholder="0" min="0" step="0.01">
        </div>
        <div>
            <label class="block text-cyan-200 text-sm mb-1">Subtotal</label>
            <input type="text" class="form-control" readonly value="$0">
        </div>
        <div class="flex items-end">
            <button type="button" class="remove-line-btn bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded" onclick="this.parentElement.parentElement.remove()">
                🗑️
            </button>
        </div>
    `;

    container.appendChild(newLine);
    console.log('✅ Línea de repuesto agregada');
}

// Función para agregar línea de servicio
function addServicioLine() {
    const container = document.getElementById('servicios-container');
    if (!container) {
        console.error('❌ Contenedor servicios no encontrado');
        return;
    }

    const lineNumber = container.children.length;
    const newLine = document.createElement('div');
    newLine.className = 'servicio-row grid grid-cols-1 md:grid-cols-6 gap-4 mb-4 p-4 bg-gray-700/30 rounded-lg border border-gray-600';
    newLine.innerHTML = `
        <div>
            <label class="block text-blue-200 text-sm mb-1">Código</label>
            <input type="text" name="serv-${lineNumber}-codigo" class="form-control" placeholder="Código">
        </div>
        <div class="md:col-span-2">
            <label class="block text-blue-200 text-sm mb-1">Descripción</label>
            <input type="text" name="serv-${lineNumber}-nombre" class="form-control" placeholder="Descripción">
        </div>
        <div>
            <label class="block text-blue-200 text-sm mb-1">Cantidad</label>
            <input type="number" name="serv-${lineNumber}-cantidad" class="form-control" placeholder="1" min="0" step="1" value="1">
        </div>
        <div>
            <label class="block text-blue-200 text-sm mb-1">Precio Unitario</label>
            <input type="number" name="serv-${lineNumber}-precio_unitario" class="form-control" placeholder="0" min="0" step="0.01">
        </div>
        <div>
            <label class="block text-blue-200 text-sm mb-1">Subtotal</label>
            <input type="text" class="form-control" readonly value="$0">
        </div>
        <div class="flex items-end">
            <button type="button" class="remove-line-btn bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded" onclick="this.parentElement.parentElement.remove()">
                🗑️
            </button>
        </div>
    `;

    container.appendChild(newLine);
    console.log('✅ Línea de servicio agregada');
}

// Inicialización cuando el DOM esté listo
function initSimpleButtons() {
    console.log('🚀 Inicializando botones simples...');

    // Esperar un poco para que todo esté cargado
    setTimeout(function() {
        console.log('🔍 Buscando botones...');

        const addRepuestoBtn = document.getElementById('add-repuesto');
        const addServicioBtn = document.getElementById('add-servicio');

        console.log('Botón repuesto encontrado:', !!addRepuestoBtn);
        console.log('Botón servicio encontrado:', !!addServicioBtn);

        if (addRepuestoBtn) {
            console.log('✅ Configurando botón repuesto...');
            addRepuestoBtn.onclick = function(e) {
                e.preventDefault();
                console.log('🖱️ CLICK REPUESTO!');
                addRepuestoLine();
            };
        }

        if (addServicioBtn) {
            console.log('✅ Configurando botón servicio...');
            addServicioBtn.onclick = function(e) {
                e.preventDefault();
                console.log('🖱️ CLICK SERVICIO!');
                addServicioLine();
            };
        }

        console.log('✅ Botones configurados');
    }, 1000);
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSimpleButtons);
} else {
    initSimpleButtons();
}
