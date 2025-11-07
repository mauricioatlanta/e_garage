// ========================================
// FUNCIONALIDADES AVANZADAS DEL FORMULARIO DE DOCUMENTOS
// ========================================

let searchTimeout = null;
let currentClient = null;
let currentVehicle = null;

// ========================================
// 1. GENERACIÓN AUTOMÁTICA DE NÚMERO DE DOCUMENTO
// ========================================

function updateDocumentNumber() {
    const tipoInput = document.getElementById('tipo');
    const numberDisplay = document.getElementById('document-number');
    
    if (!tipoInput || !numberDisplay) {
        console.log('⚠️ No se encontraron elementos para actualizar número de documento');
        return;
    }
    
    const tipo = tipoInput.value;
    if (!tipo) {
        numberDisplay.textContent = 'Will be generated automatically';
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
    const apiUrl = `/${countryPrefix}/documentos/api/obtener-numero-documento/?tipo=${apiTipo}`;
    
    console.log('📡 Obteniendo número de documento para tipo:', tipo);
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.numero) {
                numberDisplay.textContent = data.numero;
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

// ========================================
// 2. BÚSQUEDA EN TIEMPO REAL DE CLIENTES
// ========================================

function initClientSearch() {
    const searchInput = document.getElementById('cliente-search');
    const resultsContainer = document.getElementById('cliente-results');
    const clienteSelect = document.getElementById('id_cliente');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }
        
        // Debounce la búsqueda
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchClients(query);
        }, 300);
    });
    
    // Ocultar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.classList.add('hidden');
        }
    });
}

function searchClients(query) {
    const resultsContainer = document.getElementById('cliente-results');
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/clientes/search/?q=${encodeURIComponent(query)}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.clientes && data.clientes.length > 0) {
                displayClientResults(data.clientes);
            } else {
                resultsContainer.innerHTML = '<div class="p-3 text-gray-400">No clients found</div>';
                resultsContainer.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error buscando clientes:', error);
            resultsContainer.innerHTML = '<div class="p-3 text-red-400">Search error</div>';
            resultsContainer.classList.remove('hidden');
        });
}

function displayClientResults(clientes) {
    const resultsContainer = document.getElementById('cliente-results');
    
    const html = clientes.map(cliente => `
        <div class="p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-600 last:border-b-0 cliente-result-item" 
             data-cliente-id="${cliente.id}"
             data-cliente-nombre="${cliente.nombre}"
             data-cliente-identificador="${cliente.identificador || ''}">
            <div class="font-medium text-white">${cliente.nombre}</div>
            <div class="text-sm text-gray-400">${cliente.identificador || 'Sin identificador'}</div>
            ${cliente.email ? `<div class="text-xs text-gray-500">${cliente.email}</div>` : ''}
        </div>
    `).join('');
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.remove('hidden');
    
    // Agregar event listeners a los resultados
    resultsContainer.querySelectorAll('.cliente-result-item').forEach(item => {
        item.addEventListener('click', function() {
            selectClient(this.dataset.clienteId, this.dataset.clienteNombre, this.dataset.clienteIdentificador);
        });
    });
}

function selectClient(clienteId, nombre, identificador) {
    const clienteSelect = document.getElementById('id_cliente');
    const searchInput = document.getElementById('cliente-search');
    const resultsContainer = document.getElementById('cliente-results');
    
    // Seleccionar en el dropdown
    clienteSelect.value = clienteId;
    
    // Actualizar el campo de búsqueda
    searchInput.value = `${nombre} - ${identificador}`;
    
    // Ocultar resultados
    resultsContainer.classList.add('hidden');
    
    // Cargar vehículos del cliente
    loadClientVehicles(clienteId);
    
    currentClient = { id: clienteId, nombre, identificador };
}

// ========================================
// 3. CARGA DE VEHÍCULOS POR CLIENTE
// ========================================

function loadClientVehicles(clienteId) {
    const vehiculoSelect = document.getElementById('id_vehiculo');
    
    // Limpiar opciones actuales
    vehiculoSelect.innerHTML = '<option value="">Cargando vehículos...</option>';
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/vehiculos-cliente/?cliente_id=${clienteId}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.vehiculos && data.vehiculos.length > 0) {
                vehiculoSelect.innerHTML = '<option value="">Select a vehicle...</option>';
                
                data.vehiculos.forEach(vehiculo => {
                    const option = document.createElement('option');
                    option.value = vehiculo.id;
                    option.textContent = `${vehiculo.marca} ${vehiculo.modelo} (${vehiculo.año}) - ${vehiculo.patente}`;
                    option.dataset.vehiculoData = JSON.stringify(vehiculo);
                    vehiculoSelect.appendChild(option);
                });
                
                // Agregar event listener para mostrar info del vehículo
                vehiculoSelect.addEventListener('change', function() {
                    if (this.value) {
                        const vehiculoData = JSON.parse(this.selectedOptions[0].dataset.vehiculoData);
                        showVehicleInfo(vehiculoData);
                    } else {
                        hideVehicleInfo();
                    }
                });
                
            } else {
                vehiculoSelect.innerHTML = '<option value="">This client has no registered vehicles</option>';
            }
        })
        .catch(error => {
            console.error('Error cargando vehículos:', error);
            vehiculoSelect.innerHTML = '<option value="">Error loading vehicles</option>';
        });
}

// ========================================
// 4. INFORMACIÓN DEL VEHÍCULO CON MILEAGE/KILOMETRAJE
// ========================================

function showVehicleInfo(vehiculo) {
    const vehicleInfoDiv = document.getElementById('vehicle-info');
    const yearInput = document.getElementById('vehicle-year');
    const modelInput = document.getElementById('vehicle-model');
    const mileageInput = document.getElementById('vehicle-mileage');
    
    if (!vehicleInfoDiv) return;
    
    // Llenar información del vehículo
    yearInput.value = vehiculo.año || '';
    modelInput.value = `${vehiculo.marca} ${vehiculo.modelo}` || '';
    mileageInput.value = vehiculo.kilometraje || vehiculo.millas || '';
    
    // Mostrar el contenedor
    vehicleInfoDiv.classList.remove('hidden');
    
    currentVehicle = vehiculo;
}

function hideVehicleInfo() {
    const vehicleInfoDiv = document.getElementById('vehicle-info');
    if (vehicleInfoDiv) {
        vehicleInfoDiv.classList.add('hidden');
    }
    currentVehicle = null;
}

// ========================================
// 5. BÚSQUEDA RÁPIDA DE REPUESTOS
// ========================================

function initRepuestoSearch() {
    const searchInput = document.getElementById('quick-rep-search');
    const resultsContainer = document.getElementById('quick-rep-results');
    
    if (!searchInput) return;
    
    let repSearchTimeout = null;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }
        
        clearTimeout(repSearchTimeout);
        repSearchTimeout = setTimeout(() => {
            searchRepuestos(query);
        }, 300);
    });
    
    // Ocultar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.classList.add('hidden');
        }
    });
}

function searchRepuestos(query) {
    const resultsContainer = document.getElementById('quick-rep-results');
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/repuestos/search/?q=${encodeURIComponent(query)}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.repuestos && data.repuestos.length > 0) {
                displayRepuestoResults(data.repuestos);
            } else {
                resultsContainer.innerHTML = '<div class="p-3 text-gray-400">No parts found</div>';
                resultsContainer.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error buscando repuestos:', error);
            resultsContainer.innerHTML = '<div class="p-3 text-red-400">Search error</div>';
            resultsContainer.classList.remove('hidden');
        });
}

function displayRepuestoResults(repuestos) {
    const resultsContainer = document.getElementById('quick-rep-results');
    
    const html = repuestos.map(repuesto => `
        <div class="p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-600 last:border-b-0 repuesto-result-item" 
             data-repuesto-id="${repuesto.id}"
             data-repuesto-nombre="${repuesto.nombre}"
             data-repuesto-codigo="${repuesto.codigo || ''}"
             data-repuesto-precio="${repuesto.precio || 0}">
            <div class="font-medium text-white">${repuesto.nombre}</div>
            <div class="text-sm text-gray-400">Código: ${repuesto.codigo || 'Sin código'}</div>
            <div class="text-sm text-green-400">Precio: $${parseFloat(repuesto.precio || 0).toLocaleString()}</div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.remove('hidden');
    
    // Agregar event listeners
    resultsContainer.querySelectorAll('.repuesto-result-item').forEach(item => {
        item.addEventListener('click', function() {
            addRepuestoFromSearch(this.dataset);
            resultsContainer.classList.add('hidden');
        });
    });
}

function addRepuestoFromSearch(repuestoData) {
    // Esta función debería integrarse con el sistema existente de agregar repuestos
    console.log('Agregando repuesto:', repuestoData);
    
    // Aquí deberías llamar a la función existente que agrega repuestos
    // Por ejemplo: addRepuestoLine(repuestoData);
    
    // Limpiar el campo de búsqueda
    document.getElementById('quick-rep-search').value = '';
}

// ========================================
// 6. BÚSQUEDA RÁPIDA DE SERVICIOS
// ========================================

function initServicioSearch() {
    const searchInput = document.getElementById('quick-serv-search');
    const resultsContainer = document.getElementById('quick-serv-results');
    
    if (!searchInput) return;
    
    let servSearchTimeout = null;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }
        
        clearTimeout(servSearchTimeout);
        servSearchTimeout = setTimeout(() => {
            searchServicios(query);
        }, 300);
    });
    
    // Ocultar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.classList.add('hidden');
        }
    });
}

function searchServicios(query) {
    const resultsContainer = document.getElementById('quick-serv-results');
    
    // Detectar país desde la URL
    const countryPrefix = window.location.pathname.startsWith('/us/') ? 'us' : 'cl';
    const apiUrl = `/${countryPrefix}/documentos/api/servicios/search/?q=${encodeURIComponent(query)}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.servicios && data.servicios.length > 0) {
                displayServicioResults(data.servicios);
            } else {
                resultsContainer.innerHTML = '<div class="p-3 text-gray-400">No services found</div>';
                resultsContainer.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error buscando servicios:', error);
            resultsContainer.innerHTML = '<div class="p-3 text-red-400">Search error</div>';
            resultsContainer.classList.remove('hidden');
        });
}

function displayServicioResults(servicios) {
    const resultsContainer = document.getElementById('quick-serv-results');
    
    const html = servicios.map(servicio => `
        <div class="p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-600 last:border-b-0 servicio-result-item" 
             data-servicio-id="${servicio.id}"
             data-servicio-nombre="${servicio.nombre}"
             data-servicio-codigo="${servicio.codigo || ''}"
             data-servicio-precio="${servicio.precio || 0}">
            <div class="font-medium text-white">${servicio.nombre}</div>
            <div class="text-sm text-gray-400">Código: ${servicio.codigo || 'Sin código'}</div>
            <div class="text-sm text-green-400">Precio: $${parseFloat(servicio.precio || 0).toLocaleString()}</div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.remove('hidden');
    
    // Agregar event listeners
    resultsContainer.querySelectorAll('.servicio-result-item').forEach(item => {
        item.addEventListener('click', function() {
            addServicioFromSearch(this.dataset);
            resultsContainer.classList.add('hidden');
        });
    });
}

function addServicioFromSearch(servicioData) {
    console.log('Agregando servicio:', servicioData);
    
    // Limpiar el campo de búsqueda
    document.getElementById('quick-serv-search').value = '';
}

// ========================================
// 7. INICIALIZACIÓN
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing advanced document form functionalities');
    
    // 1. Generación automática de número de documento
    updateDocumentNumber();
    
    // Event listeners para los botones de tipo de documento
    const tipoButtons = document.querySelectorAll('.btn-type');
    const tipoInput = document.getElementById('tipo');
    
    tipoButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remover clase active de todos los botones
            tipoButtons.forEach(btn => btn.classList.remove('active'));
            // Agregar clase active al botón clickeado
            this.classList.add('active');
            
            // Actualizar el valor del input hidden
            const tipo = this.dataset.tipo;
            if (tipoInput) {
                tipoInput.value = tipo;
            }
            
            // Actualizar el número de documento
            updateDocumentNumber();
        });
    });
    
    // Event listener para el input hidden (fallback)
    if (tipoInput) {
        tipoInput.addEventListener('change', updateDocumentNumber);
    }
    
    // 2. Búsqueda de clientes
    initClientSearch();
    
    // 3. Búsqueda de repuestos
    initRepuestoSearch();
    
    // 4. Búsqueda de servicios
    initServicioSearch();
    
    console.log('✅ Advanced functionalities initialized');
});

// ========================================
// 8. FUNCIONES UTILITARIAS
// ========================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Exportar funciones para uso global
window.DocumentFormAdvanced = {
    updateDocumentNumber,
    searchClients,
    selectClient,
    loadClientVehicles,
    showVehicleInfo,
    searchRepuestos,
    searchServicios,
    filterVehiclesByClient
};

// Exportar función principal globalmente
window.updateDocumentNumber = updateDocumentNumber;

// ========================================
// 8. FILTRADO DE VEHÍCULOS POR CLIENTE
// ========================================

function filterVehiclesByClient() {
    const clienteSelect = document.getElementById('id_cliente');
    const vehiculoSelect = document.getElementById('id_vehiculo');
    
    if (!clienteSelect || !vehiculoSelect) {
        console.log('⚠️ No se encontraron elementos cliente o vehículo');
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
    if (clienteSelect.value) {
        loadVehiclesByClient(clienteSelect.value);
    }
}

function loadVehiclesByClient(clienteId) {
    const vehiculoSelect = document.getElementById('id_vehiculo');
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
    const vehiculoSelect = document.getElementById('id_vehiculo');
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

// Inicializar filtrado de vehículos cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    filterVehiclesByClient();
});
