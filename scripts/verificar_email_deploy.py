#!/usr/bin/env python
"""Verifica la configuracion de correo en produccion (post-deploy).

Confirma que el remitente y el Reply-To quedan en un buzon real y enrutado
(support@egarage.cl), evitando los rebotes 550 "Address does not exist".

Uso (en el servidor, con el .env cargado):

    set -a; source /srv/egarage/.env; set +a
    source /srv/egarage/venv/bin/activate   # o .venv

    # Solo mostrar la config resuelta (NO envia nada):
    python scripts/verificar_email_deploy.py

    # Ademas enviar un correo de prueba real a una casilla:
    python scripts/verificar_email_deploy.py tu_correo@gmail.com
"""

import os
import sys

# Permitir ejecutar el script directamente (python scripts/verificar_email_deploy.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

from taller.utils.email_helper import (  # noqa: E402
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)


def _show(label, value):
    print(f"  {label:<22} {value}")


def main():
    print("=" * 60)
    print("VERIFICACION DE CORREO — eGarage")
    print("=" * 60)

    print("\n[1] Settings resueltos")
    _show("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE"))
    _show("EMAIL_BACKEND", getattr(settings, "EMAIL_BACKEND", None))
    _show("DEFAULT_FROM_EMAIL", getattr(settings, "DEFAULT_FROM_EMAIL", None))
    _show("SERVER_EMAIL", getattr(settings, "SERVER_EMAIL", None))
    _show("SUPPORT_EMAIL", getattr(settings, "SUPPORT_EMAIL", None))
    _show("RESEND_API_KEY", "configurada" if getattr(settings, "RESEND_API_KEY", "") else "FALTA")

    print("\n[2] Headers que se enviaran (helper)")
    resolved_from = get_branded_from_email(settings.DEFAULT_FROM_EMAIL)
    reply_to = get_support_reply_to()
    _show("From", resolved_from)
    _show("Reply-To", reply_to)

    # Validaciones rapidas: nada de no-reply ni dominio legacy
    blob = f"{resolved_from} {reply_to} {settings.DEFAULT_FROM_EMAIL} {settings.SUPPORT_EMAIL}".lower()
    problemas = []
    if "no-reply" in blob or "noreply" in blob:
        problemas.append("Aparece un 'no-reply' en From/Reply-To.")
    if "atlantareciclajes.cl" in blob:
        problemas.append("Aparece el dominio legacy 'atlantareciclajes.cl'.")
    if "@egarage.cl" not in reply_to.lower():
        problemas.append("El Reply-To no es @egarage.cl.")

    print("\n[3] Diagnostico")
    if problemas:
        for p in problemas:
            print(f"  ❌ {p}")
        print("\n  -> Revisa /srv/egarage/.env y vuelve a desplegar.")
        sys.exit(1)
    print("  ✅ From y Reply-To apuntan a un buzon real de egarage.cl.")

    destinatario = sys.argv[1] if len(sys.argv) > 1 else None
    if not destinatario:
        print("\n(Para enviar un correo de prueba real, pasa un destinatario:")
        print(" python scripts/verificar_email_deploy.py tu_correo@gmail.com )")
        return

    print(f"\n[4] Enviando correo de prueba a {destinatario} ...")
    enviados = send_email_with_reply_to(
        subject="eGarage — prueba de Reply-To (post-deploy)",
        message=(
            "Este es un correo de prueba de eGarage.\n\n"
            "Responde a este mensaje: la respuesta debe llegar a "
            f"{reply_to} sin rebotar.\n"
        ),
        recipient_list=[destinatario],
        fail_silently=False,
    )
    if enviados:
        print(f"  ✅ Enviado. Abre el correo en {destinatario}, pulsa 'Responder'")
        print(f"     y confirma que el destino es {reply_to} (no rebota).")
    else:
        print("  ❌ No se envio. Revisa RESEND_API_KEY y los logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
