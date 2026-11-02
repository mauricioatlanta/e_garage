#!/usr/bin/env python
"""
Script para probar el flujo de eliminación de cliente en /us/es/clientes/eliminar/<id>/
Ejecutar en el servidor con:
  cd /srv/egarage && export DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod && python manage.py shell < scripts/test_delete_cliente_flow.py

O desde Django shell:
  exec(open('scripts/test_delete_cliente_flow.py').read())
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from taller.models.clientes import Cliente
from taller.utils.empresa import get_user_empresa_safe

settings.ALLOWED_HOSTS = list(set(list(settings.ALLOWED_HOSTS) + ["testserver", "www.egarage.cl"]))
U = get_user_model()
u = (
    U.objects.filter(is_superuser=True).first()
    or U.objects.filter(is_staff=True).first()
    or U.objects.first()
)
e = get_user_empresa_safe(u)
c = Cliente.objects.create(nombre="ZZZ_DELETE_FLOW", empresa=e)
print("CREATED", c.id, c.nombre, c.empresa_id)

client = Client()
client.force_login(u)
r1 = client.get(
    f"/us/es/clientes/eliminar/{c.id}/",
    SERVER_NAME="www.egarage.cl",
    SERVER_PORT=443,
    HTTP_HOST="www.egarage.cl",
)
print("GET_STATUS", r1.status_code)

r2 = client.post(
    f"/us/es/clientes/eliminar/{c.id}/",
    SERVER_NAME="www.egarage.cl",
    SERVER_PORT=443,
    HTTP_HOST="www.egarage.cl",
    follow=False,
)
print("POST_STATUS", r2.status_code)
print("POST_LOCATION", r2.headers.get("Location"))
print("EXISTS_AFTER", Cliente.objects.filter(pk=c.id).exists())
