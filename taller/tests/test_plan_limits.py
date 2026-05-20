from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch
from taller.models import Empresa
from taller.services.plan_change_service import PlanLimitValidation
from taller.forms_subscription import PlanPagoForm
from taller.forms.team_forms import TeamMemberForm

class PlanLimitValidationTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        self.owner_1 = User.objects.create_user(username="owner_express_dummy", password="password123")
        self.owner_2 = User.objects.create_user(username="owner_taller_dummy", password="password123")
        
        self.choices_mock = [('express', 'Express'), ('taller', 'Taller'), ('pro', 'Pro')]
        Empresa._meta.get_field('plan').choices = self.choices_mock

        self.empresa_express = Empresa.objects.create(plan="express", user=self.owner_1)
        self.empresa_taller = Empresa.objects.create(plan="taller", user=self.owner_2)

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
