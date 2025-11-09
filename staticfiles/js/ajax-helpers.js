// AJAX Helpers para eGarage
// Usa los endpoints dinámicos definidos en el template

// Verificar que los endpoints estén disponibles
if (typeof window.AJAX_ENDPOINTS === 'undefined') {
  console.error('⚠️ AJAX_ENDPOINTS no está definido. Asegúrate de incluir ajax_endpoints.html en tu template.');
}

// Helper para buscar clientes
async function buscarClientes(q) {
  if (!window.AJAX_ENDPOINTS?.buscarClientes) {
    console.error('❌ Endpoint buscarClientes no disponible');
    return [];
  }

  const url = `${window.AJAX_ENDPOINTS.buscarClientes}?q=${encodeURIComponent(q)}`;
  console.log("🔍 Buscando clientes con:", q, "URL:", url);

  try {
    const resp = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!resp.ok) {
      console.error("❌ Error HTTP:", resp.status, resp.statusText);
      return [];
    }

    const data = await resp.json();
    console.log("📡 Respuesta:", data);
    return data.results || [];
  } catch (error) {
    console.error("❌ Error en fetch:", error);
    return [];
  }
}

// Helper para obtener vehículos por cliente
async function vehiculosPorCliente(clienteId) {
  if (!window.AJAX_ENDPOINTS?.vehiculosPorCliente) {
    console.error('❌ Endpoint vehiculosPorCliente no disponible');
    return [];
  }

  const url = `${window.AJAX_ENDPOINTS.vehiculosPorCliente}?cliente=${clienteId}`;
  console.log("🚗 Buscando vehículos para cliente:", clienteId, "URL:", url);

  try {
    const resp = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!resp.ok) {
      console.error("❌ Error HTTP:", resp.status, resp.statusText);
      return [];
    }

    const data = await resp.json();
    console.log("📡 Respuesta:", data);
    return data.results || [];
  } catch (error) {
    console.error("❌ Error en fetch:", error);
    return [];
  }
}

// Helper para ciudades por región
async function ciudadesPorRegion(pais, region) {
  if (!window.AJAX_ENDPOINTS?.ciudadesPorRegion) {
    console.error('❌ Endpoint ciudadesPorRegion no disponible');
    return [];
  }

  const url = `${window.AJAX_ENDPOINTS.ciudadesPorRegion}?pais=${pais}&region=${region}`;
  console.log("🌍 Buscando ciudades para:", pais, region, "URL:", url);

  try {
    const resp = await fetch(url, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    if (!resp.ok) {
      console.error("❌ Error HTTP:", resp.status, resp.statusText);
      return [];
    }

    const data = await resp.json();
    console.log("📡 Respuesta:", data);
    return data.ciudades || [];
  } catch (error) {
    console.error("❌ Error en fetch:", error);
    return [];
  }
}

// Debounce helper
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
window.egarageAjax = {
  buscarClientes,
  vehiculosPorCliente,
  ciudadesPorRegion,
  debounce
};
