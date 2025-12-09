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

# Importar el core (en producción será el archivo compilado/ofuscado)
try:
    # Intentar importar el core compilado primero (para producción)
    from .motor_ia_core_compiled import MotorIACore
except ImportError:
    # Fallback al código fuente (solo para desarrollo)
    from .motor_ia_core import MotorIACore


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

        # Inicializar el core protegido
        self._core = MotorIACore(
            fecha_actual=self.fecha_actual,
            meses_analisis=self.meses_analisis,
            umbral_crecimiento=self.umbral_crecimiento,
            umbral_declive=self.umbral_declive,
        )

    def analizar_servicios_completo(self, documentos):
        """Análisis completo de servicios con IA predictiva"""
        # Preparar datos usando el core
        df_servicios = self._core.preparar_datos_servicios(documentos)

        if df_servicios.empty:
            return self._core.generar_datos_demo()

        # Delegar análisis al core protegido
        resultados = {
            "servicios_crecimiento": self._core.detectar_servicios_crecimiento(df_servicios),
            "servicios_declive": self._core.detectar_servicios_declive(df_servicios),
            "estacionalidad": self._core.analizar_estacionalidad(df_servicios),
            "comparativa_mercado": self._core.generar_comparativa_mercado(),
            "recomendaciones_ia": self._core.generar_recomendaciones_ia(df_servicios),
            "predicciones_ingresos": self._core.predecir_ingresos(df_servicios),
            "alertas_criticas": self._core.generar_alertas_criticas(df_servicios),
            "insights_ai": self._core.generar_insights_ai(df_servicios),
        }

        return resultados
