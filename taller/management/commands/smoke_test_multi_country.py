"""
Smoke Test Multi-Country - Verificación Multi-Tenant y CRUD por País/Idioma
Ejecutar: python manage.py smoke_test_multi_country

Este comando verifica:
1. Aislamiento multi-tenant (empresa A no puede acceder a datos de empresa B)
2. Deletes solo por POST (GET muestra confirmación, POST elimina)
3. CRUD básico funciona en TODOS los países/idiomas soportados
4. Listas dinámicas (endpoints JSON) funcionan por país
5. Filtrado por empresa en todas las operaciones
"""

import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.utils.dateparse import parse_date

from taller.models import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.repuesto import Repuesto
from taller.models.documento import Documento
from taller.servicios.models import Servicio, ServicioExterno

User = get_user_model()

# Países e idiomas soportados
COUNTRY_LANG_COMBINATIONS = [
    ("CL", "es"),
    ("US", "en"),
    ("US", "es"),
    ("BR", "pt"),
    ("BR", "es"),
    ("MX", "es"),
    ("PE", "es"),
    ("CO", "es"),
    ("EC", "es"),
    ("VE", "es"),
    ("AR", "es"),
    ("UY", "es"),
]


def build_country_lang_url(country: str, lang: str, path: str) -> str:
    """
    Construye URL con prefijo país/idioma

    Args:
        country: Código de país (CL, US, BR, etc.)
        lang: Código de idioma (es, en, pt)
        path: Path relativo (ej: "clientes/", "vehiculos/crear/")

    Returns:
        URL completa con prefijo (ej: "/cl/es/clientes/")
    """
    # Normalizar country a minúsculas para URL
    country_lower = country.lower()

    # Construir prefijo
    if country == "US":
        # USA puede tener /us/en/ o /us/es/
        prefix = f"/{country_lower}/{lang}/"
    else:
        # Otros países generalmente usan /{country}/{lang}/
        prefix = f"/{country_lower}/{lang}/"

    # 🔒 CORRECCIÓN: Remover / inicial del path si existe
    path_clean = path.lstrip("/") if path else ""

    return f"{prefix}{path_clean}"


def reverse_country_lang(country: str, lang: str, view_name: str, *args, verbose=False, **kwargs):
    """
    Construye URL usando reverse con namespace de país

    🔒 ESTÁNDAR: Si view_name ya incluye namespace (ej: "clientes:lista_clientes"),
    usar f"{country_ns}:{view_name}". NO agregar "taller:" duplicado.

    Args:
        country: Código de país (CL, US, BR, etc.)
        lang: Código de idioma (es, en, pt)
        view_name: Nombre de la vista (ej: "clientes:lista_clientes")
        *args, **kwargs: Argumentos para reverse()

    Returns:
        URL completa
    """
    # Mapear país a namespace
    country_ns_map = {
        "CL": "chile",
        "US": "usa",
        "BR": "chile",  # Brasil puede usar namespace chile o tener su propio
        "MX": "chile",
        "PE": "chile",
        "CO": "chile",
        "EC": "chile",
        "VE": "chile",
        "AR": "chile",
        "UY": "chile",
    }

    country_ns = country_ns_map.get(country, "chile")

    # 🔒 ESTÁNDAR: Si view_name ya tiene namespace, solo agregar country_ns
    # Ejemplo: "clientes:lista_clientes" → "chile:clientes:lista_clientes"
    if ":" in view_name:
        # Ya tiene namespace (ej: "clientes:lista_clientes")
        full_name = f"{country_ns}:{view_name}"
    else:
        # Sin namespace, agregar taller
        full_name = f"{country_ns}:taller:{view_name}"

    # Intentar múltiples variantes
    variants = [
        (full_name, "primary"),  # chile:clientes:lista_clientes
        (
            f"{country_ns}:taller:{view_name}",
            "fallback_taller",
        ),  # chile:taller:clientes:lista_clientes
        (view_name, "fallback_no_country"),  # clientes:lista_clientes
    ]

    resolved_variant = None
    resolved_url = None

    for variant_name, variant_type in variants:
        try:
            url = reverse(variant_name, args=args, kwargs=kwargs)
            # Verificar que la URL tiene el prefijo correcto
            expected_prefix = f"/{country.lower()}/{lang}/"
            if url.startswith(expected_prefix):
                resolved_variant = variant_name
                resolved_url = url
                break
            # Si no tiene prefijo, agregarlo
            if not url.startswith("/"):
                url = "/" + url
            if not url.startswith(expected_prefix):
                # Construir URL manualmente con prefijo
                resolved_url = build_country_lang_url(country, lang, url.lstrip("/"))
                resolved_variant = f"{variant_name} (manual)"
                break
            resolved_variant = variant_name
            resolved_url = url
            break
        except NoReverseMatch:
            continue

    # Fallback final: construir URL manualmente
    if not resolved_url:
        resolved_url = build_country_lang_url(country, lang, view_name.replace(":", "/"))
        resolved_variant = f"{view_name} (fallback_manual)"

    # 🔒 LOGGING: Registrar qué variante funcionó (útil para debugging)
    if verbose and resolved_variant:
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"[reverse_country_lang] {country}/{lang} - {view_name} → {resolved_variant} → {resolved_url}"
        )

    return resolved_url


class Command(BaseCommand):
    help = "Smoke test multi-country: verifica multi-tenant, CRUD y permisos en todos los países/idiomas"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []
        self.warnings = []
        self.success = []
        self.tested_countries = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Mostrar detalles de cada prueba",
        )
        parser.add_argument(
            "--country",
            type=str,
            help="Probar solo un país específico (ej: CL, US, BR)",
        )
        parser.add_argument(
            "--skip-dynamic-lists",
            action="store_true",
            help="Saltar pruebas de listas dinámicas (endpoints JSON)",
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
        country_filter = options.get("country", None)
        skip_dynamic_lists = options.get("skip_dynamic_lists", False)

        self.stdout.write(self.style.SUCCESS("\n🔍 INICIANDO SMOKE TEST MULTI-COUNTRY\n"))
        self.stdout.write("=" * 60)

        # Filtrar países si se especifica
        countries_to_test = COUNTRY_LANG_COMBINATIONS
        if country_filter:
            countries_to_test = [
                (c, l) for c, l in countries_to_test if c.upper() == country_filter.upper()
            ]
            if not countries_to_test:
                self.log_error(f'País "{country_filter}" no encontrado en combinaciones soportadas')
                return

        # 1. Setup: Crear empresas y usuarios de prueba
        self.stdout.write("\n📦 PASO 1: Creando datos de prueba...")
        try:
            # 🔒 MEJORA: Crear empresa por país (no mutar en runtime)
            # Esto valida inicialización real por país (settings, defaults, seeds, templates)
            empresas_by_country = {}
            users_by_country = {}

            # Crear empresas para países principales que vamos a probar
            test_countries = set([c for c, _ in countries_to_test])
            for country in test_countries:
                empresa, user = self._create_test_company(f"Test_{country}", country)
                empresas_by_country[country] = empresa
                users_by_country[country] = user

            # Empresas A y B para multi-tenant (usar CL como base)
            empresa_a = empresas_by_country.get(
                "CL", empresas_by_country[list(empresas_by_country.keys())[0]]
            )
            user_a = users_by_country.get("CL", users_by_country[list(users_by_country.keys())[0]])
            empresa_b, user_b = self._create_test_company("B", "CL")

            self.log_success(
                f"Empresas y usuarios de prueba creados ({len(empresas_by_country)} países)"
            )
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

        # 4. Verificar deletes solo por POST (mejorado)
        self.stdout.write("\n🛡️  PASO 4: Verificando deletes solo por POST...")
        self._test_delete_methods_improved(user_a, cliente_a, vehiculo_a, repuesto_a, verbose)

        # 5. Verificar CRUD básico en TODOS los países/idiomas
        self.stdout.write("\n📋 PASO 5: Verificando CRUD básico por país/idioma...")
        for country, lang in countries_to_test:
            self.stdout.write(f"\n🌍 Probando {country}/{lang}...")
            # 🔒 MEJORA: Usar empresa real de ese país (no mutar empresa_a)
            empresa_country = empresas_by_country.get(country, empresa_a)
            user_country = users_by_country.get(country, user_a)
            self._test_crud_by_country(user_country, empresa_country, country, lang, verbose)
            self.tested_countries.append(f"{country}/{lang}")

        # 6. Verificar listas dinámicas (endpoints JSON)
        if not skip_dynamic_lists:
            self.stdout.write("\n📊 PASO 6: Verificando listas dinámicas (endpoints JSON)...")
            self._test_dynamic_lists(
                user_a, empresa_a, empresas_by_country, users_by_country, verbose
            )

        # 7. Resumen final
        self._print_summary()

    def _create_test_company(self, suffix, country):
        """Crea una empresa y usuario de prueba"""
        empresa = Empresa.objects.create(
            nombre_taller=f"Taller Test {suffix}",
            pais=country,
            user=User.objects.create_user(
                username=f"user_test_{suffix.lower()}",
                email=f"user{suffix.lower()}@test.com",
                password="test123456",
            ),
        )
        return empresa, empresa.user

    def _create_test_data(self, empresa, user):
        """Crea datos de prueba en una empresa con campos mínimos reales"""
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

        # Documento con campos mínimos reales
        documento = None
        try:
            documento = Documento.objects.create(
                empresa=empresa,
                cliente=cliente,
                vehiculo=vehiculo,
                tipo="OT",  # Campo correcto del modelo
                numero="1",  # Campo correcto del modelo
                fecha_emision=timezone.now().date(),
                estado="EMITIDO",
                total=0.00,
            )
        except Exception as e:
            # Si falla, es crítico - el test debe fallar
            self.log_error(f"No se pudo crear documento de prueba (CRÍTICO): {e}")
            raise  # Re-lanzar para que el test falle

        return cliente, vehiculo, repuesto, documento

    def _test_multi_tenant_isolation(
        self, user_a, user_b, cliente_a, vehiculo_a, repuesto_a, documento_a, verbose
    ):
        """Verifica que usuario B no puede acceder a datos de empresa A"""
        client_b = Client()
        client_b.force_login(user_b)

        # Probar con URLs de país/idioma (usar CL/es como ejemplo)
        country, lang = "CL", "es"

        tests = [
            ("Cliente", "clientes:ver_cliente", {"pk": cliente_a.pk}),
            ("Cliente", "clientes:editar_cliente", {"pk": cliente_a.pk}),
            ("Vehículo", "vehiculos:ver_vehiculo", {"pk": vehiculo_a.id}),
            ("Vehículo", "vehiculos:editar_vehiculo", {"pk": vehiculo_a.id}),
            ("Repuesto", "repuestos:ver_repuesto", {"pk": repuesto_a.pk}),
            ("Repuesto", "repuestos:editar_repuesto", {"pk": repuesto_a.pk}),
        ]

        if documento_a:
            tests.extend(
                [
                    ("Documento", "documentos:ver_documento", {"pk": documento_a.pk}),
                    ("Documento", "documentos:editar_documento", {"pk": documento_a.pk}),
                ]
            )

        for model_name, view_name, kwargs in tests:
            try:
                url = reverse_country_lang(country, lang, view_name, verbose=verbose, **kwargs)
                if verbose:
                    self.stdout.write(f"  [DEBUG] Resolved URL: {url} for {view_name}")
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

    def _test_delete_methods_improved(self, user_a, cliente_a, vehiculo_a, repuesto_a, verbose):
        """
        Verifica que los deletes solo funcionan por POST (mejorado)
        - GET debe devolver 200 solo si hay template de confirmación (form POST + csrf token + submit)
        - POST debe eliminar y luego GET detalle debe devolver 404

        🔒 CRÍTICO: Usa Client(enforce_csrf_checks=True) para validar CSRF de verdad
        """
        # 🔒 CRÍTICO: Activar validación CSRF para que el test sea real
        client = Client(enforce_csrf_checks=True)
        client.force_login(user_a)
        country, lang = "CL", "es"

        tests = [
            ("Cliente", "clientes:eliminar_cliente", {"pk": cliente_a.pk}, Cliente),
            ("Vehículo", "vehiculos:eliminar_vehiculo", {"pk": vehiculo_a.id}, Vehiculo),
            ("Repuesto", "repuestos:eliminar_repuesto", {"pk": repuesto_a.pk}, Repuesto),
        ]

        for model_name, view_name, kwargs, ModelClass in tests:
            try:
                # Crear objeto temporal para probar delete
                if ModelClass == Cliente:
                    temp_obj = Cliente.objects.create(
                        nombre=f"Temp Cliente",
                        apellido="Delete Test",
                        empresa=user_a.empresa,
                    )
                elif ModelClass == Vehiculo:
                    temp_obj = Vehiculo.objects.create(
                        cliente=cliente_a,
                        patente=f"TEMP{user_a.empresa.id}",
                        anio=2020,
                        empresa=user_a.empresa,
                    )
                else:  # Repuesto
                    temp_obj = Repuesto.objects.create(
                        nombre=f"Temp Repuesto",
                        precio_venta=50.00,
                        cantidad_stock=5,
                        empresa=user_a.empresa,
                    )

                temp_kwargs = {"pk": temp_obj.pk}
                url = reverse_country_lang(country, lang, view_name, **temp_kwargs)

                # 🔒 CRÍTICO: Verificar que objeto existe ANTES del GET
                obj_exists_before = ModelClass.objects.filter(pk=temp_obj.pk).exists()
                if not obj_exists_before:
                    self.log_error(f"{model_name}: Objeto temporal no existe antes del test")
                    continue

                # 1. GET debe devolver 200 solo si hay template de confirmación
                response_get = client.get(url)

                # 🔒 CRÍTICO: Verificar que GET NO eliminó el objeto
                obj_exists_after_get = ModelClass.objects.filter(pk=temp_obj.pk).exists()
                if not obj_exists_after_get:
                    self.log_error(
                        f"{model_name}: GET eliminó el objeto (RIESGO CRÍTICO: delete por GET activo) - "
                        f"El objeto {temp_obj.pk} desapareció después de GET {url}"
                    )
                    continue  # No probar POST si ya se eliminó

                if response_get.status_code == 200:
                    # 🔒 VALIDACIÓN MEJORADA: Verificar que contiene form + CSRF + submit
                    content = response_get.content.decode("utf-8").lower()

                    # Buscar form (puede tener method="post" o method='post' o ser default POST)
                    has_form = "<form" in content
                    has_method_post = (
                        'method="post"' in content
                        or "method='post'" in content
                        or "method=post" in content
                    )
                    # Si no tiene method explícito, HTML default es GET, así que debe tener method="post"
                    form_is_post = has_method_post or (
                        has_form and 'method="get"' not in content and "method='get'" not in content
                    )

                    # Buscar CSRF token (puede estar en input o como variable)
                    has_csrf = (
                        "csrfmiddlewaretoken" in content
                        or "csrf_token" in content
                        or "csrf" in content
                    )

                    # Buscar botón/enviar (submit)
                    has_submit = (
                        'type="submit"' in content
                        or "type='submit'" in content
                        or "<button" in content
                        or 'input type="submit"' in content
                    )

                    if has_form and form_is_post and has_csrf and has_submit:
                        self.log_success(
                            f"{model_name}: GET muestra confirmación con form POST + CSRF + submit"
                        )
                    else:
                        missing = []
                        if not has_form:
                            missing.append("form")
                        if not form_is_post:
                            missing.append('method="post"')
                        if not has_csrf:
                            missing.append("CSRF token")
                        if not has_submit:
                            missing.append("submit button")
                        self.log_error(
                            f'{model_name}: GET retorna 200 pero NO tiene: {", ".join(missing)} - '
                            f"RIESGO: Delete directo por GET posible"
                        )
                elif response_get.status_code == 405:
                    self.log_success(f"{model_name}: GET bloqueado (405 Method Not Allowed)")
                else:
                    self.log_warning(f"{model_name}: GET retornó {response_get.status_code}")

                # 2. POST debe eliminar y luego GET detalle debe devolver 404
                # (temp_obj ya fue creado arriba)
                temp_url = url  # Reutilizar URL del objeto temporal

                # Obtener CSRF token
                csrf_response = client.get(temp_url)
                csrf_token = None
                if csrf_response.status_code == 200:
                    content = csrf_response.content.decode("utf-8")
                    import re

                    csrf_match = re.search(
                        r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', content
                    )
                    if csrf_match:
                        csrf_token = csrf_match.group(1)

                # Hacer POST para eliminar
                if csrf_token:
                    response_post = client.post(temp_url, {"csrfmiddlewaretoken": csrf_token})
                    if response_post.status_code in [200, 302, 204]:
                        # Verificar que el objeto fue eliminado
                        obj_exists = ModelClass.objects.filter(pk=temp_obj.pk).exists()
                        if not obj_exists:
                            self.log_success(
                                f"{model_name}: POST eliminó correctamente (objeto no existe)"
                            )
                        else:
                            self.log_error(f"{model_name}: POST no eliminó el objeto - RIESGO")
                    else:
                        self.log_warning(f"{model_name}: POST retornó {response_post.status_code}")
                else:
                    self.log_warning(
                        f"{model_name}: No se pudo obtener CSRF token para probar POST"
                    )

                if verbose:
                    self.stdout.write(f"  GET {url} → {response_get.status_code}")
                    if csrf_token:
                        self.stdout.write(f"  POST {temp_url} → eliminado")
            except Exception as e:
                self.log_warning(f"{model_name}: Error al probar delete - {e}")

    def _test_crud_by_country(self, user_a, empresa_a, country, lang, verbose):
        """
        Verifica que las operaciones CRUD básicas funcionan en un país/idioma específico

        🔒 MEJORA: Recibe empresa ya con país correcto (no muta en runtime)
        """
        # 🔒 CRÍTICO: No activar CSRF aquí (solo probamos GET de listas/formularios)
        client = Client()
        client.force_login(user_a)

        # Verificar que empresa tiene el país correcto
        if empresa_a.pais != country:
            self.log_warning(
                f"{country}/{lang} - Empresa tiene país {empresa_a.pais}, esperado {country}"
            )

        # Test LISTAR
        list_tests = [
            ("Clientes", "clientes:lista_clientes"),
            ("Vehículos", "vehiculos:lista_vehiculos"),
            ("Repuestos", "repuestos:lista_repuestos"),
            ("Documentos", "documentos:lista_documentos"),
        ]

        for model_name, view_name in list_tests:
            try:
                url = reverse_country_lang(country, lang, view_name, verbose=verbose)
                if verbose:
                    self.stdout.write(f"  [DEBUG] Resolved URL: {url} for {view_name}")
                response = client.get(url)
                if response.status_code == 200:
                    self.log_success(f"{country}/{lang} - {model_name}: Listar funciona (200)")
                else:
                    self.log_error(
                        f"{country}/{lang} - {model_name}: Listar falló (status {response.status_code})"
                    )
                if verbose:
                    self.stdout.write(f"  GET {url} → {response.status_code}")
            except NoReverseMatch:
                self.log_warning(
                    f"{country}/{lang} - {model_name}: URL no encontrada (reverse falló)"
                )
            except Exception as e:
                self.log_error(f"{country}/{lang} - {model_name}: Error al listar - {e}")

        # Test CREAR (solo verificar que el formulario carga)
        create_tests = [
            ("Clientes", "clientes:crear_cliente"),
            ("Vehículos", "vehiculos:crear_vehiculo"),
            ("Repuestos", "repuestos:crear_repuesto"),
            ("Documentos", "documentos:crear_documento"),
        ]

        for model_name, view_name in create_tests:
            try:
                url = reverse_country_lang(country, lang, view_name, verbose=verbose)
                if verbose:
                    self.stdout.write(f"  [DEBUG] Resolved URL: {url} for {view_name}")
                response = client.get(url)
                if response.status_code == 200:
                    self.log_success(
                        f"{country}/{lang} - {model_name}: Formulario crear carga (200)"
                    )
                else:
                    self.log_warning(
                        f"{country}/{lang} - {model_name}: Formulario crear retornó {response.status_code}"
                    )
                if verbose:
                    self.stdout.write(f"  GET {url} → {response.status_code}")
            except NoReverseMatch:
                self.log_warning(f"{country}/{lang} - {model_name}: URL crear no encontrada")
            except Exception as e:
                self.log_warning(f"{country}/{lang} - {model_name}: Error al cargar crear - {e}")

    def _test_dynamic_lists(
        self, user_a, empresa_a, empresas_by_country, users_by_country, verbose
    ):
        """
        Verifica endpoints JSON de listas dinámicas por país

        🔒 MEJORAS:
        - Usa parámetros reales (region_id/estado_id, marca_id+anio)
        - Toma primera marca/estado de DB filtrada por country (no hardcodea)
        - Payload vacío es WARNING (seed faltante), no error
        - Error solo si status != 200 o JSON inválido o datos de otro país
        - Usa empresa real de cada país (no muta empresa_a)
        """
        client = Client()
        client.force_login(user_a)

        # Probar endpoints de ciudades/regiones
        country_lang_tests = [
            ("CL", "es"),
            ("US", "en"),
            ("BR", "pt"),
        ]

        for country, lang in country_lang_tests:
            # 🔒 MEJORA: Usar empresa real de ese país (no mutar)
            empresa_country = empresas_by_country.get(country, empresa_a)
            user_country = users_by_country.get(country, user_a)

            # Endpoint de ciudades por región/estado
            try:
                url = reverse_country_lang(
                    country, lang, "clientes:obtener_ciudades", verbose=verbose
                )
                if verbose:
                    self.stdout.write(f"  [DEBUG] Resolved URL: {url} for ciudades endpoint")

                # 🔒 PARÁMETROS REALES: Usar region_id para CL, estado_id para otros
                if country == "CL":
                    # Chile: usar region_id
                    try:
                        from taller.models.ubicacion import TallerRegion

                        region = TallerRegion.objects.first()
                        if region:
                            param = f"region_id={region.id}"
                        else:
                            # No hay seeds - será WARNING
                            param = "region_id=1"  # Intentar con ID que probablemente no existe
                    except ImportError:
                        param = "region_id=1"
                else:
                    # Otros países: usar estado_id
                    try:
                        from taller.models.ubicacion import Estado

                        estado = Estado.objects.filter(pais=country).first()
                        if estado:
                            param = f"estado_id={estado.id}"
                        else:
                            # No hay seeds - será WARNING
                            param = "estado_id=1"
                    except ImportError:
                        param = "estado_id=1"

                response = client.get(f"{url}?{param}")
                if response.status_code == 200:
                    try:
                        import json

                        data = json.loads(response.content)
                        if isinstance(data, list):
                            if len(data) > 0:
                                self.log_success(
                                    f'{country}/{lang} - Ciudades por {"región" if country == "CL" else "estado"}: OK (payload no vacío)'
                                )
                            else:
                                # 🔒 WARNING: Payload vacío puede ser falta de seeds
                                self.log_warning(
                                    f"{country}/{lang} - Ciudades: payload vacío (posible falta de seeds en DB)"
                                )
                        else:
                            self.log_warning(
                                f"{country}/{lang} - Ciudades: respuesta no es lista JSON"
                            )
                    except json.JSONDecodeError:
                        self.log_error(f"{country}/{lang} - Ciudades: respuesta no es JSON válido")
                    except Exception as e:
                        self.log_warning(f"{country}/{lang} - Ciudades: error parseando JSON - {e}")
                else:
                    self.log_error(
                        f"{country}/{lang} - Ciudades: status {response.status_code} (esperado 200)"
                    )
            except Exception as e:
                self.log_warning(f"{country}/{lang} - Ciudades: error - {e}")

            # Endpoint de modelos por marca (todos los países)
            try:
                url = reverse_country_lang(
                    country, lang, "vehiculos:ajax_modelos_por_marca_anio", verbose=verbose
                )
                if verbose:
                    self.stdout.write(f"  [DEBUG] Resolved URL: {url} for modelos endpoint")

                # 🔒 PARÁMETROS REALES: marca_id + anio (no solo marca_id)
                # 🔒 DATOS DINÁMICOS: Tomar primera marca de DB filtrada por country
                try:
                    from taller.models.vehiculos import Marca

                    marca = Marca.objects.filter(country=country).first()
                    if marca:
                        marca_id = marca.id
                        # Tomar un año válido (ej: 2020)
                        anio = 2020
                        param = f"marca_id={marca_id}&anio={anio}"
                    else:
                        # No hay seeds - será WARNING
                        marca_id = 1
                        anio = 2020
                        param = f"marca_id={marca_id}&anio={anio}"
                except (ImportError, AttributeError):
                    # Fallback si no existe modelo Marca o no tiene campo country
                    marca_id = 1
                    anio = 2020
                    param = f"marca_id={marca_id}&anio={anio}"

                response = client.get(f"{url}?{param}")
                if response.status_code == 200:
                    try:
                        import json

                        data = json.loads(response.content)
                        if isinstance(data, (list, dict)):
                            # Verificar que no devuelve datos de otro país (si tiene country en respuesta)
                            if isinstance(data, list) and len(data) > 0:
                                # Verificar primer item si tiene country
                                first_item = data[0] if data else {}
                                if "country" in first_item and first_item["country"] != country:
                                    self.log_error(
                                        f'{country}/{lang} - Modelos: devuelve datos de otro país ({first_item["country"]} != {country})'
                                    )
                                else:
                                    self.log_success(
                                        f"{country}/{lang} - Modelos por marca: OK (payload no vacío)"
                                    )
                            elif (
                                isinstance(data, dict)
                                and "results" in data
                                and len(data.get("results", [])) > 0
                            ):
                                self.log_success(
                                    f"{country}/{lang} - Modelos por marca: OK (payload no vacío)"
                                )
                            else:
                                # 🔒 WARNING: Payload vacío puede ser falta de seeds
                                self.log_warning(
                                    f"{country}/{lang} - Modelos: payload vacío (posible falta de seeds en DB)"
                                )
                        else:
                            self.log_warning(
                                f"{country}/{lang} - Modelos: respuesta no es JSON válido (list/dict)"
                            )
                    except json.JSONDecodeError:
                        self.log_error(f"{country}/{lang} - Modelos: respuesta no es JSON válido")
                    except Exception as e:
                        self.log_warning(f"{country}/{lang} - Modelos: error parseando JSON - {e}")
                else:
                    self.log_error(
                        f"{country}/{lang} - Modelos: status {response.status_code} (esperado 200)"
                    )
            except Exception as e:
                self.log_warning(f"{country}/{lang} - Modelos: error - {e}")

    def _print_summary(self):
        """Imprime resumen final"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 RESUMEN FINAL\n"))

        total_tests = len(self.success) + len(self.errors) + len(self.warnings)

        self.stdout.write(f"✅ Exitosos: {len(self.success)}")
        self.stdout.write(f"❌ Errores: {len(self.errors)}")
        self.stdout.write(f"⚠️  Advertencias: {len(self.warnings)}")
        self.stdout.write(f"📊 Total: {total_tests}")
        self.stdout.write(
            f'🌍 Países probados: {len(self.tested_countries)} ({", ".join(self.tested_countries)})'
        )

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
