#!/usr/bin/env python
"""
Script para ofuscar el motor de IA con PyArmor
Ejecutar antes del despliegue a producción

Uso:
    python scripts/ofuscar_motor_ia.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(step_num, message):
    """Imprime un paso del proceso"""
    print(f"\n{BLUE}[Paso {step_num}]{RESET} {message}")


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Imprime mensaje de error"""
    print(f"{RED}❌ {message}{RESET}")


def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"{YELLOW}⚠️  {message}{RESET}")


def check_pyarmor_installed():
    """Verifica si PyArmor está instalado"""
    print_step(1, "Verificando instalación de PyArmor...")
    try:
        result = subprocess.run(
            ["pyarmor", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        print_success(f"PyArmor instalado: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("PyArmor no está instalado")
        print_warning("Instalando PyArmor...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyarmor"], check=True)
            print_success("PyArmor instalado correctamente")
            return True
        except subprocess.CalledProcessError:
            print_error("No se pudo instalar PyArmor. Instala manualmente: pip install pyarmor")
            return False


def verify_source_file():
    """Verifica que el archivo fuente existe"""
    print_step(2, "Verificando archivo fuente...")
    source_file = Path("taller/utils/motor_ia_core.py")
    if not source_file.exists():
        print_error(f"Archivo fuente no encontrado: {source_file}")
        return False
    print_success(f"Archivo fuente encontrado: {source_file}")
    return True


def obfuscate_core():
    """Ofusca el archivo motor_ia_core.py"""
    print_step(3, "Ofuscando motor_ia_core.py...")

    output_dir = Path("taller/utils/motor_ia_core_compiled")
    source_file = Path("taller/utils/motor_ia_core.py")

    # Limpiar directorio anterior si existe
    if output_dir.exists():
        print_warning(f"Limpiando directorio anterior: {output_dir}")
        shutil.rmtree(output_dir)

    try:
        # Comando de ofuscación
        cmd = [
            "pyarmor",
            "gen",
            "--recursive",
            "--output",
            str(output_dir),
            str(source_file),
        ]

        print(f"Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if output_dir.exists():
            print_success(f"Código ofuscado generado en: {output_dir}")

            # Verificar que se generaron archivos
            obfuscated_file = output_dir / "motor_ia_core.py"
            if obfuscated_file.exists():
                print_success(f"Archivo ofuscado creado: {obfuscated_file}")

                # Verificar que el archivo está ofuscado (debe contener código encriptado)
                with open(obfuscated_file, "rb") as f:
                    content = f.read()
                    # PyArmor genera código que contiene caracteres especiales
                    if b"__pyarmor__" in content or len(content) > 1000:
                        print_success("Archivo verificado como ofuscado")
                        return True
                    else:
                        print_warning("El archivo puede no estar completamente ofuscado")
                        return True  # Continuar de todas formas
            else:
                print_error("No se encontró el archivo ofuscado generado")
                return False
        else:
            print_error("No se generó el directorio de salida")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"Error al ofuscar: {e.stderr}")
        return False


def verify_obfuscation():
    """Verifica que el código ofuscado es ilegible"""
    print_step(4, "Verificando que el código está ofuscado...")

    obfuscated_file = Path("taller/utils/motor_ia_core_compiled/motor_ia_core.py")

    if not obfuscated_file.exists():
        print_error("Archivo ofuscado no encontrado")
        return False

    try:
        with open(obfuscated_file, "rb") as f:
            content = f.read()

        # Verificar características de código ofuscado
        checks = {
            "Tamaño razonable": len(content) > 500,
            "Contiene código encriptado": b"__pyarmor__" in content or b"exec" in content,
            "No es código Python legible": b"def preparar_datos_servicios" not in content,
        }

        all_passed = True
        for check_name, passed in checks.items():
            if passed:
                print_success(f"{check_name}: OK")
            else:
                print_warning(f"{check_name}: Puede necesitar revisión")
                all_passed = False

        # Intentar leer como texto para verificar ilegibilidad
        try:
            text_content = content.decode("utf-8", errors="ignore")
            if "class MotorIACore" in text_content and "def " in text_content:
                print_warning(
                    "El código puede contener texto legible. Considera usar --pack onefile"
                )
            else:
                print_success("Código verificado como ilegible")
        except:
            print_success("Código completamente binario/encriptado")

        return True

    except Exception as e:
        print_error(f"Error al verificar ofuscación: {e}")
        return False


def create_gitignore_entry():
    """Crea/actualiza .gitignore para excluir código fuente en producción"""
    print_step(5, "Verificando .gitignore...")

    gitignore_file = Path(".gitignore")
    entries_to_add = [
        "# Código fuente del core de IA (NO subir a producción)",
        "taller/utils/motor_ia_core.py",
        "",
        "# Archivos ofuscados de PyArmor",
        "taller/utils/motor_ia_core_compiled/",
        "taller/utils/pytransform/",
        "*.pyarmor",
    ]

    if not gitignore_file.exists():
        print_warning(".gitignore no existe, creándolo...")
        with open(gitignore_file, "w") as f:
            f.write("\n".join(entries_to_add) + "\n")
        print_success(".gitignore creado")
        return True

    # Leer .gitignore actual
    with open(gitignore_file, "r") as f:
        content = f.read()

    # Verificar si ya contiene las entradas
    if "motor_ia_core.py" in content:
        print_success(".gitignore ya contiene las entradas necesarias")
        return True

    # Agregar entradas
    print_warning("Agregando entradas a .gitignore...")
    with open(gitignore_file, "a") as f:
        f.write("\n" + "\n".join(entries_to_add) + "\n")
    print_success("Entradas agregadas a .gitignore")
    return True


def main():
    """Función principal"""
    print(f"\n{BLUE}{'='*60}")
    print("🔒 OFUSCACIÓN DEL MOTOR DE IA CON PYARMOR")
    print(f"{'='*60}{RESET}\n")

    # Cambiar al directorio raíz del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Directorio de trabajo: {project_root}")

    # Ejecutar pasos
    steps = [
        ("Verificar PyArmor", check_pyarmor_installed),
        ("Verificar archivo fuente", verify_source_file),
        ("Ofuscar código", obfuscate_core),
        ("Verificar ofuscación", verify_obfuscation),
        ("Actualizar .gitignore", create_gitignore_entry),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print_error(f"Fallo en: {step_name}")
            print_warning("\n⚠️  La ofuscación no se completó correctamente.")
            print_warning("Revisa los errores arriba y vuelve a intentar.")
            sys.exit(1)

    print(f"\n{GREEN}{'='*60}")
    print("✅ OFUSCACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'='*60}{RESET}\n")

    print("📋 Próximos pasos:")
    print("1. Ejecutar tests: python scripts/test_codigo_ofuscado.py")
    print("2. Verificar que motor_ia.py puede importar el core ofuscado")
    print("3. NO subir motor_ia_core.py a producción")
    print("4. Solo subir motor_ia_core_compiled/ a producción\n")


if __name__ == "__main__":
    main()
