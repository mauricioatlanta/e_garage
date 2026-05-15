#!/usr/bin/env python
import io
import os

from PIL import Image, ImageDraw, ImageFont

import django
from django.core.files.base import ContentFile

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa

print("🎨 CREANDO LOGO PERSONALIZADO PARA MAURICIO1")
print("=" * 50)

try:
    # Buscar usuario mauricio1
    user = User.objects.get(username="mauricio1")
    empresa = Empresa.objects.get(user=user)

    # Crear un logo simple con PIL
    # Tamaño del logo
    width, height = 300, 150

    # Crear imagen con fondo azul
    img = Image.new("RGB", (width, height), color="#003d82")
    draw = ImageDraw.Draw(img)

    # Intentar usar una fuente
    try:
        font_large = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        # Si no encuentra arial, usar fuente por defecto
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Dibujar texto del logo
    draw.text(
        (width // 2, height // 2 - 20),
        "TURBO",
        font=font_large,
        fill="white",
        anchor="mm",
    )
    draw.text(
        (width // 2, height // 2 + 15),
        "AUTOMOTIVE",
        font=font_small,
        fill="#00ffff",
        anchor="mm",
    )

    # Dibujar un rectángulo decorativo
    draw.rectangle([10, 10, width - 10, height - 10], outline="#00ffff", width=3)

    # Guardar imagen en memoria
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Crear archivo Django
    logo_file = ContentFile(img_buffer.read(), name="logo_turbo_auto.png")

    # Guardar en empresa
    empresa.logo.save("logo_turbo_auto.png", logo_file, save=True)

    print("✅ Logo personalizado creado y guardado")
    print(f"✅ Archivo: {empresa.logo.url if empresa.logo else 'Error'}")
    print()
    print("🏢 EMPRESA PERSONALIZADA:")
    print(f"- Nombre: {empresa.nombre_taller}")
    print(f"- Empresa: {empresa.empresa}")
    print(f"- Logo: {'✅ Configurado' if empresa.logo else '❌ Sin logo'}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
