#!/usr/bin/env python3
"""
Script simple para corregir el error de indentación en views.py línea 1224
"""

file_path = "taller/documentos/views.py"

# Crear backup
backup_path = f"{file_path}.backup"
print(f"📋 Creando backup...")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

with open(backup_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Backup creado")

# Buscar y corregir el problema específico
fixed = False
for i, line in enumerate(lines, 1):
    # Buscar líneas problemáticas con wa.me o mensaje.replace que tengan indentación incorrecta
    if ("wa.me" in line or "mensaje.replace" in line) and 'f"' in line:
        # Verificar si la indentación es incorrecta (muy poca o muy mucha)
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # La indentación correcta debería ser 4 espacios (dentro de la función, dentro del try)
        # Buscar la línea anterior para determinar la indentación correcta
        if i > 1:
            prev_line = lines[i - 2]  # i es 1-indexed, lines es 0-indexed
            if prev_line.strip():
                # Si la línea anterior es el cierre del f-string, la siguiente debe tener 4 espacios
                if '"""' in prev_line and "¡Gracias" in prev_line:
                    correct_indent = 4
                else:
                    # Usar la misma indentación que la línea anterior (si es código)
                    correct_indent = len(prev_line) - len(prev_line.lstrip())
                    if prev_line.strip().startswith("#"):
                        # Si es comentario, buscar la línea de código anterior
                        for j in range(i - 3, max(0, i - 10), -1):
                            if lines[j].strip() and not lines[j].strip().startswith("#"):
                                correct_indent = len(lines[j]) - len(lines[j].lstrip())
                                break

                # Si la indentación es muy diferente, corregirla
                if abs(indent - correct_indent) > 2 and stripped.strip():
                    print(f"🔧 Corrigiendo línea {i}: indentación {indent} -> {correct_indent}")
                    lines[i - 1] = " " * correct_indent + stripped
                    fixed = True

# Si no se encontró el problema con el método anterior, buscar específicamente la línea 1224
if not fixed:
    print("🔍 Buscando problema específico en línea 1224...")
    if len(lines) >= 1224:
        line_1224 = lines[1223]  # 0-indexed
        print(f"Línea 1224 actual: {repr(line_1224)}")

        # Buscar la línea con el cierre del f-string
        for i in range(1210, min(1225, len(lines))):
            if '¡Gracias por confiar en nuestros servicios!"""' in lines[i]:
                print(f"📍 Línea de cierre encontrada en línea {i+1}")
                # Las siguientes líneas deben tener 4 espacios de indentación
                base_indent = 4

                # Corregir las siguientes líneas
                for j in range(i + 1, min(i + 15, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith("#"):
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent != base_indent:
                            print(
                                f"🔧 Corrigiendo línea {j+1}: indentación {current_indent} -> {base_indent}"
                            )
                            lines[j] = " " * base_indent + lines[j].lstrip()
                            fixed = True
                break

if fixed:
    # Escribir archivo corregido
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("\n✅ Archivo corregido exitosamente")
else:
    print("\n⚠️  No se pudo corregir automáticamente")
    print("💡 Verificando sintaxis...")
    try:
        compile(content, file_path, "exec")
        print("✅ El archivo tiene sintaxis válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}:")
        print(f"   {e.msg}")
        if e.lineno <= len(lines):
            print(f"   Línea: {repr(lines[e.lineno-1])}")
