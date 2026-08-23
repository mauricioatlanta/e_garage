"""
create_atlanta_reciclajes — management command.

Fase 1 de la implementación de Atlanta Reciclajes: crea el tenant de prueba
(Empresa + ConfiguracionEmpresa con rubro RECYCLING) sin tocar DNS, storefront
público ni ningún otro tenant. Idempotente: correrlo de nuevo actualiza el
mismo tenant en vez de duplicarlo.

Usage:
    python manage.py create_atlanta_reciclajes
    python manage.py create_atlanta_reciclajes --username atlanta_test --email dev@example.com
    python manage.py create_atlanta_reciclajes --reset   # elimina el tenant y su data
"""
from __future__ import annotations

import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.utils.plan_catalog import PLAN_TRIAL


class Command(BaseCommand):
    help = "Crea/actualiza el tenant de prueba Atlanta Reciclajes (rubro RECYCLING)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", default="atlanta_reciclajes",
            help="Username del usuario dueño del tenant (default: atlanta_reciclajes).",
        )
        parser.add_argument(
            "--email", default="atlanta.reciclajes@egarage.cl",
            help="Email de contacto del tenant (placeholder hasta configurar el dominio real).",
        )
        parser.add_argument(
            "--nombre", default="Atlanta Reciclajes",
            help="Nombre visible del taller/negocio.",
        )
        parser.add_argument(
            "--password", default=None,
            help="Password inicial. Si se omite, se genera uno aleatorio y se imprime una sola vez.",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Elimina el usuario/tenant existente (cascade) antes de recrearlo.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]

        if options["reset"]:
            deleted, _ = User.objects.filter(username=username).delete()
            self.stdout.write(self.style.WARNING(f"Reset: {deleted} registro(s) eliminados para '{username}'."))

        with transaction.atomic():
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={"email": options["email"], "is_active": True},
            )
            generated_password = None
            if user_created:
                generated_password = options["password"] or secrets.token_urlsafe(12)
                user.set_password(generated_password)
                user.save(update_fields=["password"])

            empresa, empresa_created = Empresa.objects.get_or_create(
                user=user,
                defaults={
                    "nombre_taller": options["nombre"],
                    "empresa": options["nombre"],
                    "pais": "CL",
                    "email": options["email"],
                    "plan": PLAN_TRIAL,
                },
            )
            if not empresa_created:
                empresa.nombre_taller = options["nombre"]
                empresa.save(update_fields=["nombre_taller"])

            config, _config_created = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            config.rubro_principal = "RECYCLING"
            config.nombre_publico = options["nombre"]
            config.modules_configured_at = config.modules_configured_at or timezone.now()
            config.save(update_fields=["rubro_principal", "nombre_publico", "modules_configured_at"])

        self.stdout.write(self.style.SUCCESS(
            f"Tenant listo: empresa_id={empresa.id} username={username} "
            f"(usuario_nuevo={user_created}, empresa_nueva={empresa_created}) rubro=RECYCLING"
        ))
        if generated_password:
            self.stdout.write(self.style.WARNING(
                f"Password generado (guárdalo, no se vuelve a mostrar): {generated_password}"
            ))
