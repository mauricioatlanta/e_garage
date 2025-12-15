"""
Módulo de reportes y análisis basados en KilometrajeRegistro.

Este módulo proporciona funcionalidades para:
- Trazabilidad de garantías
- Reportes de frecuencia de visita y desgaste
- Recordatorios de mantenimiento predictivo
- Historial de mantenimiento detallado
"""

from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

from taller.models import Documento, KilometrajeRegistro, Vehiculo


class ReporteKilometraje:
    """Clase principal para generar reportes basados en kilometraje"""

    def __init__(self, empresa):
        """
        Inicializa el reporte para una empresa específica.

        Args:
            empresa: Instancia de Empresa
        """
        self.empresa = empresa

    # ========================================================================
    # 1. TRAZABILIDAD DE GARANTÍAS
    # ========================================================================

    def verificar_garantia(
        self, documento_garantia: Documento, documento_original: Documento
    ) -> Dict:
        """
        Verifica si un documento de garantía está dentro del límite de kilometraje.

        Args:
            documento_garantia: Documento de ingreso por garantía
            documento_original: Documento de la reparación original

        Returns:
            dict: {
                'dentro_garantia': bool,
                'kilometros_recorridos': int,
                'limite_garantia_km': int (configurable),
                'porcentaje_uso': float,
                'mensaje': str
            }
        """
        # Obtener registros de kilometraje
        try:
            registro_original = documento_original.registro_kilometraje
            registro_garantia = documento_garantia.registro_kilometraje
        except Exception:
            return {"dentro_garantia": False, "error": "No se encontraron registros de kilometraje"}

        if not registro_original or not registro_garantia:
            return {"dentro_garantia": False, "error": "Faltan registros de kilometraje"}

        km_original = registro_original.kilometraje
        km_garantia = registro_garantia.kilometraje
        km_recorridos = km_garantia - km_original

        # Límite de garantía (configurable, por defecto 5000 km)
        limite_garantia_km = 5000  # TODO: Hacer configurable desde ConfiguracionEmpresa

        dentro_garantia = km_recorridos <= limite_garantia_km
        porcentaje_uso = (km_recorridos / limite_garantia_km * 100) if limite_garantia_km > 0 else 0

        mensaje = (
            f"Kilómetros recorridos: {km_recorridos:,} km. "
            f"Límite de garantía: {limite_garantia_km:,} km. "
            f"Uso: {porcentaje_uso:.1f}%"
        )

        return {
            "dentro_garantia": dentro_garantia,
            "kilometros_recorridos": km_recorridos,
            "limite_garantia_km": limite_garantia_km,
            "porcentaje_uso": round(porcentaje_uso, 2),
            "kilometraje_original": km_original,
            "kilometraje_garantia": km_garantia,
            "mensaje": mensaje,
        }

    def listar_garantias_pendientes(self, limite_km: int = 5000) -> List[Dict]:
        """
        Lista documentos que podrían estar relacionados con garantías pendientes.

        Args:
            limite_km: Límite de kilometraje para considerar garantía

        Returns:
            Lista de dicts con información de garantías potenciales
        """
        # Esta función requeriría lógica adicional para identificar
        # qué documentos son garantías. Por ahora retorna estructura básica.
        documentos = Documento.objects.filter(
            empresa=self.empresa, tipo__in=["OT", "PRES"]
        ).select_related("vehiculo", "registro_kilometraje")

        garantias = []
        for doc in documentos:
            try:
                registro_km = doc.registro_kilometraje
                if registro_km:
                    # Aquí se podría agregar lógica para identificar garantías
                    garantias.append(
                        {
                            "documento": doc,
                            "kilometraje": registro_km.kilometraje,
                            "fecha": doc.fecha_emision,
                        }
                    )
            except (ObjectDoesNotExist, AttributeError):
                # Documento no tiene registro_kilometraje asociado
                continue

        return garantias

    # ========================================================================
    # 2. FRECUENCIA DE VISITA Y DESGASTE
    # ========================================================================

    def reporte_frecuencia_visitas(self) -> Dict:
        """
        Genera reporte de frecuencia de visitas y desgaste por vehículo.

        Returns:
            dict: {
                'vehiculos': List[Dict],
                'estadisticas_generales': Dict
            }
        """
        vehiculos = Vehiculo.objects.filter(empresa=self.empresa).prefetch_related(
            "historial_kilometraje"
        )

        vehiculos_data = []
        total_km = 0
        total_visitas = 0

        for vehiculo in vehiculos:
            stats = vehiculo.estadisticas_uso()

            if stats["total_registros"] > 0:
                vehiculos_data.append(
                    {
                        "vehiculo": vehiculo,
                        "patente": vehiculo.patente,
                        "cliente": vehiculo.cliente.nombre if vehiculo.cliente else "N/A",
                        "total_visitas": stats["total_registros"],
                        "km_promedio_entre_servicios": stats["km_promedio_entre_servicios"],
                        "dias_promedio_entre_servicios": stats["dias_promedio_entre_servicios"],
                        "km_total_recorridos": stats["km_total_recorridos"],
                        "fecha_ultima_visita": stats["fecha_ultimo_registro"],
                    }
                )

                total_km += stats["km_total_recorridos"] or 0
                total_visitas += stats["total_registros"]

        # Ordenar por frecuencia (más visitas primero)
        vehiculos_data.sort(key=lambda x: x["total_visitas"], reverse=True)

        return {
            "vehiculos": vehiculos_data,
            "estadisticas_generales": {
                "total_vehiculos": len(vehiculos_data),
                "total_visitas": total_visitas,
                "km_total_promedio": (
                    round(total_km / len(vehiculos_data), 2) if vehiculos_data else 0
                ),
            },
        }

    def reporte_rentabilidad_por_kilometro(self) -> Dict:
        """
        Calcula la rentabilidad por kilómetro recorrido para cada vehículo.

        Returns:
            dict: {
                'vehiculos': List[Dict],
                'ranking_rentabilidad': List[Dict]
            }
        """
        vehiculos = Vehiculo.objects.filter(empresa=self.empresa).prefetch_related(
            "documentos", "historial_kilometraje"
        )

        vehiculos_data = []

        for vehiculo in vehiculos:
            # Calcular total de ventas
            documentos = vehiculo.documentos.filter(empresa=self.empresa, estado="EMITIDO")

            total_ventas = documentos.aggregate(total=Sum("total"))["total"] or Decimal("0")

            # Obtener kilometraje total
            km_total = vehiculo.kilometraje_actual

            # Calcular rentabilidad por km
            rentabilidad_por_km = None
            if km_total > 0:
                rentabilidad_por_km = float(total_ventas) / km_total

            vehiculos_data.append(
                {
                    "vehiculo": vehiculo,
                    "patente": vehiculo.patente,
                    "cliente": vehiculo.cliente.nombre if vehiculo.cliente else "N/A",
                    "total_ventas": total_ventas,
                    "km_total": km_total,
                    "rentabilidad_por_km": (
                        round(rentabilidad_por_km, 2) if rentabilidad_por_km else None
                    ),
                    "total_visitas": documentos.count(),
                }
            )

        # Ordenar por rentabilidad (mayor primero)
        vehiculos_data.sort(
            key=lambda x: x["rentabilidad_por_km"] if x["rentabilidad_por_km"] else 0, reverse=True
        )

        return {"vehiculos": vehiculos_data, "ranking_rentabilidad": vehiculos_data[:10]}  # Top 10

    # ========================================================================
    # 3. RECORDATORIOS DE MANTENIMIENTO PREDICTIVO
    # ========================================================================

    def recordatorios_mantenimiento(
        self, servicio_km: int = 10000, margen_alerta: int = 1000
    ) -> List[Dict]:
        """
        Genera lista de vehículos que están cerca de necesitar mantenimiento.

        Args:
            servicio_km: Kilometraje recomendado para el servicio (ej: cambio de aceite cada 10,000 km)
            margen_alerta: Kilometraje antes del cual alertar (ej: alertar a los 9,000 km)

        Returns:
            Lista de dicts con vehículos que necesitan mantenimiento
        """
        vehiculos = Vehiculo.objects.filter(empresa=self.empresa).prefetch_related(
            "historial_kilometraje"
        )

        recordatorios = []

        for vehiculo in vehiculos:
            km_actual = vehiculo.kilometraje_actual

            if km_actual == 0:
                continue  # Sin historial de kilometraje

            # Obtener último registro
            ultimo_registro = vehiculo.historial_kilometraje.first()
            if not ultimo_registro:
                continue

            # Calcular próximo servicio
            # Buscar el último servicio registrado y calcular cuántos km faltan
            km_ultimo_servicio = ultimo_registro.kilometraje
            km_proximo_servicio = km_ultimo_servicio + servicio_km
            km_faltantes = km_proximo_servicio - km_actual

            # Si está dentro del margen de alerta
            if km_faltantes <= margen_alerta and km_faltantes >= 0:
                recordatorios.append(
                    {
                        "vehiculo": vehiculo,
                        "patente": vehiculo.patente,
                        "cliente": vehiculo.cliente.nombre if vehiculo.cliente else "N/A",
                        "telefono_cliente": vehiculo.cliente.telefono if vehiculo.cliente else None,
                        "email_cliente": vehiculo.cliente.email if vehiculo.cliente else None,
                        "km_actual": km_actual,
                        "km_ultimo_servicio": km_ultimo_servicio,
                        "km_proximo_servicio": km_proximo_servicio,
                        "km_faltantes": km_faltantes,
                        "fecha_ultimo_servicio": ultimo_registro.fecha_registro,
                        "urgencia": "alta" if km_faltantes <= 500 else "media",
                    }
                )

        # Ordenar por urgencia y km faltantes
        recordatorios.sort(key=lambda x: (x["km_faltantes"], x["urgencia"] == "alta"))

        return recordatorios

    # ========================================================================
    # 4. HISTORIAL DE MANTENIMIENTO DETALLADO
    # ========================================================================

    def historial_mantenimiento_vehiculo(self, vehiculo: Vehiculo) -> Dict:
        """
        Genera el historial completo de mantenimiento de un vehículo.
        Similar a un "Libro de Mantenciones Digital".

        Args:
            vehiculo: Instancia de Vehiculo

        Returns:
            dict: {
                'vehiculo': Vehiculo,
                'historial': List[Dict],
                'resumen': Dict
            }
        """
        # Obtener todos los documentos del vehículo con sus registros de kilometraje
        documentos = (
            Documento.objects.filter(empresa=self.empresa, vehiculo=vehiculo)
            .select_related("registro_kilometraje", "cliente", "tecnico_responsable")
            .prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
            .order_by("-fecha_emision")
        )

        historial = []
        total_gastado = Decimal("0")

        for doc in documentos:
            # Obtener kilometraje
            km = None
            try:
                registro_km = doc.registro_kilometraje
                if registro_km:
                    km = registro_km.kilometraje
            except (ObjectDoesNotExist, AttributeError):
                # Documento no tiene registro_kilometraje asociado
                km = None

            # Resumir trabajos realizados
            trabajos = []

            # Repuestos
            for linea in doc.lineas_repuesto.all():
                trabajos.append(f"{linea.cantidad}x {linea.nombre}")

            # Servicios
            for linea in doc.lineas_servicio.all():
                trabajos.append(linea.nombre)

            # Otros servicios
            for linea in doc.lineas_otro_servicio.all():
                trabajos.append(f"{linea.nombre} (externo)")

            resumen_trabajos = ", ".join(trabajos[:5])  # Primeros 5 trabajos
            if len(trabajos) > 5:
                resumen_trabajos += f" (+{len(trabajos) - 5} más)"

            historial.append(
                {
                    "documento": doc,
                    "numero_documento": doc.numero_documento,
                    "tipo": doc.get_tipo_display(),
                    "fecha": doc.fecha_emision,
                    "kilometraje": km,
                    "trabajos_realizados": resumen_trabajos,
                    "monto": doc.total,
                    "tecnico": doc.tecnico_responsable.nombre if doc.tecnico_responsable else "N/A",
                    "estado": doc.estado,
                }
            )

            total_gastado += doc.total

        # Calcular estadísticas
        stats = vehiculo.estadisticas_uso()

        return {
            "vehiculo": vehiculo,
            "historial": historial,
            "resumen": {
                "total_servicios": len(historial),
                "total_gastado": total_gastado,
                "km_promedio_entre_servicios": stats["km_promedio_entre_servicios"],
                "dias_promedio_entre_servicios": stats["dias_promedio_entre_servicios"],
                "fecha_primer_servicio": historial[-1]["fecha"] if historial else None,
                "fecha_ultimo_servicio": historial[0]["fecha"] if historial else None,
            },
        }

    def exportar_historial_vehiculo(self, vehiculo: Vehiculo, formato: str = "dict") -> Dict:
        """
        Exporta el historial de mantenimiento en formato estructurado.
        Útil para exportar a PDF, Excel, o mostrar en Portal del Cliente.

        Args:
            vehiculo: Instancia de Vehiculo
            formato: 'dict', 'json', 'csv' (por ahora solo 'dict')

        Returns:
            dict estructurado con toda la información
        """
        historial_data = self.historial_mantenimiento_vehiculo(vehiculo)

        return {
            "vehiculo": {
                "patente": vehiculo.patente,
                "marca": vehiculo.get_marca_display(),
                "modelo": vehiculo.get_modelo_display(),
                "anio": vehiculo.anio,
                "vin": vehiculo.vin,
                "kilometraje_actual": vehiculo.kilometraje_actual,
            },
            "cliente": {
                "nombre": vehiculo.cliente.nombre if vehiculo.cliente else "N/A",
                "telefono": vehiculo.cliente.telefono if vehiculo.cliente else None,
                "email": vehiculo.cliente.email if vehiculo.cliente else None,
            },
            "historial": historial_data["historial"],
            "resumen": historial_data["resumen"],
            "fecha_generacion": timezone.now().isoformat(),
        }
