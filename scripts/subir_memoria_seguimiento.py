#!/usr/bin/env python3
"""
Script para subir el archivo memoria_seguimiento.py al servidor
Uso: python scripts/subir_memoria_seguimiento.py
"""

import os
import subprocess
import sys

# Ruta del archivo local
LOCAL_FILE = "taller/models/memoria_seguimiento.py"
REMOTE_PATH = "/srv/egarage/taller/models/memoria_seguimiento.py"
SERVER = "root@egarage-server"  # Ajustar según tu configuración


def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"❌ Error: No se encontró {LOCAL_FILE}")
        sys.exit(1)

    print(f"📤 Subiendo {LOCAL_FILE} al servidor...")
    print(f"   Destino: {SERVER}:{REMOTE_PATH}")
    print()

    # Usar scp para subir el archivo
    try:
        cmd = ["scp", LOCAL_FILE, f"{SERVER}:{REMOTE_PATH}"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Archivo subido correctamente")
        print()
        print("Ahora ejecuta en el servidor:")
        print(f"  sudo chown egarage:www-data {REMOTE_PATH}")
        print(f"  sudo chmod 644 {REMOTE_PATH}")
        print("  sudo systemctl restart egarage-gunicorn.service")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al subir archivo: {e}")
        print(f"   Salida: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: scp no está disponible")
        print("   Alternativa: Copia el archivo manualmente o usa otro método")
        sys.exit(1)


if __name__ == "__main__":
    main()
