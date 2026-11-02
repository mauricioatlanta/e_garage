#!/usr/bin/env python3
# Agregar script force_native_select al template

import re

# Leer el archivo
with open("templates/taller/common/documentos/document_form.html", "r", encoding="utf-8") as f:
    content = f.read()

# Patrón para encontrar la sección después de api_fix.js
pattern = r'({# === FIX PARA APIS[^}]+=== #}\s*<script src="{% static \'js/api_fix\.js\' %}"></script>\s*)({# === NUEVO: M[^}]+=== #}\s*{# <script src="{% static \'js/document-form/index\.js\' %}"></script> #})'

# Reemplazo
replacement = r'\1{# === FIX AGREGIVO: Forzar select nativo === #}\n<script src="{% static \'js/force_native_select.js\' %}"></script>\n\n\2'

# Hacer el reemplazo
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Guardar el archivo
with open("templates/taller/common/documentos/document_form.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Script force_native_select agregado al template")
