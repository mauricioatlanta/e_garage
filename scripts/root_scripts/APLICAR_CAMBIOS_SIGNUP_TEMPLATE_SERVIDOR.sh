#!/bin/bash
# Script para aplicar cambios en el template de signup:
# 1. Agregar campo país
# 2. Traducir términos y condiciones
# 3. Inicializar idioma según ?from=cl

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando cambios en templates/auth/signup.html..."

python3 << 'PYEOF'
import re

file_path = "templates/auth/signup.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Agregar campo país después del email
if '{{ form.pais }}' not in content or '<!-- SECCIÓN 2: Selección de Plan -->' in content and '{{ form.pais }}' not in content.split('<!-- SECCIÓN 2: Selección de Plan -->')[0]:
    # Buscar donde termina el campo email y agregar el campo país
    email_pattern = r'({{ form\.email }}\s+{% if form\.email\.errors %}\s+<div class="error-message">{{ form\.email\.errors }}</div>\s+{% endif %}\s+</div>\s+)'
    
    country_field = '''                <div class="form-group">
                    <label class="form-label">{% trans "Country" %}</label>
                    {{ form.pais }}
                    {% if form.pais.errors %}
                    <div class="error-message">{{ form.pais.errors }}</div>
                    {% endif %}
                </div>
'''
    
    if re.search(email_pattern, content):
        content = re.sub(
            email_pattern,
            r'\1' + country_field,
            content
        )
        changes_made.append("✅ Campo país agregado")
    else:
        # Buscar patrón más simple
        if '</div>\n            </div>\n\n            <!-- SECCIÓN 2: Selección de Plan -->' in content:
            content = content.replace(
                '</div>\n            </div>\n\n            <!-- SECCIÓN 2: Selección de Plan -->',
                '</div>\n\n                <div class="form-group">\n                    <label class="form-label">{% trans "Country" %}</label>\n                    {{ form.pais }}\n                    {% if form.pais.errors %}\n                    <div class="error-message">{{ form.pais.errors }}</div>\n                    {% endif %}\n                </div>\n            </div>\n\n            <!-- SECCIÓN 2: Selección de Plan -->'
            )
            changes_made.append("✅ Campo país agregado")
else:
    changes_made.append("ℹ️  Campo país ya existe")

# 2. Reemplazar términos y condiciones con elementos lang-es/lang-en
old_terms = '{% trans "I accept the" %} <a href="/legal/">{% trans "terms and conditions" %}</a>'
new_terms = '''<span class="lang-es">Acepto los</span>
                    <span class="lang-en" style="display: none;">I accept the</span>
                    <a href="/legal/">
                        <span class="lang-es">términos y condiciones</span>
                        <span class="lang-en" style="display: none;">terms and conditions</span>
                    </a>'''

if old_terms in content:
    content = content.replace(old_terms, new_terms)
    changes_made.append("✅ Términos y condiciones traducidos")
else:
    changes_made.append("ℹ️  Términos y condiciones ya están traducidos")

# 3. Actualizar función changeLanguage para manejar lang-es/lang-en
if '// Actualizar elementos lang-es/lang-en' not in content:
    # Buscar el final de la función changeLanguage
    change_lang_end = '    const loginLink = document.querySelector(\'.login-link a\');\n    if (loginLink) {\n        loginLink.textContent = lang[\'Sign in\'];\n    }\n}'
    
    if change_lang_end in content:
        lang_update = '''    const loginLink = document.querySelector('.login-link a');
    if (loginLink) {
        loginLink.textContent = lang['Sign in'];
    }
    
    // Actualizar elementos lang-es/lang-en
    const currentLang = country === 'CL' || country === 'MX' || country === 'CO' || country === 'PE' || country === 'VE' || country === 'EC' ? 'es' : 'en';
    document.querySelectorAll('.lang-es, .lang-en').forEach(function(el) {
        if (el.classList.contains('lang-' + currentLang)) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
}'''
        
        content = content.replace(change_lang_end, lang_update)
        changes_made.append("✅ Función changeLanguage actualizada")
    else:
        changes_made.append("⚠️  No se encontró el final de changeLanguage")
else:
    changes_made.append("ℹ️  Función changeLanguage ya está actualizada")

# 4. Actualizar inicialización para detectar ?from=cl
old_init = '''// Inicializar con país por defecto si ya hay uno seleccionado
window.addEventListener('load', function() {
    const paisSelect = document.getElementById('id_pais');
    if (paisSelect.value) {
        updatePlanPrices(paisSelect.value);
        changeLanguage(paisSelect.value);
    }
});'''

new_init = '''// Inicializar con país por defecto si ya hay uno seleccionado
document.addEventListener('DOMContentLoaded', function() {
    const paisSelect = document.getElementById('id_pais');
    
    // Obtener el país desde la URL (?from=cl) o desde el select
    const urlParams = new URLSearchParams(window.location.search);
    const fromCountry = urlParams.get('from') || '';
    
    // Determinar país inicial
    let initialCountry = '';
    if (fromCountry.toLowerCase() === 'cl') {
        initialCountry = 'CL';
    } else if (fromCountry.toLowerCase() === 'mx') {
        initialCountry = 'MX';
    } else if (fromCountry.toLowerCase() === 'us') {
        initialCountry = 'US';
    } else if (paisSelect && paisSelect.value) {
        initialCountry = paisSelect.value;
    } else {
        initialCountry = 'US'; // Por defecto
    }
    
    // Establecer el país en el select si no está establecido
    if (paisSelect && !paisSelect.value && initialCountry) {
        paisSelect.value = initialCountry;
    }
    
    // Actualizar precios e idioma
    if (initialCountry) {
        updatePlanPrices(initialCountry);
        changeLanguage(initialCountry);
    }
    
    // Asegurar que los elementos lang-es/lang-en se muestren correctamente
    const currentLang = initialCountry === 'CL' || initialCountry === 'MX' || initialCountry === 'CO' || initialCountry === 'PE' || initialCountry === 'VE' || initialCountry === 'EC' ? 'es' : 'en';
    document.querySelectorAll('.lang-es, .lang-en').forEach(function(el) {
        if (el.classList.contains('lang-' + currentLang)) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
});'''

if old_init in content:
    content = content.replace(old_init, new_init)
    changes_made.append("✅ Inicialización actualizada para detectar ?from=cl")
elif 'document.addEventListener(\'DOMContentLoaded\'' in content and 'urlParams.get(\'from\')' in content:
    changes_made.append("ℹ️  Inicialización ya está actualizada")
else:
    # Buscar cualquier inicialización y reemplazarla
    if 'window.addEventListener(\'load\'' in content:
        # Reemplazar cualquier window.addEventListener('load') relacionado con país
        content = re.sub(
            r'// Inicializar con país.*?window\.addEventListener\([\'"]load[\'"].*?\}\);',
            new_init,
            content,
            flags=re.DOTALL
        )
        changes_made.append("✅ Inicialización reemplazada")
    else:
        changes_made.append("⚠️  No se encontró la inicialización a reemplazar")

# Guardar cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n".join(changes_made))
print("✅ Archivo actualizado")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"

