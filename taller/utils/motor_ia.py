# -----------------------------------------------------------------------------
# Copyright (c) 2025 eGarage. Todos los derechos reservados.
#
# PROPIEDAD INTELECTUAL PROTEGIDA. ESTRICTAMENTE CONFIDENCIAL.
# Este archivo es el wrapper público del motor de IA.
#
# Consulta el archivo LICENSE en la raíz del repositorio para más detalles
# sobre la protección de la Propiedad Intelectual de eGarage.
# -----------------------------------------------------------------------------
"""
Motor de Inteligencia Artificial para Diagnóstico Predictivo
Wrapper público que delega al core algorítmico protegido

U.S. Patent Pending
Chile Software Registration Pending
"""

from django.utils import timezone

# Importar el core (en producción será el archivo compilado/ofuscado).
# Si falla (pandas, motor_ia_core_compiled inexistente, etc.), el módulo exporta
# MotorDiagnosticoIA = None para que la vista pueda desactivar IA sin romper el sitio.
MotorIACore = None
MotorDiagnosticoIA = None

try:
    try:
        from .motor_ia_core_compiled import MotorIACore
    except ImportError:
        from .motor_ia_core import MotorIACore
except Exception:
    MotorIACore = None


def _motor_ia_class():
    """Clase del motor solo si el core está disponible (evita 500 al cargar URLConf)."""
    if MotorIACore is None:
        return None

    class MotorDiagnosticoIA:
        """
        Wrapper público del motor de IA
        Mantiene la interfaz original mientras delega al core protegido
        """

        def __init__(self):
            self.fecha_actual = timezone.now()
            self.meses_analisis = 12
            self.umbral_crecimiento = 15
            self.umbral_declive = -20

            self._core = MotorIACore(
                fecha_actual=self.fecha_actual,
                meses_analisis=self.meses_analisis,
                umbral_crecimiento=self.umbral_crecimiento,
                umbral_declive=self.umbral_declive,
            )

        def analizar_servicios_completo(self, documentos):
            """Análisis completo de servicios con IA predictiva (sin pandas)."""
            datos_servicios = self._core.preparar_datos_servicios(documentos)

            if not datos_servicios:
                return self._core.generar_datos_demo()

            resultados = {
                "servicios_crecimiento": self._core.detectar_servicios_crecimiento(datos_servicios),
                "servicios_declive": self._core.detectar_servicios_declive(datos_servicios),
                "estacionalidad": self._core.analizar_estacionalidad(datos_servicios),
                "comparativa_mercado": self._core.generar_comparativa_mercado(),
                "recomendaciones_ia": self._core.generar_recomendaciones_ia(datos_servicios),
                "predicciones_ingresos": self._core.predecir_ingresos(datos_servicios),
                "alertas_criticas": self._core.generar_alertas_criticas(datos_servicios),
                "insights_ai": self._core.generar_insights_ai(datos_servicios),
            }
            return resultados

    return MotorDiagnosticoIA


if MotorIACore is not None:
    MotorDiagnosticoIA = _motor_ia_class()
