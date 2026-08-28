"""
Tests para el management command import_cataliticos_pythonanywhere —
recuperación única de los datos reales de Atlanta Reciclajes desde la base
SQLite del proyecto original (PythonAnywhere).

Usa una base SQLite temporal con el mismo esquema mínimo (no el archivo
real recuperado, que vive fuera del repo) para validar la lógica de
mapeo/idempotencia sin depender de datos sensibles de un cliente real.
"""
import sqlite3
from pathlib import Path

import pytest
from django.core.management import call_command

from taller.models.clientes import Cliente
from taller.models.reciclaje import (
    Catalitico,
    CompraReciclaje,
    DetalleCompraCatalitico,
    ProductoChatarra,
)
from taller.tests.factories import EmpresaFactory


def _crear_sqlite_fixture(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE cataliticos_catalitico (
            id INTEGER PRIMARY KEY, codigo TEXT, descripcion TEXT,
            valor_compra REAL, valor_venta REAL, cantidad INTEGER,
            vendido INTEGER, imagen_principal TEXT
        );
        CREATE TABLE cataliticos_productochatarra (
            id INTEGER PRIMARY KEY, nombre TEXT, codigo TEXT,
            precio_kg INTEGER, categoria TEXT, cantidad REAL
        );
        CREATE TABLE cataliticos_cliente (
            id INTEGER PRIMARY KEY, nombre TEXT, apellido TEXT, rut TEXT,
            telefono TEXT, correo TEXT, direccion TEXT
        );
        CREATE TABLE cataliticos_compracatalitico (
            id INTEGER PRIMARY KEY, cliente_id INTEGER, cliente_nombre TEXT,
            cliente_apellido TEXT, cliente_telefono TEXT, fecha TEXT
        );
        CREATE TABLE cataliticos_detallecatalitico (
            id INTEGER PRIMARY KEY, compra_id INTEGER, catalitico_id INTEGER,
            cantidad INTEGER, precio_unitario REAL
        );

        INSERT INTO cataliticos_catalitico VALUES
            (1, 'K181', 'Peugeot', 35662, 74400, 1, 0, 'cataliticos/K181.jpeg'),
            (2, 'K357', 'Peugeot' || char(10) || 'Citroen', 49035.25, 129300, 0, 1, NULL);

        INSERT INTO cataliticos_productochatarra VALUES
            (1, 'Placa madre A', 'PMC0001-A', 2430, '', 0),
            (2, 'Fuentes 300', 'SCR0004', 1000, 'fuente', 0);

        INSERT INTO cataliticos_cliente VALUES
            (1, 'Ruben', 'Jara', '77.323.929-0', '+56954156132', 'ruben@example.com', 'Calle 1'),
            (2, 'Sin Datos', NULL, NULL, NULL, NULL, NULL);

        INSERT INTO cataliticos_compracatalitico VALUES
            (10, 1, 'Ruben', 'Jara', '+56954156132', '2026-01-23 00:46:36'),
            (11, 2, 'Sin Datos', NULL, NULL, '2026-01-27 01:39:41');

        INSERT INTO cataliticos_detallecatalitico VALUES
            (100, 10, 1, 1, 35000),
            (101, 11, 2, 1, 70000);
        """
    )
    con.commit()
    con.close()


@pytest.fixture
def sqlite_fixture(tmp_path) -> Path:
    path = tmp_path / "db.sqlite3"
    _crear_sqlite_fixture(path)
    return path


@pytest.mark.django_db
class TestImportCataliticosPythonanywhere:
    def test_importa_catalogo_clientes_y_compras(self, sqlite_fixture):
        empresa = EmpresaFactory()

        call_command(
            "import_cataliticos_pythonanywhere",
            str(sqlite_fixture),
            "--empresa", str(empresa.pk),
        )

        assert Catalitico.objects.filter(empresa=empresa).count() == 2
        k181 = Catalitico.objects.get(empresa=empresa, codigo="K181")
        assert k181.marca_vehiculo == "Peugeot"
        assert k181.precio_compra == 35662
        assert k181.precio_venta == 74400
        assert k181.cantidad_stock == 1
        assert k181.estado == Catalitico.ESTADO_DISPONIBLE

        k357 = Catalitico.objects.get(empresa=empresa, codigo="K357")
        assert k357.marca_vehiculo == "Peugeot"  # solo la primera marca de la línea
        assert k357.estado == Catalitico.ESTADO_VENDIDO

        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 2
        placa = ProductoChatarra.objects.get(empresa=empresa, codigo="PMC0001-A")
        assert placa.nombre == "Placa madre A"
        assert placa.precio_compra == 2430
        assert placa.categoria is None
        fuentes = ProductoChatarra.objects.get(empresa=empresa, codigo="SCR0004")
        assert fuentes.categoria.nombre == "fuente"

        assert Cliente.objects.filter(empresa=empresa).count() == 2
        ruben = Cliente.objects.get(empresa=empresa, tax_id="77.323.929-0")
        assert ruben.nombre == "Ruben"
        assert ruben.telefono == "+56954156132"

        assert CompraReciclaje.objects.filter(empresa=empresa).count() == 2
        compra_ruben = CompraReciclaje.objects.get(empresa=empresa, cliente=ruben)
        assert "[pythonanywhere:compra:10]" in compra_ruben.notas
        assert compra_ruben.created_at.strftime("%Y-%m-%d") == "2026-01-23"

        assert DetalleCompraCatalitico.objects.filter(
            compra=compra_ruben, catalitico=k181
        ).count() == 1

    def test_es_idempotente_no_duplica_al_correr_dos_veces(self, sqlite_fixture):
        empresa = EmpresaFactory()

        call_command(
            "import_cataliticos_pythonanywhere",
            str(sqlite_fixture), "--empresa", str(empresa.pk),
        )
        call_command(
            "import_cataliticos_pythonanywhere",
            str(sqlite_fixture), "--empresa", str(empresa.pk),
        )

        assert Catalitico.objects.filter(empresa=empresa).count() == 2
        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 2
        assert Cliente.objects.filter(empresa=empresa).count() == 2
        assert CompraReciclaje.objects.filter(empresa=empresa).count() == 2
        assert DetalleCompraCatalitico.objects.count() == 2

    def test_dry_run_no_escribe_nada(self, sqlite_fixture):
        empresa = EmpresaFactory()

        call_command(
            "import_cataliticos_pythonanywhere",
            str(sqlite_fixture), "--empresa", str(empresa.pk), "--dry-run",
        )

        assert Catalitico.objects.filter(empresa=empresa).count() == 0
        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 0
        assert Cliente.objects.filter(empresa=empresa).count() == 0
        assert CompraReciclaje.objects.filter(empresa=empresa).count() == 0

    def test_aislamiento_multi_tenant(self, sqlite_fixture):
        """Los datos importados nunca deben mezclarse con otra empresa."""
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()

        call_command(
            "import_cataliticos_pythonanywhere",
            str(sqlite_fixture), "--empresa", str(empresa_a.pk),
        )

        assert Catalitico.objects.filter(empresa=empresa_a).count() == 2
        assert Catalitico.objects.filter(empresa=empresa_b).count() == 0
