/**
 * STARFIELD - Sistema de estrellas animadas
 * Añade estrellas dinámicas y efectos adicionales
 */

(function() {
  'use strict';
  
  // Verificar si el starfield está presente
  const starfield = document.getElementById('bg-starfield');
  if (!starfield) return;
  
  // Configuración
  const config = {
    shootingStarInterval: 8000, // Cada 8 segundos
    shootingStarDuration: 1500,
    shootingStarEnabled: true
  };
  
  /**
   * Crea una estrella fugaz
   */
  function createShootingStar() {
    if (!config.shootingStarEnabled) return;
    
    const shootingStar = document.createElement('div');
    shootingStar.className = 'shooting-star';
    
    // Posición aleatoria en la parte superior
    const startX = Math.random() * window.innerWidth;
    const startY = Math.random() * (window.innerHeight * 0.3);
    
    // Aplicar estilos
    Object.assign(shootingStar.style, {
      position: 'fixed',
      left: startX + 'px',
      top: startY + 'px',
      width: '2px',
      height: '2px',
      background: 'linear-gradient(to right, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0))',
      borderRadius: '50%',
      boxShadow: '0 0 8px 2px rgba(255, 255, 255, 0.8)',
      transform: 'rotate(-45deg)',
      pointerEvents: 'none',
      zIndex: '-1'
    });
    
    starfield.appendChild(shootingStar);
    
    // Animar
    const animation = shootingStar.animate([
      {
        transform: 'rotate(-45deg) translateX(0) translateY(0)',
        opacity: 1,
        width: '2px',
        height: '2px'
      },
      {
        transform: 'rotate(-45deg) translateX(150px) translateY(150px)',
        opacity: 0,
        width: '80px',
        height: '2px'
      }
    ], {
      duration: config.shootingStarDuration,
      easing: 'ease-out'
    });
    
    // Eliminar después de la animación
    animation.onfinish = () => {
      shootingStar.remove();
    };
  }
  
  /**
   * Inicia el sistema de estrellas fugaces
   */
  function startShootingStars() {
    // Primera estrella después de 2 segundos
    setTimeout(createShootingStar, 2000);
    
    // Estrellas regulares
    setInterval(createShootingStar, config.shootingStarInterval);
  }
  
  /**
   * Añade twinkle a estrellas existentes
   */
  function addTwinkleEffect() {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes twinkle {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 1; }
      }
      
      .stars.layer1 {
        animation: starsMove1 240s linear infinite, twinkle 3s ease-in-out infinite;
      }
      
      .stars.layer2 {
        animation: starsMove2 120s linear infinite, twinkle 4s ease-in-out infinite;
        animation-delay: 0s, 1s;
      }
      
      .stars.layer3 {
        animation: starsMove3 60s linear infinite, twinkle 5s ease-in-out infinite;
        animation-delay: 0s, 2s;
      }
    `;
    document.head.appendChild(style);
  }
  
  /**
   * Inicialización
   */
  function init() {
    // Añadir efectos solo si no es móvil (rendimiento)
    const isMobile = window.innerWidth <= 768;
    
    if (!isMobile) {
      addTwinkleEffect();
      startShootingStars();
    }
    
    // Deshabilitar en modo reducido
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      config.shootingStarEnabled = false;
    }
  }
  
  // Ejecutar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
})();

