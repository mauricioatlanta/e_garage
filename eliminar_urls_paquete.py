import os
import shutil

# Ruta absoluta al directorio del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TALLER_URLS_DIR = os.path.join(BASE_DIR, 'taller', 'urls')

if os.path.isdir(TALLER_URLS_DIR):
    print(f"Eliminando carpeta: {TALLER_URLS_DIR}")
    shutil.rmtree(TALLER_URLS_DIR)
    print("Carpeta eliminada correctamente.")
else:
    print(f"No existe la carpeta: {TALLER_URLS_DIR}")

# Eliminar archivos .pyc y __pycache__ residuales
for root, dirs, files in os.walk(BASE_DIR):
    for d in dirs:
        if d == '__pycache__':
            dirpath = os.path.join(root, d)
            print(f"Eliminando caché: {dirpath}")
            shutil.rmtree(dirpath)
    for f in files:
        if f.endswith('.pyc'):
            filepath = os.path.join(root, f)
            print(f"Eliminando archivo: {filepath}")
            os.remove(filepath)

print("Limpieza finalizada. Reinicia el servidor de desarrollo.")
