// login_effects.js
document.addEventListener("DOMContentLoaded", () => {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Partículas (solo si no hay reduced-motion)
  if (!prefersReduced && window.tsParticles) {
    tsParticles.load("tsparticles", {
      fullScreen: { enable: false },
      background: { color: { value: "transparent" } },
      particles: {
        number: { value: 80 }, // menos partículas = menos CPU
        color: { value: ["#00ff88", "#00d4ff", "#8844ff", "#ff4488", "#ffaa00"] },
        shape: { type: ["circle", "triangle", "polygon"], polygon: { sides: 6 } },
        size: { value: { min: 0.5, max: 2 } },
        move: { enable: true, speed: { min: 0.1, max: 1.0 }, outModes: { default: "bounce" } },
        opacity: { value: { min: 0.1, max: 0.6 } },
        links: { enable: true, distance: 100, color: "#00ff88", opacity: 0.15, width: 1 }
      },
      interactivity: {
        events: { onHover: { enable: true, mode: "repulse" } },
        modes: { repulse: { distance: 80, duration: 0.3 } }
      }
    });
  }

  // Scanlines
  const scanlines = document.createElement('div');
  scanlines.className = 'cyberpunk-scanlines';
  document.body.appendChild(scanlines);

  // Glitch en logo
  const logo = document.querySelector('.egarage-logo');
  if (logo && !prefersReduced) {
    setInterval(() => {
      if (document.hidden) return;
      if (Math.random() < 0.1) {
        logo.classList.add('glitch-effect');
        setTimeout(() => logo.classList.remove('glitch-effect'), 200);
      }
    }, 3000);
  }

  // Matrix rain con rAF y pausa en background
  const canvas = document.createElement('canvas');
  canvas.className = 'matrix-canvas';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890@#$%^&*()';
  const lettersArray = letters.split('');
  const fontSize = 14;
  let columns = Math.floor(canvas.width / fontSize);
  let drops = new Array(columns).fill(1);

  function step() {
    if (prefersReduced || document.hidden) return;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ff88';
    ctx.font = fontSize + 'px monospace';
    for (let i = 0; i < drops.length; i++) {
      const text = lettersArray[Math.floor(Math.random() * lettersArray.length)];
      ctx.fillText(text, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
  }

  let rafId;
  function loop() {
    step();
    rafId = requestAnimationFrame(loop);
  }
  if (!prefersReduced) loop();

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(rafId);
    else if (!prefersReduced) loop();
  });
});


