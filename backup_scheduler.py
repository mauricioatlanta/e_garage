# backup_scheduler.py - Sistema de Backup Automatizado
"""
Sistema de backup automático para e_garage
Crear backup diario de cada empresa por separado
"""
import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import django
from django.core.management import call_command
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa, LogAuditoria

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.backup_dir = self.base_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configuración
        self.retention_days = 30
        self.max_backups_per_empresa = 10
        
    def log_auditoria(self, accion, detalles, empresa=None):
        """Registrar acción en auditoría"""
        try:
            LogAuditoria.objects.create(
                usuario=None,  # Sistema automático
                accion=accion,
                modelo='Sistema',
                objeto_id=None,
                detalles=detalles,
                empresa=empresa,
                ip_address='127.0.0.1',
                user_agent='BackupScheduler/1.0'
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
            from taller.models import (
                PerfilUsuario, Cliente, Vehiculo, Mecanico, 
                Documento, RepuestoDocumento, ServicioDocumento,
                Repuesto, Servicio, Categoria
            )
            
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
                ('servicios', Servicio.objects.filter(empresa=empresa)),
                ('categorias', Categoria.objects.filter(empresa=empresa)),
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
                backup_data['datos']['repuestos_documento'] = json.loads(
                    serializers.serialize('json', 
                        RepuestoDocumento.objects.filter(documento__in=documentos_empresa))
                )
                backup_data['datos']['servicios_documento'] = json.loads(
                    serializers.serialize('json', 
                        ServicioDocumento.objects.filter(documento__in=documentos_empresa))
                )
            
            # Logs de auditoría de la empresa (últimos 90 días)
            fecha_limite = datetime.now() - timedelta(days=90)
            logs_empresa = LogAuditoria.objects.filter(
                empresa=empresa,
                timestamp__gte=fecha_limite
            ).order_by('-timestamp')[:1000]  # Máximo 1000 logs
            
            if logs_empresa.exists():
                backup_data['datos']['logs_auditoria'] = json.loads(
                    serializers.serialize('json', logs_empresa)
                )
            
            # Estadísticas del backup
            backup_data['estadisticas'] = {
                'total_registros': total_registros,
                'total_documentos': documentos_empresa.count(),
                'total_logs': logs_empresa.count(),
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
    
    def limpiar_backups_antiguos(self):
        """Eliminar backups antiguos según configuración de retención"""
        try:
            fecha_limite = datetime.now() - timedelta(days=self.retention_days)
            archivos_eliminados = 0
            
            for backup_file in self.backup_dir.glob('backup_*.json'):
                try:
                    # Extraer fecha del nombre del archivo
                    parts = backup_file.stem.split('_')
                    if len(parts) >= 3:
                        fecha_str = f"{parts[-2]}_{parts[-1]}"
                        fecha_backup = datetime.strptime(fecha_str, '%Y%m%d_%H%M%S')
                        
                        if fecha_backup < fecha_limite:
                            backup_file.unlink()
                            archivos_eliminados += 1
                            logger.info(f"Backup antiguo eliminado: {backup_file.name}")
                            
                except (ValueError, IndexError) as e:
                    logger.warning(f"No se pudo procesar fecha del archivo {backup_file.name}: {e}")
                    continue
            
            if archivos_eliminados > 0:
                logger.info(f"Limpieza completada: {archivos_eliminados} backups antiguos eliminados")
                self.log_auditoria(
                    accion='BACKUP_LIMPIEZA',
                    detalles=f"Eliminados {archivos_eliminados} backups antiguos (>{self.retention_days} días)"
                )
            
        except Exception as e:
            logger.error(f"Error durante limpieza de backups: {e}")
    
    def limitar_backups_por_empresa(self):
        """Mantener solo un número máximo de backups por empresa"""
        try:
            empresas = Empresa.objects.all()
            
            for empresa in empresas:
                # Buscar backups de esta empresa
                patron = f"backup_{empresa.nombre}_*.json"
                backups_empresa = list(self.backup_dir.glob(patron))
                
                if len(backups_empresa) > self.max_backups_per_empresa:
                    # Ordenar por fecha (más antiguos primero)
                    backups_empresa.sort(key=lambda x: x.stat().st_mtime)
                    
                    # Eliminar los más antiguos
                    backups_a_eliminar = backups_empresa[:-self.max_backups_per_empresa]
                    
                    for backup in backups_a_eliminar:
                        backup.unlink()
                        logger.info(f"Backup eliminado por límite: {backup.name}")
                    
                    if backups_a_eliminar:
                        self.log_auditoria(
                            accion='BACKUP_LIMITE',
                            detalles=f"Eliminados {len(backups_a_eliminar)} backups por límite máximo ({self.max_backups_per_empresa})",
                            empresa=empresa
                        )
                        
        except Exception as e:
            logger.error(f"Error al limitar backups por empresa: {e}")
    
    def verificar_integridad_backup(self, backup_path):
        """Verificar que el backup es válido"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificaciones básicas
            required_keys = ['empresa', 'timestamp', 'version', 'datos']
            for key in required_keys:
                if key not in data:
                    return False, f"Falta clave requerida: {key}"
            
            # Verificar que hay datos
            if not data['datos']:
                return False, "No hay datos en el backup"
            
            return True, "Backup válido"
            
        except json.JSONDecodeError:
            return False, "JSON inválido"
        except Exception as e:
            return False, f"Error de verificación: {e}"
    
    def crear_backup_completo(self):
        """Crear backup de todas las empresas"""
        logger.info("=== INICIANDO BACKUP PROGRAMADO ===")
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
                    # Verificar integridad
                    valido, mensaje = self.verificar_integridad_backup(backup_path)
                    if valido:
                        backups_exitosos += 1
                    else:
                        logger.error(f"Backup inválido para {empresa.nombre}: {mensaje}")
                        backups_fallidos += 1
                else:
                    backups_fallidos += 1
            
            # Limpieza de backups antiguos
            self.limpiar_backups_antiguos()
            self.limitar_backups_por_empresa()
            
            # Estadísticas finales
            duration = datetime.now() - start_time
            
            logger.info(f"=== BACKUP COMPLETADO ===")
            logger.info(f"Tiempo total: {duration}")
            logger.info(f"Backups exitosos: {backups_exitosos}")
            logger.info(f"Backups fallidos: {backups_fallidos}")
            
            # Log de auditoría general
            self.log_auditoria(
                accion='BACKUP_PROGRAMADO',
                detalles=f"Backup automático completado: {backups_exitosos} exitosos, {backups_fallidos} fallidos, duración: {duration}"
            )
            
            return backups_exitosos, backups_fallidos
            
        except Exception as e:
            logger.error(f"Error crítico durante backup programado: {e}")
            self.log_auditoria(
                accion='BACKUP_ERROR_CRITICO',
                detalles=f"Error crítico durante backup automático: {str(e)}"
            )
            return 0, -1

def main():
    """Función principal para ejecución automática"""
    scheduler = BackupScheduler()
    exitosos, fallidos = scheduler.crear_backup_completo()
    
    if fallidos > 0:
        exit(1)  # Código de error para sistemas de monitoreo
    else:
        exit(0)  # Éxito

if __name__ == "__main__":
    main()
