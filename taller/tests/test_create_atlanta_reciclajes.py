"""
Tests para el management command create_atlanta_reciclajes (Fase 1).
"""
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa


@pytest.mark.django_db
class TestCreateAtlantaReciclajes:
    def test_crea_tenant_con_rubro_recycling(self):
        call_command("create_atlanta_reciclajes", "--username", "atlanta_test")

        user = User.objects.get(username="atlanta_test")
        empresa = Empresa.objects.get(user=user)
        config = ConfiguracionEmpresa.objects.get(empresa=empresa)

        assert empresa.nombre_taller == "Atlanta Reciclajes"
        assert config.rubro_principal == "RECYCLING"
        assert config.recycling_type_principal == "CATALYTIC_RECYCLING"
        assert config.get_effective_recycling_types() == [
            "CATALYTIC_RECYCLING",
            "ELECTRONIC_SCRAP",
        ]

    def test_es_idempotente_no_duplica_al_correr_dos_veces(self):
        call_command("create_atlanta_reciclajes", "--username", "atlanta_test")
        call_command("create_atlanta_reciclajes", "--username", "atlanta_test")

        assert User.objects.filter(username="atlanta_test").count() == 1
        assert Empresa.objects.filter(user__username="atlanta_test").count() == 1

    def test_reset_elimina_y_recrea(self):
        call_command("create_atlanta_reciclajes", "--username", "atlanta_test")
        empresa_id_original = Empresa.objects.get(user__username="atlanta_test").id

        call_command("create_atlanta_reciclajes", "--username", "atlanta_test", "--reset")

        empresa = Empresa.objects.get(user__username="atlanta_test")
        assert empresa.id != empresa_id_original

    def test_nombre_personalizado(self):
        call_command(
            "create_atlanta_reciclajes",
            "--username", "atlanta_test",
            "--nombre", "Atlanta Reciclajes SPA",
        )
        empresa = Empresa.objects.get(user__username="atlanta_test")
        assert empresa.nombre_taller == "Atlanta Reciclajes SPA"
