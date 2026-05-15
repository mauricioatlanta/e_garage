#!/usr/bin/env python3
"""
Script para corregir el error de indentación en taller/documentos/views.py
Específicamente en la función enviar_documento_whatsapp alrededor de la línea 1224
"""

import sys
import os

file_path = "taller/documentos/views.py"

# Verificar que el archivo existe
if not os.path.exists(file_path):
    print(f"❌ Error: No se encontró el archivo {file_path}")
    sys.exit(1)

# Crear backup
backup_path = f"{file_path}.backup_indent_fix"
print(f"📋 Creando backup en {backup_path}...")

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(backup_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✅ Backup creado")

# Buscar la función enviar_documento_whatsapp y corregir indentación
fixed = False
in_function = False
function_indent = 0

for i, line in enumerate(lines):
    # Detectar inicio de función
    if "def enviar_documento_whatsapp" in line:
        in_function = True
        function_indent = len(line) - len(line.lstrip())
        print(f"📍 Función encontrada en línea {i+1}, indentación base: {function_indent} espacios")
        continue

    # Si estamos en la función
    if in_function:
        # Detectar fin de función (siguiente función o fin de archivo)
        stripped = line.lstrip()
        if stripped.startswith("def ") and i > 0:
            # Verificar que no sea parte de un string
            if not any(
                lines[j].strip().endswith('"""') or lines[j].strip().endswith("'''")
                for j in range(max(0, i - 10), i)
            ):
                in_function = False
                continue

        # Buscar líneas problemáticas alrededor de la línea 1224
        if i >= 1210 and i < 1230:  # Rango aproximado
            # Buscar líneas con código de WhatsApp que puedan tener indentación incorrecta
            if "wa.me" in line or "mensaje.replace" in line or "url_whatsapp" in line:
                # Calcular indentación correcta (debe ser function_indent + 4 para código dentro de try)
                correct_indent = function_indent + 4
                current_indent = len(line) - len(line.lstrip())

                # Si la indentación es incorrecta, corregirla
                if current_indent != correct_indent and line.strip():
                    print(
                        f"🔧 Corrigiendo línea {i+1}: indentación {current_indent} -> {correct_indent}"
                    )
                    lines[i] = " " * correct_indent + line.lstrip()
                    fixed = True

        # Buscar líneas con "mensaje_encoded" o código relacionado
        if "mensaje_encoded" in line or ("url_whatsapp" in line and "=" in line):
            correct_indent = function_indent + 4
            current_indent = len(line) - len(line.lstrip())

            if (
                current_indent != correct_indent
                and line.strip()
                and not line.strip().startswith("#")
            ):
                print(
                    f"🔧 Corrigiendo línea {i+1}: indentación {current_indent} -> {correct_indent}"
                )
                lines[i] = " " * correct_indent + line.lstrip()
                fixed = True

# Estrategia más específica: buscar y corregir el bloque problemático
print("\n🔍 Buscando bloque específico con error de indentación...")

for i, line in enumerate(lines):
    # Buscar la línea con el mensaje de cierre
    if '¡Gracias por confiar en nuestros servicios!"""' in line:
        print(f"📍 Línea de cierre encontrada en línea {i+1}")

        # Las siguientes líneas deben tener indentación correcta
        base_indent = len(line) - len(line.lstrip())
        if base_indent == 0:
            # Si la línea de cierre está al inicio, buscar la indentación del bloque anterior
            for j in range(i - 1, max(0, i - 20), -1):
                if lines[j].strip() and not lines[j].strip().startswith("#"):
                    base_indent = len(lines[j]) - len(lines[j].lstrip())
                    break

        # Corregir las siguientes 15 líneas
        for j in range(i + 1, min(len(lines), i + 16)):
            if lines[j].strip() and not lines[j].strip().startswith("#"):
                # Las líneas de código deben tener la misma indentación que el bloque
                correct_indent = base_indent
                current_indent = len(lines[j]) - len(lines[j].lstrip())

                # Si es código (no comentario, no línea vacía), debe tener indentación correcta
                if current_indent < correct_indent and lines[j].strip():
                    print(
                        f"🔧 Corrigiendo línea {j+1}: indentación {current_indent} -> {correct_indent}"
                    )
                    lines[j] = " " * correct_indent + lines[j].lstrip()
                    fixed = True
                elif current_indent > correct_indent + 8:  # Indentación excesiva
                    print(
                        f"🔧 Corrigiendo línea {j+1}: indentación {current_indent} -> {correct_indent}"
                    )
                    lines[j] = " " * correct_indent + lines[j].lstrip()
                    fixed = True
        break

if fixed:
    # Escribir archivo corregido
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("\n✅ Archivo corregido exitosamente")
    print(f"📋 Backup guardado en: {backup_path}")
else:
    print("\n⚠️  No se encontraron problemas de indentación obvios")
    print("💡 Verificando sintaxis del archivo...")

    # Intentar compilar para verificar sintaxis
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, file_path, "exec")
        print("✅ El archivo tiene sintaxis válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis encontrado:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   {e.msg}")
        print(f"\n💡 Revisando línea {e.lineno} específicamente...")

        # Leer y mostrar la línea problemática
        if e.lineno <= len(lines):
            problem_line = lines[e.lineno - 1]
            print(f"   Contenido: {repr(problem_line)}")
            print(
                f"   Indentación actual: {len(problem_line) - len(problem_line.lstrip())} espacios"
            )

            # Intentar corregir esta línea específica
            if e.lineno > 1:
                prev_line = lines[e.lineno - 2]
                if prev_line.strip():
                    correct_indent = len(prev_line) - len(prev_line.lstrip())
                    if "try:" in prev_line or "except" in prev_line or "if " in prev_line:
                        correct_indent += 4

                    current_indent = len(problem_line) - len(problem_line.lstrip())
                    if current_indent != correct_indent and problem_line.strip():
                        print(
                            f"🔧 Corrigiendo línea {e.lineno}: indentación {current_indent} -> {correct_indent}"
                        )
                        lines[e.lineno - 1] = " " * correct_indent + problem_line.lstrip()

                        # Escribir archivo corregido
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                        print("✅ Archivo corregido")
                        sys.exit(0)
