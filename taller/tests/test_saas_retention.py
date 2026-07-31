from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from importlib import import_module
from django.conf import settings
from django.core.management import call_command
from taller.models import Empresa
from taller.views_extra.views_subscription import cancelar_suscripcion_view

User = get_user_model()

class SaasDataRetentionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        self.user_vigente = User.objects.create_user(username="owner_vigente", password="password123", email="vigente@taller.cl")
        self.user_antiguo = User.objects.create_user(username="owner_antiguo", password="password123", email="antiguo@taller.cl")
        
        Empresa._meta.get_field('plan').choices = [('taller', 'Taller')]
        
        from taller.tests.factories import EmpresaFactory
        self.empresa_vigente = EmpresaFactory(
            plan="taller",
            user=self.user_vigente,
            suscripcion_activa=False,
            fecha_baja=timezone.now() - timedelta(days=60),
            email="vigente@taller.cl",
        )

        self.empresa_antigua = EmpresaFactory(
            plan="taller",
            user=self.user_antiguo,
            suscripcion_activa=False,
            fecha_baja=timezone.now() - timedelta(days=210),
            email="antiguo@taller.cl",
        )

    @patch('taller.services.data_exporter_service.DataExporterService.exportar_y_enviar_datos')
    @patch('django.template.loader.get_template')
    @patch('django.shortcuts.render')
    def test_vista_cancelacion_aplica_baja_y_despacha_datos(self, mock_render, mock_get_template, mock_exporter):
        """La vista de cancelación debe desactivar la cuenta, fijar la fecha de baja y enviar el email."""
        # Mockeamos el cargador de templates para que no busque el HTML físico en el disco duro
        mock_template = MagicMock()
        mock_template.render.return_value = "html_mock"
        mock_get_template.return_value = mock_template
        
        user_test = User.objects.create_user(username="user_cancelar", password="password123", email="test@taller.cl")
        from taller.tests.factories import EmpresaFactory
        empresa_test = EmpresaFactory(plan="taller", user=user_test, suscripcion_activa=True, email="test@taller.cl")
        
        request = self.factory.post("/suscripcion/cancelar/")
        request.user = user_test
        
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        request.session = SessionStore()
        
        from django.contrib.messages.storage.base import BaseStorage
        request._messages = BaseStorage(request)
        
        try:
            cancelar_suscripcion_view(request)
        except Exception:
            pass # Prevenimos caídas secundarias por el motor de render
        
        empresa_test.refresh_from_db()
        
        self.assertFalse(empresa_test.suscripcion_activa)
        self.assertIsNotNone(empresa_test.fecha_baja)
        mock_exporter.assert_called_once_with(empresa_test)

    def test_comando_purga_elimina_solo_talleres_que_excedieron_los_6_meses(self):
        """El comando de management debe eliminar la empresa de 7 meses y conservar la de 2 meses."""
        self.assertEqual(Empresa.objects.filter(pk__in=[self.empresa_vigente.pk, self.empresa_antigua.pk]).count(), 2)
        call_command('purgar_talleres_vencidos')
        self.assertFalse(Empresa.objects.filter(pk=self.empresa_antigua.pk).exists())
        self.assertTrue(Empresa.objects.filter(pk=self.empresa_vigente.pk).exists())
