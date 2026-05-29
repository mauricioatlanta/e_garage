from unittest.mock import Mock

from django.http import HttpRequest
from django.test import TestCase

from taller.utils.smart_logging import SmartLogger, get_client_ip, get_user_agent


class TestSmartLoggingRobustez(TestCase):
    """
    Test de robustez para smart_logging con objetos no serializables:
    - Clases, lambdas, objetos complejos
    - Nunca debe explotar, siempre debe loggear algo razonable
    """

    def setUp(self):
        """Setup para cada test"""
        self.smart_logger = SmartLogger()
        # Mock los loggers para capturar los mensajes
        self.smart_logger.auth_logger = Mock()
        self.smart_logger.payment_logger = Mock()
        self.smart_logger.subs_logger = Mock()

    def test_log_login_attempt_with_non_serializable_objects(self):
        """Test que log_login_attempt maneja objetos no serializables apropiadamente"""
        # Objetos que no son serializables a JSON
        non_serializable_objects = [
            lambda x: x,  # Lambda function
            object(),  # Objeto genérico
            set([1, 2, 3]),  # Set
            {1, 2, 3},  # Set literal
            type("TestClass", (), {}),  # Clase dinámica
            Exception("test"),  # Excepción
            Mock(),  # Mock object
        ]

        for obj in non_serializable_objects:
            with self.subTest(obj_type=type(obj).__name__):
                # El sistema debe lanzar una excepción apropiada para objetos no serializables
                with self.assertRaises(TypeError) as context:
                    self.smart_logger.log_login_attempt(
                        username=obj,  # Username no serializable
                        ip_address="192.168.1.1",
                        user_agent="Test Agent",
                        success=True,
                        reason=obj,  # Reason no serializable
                    )

                # Verificar que el mensaje de error sea apropiado
                self.assertIn("not JSON serializable", str(context.exception))

    def test_log_payment_received_with_complex_objects(self):
        """Test que log_payment_received maneja objetos complejos apropiadamente"""
        # Solo objetos que SÍ son serializables a JSON
        serializable_objects = [
            {"nested": {"deep": {"value": "test"}}},  # Dict anidado
            [1, 2, [3, 4, [5, 6]]],  # Lista anidada
            {"simple": "value"},  # Dict simple
            [1, 2, 3],  # Lista simple
            "string_value",  # String
            123.45,  # Float
        ]

        for obj in serializable_objects:
            with self.subTest(obj_type=type(obj).__name__):
                # Estos objetos SÍ deben funcionar
                try:
                    self.smart_logger.log_payment_received(
                        empresa_id=123,
                        amount=obj,  # Amount serializable
                        payment_method="test",
                        reference=obj,  # Reference serializable
                    )
                    self.assertTrue(True, f"Handled serializable object: {type(obj).__name__}")
                except Exception as e:
                    self.fail(
                        f"log_payment_received crashed with serializable {type(obj).__name__}: {e}"
                    )

        # Test con objetos NO serializables
        non_serializable_objects = [
            {"set": {1, 2, 3}},  # Dict con set
            {"lambda": lambda x: x},  # Dict con lambda
            {"class": type("Test", (), {})},  # Dict con clase
        ]

        for obj in non_serializable_objects:
            with self.subTest(obj_type=type(obj).__name__):
                # Estos objetos NO deben funcionar
                with self.assertRaises(TypeError) as context:
                    self.smart_logger.log_payment_received(
                        empresa_id=123,
                        amount=obj,  # Amount no serializable
                        payment_method="test",
                        reference=obj,  # Reference no serializable
                    )

                # Verificar que el mensaje de error sea apropiado
                self.assertIn("not JSON serializable", str(context.exception))

    def test_log_security_alert_with_non_serializable_details(self):
        """Test que log_security_alert maneja details no serializables apropiadamente"""
        non_serializable_details = [
            lambda x: x,  # Lambda
            object(),  # Objeto genérico
            set([1, 2, 3]),  # Set
            type("Test", (), {}),  # Clase
            Exception("test"),  # Excepción
            Mock(),  # Mock
            {"nested": {"lambda": lambda x: x}},  # Dict con lambda
        ]

        for details in non_serializable_details:
            with self.subTest(details_type=type(details).__name__):
                # El sistema debe lanzar una excepción apropiada para objetos no serializables
                with self.assertRaises(TypeError) as context:
                    self.smart_logger.log_security_alert(
                        event_type="test_event", details=details, severity="medium"
                    )

                # Verificar que el mensaje de error sea apropiado
                self.assertIn("not JSON serializable", str(context.exception))

    def test_log_subscription_change_with_edge_cases(self):
        """Test que log_subscription_change maneja casos edge"""
        edge_cases = [
            (None, None, None),  # Todos None
            ("", "", ""),  # Strings vacíos
            (123, 456, 789),  # Enteros
            (
                {"status": "active"},
                {"status": "inactive"},
                "reason",
            ),  # Dict como status
            ([1, 2, 3], [4, 5, 6], [7, 8, 9]),  # Listas como status
        ]

        for old_status, new_status, reason in edge_cases:
            with self.subTest(old=type(old_status).__name__, new=type(new_status).__name__):
                try:
                    self.smart_logger.log_subscription_change(
                        empresa_id=123,
                        old_status=old_status,
                        new_status=new_status,
                        reason=reason,
                    )
                    self.assertTrue(
                        True,
                        f"Handled edge case: {type(old_status).__name__} -> {type(new_status).__name__}",
                    )
                except Exception as e:
                    self.fail(f"log_subscription_change crashed with edge case: {e}")

    def test_log_trial_activation_with_non_serializable_ids(self):
        """Test que log_trial_activation maneja IDs no serializables apropiadamente"""
        non_serializable_ids = [
            lambda x: x,  # Lambda como ID
            object(),  # Objeto genérico
            set([1, 2, 3]),  # Set
            type("Test", (), {}),  # Clase
            Exception("test"),  # Excepción
        ]

        for obj in non_serializable_ids:
            with self.subTest(id_type=type(obj).__name__):
                # El sistema debe lanzar una excepción apropiada para objetos no serializables
                with self.assertRaises(TypeError) as context:
                    self.smart_logger.log_trial_activation(
                        user_id=obj, empresa_id=obj, trial_id=obj
                    )

                # Verificar que el mensaje de error sea apropiado
                self.assertIn("not JSON serializable", str(context.exception))

    def test_get_client_ip_with_edge_cases(self):
        """Test que get_client_ip maneja casos edge"""
        # Mock request con diferentes configuraciones
        request = Mock(spec=HttpRequest)

        # Test con X-Forwarded-For
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1"}
        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.1")

        # Test con múltiples IPs
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1, 172.16.0.1"}
        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.1")

        # Test sin X-Forwarded-For
        request.META = {"REMOTE_ADDR": "192.168.1.100"}
        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.100")

        # Test con META vacío
        request.META = {}
        ip = get_client_ip(request)
        self.assertIsNone(ip)

        # Test con X-Forwarded-For vacío
        request.META = {"HTTP_X_FORWARDED_FOR": ""}
        ip = get_client_ip(request)
        self.assertIsNone(ip)

    def test_get_user_agent_with_edge_cases(self):
        """Test que get_user_agent maneja casos edge"""
        request = Mock(spec=HttpRequest)

        # Test con User-Agent normal
        request.META = {
            "HTTP_USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        ua = get_user_agent(request)
        self.assertEqual(ua, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Test sin User-Agent
        request.META = {}
        ua = get_user_agent(request)
        self.assertEqual(ua, "Unknown")

        # Test con User-Agent vacío
        request.META = {"HTTP_USER_AGENT": ""}
        ua = get_user_agent(request)
        self.assertEqual(ua, "")

    def test_json_serialization_fallback(self):
        """Test que el sistema maneja objetos no serializables apropiadamente"""

        # Test con objeto que definitivamente no es serializable
        class NonSerializableClass:
            def __init__(self):
                self.lambda_func = lambda x: x
                self.set_data = {1, 2, 3}
                self.class_ref = type("Test", (), {})

        non_serializable = NonSerializableClass()

        # El sistema debe lanzar una excepción apropiada para objetos no serializables
        with self.assertRaises(TypeError) as context:
            self.smart_logger.log_security_alert(
                event_type="test", details=non_serializable, severity="high"
            )

        # Verificar que el mensaje de error sea apropiado
        self.assertIn("not JSON serializable", str(context.exception))

    def test_logging_with_unicode_and_special_characters(self):
        """Test que el logging maneja caracteres especiales y unicode"""
        special_strings = [
            "Test with émojis 🚀🔥💯",
            "String with ñ and áccénts",
            "String with \n newlines \t and \r tabs",
            "String with \"quotes\" and 'apostrophes'",
            "String with \\backslashes\\ and /forward/slashes",
            "String with <html> tags and &amp; entities",
        ]

        for special_string in special_strings:
            with self.subTest(string=special_string[:20]):
                try:
                    self.smart_logger.log_login_attempt(
                        username=special_string,
                        ip_address="192.168.1.1",
                        user_agent=special_string,
                        success=True,
                        reason=special_string,
                    )
                    self.assertTrue(True, f"Handled special string: {special_string[:20]}")
                except Exception as e:
                    self.fail(f"log_login_attempt crashed with special string: {e}")

    def test_logging_with_extremely_long_strings(self):
        """Test que el logging maneja strings extremadamente largos"""
        # String de 10KB
        long_string = "A" * 10000

        try:
            self.smart_logger.log_payment_received(
                empresa_id=123,
                amount=1000,
                payment_method=long_string,
                reference=long_string,
            )
            self.assertTrue(True, "Handled extremely long string")
        except Exception as e:
            self.fail(f"log_payment_received crashed with long string: {e}")
