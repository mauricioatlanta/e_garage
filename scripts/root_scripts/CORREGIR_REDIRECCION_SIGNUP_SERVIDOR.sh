#!/bin/bash
# Script para corregir la redirección después del signup en el servidor

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import os
import sys

# Actualizar taller/views_extra/custom_signup.py
file_path = "taller/views_extra/custom_signup.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya tiene la corrección
    if 'account_email_verification_sent' in content and 'requires_email_verification' in content:
        print("✅ El archivo ya tiene la corrección aplicada")
    else:
        # Buscar y reemplazar la sección problemática
        old_pattern = """        # Hacer login del usuario con backend explícito
        # Django necesita saber qué backend usar cuando hay múltiples configurados
        backend = settings.AUTHENTICATION_BACKENDS[0]  # Usar el primer backend (ModelBackend)
        user.backend = backend
        login(self.request, user, backend=backend)

        # Mensaje de éxito
        if country == "CL":
            messages.success(
                self.request, "¡Cuenta creada exitosamente! Bienvenido a eGarage Chile."
            )
        else:
            messages.success(self.request, "Account created successfully! Welcome to eGarage USA.")

        # Redirigir según el país
        if country == "CL":
            return redirect("chile:centro_operaciones")
        else:
            return redirect("usa:centro_operaciones_espacial")"""
        
        new_pattern = """        # Verificar si se requiere verificación de email
        requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"

        if requires_email_verification:
            # NO hacer login automático, dejar que allauth maneje la redirección
            # Allauth automáticamente redirige a account_email_verification_sent
            if country == "CL":
                messages.success(
                    self.request,
                    "¡Cuenta creada exitosamente! Por favor, revisa tu email para activar tu cuenta."
                )
            else:
                messages.success(
                    self.request,
                    "Account created successfully! Please check your email to activate your account."
                )
            # Usar el método de allauth para obtener la URL de confirmación
            return redirect("account_email_verification_sent")
        else:
            # Si NO se requiere verificación, hacer login automático
            backend = settings.AUTHENTICATION_BACKENDS[0]
            user.backend = backend
            login(self.request, user, backend=backend)

            # Mensaje de éxito
            if country == "CL":
                messages.success(
                    self.request, "¡Cuenta creada exitosamente! Bienvenido a eGarage Chile."
                )
                return redirect("chile:centro_operaciones")
            else:
                messages.success(self.request, "Account created successfully! Welcome to eGarage USA.")
                return redirect("usa:centro_operaciones_espacial")"""
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Archivo custom_signup.py actualizado")
        else:
            print("⚠️  No se encontró el patrón exacto, el archivo puede tener cambios manuales")
            print("   Verificando si necesita actualización...")
            if 'account_email_verification_sent' not in content:
                print("❌ El archivo NO tiene la corrección. Necesita actualización manual.")
            else:
                print("✅ El archivo parece tener la corrección")
    
    # Verificar que se importó reverse si es necesario
    if 'from django.urls import reverse' not in content and 'reverse' in content:
        # Agregar import si falta
        if 'from django.shortcuts import redirect' in content:
            content = content.replace(
                'from django.shortcuts import redirect',
                'from django.shortcuts import redirect\nfrom django.urls import reverse'
            )
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Import de reverse agregado")
    
except Exception as e:
    print(f"❌ Error al actualizar {file_path}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYEOF

# Copiar template email_verification_sent.html
cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import os

template_content = """{% extends "base.html" %}
{% load static i18n country_url %}
{% block title %}{% trans "Registro exitoso" %} | eGarage{% endblock %}

{% block content %}
<div class="relative min-h-screen flex items-center justify-center overflow-hidden">
  <canvas id="particles-bg" class="fixed inset-0 w-full h-full z-0"></canvas>
  <div class="relative z-10 w-full max-w-md">
    <div class="bg-gradient-to-br from-[#0d1117cc] via-[#1a2233cc] to-[#0d1117cc] rounded-2xl shadow-2xl p-10 border-2 border-cyan-400/40 backdrop-blur-xl">
      <div class="flex flex-col items-center mb-6">
        <img src="{% static 'img/egarage_logo.png' %}" alt="eGarage Logo" class="h-16 mb-3 drop-shadow-lg animate-pulse" style="filter: drop-shadow(0 0 20px rgba(34, 211, 238, 0.8));">
        <h1 class="text-3xl md:text-4xl font-extrabold text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-yellow-300 mb-2 tracking-tight futuristic-glow">
          <span class="lang-en" style="display: none;">Registration successful!</span>
          <span class="lang-es">¡Registro exitoso!</span>
        </h1>
      </div>
      <div class="text-cyan-100 text-center text-lg mb-4">
        <p class="mb-4">
          <span class="lang-en" style="display: none;">Please check your email to activate your account.</span>
          <span class="lang-es">Por favor, revisa tu correo electrónico para activar tu cuenta.</span>
        </p>
        <p class="text-sm text-cyan-300">
          <span class="lang-en" style="display: none;">If you don't see the email, check your spam folder or request a new confirmation link.</span>
          <span class="lang-es">Si no ves el correo, revisa tu carpeta de spam o solicita un nuevo enlace de confirmación.</span>
        </p>
      </div>
      <div class="flex flex-col gap-3 mt-6">
        <a href="{% country_url 'account_login' %}" class="block text-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-cyan-500/50">
          <span class="lang-en" style="display: none;">Go to sign in</span>
          <span class="lang-es">Ir a iniciar sesión</span>
        </a>
        <a href="{% url 'account_email_verification_sent' %}" class="block text-center px-6 py-3 bg-gray-700 hover:bg-gray-600 text-cyan-300 font-medium rounded-lg transition-all">
          <span class="lang-en" style="display: none;">Resend confirmation email</span>
          <span class="lang-es">Reenviar correo de confirmación</span>
        </a>
      </div>
    </div>
  </div>
</div>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<style>
  .futuristic-glow {
    text-shadow: 0 0 24px #00ffe7, 0 0 8px #00ffe7, 0 0 2px #fff;
    letter-spacing: 2px;
  }
</style>
<script>
// Animación de puntos tipo "espacio futurista"
const canvas = document.getElementById('particles-bg');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let w = window.innerWidth;
  let h = window.innerHeight;
  canvas.width = w;
  canvas.height = h;
  let particles = Array.from({length: 80}, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() * 2.2 + 1.2,
    dx: (Math.random() - 0.5) * 0.7,
    dy: (Math.random() - 0.5) * 0.7,
    c: `hsl(${Math.random()*360}, 100%, 70%)`
  }));
  function draw() {
    ctx.clearRect(0, 0, w, h);
    for (let p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
      ctx.fillStyle = p.c;
      ctx.shadowColor = p.c;
      ctx.shadowBlur = 12;
      ctx.fill();
    }
  }
  function update() {
    for (let p of particles) {
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > w) p.dx *= -1;
      if (p.y < 0 || p.y > h) p.dy *= -1;
    }
  }
  function animate() {
    draw();
    update();
    requestAnimationFrame(animate);
  }
  animate();
  window.addEventListener('resize', () => {
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = w;
    canvas.height = h;
  });
}

// Detectar idioma y mostrar/ocultar elementos
document.addEventListener('DOMContentLoaded', function() {
  const currentLang = '{{ LANGUAGE_CODE|default:"es" }}';
  const lang = currentLang === 'en' ? 'en' : 'es';
  
  document.querySelectorAll('.lang-en, .lang-es').forEach(function(element) {
    element.style.display = 'none';
  });
  
  document.querySelectorAll('.lang-' + lang).forEach(function(element) {
    const parent = element.parentElement;
    const isInlineContext = parent && (
      parent.tagName === 'A' || 
      parent.tagName === 'BUTTON' || 
      parent.tagName === 'SPAN' ||
      parent.classList.contains('inline') ||
      parent.style.display === 'inline' ||
      parent.style.display === 'inline-block'
    );
    element.style.display = isInlineContext ? 'inline' : 'block';
  });
});
</script>
{% endblock %}"""

template_dir = "templates/account"
os.makedirs(template_dir, exist_ok=True)

template_path = os.path.join(template_dir, "email_verification_sent.html")
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(template_content)

print(f"✅ Template creado en: {template_path}")

PYEOF

# Reiniciar el servidor
touch /var/www/www_egarage_cl_wsgi.py && \
echo "✅ Cambios aplicados y servidor reiniciado"



