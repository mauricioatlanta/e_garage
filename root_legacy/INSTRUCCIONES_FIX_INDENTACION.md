# Instrucciones para Corregir Error de Indentación

## Problema
Error de indentación en `taller/documentos/views.py` línea 1224:
```
IndentationError: unexpected indent (views.py, line 1224)
```

## Solución Rápida

### Opción 1: Ejecutar el script bash (Recomendado)

En el servidor, ejecuta:

```bash
cd /home/atlantareciclajes/apps/egarage/current && \
cp taller/documentos/views.py taller/documentos/views.py.backup && \
bash EJECUTAR_EN_SERVIDOR.sh
```

### Opción 2: Comando Python directo

Si prefieres ejecutar directamente el comando Python:

```bash
cd /home/atlantareciclajes/apps/egarage/current && \
cp taller/documentos/views.py taller/documentos/views.py.backup && \
python3 << 'PYEOF'
import sys

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar línea de cierre del f-string
target_idx = None
for i, line in enumerate(lines):
    if '¡Gracias por confiar en nuestros servicios!"""' in line:
        target_idx = i
        break

if target_idx is None:
    print("❌ No se encontró la línea")
    sys.exit(1)

# Corregir indentación (4 espacios)
base_indent = 4
fixed = False

for i in range(target_idx + 1, min(target_idx + 21, len(lines))):
    line = lines[i]
    stripped = line.lstrip()
    
    if not stripped:
        continue
    
    # Reemplazar tabs
    if '\t' in line:
        line = line.replace('\t', '    ')
        lines[i] = line
        fixed = True
    
    if stripped and not stripped.startswith('#'):
        current_indent = len(line) - len(stripped)
        if abs(current_indent - base_indent) > 1:
            print(f"🔧 Línea {i+1}: {current_indent} -> {base_indent} espacios")
            lines[i] = ' ' * base_indent + stripped
            fixed = True

if fixed:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Verificar sintaxis
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        print("✅ Archivo corregido y sintaxis válida")
    except SyntaxError as e:
        print(f"❌ Error en línea {e.lineno}: {e.msg}")
        sys.exit(1)
else:
    print("⚠️  No se encontraron problemas")
PYEOF
```

### Opción 3: Usar el script Python standalone

Si subes el archivo `fix_views_indentation.py` al servidor:

```bash
cd /home/atlantareciclajes/apps/egarage/current && \
python3 fix_views_indentation.py
```

## Verificación

Después de ejecutar el fix, verifica que no hay errores de sintaxis:

```bash
python3 -m py_compile taller/documentos/views.py
```

Si no hay errores, el comando no mostrará nada.

## Restaurar Backup

Si algo sale mal, puedes restaurar el backup:

```bash
cp taller/documentos/views.py.backup taller/documentos/views.py
```

