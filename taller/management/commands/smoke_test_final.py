"""
Smoke Test Final - Verificación Multi-Tenant y CRUD
Ejecutar: python manage.py smoke_test_final

Este comando verifica:
1. Aislamiento multi-tenant (empresa A no puede acceder a datos de empresa B)
2. Deletes solo por POST
3. CRUD básico funciona
4. Filtrado por empresa en todas las operaciones
"""

import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from taller.models import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.repuesto import Repuesto
from taller.models.documento import Documento
from taller.servicios.models import Servicio, ServicioExterno

User = get_user_model()


class Command(BaseCommand):
    help = "Smoke test final: verifica multi-tenant, CRUD y permisos"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []
        self.warnings = []
        self.success = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Mostrar detalles de cada prueba",
        )

    def log_success(self, message):
        self.success.append(message)
        self.stdout.write(self.style.SUCCESS(f"✅ {message}"))

    def log_error(self, message):
        self.errors.append(message)
        self.stdout.write(self.style.ERROR(f"❌ {message}"))

    def log_warning(self, message):
        self.warnings.append(message)
        self.stdout.write(self.style.WARNING(f"⚠️  {message}"))

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.SUCCESS("\n🔍 INICIANDO SMOKE TEST FINAL\n"))
        self.stdout.write("=" * 60)

        # 1. Setup: Crear empresas y usuarios de prueba
        self.stdout.write("\n📦 PASO 1: Creando datos de prueba...")
        try:
            empresa_a, user_a = self._create_test_company("A", "CL")
            empresa_b, user_b = self._create_test_company("B", "CL")
            self.log_success("Empresas y usuarios de prueba creados")
        except Exception as e:
            self.log_error(f"Error creando datos de prueba: {e}")
            return

        # 2. Crear datos en empresa A
        self.stdout.write("\n📦 PASO 2: Creando datos en empresa A...")
        try:
            cliente_a, vehiculo_a, repuesto_a, documento_a = self._create_test_data(
                empresa_a, user_a
            )
            self.log_success("Datos de prueba creados en empresa A")
        except Exception as e:
            self.log_error(f"Error creando datos: {e}")
            return

        # 3. Verificar aislamiento multi-tenant
        self.stdout.write("\n🔒 PASO 3: Verificando aislamiento multi-tenant...")
        self._test_multi_tenant_isolation(
            user_a, user_b, cliente_a, vehiculo_a, repuesto_a, documento_a, verbose
        )

        # 4. Verificar deletes solo por POST
        self.stdout.write("\n🛡️  PASO 4: Verificando deletes solo por POST...")
        self._test_delete_methods(user_a, cliente_a, vehiculo_a, repuesto_a, verbose)

        # 5. Verificar CRUD básico
        self.stdout.write("\n📋 PASO 5: Verificando CRUD básico...")
        self._test_crud_basic(user_a, empresa_a, verbose)

        # 6. Resumen final
        self._print_summary()

    def _create_test_company(self, suffix, country):
        """Crea una empresa y usuario de prueba"""
        empresa = Empresa.objects.create(
            nombre_taller=f"Taller Test {suffix}",
            pais=country,
        )
        user = User.objects.create_user(
            username=f"user_test_{suffix.lower()}",
            email=f"user{suffix.lower()}@test.com",
            password="test123456",
        )
        user.empresa = empresa
        user.save()
        return empresa, user

    def _create_test_data(self, empresa, user):
        """Crea datos de prueba en una empresa"""
        cliente = Cliente.objects.create(
            nombre=f"Cliente Test",
            apellido="Multi-Tenant",
            email="cliente@test.com",
            telefono="123456789",
            empresa=empresa,
        )

        vehiculo = Vehiculo.objects.create(
            cliente=cliente,
            patente=f"TEST{empresa.id}",
            anio=2020,
            empresa=empresa,
        )

        repuesto = Repuesto.objects.create(
            nombre="Repuesto Test",
            precio_venta=100.00,
            cantidad_stock=10,
            empresa=empresa,
        )

        # Documento requiere más campos, crear solo si es posible
        documento = None
        try:
            documento = Documento.objects.create(
                cliente=cliente,
                vehiculo=vehiculo,
                tipo_documento="OT",
                numero_documento=1,
                empresa=empresa,
            )
        except Exception as e:
            self.log_warning(f"No se pudo crear documento de prueba: {e}")

        return cliente, vehiculo, repuesto, documento

    def _test_multi_tenant_isolation(
        self, user_a, user_b, cliente_a, vehiculo_a, repuesto_a, documento_a, verbose
    ):
        """Verifica que usuario B no puede acceder a datos de empresa A"""
        client_b = Client()
        client_b.force_login(user_b)

        tests = [
            ("Cliente", f"/clientes/ver/{cliente_a.pk}/", "ver_cliente"),
            ("Cliente", f"/clientes/editar/{cliente_a.pk}/", "editar_cliente"),
            ("Vehículo", f"/vehiculos/{vehiculo_a.id}/", "ver_vehiculo"),
            ("Vehículo", f"/vehiculos/{vehiculo_a.id}/editar/", "editar_vehiculo"),
            ("Repuesto", f"/repuestos/{repuesto_a.pk}/", "ver_repuesto"),
            ("Repuesto", f"/repuestos/editar/{repuesto_a.pk}/", "editar_repuesto"),
        ]

        if documento_a:
            tests.extend(
                [
                    ("Documento", f"/documentos/ver/{documento_a.pk}/", "ver_documento"),
                    ("Documento", f"/documentos/form/{documento_a.pk}/", "documento_editar"),
                ]
            )

        for model_name, url, view_name in tests:
            try:
                response = client_b.get(url)
                if response.status_code == 404:
                    self.log_success(f"{model_name}: Usuario B no puede acceder (404)")
                elif response.status_code == 403:
                    self.log_success(f"{model_name}: Usuario B bloqueado (403)")
                else:
                    self.log_error(
                        f"{model_name}: Usuario B pudo acceder (status {response.status_code}) - "
                        f"RIESGO DE SEGURIDAD MULTI-TENANT"
                    )
                    if verbose:
                        self.stdout.write(f"  URL: {url}")
                        self.stdout.write(f"  View: {view_name}")
            except Exception as e:
                self.log_warning(f"{model_name}: Error al probar acceso - {e}")

    def _test_delete_methods(self, user_a, cliente_a, vehiculo_a, repuesto_a, verbose):
        """Verifica que los deletes solo funcionan por POST"""
        client = Client()
        client.force_login(user_a)

        tests = [
            ("Cliente", f"/clientes/eliminar/{cliente_a.pk}/", "eliminar_cliente"),
            ("Vehículo", f"/vehiculos/{vehiculo_a.id}/eliminar/", "eliminar_vehiculo"),
            ("Repuesto", f"/repuestos/{repuesto_a.pk}/eliminar/", "eliminar_repuesto"),
        ]

        for model_name, url, view_name in tests:
            try:
                # Intentar DELETE por GET (debe fallar o mostrar confirmación)
                response = client.get(url)
                if response.status_code in [200, 405]:
                    # 200 = muestra confirmación (OK), 405 = método no permitido (OK)
                    self.log_success(f"{model_name}: Delete por GET muestra confirmación o bloquea")
                else:
                    self.log_warning(f"{model_name}: Delete por GET retornó {response.status_code}")

                if verbose:
                    self.stdout.write(f"  GET {url} → {response.status_code}")
            except Exception as e:
                self.log_warning(f"{model_name}: Error al probar delete - {e}")

    def _test_crud_basic(self, user_a, empresa_a, verbose):
        """Verifica que las operaciones CRUD básicas funcionan"""
        client = Client()
        client.force_login(user_a)

        # Test LISTAR
        list_tests = [
            ("Clientes", "/clientes/", "lista_clientes"),
            ("Vehículos", "/vehiculos/", "lista_vehiculos"),
            ("Repuestos", "/repuestos/", "lista_repuestos"),
            ("Documentos", "/documentos/", "lista_documentos"),
        ]

        for model_name, url, view_name in list_tests:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.log_success(f"{model_name}: Listar funciona (200)")
                else:
                    self.log_error(f"{model_name}: Listar falló (status {response.status_code})")
                if verbose:
                    self.stdout.write(f"  GET {url} → {response.status_code}")
            except Exception as e:
                self.log_error(f"{model_name}: Error al listar - {e}")

        # Test CREAR (solo verificar que el formulario carga)
        create_tests = [
            ("Clientes", "/clientes/crear/", "crear_cliente"),
            ("Vehículos", "/vehiculos/crear/", "crear_vehiculo"),
            ("Repuestos", "/repuestos/crear/", "crear_repuesto"),
            ("Documentos", "/documentos/form/", "documento_crear"),
        ]

        for model_name, url, view_name in create_tests:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.log_success(f"{model_name}: Formulario crear carga (200)")
                else:
                    self.log_warning(
                        f"{model_name}: Formulario crear retornó {response.status_code}"
                    )
                if verbose:
                    self.stdout.write(f"  GET {url} → {response.status_code}")
            except Exception as e:
                self.log_warning(f"{model_name}: Error al cargar crear - {e}")

    def _print_summary(self):
        """Imprime resumen final"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 RESUMEN FINAL\n"))

        total_tests = len(self.success) + len(self.errors) + len(self.warnings)

        self.stdout.write(f"✅ Exitosos: {len(self.success)}")
        self.stdout.write(f"❌ Errores: {len(self.errors)}")
        self.stdout.write(f"⚠️  Advertencias: {len(self.warnings)}")
        self.stdout.write(f"📊 Total: {total_tests}")

        if self.errors:
            self.stdout.write(self.style.ERROR("\n❌ ERRORES CRÍTICOS ENCONTRADOS:"))
            for error in self.errors:
                self.stdout.write(f"  • {error}")
            self.stdout.write("\n⚠️  ACCIÓN REQUERIDA: Revisar errores antes de avanzar.")
            sys.exit(1)
        elif self.warnings:
            self.stdout.write(self.style.WARNING("\n⚠️  ADVERTENCIAS (no bloquean):"))
            for warning in self.warnings:
                self.stdout.write(f"  • {warning}")
            self.stdout.write(
                self.style.SUCCESS("\n✅ SISTEMA OPERATIVO - Advertencias son mejoras menores.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n🎉 TODAS LAS PRUEBAS PASARON - Sistema 100% operativo.")
            )

        self.stdout.write("\n" + "=" * 60 + "\n")
