#!/usr/bin/env python3
"""
Script para corregir el error "unmatched ')'" en views.py línea 1225
"""

import sys
import re

file_path = "taller/documentos/views.py"

print("📋 Leyendo archivo...")
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("🔍 Buscando función enviar_documento_whatsapp...")

# Encontrar la función
func_start = None
for i, line in enumerate(lines):
    if "def enviar_documento_whatsapp" in line:
        func_start = i
        break

if func_start is None:
    print("❌ No se encontró la función")
    sys.exit(1)

print(f"📍 Función encontrada en línea {func_start + 1}")

# Buscar el bloque del return JsonResponse
return_start = None
for i in range(func_start, min(func_start + 100, len(lines))):
    if "return JsonResponse(" in lines[i]:
        return_start = i
        break

if return_start is None:
    print("❌ No se encontró el return JsonResponse")
    sys.exit(1)

print(f"📍 return JsonResponse encontrado en línea {return_start + 1}")

# Verificar y corregir el bloque JsonResponse
# Debe tener la estructura:
# return JsonResponse(
#     {
#         ...
#     }
# )

# Leer las siguientes 15 líneas después del return
problem_area = lines[return_start : return_start + 15]

print("\n📄 Área problemática:")
for i, line in enumerate(problem_area, return_start + 1):
    print(f"{i:4d}: {repr(line)}")

# Verificar balance de paréntesis y llaves
paren_count = 0
brace_count = 0

for i in range(return_start, min(return_start + 20, len(lines))):
    line = lines[i]
    paren_count += line.count("(") - line.count(")")
    brace_count += line.count("{") - line.count("}")

print(f"\n📊 Balance: paréntesis={paren_count}, llaves={brace_count}")

# Si hay desbalance, corregir
if paren_count != 0 or brace_count != 0:
    print("⚠️  Desbalance detectado, corrigiendo...")

    # Buscar la estructura correcta del JsonResponse
    # Debe ser:
    # return JsonResponse(
    #     {
    #         "success": True,
    #         ...
    #     }
    # )

    # Encontrar dónde termina el JsonResponse
    end_idx = return_start
    paren_count = 0
    brace_count = 0
    found_open = False

    for i in range(return_start, min(return_start + 20, len(lines))):
        line = lines[i]
        if "return JsonResponse(" in line:
            paren_count = 1
            found_open = True
            continue

        if found_open:
            paren_count += line.count("(") - line.count(")")
            brace_count += line.count("{") - line.count("}")

            if paren_count == 0 and brace_count == 0:
                end_idx = i
                break

    print(f"📍 Fin del JsonResponse en línea {end_idx + 1}")

    # Reconstruir el bloque correctamente
    correct_block = [
        "    return JsonResponse(\n",
        "        {\n",
        '            "success": True,\n',
        '            "url_whatsapp": url_whatsapp,\n',
        '            "telefono": telefono,\n',
        '            "mensaje": mensaje,\n',
        "        }\n",
        "    )\n",
    ]

    # Reemplazar el bloque
    new_lines = lines[:return_start] + correct_block + lines[end_idx + 1 :]

    # Verificar sintaxis
    try:
        code = "".join(new_lines)
        compile(code, file_path, "exec")
        print("✅ Sintaxis válida después de la corrección")

        # Crear backup
        backup_path = f"{file_path}.backup_paren_fix"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"📋 Backup creado: {backup_path}")

        # Escribir archivo corregido
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("✅ Archivo corregido")

    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"   Línea {e.lineno}: {e.msg}")
        sys.exit(1)
else:
    print("✅ Paréntesis y llaves están balanceados")
    print("🔍 Verificando sintaxis completa...")

    try:
        code = "".join(lines)
        compile(code, file_path, "exec")
        print("✅ El archivo tiene sintaxis válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}:")
        print(f"   {e.msg}")
        if e.lineno <= len(lines):
            print(f"   Línea: {repr(lines[e.lineno-1][:80])}")

        # Intentar corregir específicamente el error
        if e.lineno == 1225 and "unmatched" in str(e):
            print("\n🔧 Intentando corregir línea 1225 específicamente...")

            # Leer contexto alrededor de la línea 1225
            context_start = max(0, e.lineno - 10)
            context_end = min(len(lines), e.lineno + 5)

            print("\n📄 Contexto alrededor de la línea problemática:")
            for i in range(context_start, context_end):
                marker = ">>>" if i == e.lineno - 1 else "   "
                print(f"{marker} {i+1:4d}: {repr(lines[i])}")

            # El problema podría ser que hay un paréntesis extra o falta uno
            # Verificar la estructura del return JsonResponse
            if e.lineno - 1 < len(lines):
                problem_line = lines[e.lineno - 1]

                # Si la línea tiene un ')' pero no debería, o viceversa
                # Reconstruir el bloque JsonResponse correctamente
                return_line_idx = None
                for i in range(max(0, e.lineno - 10), e.lineno):
                    if "return JsonResponse(" in lines[i]:
                        return_line_idx = i
                        break

                if return_line_idx is not None:
                    print(f"\n🔧 Reconstruyendo bloque desde línea {return_line_idx + 1}")

                    # Crear el bloque correcto
                    correct_json_response = [
                        "    return JsonResponse(\n",
                        "        {\n",
                        '            "success": True,\n',
                        '            "url_whatsapp": url_whatsapp,\n',
                        '            "telefono": telefono,\n',
                        '            "mensaje": mensaje,\n',
                        "        }\n",
                        "    )\n",
                    ]

                    # Encontrar dónde termina el bloque actual (buscar el siguiente 'def' o fin de función)
                    block_end = return_line_idx + 15
                    for i in range(return_line_idx + 1, min(return_line_idx + 20, len(lines))):
                        stripped = lines[i].strip()
                        if stripped.startswith("def ") or (
                            stripped
                            and not stripped.startswith("#")
                            and not any(c in stripped for c in ["{", "}", "(", ")", '"'])
                        ):
                            # Verificar si estamos fuera del bloque
                            if i > return_line_idx + 7:
                                block_end = i
                                break

                    # Reemplazar el bloque
                    new_lines = lines[:return_line_idx] + correct_json_response + lines[block_end:]

                    # Verificar sintaxis
                    try:
                        code = "".join(new_lines)
                        compile(code, file_path, "exec")
                        print("✅ Sintaxis válida después de la reconstrucción")

                        # Backup
                        backup_path = f"{file_path}.backup_paren_fix"
                        with open(backup_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)
                        print(f"📋 Backup: {backup_path}")

                        # Escribir
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(new_lines)
                        print("✅ Archivo corregido")

                    except SyntaxError as e2:
                        print(f"❌ Aún hay error: {e2}")
                        sys.exit(1)
