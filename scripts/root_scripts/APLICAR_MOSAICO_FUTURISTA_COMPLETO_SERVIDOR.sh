#!/bin/bash
# Script para aplicar el diseño de mosaico futurista completo al selector de país

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🎨 Aplicando diseño de mosaico futurista de alta calidad..."

python3 << 'PYEOF'
file_path = "templates/public/selector_pais.html"

# Contenido completo del nuevo diseño
content = '''{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>eGarage</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * { 
      margin: 0; 
      padding: 0; 
      box-sizing: border-box; 
    }
    
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      overflow-x: hidden;
      overflow-y: auto;
    }
    
    body {
      background: #0a0a23;
      font-family: 'Orbitron', 'Rajdhani', sans-serif;
      color: #fff;
      min-height: 100vh;
      position: relative;
      padding: 200px 2rem 4rem;
    }

    /* Fondo animado futurista */
    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        linear-gradient(135deg, #0a0a23 0%, #1a1a2e 50%, #0f1419 100%),
        repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 230, 255, 0.03) 2px, rgba(0, 230, 255, 0.03) 4px),
        repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0, 230, 255, 0.03) 2px, rgba(0, 230, 255, 0.03) 4px);
      background-size: 100% 100%, 50px 50px, 50px 50px;
      animation: gridMove 20s linear infinite;
      z-index: 0;
    }

    @keyframes gridMove {
      0% { background-position: 0 0, 0 0, 0 0; }
      100% { background-position: 0 0, 50px 50px, 50px 50px; }
    }

    body::after {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        radial-gradient(circle at 20% 30%, rgba(0, 230, 255, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(0, 184, 212, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(0, 116, 217, 0.08) 0%, transparent 70%);
      animation: pulse 8s ease-in-out infinite;
      z-index: 0;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.8; transform: scale(1.1); }
    }

    /* Partículas de fondo */
    .bg-particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      overflow: hidden;
      pointer-events: none;
    }
    .particle {
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(0, 230, 255, 0.4) 0%, transparent 70%);
      animation: float 15s infinite ease-in-out;
      box-shadow: 0 0 20px rgba(0, 230, 255, 0.5);
    }
    .particle:nth-child(1) { width: 120px; height: 120px; left: 10%; top: 20%; animation-delay: 0s; }
    .particle:nth-child(2) { width: 90px; height: 90px; left: 80%; top: 30%; animation-delay: 2s; }
    .particle:nth-child(3) { width: 150px; height: 150px; left: 50%; top: 60%; animation-delay: 4s; }
    .particle:nth-child(4) { width: 100px; height: 100px; left: 20%; top: 80%; animation-delay: 6s; }
    .particle:nth-child(5) { width: 80px; height: 80px; left: 70%; top: 10%; animation-delay: 8s; }
    .particle:nth-child(6) { width: 110px; height: 110px; left: 30%; top: 50%; animation-delay: 10s; }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0.4; }
      25% { transform: translateY(-40px) translateX(20px) scale(1.1); opacity: 0.6; }
      50% { transform: translateY(-60px) translateX(-30px) scale(0.9); opacity: 0.5; }
      75% { transform: translateY(-20px) translateX(40px) scale(1.05); opacity: 0.7; }
    }

    /* Header con logo */
    .page-header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 100;
      padding: 2rem;
      background: rgba(10, 18, 40, 0.95);
      backdrop-filter: blur(30px);
      border-bottom: 2px solid rgba(0, 230, 255, 0.3);
      box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6);
    }
    
    .header-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .header-logo {
      height: 160px;
      width: auto;
      filter: drop-shadow(0 0 40px rgba(0, 230, 255, 0.8));
      animation: logoGlow 3s ease-in-out infinite;
    }
    
    @keyframes logoGlow {
      0%, 100% {
        filter: drop-shadow(0 0 40px rgba(0, 230, 255, 0.8));
        transform: scale(1);
      }
      50% {
        filter: drop-shadow(0 0 60px rgba(0, 230, 255, 1));
        transform: scale(1.02);
      }
    }

    /* Contenedor principal - MOSAICO FUTURISTA */
    .mosaic-container {
      position: relative;
      z-index: 10;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    /* Grid de mosaico inteligente */
    .country-mosaic {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
      padding: 0;
    }

    /* Tarjetas de país - Diseño futurista premium */
    .country-card {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2.5rem 2rem;
      border-radius: 24px;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      overflow: hidden;
      min-height: 200px;
      backdrop-filter: blur(20px);
      border: 2px solid transparent;
      box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    /* Efecto de brillo animado */
    .country-card::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
      transform: rotate(45deg);
      transition: all 0.8s;
      opacity: 0;
    }

    .country-card:hover::before {
      animation: shine 1.5s infinite;
    }

    @keyframes shine {
      0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); opacity: 0; }
      50% { opacity: 1; }
      100% { transform: translateX(100%) translateY(100%) rotate(45deg); opacity: 0; }
    }

    /* Borde animado */
    .country-card::after {
      content: '';
      position: absolute;
      inset: -2px;
      border-radius: 24px;
      padding: 2px;
      background: linear-gradient(135deg, rgba(0, 230, 255, 0.5), rgba(0, 184, 212, 0.3), rgba(0, 230, 255, 0.5));
      -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      -webkit-mask-composite: xor;
      mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      mask-composite: exclude;
      opacity: 0;
      transition: opacity 0.5s;
    }

    .country-card:hover::after {
      opacity: 1;
      animation: borderGlow 2s ease-in-out infinite;
    }

    @keyframes borderGlow {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    .country-card:hover {
      transform: translateY(-8px) scale(1.05);
      box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.6),
        0 0 60px rgba(0, 230, 255, 0.4),
        0 0 100px rgba(0, 230, 255, 0.2),
        inset 0 0 40px rgba(255, 255, 255, 0.1);
      z-index: 20;
    }

    .country-card:active {
      transform: translateY(-4px) scale(1.02);
    }

    /* Flag emoji */
    .country-flag {
      font-size: 4.5rem;
      margin-bottom: 1rem;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.4));
      transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
      display: block;
      line-height: 1;
    }

    .country-card:hover .country-flag {
      transform: scale(1.2) rotate(10deg);
      filter: drop-shadow(0 8px 24px rgba(0, 230, 255, 0.6));
    }

    /* Código del país */
    .country-code {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.1rem;
      font-weight: 800;
      letter-spacing: 4px;
      margin-bottom: 0.5rem;
      opacity: 0.9;
      text-shadow: 0 0 15px rgba(0, 230, 255, 0.5);
      transition: all 0.3s;
    }

    .country-card:hover .country-code {
      opacity: 1;
      text-shadow: 0 0 25px rgba(0, 230, 255, 0.9);
      letter-spacing: 5px;
    }

    /* Nombre del país */
    .country-name {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.4rem;
      font-weight: 700;
      text-align: center;
      letter-spacing: 2px;
      text-transform: uppercase;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
      transition: all 0.3s;
    }

    .country-card:hover .country-name {
      text-shadow: 0 0 30px rgba(255, 255, 255, 0.8);
    }

    /* Estilos específicos por país */
    .country-card.usa {
      background: linear-gradient(135deg, #002868 0%, #0050b3 50%, #003d82 100%);
      color: #fff;
    }

    .country-card.brasil {
      background: linear-gradient(135deg, #009c3b 0%, #007a2f 30%, #ffdf00 70%, #ffcc00 100%);
      color: #000;
    }

    .country-card.venezuela {
      background: linear-gradient(135deg, #FFCC00 0%, #00247D 50%, #CF142B 100%);
      color: #fff;
    }

    .country-card.peru {
      background: linear-gradient(135deg, #D91023 0%, #FFFFFF 50%, #D91023 100%);
      color: #fff;
    }

    .country-card.chile {
      background: linear-gradient(135deg, #d52b1e 0%, #b8241a 50%, #0033a0 100%);
      color: #fff;
    }

    .country-card.colombia {
      background: linear-gradient(135deg, #FFCE00 0%, #003087 50%, #CE1126 100%);
      color: #fff;
    }

    .country-card.ecuador {
      background: linear-gradient(135deg, #FFD700 0%, #0033A0 50%, #EF3340 100%);
      color: #000;
    }

    .country-card.mexico {
      background: linear-gradient(135deg, #006847 0%, #FFFFFF 50%, #CE1126 100%);
      color: #fff;
    }

    /* Footer */
    .footer-text {
      text-align: center;
      margin-top: 3rem;
      font-family: 'Rajdhani', sans-serif;
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.5);
      letter-spacing: 1px;
    }

    /* Responsive */
    @media (max-width: 1200px) {
      .country-mosaic {
        grid-template-columns: repeat(3, 1fr);
      }
    }

    @media (max-width: 900px) {
      body {
        padding: 180px 1.5rem 3rem;
      }
      
      .header-logo {
        height: 120px;
      }
      
      .country-mosaic {
        grid-template-columns: repeat(2, 1fr);
        gap: 1.2rem;
      }
      
      .country-card {
        min-height: 180px;
        padding: 2rem 1.5rem;
      }
      
      .country-flag {
        font-size: 3.5rem;
      }
      
      .country-name {
        font-size: 1.2rem;
      }
    }

    @media (max-width: 600px) {
      body {
        padding: 160px 1rem 2rem;
      }
      
      .header-logo {
        height: 100px;
      }
      
      .country-mosaic {
        grid-template-columns: 1fr;
        gap: 1rem;
      }
      
      .country-card {
        min-height: 160px;
        padding: 1.5rem 1.2rem;
      }
      
      .country-flag {
        font-size: 3rem;
      }
      
      .country-name {
        font-size: 1.1rem;
      }
      
      .country-code {
        font-size: 0.95rem;
      }
    }

    /* Animación de entrada */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .country-card {
      animation: fadeInUp 0.6s ease-out backwards;
    }

    .country-card:nth-child(1) { animation-delay: 0.1s; }
    .country-card:nth-child(2) { animation-delay: 0.2s; }
    .country-card:nth-child(3) { animation-delay: 0.3s; }
    .country-card:nth-child(4) { animation-delay: 0.4s; }
    .country-card:nth-child(5) { animation-delay: 0.5s; }
    .country-card:nth-child(6) { animation-delay: 0.6s; }
    .country-card:nth-child(7) { animation-delay: 0.7s; }
    .country-card:nth-child(8) { animation-delay: 0.8s; }
  </style>
</head>
<body>
  <div class="bg-particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
  </div>

  <!-- Header con logo -->
  <header class="page-header">
    <div class="header-content">
      <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage" class="header-logo">
    </div>
  </header>

  <!-- Mosaico de países -->
  <div class="mosaic-container">
    <div class="country-mosaic">
      <a href="/us/" class="country-card usa">
        <span class="country-flag">🇺🇸</span>
        <span class="country-code">US</span>
        <span class="country-name">United States</span>
      </a>

      <a href="/br/" class="country-card brasil">
        <span class="country-flag">🇧🇷</span>
        <span class="country-code">BR</span>
        <span class="country-name">Brasil</span>
      </a>

      <a href="/ve/" class="country-card venezuela">
        <span class="country-flag">🇻🇪</span>
        <span class="country-code">VE</span>
        <span class="country-name">Venezuela</span>
      </a>

      <a href="/pe/" class="country-card peru">
        <span class="country-flag">🇵🇪</span>
        <span class="country-code">PE</span>
        <span class="country-name">Perú</span>
      </a>

      <a href="/cl/" class="country-card chile">
        <span class="country-flag">🇨🇱</span>
        <span class="country-code">CL</span>
        <span class="country-name">Chile</span>
      </a>

      <a href="/co/" class="country-card colombia">
        <span class="country-flag">🇨🇴</span>
        <span class="country-code">CO</span>
        <span class="country-name">Colombia</span>
      </a>

      <a href="/ec/" class="country-card ecuador">
        <span class="country-flag">🇪🇨</span>
        <span class="country-code">EC</span>
        <span class="country-name">Ecuador</span>
      </a>

      <a href="/mx/" class="country-card mexico">
        <span class="country-flag">🇲🇽</span>
        <span class="country-code">MX</span>
        <span class="country-name">México</span>
      </a>
    </div>
    
    <p class="footer-text">
      Más países pronto · eGarage AI
    </p>
  </div>
</body>
</html>
'''

# Escribir el archivo completo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Diseño de mosaico futurista aplicado")
print("   - Sin contenedores anidados")
print("   - Sin scrollbars")
print("   - Grid inteligente responsive")
print("   - Tarjetas futuristas premium")
print("   - Efectos de brillo y animaciones avanzadas")
print("   - Diseño de alta calidad internacional")
PYEOF

echo ""
echo "✅✅✅ Rediseño completo aplicado ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



