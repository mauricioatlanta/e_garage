#!/bin/bash
# Script para eliminar la sección "Business Information" del formulario de registro
# y hacer que esos campos sean opcionales

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Eliminando sección Business Information del template signup.html..."

# Eliminar la sección Business Information del template
python3 << 'PYEOF'
import re

file_path = "templates/auth/signup.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y eliminar la sección completa "Business Information"
# Desde "<!-- SECCIÓN 2: Datos de la Empresa -->" hasta "<!-- SECCIÓN 3: Selección de Plan -->"
pattern = r'<!-- SECCIÓN 2: Datos de la Empresa -->.*?<!-- SECCIÓN 3: Selección de Plan -->'
replacement = '<!-- SECCIÓN 2: Selección de Plan -->'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Template actualizado")
else:
    print("⚠️  No se encontró la sección a eliminar (puede que ya esté eliminada)")

PYEOF

echo ""
echo "🔧 Haciendo campos opcionales en el formulario..."

# Hacer campos opcionales en el formulario
python3 << 'PYEOF'
import re

file_path = "taller/forms/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar específicamente los campos
content = re.sub(
    r'nombre_taller = forms\.CharField\([^)]+required=True[^)]+\)',
    lambda m: m.group(0).replace('required=True', 'required=False').replace('"required": "required",', ''),
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'telefono = forms\.CharField\([^)]+required=True[^)]+\)',
    lambda m: m.group(0).replace('required=True', 'required=False').replace('"required": "required",', ''),
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'pais = forms\.ChoiceField\([^)]+required=True[^)]+\)',
    lambda m: m.group(0).replace('required=True', 'required=False').replace('"required": "required",', ''),
    content,
    flags=re.DOTALL
)

# Actualizar clean_pais para que no requiera país
old_clean_pais = '''    def clean_pais(self):
        pais = self.cleaned_data.get("pais")
        if not pais:
            raise ValidationError("Debes seleccionar un país")
        return pais'''

new_clean_pais = '''    def clean_pais(self):
        pais = self.cleaned_data.get("pais")
        # El país es opcional - se puede determinar automáticamente desde ?from=cl
        # Si no se proporciona, la vista usará el valor por defecto
        return pais'''

if old_clean_pais in content:
    content = content.replace(old_clean_pais, new_clean_pais)
    print("✅ Método clean_pais actualizado")

# Actualizar clean_telefono para permitir teléfono vacío
old_clean_telefono_start = '    def clean_telefono(self):\n        telefono = self.cleaned_data.get("telefono", "").strip()\n        pais = self.cleaned_data.get("pais")\n\n        if not pais:\n            return telefono'
new_clean_telefono_start = '    def clean_telefono(self):\n        telefono = self.cleaned_data.get("telefono", "").strip()\n        # Si no hay teléfono, está bien (es opcional)\n        if not telefono:\n            return telefono\n        \n        pais = self.cleaned_data.get("pais")\n\n        if not pais:\n            return telefono'

if old_clean_telefono_start in content:
    content = content.replace(old_clean_telefono_start, new_clean_telefono_start)
    print("✅ Método clean_telefono actualizado")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Formulario actualizado")
PYEOF

echo ""
echo "🔧 Actualizando vista para usar valores por defecto..."

# Actualizar la vista
python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la extracción de datos
old_extraction = '''            # Extraer datos del formulario
            nombre = form.cleaned_data["nombre"]
            apellido = form.cleaned_data["apellido"]
            email = form.cleaned_data["email"]
            nombre_taller = form.cleaned_data["nombre_taller"]
            telefono = form.cleaned_data["telefono"]
            pais = form.cleaned_data["pais"]
            plan = form.cleaned_data["plan"]
            password = form.cleaned_data["password1"]'''

new_extraction = '''            # Extraer datos del formulario
            nombre = form.cleaned_data["nombre"]
            apellido = form.cleaned_data["apellido"]
            email = form.cleaned_data["email"]
            # Campos opcionales - usar valores por defecto si no se proporcionan
            nombre_taller = form.cleaned_data.get("nombre_taller") or f"Taller de {nombre}"
            telefono = form.cleaned_data.get("telefono") or ""
            # El país se determina desde ?from=cl o desde el formulario
            pais = form.cleaned_data.get("pais") or initial_country
            plan = form.cleaned_data["plan"]
            password = form.cleaned_data["password1"]'''

if old_extraction in content:
    content = content.replace(old_extraction, new_extraction)
    print("✅ Vista actualizada")
else:
    print("⚠️  No se encontró el bloque a reemplazar (puede que ya esté actualizado)")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

PYEOF

echo ""
echo "✅✅✅ Cambios aplicados correctamente ✅✅✅"
echo ""
echo "📋 Resumen de cambios:"
echo "  - Se eliminó la sección 'Business Information' del template"
echo "  - Los campos nombre_taller, telefono y pais son ahora opcionales"
echo "  - El país se determina automáticamente desde ?from=cl"
echo "  - Se usan valores por defecto si no se proporcionan"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"

