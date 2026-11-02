#!/bin/bash
# Script para actualizar selector_pais.html en el servidor con la versión completa local

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path

file_path = 'templates/public/selector_pais.html'

print(f"📝 Actualizando {file_path} con versión completa...\n")

# Contenido completo del archivo local
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
      overflow: hidden;
    }
    
    body {
      background: #0a0a23;
      font-family: 'Rajdhani', 'Orbitron', 'Segoe UI', sans-serif;
      color: #fff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: relative;
    }

    /* Fondo animado con gradiente y grid */
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

    /* Partículas de fondo animadas */
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
      padding: 1.5rem 2rem;
      background: rgba(10, 18, 40, 0.85);
      backdrop-filter: blur(20px);
      border-bottom: 1px solid rgba(0, 230, 255, 0.2);
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    
    .header-content {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
    }
    
    .header-logo {
      height: 50px;
      width: auto;
      filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));
      animation: logoGlow 3s ease-in-out infinite;
    }
    
    @keyframes logoGlow {
      0%, 100% {
        filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));
        transform: scale(1);
      }
      50% {
        filter: drop-shadow(0 0 30px rgba(0, 230, 255, 0.9));
        transform: scale(1.02);
      }
    }
    
    .header-title {
      font-family: 'Orbitron', sans-serif;
      font-size: 2rem;
      font-weight: 700;
      background: linear-gradient(135deg, #00e6ff 0%, #00b8d4 50%, #00acc1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 2px;
      text-transform: uppercase;
      text-shadow: 0 0 30px rgba(0, 230, 255, 0.5);
    }

    .selector-container {
      position: relative;
      z-index: 10;
      background: rgba(20, 40, 80, 0.75);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      box-shadow: 
        0 0 60px rgba(0, 230, 255, 0.3),
        inset 0 0 60px rgba(0, 230, 255, 0.1),
        0 8px 32px rgba(0, 0, 0, 0.4);
      padding: 2.5rem 2rem;
      text-align: center;
      max-width: 550px;
      width: 90%;
      max-height: 85vh;
      overflow-y: auto;
      border: 2px solid rgba(0, 230, 255, 0.3);
      margin-top: 100px;
    }
    
    .selector-container::before {
      content: '';
      position: absolute;
      top: -2px;
      left: -2px;
      right: -2px;
      bottom: -2px;
      background: linear-gradient(135deg, rgba(0, 230, 255, 0.5), rgba(0, 184, 212, 0.3), rgba(0, 230, 255, 0.5));
      border-radius: 24px;
      z-index: -1;
      opacity: 0;
      transition: opacity 0.3s;
    }
    
    .selector-container:hover::before {
      opacity: 1;
    }
    
    .subtitle {
      font-family: 'Rajdhani', sans-serif;
      font-size: 1.1rem;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 2rem;
      letter-spacing: 1px;
      font-weight: 400;
    }

    .country-buttons {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .country-btn {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 1.2rem;
      width: 100%;
      padding: 1.4rem 1.8rem;
      font-size: 1.2rem;
      font-weight: 600;
      border-radius: 16px;
      border: 2px solid transparent;
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      text-decoration: none;
      font-family: 'Rajdhani', sans-serif;
      position: relative;
      overflow: hidden;
      min-height: 75px;
      backdrop-filter: blur(10px);
    }

    .country-btn::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
      transition: left 0.6s;
    }

    .country-btn::after {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: 16px;
      padding: 2px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.1));
      -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      -webkit-mask-composite: xor;
      mask-composite: exclude;
      opacity: 0;
      transition: opacity 0.4s;
    }

    .country-btn:hover::before {
      left: 100%;
    }
    
    .country-btn:hover::after {
      opacity: 1;
    }
    
    .country-btn:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.3),
        inset 0 0 20px rgba(255, 255, 255, 0.1);
      border-color: rgba(0, 230, 255, 0.6);
    }

    .country-btn.usa {
      background: linear-gradient(135deg, #002868 0%, #0050b3 50%, #003d82 100%);
      color: #fff;
      border: 2px solid rgba(0, 80, 179, 0.5);
      box-shadow: 
        0 4px 20px rgba(0, 80, 179, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.05);
    }

    .country-btn.usa:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(0, 80, 179, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.1);
      border-color: #00e6ff;
    }

    .country-btn.chile {
      background: linear-gradient(135deg, #d52b1e 0%, #b8241a 50%, #0033a0 100%);
      color: #fff;
      border: 2px solid rgba(213, 43, 30, 0.5);
      box-shadow: 
        0 4px 20px rgba(213, 43, 30, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.05);
    }

    .country-btn.chile:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(213, 43, 30, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.1);
      border-color: #00e6ff;
    }

    .country-btn.brasil {
      background: linear-gradient(135deg, #009c3b 0%, #007a2f 30%, #ffdf00 70%, #ffcc00 100%);
      color: #000;
      border: 2px solid rgba(0, 156, 59, 0.5);
      box-shadow: 
        0 4px 20px rgba(0, 156, 59, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.1);
    }

    .country-btn.brasil:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(0, 156, 59, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.15);
      border-color: #002776;
    }

    .country-btn.venezuela {
      background: linear-gradient(135deg, #FFCC00 0%, #00247D 50%, #CF142B 100%);
      color: #fff;
      border: 2px solid rgba(255, 204, 0, 0.5);
      box-shadow: 
        0 4px 20px rgba(255, 204, 0, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.05);
    }

    .country-btn.venezuela:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(255, 204, 0, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.1);
      border-color: #CF142B;
    }

    .country-btn.peru {
      background: linear-gradient(135deg, #DC143C 0%, #FFFFFF 50%, #DC143C 100%);
      color: #000;
      border: 2px solid rgba(220, 20, 60, 0.5);
      box-shadow: 
        0 4px 20px rgba(220, 20, 60, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.1);
    }

    .country-btn.peru:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(220, 20, 60, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.15);
      border-color: #FFFFFF;
    }

    .country-btn.mexico {
      background: linear-gradient(135deg, #006341 0%, #FFFFFF 50%, #CE1126 100%);
      color: #000;
      border: 2px solid rgba(0, 99, 65, 0.5);
      box-shadow: 
        0 4px 20px rgba(0, 99, 65, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.1);
    }

    .country-btn.mexico:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(0, 99, 65, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.15);
      border-color: #CE1126;
    }

    .country-btn.colombia {
      background: linear-gradient(135deg, #FCD116 0%, #003893 50%, #CE1126 100%);
      color: #000;
      border: 2px solid rgba(252, 209, 22, 0.5);
      box-shadow: 
        0 4px 20px rgba(252, 209, 22, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.1);
    }

    .country-btn.colombia:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(252, 209, 22, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.15);
      border-color: #CE1126;
    }

    .country-btn.ecuador {
      background: linear-gradient(135deg, #FFD700 0%, #0033A0 50%, #EF3340 100%);
      color: #000;
      border: 2px solid rgba(255, 215, 0, 0.5);
      box-shadow: 
        0 4px 20px rgba(255, 215, 0, 0.4),
        inset 0 0 15px rgba(255, 255, 255, 0.1);
    }

    .country-btn.ecuador:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.4),
        0 8px 30px rgba(255, 215, 0, 0.6),
        inset 0 0 20px rgba(255, 255, 255, 0.15);
      border-color: #EF3340;
    }

    .flag {
      font-size: 2.8rem;
      filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
      transition: transform 0.3s;
    }
    
    .country-btn:hover .flag {
      transform: scale(1.15) rotate(5deg);
    }

    .country-name {
      flex: 1;
      text-align: left;
      font-weight: 600;
      letter-spacing: 0.5px;
    }
    
    .country-code {
      font-family: 'Orbitron', sans-serif;
      font-size: 0.9rem;
      font-weight: 700;
      opacity: 0.7;
      letter-spacing: 2px;
      margin-right: 0.5rem;
    }

    @media (max-width: 600px) {
      .page-header {
        padding: 1rem 1.5rem;
      }
      
      .header-logo {
        height: 40px;
      }
      
      .header-title {
        font-size: 1.5rem;
      }
      
      .selector-container {
        padding: 2rem 1.5rem 1.5rem;
        margin-top: 80px;
      }
      
      .country-btn {
        font-size: 1rem;
        padding: 1.2rem 1.5rem;
        min-height: 65px;
      }
      
      .flag {
        font-size: 2.2rem;
      }
      
      .country-code {
        font-size: 0.8rem;
      }
      
      .subtitle {
        font-size: 1rem;
        margin-bottom: 1.5rem;
      }
    }
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

  <div class="selector-container">
    <p class="subtitle">Elige el país donde está tu taller</p>

    <div class="country-buttons">
      <a href="/us/" class="country-btn usa">
        <span class="flag">🇺🇸</span>
        <span class="country-code">US</span>
        <span class="country-name">United States</span>
      </a>

      <a href="/br/" class="country-btn brasil">
        <span class="flag">🇧🇷</span>
        <span class="country-code">BR</span>
        <span class="country-name">Brasil</span>
      </a>

      <a href="/ve/" class="country-btn venezuela">
        <span class="flag">🇻🇪</span>
        <span class="country-code">VE</span>
        <span class="country-name">Venezuela</span>
      </a>

      <a href="/pe/" class="country-btn peru">
        <span class="flag">🇵🇪</span>
        <span class="country-code">PE</span>
        <span class="country-name">Perú</span>
      </a>

      <a href="/cl/" class="country-btn chile">
        <span class="flag">🇨🇱</span>
        <span class="country-code">CL</span>
        <span class="country-name">Chile</span>
      </a>

      <a href="/co/" class="country-btn colombia">
        <span class="flag">🇨🇴</span>
        <span class="country-code">CO</span>
        <span class="country-name">Colombia</span>
      </a>

      <a href="/ec/" class="country-btn ecuador">
        <span class="flag">🇪🇨</span>
        <span class="country-code">EC</span>
        <span class="country-name">Ecuador</span>
      </a>

      <a href="/mx/" class="country-btn mexico">
        <span class="flag">🇲🇽</span>
        <span class="country-code">MX</span>
        <span class="country-name">México</span>
      </a>
    </div>
    
    <p style="margin-top: 1.5rem; font-size: 0.85rem; color: rgba(255, 255, 255, 0.5); font-family: 'Rajdhani', sans-serif;">
      Más países pronto · eGarage AI
    </p>
  </div>

  <script>
    // Agregar efecto de entrada
    document.addEventListener('DOMContentLoaded', function() {
      const container = document.querySelector('.selector-container');
      container.style.opacity = '0';
      container.style.transform = 'translateY(30px)';

      setTimeout(() => {
        container.style.transition = 'all 0.8s ease-out';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
      }, 100);
    });
  </script>
</body>
</html>'''

# Crear directorio si no existe
Path(file_path).parent.mkdir(parents=True, exist_ok=True)

# Escribir el archivo completo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado completamente")
print("   - Título: eGarage (sin texto adicional)")
print("   - Header: Solo logo (sin texto)")
print("   - Un solo USA (sin duplicados)")
print("   - 8 países: US, BR, VE, PE, CL, CO, EC, MX")
print("   - Fondo animado con grid y partículas")
print("   - Estilos futuristas mejorados")

PYEOF

touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
