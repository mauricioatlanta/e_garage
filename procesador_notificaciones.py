# procesador_notificaciones.py - Procesador Automático de Notificaciones
"""
Procesador que se ejecuta periódicamente para enviar notificaciones automáticas
"""
import os
import django
import logging
from datetime import datetime, timedelta

# Configurar Django
# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.utils.notificaciones import (
    procesar_cola_notificaciones,
    verificar_suscripciones_vencimiento,
    verificar_recordatorios_mantenimiento,
    notificar_documento_creado
)
from taller.models.notificacion import NotificacionEnviada
from taller.models.auditoria import LogAuditoria
from taller.models.empresa import Empresa

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('procesador_notificaciones.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcesadorNotificaciones:
    """Procesador principal de notificaciones automáticas"""
    
    def __init__(self):
        self.inicio = datetime.now()
        self.estadisticas = {
            'notificaciones_enviadas': 0,
            'suscripciones_verificadas': 0,
            'recordatorios_enviados': 0,
            'errores': 0
        }
    
    def log_sistema(self, mensaje, nivel='INFO'):
        """Log con timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {nivel}: {mensaje}")
        
        if nivel == 'ERROR':
            logger.error(mensaje)
        elif nivel == 'WARNING':
            logger.warning(mensaje)
        else:
            logger.info(mensaje)
    
    def procesar_cola_pendientes(self):
        """Procesar cola de notificaciones pendientes"""
        self.log_sistema("Procesando cola de notificaciones pendientes...")
        
        try:
            total_enviadas = procesar_cola_notificaciones()
            self.estadisticas['notificaciones_enviadas'] = total_enviadas
            
            if total_enviadas > 0:
                self.log_sistema(f"✅ {total_enviadas} notificaciones enviadas desde cola")
            else:
                self.log_sistema("📭 No hay notificaciones pendientes para enviar")
                
        except Exception as e:
            self.log_sistema(f"❌ Error procesando cola: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def verificar_suscripciones(self):
        """Verificar suscripciones próximas a vencer"""
        self.log_sistema("Verificando suscripciones próximas a vencer...")
        
        try:
            empresas_notificadas = verificar_suscripciones_vencimiento()
            self.estadisticas['suscripciones_verificadas'] = len(empresas_notificadas)
            
            if empresas_notificadas:
                self.log_sistema(f"⚠️  {len(empresas_notificadas)} empresas con suscripción por vencer:")
                for empresa in empresas_notificadas:
                    self.log_sistema(f"   - {empresa}")
            else:
                self.log_sistema("✅ Todas las suscripciones están al día")
                
        except Exception as e:
            self.log_sistema(f"❌ Error verificando suscripciones: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def verificar_mantenimientos(self):
        """Verificar recordatorios de mantenimiento"""
        self.log_sistema("Verificando recordatorios de mantenimiento...")
        
        try:
            recordatorios_enviados = verificar_recordatorios_mantenimiento()
            self.estadisticas['recordatorios_enviados'] = recordatorios_enviados
            
            if recordatorios_enviados > 0:
                self.log_sistema(f"🔧 {recordatorios_enviados} recordatorios de mantenimiento enviados")
            else:
                self.log_sistema("📅 No hay recordatorios de mantenimiento pendientes")
                
        except Exception as e:
            self.log_sistema(f"❌ Error verificando mantenimientos: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def limpiar_notificaciones_antiguas(self, dias=30):
        """Limpiar notificaciones antiguas"""
        self.log_sistema(f"Limpiando notificaciones antiguas (>{dias} días)...")
        
        try:
            fecha_limite = datetime.now() - timedelta(days=dias)
            notificaciones_antiguas = NotificacionEnviada.objects.filter(
                created_at__lt=fecha_limite,
                estado__in=['ENVIADO', 'ENTREGADO', 'ERROR']
            )
            
            count = notificaciones_antiguas.count()
            if count > 0:
                notificaciones_antiguas.delete()
                self.log_sistema(f"🗑️  {count} notificaciones antiguas eliminadas")
            else:
                self.log_sistema("✅ No hay notificaciones antiguas para limpiar")
                
        except Exception as e:
            self.log_sistema(f"❌ Error limpiando notificaciones: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def generar_reporte_notificaciones(self):
        """Generar reporte del estado de notificaciones"""
        self.log_sistema("Generando reporte de notificaciones...")
        
        try:
            # Estadísticas de notificaciones por estado
            estados = {}
            for estado in ['PENDIENTE', 'ENVIADO', 'ENTREGADO', 'ERROR', 'REINTENTO']:
                count = NotificacionEnviada.objects.filter(estado=estado).count()
                estados[estado] = count
            
            # Notificaciones de las últimas 24 horas
            hace_24h = datetime.now() - timedelta(hours=24)
            notif_24h = NotificacionEnviada.objects.filter(
                created_at__gte=hace_24h
            ).count()
            
            # Tipos de notificación más usados
            from django.db.models import Count
            tipos_populares = NotificacionEnviada.objects.values(
                'tipo_notificacion__nombre'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            self.log_sistema("📊 REPORTE DE NOTIFICACIONES:")
            self.log_sistema(f"   📈 Últimas 24h: {notif_24h}")
            self.log_sistema("   📋 Por estado:")
            for estado, count in estados.items():
                if count > 0:
                    self.log_sistema(f"      - {estado}: {count}")
            
            if tipos_populares:
                self.log_sistema("   🏆 Tipos más usados:")
                for tipo in tipos_populares:
                    nombre = tipo['tipo_notificacion__nombre'] or 'Sin nombre'
                    self.log_sistema(f"      - {nombre}: {tipo['count']}")
                
        except Exception as e:
            self.log_sistema(f"❌ Error generando reporte: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def test_envio_notificacion(self):
        """Probar envío de notificación de ejemplo"""
        self.log_sistema("🧪 Realizando prueba de notificación...")
        
        try:
            from taller.utils.notificaciones import NotificacionManager
            from taller.models.documento import Documento
            
            # Buscar empresa y documento para prueba
            empresa = Empresa.objects.first()
            documento = Documento.objects.first()
            
            if not empresa:
                self.log_sistema("⚠️  No hay empresas para probar", 'WARNING')
                return
            
            manager = NotificacionManager(empresa)
            
            # Crear notificación de prueba (sin enviar realmente)
            notificaciones = manager.crear_notificacion(
                evento='DOCUMENTO_CREADO',
                destinatario_email='test@prueba.local',
                destinatario_nombre='Cliente de Prueba',
                destinatario_telefono='+56912345678',
                documento=documento,
                datos_extra={
                    'numero_documento': documento.id if documento else 999,
                    'total': 50000,
                    'es_prueba': True
                }
            )
            
            if notificaciones:
                self.log_sistema(f"✅ Prueba exitosa: {len(notificaciones)} notificaciones creadas")
                for notif in notificaciones:
                    self.log_sistema(f"   - {notif.tipo_notificacion.nombre}: {notif.estado}")
            else:
                self.log_sistema("⚠️  No se crearon notificaciones de prueba", 'WARNING')
                
        except Exception as e:
            self.log_sistema(f"❌ Error en prueba: {e}", 'ERROR')
            self.estadisticas['errores'] += 1
    
    def ejecutar_procesamiento_completo(self):
        """Ejecutar procesamiento completo de notificaciones"""
        self.log_sistema("=" * 60)
        self.log_sistema("🚀 INICIANDO PROCESAMIENTO DE NOTIFICACIONES")
        self.log_sistema("=" * 60)
        
        # 1. Procesar cola de notificaciones pendientes
        self.procesar_cola_pendientes()
        
        # 2. Verificar suscripciones
        self.verificar_suscripciones()
        
        # 3. Verificar recordatorios de mantenimiento
        self.verificar_mantenimientos()
        
        # 4. Limpiar notificaciones antiguas (solo una vez por día)
        hora_actual = datetime.now().hour
        if hora_actual == 2:  # A las 2 AM
            self.limpiar_notificaciones_antiguas()
        
        # 5. Generar reporte
        self.generar_reporte_notificaciones()
        
        # 6. Prueba opcional (solo en desarrollo)
        if os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true':
            self.test_envio_notificacion()
        
        # Estadísticas finales
        duracion = datetime.now() - self.inicio
        
        self.log_sistema("=" * 60)
        self.log_sistema("📊 ESTADÍSTICAS DE PROCESAMIENTO")
        self.log_sistema("=" * 60)
        self.log_sistema(f"⏱️  Duración total: {duracion}")
        self.log_sistema(f"📧 Notificaciones enviadas: {self.estadisticas['notificaciones_enviadas']}")
        self.log_sistema(f"🏢 Suscripciones verificadas: {self.estadisticas['suscripciones_verificadas']}")
        self.log_sistema(f"🔧 Recordatorios enviados: {self.estadisticas['recordatorios_enviados']}")
        self.log_sistema(f"❌ Errores: {self.estadisticas['errores']}")
        
        if self.estadisticas['errores'] == 0:
            self.log_sistema("🎉 PROCESAMIENTO COMPLETADO EXITOSAMENTE")
            return True
        else:
            self.log_sistema("⚠️  PROCESAMIENTO COMPLETADO CON ERRORES")
            return False

def main():
    """Función principal para ejecución automática"""
    procesador = ProcesadorNotificaciones()
    exito = procesador.ejecutar_procesamiento_completo()
    
    if exito:
        exit(0)  # Éxito
    else:
        exit(1)  # Errores encontrados

if __name__ == "__main__":
    main()
