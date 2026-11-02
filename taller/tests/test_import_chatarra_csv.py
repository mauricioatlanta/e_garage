"""
Tests para el comando import_chatarra_csv (Fase 1 — Atlanta Reciclajes).

No importa el CSV recuperado real (no está en el repo); valida el
comportamiento del importador con CSVs sintéticos: creación, idempotencia,
dry-run, filas inválidas y resolución de --empresa por id o username.
"""
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from taller.models.reciclaje import CategoriaChatarra, ProductoChatarra
from taller.tests.factories import EmpresaFactory


def _write_csv(tmp_path, rows, header="codigo,nombre,categoria,unidad_medida,precio_compra,precio_venta,cantidad_stock,proveedor"):
    path = tmp_path / "chatarra.csv"
    lines = [header] + rows
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


@pytest.mark.django_db
class TestImportChatarraCsv:
    def test_crea_productos_desde_csv(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, [
            "CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A",
            "AL-01,Placas de aluminio,Aluminio,KG,500,800,10,Proveedor B",
        ])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id))

        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 2
        cobre = ProductoChatarra.objects.get(empresa=empresa, codigo="CU-01")
        assert cobre.nombre == "Cable de cobre"
        assert cobre.precio_venta == Decimal("1500")
        assert cobre.cantidad_stock == Decimal("25.5")
        assert cobre.categoria.nombre == "Cobre"
        assert cobre.origen_importacion == csv_path

    def test_es_idempotente_update_or_create(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, ["CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A"])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id))
        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id))

        assert ProductoChatarra.objects.filter(empresa=empresa, codigo="CU-01").count() == 1

    def test_dry_run_no_escribe(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, ["CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A"])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id), "--dry-run")

        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 0
        assert CategoriaChatarra.objects.filter(empresa=empresa).count() == 0

    def test_fila_sin_codigo_se_salta_sin_abortar_el_resto(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, [
            ",Sin código,Cobre,KG,1000,1500,25.5,Proveedor A",
            "AL-01,Placas de aluminio,Aluminio,KG,500,800,10,Proveedor B",
        ])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id))

        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 1
        assert ProductoChatarra.objects.get(empresa=empresa).codigo == "AL-01"

    def test_decimal_invalido_se_salta_la_fila(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, [
            "CU-01,Cable de cobre,Cobre,KG,no-es-numero,1500,25.5,Proveedor A",
        ])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa.id))

        assert ProductoChatarra.objects.filter(empresa=empresa).count() == 0

    def test_columnas_obligatorias_faltantes_lanza_command_error(self, tmp_path):
        empresa = EmpresaFactory()
        path = tmp_path / "malo.csv"
        path.write_text("nombre,precio_venta\nCable,1500\n", encoding="utf-8")

        with pytest.raises(CommandError):
            call_command("import_chatarra_csv", str(path), "--empresa", str(empresa.id))

    def test_empresa_resuelta_por_username(self, tmp_path):
        empresa = EmpresaFactory()
        csv_path = _write_csv(tmp_path, ["CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A"])

        call_command("import_chatarra_csv", csv_path, "--empresa", empresa.user.username)

        assert ProductoChatarra.objects.filter(empresa=empresa, codigo="CU-01").exists()

    def test_empresa_inexistente_lanza_command_error(self, tmp_path):
        csv_path = _write_csv(tmp_path, ["CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A"])

        with pytest.raises(CommandError):
            call_command("import_chatarra_csv", csv_path, "--empresa", "999999")

    def test_no_mezcla_stock_entre_empresas(self, tmp_path):
        empresa_a = EmpresaFactory()
        empresa_b = EmpresaFactory()
        csv_path = _write_csv(tmp_path, ["CU-01,Cable de cobre,Cobre,KG,1000,1500,25.5,Proveedor A"])

        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa_a.id))
        call_command("import_chatarra_csv", csv_path, "--empresa", str(empresa_b.id))

        assert ProductoChatarra.objects.filter(codigo="CU-01").count() == 2
        assert ProductoChatarra.objects.get(empresa=empresa_a, codigo="CU-01").empresa_id == empresa_a.id
        assert ProductoChatarra.objects.get(empresa=empresa_b, codigo="CU-01").empresa_id == empresa_b.id
