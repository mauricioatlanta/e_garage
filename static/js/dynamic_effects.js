// ===== EFECTOS DINÁMICOS ESPACIALES - GEORGE AUTO REPAIR =====
// JavaScript para crear partículas, explosiones y efectos interactivos
// Sistema de gestión para George Auto Repair

class DynamicEffects {
  constructor() {
    this.particles = [];
    this.explosions = [];
    this.isInitialized = false;
  }

  // Inicializar efectos dinámicos
  init() {
    if (this.isInitialized) return;
    
    this.createParticles();
    this.createRandomExplosions();
    this.setupEventListeners();
    
    this.isInitialized = true;
  }

  // Crear partículas flotantes
  createParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    for (let i = 0; i < 50; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.top = Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 3 + 's';
      particlesContainer.appendChild(particle);
    }
  }

  // Crear explosiones aleatorias
  createRandomExplosions() {
    setInterval(() => {
      const x = Math.random() * window.innerWidth;
      const y = Math.random() * window.innerHeight;
      this.createExplosion(x, y);
    }, 3000);
  }

  // Crear explosión en coordenadas específicas
  createExplosion(x, y) {
    const explosion = document.createElement('div');
    explosion.className = 'explosion';
    explosion.style.left = x + 'px';
    explosion.style.top = y + 'px';
    document.body.appendChild(explosion);
    
    setTimeout(() => {
      explosion.remove();
    }, 500);
  }

  // Configurar event listeners
  setupEventListeners() {
    // Efectos en tarjetas
    const cards = document.querySelectorAll('.futuristic-card');
    cards.forEach(card => {
      card.addEventListener('click', (e) => {
        if (!e.target.closest('a') && !e.target.closest('button')) {
          const rect = card.getBoundingClientRect();
          this.createExplosion(
            e.clientX - rect.left,
            e.clientY - rect.top
          );
        }
      });
    });

    // Efectos en botones
    const buttons = document.querySelectorAll('.futuristic-btn');
    buttons.forEach(button => {
      button.addEventListener('click', (e) => {
        const rect = button.getBoundingClientRect();
        this.createExplosion(
          e.clientX - rect.left,
          e.clientY - rect.top
        );
      });
    });
  }
}

// ===== FUNCIONES DE BÚSQUEDA Y FILTRADO =====
class SearchAndFilter {
  constructor() {
    this.searchInput = null;
    this.searchBtn = null;
    this.filters = [];
    this.items = [];
    this.isInitialized = false;
  }

  // Inicializar búsqueda y filtros
  init(selectors) {
    if (this.isInitialized) return;

    this.searchInput = document.querySelector(selectors.searchInput);
    this.searchBtn = document.querySelector(selectors.searchBtn);
    this.filters = document.querySelectorAll(selectors.filters);
    this.items = document.querySelectorAll(selectors.items);

    this.setupEventListeners();
    this.isInitialized = true;
  }

  // Configurar event listeners
  setupEventListeners() {
    if (this.searchInput) {
      this.searchInput.addEventListener('input', () => this.performSearch());
      this.searchInput.addEventListener('focus', () => this.handleFocus());
      this.searchInput.addEventListener('blur', () => this.handleBlur());
    }

    if (this.searchBtn) {
      this.searchBtn.addEventListener('click', () => this.performSearch());
    }

    this.filters.forEach(filter => {
      filter.addEventListener('change', () => this.performSearch());
    });
  }

  // Realizar búsqueda
  performSearch() {
    const query = this.searchInput ? this.searchInput.value.toLowerCase().trim() : '';
    const filterValues = this.getFilterValues();
    
    this.items.forEach(item => {
      const matches = this.itemMatches(item, query, filterValues);
      this.updateItemVisibility(item, matches);
    });
  }

  // Obtener valores de filtros
  getFilterValues() {
    const values = {};
    this.filters.forEach(filter => {
      if (filter.value) {
        values[filter.name || filter.id] = filter.value;
      }
    });
    return values;
  }

  // Verificar si un item coincide con la búsqueda
  itemMatches(item, query, filterValues) {
    const data = item.dataset;
    
    // Búsqueda por texto
    const textMatches = !query || 
      (data.name && data.name.toLowerCase().includes(query)) ||
      (data.category && data.category.toLowerCase().includes(query)) ||
      (data.subcategory && data.subcategory.toLowerCase().includes(query));

    // Filtros
    const filterMatches = Object.keys(filterValues).every(key => {
      const filterValue = filterValues[key];
      const itemValue = data[key] || data[key + 'Code'];
      return !filterValue || itemValue === filterValue;
    });

    return textMatches && filterMatches;
  }

  // Actualizar visibilidad del item
  updateItemVisibility(item, matches) {
    if (matches) {
      item.style.display = 'block';
      item.style.opacity = '1';
      item.style.transform = 'scale(1)';
    } else {
      item.style.opacity = '0.3';
      item.style.transform = 'scale(0.95)';
    }
  }

  // Manejar focus del input
  handleFocus() {
    if (this.searchInput) {
      this.searchInput.parentElement.style.borderColor = 'rgb(34 211 238 / 0.6)';
    }
  }

  // Manejar blur del input
  handleBlur() {
    if (this.searchInput) {
      this.searchInput.parentElement.style.borderColor = 'rgb(34 211 238 / 0.3)';
    }
  }
}

// ===== FUNCIONES DE MODAL =====
class FuturisticModal {
  constructor() {
    this.modal = null;
    this.isInitialized = false;
  }

  // Inicializar modal
  init(modalSelector) {
    if (this.isInitialized) return;

    this.modal = document.querySelector(modalSelector);
    if (!this.modal) return;

    this.setupEventListeners();
    this.isInitialized = true;
  }

  // Configurar event listeners
  setupEventListeners() {
    // Cerrar con Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.close();
      }
    });

    // Cerrar al hacer clic fuera
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });
  }

  // Abrir modal
  open(content = {}) {
    if (!this.modal) return;

    // Actualizar contenido si se proporciona
    if (content.title) {
      const titleEl = this.modal.querySelector('.modal-title');
      if (titleEl) titleEl.textContent = content.title;
    }

    if (content.message) {
      const messageEl = this.modal.querySelector('.modal-message');
      if (messageEl) messageEl.textContent = content.message;
    }

    if (content.itemName) {
      const nameEl = this.modal.querySelector('.item-name');
      if (nameEl) nameEl.textContent = content.itemName;
    }

    this.modal.classList.add('show');
  }

  // Cerrar modal
  close() {
    if (!this.modal) return;
    this.modal.classList.remove('show');
  }

  // Configurar callback de eliminación
  setupDeleteCallback(callback) {
    const deleteBtn = this.modal.querySelector('.delete-btn');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', callback);
    }
  }
}

// ===== INICIALIZACIÓN GLOBAL =====
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar efectos dinámicos
  const dynamicEffects = new DynamicEffects();
  dynamicEffects.init();

  // Inicializar búsqueda y filtros si existen elementos
  const searchAndFilter = new SearchAndFilter();
  const searchSelectors = {
    searchInput: '#searchInput',
    searchBtn: '#searchBtn',
    filters: '.futuristic-filters select',
    items: '.futuristic-card'
  };
  
  if (document.querySelector(searchSelectors.searchInput) || 
      document.querySelector(searchSelectors.items)) {
    searchAndFilter.init(searchSelectors);
  }

  // Inicializar modal si existe
  const modal = new FuturisticModal();
  const modalSelector = '#futuristicModal';
  if (document.querySelector(modalSelector)) {
    modal.init(modalSelector);
  }

  // Hacer disponibles globalmente
  window.DynamicEffects = DynamicEffects;
  window.SearchAndFilter = SearchAndFilter;
  window.FuturisticModal = FuturisticModal;
  window.dynamicEffects = dynamicEffects;
  window.searchAndFilter = searchAndFilter;
  window.futuristicModal = modal;
});

// ===== FUNCIONES GLOBALES PARA TEMPLATES =====

// Función para confirmar eliminación
window.confirmarEliminacion = function(id, nombre, url) {
  if (window.futuristicModal) {
    window.futuristicModal.open({
      title: 'Confirmar Eliminación',
      message: '¿Está seguro de que desea eliminar',
      itemName: nombre
    });

    window.futuristicModal.setupDeleteCallback(() => {
      eliminarItem(id, url);
    });
  } else {
    // Fallback a confirm nativo
    if (confirm(`¿Está seguro de que desea eliminar "${nombre}"?`)) {
      eliminarItem(id, url);
    }
  }
};

// Función para eliminar item
function eliminarItem(id, url) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json',
    },
  })
  .then(response => {
    if (response.ok) {
      window.location.reload();
    } else {
      alert('Error al eliminar el elemento');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al eliminar el elemento');
  });
}

// Función para cerrar modal
window.cerrarModal = function() {
  if (window.futuristicModal) {
    window.futuristicModal.close();
  }
};
