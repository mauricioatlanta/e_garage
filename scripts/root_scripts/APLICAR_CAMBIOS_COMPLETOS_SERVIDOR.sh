#!/bin/bash
# Script para aplicar todos los cambios: sin siglas duplicadas, colores neon, botones más pequeños, logo más grande

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando cambios completos en selector_pais.html..."

# Backup
cp templates/public/selector_pais.html templates/public/selector_pais.html.backup_$(date +%Y%m%d_%H%M%S)

python3 << 'PYEOF'
file_path = "templates/public/selector_pais.html"

# Contenido completo actualizado
content = """{% load static %}
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
      background: #000000;
      font-family: 'Orbitron', 'Rajdhani', sans-serif;
      color: #fff;
      min-height: 100vh;
      position: relative;
      padding: 2rem;
    }

    /* Fondo animado super futurista - Negro, Calipso, Neon */
    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(0, 191, 255, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(0, 150, 255, 0.08) 0%, transparent 70%),
        linear-gradient(135deg, #000000 0%, #0a0a1a 50%, #000000 100%);
      animation: pulse 8s ease-in-out infinite;
      z-index: 0;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.9; transform: scale(1.05); }
    }

    body::after {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 255, 0.05) 2px, rgba(0, 255, 255, 0.05) 4px),
        repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0, 191, 255, 0.05) 2px, rgba(0, 191, 255, 0.05) 4px);
      background-size: 50px 50px, 50px 50px;
      animation: gridMove 20s linear infinite;
      z-index: 1;
    }

    @keyframes gridMove {
      0% { background-position: 0 0, 0 0; }
      100% { background-position: 50px 50px, 50px 50px; }
    }

    /* Partículas de fondo neon */
    .bg-particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 2;
      overflow: hidden;
      pointer-events: none;
    }
    .particle {
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(0, 255, 255, 0.6) 0%, transparent 70%);
      animation: float 15s infinite ease-in-out;
      box-shadow: 0 0 30px rgba(0, 255, 255, 0.8), 0 0 60px rgba(0, 191, 255, 0.4);
    }
    .particle:nth-child(1) { width: 120px; height: 120px; left: 10%; top: 20%; animation-delay: 0s; }
    .particle:nth-child(2) { width: 90px; height: 90px; left: 80%; top: 30%; animation-delay: 2s; }
    .particle:nth-child(3) { width: 150px; height: 150px; left: 50%; top: 60%; animation-delay: 4s; }
    .particle:nth-child(4) { width: 100px; height: 100px; left: 20%; top: 80%; animation-delay: 6s; }
    .particle:nth-child(5) { width: 80px; height: 80px; left: 70%; top: 10%; animation-delay: 8s; }
    .particle:nth-child(6) { width: 110px; height: 110px; left: 30%; top: 50%; animation-delay: 10s; }
    .particle:nth-child(7) { width: 130px; height: 130px; left: 60%; top: 40%; animation-delay: 12s; }
    .particle:nth-child(8) { width: 95px; height: 95px; left: 40%; top: 15%; animation-delay: 14s; }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0.5; }
      25% { transform: translateY(-50px) translateX(30px) scale(1.2); opacity: 0.8; }
      50% { transform: translateY(-80px) translateX(-40px) scale(0.9); opacity: 0.6; }
      75% { transform: translateY(-30px) translateX(50px) scale(1.1); opacity: 0.9; }
    }

    /* Logo imponente centrado */
    .logo-container {
      position: relative;
      z-index: 10;
      text-align: center;
      margin-bottom: 3rem;
      padding-top: 2rem;
    }
    
    .logo-container img {
      height: 250px;
      width: auto;
      filter: drop-shadow(0 0 60px rgba(0, 255, 255, 1)) drop-shadow(0 0 100px rgba(0, 191, 255, 0.6));
      animation: logoGlow 3s ease-in-out infinite;
    }
    
    @keyframes logoGlow {
      0%, 100% {
        filter: drop-shadow(0 0 60px rgba(0, 255, 255, 1)) drop-shadow(0 0 100px rgba(0, 191, 255, 0.6));
        transform: scale(1);
      }
      50% {
        filter: drop-shadow(0 0 80px rgba(0, 255, 255, 1.2)) drop-shadow(0 0 120px rgba(0, 191, 255, 0.8));
        transform: scale(1.05);
      }
    }

    /* Contenedor principal */
    .mosaic-container {
      position: relative;
      z-index: 10;
      max-width: 1600px;
      margin: 0 auto;
      width: 100%;
    }

    /* Grid de mosaico */
    .country-mosaic {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1.2rem;
      padding: 0;
    }

    /* Tarjetas de país - ULTRA REALISTAS Y FUTURISTAS */
    .country-card {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1.5rem 1.2rem;
      border-radius: 16px;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      overflow: hidden;
      min-height: 160px;
      
      /* Efecto ultra realista con profundidad */
      border: 2px solid rgba(255, 255, 255, 0.15);
      box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.8),
        0 4px 16px rgba(0, 0, 0, 0.6),
        inset 0 2px 4px rgba(255, 255, 255, 0.2),
        inset 0 -2px 4px rgba(0, 0, 0, 0.5);
    }

    /* Efecto de brillo metálico */
    .country-card::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.3) 50%, transparent 70%);
      transform: rotate(45deg);
      transition: all 1s;
      opacity: 0;
    }

    .country-card:hover::before {
      animation: metallicShine 1.5s infinite;
    }

    @keyframes metallicShine {
      0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); opacity: 0; }
      50% { opacity: 1; }
      100% { transform: translateX(100%) translateY(100%) rotate(45deg); opacity: 0; }
    }

    /* Borde neon animado */
    .country-card::after {
      content: '';
      position: absolute;
      inset: -3px;
      border-radius: 20px;
      padding: 3px;
      background: linear-gradient(135deg, rgba(0, 255, 255, 0.8), rgba(0, 191, 255, 0.6), rgba(0, 255, 255, 0.8));
      -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      -webkit-mask-composite: xor;
      mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      mask-composite: exclude;
      opacity: 0;
      transition: opacity 0.5s;
    }

    .country-card:hover::after {
      opacity: 1;
      animation: neonPulse 2s ease-in-out infinite;
    }

    @keyframes neonPulse {
      0%, 100% { opacity: 0.8; filter: brightness(1); }
      50% { opacity: 1; filter: brightness(1.3); }
    }

    .country-card:hover {
      transform: translateY(-8px) scale(1.05);
      box-shadow: 
        0 16px 48px rgba(0, 0, 0, 0.9),
        0 8px 24px rgba(0, 0, 0, 0.7),
        0 0 60px rgba(0, 255, 255, 0.5),
        0 0 100px rgba(0, 191, 255, 0.3),
        inset 0 2px 4px rgba(255, 255, 255, 0.3),
        inset 0 -2px 4px rgba(0, 0, 0, 0.6);
      z-index: 20;
      border-color: rgba(0, 255, 255, 0.4);
    }

    .country-card:active {
      transform: translateY(-4px) scale(1.02);
    }

    /* Flag emoji */
    .country-flag {
      font-size: 2.8rem;
      margin-bottom: 0.8rem;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.8));
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      display: block;
      line-height: 1;
    }

    .country-card:hover .country-flag {
      transform: scale(1.2) rotate(10deg);
      filter: drop-shadow(0 8px 24px rgba(0, 255, 255, 0.9));
    }

    /* Nombre del país - COLOR NEON (sin código duplicado) */
    .country-name {
      font-family: 'Orbitron', sans-serif;
      font-size: 1rem;
      font-weight: 700;
      text-align: center;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #00FFFF;
      text-shadow: 
        0 0 8px rgba(0, 255, 255, 1),
        0 0 16px rgba(0, 255, 255, 0.8),
        0 0 24px rgba(0, 255, 255, 0.6),
        0 0 32px rgba(0, 191, 255, 0.4),
        0 2px 6px rgba(0, 0, 0, 0.95);
      transition: all 0.3s;
      line-height: 1.3;
    }

    .country-card:hover .country-name {
      color: #00FFFF;
      text-shadow: 
        0 0 12px rgba(0, 255, 255, 1),
        0 0 24px rgba(0, 255, 255, 0.9),
        0 0 36px rgba(0, 255, 255, 0.7),
        0 0 48px rgba(0, 191, 255, 0.5),
        0 2px 6px rgba(0, 0, 0, 0.95);
    }
    
    /* Ocultar código del país para evitar duplicación */
    .country-code {
      display: none;
    }

    /* Estilos específicos por país - COLORES VIVOS Y DEFINIDOS */
    .country-card.usa {
      background: linear-gradient(135deg, #001f54 0%, #003d82 25%, #002868 50%, #BF0A30 75%, #d41e3d 100%);
      border-color: rgba(191, 10, 48, 0.6);
    }
    .country-card.usa .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.brasil {
      background: linear-gradient(135deg, #006b3c 0%, #00c853 20%, #ffd700 40%, #ffc107 60%, #00c853 80%, #006b3c 100%);
      border-color: rgba(255, 215, 0, 0.6);
    }
    .country-card.brasil .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.venezuela {
      background: linear-gradient(135deg, #FFD700 0%, #FFC107 25%, #003893 50%, #00247D 75%, #CF142B 100%);
      border-color: rgba(255, 215, 0, 0.6);
    }
    .country-card.venezuela .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.peru {
      background: linear-gradient(135deg, #DC143C 0%, #C41E3A 25%, #FFFFFF 50%, #DC143C 75%, #C41E3A 100%);
      border-color: rgba(220, 20, 60, 0.6);
    }
    .country-card.peru .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.chile {
      background: linear-gradient(135deg, #D52B1E 0%, #C41E3A 25%, #B71C1C 50%, #0033A0 75%, #002171 100%);
      border-color: rgba(213, 43, 30, 0.6);
    }
    .country-card.chile .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.colombia {
      background: linear-gradient(135deg, #FFD700 0%, #FFC107 25%, #003893 50%, #002171 75%, #CE1126 100%);
      border-color: rgba(255, 215, 0, 0.6);
    }
    .country-card.colombia .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.ecuador {
      background: linear-gradient(135deg, #FFD700 0%, #FFC107 25%, #003893 50%, #002171 75%, #EF3340 100%);
      border-color: rgba(255, 215, 0, 0.6);
    }
    .country-card.ecuador .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    .country-card.mexico {
      background: linear-gradient(135deg, #006847 0%, #008751 25%, #FFFFFF 50%, #CE1126 75%, #B71C1C 100%);
      border-color: rgba(0, 104, 71, 0.6);
    }
    .country-card.mexico .country-name {
      color: #00FFFF;
      text-shadow: 0 0 10px rgba(0, 255, 255, 1), 0 0 20px rgba(0, 255, 255, 0.8), 0 0 30px rgba(0, 191, 255, 0.6), 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    /* Footer minimalista - COLOR NEON */
    .footer-text {
      text-align: center;
      margin-top: 4rem;
      font-family: 'Rajdhani', sans-serif;
      font-size: 0.85rem;
      color: #00FFFF;
      text-shadow: 
        0 0 8px rgba(0, 255, 255, 0.8),
        0 0 16px rgba(0, 255, 255, 0.6);
      letter-spacing: 2px;
    }

    /* Responsive */
    @media (max-width: 1400px) {
      .country-mosaic {
        grid-template-columns: repeat(3, 1fr);
      }
    }

    @media (max-width: 1000px) {
      body {
        padding: 1.5rem;
      }
      
      .logo-container img {
        height: 200px;
      }
      
      .country-mosaic {
        grid-template-columns: repeat(2, 1fr);
        gap: 1.2rem;
      }
      
      .country-card {
        min-height: 150px;
        padding: 1.2rem 1rem;
      }
      
      .country-flag {
        font-size: 2.5rem;
      }
      
      .country-name {
        font-size: 0.9rem;
      }
    }

    @media (max-width: 600px) {
      body {
        padding: 1rem;
      }
      
      .logo-container img {
        height: 160px;
      }
      
      .country-mosaic {
        grid-template-columns: 1fr;
        gap: 1rem;
      }
      
      .country-card {
        min-height: 140px;
        padding: 1rem 0.8rem;
      }
      
      .country-flag {
        font-size: 2.2rem;
      }
      
      .country-name {
        font-size: 0.85rem;
      }
    }

    /* Animación de entrada */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(40px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .country-card {
      animation: fadeInUp 0.8s ease-out backwards;
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
    <div class="particle"></div>
    <div class="particle"></div>
  </div>

  <!-- Logo imponente -->
  <div class="logo-container">
    <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage">
  </div>

  <!-- Mosaico de países -->
  <div class="mosaic-container">
    <div class="country-mosaic">
      <a href="/us/" class="country-card usa">
        <span class="country-flag">🇺🇸</span>
        <span class="country-name">United States</span>
      </a>

      <a href="/br/" class="country-card brasil">
        <span class="country-flag">🇧🇷</span>
        <span class="country-name">Brasil</span>
      </a>

      <a href="/ve/" class="country-card venezuela">
        <span class="country-flag">🇻🇪</span>
        <span class="country-name">Venezuela</span>
      </a>

      <a href="/pe/" class="country-card peru">
        <span class="country-flag">🇵🇪</span>
        <span class="country-name">Perú</span>
      </a>

      <a href="/cl/" class="country-card chile">
        <span class="country-flag">🇨🇱</span>
        <span class="country-name">Chile</span>
      </a>

      <a href="/co/" class="country-card colombia">
        <span class="country-flag">🇨🇴</span>
        <span class="country-name">Colombia</span>
      </a>

      <a href="/ec/" class="country-card ecuador">
        <span class="country-flag">🇪🇨</span>
        <span class="country-name">Ecuador</span>
      </a>

      <a href="/mx/" class="country-card mexico">
        <span class="country-flag">🇲🇽</span>
        <span class="country-name">México</span>
      </a>
    </div>
    
    <p class="footer-text">
      Más países pronto · eGarage AI
    </p>
  </div>
</body>
</html>"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado correctamente")
PYEOF

echo ""
echo "✅✅✅ Cambios completos aplicados ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



