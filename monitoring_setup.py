# monitoring_setup.py - Configuración de Monitoreo
"""
Script para configurar monitoreo y alertas en producción
"""
import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from taller.models import Empresa, LogAuditoria, Documento

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.logs_dir = self.base_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configuración de alertas
        self.webhook_url = os.environ.get('SLACK_WEBHOOK_URL', '')
        self.email_alerts = os.environ.get('EMAIL_ALERTS', '').split(',')
        self.sentry_dsn = os.environ.get('SENTRY_DSN', '')
        
    def enviar_alerta_slack(self, mensaje, nivel='info'):
        """Enviar alerta a Slack"""
        if not self.webhook_url:
            return False
            
        try:
            color = {
                'info': '#36a64f',
                'warning': '#ffcc00', 
                'error': '#ff0000',
                'critical': '#8B0000'
            }.get(nivel, '#36a64f')
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"E-Garage - {nivel.upper()}",
                    "text": mensaje,
                    "footer": "E-Garage Monitoring",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error enviando alerta Slack: {e}")
            return False
    
    def verificar_salud_sistema(self):
        """Verificar estado general del sistema"""
        checks = {
            'database': False,
            'empresas': False,
            'usuarios': False,
            'documentos_recientes': False,
            'espacio_disco': False,
            'logs_auditoria': False
        }
        
        problemas = []
        
        try:
            # 1. Verificar conexión a base de datos
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks['database'] = True
                
        except Exception as e:
            problemas.append(f"Error BD: {e}")
        
        try:
            # 2. Verificar empresas activas
            empresas_count = Empresa.objects.count()
            if empresas_count > 0:
                checks['empresas'] = True
            else:
                problemas.append("No hay empresas registradas")
                
        except Exception as e:
            problemas.append(f"Error empresas: {e}")
        
        try:
            # 3. Verificar usuarios con perfil
            from taller.models import PerfilUsuario
            usuarios_con_perfil = PerfilUsuario.objects.count()
            if usuarios_con_perfil > 0:
                checks['usuarios'] = True
            else:
                problemas.append("No hay usuarios con perfil")
                
        except Exception as e:
            problemas.append(f"Error usuarios: {e}")
        
        try:
            # 4. Verificar documentos recientes (últimas 24h)
            from django.utils import timezone
            hace_24h = timezone.now() - timezone.timedelta(hours=24)
            docs_recientes = Documento.objects.filter(created_at__gte=hace_24h).count()
            checks['documentos_recientes'] = docs_recientes >= 0  # Puede ser 0
            
        except Exception as e:
            problemas.append(f"Error documentos: {e}")
        
        try:
            # 5. Verificar espacio en disco
            import shutil
            total, used, free = shutil.disk_usage(self.base_dir)
            free_percent = (free / total) * 100
            
            if free_percent > 10:  # Al menos 10% libre
                checks['espacio_disco'] = True
            else:
                problemas.append(f"Poco espacio en disco: {free_percent:.1f}% libre")
                
        except Exception as e:
            problemas.append(f"Error espacio disco: {e}")
        
        try:
            # 6. Verificar logs de auditoría
            logs_count = LogAuditoria.objects.count()
            checks['logs_auditoria'] = logs_count >= 0
            
        except Exception as e:
            problemas.append(f"Error logs auditoría: {e}")
        
        # Generar reporte
        checks_passed = sum(checks.values())
        total_checks = len(checks)
        health_score = (checks_passed / total_checks) * 100
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'checks': checks,
            'problemas': problemas,
            'status': 'healthy' if health_score >= 90 else 'warning' if health_score >= 70 else 'critical'
        }
        
        return status
    
    def generar_reporte_uso(self):
        """Generar reporte de uso del sistema"""
        try:
            from django.contrib.auth.models import User
            from django.utils import timezone
            
            # Período de análisis (últimos 7 días)
            hace_7_dias = timezone.now() - timezone.timedelta(days=7)
            hace_24h = timezone.now() - timezone.timedelta(hours=24)
            
            reporte = {
                'timestamp': datetime.now().isoformat(),
                'periodo': '7 días',
                'empresas': {
                    'total': Empresa.objects.count(),
                    'activas_7d': 0  # Se calculará con logs
                },
                'usuarios': {
                    'total': User.objects.count(),
                    'activos_7d': 0  # Se calculará con logs
                },
                'documentos': {
                    'total': Documento.objects.count(),
                    'creados_7d': Documento.objects.filter(created_at__gte=hace_7_dias).count(),
                    'creados_24h': Documento.objects.filter(created_at__gte=hace_24h).count()
                },
                'auditoria': {
                    'total_eventos': LogAuditoria.objects.count(),
                    'eventos_7d': LogAuditoria.objects.filter(timestamp__gte=hace_7_dias).count(),
                    'eventos_24h': LogAuditoria.objects.filter(timestamp__gte=hace_24h).count()
                }
            }
            
            # Calcular empresas activas (con logs en los últimos 7 días)
            empresas_activas = LogAuditoria.objects.filter(
                timestamp__gte=hace_7_dias,
                empresa__isnull=False
            ).values('empresa').distinct().count()
            
            reporte['empresas']['activas_7d'] = empresas_activas
            
            # Calcular usuarios activos
            usuarios_activos = LogAuditoria.objects.filter(
                timestamp__gte=hace_7_dias,
                usuario__isnull=False
            ).values('usuario').distinct().count()
            
            reporte['usuarios']['activos_7d'] = usuarios_activos
            
            # Top acciones en auditoría
            top_acciones = LogAuditoria.objects.filter(
                timestamp__gte=hace_7_dias
            ).values('accion').annotate(
                count=models.Count('accion')
            ).order_by('-count')[:5]
            
            reporte['top_acciones'] = list(top_acciones)
            
            return reporte
            
        except Exception as e:
            logger.error(f"Error generando reporte de uso: {e}")
            return None
    
    def verificar_backups(self):
        """Verificar estado de los backups"""
        backup_dir = self.base_dir / 'backups'
        
        if not backup_dir.exists():
            return {
                'status': 'error',
                'mensaje': 'Directorio de backups no existe'
            }
        
        try:
            # Buscar backup más reciente
            backups = list(backup_dir.glob('backup_*.json'))
            
            if not backups:
                return {
                    'status': 'warning',
                    'mensaje': 'No se encontraron backups'
                }
            
            # Ordenar por fecha de modificación
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            backup_mas_reciente = backups[0]
            
            # Verificar antigüedad
            import time
            antiguedad_horas = (time.time() - backup_mas_reciente.stat().st_mtime) / 3600
            
            status = {
                'backup_mas_reciente': backup_mas_reciente.name,
                'antiguedad_horas': round(antiguedad_horas, 1),
                'total_backups': len(backups)
            }
            
            if antiguedad_horas <= 26:  # Menos de 26 horas (permite margen)
                status['status'] = 'ok'
                status['mensaje'] = 'Backups actualizados'
            elif antiguedad_horas <= 48:  # Menos de 48 horas
                status['status'] = 'warning'
                status['mensaje'] = 'Backups algo antiguos'
            else:
                status['status'] = 'error'
                status['mensaje'] = 'Backups muy antiguos'
            
            return status
            
        except Exception as e:
            return {
                'status': 'error',
                'mensaje': f'Error verificando backups: {e}'
            }
    
    def ejecutar_monitoreo_completo(self):
        """Ejecutar todas las verificaciones de monitoreo"""
        logger.info("=== INICIANDO MONITOREO COMPLETO ===")
        
        # 1. Verificar salud del sistema
        salud = self.verificar_salud_sistema()
        logger.info(f"Salud del sistema: {salud['health_score']:.1f}% ({salud['status']})")
        
        # 2. Verificar backups
        backup_status = self.verificar_backups()
        logger.info(f"Estado backups: {backup_status['status']} - {backup_status['mensaje']}")
        
        # 3. Generar reporte de uso
        reporte_uso = self.generar_reporte_uso()
        if reporte_uso:
            logger.info(f"Documentos últimas 24h: {reporte_uso['documentos']['creados_24h']}")
            logger.info(f"Usuarios activos (7d): {reporte_uso['usuarios']['activos_7d']}")
        
        # 4. Enviar alertas si es necesario
        alertas_enviadas = 0
        
        # Alerta por salud del sistema
        if salud['status'] == 'critical':
            mensaje = f"🚨 CRÍTICO: Salud del sistema {salud['health_score']:.1f}%\nProblemas: {', '.join(salud['problemas'])}"
            if self.enviar_alerta_slack(mensaje, 'critical'):
                alertas_enviadas += 1
        elif salud['status'] == 'warning':
            mensaje = f"⚠️ ADVERTENCIA: Salud del sistema {salud['health_score']:.1f}%\nProblemas: {', '.join(salud['problemas'])}"
            if self.enviar_alerta_slack(mensaje, 'warning'):
                alertas_enviadas += 1
        
        # Alerta por backups
        if backup_status['status'] == 'error':
            mensaje = f"🚨 ERROR BACKUP: {backup_status['mensaje']}"
            if self.enviar_alerta_slack(mensaje, 'error'):
                alertas_enviadas += 1
        elif backup_status['status'] == 'warning':
            mensaje = f"⚠️ BACKUP: {backup_status['mensaje']} (Antigüedad: {backup_status.get('antiguedad_horas', 0):.1f}h)"
            if self.enviar_alerta_slack(mensaje, 'warning'):
                alertas_enviadas += 1
        
        # Registrar en auditoría
        try:
            LogAuditoria.objects.create(
                usuario=None,
                accion='MONITOREO_SISTEMA',
                modelo='Sistema',
                objeto_id=None,
                detalles=f"Monitoreo completo - Salud: {salud['health_score']:.1f}%, Backup: {backup_status['status']}, Alertas: {alertas_enviadas}",
                ip_address='127.0.0.1',
                user_agent='MonitoringSetup/1.0'
            )
        except Exception as e:
            logger.error(f"Error registrando auditoría de monitoreo: {e}")
        
        # Guardar reportes en archivos
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Reporte de salud
            with open(self.logs_dir / f'health_report_{timestamp}.json', 'w') as f:
                json.dump(salud, f, indent=2, default=str)
            
            # Reporte de uso
            if reporte_uso:
                with open(self.logs_dir / f'usage_report_{timestamp}.json', 'w') as f:
                    json.dump(reporte_uso, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error guardando reportes: {e}")
        
        logger.info(f"=== MONITOREO COMPLETADO - Alertas enviadas: {alertas_enviadas} ===")
        
        return {
            'salud': salud,
            'backups': backup_status,
            'uso': reporte_uso,
            'alertas_enviadas': alertas_enviadas
        }

def main():
    """Función principal para ejecución automática"""
    monitor = MonitoringSetup()
    resultado = monitor.ejecutar_monitoreo_completo()
    
    # Código de salida basado en el estado
    if resultado['salud']['status'] == 'critical':
        exit(2)  # Crítico
    elif resultado['salud']['status'] == 'warning':
        exit(1)  # Advertencia
    else:
        exit(0)  # OK

if __name__ == "__main__":
    main()
