#!/bin/bash
# Script para copiar el archivo EXACTO del PC local al servidor
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "📋 Creando backup..."
cp templates/public/selector_pais.html templates/public/selector_pais.html.backup_exacto_$(date +%Y%m%d_%H%M%S)

echo "🔧 Copiando archivo exacto desde el contenido local..."

# Usar cat con heredoc para copiar el contenido exacto
cat > templates/public/selector_pais.html << 'TEMPLATE_EOF'
{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>eGarage - Selecciona tu país</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap" rel="stylesheet" />
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #0a0a23 0%, #1a1a2e 100%);
      font-family: 'Orbitron', 'Segoe UI', sans-serif;
      color: #fff;
      min-height: 100vh;
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    /* Partículas de fondo */
    .bg-particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 0;
      overflow: hidden;
    }
    .particle {
      position: absolute;
      border-radius: 50%;
      background: rgba(0, 230, 255, 0.3);
      animation: float 20s infinite ease-in-out;
    }
    .particle:nth-child(1) { width: 80px; height: 80px; left: 10%; top: 20%; animation-delay: 0s; }
    .particle:nth-child(2) { width: 60px; height: 60px; left: 80%; top: 30%; animation-delay: 2s; }
    .particle:nth-child(3) { width: 100px; height: 100px; left: 50%; top: 60%; animation-delay: 4s; }
    .particle:nth-child(4) { width: 70px; height: 70px; left: 20%; top: 80%; animation-delay: 6s; }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
      50% { transform: translateY(-30px) translateX(30px); opacity: 0.6; }
    }

    .selector-container {
      position: relative;
      z-index: 10;
      background: rgba(20, 40, 80, 0.95);
      border-radius: 32px;
      box-shadow: 0 0 60px rgba(0, 230, 255, 0.3);
      padding: 3.5rem 2.5rem 2.5rem;
      text-align: center;
      max-width: 500px;
      width: 90%;
      max-height: 90vh;
      overflow-y: auto;
      border: 1px solid rgba(0, 230, 255, 0.2);
    }

    .logo-container {
      margin-bottom: 3rem;
      position: relative;
    }
    .logo {
      height: 120px;
      width: auto;
      filter: drop-shadow(0 4px 12px rgba(0, 230, 255, 0.4));
      animation: pulse 3s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
        filter: drop-shadow(0 4px 12px rgba(0, 230, 255, 0.4));
      }
      50% {
        transform: scale(1.03);
        filter: drop-shadow(0 6px 18px rgba(0, 230, 255, 0.6));
      }
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
      justify-content: center;
      gap: 1rem;
      width: 100%;
      padding: 1.3rem;
      font-size: 1.3rem;
      font-weight: bold;
      border-radius: 16px;
      border: 2px solid transparent;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      font-family: 'Orbitron', sans-serif;
      position: relative;
      overflow: hidden;
      min-height: 70px;
    }

    .country-btn::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
      transition: left 0.5s;
    }

    .country-btn:hover::before {
      left: 100%;
    }

    .country-btn.usa {
      background: linear-gradient(135deg, #002868 0%, #0050b3 100%);
      color: #fff;
      border-color: #0050b3;
      box-shadow: 0 4px 20px rgba(0, 80, 179, 0.4);
    }

    .country-btn.usa:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(0, 80, 179, 0.6);
      border-color: #00e6ff;
    }

    .country-btn.chile {
      background: linear-gradient(135deg, #d52b1e 0%, #0033a0 100%);
      color: #fff;
      border-color: #d52b1e;
      box-shadow: 0 4px 20px rgba(213, 43, 30, 0.4);
    }

    .country-btn.chile:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(213, 43, 30, 0.6);
      border-color: #00e6ff;
    }

    .country-btn.brasil {
      background: linear-gradient(135deg, #009c3b 0%, #ffdf00 100%);
      color: #000;
      border-color: #009c3b;
      box-shadow: 0 4px 20px rgba(0, 156, 59, 0.4);
    }

    .country-btn.brasil:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(0, 156, 59, 0.6);
      border-color: #002776;
    }

    .country-btn.venezuela {
      background: linear-gradient(135deg, #FFCC00 0%, #00247D 50%, #CF142B 100%);
      color: #fff;
      border-color: #FFCC00;
      box-shadow: 0 4px 20px rgba(255, 204, 0, 0.4);
    }

    .country-btn.venezuela:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(255, 204, 0, 0.6);
      border-color: #CF142B;
    }

    .country-btn.peru {
      background: linear-gradient(135deg, #DC143C 0%, #FFFFFF 50%, #DC143C 100%);
      color: #000;
      border-color: #DC143C;
      box-shadow: 0 4px 20px rgba(220, 20, 60, 0.4);
    }

    .country-btn.mexico {
      background: linear-gradient(135deg, #006341 0%, #FFFFFF 50%, #CE1126 100%);
      color: #000;
      border-color: #006341;
      box-shadow: 0 4px 20px rgba(0, 99, 65, 0.4);
    }

    .country-btn.mexico:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(0, 99, 65, 0.6);
      border-color: #CE1126;
    }

    .country-btn.peru:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(220, 20, 60, 0.6);
      border-color: #FFFFFF;
    }

    .country-btn.colombia {
      background: linear-gradient(135deg, #FCD116 0%, #003893 50%, #CE1126 100%);
      color: #000;
      border-color: #FCD116;
      box-shadow: 0 4px 20px rgba(252, 209, 22, 0.4);
    }

    .country-btn.colombia:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(252, 209, 22, 0.6);
      border-color: #CE1126;
    }

    .country-btn.ecuador {
      background: linear-gradient(135deg, #FFD700 0%, #0033A0 50%, #EF3340 100%);
      color: #000;
      border-color: #FFD700;
      box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4);
    }

    .country-btn.ecuador:hover {
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 8px 30px rgba(255, 215, 0, 0.6);
      border-color: #EF3340;
    }

    .flag {
      font-size: 2.5rem;
    }

    .country-name {
      flex: 1;
      text-align: left;
    }

    @media (max-width: 600px) {
      .selector-container {
        padding: 2rem 1.2rem 1.5rem;
      }
      .country-btn {
        font-size: 1.1rem;
        padding: 1rem;
        min-height: 60px;
      }
      .flag {
        font-size: 1.8rem;
      }
      .logo {
        height: 100px;
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
  </div>

  <div class="selector-container">
    <div class="logo-container">
      <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage Logo" class="logo">
    </div>

    <div class="country-buttons">
      <a href="/br/" class="country-btn brasil">
        <span class="flag">🇧🇷</span>
        <span class="country-name">Brasil</span>
      </a>

      <a href="/cl/" class="country-btn chile">
        <span class="flag">🇨🇱</span>
        <span class="country-name">Chile</span>
      </a>

      <a href="/co/" class="country-btn colombia">
        <span class="flag">🇨🇴</span>
        <span class="country-name">Colombia</span>
      </a>

      <a href="/ec/" class="country-btn ecuador">
        <span class="flag">🇪🇨</span>
        <span class="country-name">Ecuador</span>
      </a>

      <a href="/mx/" class="country-btn mexico">
        <span class="flag">🇲🇽</span>
        <span class="country-name">México</span>
      </a>

      <a href="/pe/" class="country-btn peru">
        <span class="flag">🇵🇪</span>
        <span class="country-name">Perú</span>
      </a>

      <a href="/us/" class="country-btn usa">
        <span class="flag">🇺🇸</span>
        <span class="country-name">United States</span>
      </a>

      <a href="/ve/" class="country-btn venezuela">
        <span class="flag">🇻🇪</span>
        <span class="country-name">Venezuela</span>
      </a>
    </div>
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
</html>
TEMPLATE_EOF

echo "✅ Archivo copiado exactamente desde el contenido local"
echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "💡 Limpia la caché del navegador (Ctrl+Shift+Delete) y recarga (Ctrl+F5)"

