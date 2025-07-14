const canvas = document.createElement('canvas');
canvas.id = 'smoke-canvas';
document.body.appendChild(canvas);

const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];
for (let i = 0; i < 100; i++) {
  particles.push({
    x: Math.random() * canvas.width,
    y: canvas.height + Math.random() * 200,
    speed: 0.5 + Math.random(),
    radius: 20 + Math.random() * 30,
    alpha: 0.1 + Math.random() * 0.3
  });
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let p of particles) {
    ctx.beginPath();
    ctx.fillStyle = `rgba(200, 200, 200, ${p.alpha})`;
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    ctx.fill();
    p.y -= p.speed;
    if (p.y + p.radius < 0) {
      p.y = canvas.height + p.radius;
      p.x = Math.random() * canvas.width;
    }
  }
  requestAnimationFrame(draw);
}

draw();