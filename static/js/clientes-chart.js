let _chart = null;
async function fetchClientesStats(params = {}){
  const qs = new URLSearchParams(params).toString();
  const res = await fetch('/analytics/clientes-api/?' + qs);
  return await res.json();
}

async function initClientesChart(canvasId, legendContainerId, params = {}){
  const canvas = document.getElementById(canvasId);
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  try{
    const json = await fetchClientesStats(params);
    const labels = json.distribution.map(item => item.region__nombre) || [];
    const data = json.distribution.map(item => item.count) || [];

  // generate neon palette
  const palette = labels.map((l,i)=>{
    const hue = (i*55)%360;
    return `hsl(${hue} 95% 60%)`;
  });

  if(_chart){ _chart.destroy(); _chart = null; }
  // center plugin to show total
  const centerText = {
    id: 'centerText',
    afterDraw(chart){
      const {ctx, chartArea: {top, right, bottom, left, width, height}} = chart;
      const total = (chart.data.datasets[0].data || []).reduce((s,v)=>s+(v||0),0);
      ctx.save();
      const fontSize = Math.min(width, height) / 8;
      ctx.font = `bold ${fontSize}px 'Share Tech Mono', monospace`;
      ctx.fillStyle = '#00ffe7';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(total, left + width/2, top + height/2 - (fontSize*0.15));
      ctx.font = `12px 'Share Tech Mono', monospace`;
      ctx.fillStyle = '#c7fff7';
      ctx.fillText('Clientes', left + width/2, top + height/2 + (fontSize*0.9));
      ctx.restore();
    }
  };

  _chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: palette,
          borderColor: '#071116',
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0b1220',
            titleColor: '#00ffe7',
            bodyColor: '#e6fff9',
            borderColor: '#00ffe7',
            borderWidth: 1
          }
        }
      }
    });

    // register center text plugin if not already
    if(!Chart.registry.getPlugin('centerText')){
      Chart.register(centerText);
    }

    // render legend
  const leyenda = document.getElementById(legendContainerId);
  if(leyenda){
    leyenda.innerHTML = '';
    labels.forEach((lab, idx) => {
      const li = document.createElement('li');
      li.className = 'flex items-center gap-3';
      const sw = document.createElement('span');
      sw.style.width = '18px'; sw.style.height = '18px'; sw.style.borderRadius = '6px';
      sw.style.background = palette[idx];
      sw.style.boxShadow = `0 6px 18px ${palette[idx]}66`;
      const txt = document.createElement('span');
      txt.className = 'text-white font-mono';
      txt.textContent = `${lab} — ${data[idx] || 0}`;
      li.appendChild(sw); li.appendChild(txt);
      leyenda.appendChild(li);
    });
  }

  }catch(err){
    console.error('Error fetching clientes stats', err);
  }
}

async function refreshClientesChart(opts = {}){
  await initClientesChart('clientes-region-chart','leyenda-regiones', opts);
}

// Auto init if DOM ready
if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', ()=>initClientesChart('clientes-region-chart','leyenda-regiones'));
} else {
  initClientesChart('clientes-region-chart','leyenda-regiones');
}

// Export for console usage
window.refreshClientesChart = refreshClientesChart;
