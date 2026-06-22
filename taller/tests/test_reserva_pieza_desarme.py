"""
Ciclo completo de reserva de PiezaDesarme para el kiosko.

Verifica que estado_pieza es fuente de verdad confiable:
  DISPONIBLE → RESERVADA al crear línea en BORRADOR
  RESERVADA  → DISPONIBLE al eliminar esa línea
  RESERVADA  → VENDIDA    al emitir el documento (pieza agotada)
  RESERVADA  → DISPONIBLE al emitir el documento (pieza con stock residual)
  RESERVADA  → DISPONIBLE al anular el documento en BORRADOR
  Dos BORADORs: pieza no se libera hasta que el último BORRADOR la suelte
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import ORIGEN_DESARME, LineaRepuesto
from taller.models.pieza_desarme import (
    ESTADO_DISPONIBLE,
    ESTADO_RESERVADA,
    ESTADO_VENDIDA,
    PiezaDesarme,
)
from taller.models.vehiculos import Vehiculo


@pytest.mark.django_db
class TestReservaPiezaDesarme:
    """estado_pieza es fuente de verdad: el kiosko solo confía en DISPONIBLE."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="test_reserva_kiosko", password="x"
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Reserva", pais="CL", user=self.user, plan="paid"
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente", apellido="Reserva", empresa=self.empresa
        )
        self.vehiculo_cliente = Vehiculo.objects.create(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=self.cliente,
            patente="RES01",
            anio=2020,
        )
        self.vehiculo_desarme = Vehiculo.objects.create(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_DESARME,
            patente="RESD",
            anio=2018,
        )

    def _pieza(self, cantidad=1, nombre="Pieza Test"):
        return PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo=self.vehiculo_desarme,
            codigo=f"P-{nombre[:4]}",
            nombre=nombre,
            cantidad=cantidad,
        )

    def _doc(self, estado="BORRADOR"):
        return Documento.objects.create(
            empresa=self.empresa,
            tipo="OT",
            estado=estado,
            cliente=self.cliente,
            vehiculo=self.vehiculo_cliente,
        )

    def _linea(self, doc, pieza, cantidad=1):
        return LineaRepuesto.objects.create(
            documento=doc,
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme=pieza,
            codigo=pieza.codigo,
            nombre=pieza.nombre,
            cantidad=cantidad,
            precio_unitario=Decimal("100"),
        )

    # ── Paso 1: crear línea en BORRADOR → pieza pasa a RESERVADA ──────────────
    def test_crear_linea_reserva_pieza(self):
        pieza = self._pieza()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE

        doc = self._doc("BORRADOR")
        self._linea(doc, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA, (
            f"Esperaba RESERVADA después de crear línea, obtuve {pieza.estado_pieza}"
        )

    # ── Paso 2: eliminar esa línea → pieza vuelve a DISPONIBLE ───────────────
    def test_eliminar_linea_libera_pieza(self):
        pieza = self._pieza()
        doc = self._doc("BORRADOR")
        linea = self._linea(doc, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        linea.delete()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE después de eliminar línea, obtuve {pieza.estado_pieza}"
        )

    # ── Paso 3: emitir documento → pieza pasa a VENDIDA (stock agotado) ──────
    def test_emitir_documento_vende_pieza_agotada(self):
        pieza = self._pieza(cantidad=1)
        doc = self._doc("BORRADOR")
        self._linea(doc, pieza, cantidad=1)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        doc.estado = "EMITIDO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_VENDIDA, (
            f"Esperaba VENDIDA después de emitir (stock=0), obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 0

    # ── Paso 3b: emitir documento → pieza vuelve a DISPONIBLE (stock residual) ─
    def test_emitir_documento_libera_pieza_con_stock_residual(self):
        pieza = self._pieza(cantidad=3)
        doc = self._doc("BORRADOR")
        self._linea(doc, pieza, cantidad=1)  # usa 1 de 3

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        doc.estado = "EMITIDO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE (quedan 2 unidades), obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 2

    # ── Paso 4: anular documento en BORRADOR → pieza vuelve a DISPONIBLE ─────
    def test_anular_borrador_libera_pieza(self):
        pieza = self._pieza()
        doc = self._doc("BORRADOR")
        self._linea(doc, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        doc.estado = "ANULADO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE tras anular BORRADOR, obtuve {pieza.estado_pieza}"
        )

    # ── Paso 5: eliminar documento BORRADOR → CASCADE libera pieza ───────────
    def test_eliminar_documento_borrador_libera_pieza(self):
        pieza = self._pieza()
        doc = self._doc("BORRADOR")
        self._linea(doc, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        doc.delete()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE tras eliminar documento, obtuve {pieza.estado_pieza}"
        )

    # ── Dos BORADORs: pieza no se libera hasta que el último la suelte ────────
    def test_dos_borradores_pieza_no_se_libera_hasta_el_ultimo(self):
        pieza = self._pieza(cantidad=2)
        doc1 = self._doc("BORRADOR")
        doc2 = self._doc("BORRADOR")
        self._linea(doc1, pieza, cantidad=1)
        self._linea(doc2, pieza, cantidad=1)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA

        # Eliminar línea del primer borrador → sigue reservada (doc2 la tiene)
        doc1.lineas_repuesto.filter(pieza_desarme=pieza).delete()
        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_RESERVADA, (
            "Pieza no debería liberarse mientras doc2 la tenga reservada"
        )

        # Eliminar línea del segundo borrador → ahora sí se libera
        doc2.lineas_repuesto.filter(pieza_desarme=pieza).delete()
        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE tras soltar el último borrador, obtuve {pieza.estado_pieza}"
        )

    # ── Presupuestos NO reservan piezas ──────────────────────────────────────
    def test_presupuesto_no_reserva_pieza(self):
        pieza = self._pieza()
        pres = Documento.objects.create(
            empresa=self.empresa,
            tipo="PRES",
            estado="BORRADOR",
            cliente=self.cliente,
            vehiculo=self.vehiculo_cliente,
        )
        self._linea(pres, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            "Los presupuestos no deben reservar piezas"
        )
