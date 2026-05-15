/**
 * Landing Page Chile - JavaScript para animaciones y tracking
 * Optimizado para conversión
 */

// Crear partículas flotantes
function createParticles() {
  const particlesContainer = document.getElementById('particles');
  if (!particlesContainer) return;

  const particleCount = 30; // Reducido para mejor performance

  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 15 + 's';
    particle.style.animationDuration = (15 + Math.random() * 10) + 's';
    particlesContainer.appendChild(particle);
  }
}

// Animaciones de entrada
function animateOnScroll() {
  const elements = document.querySelectorAll('[data-animate]');

  elements.forEach(element => {
    const elementTop = element.getBoundingClientRect().top;
    const elementVisible = 150;

    if (elementTop < window.innerHeight - elementVisible) {
      element.classList.add('animate');
    }
  });
}

// Efecto parallax para el fondo
function parallaxEffect() {
  const scrolled = window.pageYOffset;
  const parallax = document.querySelector('.futuristic-bg');
  const speed = scrolled * 0.3; // Reducido para mejor performance

  if (parallax) {
    parallax.style.transform = `translateY(${speed}px)`;
  }
}

// Tracking de eventos
function trackEvent(eventName, element) {
  // Enviar evento a Google Analytics si está disponible
  if (typeof gtag !== 'undefined') {
    gtag('event', eventName, {
      'event_category': 'Landing Chile',
      'event_label': element ? element.textContent : '',
      'value': 1
    });
  }

  // Log local para debugging
  console.log('Event tracked:', eventName, element ? element.textContent : '');

  // Aquí puedes agregar más servicios de tracking
  // Ejemplo: Facebook Pixel, Mixpanel, etc.
}

// Smooth scroll para enlaces internos
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        const offsetTop = target.offsetTop - 80; // Ajustar por navegación fija
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }
    });
  });
}

// Tracking de CTAs
function initCTATracking() {
  document.querySelectorAll('[data-track]').forEach(element => {
    element.addEventListener('click', function() {
      const trackName = this.getAttribute('data-track');
      trackEvent(trackName, this);
    });
  });
}

// Efectos hover mejorados
function initHoverEffects() {
  document.querySelectorAll('.hover-lift').forEach(element => {
    element.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-5px)';
    });

    element.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });
}

// Optimización de performance
function throttle(func, wait) {
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

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
  // Crear partículas
  createParticles();

  // Inicializar animaciones
  animateOnScroll();

  // Inicializar smooth scroll
  initSmoothScroll();

  // Inicializar tracking de CTAs
  initCTATracking();

  // Inicializar efectos hover
  initHoverEffects();

  // Animar elementos al cargar (con delay)
  setTimeout(() => {
    const elements = document.querySelectorAll('[data-animate]');
    elements.forEach((element, index) => {
      setTimeout(() => {
        element.classList.add('animate');
      }, index * 100);
    });
  }, 500);

  // Event listeners optimizados con throttle
  const throttledAnimateOnScroll = throttle(animateOnScroll, 100);
  const throttledParallaxEffect = throttle(parallaxEffect, 16); // 60fps

  window.addEventListener('scroll', () => {
    throttledAnimateOnScroll();
    throttledParallaxEffect();
  });

  // Tracking de tiempo en página
  let startTime = Date.now();
  window.addEventListener('beforeunload', function() {
    const timeOnPage = Math.round((Date.now() - startTime) / 1000);
    trackEvent('time_on_page', { value: timeOnPage });
  });

  // Tracking de scroll depth
  let maxScroll = 0;
  window.addEventListener('scroll', throttle(() => {
    const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
    if (scrollPercent > maxScroll) {
      maxScroll = scrollPercent;

      // Track milestones de scroll
      if (maxScroll >= 25 && maxScroll < 50) {
        trackEvent('scroll_25_percent');
      } else if (maxScroll >= 50 && maxScroll < 75) {
        trackEvent('scroll_50_percent');
      } else if (maxScroll >= 75 && maxScroll < 90) {
        trackEvent('scroll_75_percent');
      } else if (maxScroll >= 90) {
        trackEvent('scroll_90_percent');
      }
    }
  }, 500));

  // Tracking de secciones vistas
  const sections = ['hero', 'beneficios', 'casos-uso', 'metricas', 'caracteristicas', 'comparativa', 'planes', 'testimonios', 'cta-final'];
  const viewedSections = new Set();

  window.addEventListener('scroll', throttle(() => {
    sections.forEach(sectionId => {
      const section = document.getElementById(sectionId);
      if (section && !viewedSections.has(sectionId)) {
        const rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
          viewedSections.add(sectionId);
          trackEvent(`section_viewed_${sectionId}`);
        }
      }
    });
  }, 1000));
});

// Exportar funciones para uso global si es necesario
window.LandingChile = {
  trackEvent,
  createParticles,
  animateOnScroll
};
