"""
Ciclo completo de inventario de PiezaDesarme.

Contrato actual (borradores NO reservan stock):
  Crear línea en BORRADOR      → pieza permanece DISPONIBLE
  Eliminar línea de BORRADOR   → pieza permanece DISPONIBLE
  Emitir documento (qty→0)     → pieza pasa a VENDIDA
  Emitir documento (qty residual) → pieza permanece DISPONIBLE
  Anular EMITIDO               → pieza vuelve a DISPONIBLE
  Anular BORRADOR              → pieza permanece DISPONIBLE (nunca se movió)
  Eliminar documento BORRADOR  → pieza permanece DISPONIBLE
  Presupuesto (PRES)           → pieza permanece DISPONIBLE en cualquier caso
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
    ESTADO_VENDIDA,
    PiezaDesarme,
)
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo
from taller.services.inventory_service import InventoryService


@pytest.mark.django_db
class TestInventarioPiezaDesarme:
    """Los borradores no bloquean piezas; el stock solo se mueve al emitir."""

    def setup_method(self):
        self.user = User.objects.create_user(username="test_inv_kiosko", password="x")
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Inv", pais="CL", user=self.user, plan="paid"
        )
        self.cliente = Cliente.objects.create(
            nombre="Cliente", apellido="Inv", empresa=self.empresa
        )
        self.vehiculo_cliente = Vehiculo.objects.create(
            empresa=self.empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente=self.cliente,
            patente="INV01",
            anio=2020,
        )
        self.vehiculo_desarme = VehiculoDesarme.objects.create(
            empresa=self.empresa,
            patente="INVD",
            anio=2018,
        )

    def _pieza(self, cantidad=1, nombre="Pieza Test"):
        return PiezaDesarme.objects.create(
            empresa=self.empresa,
            vehiculo_desarme=self.vehiculo_desarme,
            codigo=f"P-{nombre[:4]}",
            nombre=nombre,
            cantidad=cantidad,
        )

    def _doc(self, tipo="OT", estado="BORRADOR"):
        return Documento.objects.create(
            empresa=self.empresa,
            tipo=tipo,
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

    # ── Borrador: sin efecto sobre stock ─────────────────────────────────────

    def test_crear_linea_en_borrador_no_cambia_estado(self):
        pieza = self._pieza()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE

        doc = self._doc()
        self._linea(doc, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Borrador no debe cambiar estado de pieza, obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 1  # sin cambio en cantidad

    def test_eliminar_linea_de_borrador_no_cambia_estado(self):
        pieza = self._pieza()
        doc = self._doc()
        linea = self._linea(doc, pieza)

        linea.delete()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE
        assert pieza.cantidad == 1

    def test_eliminar_documento_borrador_no_cambia_estado(self):
        pieza = self._pieza()
        doc = self._doc()
        self._linea(doc, pieza)

        doc.delete()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE
        assert pieza.cantidad == 1

    def test_anular_borrador_no_cambia_estado(self):
        pieza = self._pieza()
        doc = self._doc()
        self._linea(doc, pieza)

        doc.estado = "ANULADO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE
        assert pieza.cantidad == 1

    # ── Emisión: aquí ocurre el movimiento de stock ───────────────────────────

    def test_emitir_documento_agota_pieza(self):
        pieza = self._pieza(cantidad=1)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=1)

        doc.estado = "EMITIDO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_VENDIDA, (
            f"Esperaba VENDIDA después de emitir (stock=0), obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 0

    def test_emitir_documento_deja_disponible_con_stock_residual(self):
        pieza = self._pieza(cantidad=3)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=1)  # vende 1 de 3

        doc.estado = "EMITIDO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE (quedan 2 unidades), obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 2

    # ── Anulación de emitido: repone stock ────────────────────────────────────

    def test_anular_emitido_repone_stock(self):
        pieza = self._pieza(cantidad=1)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=1)

        doc.estado = "EMITIDO"
        doc.save()
        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_VENDIDA

        doc.estado = "ANULADO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Esperaba DISPONIBLE tras anular emitido, obtuve {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 1

    # ── Presupuestos: nunca mueven stock ──────────────────────────────────────

    def test_presupuesto_no_afecta_pieza(self):
        pieza = self._pieza()
        pres = self._doc(tipo="PRES")
        self._linea(pres, pieza)

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE
        assert pieza.cantidad == 1

    # ── Concurrencia: validación de stock en emisión ──────────────────────────

    def test_emitir_con_stock_suficiente_descuenta_correctamente(self):
        """Emitir con cantidad >= requerida → stock baja, VENDIDA si llega a 0."""
        pieza = self._pieza(cantidad=3)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=2)

        errores = InventoryService.validar_stock_disponible(doc)
        assert errores == [], f"No debe haber errores de stock: {errores}"

        doc.estado = "EMITIDO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.cantidad == 1
        assert pieza.estado_pieza == ESTADO_DISPONIBLE

    def test_emitir_falla_cuando_stock_fue_agotado_concurrentemente(self):
        """
        Simula que otra transacción agotó el stock antes de que este documento
        se emita. El documento debe permanecer como BORRADOR y la validación
        debe devolver errores.

        Nota: en SQLite este test valida la lógica de negocio, NO el lock real.
        select_for_update() solo es efectivo contra Postgres en producción.
        """
        pieza = self._pieza(cantidad=1)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=1)

        # Simular: otra transacción concurrente agotó el stock y confirmó
        PiezaDesarme.objects.filter(pk=pieza.pk).update(
            cantidad=0, estado_pieza=ESTADO_VENDIDA
        )

        errores = InventoryService.validar_stock_disponible(doc)

        assert len(errores) > 0, "Debe haber error de stock insuficiente"
        doc.refresh_from_db()
        assert doc.estado == "BORRADOR", "El documento debe permanecer como BORRADOR"

    def test_anular_emitido_vendida_restaura_disponible(self):
        """
        Anular un emitido que agotó la pieza (cantidad=0, VENDIDA) repone la
        cantidad y revierte a DISPONIBLE.

        TODO: cuando exista DatosDTE, condicionar esta reversión al estado del DTE
        (no revertir automáticamente si ya se emitió un documento fiscal real).
        """
        pieza = self._pieza(cantidad=1)
        doc = self._doc()
        self._linea(doc, pieza, cantidad=1)

        doc.estado = "EMITIDO"
        doc.save()
        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_VENDIDA
        assert pieza.cantidad == 0

        doc.estado = "ANULADO"
        doc.save()

        pieza.refresh_from_db()
        assert pieza.estado_pieza == ESTADO_DISPONIBLE, (
            f"Anular debe restaurar DISPONIBLE, obtuvo {pieza.estado_pieza}"
        )
        assert pieza.cantidad == 1
