"""
Script para generar iconos PNG optimizados para PWA desde el SVG futurista.
Requiere: pip install cairosvg pillow
"""

import os
from pathlib import Path


def generate_pwa_icons():
    """Genera iconos PNG en múltiples tamaños para PWA"""

    try:
        import cairosvg
        from PIL import Image, ImageDraw, ImageFilter

        print("✓ Bibliotecas importadas correctamente")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n📦 Instala las dependencias necesarias con:")
        print("   pip install cairosvg pillow")
        return False

    # Rutas
    svg_path = Path("static/images/egarage_default_logo.svg")
    output_dir = Path("static/images")

    if not svg_path.exists():
        print(f"❌ No se encontró el archivo SVG: {svg_path}")
        return False

    print(f"\n🎨 Generando iconos desde: {svg_path}")

    # Tamaños requeridos para PWA
    sizes = [192, 512, 1024]  # Incluimos 1024 para mejor calidad

    for size in sizes:
        output_path = output_dir / f"egarage_icon_{size}x{size}.png"

        try:
            # Convertir SVG a PNG con el tamaño específico
            cairosvg.svg2png(
                url=str(svg_path),
                write_to=str(output_path),
                output_width=size,
                output_height=size,
                background_color="#0a0e27",  # Fondo oscuro
            )

            # Optimizar la imagen con Pillow
            img = Image.open(output_path)

            # Aplicar un ligero suavizado para mejor calidad
            img = img.filter(ImageFilter.SMOOTH)

            # Guardar con máxima calidad
            img.save(output_path, "PNG", optimize=True, quality=100)

            file_size = output_path.stat().st_size / 1024  # KB
            print(f"✓ Generado: {output_path.name} ({file_size:.1f} KB)")

        except Exception as e:
            print(f"❌ Error generando {size}x{size}: {e}")
            continue

    # Copiar el de 512x512 como el logo por defecto
    default_logo = output_dir / "egarage_default_logo.png"
    source_512 = output_dir / "egarage_icon_512x512.png"

    if source_512.exists():
        import shutil

        shutil.copy2(source_512, default_logo)
        print(f"✓ Actualizado: {default_logo.name}")

    print("\n✅ ¡Iconos generados exitosamente!")
    print("\n📱 Archivos generados:")
    print(f"   - egarage_icon_192x192.png (para Android)")
    print(f"   - egarage_icon_512x512.png (para splash screens)")
    print(f"   - egarage_icon_1024x1024.png (alta resolución)")
    print(f"   - egarage_default_logo.png (actualizado)")

    return True


def create_fallback_png():
    """Crea un PNG alternativo usando PIL si cairosvg no está disponible"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter

        print("\n🎨 Creando ícono alternativo con PIL...")

        sizes = [192, 512]
        output_dir = Path("static/images")

        for size in sizes:
            # Crear imagen con fondo oscuro
            img = Image.new("RGBA", (size, size), (10, 14, 39, 255))
            draw = ImageDraw.Draw(img)

            # Calcular proporciones
            center = size // 2
            gear_radius = int(size * 0.30)

            # Dibujar engranaje simplificado
            # Círculo exterior
            for thickness in range(4, 0, -1):
                alpha = int(255 * (thickness / 4))
                draw.ellipse(
                    [
                        center - gear_radius,
                        center - gear_radius,
                        center + gear_radius,
                        center + gear_radius,
                    ],
                    outline=(0, 212, 255, alpha),
                    width=thickness,
                )

            # Dientes del engranaje (simplificado)
            tooth_size = int(size * 0.03)
            for angle in range(0, 360, 45):
                import math

                rad = math.radians(angle)
                x = center + int((gear_radius + tooth_size) * math.cos(rad))
                y = center + int((gear_radius + tooth_size) * math.sin(rad))
                draw.ellipse(
                    [
                        x - tooth_size // 2,
                        y - tooth_size // 2,
                        x + tooth_size // 2,
                        y + tooth_size // 2,
                    ],
                    fill=(0, 145, 255, 255),
                )

            # Círculo interior brillante
            inner_radius = int(gear_radius * 0.3)
            draw.ellipse(
                [
                    center - inner_radius,
                    center - inner_radius,
                    center + inner_radius,
                    center + inner_radius,
                ],
                fill=(0, 240, 255, 255),
            )

            # Aplicar efecto de brillo
            img = img.filter(ImageFilter.SMOOTH)

            # Agregar texto
            try:
                # Intentar usar una fuente del sistema
                font_size = int(size * 0.12)
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            text = "eGARAGE"
            # Usar textbbox para obtener el tamaño del texto
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (size - text_width) // 2
            text_y = int(size * 0.65)

            # Texto con efecto de brillo
            for offset in range(3, 0, -1):
                alpha = int(100 * (offset / 3))
                draw.text((text_x, text_y), text, fill=(0, 212, 255, alpha), font=font)
            draw.text((text_x, text_y), text, fill=(0, 212, 255, 255), font=font)

            # Guardar
            output_path = output_dir / f"egarage_icon_{size}x{size}.png"
            img.save(output_path, "PNG", optimize=True)
            print(f"✓ Generado: {output_path.name}")

        # Copiar el de 512 como default
        import shutil

        source = output_dir / "egarage_icon_512x512.png"
        dest = output_dir / "egarage_default_logo.png"
        if source.exists():
            shutil.copy2(source, dest)
            print(f"✓ Actualizado: {dest.name}")

        print("\n✅ ¡Íconos generados exitosamente con PIL!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GENERADOR DE ICONOS PWA FUTURISTAS - eGARAGE")
    print("=" * 60)

    # Intentar primero con cairosvg (mejor calidad)
    success = generate_pwa_icons()

    # Si falla, usar PIL como alternativa
    if not success:
        print("\n⚠️  Intentando método alternativo...")
        create_fallback_png()

    print("\n" + "=" * 60)
    print("🔄 No olvides limpiar el caché del navegador para ver los cambios")
    print("=" * 60)
