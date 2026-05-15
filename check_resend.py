#!/usr/bin/env python
import os
import sys
from pathlib import Path

import django
from dotenv import load_dotenv
from django.conf import settings
from django.core.mail import send_mail

BASE_DIR = Path(__file__).resolve().parent
RECIPIENT_EMAIL = "tu-correo-personal@gmail.com"

load_dotenv(BASE_DIR / ".env.prod", override=False)
load_dotenv(BASE_DIR / ".env", override=True)

# Configurar el entorno real que usa manage.py en local
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


def test_resend_flow():
    subject = "eGarage: Test de Conectividad Resend"
    message = (
        "Si estás leyendo esto, el cambio de API Key fue exitoso y el flujo de correo "
        "está activo."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient = sys.argv[1].strip() if len(sys.argv) > 1 else RECIPIENT_EMAIL
    recipient_list = [recipient]

    print(f"Intentando enviar desde: {from_email}...")

    try:
        send_count = send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        if send_count:
            print("[OK] El correo ha sido enviado y aceptado por Resend.")
        else:
            print("[WARN] El correo no se envio, pero no hubo error explicito.")
    except ModuleNotFoundError as exc:
        if exc.name == "anymail":
            print("[ERROR] Error al enviar el correo: django-anymail no esta instalado.")
            print("\nInstala dependencias con: pip install -r requirements.txt")
            return
        raise
    except Exception as e:
        print(f"[ERROR] Error al enviar el correo: {e}")
        print("\nRevisa si el dominio egarage.cl sigue verificado en el panel de Resend.")


if __name__ == "__main__":
    test_resend_flow()
