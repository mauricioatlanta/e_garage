#!/bin/bash
# Script para agregar la URL /legal/ y aplicar el template mejorado

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Agregando URL /legal/ y aplicando template mejorado..."

# 1. Agregar URL en gestion_taller/urls.py
python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya existe la URL
if 'path("legal/' in content:
    print("ℹ️  URL /legal/ ya existe")
else:
    # Buscar donde agregar la URL (después de registro/)
    if 'path("registro/", registro, name="registro"),' in content:
        content = content.replace(
            'path("registro/", registro, name="registro"),',
            'path("registro/", registro, name="registro"),\n    # Términos y condiciones\n    path("legal/", TemplateView.as_view(template_name="legal.html"), name="legal"),'
        )
        print("✅ URL /legal/ agregada")
    else:
        print("⚠️  No se encontró el patrón para agregar la URL")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF

# 2. Aplicar template mejorado
python3 << 'PYEOF'
file_path = "templates/legal.html"

content = '''{% extends "base.html" %}
{% load static %}
{% block title %}Términos y Condiciones | eGarage{% endblock %}

{% block content %}
<div class="relative min-h-screen py-16 px-4 overflow-hidden">
  <!-- Fondo animado -->
  <div class="fixed inset-0 bg-gradient-to-br from-[#0a0a23] via-[#1a1a2e] to-[#0f1419] z-0"></div>
  <div class="fixed inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(0,230,255,0.15),transparent_50%)] z-0"></div>
  
  <!-- Contenido -->
  <div class="relative z-10 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="text-center mb-12">
      <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage" class="h-20 mx-auto mb-6 filter drop-shadow-[0_0_30px_rgba(0,230,255,0.8)]">
      <h1 class="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
        Términos y Condiciones
      </h1>
      <p class="text-cyan-300 text-lg">Política de Privacidad y Uso del Servicio</p>
    </div>

    <!-- Tarjetas de contenido -->
    <div class="space-y-6">
      <!-- Términos y Condiciones -->
      <div class="bg-gradient-to-br from-[#0d1117cc] via-[#1a2233cc] to-[#0d1117cc] backdrop-blur-xl rounded-2xl border-2 border-cyan-400/30 p-8 shadow-2xl hover:border-cyan-400/50 transition-all">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-2xl">
            📜
          </div>
          <h2 class="text-2xl font-bold text-cyan-300">Términos y Condiciones</h2>
        </div>
        <p class="text-gray-300 mb-4 leading-relaxed">
          El uso de eGarage implica la aceptación de estos términos. El servicio se provee "tal cual" y puede cambiar sin previo aviso. El usuario es responsable de la veracidad de los datos ingresados y del uso adecuado de la plataforma.
        </p>
        <ul class="space-y-3 text-gray-300">
          <li class="flex items-start gap-3">
            <span class="text-cyan-400 mt-1">▸</span>
            <span>No se permite el uso para actividades ilícitas.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-cyan-400 mt-1">▸</span>
            <span>La información ingresada es responsabilidad del usuario.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-cyan-400 mt-1">▸</span>
            <span>Nos reservamos el derecho de suspender cuentas por mal uso.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-cyan-400 mt-1">▸</span>
            <span>El usuario debe mantener la confidencialidad de sus credenciales de acceso.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-cyan-400 mt-1">▸</span>
            <span>eGarage no se hace responsable por pérdidas derivadas del uso incorrecto del sistema.</span>
          </li>
        </ul>
      </div>

      <!-- Política de Privacidad -->
      <div class="bg-gradient-to-br from-[#0d1117cc] via-[#1a2233cc] to-[#0d1117cc] backdrop-blur-xl rounded-2xl border-2 border-purple-400/30 p-8 shadow-2xl hover:border-purple-400/50 transition-all">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-2xl">
            🔒
          </div>
          <h2 class="text-2xl font-bold text-purple-300">Política de Privacidad</h2>
        </div>
        <p class="text-gray-300 mb-4 leading-relaxed">
          Respetamos tu privacidad. Los datos personales se usan solo para la operación del sistema y no se comparten con terceros salvo obligación legal. Puedes solicitar la eliminación de tu cuenta y datos en cualquier momento.
        </p>
        <ul class="space-y-3 text-gray-300">
          <li class="flex items-start gap-3">
            <span class="text-purple-400 mt-1">▸</span>
            <span>Solo recolectamos datos necesarios para el funcionamiento del servicio.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-purple-400 mt-1">▸</span>
            <span>No vendemos ni compartimos datos con terceros sin tu consentimiento.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-purple-400 mt-1">▸</span>
            <span>Puedes contactarnos para ejercer tus derechos ARCO (Acceso, Rectificación, Cancelación y Oposición).</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-purple-400 mt-1">▸</span>
            <span>Utilizamos medidas de seguridad avanzadas para proteger tu información.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-purple-400 mt-1">▸</span>
            <span>Los datos se almacenan en servidores seguros y se respetan las normativas de protección de datos.</span>
          </li>
        </ul>
      </div>

      <!-- Propiedad Intelectual -->
      <div class="bg-gradient-to-br from-[#0d1117cc] via-[#1a2233cc] to-[#0d1117cc] backdrop-blur-xl rounded-2xl border-2 border-yellow-400/30 p-8 shadow-2xl hover:border-yellow-400/50 transition-all">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center text-2xl">
            ⚖️
          </div>
          <h2 class="text-2xl font-bold text-yellow-300">Propiedad Intelectual</h2>
        </div>
        <p class="text-gray-300 mb-4 leading-relaxed">
          Todos los derechos de propiedad intelectual sobre eGarage, incluyendo el software, diseño, logotipos y contenido, son propiedad de <strong class="text-cyan-400">AtlantaReciclajes</strong>.
        </p>
        <ul class="space-y-3 text-gray-300">
          <li class="flex items-start gap-3">
            <span class="text-yellow-400 mt-1">▸</span>
            <span>El contenido generado por el usuario permanece como propiedad del usuario.</span>
          </li>
          <li class="flex items-start gap-3">
            <span class="text-yellow-400 mt-1">▸</span>
            <span>No está permitida la reproducción, distribución o modificación del software sin autorización.</span>
          </li>
        </ul>
      </div>

      <!-- Contacto Legal -->
      <div class="bg-gradient-to-br from-[#0d1117cc] via-[#1a2233cc] to-[#0d1117cc] backdrop-blur-xl rounded-2xl border-2 border-green-400/30 p-8 shadow-2xl hover:border-green-400/50 transition-all">
        <div class="flex items-center gap-4 mb-6">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-2xl">
            📧
          </div>
          <h2 class="text-2xl font-bold text-green-300">Contacto Legal</h2>
        </div>
        <p class="text-gray-300 mb-4 leading-relaxed">
          Para consultas legales, solicitudes de datos o cualquier asunto relacionado con estos términos, puedes contactarnos:
        </p>
        <div class="space-y-2 text-gray-300">
          <p>
            <strong class="text-cyan-400">Email:</strong> 
            <a href="mailto:suscripcion@atlantareciclajes.cl" class="text-cyan-400 hover:text-cyan-300 underline transition-colors">
              suscripcion@atlantareciclajes.cl
            </a>
          </p>
          <p class="text-sm text-gray-400 mt-4">
            <strong>Titular de los derechos:</strong> <span class="text-cyan-300">AtlantaReciclajes</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="text-center mt-12 pt-8 border-t border-cyan-400/20">
      <p class="text-gray-400 text-sm">
        eGarage {{ APP_VERSION|default:"v1.0" }} — {{ COPYRIGHT_TEXT|default:"© 2024" }}
      </p>
      <a href="/" class="inline-block mt-6 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-cyan-500/50">
        Volver al Inicio
      </a>
    </div>
  </div>
</div>

<style>
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .space-y-6 > div {
    animation: fadeIn 0.6s ease-out backwards;
  }
  
  .space-y-6 > div:nth-child(1) { animation-delay: 0.1s; }
  .space-y-6 > div:nth-child(2) { animation-delay: 0.2s; }
  .space-y-6 > div:nth-child(3) { animation-delay: 0.3s; }
  .space-y-6 > div:nth-child(4) { animation-delay: 0.4s; }
</style>
{% endblock %}
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Template legal.html actualizado con diseño futurista")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de cambios:"
echo "  - URL /legal/ agregada en gestion_taller/urls.py"
echo "  - Template legal.html rediseñado con estilo futurista"
echo "  - Diseño de tarjetas premium con efectos hover"
echo "  - Animaciones de entrada escalonadas"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



