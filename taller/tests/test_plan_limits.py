from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch
from taller.models import Empresa, TeamMember
from taller.services.plan_change_service import PlanLimitValidation
from taller.forms_subscription import PlanPagoForm
from taller.forms.team_forms import TeamMemberForm

class PlanLimitValidationTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        from taller.tests.factories import EmpresaFactory
        self.choices_mock = [('express', 'Express'), ('taller', 'Taller'), ('pro', 'Pro')]
        Empresa._meta.get_field('plan').choices = self.choices_mock

        self.empresa_express = EmpresaFactory(plan="express")
        self.empresa_taller = EmpresaFactory(plan="taller")

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_plan_express_bloquea_exceso_usuarios(self, mock_get_count):
        """El plan express (límite 1) debe rechazar usuarios adicionales si ya hay 1."""
        mock_get_count.return_value = 1
        can_add, count, limite = PlanLimitValidation.can_add_user(self.empresa_express) 
        self.assertFalse(can_add)

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_plan_taller_permite_usuarios_dentro_del_limite(self, mock_get_count):
        """El plan taller (límite 4) debe permitir agregar usuarios si tiene 2."""
        mock_get_count.return_value = 2
        can_add, count, limite = PlanLimitValidation.can_add_user(self.empresa_taller)
        self.assertTrue(can_add)

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_formulario_suscripcion_lanza_error_al_exceder_limite(self, mock_get_count): 
        """El PlanPagoForm debe fallar si la empresa no tiene cupos."""
        mock_get_count.return_value = 1
        form_data = {'plan': 'express'}
        form = PlanPagoForm(data=form_data, empresa_actual=self.empresa_express)
        form.fields['plan'].choices = self.choices_mock
        self.assertFalse(form.is_valid())
        # Agregamos [0] para evaluar el string exacto de la lista de errores
        self.assertIn("Has alcanzado el límite de usuarios permitido", form.errors['__all__'][0])

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_formulario_suscripcion_es_valido_si_hay_cupos(self, mock_get_count):
        """El PlanPagoForm debe ser válido si la empresa tiene cupos disponibles."""
        mock_get_count.return_value = 2
        form_data = {'plan': 'taller'}
        form = PlanPagoForm(data=form_data, empresa_actual=self.empresa_taller)
        form.fields['plan'].choices = self.choices_mock
        self.assertTrue(form.is_valid())

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_team_member_form_bloquea_creacion_si_no_hay_cupos(self, mock_get_count):
        """TeamMemberForm debe rechazar la creación de personal si el plan está lleno."""
        mock_get_count.return_value = 1  # Límite Express alcanzado
        form_data = {
            'email': 'nuevo@taller.cl',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'password': 'passwordSecure123',
            'rol': 'Admin'
        }
        form = TeamMemberForm(data=form_data, empresa=self.empresa_express)
        self.assertFalse(form.is_valid())
        self.assertIn("No puedes agregar más usuarios", form.errors['__all__'][0])

    @patch('taller.services.plan_change_service.PlanLimitValidation.get_count')
    def test_team_member_form_permite_creacion_si_hay_cupos(self, mock_get_count):
        """TeamMemberForm debe validar correctamente si el plan posee vacantes."""
        mock_get_count.return_value = 2  # Plan Taller tiene 2 de 4 ocupados
        form_data = {
            'email': 'nuevo@taller.cl',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'password': 'passwordSecure123',
            'rol': 'Admin'
        }
        form = TeamMemberForm(data=form_data, empresa=self.empresa_taller)
        self.assertTrue(form.is_valid())


class TestGetCountIntegracion(TestCase):
    """
    Tests de integración para PlanLimitValidation.get_count() sin mocks.

    Verifican el conteo real contra DB para detectar regressions como el
    bug de double-counting del owner (Fix 1, 2026-06-22).
    """

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.User = User
        from taller.tests.factories import EmpresaFactory
        # El signal ensure_owner_rbac crea TeamMember(rol="Owner") al guardar la Empresa.
        self.empresa = EmpresaFactory(plan="taller")
        self.owner = self.empresa.user

    def test_get_count_empresa_nueva_es_1(self):
        """
        Empresa recién creada: el signal crea el TeamMember del owner.
        get_count() debe retornar 1, no 2 — regresión exacta del bug de
        double-counting que sumaba 1 fijo + el TeamMember del owner.
        """
        self.assertTrue(
            TeamMember.objects.filter(
                empresa=self.empresa, user=self.owner, is_active=True
            ).exists(),
            "El signal ensure_owner_rbac debió crear el TeamMember del owner al guardar Empresa.",
        )
        self.assertEqual(PlanLimitValidation.get_count(self.empresa), 1)

    def test_get_count_owner_mas_dos_miembros_es_3(self):
        """
        Owner + 2 TeamMembers activos adicionales → get_count() debe retornar 3,
        no 4 (regresión: el double-count habría dado 1+3=4).
        """
        miembro_1 = self.User.objects.create_user(username="miembro1_integ", password="pass123")
        miembro_2 = self.User.objects.create_user(username="miembro2_integ", password="pass123")
        TeamMember.objects.create(user=miembro_1, empresa=self.empresa, rol="Vendedor", is_active=True)
        TeamMember.objects.create(user=miembro_2, empresa=self.empresa, rol="Admin", is_active=True)
        self.assertEqual(PlanLimitValidation.get_count(self.empresa), 3)
