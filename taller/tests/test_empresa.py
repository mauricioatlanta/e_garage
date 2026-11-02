"""
Tests para el modelo Empresa refinado
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from django.contrib.auth.models import User
from django.utils import timezone

from taller.models.empresa import Empresa


@pytest.fixture
def user():
    """Fixture para crear un usuario de prueba"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def empresa_chile(db):
    """Fixture para crear una empresa de Chile"""
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(
        nombre_taller="Taller Chile Test",
        pais="CL",
        moneda="CLP",
        zona_horaria="America/Santiago",
    )


@pytest.fixture
def empresa_usa(db):
    """Fixture para crear una empresa de USA"""
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(
        nombre_taller="USA Garage Test",
        pais="US",
        moneda="USD",
        zona_horaria="America/New_York",
    )


@pytest.mark.django_db
def test_dias_restantes_ceil(empresa_chile):
    """Test que verifica el cálculo de días restantes con ceil"""
    # Simular que faltan 1.9 días (30 horas)
    ahora = timezone.now()
    empresa_chile.fecha_fin = ahora + timedelta(hours=30)
    empresa_chile.save()

    # Con ceil, 30 horas = 1.25 días → 2 días
    assert empresa_chile.dias_restantes == 2


@pytest.mark.django_db
def test_moneda_por_pais_auto_correccion():
    """Test que verifica la auto-corrección de moneda por país"""
    from taller.tests.factories import EmpresaFactory

    # Test 1: Empresa USA con moneda incorrecta
    empresa_usa = EmpresaFactory(nombre_taller="Test USA", pais="US", moneda="CLP")
    empresa_usa.save()  # Debería auto-corregir
    assert empresa_usa.moneda == "USD"

    # Test 2: Empresa Chile con moneda incorrecta
    empresa_chile = EmpresaFactory(nombre_taller="Test Chile", pais="CL", moneda="USD")
    empresa_chile.save()  # Debería auto-corregir
    assert empresa_chile.moneda == "CLP"


@pytest.mark.django_db
def test_tz_por_pais_auto_correccion():
    """Test que verifica la auto-corrección de zona horaria por país"""
    from taller.tests.factories import EmpresaFactory

    # Test 1: Empresa USA con TZ de Chile
    empresa_usa = EmpresaFactory(nombre_taller="Test USA TZ", pais="US", zona_horaria="America/Santiago")
    empresa_usa.save()  # Debería auto-corregir
    assert empresa_usa.zona_horaria == "America/New_York"

    # Test 2: Empresa Chile con TZ de USA
    empresa_chile = EmpresaFactory(nombre_taller="Test Chile TZ", pais="CL", zona_horaria="America/New_York")
    empresa_chile.save()  # Debería auto-corregir
    assert empresa_chile.zona_horaria == "America/Santiago"


@pytest.mark.django_db
def test_estados_suscripcion(empresa_chile):
    """Test que verifica los estados de suscripción"""
    ahora = timezone.now()

    # Test 1: Estado activa
    empresa_chile.fecha_fin = ahora + timedelta(days=10)
    empresa_chile.suscripcion_activa = True
    empresa_chile.save()
    assert empresa_chile.estado_suscripcion == "activa"
    assert empresa_chile.color_estado == "green"

    # Test 2: Estado advertencia
    empresa_chile.fecha_fin = ahora + timedelta(days=3)
    empresa_chile.save()
    assert empresa_chile.estado_suscripcion == "advertencia"
    assert empresa_chile.color_estado == "orange"

    # Test 3: Estado crítico
    empresa_chile.fecha_fin = ahora + timedelta(hours=12)
    empresa_chile.save()
    assert empresa_chile.estado_suscripcion == "critico"
    assert empresa_chile.color_estado == "red"

    # Test 4: Estado vencida
    empresa_chile.fecha_fin = ahora - timedelta(days=1)
    empresa_chile.suscripcion_activa = False
    empresa_chile.save()
    assert empresa_chile.estado_suscripcion == "vencida"
    assert empresa_chile.color_estado == "gray"


@pytest.mark.django_db
def test_extender_suscripcion(empresa_chile):
    """Test que verifica la extensión de suscripción"""
    ahora = timezone.now()

    # Test 1: Extender suscripción activa
    fecha_fin_original = ahora + timedelta(days=5)
    empresa_chile.fecha_fin = fecha_fin_original
    empresa_chile.suscripcion_activa = True
    empresa_chile.save()

    empresa_chile.extender_suscripcion(30)

    # Debería extender desde la fecha original
    fecha_esperada = fecha_fin_original + timedelta(days=30)
    assert empresa_chile.fecha_fin == fecha_esperada
    assert empresa_chile.suscripcion_activa is True
    assert empresa_chile.notificacion_5_dias is False
    assert empresa_chile.notificacion_1_dia is False
    assert empresa_chile.notificacion_vencido is False

    # Test 2: Extender suscripción vencida
    empresa_chile.fecha_fin = ahora - timedelta(days=1)
    empresa_chile.suscripcion_activa = False
    empresa_chile.save()

    empresa_chile.extender_suscripcion(30)

    # Debería extender desde ahora
    fecha_esperada = ahora + timedelta(days=30)
    # Permitir diferencia de segundos
    assert abs((empresa_chile.fecha_fin - fecha_esperada).total_seconds()) < 5
    assert empresa_chile.suscripcion_activa is True


@pytest.mark.django_db
def test_extender_suscripcion_desde_ahora_ignora_fecha_fin_futura(empresa_chile):
    """
    Regresión: activar un pago sobre un trial vigente (fecha_fin futura) no debe
    sumar los días de trial restantes al período pagado. desde_ahora=True fuerza
    la extensión desde "ahora", igual que si la suscripción ya hubiera vencido.
    """
    ahora = timezone.now()
    fecha_fin_trial = ahora + timedelta(days=30)
    empresa_chile.fecha_fin = fecha_fin_trial
    empresa_chile.suscripcion_activa = False
    empresa_chile.save()

    empresa_chile.extender_suscripcion(365, desde_ahora=True)

    fecha_esperada = ahora + timedelta(days=365)
    assert abs((empresa_chile.fecha_fin - fecha_esperada).total_seconds()) < 5
    # Nunca debería acercarse a fecha_fin_trial + 365 (el bug original).
    assert empresa_chile.fecha_fin < fecha_fin_trial + timedelta(days=365)
    assert empresa_chile.suscripcion_activa is True


@pytest.mark.django_db
def test_extender_suscripcion_desde_ahora_false_preserva_comportamiento_default(empresa_chile):
    """desde_ahora=False (default) sigue acumulando sobre fecha_fin futura, sin cambios."""
    ahora = timezone.now()
    fecha_fin_original = ahora + timedelta(days=10)
    empresa_chile.fecha_fin = fecha_fin_original
    empresa_chile.suscripcion_activa = True
    empresa_chile.save()

    empresa_chile.extender_suscripcion(30, desde_ahora=False)

    assert empresa_chile.fecha_fin == fecha_fin_original + timedelta(days=30)


@pytest.mark.django_db
def test_formato_moneda(empresa_chile, empresa_usa):
    """Test que verifica el formato de moneda por país"""
    # Test Chile
    formato_cl = empresa_chile.formato_moneda
    assert formato_cl["simbolo"] == "$"
    assert formato_cl["codigo"] == "CLP"
    assert formato_cl["decimales"] == 0

    # Test USA
    formato_us = empresa_usa.formato_moneda
    assert formato_us["simbolo"] == "$"
    assert formato_us["codigo"] == "USD"
    assert formato_us["decimales"] == 2


@pytest.mark.django_db
def test_mensajes_alerta(empresa_chile):
    """Test que verifica los mensajes de alerta contextuales"""
    ahora = timezone.now()

    # Test 1: Vencida
    empresa_chile.fecha_fin = ahora - timedelta(days=1)
    empresa_chile.suscripcion_activa = False
    empresa_chile.save()

    mensaje = empresa_chile.get_mensaje_alerta()
    assert "vencido" in mensaje.lower()
    assert empresa_chile.debe_mostrar_alerta() is False  # Vencida no muestra alerta

    # Test 2: Crítica (1 día)
    empresa_chile.fecha_fin = ahora + timedelta(hours=12)
    empresa_chile.suscripcion_activa = True
    empresa_chile.save()

    mensaje = empresa_chile.get_mensaje_alerta()
    assert "mañana" in mensaje.lower()
    assert empresa_chile.debe_mostrar_alerta() is True

    # Test 3: Advertencia (3 días)
    empresa_chile.fecha_fin = ahora + timedelta(days=3)
    empresa_chile.save()

    mensaje = empresa_chile.get_mensaje_alerta()
    assert "3 días" in mensaje
    assert empresa_chile.debe_mostrar_alerta() is True

    # Test 4: Activa (10 días)
    empresa_chile.fecha_fin = ahora + timedelta(days=10)
    empresa_chile.save()

    mensaje = empresa_chile.get_mensaje_alerta()
    assert mensaje == ""  # Sin mensaje
    assert empresa_chile.debe_mostrar_alerta() is False


@pytest.mark.django_db
def test_marcar_pago_recibido(empresa_chile):
    """Test que verifica el marcado de pago recibido"""
    ahora = timezone.now()
    empresa_chile.fecha_fin = ahora - timedelta(days=1)  # Vencida
    empresa_chile.suscripcion_activa = False
    empresa_chile.save()

    # Marcar pago
    empresa_chile.marcar_pago_recibido(monto=Decimal("50000"), plan="premium")

    assert empresa_chile.valor_mensual == Decimal("50000")
    assert empresa_chile.plan == "premium"
    assert empresa_chile.suscripcion_activa is True
    assert empresa_chile.ultimo_pago is not None
    # Debería haber extendido 30 días desde ahora
    fecha_esperada = ahora + timedelta(days=30)
    assert abs((empresa_chile.fecha_fin - fecha_esperada).total_seconds()) < 5


@pytest.mark.django_db
def test_timezone_display(empresa_chile, empresa_usa):
    """Test que verifica el display de zona horaria"""
    assert empresa_chile.timezone_display == "Chile Time (CLT)"
    assert empresa_usa.timezone_display == "Eastern Time (ET)"


@pytest.mark.django_db
def test_convert_to_local_time(empresa_chile):
    """Test que verifica la conversión a hora local"""
    utc_time = timezone.now()
    local_time = empresa_chile.convert_to_local_time(utc_time)

    assert local_time is not None
    assert local_time.tzinfo is not None


@pytest.mark.django_db
def test_format_local_datetime(empresa_chile):
    """Test que verifica el formateo de datetime local"""
    utc_time = timezone.now()

    # Test formato full
    formatted = empresa_chile.format_local_datetime(utc_time, "full")
    assert formatted != ""
    assert "/" in formatted  # MM/DD/YYYY formato

    # Test formato date
    formatted_date = empresa_chile.format_local_datetime(utc_time, "date")
    assert formatted_date != ""
    assert ":" not in formatted_date  # Solo fecha, no hora

    # Test formato time
    formatted_time = empresa_chile.format_local_datetime(utc_time, "time")
    assert formatted_time != ""
    assert ":" in formatted_time  # Solo hora, no fecha


@pytest.mark.django_db
def test_constraints_validation():
    """Test que verifica las constraints de validación"""
    user = User.objects.create_user(username="constraint_test", password="test")

    # Test constraint dias_prueba >= 0
    empresa = Empresa(
        user=user,
        nombre_taller="Test Constraints",
        dias_prueba=-1,  # Inválido
    )

    # No debería poder guardar con dias_prueba negativo
    with pytest.raises(Exception):  # IntegrityError o ValidationError
        empresa.save()

    # Test constraint valor_mensual >= 0
    empresa.dias_prueba = 30
    empresa.valor_mensual = Decimal("-100")  # Inválido

    # No debería poder guardar con valor_mensual negativo
    with pytest.raises(Exception):  # IntegrityError o ValidationError
        empresa.save()
