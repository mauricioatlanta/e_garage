#!/usr/bin/env python
"""
Script para crear ConfiguracionEmpresa para la empresa US en el servidor.
Uso en servidor:
  cd /srv/egarage && python manage.py shell < scripts/crear_config_empresa_us.py
O desde shell:
  python manage.py shell -c "$(cat scripts/crear_config_empresa_us.py)"
"""
from decimal import Decimal
from django.apps import apps

Empresa = apps.get_model("taller", "Empresa")
Conf = apps.get_model("taller", "ConfiguracionEmpresa")

emp = Empresa.objects.get(pais__iexact="US")
# Solo campos que existen sin migración 0077 (sales_tax_rate). Si el servidor
# tiene 0077 aplicada, puedes añadir 'sales_tax_rate': Decimal('0.00') a defaults.
conf, created = Conf.objects.get_or_create(
    empresa=emp,
    defaults={
        "moneda": "USD",
        "tasa_impuesto": Decimal("0.00"),
        "aplicar_impuesto_por_defecto": False,
    },
)
print("created?", created, "conf=", conf)
