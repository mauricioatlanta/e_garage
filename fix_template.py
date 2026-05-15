#!/usr/bin/env python3
# Script para arreglar el template

import re

# Leer el archivo
with open("templates/taller/common/documentos/document_form.html", "r", encoding="utf-8") as f:
    content = f.read()

# Patrón para encontrar la sección
pattern = r'<script src="{% static \'js/fix_vehiculos_select2\.js\' %}"></script>\s*{# === FIX DE EMERGENCIA[^}]+=== #}\s*<script src="{% static \'js/emergency_fix_vehiculos\.js\' %}"></script>\s*{# === NUEVO: M[^}]+=== #}\s*{# <script src="{% static \'js/document-form/index\.js\' %}"></script> #}'

# Reemplazo
replacement = """<script src="{% static 'js/fix_vehiculos_select2.js' %}"></script>

{# === FIX DE EMERGENCIA - Se ejecuta inmediatamente === #}
<script src="{% static 'js/emergency_fix_vehiculos.js' %}"></script>

{# === FIX PARA APIS - Soluciona errores de JSON === #}
<script src="{% static 'js/api_fix.js' %}"></script>

{# === NUEVO: Módulos JavaScript modularizados (pendiente collectstatic en prod) === #}
{# <script src="{% static 'js/document-form/index.js' %}"></script> #}"""

# Hacer el reemplazo
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Guardar el archivo
with open("templates/taller/common/documentos/document_form.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Template actualizado exitosamente")
