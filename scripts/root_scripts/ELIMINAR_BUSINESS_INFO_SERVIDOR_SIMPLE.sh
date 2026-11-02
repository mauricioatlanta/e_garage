#!/bin/bash
# Script para eliminar la sección "Business Information" del formulario de registro

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando cambios en el servidor..."

# 1. Eliminar sección Business Information del template
python3 << 'PYEOF'
import re

file_path = "templates/auth/signup.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y eliminar la sección completa desde "SECCIÓN 2: Datos de la Empresa" hasta "SECCIÓN 3: Selección de Plan"
pattern = r'<!-- SECCIÓN 2: Datos de la Empresa -->.*?<!-- SECCIÓN 3: Selección de Plan -->'
replacement = '<!-- SECCIÓN 2: Selección de Plan -->'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Template signup.html actualizado")
else:
    print("⚠️  Sección ya eliminada o no encontrada")
PYEOF

# 2. Hacer campos opcionales en el formulario
python3 << 'PYEOF'
file_path = "taller/forms/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Hacer nombre_taller opcional
    if 'nombre_taller = forms.CharField' in line:
        new_lines.append(line)
        i += 1
        # Buscar y reemplazar required=True y "required": "required"
        while i < len(lines) and ')' not in lines[i-1] if i > 0 else True:
            if i < len(lines):
                l = lines[i]
                l = l.replace('required=True', 'required=False')
                l = l.replace('"required": "required",', '')
                new_lines.append(l)
                i += 1
                if ')' in l:
                    break
        continue
    
    # Hacer telefono opcional
    if 'telefono = forms.CharField' in line:
        new_lines.append(line)
        i += 1
        while i < len(lines) and ')' not in lines[i-1] if i > 0 else True:
            if i < len(lines):
                l = lines[i]
                l = l.replace('required=True', 'required=False')
                l = l.replace('"required": "required",', '')
                new_lines.append(l)
                i += 1
                if ')' in l:
                    break
        continue
    
    # Hacer pais opcional
    if 'pais = forms.ChoiceField' in line:
        new_lines.append(line)
        i += 1
        while i < len(lines) and ')' not in lines[i-1] if i > 0 else True:
            if i < len(lines):
                l = lines[i]
                l = l.replace('required=True', 'required=False')
                l = l.replace('"required": "required",', '')
                new_lines.append(l)
                i += 1
                if ')' in l:
                    break
        continue
    
    # Actualizar clean_pais
    if 'def clean_pais(self):' in line:
        new_lines.append(line)
        i += 1
        # Reemplazar el contenido del método
        if i < len(lines) and 'pais = self.cleaned_data.get("pais")' in lines[i]:
            new_lines.append('        pais = self.cleaned_data.get("pais")\n')
            new_lines.append('        # El país es opcional - se puede determinar automáticamente desde ?from=cl\n')
            new_lines.append('        # Si no se proporciona, la vista usará el valor por defecto\n')
            new_lines.append('        return pais\n')
            i += 1
            # Saltar las líneas antiguas del método
            while i < len(lines) and ('if not pais:' in lines[i] or 'raise ValidationError' in lines[i] or 'return pais' in lines[i]):
                i += 1
        continue
    
    # Actualizar clean_telefono para permitir vacío
    if 'def clean_telefono(self):' in line:
        new_lines.append(line)
        i += 1
        if i < len(lines) and 'telefono = self.cleaned_data.get("telefono", "").strip()' in lines[i]:
            new_lines.append('        telefono = self.cleaned_data.get("telefono", "").strip()\n')
            new_lines.append('        # Si no hay teléfono, está bien (es opcional)\n')
            new_lines.append('        if not telefono:\n')
            new_lines.append('            return telefono\n')
            new_lines.append('        \n')
            i += 1
            # Continuar con el resto del método
            while i < len(lines) and ('pais = self.cleaned_data.get("pais")' not in lines[i]):
                i += 1
            if i < len(lines):
                new_lines.append(lines[i])
                i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Formulario actualizado")
PYEOF

# 3. Actualizar vista para usar valores por defecto
python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la extracción de datos
old = '''            nombre_taller = form.cleaned_data["nombre_taller"]
            telefono = form.cleaned_data["telefono"]
            pais = form.cleaned_data["pais"]'''

new = '''            # Campos opcionales - usar valores por defecto si no se proporcionan
            nombre_taller = form.cleaned_data.get("nombre_taller") or f"Taller de {nombre}"
            telefono = form.cleaned_data.get("telefono") or ""
            # El país se determina desde ?from=cl o desde el formulario
            pais = form.cleaned_data.get("pais") or initial_country'''

if old in content:
    content = content.replace(old, new)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Vista actualizada")
else:
    print("⚠️  Vista ya actualizada o estructura diferente")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



