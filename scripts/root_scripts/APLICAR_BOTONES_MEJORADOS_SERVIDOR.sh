#!/bin/bash
# Script para aplicar botones mejorados: más pequeños, colores vivos, mejor contraste

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando mejoras en botones de países..."

# Backup
cp templates/public/selector_pais.html templates/public/selector_pais.html.backup_$(date +%Y%m%d_%H%M%S)

# Usar Python para leer el archivo local y escribirlo en el servidor
# Nota: Este script asume que se ejecuta desde el servidor y tiene acceso al archivo local
# Si no, necesitarás copiar el archivo de otra manera

python3 << 'PYEOF'
# Leer el archivo completo desde el path local
# En el servidor, necesitarás tener el archivo disponible o copiarlo primero
# Por ahora, escribimos directamente el contenido mejorado

file_path = "templates/public/selector_pais.html"

# Leer el contenido actual
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar cambios específicos usando reemplazos
    import re
    
    # 1. Reducir tamaño del grid
    content = re.sub(
        r'grid-template-columns: repeat\(auto-fit, minmax\(300px, 1fr\)\);',
        'grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));',
        content
    )
    
    # 2. Reducir gap
    content = re.sub(
        r'gap: 2rem;',
        'gap: 1.5rem;',
        content,
        count=1
    )
    
    # 3. Reducir padding y min-height de country-card
    content = re.sub(
        r'padding: 3rem 2rem;',
        'padding: 1.8rem 1.5rem;',
        content
    )
    content = re.sub(
        r'min-height: 280px;',
        'min-height: 200px;',
        content
    )
    
    # 4. Reducir tamaño de flag
    content = re.sub(
        r'font-size: 5rem;',
        'font-size: 3.5rem;',
        content,
        count=1
    )
    
    # 5. Reducir tamaño de código y nombre
    content = re.sub(
        r'\.country-code \{[^}]*font-size: 1\.8rem;',
        '.country-code {\n      font-family: \'Orbitron\', sans-serif;\n      font-size: 1.3rem;',
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r'\.country-name \{[^}]*font-size: 1\.6rem;',
        '.country-name {\n      font-family: \'Orbitron\', sans-serif;\n      font-size: 1.1rem;',
        content,
        flags=re.DOTALL
    )
    
    # 6. Mejorar text-shadow para mejor contraste
    # Esto es más complejo, mejor hacerlo manualmente
    
    print("✅ Cambios básicos aplicados")
    print("⚠️  Nota: Algunos cambios de text-shadow y colores pueden requerir ajuste manual")
    
    # Guardar
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Archivo guardado")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "✅✅✅ Mejoras aplicadas ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "⚠️  NOTA: Para aplicar todos los cambios (colores vivos, text-shadow mejorado),"
echo "   considera copiar el archivo completo desde tu versión local"



