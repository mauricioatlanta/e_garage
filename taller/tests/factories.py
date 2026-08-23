"""
taller/tests/factories.py — Test object factories for eGarage.

Design constraints:
  - Zero third-party dependencies (no factory_boy, model_bakery, faker).
  - Each factory creates only the minimum required relations.
  - Thread-safe unique sequence for usernames / emails / patenets.
  - Every factory accepts **kwargs so callers can override any field.
  - ConfiguracionEmpresa is NOT auto-created by EmpresaFactory; pass
    with_config=True when the test needs it.

Quick reference
---------------
    empresa  = EmpresaFactory()
    empresa  = EmpresaFactory(pais="US", with_config=True)
    cliente  = ClienteFactory(empresa=empresa)
    vehiculo = VehiculoFactory(empresa=empresa)          # no cliente
    vehiculo = VehiculoFactory(empresa=empresa, cliente=cliente)
    doc      = DocumentoFactory(empresa=empresa)
    doc      = DocumentoFactory(empresa=empresa, cliente=cliente, vehiculo=vehiculo)
    repuesto = RepuestoFactory(empresa=empresa)
    user     = UserFactory()
    config   = ConfiguracionEmpresaFactory(empresa=empresa)
"""

import itertools
import threading
from decimal import Decimal

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_EXTERNO
from taller.models.pieza_desarme import PiezaDesarme
from taller.models.reciclaje import CategoriaChatarra, ProductoChatarra, Catalitico
from taller.models.repuesto import Repuesto
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo

# ---------------------------------------------------------------------------
# Thread-safe sequence — unique across the entire test run, not per-process.
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_counter = itertools.count(1)


def _seq() -> int:
    with _lock:
        return next(_counter)


# ---------------------------------------------------------------------------
# UserFactory
# ---------------------------------------------------------------------------

def UserFactory(**kwargs) -> User:
    """
    Creates a Django User with a unique username and email.

    Auto-generated:
        username  → "user_<n>"
        email     → "user_<n>@test.egarage.cl"
        password  → "testpass" (set_password, not raw)

    Override any field via kwargs:
        UserFactory(username="alice", email="alice@example.com")
    """
    n = _seq()
    defaults = dict(
        username=f"user_{n}",
        email=f"user_{n}@test.egarage.cl",
        password="testpass",
    )
    defaults.update(kwargs)
    password = defaults.pop("password", "testpass")
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


# ---------------------------------------------------------------------------
# EmpresaFactory
# ---------------------------------------------------------------------------

def EmpresaFactory(*, with_config: bool = False, **kwargs) -> Empresa:
    """
    Creates an Empresa with a freshly created User.

    Auto-created dependencies:
        User  — unique per call, not reused across factories.

    Auto-generated fields:
        nombre_taller → "Empresa <n>"
        pais          → "CL"
        slug          → auto-derived from nombre_taller (by Empresa.save)
        fecha_fin     → auto-set to fecha_inicio + dias_prueba (by Empresa.save)

    Optional:
        with_config=True  → also creates a ConfiguracionEmpresa for the empresa.

    Override any field:
        EmpresaFactory(pais="US")
        EmpresaFactory(pais="CL", plan="growth")
        EmpresaFactory(user=existing_user)   # skip auto-created user

    Returns the Empresa instance. If with_config=True, the config is
    accessible as empresa.config (OneToOne reverse accessor).
    """
    n = _seq()
    if "user" not in kwargs:
        kwargs["user"] = UserFactory()

    defaults = dict(
        nombre_taller=f"Empresa {n}",
        pais="CL",
    )
    defaults.update(kwargs)
    empresa = Empresa.objects.create(**defaults)

    if with_config:
        ConfiguracionEmpresaFactory(empresa=empresa)

    return empresa


# ---------------------------------------------------------------------------
# ConfiguracionEmpresaFactory
# ---------------------------------------------------------------------------

def ConfiguracionEmpresaFactory(*, empresa: Empresa | None = None, **kwargs) -> ConfiguracionEmpresa:
    """
    Creates a ConfiguracionEmpresa for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().

    Auto-generated fields:
        nombre_publico → empresa.nombre_taller
        rubro_principal → "WORKSHOP"

    All fields are nullable except empresa; the factory only sets the minimum.
    """
    if empresa is None:
        empresa = EmpresaFactory()

    defaults = dict(
        empresa=empresa,
        nombre_publico=empresa.nombre_taller,
        rubro_principal="WORKSHOP",
    )
    defaults.update(kwargs)
    return ConfiguracionEmpresa.objects.create(**defaults)


# ---------------------------------------------------------------------------
# ClienteFactory
# ---------------------------------------------------------------------------

def ClienteFactory(*, empresa: Empresa | None = None, **kwargs) -> Cliente:
    """
    Creates a Cliente for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().

    Auto-generated fields:
        nombre   → "Cliente <n>"
        apellido → "Test"

    Override:
        ClienteFactory(empresa=empresa, nombre="Juan", email="juan@example.com")
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = dict(
        empresa=empresa,
        nombre=f"Cliente {n}",
        apellido="Test",
    )
    defaults.update(kwargs)
    return Cliente.objects.create(**defaults)


# ---------------------------------------------------------------------------
# VehiculoFactory
# ---------------------------------------------------------------------------

def VehiculoFactory(
    *,
    empresa: Empresa | None = None,
    cliente: Cliente | None = None,
    **kwargs,
) -> Vehiculo:
    """
    Creates a Vehiculo for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().
    cliente is optional (Vehiculo.cliente is null=True, blank=True).

    Auto-generated fields:
        patente      → "TEST<n>" (unique, max 20 chars)
        marca_texto  → "Toyota"
        modelo_texto → "Corolla"

    Override:
        VehiculoFactory(empresa=empresa, patente="ABC123", anio=2022)
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = dict(
        empresa=empresa,
        patente=f"T{n:05d}",
        marca_texto="Toyota",
        modelo_texto="Corolla",
    )
    if cliente is not None:
        defaults["cliente"] = cliente
    defaults.update(kwargs)
    return Vehiculo.objects.create(**defaults)


# ---------------------------------------------------------------------------
# DocumentoFactory
# ---------------------------------------------------------------------------

def DocumentoFactory(
    *,
    empresa: Empresa | None = None,
    cliente: Cliente | None = None,
    vehiculo: Vehiculo | None = None,
    **kwargs,
) -> Documento:
    """
    Creates a Documento for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().
    cliente is required by the DB (NOT NULL); if not supplied, one is
    created automatically for the empresa.
    vehiculo is optional (Documento.vehiculo is null=True, blank=True).

    Auto-generated fields:
        tipo   → "OT"
        estado → "BORRADOR"
        numero → "" (Documento.save() generates sequence number on EMITIDO)

    Override:
        DocumentoFactory(empresa=empresa, tipo="PRES")
        DocumentoFactory(empresa=empresa, cliente=cliente, vehiculo=vehiculo)
    """
    if empresa is None:
        empresa = EmpresaFactory()
    if cliente is None:
        cliente = ClienteFactory(empresa=empresa)

    defaults = dict(
        empresa=empresa,
        cliente=cliente,
        tipo="OT",
        estado="BORRADOR",
    )
    if vehiculo is not None:
        defaults["vehiculo"] = vehiculo
    defaults.update(kwargs)
    return Documento.objects.create(**defaults)


# ---------------------------------------------------------------------------
# RepuestoFactory
# ---------------------------------------------------------------------------

def RepuestoFactory(*, empresa: Empresa | None = None, **kwargs) -> Repuesto:
    """
    Creates a Repuesto for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().

    Auto-generated fields:
        nombre          → "Repuesto <n>"
        precio_venta    → Decimal("10000.00")
        cantidad_stock  → 5
        stock_minimo    → 2

    Override:
        RepuestoFactory(empresa=empresa, precio_venta=Decimal("500.00"), cantidad_stock=0)
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = dict(
        empresa=empresa,
        nombre=f"Repuesto {n}",
        precio_venta=Decimal("10000.00"),
        cantidad_stock=5,
        stock_minimo=2,
    )
    defaults.update(kwargs)
    return Repuesto.objects.create(**defaults)


# ---------------------------------------------------------------------------
# VehiculoDesarmeFactory
# ---------------------------------------------------------------------------

def VehiculoDesarmeFactory(*, empresa=None, **kwargs) -> VehiculoDesarme:
    """
    Creates a VehiculoDesarme for an Empresa.

    Auto-generated fields:
        estado_desarme → "INGRESADO"
        es_placeholder → False

    Override:
        VehiculoDesarmeFactory(empresa=empresa, estado_desarme="AGOTADO")
    """
    if empresa is None:
        empresa = EmpresaFactory()

    defaults = dict(empresa=empresa, estado_desarme="INGRESADO")
    defaults.update(kwargs)
    return VehiculoDesarme.objects.create(**defaults)


# ---------------------------------------------------------------------------
# PiezaDesarmeFactory
# ---------------------------------------------------------------------------

def PiezaDesarmeFactory(*, empresa=None, vehiculo_desarme=None, **kwargs) -> PiezaDesarme:
    """
    Creates a PiezaDesarme for an Empresa.

    If no empresa is supplied, one is created via EmpresaFactory().
    If no vehiculo_desarme is supplied, one is created via VehiculoDesarmeFactory().

    Auto-generated fields:
        codigo         → "PIE-<n>"
        nombre         → "Pieza <n>"
        estado_pieza   → "DISPONIBLE"
        activo         → True

    Override:
        PiezaDesarmeFactory(empresa=empresa, imagen=None, precio_venta_sugerido=None)
    """
    if empresa is None:
        empresa = EmpresaFactory()

    if vehiculo_desarme is None:
        vehiculo_desarme = VehiculoDesarmeFactory(empresa=empresa)

    n = _seq()
    defaults = dict(
        empresa=empresa,
        vehiculo_desarme=vehiculo_desarme,
        codigo=f"PIE-{n}",
        nombre=f"Pieza {n}",
        estado_pieza="DISPONIBLE",
        activo=True,
    )
    defaults.update(kwargs)
    return PiezaDesarme.objects.create(**defaults)


# ---------------------------------------------------------------------------
# LineaRepuestoFactory
# ---------------------------------------------------------------------------

def LineaRepuestoFactory(*, documento=None, empresa=None, **kwargs) -> LineaRepuesto:
    """
    Creates a LineaRepuesto for a Documento.

    If no documento is supplied, one is created via DocumentoFactory() for
    the given empresa (or a new one). Uses ORIGEN_EXTERNO to avoid FK
    requirements on Repuesto/PiezaDesarme.

    Auto-generated fields:
        codigo         → "COD-<n>"
        nombre         → "Pieza <n>"
        cantidad       → 1
        precio_unitario → Decimal("5000.00")
        origen_repuesto → ORIGEN_EXTERNO

    Override:
        LineaRepuestoFactory(documento=doc, cantidad=5)
    """
    if documento is None:
        if empresa is None:
            empresa = EmpresaFactory()
        documento = DocumentoFactory(empresa=empresa)

    n = _seq()
    defaults = dict(
        documento=documento,
        codigo=f"COD-{n}",
        nombre=f"Pieza {n}",
        cantidad=1,
        precio_unitario=Decimal("5000.00"),
        origen_repuesto=ORIGEN_EXTERNO,
    )
    defaults.update(kwargs)
    return LineaRepuesto.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Reciclaje (Atlanta Reciclajes): CategoriaChatarraFactory, ProductoChatarraFactory,
# CataliticoFactory
# ---------------------------------------------------------------------------

def CategoriaChatarraFactory(*, empresa: Empresa | None = None, **kwargs) -> CategoriaChatarra:
    """
    Creates a CategoriaChatarra for an Empresa.

    Auto-generated fields:
        nombre → "Categoría Chatarra <n>"
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = {
        "empresa": empresa,
        "nombre": f"Categoría Chatarra {n}",
    }
    defaults.update(kwargs)
    return CategoriaChatarra.objects.create(**defaults)


def ProductoChatarraFactory(*, empresa: Empresa | None = None, **kwargs) -> ProductoChatarra:
    """
    Creates a ProductoChatarra for an Empresa.

    Auto-generated fields:
        codigo         → "CHT-<n>"
        nombre         → "Chatarra <n>"
        precio_venta   → Decimal("1000.00")
        cantidad_stock → Decimal("10.000")

    Override:
        ProductoChatarraFactory(empresa=empresa, codigo="CU-01", unidad_medida=ProductoChatarra.UNIDAD_KG)
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = {
        "empresa": empresa,
        "codigo": f"CHT-{n}",
        "nombre": f"Chatarra {n}",
        "precio_venta": Decimal("1000.00"),
        "cantidad_stock": Decimal("10.000"),
    }
    defaults.update(kwargs)
    return ProductoChatarra.objects.create(**defaults)


def CataliticoFactory(*, empresa: Empresa | None = None, **kwargs) -> Catalitico:
    """
    Creates a Catalitico for an Empresa.

    Auto-generated fields:
        codigo       → "CAT-<n>"
        precio_venta → Decimal("50000.00")

    Override:
        CataliticoFactory(empresa=empresa, estado=Catalitico.ESTADO_VENDIDO)
    """
    if empresa is None:
        empresa = EmpresaFactory()

    n = _seq()
    defaults = {
        "empresa": empresa,
        "codigo": f"CAT-{n}",
        "nombre": f"Catalítico {n}",
        "precio_venta": Decimal("50000.00"),
    }
    defaults.update(kwargs)
    return Catalitico.objects.create(**defaults)
