#!/usr/bin/env python
"""
Script para preparar paquete de actualización completo para el servidor
Incluye todos los cambios estructurales y archivos necesarios
"""
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent
DEPLOY_DIR = BASE_DIR / "deploy_atlantareciclajes"
ZIP_NAME = "egarage_update_atlantareciclajes.zip"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Archivos y carpetas a incluir en la actualización
ARCHIVOS_INCLUIR = {
    # Templates - Estructura completa actualizada (CAMBIOS ESTRUCTURALES)
    "templates": [
        "templates/account",  # Login, signup, email confirmation
        "templates/auth",  # Auth alternativo
        "templates/cl",  # Templates Chile (es/en)
        "templates/us",  # Templates USA (es/en)
        "templates/taller",  # Templates principales del taller
        "templates/email",  # Emails de sistema
        "templates/emails",  # Emails adicionales
        "templates/portal",  # Portal de clientes
        "templates/suscripcion",  # Suscripciones
        "templates/onboarding",  # Onboarding por país
        "templates/registration",  # Registro
        "templates/components",  # Componentes reutilizables
        "templates/errors",  # Páginas de error
        "templates/landing",  # Landing pages
        "templates/base.html",  # Template base
        "templates/landing_inicio.html",  # Landing principal
        "templates/admin_panel",  # Panel admin
        "templates/analytics",  # Analytics
        "templates/business_intelligence",  # BI
        "templates/settings",  # Settings
        "templates/suspension",  # Suspensión
        "templates/br",  # Brasil
        "templates/co",  # Colombia
        "templates/ec",  # Ecuador
        "templates/mx",  # México
        "templates/pe",  # Perú
        "templates/ve",  # Venezuela
    ],
    # Código Python - App taller
    "taller": [
        "taller/views_extra",  # Views adicionales
        "taller/models",  # Modelos (incluye pago.py)
        "taller/forms",  # Formularios
        "taller/middleware",  # Middleware personalizado
        "taller/context_processors",  # Context processors
        "taller/management",  # Management commands
        "taller/signals.py",  # Signals
        "taller/apps.py",  # Configuración app
        "taller/urls.py",  # URLs del taller
        "taller/views.py",  # Views principales
        "taller/admin.py",  # Admin
        "taller/backends",  # Backends personalizados
    ],
    # Configuración Django
    "gestion_taller": [
        "gestion_taller/urls.py",  # URLs principales
        "gestion_taller/settings.py",  # Settings (importante)
        "gestion_taller/wsgi.py",  # WSGI
        "gestion_taller/asgi.py",  # ASGI
    ],
    # Otros archivos importantes
    "otros": [
        "manage.py",  # Script de gestión
        "core",  # App core
        "ubicacion",  # App ubicación
    ],
}

# Archivos a excluir (no necesarios en servidor)
EXCLUIR_PATRONES = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git",
    ".gitignore",
    "*.log",
    "*.bak",
    "*.backup",
    ".env",
    "venv",
    ".venv",
    "node_modules",
    "staticfiles",
    "media",
    "db.sqlite3",
    "*.zip",
    "_archive",
    "_backup",
    "backups",
    "htmlcov",
    ".pytest_cache",
    "*.code-workspace",
    ".idea",
    ".vscode",
]


def deberia_excluir(ruta):
    """Verifica si un archivo/carpeta debe ser excluido"""
    ruta_str = str(ruta)
    nombre = ruta.name

    # Excluir archivos ocultos
    if nombre.startswith("."):
        return True

    # Verificar patrones de exclusión
    for patron in EXCLUIR_PATRONES:
        if patron in ruta_str:
            return True

    return False


def copiar_archivos(origen, destino, categoria):
    """Copia archivos y carpetas manteniendo estructura"""
    archivos_copiados = []
    errores = []

    for item in ARCHIVOS_INCLUIR.get(categoria, []):
        origen_path = BASE_DIR / item
        if not origen_path.exists():
            errores.append(f"⚠️  No encontrado: {item}")
            continue

        # Calcular ruta destino relativa
        if item.startswith("templates/"):
            destino_path = destino / item
        elif item.startswith("taller/"):
            destino_path = destino / item
        elif item.startswith("gestion_taller/"):
            destino_path = destino / item
        else:
            destino_path = destino / item

        try:
            if origen_path.is_file():
                # Copiar archivo
                destino_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origen_path, destino_path)
                archivos_copiados.append(item)
            elif origen_path.is_dir():
                # Copiar directorio completo
                shutil.copytree(
                    origen_path,
                    destino_path,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", "*.pyo", ".git", "*.log", "*.bak", "*.backup"
                    ),
                    dirs_exist_ok=True,
                )
                archivos_copiados.append(item)
        except Exception as e:
            errores.append(f"❌ Error copiando {item}: {e}")

    return archivos_copiados, errores


def crear_zip(directorio, archivo_zip):
    """Crea archivo ZIP desde directorio"""
    print(f"\n📦 Creando archivo ZIP: {archivo_zip.name}")

    with zipfile.ZipFile(archivo_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directorio):
            # Filtrar directorios a excluir
            dirs[:] = [d for d in dirs if not deberia_excluir(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file
                if deberia_excluir(file_path):
                    continue

                # Ruta relativa dentro del ZIP
                arcname = file_path.relative_to(directorio)
                zipf.write(file_path, arcname)

    tamaño = archivo_zip.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ ZIP creado: {tamaño:.2f} MB")


def main():
    print("=" * 70)
    print("🚀 PREPARANDO ACTUALIZACIÓN PARA SERVIDOR")
    print("=" * 70)
    print(f"\n📁 Directorio base: {BASE_DIR}")
    print(f"📦 Directorio de despliegue: {DEPLOY_DIR}")
    print(f"⏰ Timestamp: {TIMESTAMP}\n")

    # Limpiar directorio anterior si existe
    if DEPLOY_DIR.exists():
        print(f"🧹 Limpiando directorio anterior...")
        shutil.rmtree(DEPLOY_DIR)

    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)

    # Copiar archivos por categoría
    total_copiados = []
    total_errores = []

    print("\n" + "=" * 70)
    print("📋 COPIANDO ARCHIVOS...")
    print("=" * 70)

    for categoria in ["templates", "taller", "gestion_taller", "otros"]:
        print(f"\n📂 Categoría: {categoria.upper()}")
        copiados, errores = copiar_archivos(BASE_DIR, DEPLOY_DIR, categoria)
        total_copiados.extend(copiados)
        total_errores.extend(errores)

        if copiados:
            print(f"   ✅ {len(copiados)} items copiados")
        if errores:
            for error in errores:
                print(f"   {error}")

    # Crear archivo de información
    info_file = DEPLOY_DIR / "INFO_ACTUALIZACION.txt"
    with open(info_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("INFORMACIÓN DE ACTUALIZACIÓN\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total archivos/carpetas: {len(total_copiados)}\n\n")
        f.write("ARCHIVOS INCLUIDOS:\n")
        f.write("-" * 70 + "\n")
        for item in sorted(total_copiados):
            f.write(f"  • {item}\n")
        if total_errores:
            f.write("\nADVERTENCIAS:\n")
            f.write("-" * 70 + "\n")
            for error in total_errores:
                f.write(f"  {error}\n")

    print(f"\n✅ Archivo de información creado: {info_file.name}")

    # Crear ZIP
    zip_path = BASE_DIR / ZIP_NAME
    if zip_path.exists():
        backup_zip = BASE_DIR / f"{ZIP_NAME}.backup_{TIMESTAMP}"
        shutil.move(zip_path, backup_zip)
        print(f"📦 ZIP anterior respaldado como: {backup_zip.name}")

    crear_zip(DEPLOY_DIR, zip_path)

    # Resumen final
    print("\n" + "=" * 70)
    print("✅ ACTUALIZACIÓN PREPARADA")
    print("=" * 70)
    print(f"\n📦 Archivo ZIP: {zip_path}")
    print(f"   Tamaño: {zip_path.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"\n📁 Directorio descomprimido: {DEPLOY_DIR}")
    print(f"   Total items: {len(total_copiados)}")

    if total_errores:
        print(f"\n⚠️  Advertencias: {len(total_errores)}")

    print("\n" + "=" * 70)
    print("📋 PRÓXIMOS PASOS:")
    print("=" * 70)
    print("\n1. Revisar el contenido en: deploy_atlantareciclajes/")
    print("2. Subir el ZIP al servidor con FileZilla:")
    print("   - Destino: /home/atlantareciclajes/egarage_update/")
    print("   - Archivo: egarage_update_atlantareciclajes.zip")
    print("3. Ejecutar en servidor: ./2_actualizar_FIXED.sh")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
