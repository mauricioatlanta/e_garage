// -----------------------------------------------------------------------------
// Copyright (c) 2025 eGarage. Todos los derechos reservados.
//
// PROPIEDAD INTELECTUAL PROTEGIDA. ESTRICTAMENTE CONFIDENCIAL.
// Este archivo contiene efectos visuales y animaciones propietarias.
//
// Consulta el archivo LICENSE en la raíz del repositorio para más detalles
// sobre la protección de la Propiedad Intelectual de eGarage.
// -----------------------------------------------------------------------------

// Fondo de partículas canvas minimal: solo puntos muy pequeños (sin "globos").
(function(){
  const holder = document.getElementById('bg-starfield');
  if(!holder) return;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  holder.appendChild(canvas);

  let w=canvas.width=window.innerWidth;
  let h=canvas.height=window.innerHeight;
  window.addEventListener('resize',()=>{w=canvas.width=window.innerWidth;h=canvas.height=window.innerHeight;init();});

  const stars=[];
  function count(){
    // Densidad moderada, adaptable a pantalla (sin sobrecargar)
    return Math.min(1200, Math.floor((w*h)/4500));
  }

  function init(){
    stars.length=0;
    const N = count();
    for(let i=0;i<N;i++){
      stars.push({
        x: Math.random()*w,
        y: Math.random()*h,
        d: Math.random()*0.6 + 0.2, // diámetro muy pequeño
        sp: 0.02 + Math.random()*0.05, // velocidad horizontal lenta
        tw: 2 + Math.random()*6, // frecuencia twinkle
        ph: Math.random()*Math.PI*2,
        c: Math.random()<0.85 ? 'base' : (Math.random()<0.5 ? 'cyan':'warm')
      });
    }
  }
  init();

  function draw(){
    ctx.clearRect(0,0,w,h);
    // Fondo oscuro sólido (evita halos grandes)
    ctx.fillStyle = '#05070c';
    ctx.fillRect(0,0,w,h);

    const t = performance.now()/1000;
    for(const s of stars){
      const tw = 0.4 + Math.sin(t*s.tw + s.ph)*0.6; // 0..1
      let color;
      if(s.c==='base') color = `rgba(220,235,255,${tw})`;
      else if(s.c==='cyan') color = `rgba(120,255,250,${tw})`;
      else color = `rgba(255,210,140,${tw})`;
      ctx.fillStyle = color;
      // Puntos muy pequeños (fillRect) para evitar sensación de círculo grande
      ctx.fillRect(s.x, s.y, s.d, s.d);
      // ligera cola sub-píxel para sensación de movimiento (difuminado manual)
      if(tw>0.75 && s.d>0.35){
        ctx.fillStyle = color.replace(/,([^,]+)\)$/ , ',0.3)');
        ctx.fillRect(s.x - 1.2, s.y, s.d/2, s.d/2);
      }
      s.x -= s.sp;
      if(s.x < -2){ s.x = w + Math.random()*10; s.y = Math.random()*h; }
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();





