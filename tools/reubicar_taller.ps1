# Crear carpetas
New-Item -ItemType Directory -Force taller\urls | Out-Null
New-Item -ItemType Directory -Force taller\views | Out-Null
New-Item -ItemType Directory -Force taller\forms | Out-Null
New-Item -ItemType Directory -Force _backup\models_legacy | Out-Null
New-Item -ItemType File -Force taller\urls\__init__.py | Out-Null
New-Item -ItemType File -Force taller\views\__init__.py | Out-Null
New-Item -ItemType File -Force taller\forms\__init__.py | Out-Null

# Ejemplos de movimientos
Move-Item taller\taller_main_urls.py taller\urls\main.py -ErrorAction SilentlyContinue
Move-Item taller\business_intelligence_urls.py taller\urls\business_intelligence.py -ErrorAction SilentlyContinue
Move-Item taller\ajax_urls.py taller\urls\ajax.py -ErrorAction SilentlyContinue
Move-Item taller\urls_autocomplete.py taller\urls\urls_autocomplete.py -ErrorAction SilentlyContinue
Move-Item taller\urls_dashboard.py taller\urls\urls_dashboard.py -ErrorAction SilentlyContinue

Move-Item taller\views.py taller\views\views.py -ErrorAction SilentlyContinue
Move-Item taller\taller_views.py taller\views\taller.py -ErrorAction SilentlyContinue
Move-Item taller\dashboard_views.py taller\views\dashboard.py -ErrorAction SilentlyContinue
Move-Item taller\ajax_views.py taller\views\ajax_legacy.py -ErrorAction SilentlyContinue
Move-Item taller\main_views*.py taller\views\ -ErrorAction SilentlyContinue
Move-Item taller\*catalogo*views.py taller\views\ -ErrorAction SilentlyContinue
Move-Item taller\ia_views.py taller\views\ia.py -ErrorAction SilentlyContinue
Move-Item taller\registro_views.py taller\views\registro.py -ErrorAction SilentlyContinue

Move-Item taller\empresa_forms.py taller\forms\empresa.py -ErrorAction SilentlyContinue
Move-Item taller\forms.py taller\forms\forms.py -ErrorAction SilentlyContinue
Move-Item taller\forms_*.py taller\forms\ -ErrorAction SilentlyContinue

Move-Item taller\models*.py _backup\models_legacy\ -ErrorAction SilentlyContinue
Move-Item taller\urls.py.backup _backup\ -ErrorAction SilentlyContinue

# Middlewares: deja solo uno
if (Test-Path taller\middlewares.py) { Move-Item taller\middlewares.py taller\middleware.py -ErrorAction SilentlyContinue }
