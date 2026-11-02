#!/usr/bin/env bash
# Verificación en servidor: WeasyPrint, qrcode, vistas PDF/panel, templates, URLs y generación PDF.
# Uso: copiar a /srv/egarage y ejecutar: bash verify_documento_panel.sh

set -e
cd /srv/egarage
source /srv/egarage/venv/bin/activate
export DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod

printf '\n===== VERIFY WEASYPRINT =====\n'
python - <<'PY'
import weasyprint
print("WeasyPrint OK:", weasyprint.__version__)
PY

printf '\n===== VERIFY QRCODE =====\n'
python - <<'PY'
import qrcode
print("qrcode OK")
PY

printf '\n===== VERIFY VIEW EXISTS =====\n'
rg -n "descargar_documento_pdf|imprimir_documento|compartir_documento_whatsapp|enviar_documento_email|ver_documento_publico" taller/desarme/views_pdf.py -S 2>/dev/null || grep -n "descargar_documento_pdf\|imprimir_documento\|compartir_documento_whatsapp\|enviar_documento_email\|ver_documento_publico" taller/desarme/views_pdf.py 2>/dev/null || true

printf '\n===== VERIFY TEMPLATE PDF =====\n'
ls -lah templates/taller/documentos/pdf/ 2>/dev/null || echo "Path not found"

printf '\n===== VERIFY TEMPLATE PRINT =====\n'
ls -lah templates/taller/documentos/ 2>/dev/null || echo "Path not found"

printf '\n===== VERIFY CSS PDF =====\n'
ls -lah static/css/documentos/ 2>/dev/null || echo "Path not found"

printf '\n===== VERIFY URL REGISTRATION =====\n'
rg -n "descargar_documento_pdf|imprimir_documento|compartir_documento_whatsapp|enviar_documento_email|ver_documento_publico" taller/documentos/urls.py -S 2>/dev/null || grep -n "descargar_documento_pdf\|imprimir_documento\|compartir_documento_whatsapp\|enviar_documento_email\|ver_documento_publico" taller/documentos/urls.py 2>/dev/null || true

printf '\n===== TEST URL RESOLVE =====\n'
python manage.py shell <<'PY'
from django.urls import reverse
print("PDF:", reverse("documentos:descargar_documento_pdf", args=[1]))
print("PRINT:", reverse("documentos:imprimir_documento", args=[1]))
print("WA:", reverse("documentos:compartir_documento_whatsapp", args=[1]))
print("EMAIL:", reverse("documentos:enviar_documento_email", args=[1]))
PY

printf '\n===== TEST DOCUMENT EXISTS =====\n'
python manage.py shell <<'PY'
from taller.models import Documento
d = Documento.objects.first()
print("DOC:", d.id if d else "NO DOC")
PY

printf '\n===== TEST PDF GENERATION =====\n'
python manage.py shell <<'PY'
from django.test import RequestFactory
from django.contrib.auth.models import User
from taller.models import Documento
from taller.desarme.views_pdf import descargar_documento_pdf

rf = RequestFactory()
user = User.objects.first()
doc = Documento.objects.first()

if not user or not doc:
    print("Missing user or document")
else:
    request = rf.get("/")
    request.user = user
    request.session = {}
    try:
        response = descargar_documento_pdf(request, doc.id)
        print("PDF STATUS:", response.status_code)
        if response.status_code == 200:
            print("PDF SIZE:", len(response.content))
        else:
            print("(302/404 expected if empresa not in request)")
    except Exception as e:
        print("ERROR:", e)
PY

printf '\n===== CHECK EMAIL CONFIG =====\n'
python manage.py shell <<'PY'
from django.conf import settings
print("EMAIL_HOST:", getattr(settings, "EMAIL_HOST", "NOT SET"))
print("EMAIL_PORT:", getattr(settings, "EMAIL_PORT", "NOT SET"))
print("EMAIL_USER:", getattr(settings, "EMAIL_HOST_USER", "NOT SET"))
PY

printf '\n===== RESTART GUNICORN =====\n'
sudo systemctl restart gunicorn
sudo systemctl status gunicorn --no-pager -l
