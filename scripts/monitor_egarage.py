import requests
import sys
import subprocess
from datetime import datetime
import urllib3

# Configuración
BASE_URL = "https://www.egarage.cl"
ENDPOINTS = [
    {"name": "LOGIN USA", "path": "/us/login/", "device": "Desktop"},
    {"name": "SIGNUP USA", "path": "/us/signup/", "device": "Desktop"},
    {"name": "CHILE HOME", "path": "/cl/es/", "device": "Desktop"},
]
UA_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"


def check_health():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print(f"=== MONITOR EGARAGE - {datetime.now().isoformat()} ===")
    errors = 0

    for ep in ENDPOINTS:
        url = f"{BASE_URL}{ep['path']}"
        try:
            # Probar Desktop
            r = requests.get(url, timeout=10, verify=False)
            status = r.status_code
            print(f"Testing {ep['name']} (Desktop) -> {status} {'✅' if status == 200 else '❌'}")
            if status != 200:
                errors += 1

            # Probar Mobile
            r_m = requests.get(url, headers={"User-Agent": UA_MOBILE}, timeout=10, verify=False)
            status_m = r_m.status_code
            print(
                f"Testing {ep['name']} (Mobile)  -> {status_m} {'✅' if status_m == 200 else '❌'}"
            )
            if status_m != 200:
                errors += 1

        except Exception as e:
            print(f"Error connecting to {url}: {e}")
            errors += 1

    # Revisar Logs de Gunicorn si hay errores
    if errors > 0:
        print("\n--- REVISANDO LOGS DE GUNICORN ---")
        try:
            subprocess.run(["journalctl", "-u", "gunicorn", "-n", "20", "--no-pager"], check=False)
        except Exception as e:
            print(f"Could not read journal logs: {e}")

    return errors


if __name__ == "__main__":
    err_count = check_health()
    if err_count == 0:
        print("\n=== TODO OK 🚀 ===")
        sys.exit(0)
    else:
        print(f"\n=== SE DETECTARON {err_count} FALLOS 🚨 ===")
        sys.exit(1)
