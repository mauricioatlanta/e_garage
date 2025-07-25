# backup_simple_working.py - Sistema de Backup Funcional
"""
Sistema de backup simplificado que funciona con los modelos disponibles
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa, LogAuditoria, Documento, PerfilUsuario, Cliente, Vehiculo, Mecanico, Repuesto

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_simple_working.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupSimplificado:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.backup_dir = self.base_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
    def log_auditoria(self, accion, detalles, empresa=None):
        """Registrar acción en auditoría"""
        try:
            LogAuditoria.objects.create(
                usuario=None,
                accion=accion,
                modelo='Sistema',
                objeto_id=None,
                detalles=detalles,
                empresa=empresa,
                ip_address='127.0.0.1',
                user_agent='BackupSimplificado/1.0'
            )
        except Exception as e:
            logger.error(f"Error al registrar auditoría: {e}")
    
    def crear_backup_empresa(self, empresa):
        """Crear backup completo de una empresa"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{empresa.nombre}_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Iniciando backup para empresa: {empresa.nombre}")
            
            # Recopilar datos de la empresa
            from django.core import serializers
            from taller.models import RepuestoDocumento, ServicioDocumento
            
            backup_data = {
                'empresa': {
                    'id': empresa.id,
                    'nombre': empresa.nombre,
                    'rut': empresa.rut,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email,
                    'created_at': empresa.created_at.isoformat() if hasattr(empresa, 'created_at') else None
                },
                'timestamp': timestamp,
                'version': '1.0',
                'datos': {}
            }
            
            # Datos relacionados con la empresa
            modelos_a_respaldar = [
                ('perfiles_usuario', PerfilUsuario.objects.filter(empresa=empresa)),
                ('clientes', Cliente.objects.filter(empresa=empresa)),
                ('vehiculos', Vehiculo.objects.filter(empresa=empresa)),
                ('mecanicos', Mecanico.objects.filter(empresa=empresa)),
                ('documentos', Documento.objects.filter(empresa=empresa)),
                ('repuestos', Repuesto.objects.filter(empresa=empresa)),
            ]
            
            total_registros = 0
            for nombre_modelo, queryset in modelos_a_respaldar:
                try:
                    count = queryset.count()
                    if count > 0:
                        data = serializers.serialize('json', queryset)
                        backup_data['datos'][nombre_modelo] = json.loads(data)
                        total_registros += count
                        logger.info(f"  - {nombre_modelo}: {count} registros")
                    else:
                        backup_data['datos'][nombre_modelo] = []
                except Exception as e:
                    logger.error(f"Error al respaldar {nombre_modelo}: {e}")
                    backup_data['datos'][nombre_modelo] = []
            
            # Documentos relacionados (RepuestoDocumento, ServicioDocumento)
            documentos_empresa = Documento.objects.filter(empresa=empresa)
            if documentos_empresa.exists():
                try:
                    backup_data['datos']['repuestos_documento'] = json.loads(
                        serializers.serialize('json', 
                            RepuestoDocumento.objects.filter(documento__in=documentos_empresa))
                    )
                    backup_data['datos']['servicios_documento'] = json.loads(
                        serializers.serialize('json', 
                            ServicioDocumento.objects.filter(documento__in=documentos_empresa))
                    )
                except Exception as e:
                    logger.error(f"Error respaldando documentos relacionados: {e}")
                    backup_data['datos']['repuestos_documento'] = []
                    backup_data['datos']['servicios_documento'] = []
            
            # Logs de auditoría de la empresa (últimos 30 días)
            fecha_limite = datetime.now() - timedelta(days=30)
            try:
                logs_empresa = LogAuditoria.objects.filter(
                    empresa=empresa,
                    timestamp__gte=fecha_limite
                ).order_by('-timestamp')[:500]  # Máximo 500 logs
                
                if logs_empresa.exists():
                    backup_data['datos']['logs_auditoria'] = json.loads(
                        serializers.serialize('json', logs_empresa)
                    )
                    logger.info(f"  - logs_auditoria: {logs_empresa.count()} registros")
            except Exception as e:
                logger.error(f"Error respaldando logs de auditoría: {e}")
                backup_data['datos']['logs_auditoria'] = []
            
            # Estadísticas del backup
            backup_data['estadisticas'] = {
                'total_registros': total_registros,
                'total_documentos': documentos_empresa.count(),
                'total_logs': len(backup_data['datos'].get('logs_auditoria', [])),
                'size_mb': 0  # Se calculará después
            }
            
            # Guardar backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            # Calcular tamaño
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            backup_data['estadisticas']['size_mb'] = round(size_mb, 2)
            
            # Actualizar archivo con el tamaño
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Backup completado: {backup_filename} ({size_mb:.2f} MB)")
            
            # Registrar en auditoría
            self.log_auditoria(
                accion='BACKUP_CREADO',
                detalles=f"Backup automático creado: {backup_filename}, {total_registros} registros, {size_mb:.2f} MB",
                empresa=empresa
            )
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error al crear backup para {empresa.nombre}: {e}")
            self.log_auditoria(
                accion='BACKUP_ERROR',
                detalles=f"Error al crear backup: {str(e)}",
                empresa=empresa
            )
            return None
    
    def crear_backup_completo(self):
        """Crear backup de todas las empresas"""
        logger.info("=== INICIANDO BACKUP SIMPLIFICADO ===")
        start_time = datetime.now()
        
        try:
            empresas = Empresa.objects.all()
            total_empresas = empresas.count()
            backups_exitosos = 0
            backups_fallidos = 0
            
            logger.info(f"Empresas a respaldar: {total_empresas}")
            
            for empresa in empresas:
                backup_path = self.crear_backup_empresa(empresa)
                
                if backup_path:
                    backups_exitosos += 1
                else:
                    backups_fallidos += 1
            
            # Estadísticas finales
            duration = datetime.now() - start_time
            
            logger.info(f"=== BACKUP COMPLETADO ===")
            logger.info(f"Tiempo total: {duration}")
            logger.info(f"Backups exitosos: {backups_exitosos}")
            logger.info(f"Backups fallidos: {backups_fallidos}")
            
            # Log de auditoría general
            self.log_auditoria(
                accion='BACKUP_PROGRAMADO',
                detalles=f"Backup simplificado completado: {backups_exitosos} exitosos, {backups_fallidos} fallidos, duración: {duration}"
            )
            
            return backups_exitosos, backups_fallidos
            
        except Exception as e:
            logger.error(f"Error crítico durante backup: {e}")
            self.log_auditoria(
                accion='BACKUP_ERROR_CRITICO',
                detalles=f"Error crítico durante backup: {str(e)}"
            )
            return 0, -1

def main():
    """Función principal para ejecución automática"""
    backup = BackupSimplificado()
    exitosos, fallidos = backup.crear_backup_completo()
    
    if fallidos > 0:
        exit(1)  # Código de error para sistemas de monitoreo
    else:
        exit(0)  # Éxito

if __name__ == "__main__":
    main()
