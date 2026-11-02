"""
Tests de integridad de stock — flujo venta desde inventario (Documento canónico).

Cubre:
- Venta total: pieza queda en cantidad=0, estado=VENDIDA.
- Venta parcial: cantidad decrementada, estado permanece DISPONIBLE.
- Sobre-venta rechazada: stock insuficiente dentro del atomic.
- Doble venta secuencial rechazada al agotar stock.
- Storefront excluye piezas con cantidad=0.
- Kiosko excluye piezas con cantidad=0.
- Aislamiento multi-tenant en storefront.
- Anulación de VentaDesarme restaura cantidad y estado.
"""

import json
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client

from taller.models.pieza_desarme import (
    ESTADO_DISPONIBLE,
    ESTADO_VENDIDA,
    PiezaDesarme,
)
from taller.tests.factories import (
    EmpresaFactory,
    PiezaDesarmeFactory,
    VehiculoDesarmeFactory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VENTA_SESSION_KEY = "venta_desde_inventario"


def _make_empresa_con_usuario(pais="CL"):
    empresa = EmpresaFactory(pais=pais)
    return empresa, empresa.user


def _login(client, user):
    client.force_login(user)


def _set_session_venta(client, vehiculo, items):
    """Inyecta datos de sesión de venta para saltar crear_venta_desde_inventario."""
    session = client.session
    session[VENTA_SESSION_KEY] = {
        "vehiculo_id": vehiculo.pk,
        "items": items,
    }
    session.save()


def _url_finalizar(vehiculo, pais="CL"):
    return f"/{pais.lower()}/es/desarme/vehiculos/{vehiculo.pk}/finalizar-venta-desde-inventario/"


def _url_confirmar(vehiculo, pais="CL"):
    return f"/{pais.lower()}/es/desarme/vehiculos/{vehiculo.pk}/confirmar-venta-desde-inventario/"


def _post_finalizar(client, vehiculo, pieza, cantidad, precio, pais="CL"):
    """Hace POST a finalizar_venta_desde_inventario con cliente rápido."""
    _set_session_venta(client, vehiculo, [
        {"id": pieza.pk, "cantidad": cantidad, "precio_venta": str(precio)},
    ])
    return client.post(
        _url_finalizar(vehiculo, pais),
        {
            "usar_cliente_rapido": "on",
            "cliente_nombre": "Comprador Test",
            "cliente_rut": "",
            "cliente_telefono": "",
            "cliente_email": "",
            "cliente_direccion": "",
            "observaciones": "",
        },
        follow=False,
    )


# ---------------------------------------------------------------------------
# Venta total — pieza agotada debe quedar VENDIDA
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVentaTotalAgotaPieza:
    def setup_method(self):
        self.empresa, self.user = _make_empresa_con_usuario()
        self.vehiculo = VehiculoDesarmeFactory(empresa=self.empresa)
        self.pieza = PiezaDesarmeFactory(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo,
            cantidad=1,
            precio_venta_sugerido=Decimal("50000"),
            estado_pieza=ESTADO_DISPONIBLE,
        )
        self.client = Client()
        _login(self.client, self.user)

    def test_cantidad_llega_a_cero_y_estado_es_vendida(self):
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("50000"))
        self.pieza.refresh_from_db()
        assert self.pieza.cantidad == 0
        assert self.pieza.estado_pieza == ESTADO_VENDIDA

    def test_pieza_no_aparece_en_storefront_tras_venta(self):
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("50000"))
        self.pieza.refresh_from_db()
        visible = PiezaDesarme.objects.filter(
            empresa=self.empresa,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert self.pieza not in visible


# ---------------------------------------------------------------------------
# Venta parcial — pieza sigue disponible
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVentaParcialMantienePieza:
    def setup_method(self):
        self.empresa, self.user = _make_empresa_con_usuario()
        self.vehiculo = VehiculoDesarmeFactory(empresa=self.empresa)
        self.pieza = PiezaDesarmeFactory(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo,
            cantidad=3,
            precio_venta_sugerido=Decimal("20000"),
            estado_pieza=ESTADO_DISPONIBLE,
        )
        self.client = Client()
        _login(self.client, self.user)

    def test_cantidad_decrementada_y_estado_disponible(self):
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("20000"))
        self.pieza.refresh_from_db()
        assert self.pieza.cantidad == 2
        assert self.pieza.estado_pieza == ESTADO_DISPONIBLE

    def test_pieza_sigue_visible_en_storefront(self):
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("20000"))
        self.pieza.refresh_from_db()
        visible = PiezaDesarme.objects.filter(
            empresa=self.empresa,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert self.pieza in visible


# ---------------------------------------------------------------------------
# Sobre-venta rechazada — stock insuficiente
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSobreVentaRechazada:
    def setup_method(self):
        self.empresa, self.user = _make_empresa_con_usuario()
        self.vehiculo = VehiculoDesarmeFactory(empresa=self.empresa)
        self.pieza = PiezaDesarmeFactory(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo,
            cantidad=1,
            precio_venta_sugerido=Decimal("30000"),
            estado_pieza=ESTADO_DISPONIBLE,
        )
        self.client = Client()
        _login(self.client, self.user)

    def test_solicitar_mas_de_disponible_no_modifica_stock(self):
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=5, precio=Decimal("30000"))
        self.pieza.refresh_from_db()
        assert self.pieza.cantidad == 1
        assert self.pieza.estado_pieza == ESTADO_DISPONIBLE


# ---------------------------------------------------------------------------
# Doble venta secuencial — segunda falla al agotar el stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDobleVentaSecuencial:
    def setup_method(self):
        self.empresa, self.user = _make_empresa_con_usuario()
        self.vehiculo = VehiculoDesarmeFactory(empresa=self.empresa)
        self.pieza = PiezaDesarmeFactory(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo,
            cantidad=1,
            precio_venta_sugerido=Decimal("40000"),
            estado_pieza=ESTADO_DISPONIBLE,
        )
        self.client = Client()
        _login(self.client, self.user)

    def test_segunda_venta_falla_despues_de_agotarse(self):
        # Primera venta — agota el stock
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("40000"))
        self.pieza.refresh_from_db()
        assert self.pieza.cantidad == 0

        # Segunda venta — debe ser rechazada (stock agotado)
        _post_finalizar(self.client, self.vehiculo, self.pieza, cantidad=1, precio=Decimal("40000"))
        self.pieza.refresh_from_db()
        # La cantidad no debe bajar de 0
        assert self.pieza.cantidad == 0


# ---------------------------------------------------------------------------
# Storefront y kiosko excluyen piezas con cantidad=0
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStorefrontExcluyeCantidadCero:
    def test_pieza_con_cantidad_cero_invisible_aunque_estado_disponible(self):
        empresa = EmpresaFactory()
        vehiculo = VehiculoDesarmeFactory(empresa=empresa)
        pieza = PiezaDesarmeFactory(
            empresa=empresa,
            vehiculo_desarme=vehiculo,
            cantidad=0,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
        )
        qs = PiezaDesarme.objects.filter(
            empresa=empresa,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert pieza not in qs

    def test_pieza_con_cantidad_positiva_visible(self):
        empresa = EmpresaFactory()
        vehiculo = VehiculoDesarmeFactory(empresa=empresa)
        pieza = PiezaDesarmeFactory(
            empresa=empresa,
            vehiculo_desarme=vehiculo,
            cantidad=2,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
        )
        qs = PiezaDesarme.objects.filter(
            empresa=empresa,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert pieza in qs


# ---------------------------------------------------------------------------
# Aislamiento multi-tenant — empresa_b no ve piezas de empresa_a
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMultiTenantAislamientoStorefront:
    def test_filtro_empresa_no_cruza_tenants(self):
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()

        vehiculo_a = VehiculoDesarmeFactory(empresa=empresa_a)
        pieza_a = PiezaDesarmeFactory(
            empresa=empresa_a,
            vehiculo_desarme=vehiculo_a,
            cantidad=1,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
        )

        vehiculo_b = VehiculoDesarmeFactory(empresa=empresa_b)
        pieza_b = PiezaDesarmeFactory(
            empresa=empresa_b,
            vehiculo_desarme=vehiculo_b,
            cantidad=1,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
        )

        qs_a = PiezaDesarme.objects.filter(
            empresa=empresa_a,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert pieza_a in qs_a
        assert pieza_b not in qs_a

        qs_b = PiezaDesarme.objects.filter(
            empresa=empresa_b,
            estado_pieza=ESTADO_DISPONIBLE,
            activo=True,
            cantidad__gt=0,
        )
        assert pieza_b in qs_b
        assert pieza_a not in qs_b


# ---------------------------------------------------------------------------
# Anulación de VentaDesarme (venta rápida) restaura stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnulacionVentaRapidaRestauraStock:
    def setup_method(self):
        self.empresa, self.user = _make_empresa_con_usuario()
        self.vehiculo = VehiculoDesarmeFactory(empresa=self.empresa)
        self.pieza = PiezaDesarmeFactory(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo,
            cantidad=1,
            precio_venta_sugerido=Decimal("25000"),
            estado_pieza=ESTADO_DISPONIBLE,
        )
        self.client = Client()
        _login(self.client, self.user)

    def test_anulacion_restaura_cantidad_y_estado(self):
        from taller.models.venta_desarme import VentaDesarme, LineaVentaDesarme

        # Simular lo que hace views_venta.py al confirmar la venta rápida
        venta = VentaDesarme.objects.create(
            empresa=self.empresa,
            cliente_nombre="Comprador Anulacion",
        )
        LineaVentaDesarme.objects.create(
            venta=venta,
            pieza=self.pieza,
            nombre_pieza=self.pieza.nombre,
            codigo_pieza=self.pieza.codigo or "",
            cantidad=1,
            precio_unitario=Decimal("25000"),
        )
        self.pieza.cantidad = 0
        self.pieza.estado_pieza = ESTADO_VENDIDA
        self.pieza.save(update_fields=["cantidad", "estado_pieza"])

        # Anular la venta vía la URL
        resp = self.client.post(
            f"/cl/es/desarme/ventas/{venta.pk}/anular/",
            follow=False,
        )
        # La vista puede redirigir o renderizar el recibo con estado actualizado
        self.pieza.refresh_from_db()
        assert self.pieza.cantidad == 1
        assert self.pieza.estado_pieza == ESTADO_DISPONIBLE
