from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from random import randint, choice

from faker import Faker

from taller.models import (
    Cliente,
    Vehiculo,
    Documento,
    LineaServicio,
    Empresa,
)

fake = Faker('es_CL')
User = get_user_model()


class Command(BaseCommand):
    help = 'Seed comercial realista'

    def handle(self, *args, **kwargs):

        self.stdout.write("🚀 Generando datos...")

        usuario = User.objects.filter(is_superuser=True).first()

        if not usuario:
            self.stdout.write(self.style.ERROR("❌ No hay superusuario"))
            return

        empresa = Empresa.objects.first()

        if not empresa:
            self.stdout.write(self.style.ERROR("❌ No existe empresa"))
            return

        servicios = [
            ("Cambio de aceite", 28990),
            ("Alineación", 19990),
            ("Balanceo", 15990),
            ("Diagnóstico scanner", 24990),
            ("Cambio de batería", 89990),
            ("Mantención", 129990),
        ]

        total_docs = 0

        for _ in range(30):

            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre=fake.name(),
                telefono=f"+569{randint(10000000,99999999)}",
                email=fake.email(),
            )

            vehiculo = Vehiculo.objects.create(
                empresa=empresa,
                cliente=cliente,
                patente=fake.license_plate(),
                anio=randint(2008, 2025),
            )

            documento = Documento.objects.create(
                empresa=empresa,
                cliente=cliente,
                vehiculo=vehiculo,
                fecha_emision=timezone.now(),
                tipo='orden_trabajo',
                estado='abierto',
                moneda='CLP',
                total=0,
            )

            total = Decimal('0')

            for _ in range(randint(1, 4)):

                nombre, precio = choice(servicios)

                cantidad = randint(1, 2)

                subtotal = Decimal(precio) * Decimal(cantidad)

                LineaServicio.objects.create(
                    documento=documento,
                    nombre=nombre,
                    cantidad=cantidad,
                    precio_unitario=Decimal(precio),
                )

                total += subtotal

            documento.total = total
            documento.neto_servicios = total
            documento.save()

            total_docs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Seed completado: {total_docs} documentos"
            )
        )
