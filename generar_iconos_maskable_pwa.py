"""
Script para generar iconos PNG MASKABLE optimizados para PWA.
Crea iconos adaptativos siguiendo las especificaciones de Android para iconos maskable.

Características:
- Sin texto (solo símbolo central)
- Respeta área segura (60-80% del centro)
- Fondo #0a0e27 (color del tema)
- Estilo neón azul futurista
- Múltiples tamaños para PWA

Requiere: pip install pillow
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


# Colores del tema eGarage
BG_COLOR = (10, 14, 39)  # #0a0e27
NEON_CYAN = (0, 212, 255)  # #00d4ff
NEON_BLUE = (0, 145, 255)  # #0091ff
NEON_PURPLE = (108, 0, 255)  # #6c00ff
NEON_BRIGHT = (0, 240, 255)  # #00f0ff


def draw_gear_with_car(draw, center_x, center_y, size, scale_factor=1.0):
    """
    Dibuja el engranaje con el auto en el centro.
    scale_factor controla el tamaño (0.6-0.8 para área segura)
    """
    # Radio del engranaje (60-70% del área segura)
    gear_radius = int(size * 0.20 * scale_factor)

    # Sombra del engranaje
    shadow_offset = 2
    for i in range(3):
        alpha = 60 - (i * 20)
        draw.ellipse(
            [
                center_x - gear_radius - shadow_offset + i,
                center_y - gear_radius - shadow_offset + i,
                center_x + gear_radius + shadow_offset - i,
                center_y + gear_radius + shadow_offset - i,
            ],
            outline=(*NEON_CYAN, alpha),
            width=3 - i,
        )

    # Círculo exterior del engranaje
    for i in range(4, 0, -1):
        alpha = int(200 + (i * 10))
        draw.ellipse(
            [
                center_x - gear_radius,
                center_y - gear_radius,
                center_x + gear_radius,
                center_y + gear_radius,
            ],
            outline=(*NEON_CYAN, alpha),
            width=i,
        )

    # Dientes del engranaje (8 dientes)
    tooth_length = int(gear_radius * 0.25)
    tooth_width = max(3, int(size * 0.015))
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        start_radius = gear_radius

        # Punto de inicio del diente (en el borde del círculo)
        x1 = center_x + int(start_radius * math.cos(rad))
        y1 = center_y + int(start_radius * math.sin(rad))

        # Punto final del diente (fuera del círculo)
        end_radius = gear_radius + tooth_length
        x2 = center_x + int(end_radius * math.cos(rad))
        y2 = center_y + int(end_radius * math.sin(rad))

        # Dibujar diente
        points = [
            (
                x1 - int(tooth_width * math.cos(rad + math.pi / 2)),
                y1 - int(tooth_width * math.sin(rad + math.pi / 2)),
            ),
            (
                x2 - int(tooth_width * math.cos(rad + math.pi / 2)),
                y2 - int(tooth_width * math.sin(rad + math.pi / 2)),
            ),
            (
                x2 + int(tooth_width * math.cos(rad + math.pi / 2)),
                y2 + int(tooth_width * math.sin(rad + math.pi / 2)),
            ),
            (
                x1 + int(tooth_width * math.cos(rad + math.pi / 2)),
                y1 + int(tooth_width * math.sin(rad + math.pi / 2)),
            ),
        ]
        draw.polygon(points, fill=(*NEON_BLUE, 220), outline=(*NEON_CYAN, 255))

    # Auto futurista en el centro
    car_size = int(gear_radius * 0.6)

    # Carrocería principal del auto
    car_points = [
        (center_x - car_size, center_y - int(car_size * 0.3)),
        (center_x - int(car_size * 0.7), center_y - int(car_size * 0.6)),
        (center_x + int(car_size * 0.7), center_y - int(car_size * 0.6)),
        (center_x + car_size, center_y - int(car_size * 0.3)),
        (center_x + car_size, center_y + int(car_size * 0.3)),
        (center_x + int(car_size * 0.8), center_y + int(car_size * 0.4)),
        (center_x - int(car_size * 0.8), center_y + int(car_size * 0.4)),
        (center_x - car_size, center_y + int(car_size * 0.3)),
    ]

    # Dibujar carrocería con gradiente simulado
    draw.polygon(car_points, fill=(*NEON_BLUE, 180), outline=(*NEON_CYAN, 255))

    # Parabrisas
    windshield_points = [
        (center_x - int(car_size * 0.6), center_y - int(car_size * 0.4)),
        (center_x - int(car_size * 0.2), center_y - int(car_size * 0.55)),
        (center_x + int(car_size * 0.2), center_y - int(car_size * 0.55)),
        (center_x + int(car_size * 0.6), center_y - int(car_size * 0.4)),
        (center_x + int(car_size * 0.5), center_y - int(car_size * 0.35)),
        (center_x - int(car_size * 0.5), center_y - int(car_size * 0.35)),
    ]
    draw.polygon(windshield_points, fill=(*NEON_BRIGHT, 150))

    # Faros delanteros
    headlight_radius = max(2, int(size * 0.008))
    for offset in [-int(car_size * 0.6), int(car_size * 0.6)]:
        draw.ellipse(
            [
                center_x + offset - headlight_radius,
                center_y - int(car_size * 0.15) - headlight_radius,
                center_x + offset + headlight_radius,
                center_y - int(car_size * 0.15) + headlight_radius,
            ],
            fill=(*NEON_BRIGHT, 255),
            outline=(*NEON_CYAN, 200),
        )

        # Brillo del faro
        draw.ellipse(
            [
                center_x + offset - headlight_radius // 2,
                center_y - int(car_size * 0.15) - headlight_radius // 2,
                center_x + offset + headlight_radius // 2,
                center_y - int(car_size * 0.15) + headlight_radius // 2,
            ],
            fill=(255, 255, 255, 200),
        )

    # Centro del engranaje
    center_radius = int(gear_radius * 0.25)
    draw.ellipse(
        [
            center_x - center_radius,
            center_y - center_radius,
            center_x + center_radius,
            center_y + center_radius,
        ],
        fill=(*BG_COLOR, 200),
        outline=(*NEON_CYAN, 200),
    )

    # Centro brillante
    inner_radius = int(center_radius * 0.5)
    draw.ellipse(
        [
            center_x - inner_radius,
            center_y - inner_radius,
            center_x + inner_radius,
            center_y + inner_radius,
        ],
        fill=(*NEON_CYAN, 255),
    )


def add_glow_effect(img, iterations=2):
    """Aplica un efecto de brillo suave a la imagen"""
    for _ in range(iterations):
        blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
        # Mezclar la imagen original con la difuminada
        img = Image.blend(img, blurred, 0.3)
    return img


def create_maskable_icon(size, output_path):
    """
    Crea un icono maskable de tamaño especificado.
    Respeta el área segura (80% del centro) para evitar recortes.
    """
    # Crear imagen con fondo del tema
    img = Image.new("RGBA", (size, size), (*BG_COLOR, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    center_x = size // 2
    center_y = size // 2

    # Agregar un ligero gradiente de fondo
    for i in range(size):
        alpha = int(255 * (1 - (i / size) * 0.1))
        color = (
            int(BG_COLOR[0] * (1 + (i / size) * 0.1)),
            int(BG_COLOR[1] * (1 + (i / size) * 0.05)),
            int(BG_COLOR[2] * (1 + (i / size) * 0.15)),
            alpha,
        )
        draw.rectangle([(0, i), (size, i + 1)], fill=color)

    # Agregar círculos decorativos sutiles en el fondo
    for radius, opacity in [(size * 0.4, 0.05), (size * 0.6, 0.03)]:
        draw.ellipse(
            [
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ],
            outline=(*NEON_CYAN, int(255 * opacity)),
            width=1,
        )

    # Dibujar el símbolo central (80% del área central para área segura)
    draw_gear_with_car(draw, center_x, center_y, size, scale_factor=0.75)

    # Aplicar efecto de brillo suave
    img = add_glow_effect(img, iterations=1)

    # Guardar
    img.save(output_path, "PNG", optimize=True)
    return img


def generate_all_maskable_icons():
    """Genera todos los iconos maskable en los tamaños requeridos"""
    print("=" * 70)
    print("🚀 GENERADOR DE ICONOS MASKABLE PWA - eGARAGE")
    print("=" * 70)
    print("\n📋 Características:")
    print("   ✓ Sin texto (solo símbolo)")
    print("   ✓ Área segura respetada (75% del centro)")
    print("   ✓ Fondo #0a0e27")
    print("   ✓ Estilo neón azul futurista")
    print("   ✓ Optimizado para iconos maskable\n")

    output_dir = Path("static/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tamaños requeridos por el manifest.json y PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    print("🎨 Generando iconos...\n")

    for size in sizes:
        output_path = output_dir / f"egarage_icon_{size}x{size}.png"

        try:
            create_maskable_icon(size, output_path)
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"   ✓ {output_path.name:30s} ({file_size:6.1f} KB)")
        except Exception as e:
            print(f"   ❌ Error generando {size}x{size}: {e}")
            continue

    # Generar también el de 1024 para alta resolución
    size_1024 = 1024
    output_path_1024 = output_dir / f"egarage_icon_{size_1024}x{size_1024}.png"
    try:
        create_maskable_icon(size_1024, output_path_1024)
        file_size = output_path_1024.stat().st_size / 1024
        print(f"   ✓ {output_path_1024.name:30s} ({file_size:6.1f} KB)")
    except Exception as e:
        print(f"   ❌ Error generando {size_1024}x{size_1024}: {e}")

    # Copiar el de 512x512 como logo por defecto
    default_logo = output_dir / "egarage_default_logo.png"
    source_512 = output_dir / "egarage_icon_512x512.png"

    if source_512.exists():
        import shutil

        shutil.copy2(source_512, default_logo)
        print(f"\n   ✓ Actualizado: {default_logo.name}")

    print("\n" + "=" * 70)
    print("✅ ¡Iconos maskable generados exitosamente!")
    print("=" * 70)
    print("\n📱 Próximos pasos:")
    print("   1. Ejecuta: python manage.py collectstatic --no-input")
    print("   2. Limpia el caché del navegador en tu celular")
    print("   3. Desinstala la PWA antigua si existe")
    print("   4. Reinstala la PWA para ver los nuevos iconos")
    print("=" * 70)


if __name__ == "__main__":
    try:
        generate_all_maskable_icons()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback

        traceback.print_exc()
