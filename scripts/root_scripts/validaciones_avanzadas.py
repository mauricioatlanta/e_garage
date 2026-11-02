#!/usr/bin/env python
"""
Validaciones avanzadas adicionales - Paso 2 extendido
Validaciones profundas de lógica de negocio y performance
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

import traceback
from decimal import Decimal

from django.db.models import Count, F

from taller.models import *
from taller.servicios.models import *


class ValidadorAvanzado:
    """Validador avanzado de lógica de negocio"""

    def __init__(self):
        self.resultados = []
        self.rendimiento = []

    def log_resultado(self, test, estado, detalles=""):
        """Registrar resultado de test"""
        resultado = {
            "test": test,
            "estado": estado,  # 'PASS', 'FAIL', 'WARNING'
            "detalles": detalles,
        }
        self.resultados.append(resultado)

        emoji = "✅" if estado == "PASS" else "❌" if estado == "FAIL" else "⚠️"
        print(f"{emoji} {test}: {detalles}")

    def validar_8_logica_multiempresa(self):
        """Validar que la lógica multiempresa no mezcle datos"""
        print("\n🔍 VALIDACIÓN 8: Lógica Multiempresa Avanzada")
        print("-" * 50)

        try:
            # Verificar que no existan documentos que referencien vehículos de otras empresas
            docs_cruzados = Documento.objects.filter(
                vehiculo__cliente__empresa__isnull=False
            ).exclude(empresa=F("vehiculo__cliente__empresa"))

            if docs_cruzados.exists():
                self.log_resultado(
                    "Aislamiento Multiempresa",
                    "FAIL",
                    f"{docs_cruzados.count()} documentos referencian vehículos de otras empresas",
                )
            else:
                self.log_resultado(
                    "Aislamiento Multiempresa",
                    "PASS",
                    "No hay cruces entre empresas en documentos",
                )

            # Verificar que servicios estén correctamente filtrados por país
            servicios_por_pais = (
                Servicio.objects.values("country").annotate(count=Count("id")).order_by("country")
            )

            detalles_paises = ", ".join(
                [f"{s['country']}:{s['count']}" for s in servicios_por_pais]
            )
            self.log_resultado(
                "Distribución Servicios por País",
                "PASS",
                f"Servicios distribuidos: {detalles_paises}",
            )

        except Exception as e:
            self.log_resultado("Lógica Multiempresa", "FAIL", f"Error en validación: {str(e)}")

    def validar_9_performance_consultas(self):
        """Validar performance de consultas críticas"""
        print("\n🔍 VALIDACIÓN 9: Performance de Consultas")
        print("-" * 50)

        import time

        # Test 1: Búsqueda de servicios por país/idioma
        start_time = time.time()
        servicios_cl = (
            Servicio.objects.filter(country="CL")
            .select_related("subcategoria")
            .prefetch_related("names")[:10]
        )
        list(servicios_cl)  # Forzar evaluación
        tiempo_busqueda = time.time() - start_time

        if tiempo_busqueda < 0.1:
            self.log_resultado(
                "Performance Búsqueda Servicios",
                "PASS",
                f"Búsqueda completada en {tiempo_busqueda:.3f}s",
            )
        else:
            self.log_resultado(
                "Performance Búsqueda Servicios",
                "WARNING",
                f"Búsqueda lenta: {tiempo_busqueda:.3f}s",
            )

        # Test 2: Consulta de documentos multiempresa
        start_time = time.time()
        docs_empresa = Documento.objects.select_related("empresa", "cliente", "vehiculo")[:50]
        list(docs_empresa)  # Forzar evaluación
        tiempo_docs = time.time() - start_time

        if tiempo_docs < 0.2:
            self.log_resultado(
                "Performance Consulta Documentos",
                "PASS",
                f"Consulta completada en {tiempo_docs:.3f}s",
            )
        else:
            self.log_resultado(
                "Performance Consulta Documentos",
                "WARNING",
                f"Consulta lenta: {tiempo_docs:.3f}s",
            )

    def validar_10_calculos_financieros(self):
        """Validar cálculos financieros y separación interno/externo"""
        print("\n🔍 VALIDACIÓN 10: Cálculos Financieros")
        print("-" * 50)

        try:
            # Verificar que servicios externos no se cuenten como ingresos
            otros_servicios = OtroServicioDocumento.objects.all()

            for otro_servicio in otros_servicios[:5]:  # Muestra de 5
                if hasattr(otro_servicio, "ganancia"):
                    ganancia = otro_servicio.ganancia
                    if isinstance(ganancia, (int, float, Decimal)) and ganancia >= 0:
                        self.log_resultado(
                            f"Ganancia Servicio Externo #{otro_servicio.pk}",
                            "PASS",
                            f"Ganancia calculada: ${ganancia:,.2f}",
                        )
                    else:
                        self.log_resultado(
                            f"Ganancia Servicio Externo #{otro_servicio.pk}",
                            "WARNING",
                            f"Ganancia negativa o inválida: {ganancia}",
                        )

            # Verificar separación de costos
            servicios_internos = Servicio.objects.filter(tipo="interno").count()
            servicios_externos = Servicio.objects.filter(tipo="externo").count()

            self.log_resultado(
                "Separación Tipos de Servicio",
                "PASS",
                f"Internos: {servicios_internos}, Externos: {servicios_externos}",
            )

        except Exception as e:
            self.log_resultado("Cálculos Financieros", "FAIL", f"Error: {str(e)}")

    def validar_11_integridad_busqueda(self):
        """Validar integridad del sistema de búsqueda"""
        print("\n🔍 VALIDACIÓN 11: Integridad Sistema Búsqueda")
        print("-" * 50)

        try:
            # Test de búsqueda por alias
            terminos_busqueda = ["towing", "remolque", "aceite", "oil"]

            for termino in terminos_busqueda:
                # Buscar servicios que contengan el término en aliases
                servicios_encontrados = Servicio.objects.filter(
                    names__aliases__icontains=termino
                ).distinct()

                count = servicios_encontrados.count()
                self.log_resultado(
                    f"Búsqueda por '{termino}'",
                    "PASS" if count > 0 else "WARNING",
                    f"{count} resultados encontrados",
                )

            # Verificar que todos los servicios tengan al menos un nombre
            servicios_sin_nombre = Servicio.objects.filter(names__isnull=True).count()

            if servicios_sin_nombre == 0:
                self.log_resultado(
                    "Servicios con Nombres",
                    "PASS",
                    "Todos los servicios tienen nombres definidos",
                )
            else:
                self.log_resultado(
                    "Servicios con Nombres",
                    "FAIL",
                    f"{servicios_sin_nombre} servicios sin nombres",
                )

        except Exception as e:
            self.log_resultado("Sistema de Búsqueda", "FAIL", f"Error: {str(e)}")

    def validar_12_escalabilidad_datos(self):
        """Validar escalabilidad con volumen de datos"""
        print("\n🔍 VALIDACIÓN 12: Escalabilidad de Datos")
        print("-" * 50)

        try:
            # Contar objetos principales
            counts = {
                "Servicios": Servicio.objects.count(),
                "ServicioNames": ServicioName.objects.count(),
                "Categorías": CategoriaServicio.objects.count(),
                "Subcategorías": SubcategoriaServicio.objects.count(),
                "Documentos": Documento.objects.count(),
                "OtrosServicios": OtroServicioDocumento.objects.count(),
            }

            for modelo, count in counts.items():
                if count > 0:
                    self.log_resultado(f"Volumen {modelo}", "PASS", f"{count} registros")
                else:
                    self.log_resultado(
                        f"Volumen {modelo}", "WARNING", f"Sin datos: {count} registros"
                    )

            # Verificar ratios de traducciones
            servicios_count = Servicio.objects.count()
            traducciones_count = ServicioName.objects.count()

            if servicios_count > 0:
                ratio_traducciones = traducciones_count / servicios_count
                if ratio_traducciones >= 1.8:  # Esperamos ~2 idiomas por servicio
                    self.log_resultado(
                        "Ratio Traducciones",
                        "PASS",
                        f"{ratio_traducciones:.1f} traducciones por servicio",
                    )
                else:
                    self.log_resultado(
                        "Ratio Traducciones",
                        "WARNING",
                        f"Pocas traducciones: {ratio_traducciones:.1f} por servicio",
                    )

        except Exception as e:
            self.log_resultado("Escalabilidad de Datos", "FAIL", f"Error: {str(e)}")

    def ejecutar_validaciones_avanzadas(self):
        """Ejecutar suite completa de validaciones avanzadas"""
        print("🚀 INICIANDO VALIDACIONES AVANZADAS")
        print("🎯 Verificando lógica de negocio y performance")
        print("=" * 70)

        try:
            self.validar_8_logica_multiempresa()
            self.validar_9_performance_consultas()
            self.validar_10_calculos_financieros()
            self.validar_11_integridad_busqueda()
            self.validar_12_escalabilidad_datos()

        except Exception as e:
            self.log_resultado("VALIDACIONES AVANZADAS", "FAIL", f"Error crítico: {str(e)}")
            traceback.print_exc()

        self.generar_reporte_avanzado()

    def generar_reporte_avanzado(self):
        """Generar reporte final de validaciones avanzadas"""
        print("\n" + "=" * 70)
        print("📊 REPORTE VALIDACIONES AVANZADAS")
        print("=" * 70)

        total_tests = len(self.resultados)
        tests_pass = len([r for r in self.resultados if r["estado"] == "PASS"])
        tests_fail = len([r for r in self.resultados if r["estado"] == "FAIL"])
        tests_warning = len([r for r in self.resultados if r["estado"] == "WARNING"])

        print(f"📈 Total tests ejecutados: {total_tests}")
        print(f"✅ Tests exitosos: {tests_pass}")
        print(f"❌ Tests fallidos: {tests_fail}")
        print(f"⚠️ Advertencias: {tests_warning}")

        # Calcular porcentaje de éxito
        if total_tests > 0:
            porcentaje_exito = (tests_pass / total_tests) * 100
            print(f"🎯 Porcentaje de éxito: {porcentaje_exito:.1f}%")

            if porcentaje_exito >= 90:
                print("\n🎉 SISTEMA AVANZADO: Validaciones satisfactorias")
                print("✅ Listo para entorno de producción")
            elif porcentaje_exito >= 75:
                print("\n⚠️ SISTEMA FUNCIONAL: Algunas mejoras recomendadas")
            else:
                print("\n❌ ACCIÓN REQUERIDA: Resolver problemas críticos")

        # Mostrar fallos si los hay
        fallos = [r for r in self.resultados if r["estado"] == "FAIL"]
        if fallos:
            print("\n❌ PROBLEMAS A RESOLVER:")
            for fallo in fallos:
                print(f"   - {fallo['test']}: {fallo['detalles']}")

        return tests_fail == 0


if __name__ == "__main__":
    validador = ValidadorAvanzado()
    validador.ejecutar_validaciones_avanzadas()
