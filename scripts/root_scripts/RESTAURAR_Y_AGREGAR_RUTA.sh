#!/bin/bash
# Script para restaurar urls.py y agregar la ruta correctamente
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup del archivo actual..."
cp "$FILE" "$FILE.backup_antes_restaurar_$(date +%Y%m%d_%H%M%S)"

echo "🔄 Restaurando desde Git..."
git checkout HEAD -- "$FILE" 2>/dev/null || {
    echo "⚠️  Git no disponible, buscando backup más reciente..."
    BACKUP=$(ls -t "$FILE".backup_* 2>/dev/null | grep -v "antes_restaurar" | head -1)
    if [ -n "$BACKUP" ]; then
        echo "📋 Restaurando desde: $BACKUP"
        cp "$BACKUP" "$FILE"
    else
        echo "❌ No se encontró backup válido"
        exit 1
    fi
}

echo "✅ Archivo restaurado"
echo "🔧 Agregando ruta cl/egarage/ correctamente..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si ya existe
has_route = any('cl/egarage/' in line and 'RedirectView' in line for line in lines)

if has_route:
    print("✅ La ruta cl/egarage/ ya existe")
else:
    print("🔧 Agregando ruta cl/egarage/...")
    new_lines = []
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Buscar cl/centro-operaciones-espacial/ y agregar después
        if 'cl/centro-operaciones-espacial/' in line:
            # Buscar el cierre de este path (name= y ),)
            j = i + 1
            while j < len(lines) and j < i + 5:
                if 'name="cl_centro_operaciones_redirect"' in lines[j]:
                    # Buscar el ), que cierra este path
                    k = j + 1
                    while k < len(lines) and k < j + 3:
                        if '),' in lines[k]:
                            # Insertar la nueva ruta aquí
                            indent = len(lines[k]) - len(lines[k].lstrip())
                            new_lines.append(' ' * indent + 'path(\n')
                            new_lines.append(' ' * indent + '    "cl/egarage/",\n')
                            new_lines.append(' ' * indent + '    RedirectView.as_view(url="/cl/es/egarage/", permanent=False),\n')
                            new_lines.append(' ' * indent + '    name="cl_egarage_redirect",\n')
                            new_lines.append(' ' * indent + '),\n')
                            added = True
                            print(f"✅ Ruta agregada después de línea {k+1}")
                            break
                        k += 1
                    break
                j += 1
    
    if added:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # Verificar sintaxis
        import ast
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            print("✅ Sintaxis correcta")
        except SyntaxError as e:
            print(f"❌ Error de sintaxis: {e}")
    else:
        print("⚠️  No se pudo agregar la ruta")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

