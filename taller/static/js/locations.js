/**
 * locations.js - Manejador unificado para Country → State → City
 * 
 * Versión 2.0 - Con cache, debounce y abort controller
 * 
 * Mejoras:
 * - Cache en memoria del navegador (evita llamadas repetidas)
 * - Debounce de 200ms (UX suave)
 * - AbortController para cancelar fetches si usuario cambia rápido
 * 
 * Uso:
 *   import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
 *   bindCountryStateCity('#id_country', '#id_state', '#id_city');
 * 
 * Soporta: Chile, USA, Brasil, Perú, Venezuela
 * API: /api/locations?country=XX&state=YY
 */

// ============================================================================
// CACHE SIMPLE EN MEMORIA
// ============================================================================

/**
 * Cache simple para estados y ciudades
 * Key format: 
 *   - States: "states:COUNTRY"
 *   - Cities: "cities:COUNTRY:STATE"
 */
const locationsCache = new Map();

/**
 * Obtener del cache
 */
function getCached(key) {
  return locationsCache.get(key) || null;
}

/**
 * Guardar en cache
 */
function setCache(key, value) {
  locationsCache.set(key, value);
}

/**
 * Limpiar cache (útil para testing o refresh)
 */
export function clearLocationsCache() {
  locationsCache.clear();
  console.log('[locations.js] Cache cleared');
}

// ============================================================================
// DEBOUNCE UTILITY
// ============================================================================

/**
 * Debounce para evitar llamadas excesivas
 * 
 * @param {Function} func - Función a ejecutar
 * @param {number} wait - Tiempo de espera en ms (default: 200)
 * @returns {Function} Función con debounce
 */
function debounce(func, wait = 200) {
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

// ============================================================================
// FETCH CON ABORT CONTROLLER
// ============================================================================

/**
 * Helper para fetch con credenciales y abort controller
 * 
 * @param {string} url - URL a consultar
 * @param {AbortSignal} signal - Señal de abort (opcional)
 * @returns {Promise<object>} - JSON response
 */
async function fetchJSON(url, signal = null) {
  const options = { 
    credentials: 'same-origin'
  };
  
  if (signal) {
    options.signal = signal;
  }
  
  const r = await fetch(url, options);
  
  if (!r.ok) {
    throw new Error(`HTTP ${r.status}: ${r.statusText}`);
  }
  
  return r.json();
}

// ============================================================================
// BIND PRINCIPAL CON CACHE, DEBOUNCE Y ABORT
// ============================================================================

/**
 * Bind automático de selectores Country → State → City
 * Con cache, debounce y abort controller para UX óptima
 * 
 * @param {string} countrySel - Selector CSS para país (ej: '#id_country')
 * @param {string} stateSel - Selector CSS para estado (ej: '#id_state')
 * @param {string} citySel - Selector CSS para ciudad (ej: '#id_city')
 * @param {object} options - Opciones adicionales
 * @param {string} options.loadingText - Texto mientras carga (default: "Loading...")
 * @param {string} options.emptyText - Texto para opción vacía (default: "--")
 * @param {boolean} options.debug - Activar logs de debug (default: false)
 * @param {number} options.debounceMs - Tiempo de debounce en ms (default: 200)
 * 
 * @example
 * // Básico
 * bindCountryStateCity('#id_country', '#id_state', '#id_city');
 * 
 * @example
 * // Con opciones personalizadas
 * bindCountryStateCity('#id_country', '#id_state', '#id_city', {
 *   loadingText: 'Cargando...',
 *   emptyText: 'Seleccione...',
 *   debug: true,
 *   debounceMs: 150
 * });
 */
export async function bindCountryStateCity(countrySel, stateSel, citySel, options = {}) {
  const $country = document.querySelector(countrySel);
  const $state = document.querySelector(stateSel);
  const $city = document.querySelector(citySel);
  
  // Validar que los elementos existan
  if (!$country || !$state || !$city) {
    console.warn('[locations.js] No se encontraron todos los selectores:', {
      country: !!$country,
      state: !!$state,
      city: !!$city
    });
    return;
  }
  
  // Opciones por defecto
  const {
    loadingText = 'Loading...',
    emptyText = '--',
    debug = false,
    debounceMs = 200  // ✅ 200ms por defecto (150-250ms recomendado)
  } = options;
  
  const log = (...args) => debug && console.log('[locations.js]', ...args);
  
  // ============================================================================
  // ABORT CONTROLLERS
  // ============================================================================
  
  let statesAbortController = null;
  let citiesAbortController = null;
  
  /**
   * Cargar estados/departamentos del país seleccionado
   * Con cache y abort controller
   */
  async function loadStates() {
    const country = ($country.value || '').toUpperCase();
    
    // Cancelar fetch anterior si existe
    if (statesAbortController) {
      statesAbortController.abort();
      log('Aborted previous states fetch');
    }
    
    // Limpiar selects dependientes
    $state.innerHTML = `<option value="">${emptyText}</option>`;
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    $state.disabled = true;
    $city.disabled = true;
    
    if (!country) {
      log('No country selected');
      return;
    }
    
    // ✅ Verificar cache primero
    const cacheKey = `states:${country}`;
    const cached = getCached(cacheKey);
    
    if (cached) {
      log(`Loaded ${cached.length} states from CACHE for ${country}`);
      populateStatesSelect(cached);
      return;
    }
    
    // Fetch desde API con abort controller
    log('Loading states for country:', country);
    $state.innerHTML = `<option value="">${loadingText}</option>`;
    
    // ✅ Crear nuevo AbortController
    statesAbortController = new AbortController();
    
    try {
      const data = await fetchJSON(
        `/api/locations?country=${country}`,
        statesAbortController.signal  // ✅ Pasar signal
      );
      
      const states = data.states || [];
      log(`Loaded ${states.length} states for ${country}`);
      
      // ✅ Guardar en cache
      setCache(cacheKey, states);
      
      populateStatesSelect(states);
      
    } catch (error) {
      // ✅ Ignorar errores de abort (usuario cambió rápido)
      if (error.name === 'AbortError') {
        log('States fetch aborted (user changed selection)');
        return;
      }
      
      console.error('[locations.js] Error loading states:', error);
      $state.innerHTML = `<option value="">Error loading states</option>`;
    }
  }
  
  /**
   * Poblar select de estados
   */
  function populateStatesSelect(states) {
    $state.innerHTML = `<option value="">${emptyText}</option>`;
    
    states.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.code || s.id;
      opt.dataset.stateId = s.id;
      opt.dataset.stateCode = s.code || '';
      opt.textContent = s.name;
      $state.appendChild(opt);
    });
    
    $state.disabled = false;
    
    // Si hay un valor pre-seleccionado en state, cargar ciudades
    if ($state.value) {
      loadCities();  // No await, se ejecuta con debounce
    }
  }
  
  /**
   * Cargar ciudades del estado seleccionado
   * Con cache y abort controller
   */
  async function loadCities() {
    const country = ($country.value || '').toUpperCase();
    const state = ($state.value || '').toUpperCase();
    
    // Cancelar fetch anterior si existe
    if (citiesAbortController) {
      citiesAbortController.abort();
      log('Aborted previous cities fetch');
    }
    
    // Limpiar ciudades
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    $city.disabled = true;
    
    if (!country || !state) {
      log('Country or state not selected');
      return;
    }
    
    // ✅ Verificar cache primero
    const cacheKey = `cities:${country}:${state}`;
    const cached = getCached(cacheKey);
    
    if (cached) {
      log(`Loaded ${cached.length} cities from CACHE for ${country}-${state}`);
      populateCitiesSelect(cached);
      return;
    }
    
    // Fetch desde API con abort controller
    log('Loading cities for:', country, state);
    $city.innerHTML = `<option value="">${loadingText}</option>`;
    
    // ✅ Crear nuevo AbortController
    citiesAbortController = new AbortController();
    
    try {
      const data = await fetchJSON(
        `/api/locations?country=${country}&state=${state}`,
        citiesAbortController.signal  // ✅ Pasar signal
      );
      
      const cities = data.cities || [];
      log(`Loaded ${cities.length} cities for ${country}-${state}`);
      
      // ✅ Guardar en cache
      setCache(cacheKey, cities);
      
      populateCitiesSelect(cities);
      
    } catch (error) {
      // ✅ Ignorar errores de abort
      if (error.name === 'AbortError') {
        log('Cities fetch aborted (user changed selection)');
        return;
      }
      
      console.error('[locations.js] Error loading cities:', error);
      $city.innerHTML = `<option value="">Error loading cities</option>`;
    }
  }
  
  /**
   * Poblar select de ciudades
   */
  function populateCitiesSelect(cities) {
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    
    cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      $city.appendChild(opt);
    });
    
    $city.disabled = false;
  }
  
  // ============================================================================
  // EVENT LISTENERS CON DEBOUNCE
  // ============================================================================
  
  // ✅ Aplicar debounce a loadStates y loadCities
  const debouncedLoadStates = debounce(loadStates, debounceMs);
  const debouncedLoadCities = debounce(loadCities, debounceMs);
  
  // Event listeners
  $country.addEventListener('change', debouncedLoadStates);
  $state.addEventListener('change', debouncedLoadCities);
  
  // Inicialización: Si ya hay un país seleccionado, cargar estados
  if ($country.value) {
    log('Init: Country pre-selected, loading states');
    await loadStates();  // Init sin debounce
  }
}

// ============================================================================
// VERSIÓN ALTERNATIVA POR IDs
// ============================================================================

/**
 * Versión alternativa usando IDs de estado en lugar de códigos
 * Con cache, debounce y abort controller
 * 
 * Útil cuando se trabaja directamente con ForeignKeys
 */
export async function bindCountryStateCity_ByIds(countrySel, stateSel, citySel, options = {}) {
  const $country = document.querySelector(countrySel);
  const $state = document.querySelector(stateSel);
  const $city = document.querySelector(citySel);
  
  if (!$country || !$state || !$city) return;
  
  const {
    loadingText = 'Loading...',
    emptyText = '--',
    debug = false,
    debounceMs = 200
  } = options;
  
  const log = (...args) => debug && console.log('[locations.js ByIds]', ...args);
  
  let statesAbortController = null;
  let citiesAbortController = null;
  
  /**
   * Cargar estados usando endpoint REST
   */
  async function loadStates() {
    const country = ($country.value || '').toUpperCase();
    
    // Cancelar fetch anterior
    if (statesAbortController) {
      statesAbortController.abort();
    }
    
    $state.innerHTML = `<option value="">${emptyText}</option>`;
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    $state.disabled = true;
    $city.disabled = true;
    
    if (!country) return;
    
    // ✅ Cache
    const cacheKey = `states_byid:${country}`;
    const cached = getCached(cacheKey);
    
    if (cached) {
      log(`Loaded ${cached.length} states from CACHE for ${country}`);
      populateStatesSelect(cached);
      return;
    }
    
    log('Loading states for country:', country);
    $state.innerHTML = `<option value="">${loadingText}</option>`;
    
    statesAbortController = new AbortController();
    
    try {
      const data = await fetchJSON(
        `/api/locations/states/${country}/`,
        statesAbortController.signal
      );
      
      const states = data.states || [];
      log(`Loaded ${states.length} states for ${country}`);
      
      setCache(cacheKey, states);
      populateStatesSelect(states);
      
    } catch (error) {
      if (error.name === 'AbortError') {
        log('States fetch aborted');
        return;
      }
      
      console.error('[locations.js] Error loading states:', error);
      $state.innerHTML = `<option value="">Error loading states</option>`;
    }
  }
  
  function populateStatesSelect(states) {
    $state.innerHTML = `<option value="">${emptyText}</option>`;
    
    states.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;  // Usar ID directamente
      opt.textContent = s.name;
      opt.dataset.code = s.code;
      opt.dataset.salesTax = s.sales_tax || 0;
      $state.appendChild(opt);
    });
    
    $state.disabled = false;
    
    if ($state.value) {
      loadCities();
    }
  }
  
  /**
   * Cargar ciudades usando endpoint REST
   */
  async function loadCities() {
    const stateId = $state.value;
    
    // Cancelar fetch anterior
    if (citiesAbortController) {
      citiesAbortController.abort();
    }
    
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    $city.disabled = true;
    
    if (!stateId) return;
    
    // ✅ Cache
    const cacheKey = `cities_byid:${stateId}`;
    const cached = getCached(cacheKey);
    
    if (cached) {
      log(`Loaded ${cached.length} cities from CACHE for state ${stateId}`);
      populateCitiesSelect(cached);
      return;
    }
    
    log('Loading cities for state ID:', stateId);
    $city.innerHTML = `<option value="">${loadingText}</option>`;
    
    citiesAbortController = new AbortController();
    
    try {
      const data = await fetchJSON(
        `/api/locations/cities/${stateId}/`,
        citiesAbortController.signal
      );
      
      const cities = data.cities || [];
      log(`Loaded ${cities.length} cities for state ${stateId}`);
      
      setCache(cacheKey, cities);
      populateCitiesSelect(cities);
      
    } catch (error) {
      if (error.name === 'AbortError') {
        log('Cities fetch aborted');
        return;
      }
      
      console.error('[locations.js] Error loading cities:', error);
      $city.innerHTML = `<option value="">Error loading cities</option>`;
    }
  }
  
  function populateCitiesSelect(cities) {
    $city.innerHTML = `<option value="">${emptyText}</option>`;
    
    cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      $city.appendChild(opt);
    });
    
    $city.disabled = false;
  }
  
  // Event listeners con debounce
  const debouncedLoadStates = debounce(loadStates, debounceMs);
  const debouncedLoadCities = debounce(loadCities, debounceMs);
  
  $country.addEventListener('change', debouncedLoadStates);
  $state.addEventListener('change', debouncedLoadCities);
  
  // Inicialización
  if ($country.value) {
    log('Init: Country pre-selected, loading states');
    await loadStates();  // Sin debounce en init
  }
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Helper para detectar país desde URL o contexto
 */
export function detectCountryFromPath() {
  const path = window.location.pathname;
  
  if (path.includes('/us/')) return 'US';
  if (path.includes('/br/')) return 'BR';
  if (path.includes('/cl/')) return 'CL';
  if (path.includes('/pe/')) return 'PE';
  if (path.includes('/ve/')) return 'VE';
  
  return null;
}

/**
 * Helper para auto-seleccionar país basado en URL
 */
export function autoSelectCountryFromPath(countrySel) {
  const country = detectCountryFromPath();
  if (country) {
    const $country = document.querySelector(countrySel);
    if ($country && !$country.value) {
      $country.value = country;
      $country.dispatchEvent(new Event('change'));
      return country;
    }
  }
  return null;
}

/**
 * Precarga de estados para un país (útil para mejorar UX)
 * 
 * @param {string} country - Código de país (CL, US, BR, PE, VE)
 * 
 * @example
 * // Precargar estados de Perú al cargar la página
 * preloadStates('PE');
 */
export async function preloadStates(country) {
  const cacheKey = `states:${country.toUpperCase()}`;
  
  // Si ya está en cache, no hacer nada
  if (getCached(cacheKey)) {
    console.log(`[locations.js] States for ${country} already in cache`);
    return;
  }
  
  try {
    const data = await fetchJSON(`/api/locations?country=${country.toUpperCase()}`);
    const states = data.states || [];
    setCache(cacheKey, states);
    console.log(`[locations.js] Preloaded ${states.length} states for ${country}`);
  } catch (error) {
    console.error(`[locations.js] Error preloading states for ${country}:`, error);
  }
}

/**
 * Precarga de ciudades para un estado (útil para UX)
 * 
 * @param {string} country - Código de país
 * @param {string} state - Código de estado
 */
export async function preloadCities(country, state) {
  const cacheKey = `cities:${country.toUpperCase()}:${state.toUpperCase()}`;
  
  if (getCached(cacheKey)) {
    console.log(`[locations.js] Cities for ${country}-${state} already in cache`);
    return;
  }
  
  try {
    const data = await fetchJSON(`/api/locations?country=${country.toUpperCase()}&state=${state.toUpperCase()}`);
    const cities = data.cities || [];
    setCache(cacheKey, cities);
    console.log(`[locations.js] Preloaded ${cities.length} cities for ${country}-${state}`);
  } catch (error) {
    console.error(`[locations.js] Error preloading cities for ${country}-${state}:`, error);
  }
}

/**
 * Estadísticas del cache (útil para debugging)
 */
export function getCacheStats() {
  const stats = {
    size: locationsCache.size,
    keys: Array.from(locationsCache.keys()),
    totalItems: 0
  };
  
  locationsCache.forEach((value, key) => {
    if (Array.isArray(value)) {
      stats.totalItems += value.length;
    }
  });
  
  return stats;
}

// ============================================================================
// EXPORT DEFAULT
// ============================================================================

export default {
  bindCountryStateCity,
  bindCountryStateCity_ByIds,
  detectCountryFromPath,
  autoSelectCountryFromPath,
  preloadStates,
  preloadCities,
  clearLocationsCache,
  getCacheStats
};
