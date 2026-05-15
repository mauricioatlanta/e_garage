"""
Tests para módulo de WhatsApp
"""
from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from taller.models import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.comprobante_pago import ComprobantePago
from taller.whatsapp.providers import DummyWhatsAppProvider, MetaWhatsAppProvider, get_whatsapp_provider
from taller.whatsapp.helpers import normalize_phone, build_wa_link, build_document_wa_message, validate_phone_by_country
from taller.whatsapp.admin_notifications import notify_admin_new_subscription
from taller.whatsapp.models import WhatsAppAdminNotificationLog
from taller.models.comprobante_pago import ComprobantePago

User = get_user_model()


class WhatsAppProviderTests(TestCase):
    """Tests para providers de WhatsApp"""
    
    def test_dummy_provider_sends_successfully(self):
        """Dummy provider debe retornar success=True"""
        provider = DummyWhatsAppProvider()
        result = provider.send("+56912345678", "Test message")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "dummy")
        self.assertIn("message_id", result)
    
    def test_meta_provider_without_credentials(self):
        """Meta provider sin credenciales debe retornar error"""
        provider = MetaWhatsAppProvider()
        result = provider.send("+56912345678", "Test message")
        
        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "meta")
        self.assertIn("error", result)
    
    @override_settings(
        WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=False,
        WHATSAPP_ADMIN_PROVIDER="dummy"
    )
    def test_get_provider_disabled_returns_dummy(self):
        """Si notificaciones están deshabilitadas, debe retornar dummy"""
        provider = get_whatsapp_provider()
        self.assertIsInstance(provider, DummyWhatsAppProvider)
    
    @override_settings(
        WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=True,
        WHATSAPP_ADMIN_PROVIDER="dummy"
    )
    def test_get_provider_dummy_when_enabled(self):
        """Si está habilitado con provider dummy, debe retornar DummyWhatsAppProvider"""
        provider = get_whatsapp_provider()
        self.assertIsInstance(provider, DummyWhatsAppProvider)


class WhatsAppHelpersTests(TestCase):
    """Tests para helpers de WhatsApp"""
    
    def test_normalize_phone_chile_format(self):
        """Normalizar teléfono chileno sin código de país"""
        result = normalize_phone("912345678", "56")
        self.assertEqual(result, "56912345678")
    
    def test_normalize_phone_with_plus(self):
        """Normalizar teléfono con +"""
        result = normalize_phone("+56912345678", "56")
        self.assertEqual(result, "56912345678")
    
    def test_normalize_phone_with_spaces(self):
        """Normalizar teléfono con espacios"""
        result = normalize_phone("+56 9 1234 5678", "56")
        self.assertEqual(result, "56912345678")
    
    def test_build_wa_link_valid(self):
        """Construir link wa.me válido"""
        link = build_wa_link("+56912345678", "Hola mundo")
        self.assertIsNotNone(link)
        self.assertIn("wa.me/56912345678", link)
        self.assertIn("text=", link)
    
    def test_build_wa_link_no_phone(self):
        """Construir link sin teléfono debe retornar None"""
        link = build_wa_link("", "Hola mundo")
        self.assertIsNone(link)
    
    def test_build_document_wa_message_spanish(self):
        """Construir mensaje de documento en español"""
        message = build_document_wa_message(
            documento=None,
            cliente_nombre="Juan Pérez",
            tipo_doc="Presupuesto",
            numero_doc="123",
            total=100000.0,
            empresa_nombre="Taller Test",
            url_documento="https://example.com/doc/123",
            language="es",
        )
        
        self.assertIn("Juan Pérez", message)
        self.assertIn("Presupuesto", message)
        self.assertIn("123", message)
        self.assertIn("Taller Test", message)
    
    def test_build_document_wa_message_english(self):
        """Construir mensaje de documento en inglés"""
        message = build_document_wa_message(
            documento=None,
            cliente_nombre="John Doe",
            tipo_doc="Quote",
            numero_doc="123",
            total=1000.0,
            empresa_nombre="Test Shop",
            url_documento="https://example.com/doc/123",
            language="en",
        )
        
        self.assertIn("John Doe", message)
        self.assertIn("Quote", message)
        self.assertIn("Test Shop", message)


class WhatsAppAdminNotificationsTests(TestCase):
    """Tests para notificaciones admin"""
    
    def setUp(self):
        """Crear datos de prueba"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="test123"
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Test",
            pais="CL",
            user=self.user,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date(),
        )
    
    @override_settings(
        WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=True,
        WHATSAPP_ADMIN_PROVIDER="dummy",
        WHATSAPP_ADMIN_NUMBER="+56912345678"
    )
    def test_notify_admin_new_subscription(self):
        """Notificar admin sobre nueva suscripción"""
        result = notify_admin_new_subscription(
            empresa=self.empresa,
            plan="basico",
            monto=10000.0,
            es_nueva_suscripcion=True,
        )
        
        # Debe retornar True (dummy provider siempre tiene éxito)
        self.assertTrue(result)
    
    @override_settings(
        WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=False,
        WHATSAPP_ADMIN_PROVIDER="dummy",
        WHATSAPP_ADMIN_NUMBER="+56912345678"
    )
    def test_notify_admin_disabled(self):
        """Si notificaciones están deshabilitadas, debe retornar False"""
        result = notify_admin_new_subscription(
            empresa=self.empresa,
            plan="basico",
            monto=10000.0,
            es_nueva_suscripcion=True,
        )
        
        self.assertFalse(result)
    
    @override_settings(
        WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=True,
        WHATSAPP_ADMIN_PROVIDER="dummy",
        WHATSAPP_ADMIN_NUMBER=None  # Sin número configurado
    )
    def test_notify_admin_no_number(self):
        """Si no hay número configurado, debe retornar False"""
        result = notify_admin_new_subscription(
            empresa=self.empresa,
            plan="basico",
            monto=10000.0,
            es_nueva_suscripcion=True,
        )
        
        self.assertFalse(result)
