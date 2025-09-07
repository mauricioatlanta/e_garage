# Configuración temporal para usar SQLite
import os
from pathlib import Path

# Importar la configuración base
from e_garage.settings import *

# ============================================================
# 🗄️ BASE DE DATOS (SQLite para pruebas)
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

print("🔧 Usando configuración SQLite temporal para pruebas")
