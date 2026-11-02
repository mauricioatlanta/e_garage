from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models import (
    Cliente,
    Documento,
    Empresa,
    PiezaDesarme,
    PiezaDesarmeCompanyLabel,
    Vehiculo,
    VehiculoDesarme,
)


class Command(BaseCommand):
    help = (
        "Bootstrap demo para Venezuela (empresa, usuario, cliente, vehiculos, documento y desarme)"
    )

    def _model_fields(self, model):
        return {f.name for f in model._meta.get_fields()}

    def _filtered_payload(self, model, payload):
        allowed = self._model_fields(model)
        return {k: v for k, v in payload.items() if k in allowed}

    @transaction.atomic
    def handle(self, *args, **kwargs):
        User = get_user_model()
        self.stdout.write(self.style.NOTICE("=== BOOTSTRAP VE DEMO ==="))

        # 1) Usuario demo (primero, porque Empresa usa OneToOne con user).
        user_defaults = {
            "email": "demo_ve@egarage.cl",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
        user, user_created = User.objects.get_or_create(username="demo_ve", defaults=user_defaults)
        if user_created:
            user.set_password("demo1234")
            user.save(update_fields=["password"])
        self.stdout.write(f"Usuario: {user.username} (nuevo={user_created})")

        # 2) Empresa demo VE (ajustada a los campos reales de Empresa).
        empresa_defaults = self._filtered_payload(
            Empresa,
            {
                "nombre_taller": "AutoDesarme Caracas Demo",
                "empresa": "AutoDesarme Caracas Demo",
                "pais": "VE",
                "telefono": "+58 412-555-1234",
                "email": "demo_ve@egarage.cl",
                "moneda": "USD",  # VE opera normalmente en USD en este flujo.
                "zona_horaria": "America/Caracas",
                "suscripcion_activa": True,
                "plan": "trial",
            },
        )
        empresa, empresa_created = Empresa.objects.get_or_create(
            user=user, defaults=empresa_defaults
        )
        if not empresa_created:
            empresa_patch = self._filtered_payload(
                Empresa,
                {
                    "nombre_taller": "AutoDesarme Caracas Demo",
                    "empresa": "AutoDesarme Caracas Demo",
                    "pais": "VE",
                    "telefono": "+58 412-555-1234",
                    "email": "demo_ve@egarage.cl",
                    "zona_horaria": "America/Caracas",
                },
            )
            changed = []
            for key, value in empresa_patch.items():
                if getattr(empresa, key, None) != value:
                    setattr(empresa, key, value)
                    changed.append(key)
            if changed:
                empresa.save(update_fields=changed)
        self.stdout.write(f"Empresa: {empresa} (nueva={empresa_created})")

        # 3) Cliente demo.
        cliente_defaults = self._filtered_payload(
            Cliente,
            {
                "nombre": "Juan",
                "apellido": "Perez",
                "telefono": "+58 412-111-2233",
                "email": "juan.perez.demo.ve@egarage.cl",
                "tax_id_type": "VE_RIF",
                "tax_id": "J123456789",
                "giro": "Comercio automotriz",
                "empresa": empresa,
            },
        )
        cliente_lookup = self._filtered_payload(
            Cliente,
            {"empresa": empresa, "telefono": "+58 412-111-2233"},
        )
        cliente, cliente_created = Cliente.objects.get_or_create(
            **cliente_lookup, defaults=cliente_defaults
        )
        self.stdout.write(f"Cliente: {cliente} (nuevo={cliente_created})")

        # Marca/modelo para que queden persistidos en FK y en texto (demo comercial).
        marca_obj, _ = Marca.objects.get_or_create(nombre="Toyota", country="VE")
        modelo_obj, _ = Modelo.objects.get_or_create(
            nombre="Corolla",
            marca=marca_obj,
            defaults={"country": "VE"},
        )

        # 4) Vehiculo de cliente.
        vehiculo_defaults = self._filtered_payload(
            Vehiculo,
            {
                "cliente": cliente,
                "empresa": empresa,
                "marca": marca_obj,
                "marca_texto": "Toyota",
                "modelo": modelo_obj,
                "modelo_texto": "Corolla",
                "anio": 2012,
                "patente": "AB123CD",
                "tipo_uso": getattr(Vehiculo, "TIPO_USO_CLIENTE", "CLIENTE"),
            },
        )
        vehiculo_lookup = self._filtered_payload(
            Vehiculo,
            {"empresa": empresa, "patente": "AB123CD"},
        )
        vehiculo, vehiculo_created = Vehiculo.objects.get_or_create(
            **vehiculo_lookup, defaults=vehiculo_defaults
        )
        self.stdout.write(f"Vehiculo cliente: {vehiculo} (nuevo={vehiculo_created})")

        # 5) Documento base OT.
        documento_defaults = self._filtered_payload(
            Documento,
            {
                "empresa": empresa,
                "cliente": cliente,
                "vehiculo": vehiculo,
                "tipo": "OT",
                "country": "VE",
                "moneda": "USD",
                "observaciones": "Cambio de motor + revision general (demo VE)",
            },
        )
        documento_lookup = self._filtered_payload(
            Documento,
            {"empresa": empresa, "cliente": cliente, "vehiculo": vehiculo, "tipo": "OT"},
        )
        documento, documento_created = Documento.objects.get_or_create(
            **documento_lookup, defaults=documento_defaults
        )
        self.stdout.write(f"Documento OT: {documento.pk} (nuevo={documento_created})")

        marca_desarme_obj, _ = Marca.objects.get_or_create(nombre="Chevrolet", country="VE")
        modelo_desarme_obj, _ = Modelo.objects.get_or_create(
            nombre="Aveo",
            marca=marca_desarme_obj,
            defaults={"country": "VE"},
        )

        # 6) Vehiculo de desarme "operativo" para piezas (modelo actual PiezaDesarme.vehiculo -> Vehiculo).
        vehiculo_desarme_defaults = self._filtered_payload(
            Vehiculo,
            {
                "empresa": empresa,
                "cliente": None,
                "tipo_uso": getattr(Vehiculo, "TIPO_USO_DESARME", "DESARME"),
                "marca": marca_desarme_obj,
                "marca_texto": "Chevrolet",
                "modelo": modelo_desarme_obj,
                "modelo_texto": "Aveo",
                "anio": 2010,
                "patente": "VE-DESARME-001",
                "estado_desarme": "INGRESADO",
                "ubicacion_fisica": "Patio A-01",
            },
        )
        vehiculo_desarme_lookup = self._filtered_payload(
            Vehiculo,
            {"empresa": empresa, "patente": "VE-DESARME-001"},
        )
        vehiculo_desarme, vd_created = Vehiculo.objects.get_or_create(
            **vehiculo_desarme_lookup, defaults=vehiculo_desarme_defaults
        )
        self.stdout.write(f"Vehiculo desarme (Vehiculo): {vehiculo_desarme} (nuevo={vd_created})")

        # 7) Registro en VehiculoDesarme (si el modelo existe/está migrado en este entorno).
        vehiculo_desarme_model_defaults = self._filtered_payload(
            VehiculoDesarme,
            {
                "empresa": empresa,
                "marca_texto": "Chevrolet",
                "modelo_texto": "Aveo",
                "anio": 2010,
                "patente": "VE-DES-ALT-001",
                "estado_desarme": "INGRESADO",
                "ubicacion_fisica": "Patio A-01",
            },
        )
        if "vin" in self._model_fields(VehiculoDesarme):
            vehiculo_desarme_model_defaults.setdefault("vin", "8AGTT45E0AR000001")
        vdm_lookup = self._filtered_payload(
            VehiculoDesarme,
            {"empresa": empresa, "patente": "VE-DES-ALT-001"},
        )
        vdm, vdm_created = VehiculoDesarme.objects.get_or_create(
            **vdm_lookup, defaults=vehiculo_desarme_model_defaults
        )
        self.stdout.write(f"VehiculoDesarme: {vdm} (nuevo={vdm_created})")

        # 8) Piezas + labels venezolanos.
        piezas_data = [
            ("motor-completo", "Motor completo", 1, "800.00", ["motor"]),
            ("alternador", "Alternador", 1, "120.00", ["planta"]),
            ("arranque", "Arranque", 1, "90.00", ["burro"]),
            ("puerta-del-izq", "Puerta delantera izq", 1, "150.00", []),
        ]

        for codigo, nombre, cantidad, precio, aliases in piezas_data:
            pieza_defaults = self._filtered_payload(
                PiezaDesarme,
                {
                    "empresa": empresa,
                    "vehiculo_desarme": vdm,
                    "codigo": codigo,
                    "nombre": nombre,
                    "cantidad": cantidad,
                    "precio_venta_sugerido": precio,
                    "precio_referencia": precio,
                    "precio_sugerido": precio,
                    "origen_precio": "MANUAL",
                    "estado_pieza": "DISPONIBLE",
                    "activo": True,
                },
            )
            pieza_lookup = self._filtered_payload(
                PiezaDesarme,
                {"empresa": empresa, "vehiculo_desarme": vdm, "codigo": codigo},
            )
            pieza, pieza_created = PiezaDesarme.objects.get_or_create(
                **pieza_lookup, defaults=pieza_defaults
            )

            label_defaults = self._filtered_payload(
                PiezaDesarmeCompanyLabel,
                {
                    "empresa": empresa,
                    "pieza_desarme": pieza,
                    "language": "es",
                    "label": nombre,
                    "aliases": aliases,
                    "is_preferred": True,
                },
            )
            label_lookup = self._filtered_payload(
                PiezaDesarmeCompanyLabel,
                {"empresa": empresa, "pieza_desarme": pieza, "language": "es"},
            )
            label, label_created = PiezaDesarmeCompanyLabel.objects.get_or_create(
                **label_lookup, defaults=label_defaults
            )
            if not label_created and "aliases" in self._model_fields(PiezaDesarmeCompanyLabel):
                label.aliases = aliases
                label.save(update_fields=["aliases"])

            self.stdout.write(
                f"Pieza: {pieza.nombre} (nuevo={pieza_created}) | Label: {label.label} (nuevo={label_created})"
            )

        self.stdout.write(self.style.SUCCESS("Bootstrap VE demo listo."))
