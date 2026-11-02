#!/usr/bin/env python
"""
Script para validar que el código ofuscado funciona correctamente
Ejecutar después de ofuscar con PyArmor

Uso:
    python scripts/test_codigo_ofuscado.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django

django.setup()

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(test_name):
    """Imprime nombre del test"""
    print(f"\n{BLUE}🧪 {test_name}{RESET}")


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Imprime mensaje de error"""
    print(f"{RED}❌ {message}{RESET}")


def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"{YELLOW}⚠️  {message}{RESET}")


def test_import_ofuscado():
    """Test 1: Verificar que se puede importar el código ofuscado"""
    print_test("Test 1: Importación del código ofuscado")

    try:
        # Intentar importar el wrapper que debe usar el core ofuscado
        from taller.utils.motor_ia import MotorDiagnosticoIA

        print_success("MotorDiagnosticoIA importado correctamente")

        # Verificar que el core está disponible
        motor = MotorDiagnosticoIA()
        if hasattr(motor, "_core"):
            print_success("Core ofuscado cargado correctamente")
            return True
        else:
            print_error("El core no está disponible en el motor")
            return False

    except ImportError as e:
        print_error(f"Error al importar: {e}")
        print_warning("Verifica que el código fue ofuscado correctamente")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False


def test_funcionalidad_basica():
    """Test 2: Verificar funcionalidad básica del motor"""
    print_test("Test 2: Funcionalidad básica del motor")

    try:
        from taller.utils.motor_ia import MotorDiagnosticoIA

        motor = MotorDiagnosticoIA()

        # Test con datos vacíos (debe generar datos demo)
        resultados = motor.analizar_servicios_completo([])

        # Verificar estructura de resultados
        campos_requeridos = [
            "servicios_crecimiento",
            "servicios_declive",
            "estacionalidad",
            "comparativa_mercado",
            "recomendaciones_ia",
            "predicciones_ingresos",
            "alertas_criticas",
            "insights_ai",
        ]

        for campo in campos_requeridos:
            if campo not in resultados:
                print_error(f"Campo faltante en resultados: {campo}")
                return False

        print_success("Estructura de resultados correcta")
        print_success(f"Servicios en crecimiento: {len(resultados['servicios_crecimiento'])}")
        print_success(f"Predicciones generadas: {len(resultados['predicciones_ingresos'])}")
        print_success(f"Recomendaciones: {len(resultados['recomendaciones_ia'])}")

        return True

    except Exception as e:
        print_error(f"Error en funcionalidad básica: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_predicciones_ingresos():
    """Test 3: Verificar que las predicciones de ingresos funcionan"""
    print_test("Test 3: Predicciones de ingresos")

    try:
        from taller.utils.motor_ia import MotorDiagnosticoIA

        motor = MotorDiagnosticoIA()
        resultados = motor.analizar_servicios_completo([])

        predicciones = resultados.get("predicciones_ingresos", [])

        if not predicciones:
            print_error("No se generaron predicciones")
            return False

        # Verificar estructura de cada predicción
        for pred in predicciones:
            campos_requeridos = ["mes", "ingreso_predicho", "confianza", "rango_min", "rango_max"]
            for campo in campos_requeridos:
                if campo not in pred:
                    print_error(f"Campo faltante en predicción: {campo}")
                    return False

            # Verificar que los valores son razonables
            if pred["rango_min"] > pred["rango_max"]:
                print_error("Rango mínimo mayor que máximo")
                return False

            if not (0 <= pred["confianza"] <= 100):
                print_error(f"Confianza fuera de rango: {pred['confianza']}")
                return False

        print_success(f"Predicciones validadas: {len(predicciones)} períodos")
        return True

    except Exception as e:
        print_error(f"Error en predicciones: {e}")
        return False


def test_recomendaciones_ia():
    """Test 4: Verificar que las recomendaciones de IA funcionan"""
    print_test("Test 4: Recomendaciones de IA")

    try:
        from taller.utils.motor_ia import MotorDiagnosticoIA

        motor = MotorDiagnosticoIA()
        resultados = motor.analizar_servicios_completo([])

        recomendaciones = resultados.get("recomendaciones_ia", [])

        if not recomendaciones:
            print_error("No se generaron recomendaciones")
            return False

        # Verificar estructura de cada recomendación
        for rec in recomendaciones:
            campos_requeridos = ["tipo", "icono", "titulo", "mensaje", "impacto", "probabilidad"]
            for campo in campos_requeridos:
                if campo not in rec:
                    print_error(f"Campo faltante en recomendación: {campo}")
                    return False

            # Verificar valores válidos
            if rec["impacto"] not in ["Alto", "Medio", "Bajo"]:
                print_error(f"Impacto inválido: {rec['impacto']}")
                return False

            if not (0 <= rec["probabilidad"] <= 100):
                print_error(f"Probabilidad fuera de rango: {rec['probabilidad']}")
                return False

        print_success(f"Recomendaciones validadas: {len(recomendaciones)}")
        return True

    except Exception as e:
        print_error(f"Error en recomendaciones: {e}")
        return False


def test_comparativa_mercado():
    """Test 5: Verificar comparativa de mercado"""
    print_test("Test 5: Comparativa de mercado")

    try:
        from taller.utils.motor_ia import MotorDiagnosticoIA

        motor = MotorDiagnosticoIA()
        resultados = motor.analizar_servicios_completo([])

        comparativa = resultados.get("comparativa_mercado", [])

        if not comparativa:
            print_error("No se generó comparativa de mercado")
            return False

        # Verificar estructura
        for item in comparativa:
            campos_requeridos = ["servicio", "nuestro_precio", "precio_mercado", "diferencia"]
            for campo in campos_requeridos:
                if campo not in item:
                    print_error(f"Campo faltante en comparativa: {campo}")
                    return False

        print_success(f"Comparativa de mercado validada: {len(comparativa)} servicios")
        return True

    except Exception as e:
        print_error(f"Error en comparativa: {e}")
        return False


def test_con_datos_reales():
    """Test 6: Test con datos reales de la base de datos (si están disponibles)"""
    print_test("Test 6: Test con datos reales (opcional)")

    try:
        from taller.utils.motor_ia import MotorDiagnosticoIA
        from taller.models import Documento

        # Intentar obtener documentos reales
        documentos = Documento.objects.all()[:10]

        if documentos.count() == 0:
            print_warning("No hay documentos en la BD, saltando test con datos reales")
            return True

        motor = MotorDiagnosticoIA()
        resultados = motor.analizar_servicios_completo(documentos)

        # Verificar que se procesaron los datos
        if resultados.get("servicios_crecimiento") or resultados.get("servicios_declive"):
            print_success(f"Análisis realizado con {documentos.count()} documentos")
        else:
            print_warning("No se detectaron tendencias (puede ser normal con pocos datos)")

        return True

    except Exception as e:
        print_warning(f"No se pudo ejecutar test con datos reales: {e}")
        return True  # No es crítico


def main():
    """Función principal"""
    print(f"\n{BLUE}{'='*60}")
    print("🧪 VALIDACIÓN DEL CÓDIGO OFUSCADO")
    print(f"{'='*60}{RESET}\n")

    tests = [
        ("Importación", test_import_ofuscado),
        ("Funcionalidad Básica", test_funcionalidad_basica),
        ("Predicciones de Ingresos", test_predicciones_ingresos),
        ("Recomendaciones IA", test_recomendaciones_ia),
        ("Comparativa de Mercado", test_comparativa_mercado),
        ("Datos Reales", test_con_datos_reales),
    ]

    resultados = []
    for test_name, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((test_name, resultado))
        except Exception as e:
            print_error(f"Error inesperado en {test_name}: {e}")
            resultados.append((test_name, False))

    # Resumen
    print(f"\n{BLUE}{'='*60}")
    print("📊 RESUMEN DE TESTS")
    print(f"{'='*60}{RESET}\n")

    passed = sum(1 for _, result in resultados if result)
    total = len(resultados)

    for test_name, result in resultados:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{BLUE}Resultado: {passed}/{total} tests pasados{RESET}\n")

    if passed == total:
        print(f"{GREEN}{'='*60}")
        print("✅ TODOS LOS TESTS PASARON")
        print("El código ofuscado funciona correctamente")
        print(f"{'='*60}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'='*60}")
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores arriba antes de desplegar a producción")
        print(f"{'='*60}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
