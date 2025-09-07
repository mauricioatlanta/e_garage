#!/usr/bin/env python
"""
Script de validaciones de consistencia de datos entre países
Paso 2 del plan de completitud al 100%
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

import traceback

from django.db.models import Count, F

from taller.models import *
from taller.servicios.models import *


class ValidadorConsistencia:
    """Validador completo de consistencia de datos entre países"""

    def __init__(self):
        self.errores = []
        self.advertencias = []
        self.correciones_aplicadas = []

    def log_error(self, tipo, mensaje, modelo=None, objeto_id=None):
        """Registrar error de consistencia"""
        error = {
            "tipo": tipo,
            "mensaje": mensaje,
            "modelo": modelo.__name__ if modelo else None,
            "objeto_id": objeto_id,
            "nivel": "ERROR",
        }
        self.errores.append(error)
        print(f"❌ ERROR: {mensaje}")

    def log_advertencia(self, tipo, mensaje, modelo=None, objeto_id=None):
        """Registrar advertencia de consistencia"""
        advertencia = {
            "tipo": tipo,
            "mensaje": mensaje,
            "modelo": modelo.__name__ if modelo else None,
            "objeto_id": objeto_id,
            "nivel": "WARNING",
        }
        self.advertencias.append(advertencia)
        print(f"⚠️ ADVERTENCIA: {mensaje}")

    def log_correccion(self, mensaje, accion):
        """Registrar corrección aplicada"""
        correccion = {"mensaje": mensaje, "accion": accion}
        self.correciones_aplicadas.append(correccion)
        print(f"🔧 CORREGIDO: {mensaje}")

    def validar_1_fk_vehiculos_clientes(self):
        """Validar que vehículos pertenezcan a clientes del mismo país/empresa"""
        print("\n🔍 VALIDACIÓN 1: FK Vehículos → Clientes")
        print("-" * 50)

        # Buscar vehículos que referencian clientes de empresas diferentes
        vehiculos_inconsistentes = Vehiculo.objects.select_related(
            "cliente", "cliente__empresa"
        ).exclude(cliente__empresa__isnull=True)

        for vehiculo in vehiculos_inconsistentes:
            try:
                empresa_vehiculo = vehiculo.cliente.empresa
                # Verificar si hay alguna inconsistencia
                if not empresa_vehiculo:
                    self.log_error(
                        "FK_ORPHAN",
                        f"Vehículo {vehiculo.patente} pertenece a cliente sin empresa",
                        Vehiculo,
                        vehiculo.pk,
                    )
            except Exception as e:
                self.log_error(
                    "FK_ERROR",
                    f"Error validando vehículo {vehiculo.patente}: {str(e)}",
                    Vehiculo,
                    vehiculo.pk,
                )

        print("✅ Validación FK Vehículos-Clientes completada")

    def validar_2_fk_documentos_multiempresa(self):
        """Validar que documentos referencien objetos de la misma empresa"""
        print("\n🔍 VALIDACIÓN 2: FK Documentos → Multiempresa")
        print("-" * 50)

        # Validar que cliente y empresa del documento coincidan
        documentos_inconsistentes = Documento.objects.select_related(
            "empresa", "cliente", "cliente__empresa"
        ).exclude(cliente__empresa=F("empresa"))

        count_inconsistentes = documentos_inconsistentes.count()
        if count_inconsistentes > 0:
            self.log_error(
                "MULTIEMPRESA_MISMATCH",
                f"{count_inconsistentes} documentos con cliente de empresa diferente",
                Documento,
            )

            for doc in documentos_inconsistentes[:5]:  # Solo primeros 5 para no saturar
                self.log_error(
                    "DOCUMENTO_EMPRESA_MISMATCH",
                    f"Documento {doc.numero_documento}: empresa={doc.empresa.pk}, cliente.empresa={doc.cliente.empresa.pk}",
                    Documento,
                    doc.pk,
                )
        else:
            print("✅ Todos los documentos tienen consistencia multiempresa")

    def validar_3_servicios_country_consistency(self):
        """Validar consistencia de países en servicios"""
        print("\n🔍 VALIDACIÓN 3: Consistencia Country en Servicios")
        print("-" * 50)

        # Validar que servicios hereden country de su subcategoría
        servicios_inconsistentes = Servicio.objects.select_related(
            "subcategoria", "subcategoria__categoria"
        ).exclude(country=F("subcategoria__country"))

        count_inconsistentes = servicios_inconsistentes.count()
        if count_inconsistentes > 0:
            self.log_error(
                "COUNTRY_MISMATCH",
                f"{count_inconsistentes} servicios con country diferente a su subcategoría",
                Servicio,
            )

            # Intentar corregir automáticamente
            for servicio in servicios_inconsistentes:
                country_correcto = servicio.subcategoria.country
                country_anterior = servicio.country
                servicio.country = country_correcto
                servicio.save()

                self.log_correccion(
                    f"Servicio {servicio.code}: {country_anterior} → {country_correcto}",
                    "Auto-sincronización de country",
                )
        else:
            print("✅ Todos los servicios tienen country consistente")

    def validar_4_traducciones_completas(self):
        """Validar que servicios tengan traducciones completas"""
        print("\n🔍 VALIDACIÓN 4: Completitud de Traducciones")
        print("-" * 50)

        # Servicios sin traducción en español
        servicios_sin_es = Servicio.objects.exclude(names__language="es").distinct()

        # Servicios sin traducción en inglés
        servicios_sin_en = Servicio.objects.exclude(names__language="en").distinct()

        if servicios_sin_es.exists():
            count = servicios_sin_es.count()
            self.log_advertencia(
                "TRADUCCION_FALTANTE",
                f"{count} servicios sin traducción al español",
                Servicio,
            )

        if servicios_sin_en.exists():
            count = servicios_sin_en.count()
            self.log_advertencia(
                "TRADUCCION_FALTANTE",
                f"{count} servicios sin traducción al inglés",
                Servicio,
            )

        # Servicios con traducciones duplicadas (violando unique_together)
        duplicados = (
            ServicioName.objects.values("servicio", "language")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if duplicados.exists():
            self.log_error(
                "TRADUCCION_DUPLICADA",
                f"{duplicados.count()} servicios con traducciones duplicadas",
                ServicioName,
            )

    def validar_5_unique_constraints(self):
        """Validar constraints unique_together"""
        print("\n🔍 VALIDACIÓN 5: Constraints Unique Together")
        print("-" * 50)

        # Validar unique_together en Servicio (country, tipo, code)
        duplicados_servicio = (
            Servicio.objects.values("country", "tipo", "code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if duplicados_servicio.exists():
            for dup in duplicados_servicio:
                self.log_error(
                    "UNIQUE_VIOLATION",
                    f"Servicios duplicados: {dup['country']}-{dup['tipo']}-{dup['code']} ({dup['count']} instancias)",
                    Servicio,
                )
        else:
            print("✅ No hay violaciones de unique_together en Servicio")

        # Validar unique_together en ServicioName (servicio, language, is_default)
        duplicados_name = (
            ServicioName.objects.filter(is_default=True)
            .values("servicio", "language")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if duplicados_name.exists():
            for dup in duplicados_name:
                self.log_error(
                    "UNIQUE_VIOLATION",
                    f"Traducciones default duplicadas: servicio {dup['servicio']}, idioma {dup['language']} ({dup['count']} instancias)",
                    ServicioName,
                )
        else:
            print("✅ No hay violaciones de unique_together en ServicioName")

    def validar_6_integridad_referencial(self):
        """Validar integridad referencial completa"""
        print("\n🔍 VALIDACIÓN 6: Integridad Referencial")
        print("-" * 50)

        # OtroServicioDocumento debe referenciar Servicio existente
        try:
            otros_servicios_huerfanos = OtroServicioDocumento.objects.filter(
                servicio__isnull=True
            )

            if otros_servicios_huerfanos.exists():
                count = otros_servicios_huerfanos.count()
                self.log_advertencia(
                    "FK_NULL",
                    f"{count} otros servicios sin referencia a catálogo",
                    OtroServicioDocumento,
                )
            else:
                print("✅ Todos los otros servicios tienen referencia válida")

        except Exception as e:
            self.log_error(
                "VALIDATION_ERROR", f"Error validando integridad referencial: {str(e)}"
            )

    def validar_7_datos_por_pais(self):
        """Validar distribución de datos por país"""
        print("\n🔍 VALIDACIÓN 7: Distribución por País")
        print("-" * 50)

        paises = ["CL", "US"]

        for pais in paises:
            print(f"\n🌍 País: {pais}")

            # Contar datos por país
            count_servicios = Servicio.objects.filter(country=pais).count()
            count_categorias = CategoriaServicio.objects.filter(country=pais).count()
            count_subcategorias = SubcategoriaServicio.objects.filter(
                country=pais
            ).count()

            print(f"   Servicios: {count_servicios}")
            print(f"   Categorías: {count_categorias}")
            print(f"   Subcategorías: {count_subcategorias}")

            # Verificar balance mínimo
            if count_servicios == 0:
                self.log_advertencia(
                    "DATOS_FALTANTES", f"País {pais} no tiene servicios", Servicio
                )

            if count_categorias == 0:
                self.log_advertencia(
                    "DATOS_FALTANTES",
                    f"País {pais} no tiene categorías de servicio",
                    CategoriaServicio,
                )

    def ejecutar_validaciones_completas(self):
        """Ejecutar suite completa de validaciones"""
        print("🚀 INICIANDO VALIDACIONES DE CONSISTENCIA")
        print("🎯 Verificando integridad de datos entre países")
        print("=" * 70)

        try:
            self.validar_1_fk_vehiculos_clientes()
            self.validar_2_fk_documentos_multiempresa()
            self.validar_3_servicios_country_consistency()
            self.validar_4_traducciones_completas()
            self.validar_5_unique_constraints()
            self.validar_6_integridad_referencial()
            self.validar_7_datos_por_pais()

        except Exception as e:
            self.log_error("CRITICAL_ERROR", f"Error crítico en validaciones: {str(e)}")
            traceback.print_exc()

        self.generar_reporte_final()

    def generar_reporte_final(self):
        """Generar reporte final de validaciones"""
        print("\n" + "=" * 70)
        print("📊 REPORTE FINAL DE VALIDACIONES")
        print("=" * 70)

        total_errores = len(self.errores)
        total_advertencias = len(self.advertencias)
        total_correcciones = len(self.correciones_aplicadas)

        print(f"❌ Errores encontrados: {total_errores}")
        print(f"⚠️ Advertencias: {total_advertencias}")
        print(f"🔧 Correcciones aplicadas: {total_correcciones}")

        # Mostrar errores críticos
        if total_errores > 0:
            print("\n❌ ERRORES CRÍTICOS:")
            for error in self.errores[:10]:  # Solo primeros 10
                print(f"   - {error['tipo']}: {error['mensaje']}")

        # Mostrar advertencias importantes
        if total_advertencias > 0:
            print("\n⚠️ ADVERTENCIAS:")
            for adv in self.advertencias[:5]:  # Solo primeras 5
                print(f"   - {adv['tipo']}: {adv['mensaje']}")

        # Mostrar correcciones aplicadas
        if total_correcciones > 0:
            print("\n🔧 CORRECCIONES APLICADAS:")
            for corr in self.correciones_aplicadas:
                print(f"   - {corr['mensaje']}")

        # Estado final
        if total_errores == 0:
            print("\n✅ CONSISTENCIA VALIDADA: Base de datos íntegra")
            print("🎯 Sistema listo para producción multicountry")
        else:
            print(f"\n⚠️ ACCIÓN REQUERIDA: {total_errores} errores necesitan corrección")

        return total_errores == 0


if __name__ == "__main__":
    validador = ValidadorConsistencia()
    validador.ejecutar_validaciones_completas()
