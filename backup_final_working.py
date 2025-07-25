# backup_final_working.py - Sistema de Backup Final que Funciona
"""
Sistema de backup final con campos correctos del modelo
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
        logging.FileHandler('backup_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupFinal:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.backup_dir = self.base_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
    def log_auditoria_sistema(self, accion, descripcion, empresa=None):
        """Registrar acción en auditoría del sistema"""
        try:
            # Crear un usuario del sistema si no existe
            sistema_user, created = User.objects.get_or_create(
                username='sistema_backup',
                defaults={
                    'email': 'sistema@egarage.local',
                    'first_name': 'Sistema',
                    'last_name': 'Backup',
                    'is_active': True
                }
            )
            
            # Si no hay empresa específica, usar la primera disponible
            if not empresa:
                empresa = Empresa.objects.first()
            
            if empresa:
                LogAuditoria.objects.create(
                    empresa=empresa,
                    usuario=sistema_user,
                    accion='EXPORT',  # Usar una acción válida del modelo
                    modelo='EMPRESA',
                    descripcion=f"BACKUP: {descripcion}",
                    ip_address='127.0.0.1',
                    user_agent='BackupFinal/1.0'
                )
        except Exception as e:
            logger.error(f"Error al registrar auditoría: {e}")
    
    def crear_backup_empresa(self, empresa):
        """Crear backup completo de una empresa"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Usar nombre_taller que es el campo correcto
            backup_filename = f"backup_{empresa.nombre_taller}_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Iniciando backup para empresa: {empresa.nombre_taller}")
            
            # Recopilar datos de la empresa
            from django.core import serializers
            from taller.models import RepuestoDocumento, ServicioDocumento
            
            backup_data = {
                'empresa': {
                    'id': empresa.id,
                    'nombre_taller': empresa.nombre_taller,
                    'empresa': empresa.empresa,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email,
                    'fecha_inicio': empresa.fecha_inicio.isoformat() if empresa.fecha_inicio else None,
                    'suscripcion_activa': empresa.suscripcion_activa
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
                    
                    repuestos_doc_count = RepuestoDocumento.objects.filter(documento__in=documentos_empresa).count()
                    servicios_doc_count = ServicioDocumento.objects.filter(documento__in=documentos_empresa).count()
                    
                    logger.info(f"  - repuestos_documento: {repuestos_doc_count} registros")
                    logger.info(f"  - servicios_documento: {servicios_doc_count} registros")
                    
                    total_registros += repuestos_doc_count + servicios_doc_count
                    
                except Exception as e:
                    logger.error(f"Error respaldando documentos relacionados: {e}")
                    backup_data['datos']['repuestos_documento'] = []
                    backup_data['datos']['servicios_documento'] = []
            
            # Logs de auditoría de la empresa (últimos 30 días)
            fecha_limite = datetime.now() - timedelta(days=30)
            try:
                logs_empresa = LogAuditoria.objects.filter(
                    empresa=empresa,
                    fecha_hora__gte=fecha_limite
                ).order_by('-fecha_hora')[:500]  # Máximo 500 logs
                
                if logs_empresa.exists():
                    backup_data['datos']['logs_auditoria'] = json.loads(
                        serializers.serialize('json', logs_empresa)
                    )
                    logger.info(f"  - logs_auditoria: {logs_empresa.count()} registros")
                    total_registros += logs_empresa.count()
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
            self.log_auditoria_sistema(
                accion='BACKUP_CREADO',
                descripcion=f"Backup automático creado: {backup_filename}, {total_registros} registros, {size_mb:.2f} MB",
                empresa=empresa
            )
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error al crear backup para {empresa.nombre_taller}: {e}")
            self.log_auditoria_sistema(
                accion='BACKUP_ERROR',
                descripcion=f"Error al crear backup: {str(e)}",
                empresa=empresa
            )
            return None
    
    def limpiar_backups_antiguos(self, dias_retencion=30):
        """Eliminar backups antiguos"""
        try:
            fecha_limite = datetime.now() - timedelta(days=dias_retencion)
            archivos_eliminados = 0
            
            for backup_file in self.backup_dir.glob('backup_*.json'):
                try:
                    # Verificar antigüedad del archivo
                    fecha_archivo = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if fecha_archivo < fecha_limite:
                        backup_file.unlink()
                        archivos_eliminados += 1
                        logger.info(f"Backup antiguo eliminado: {backup_file.name}")
                        
                except Exception as e:
                    logger.warning(f"No se pudo procesar archivo {backup_file.name}: {e}")
                    continue
            
            if archivos_eliminados > 0:
                logger.info(f"Limpieza completada: {archivos_eliminados} backups antiguos eliminados")
                self.log_auditoria_sistema(
                    accion='BACKUP_LIMPIEZA',
                    descripcion=f"Eliminados {archivos_eliminados} backups antiguos (>{dias_retencion} días)"
                )
            
        except Exception as e:
            logger.error(f"Error durante limpieza de backups: {e}")
    
    def crear_backup_completo(self):
        """Crear backup de todas las empresas"""
        logger.info("=== INICIANDO BACKUP FINAL ===")
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
            
            # Limpieza de backups antiguos
            self.limpiar_backups_antiguos()
            
            # Estadísticas finales
            duration = datetime.now() - start_time
            
            logger.info(f"=== BACKUP COMPLETADO ===")
            logger.info(f"Tiempo total: {duration}")
            logger.info(f"Backups exitosos: {backups_exitosos}")
            logger.info(f"Backups fallidos: {backups_fallidos}")
            
            # Log de auditoría general
            self.log_auditoria_sistema(
                accion='BACKUP_PROGRAMADO',
                descripcion=f"Backup final completado: {backups_exitosos} exitosos, {backups_fallidos} fallidos, duración: {duration}"
            )
            
            return backups_exitosos, backups_fallidos
            
        except Exception as e:
            logger.error(f"Error crítico durante backup: {e}")
            self.log_auditoria_sistema(
                accion='BACKUP_ERROR_CRITICO',
                descripcion=f"Error crítico durante backup: {str(e)}"
            )
            return 0, -1

def main():
    """Función principal para ejecución automática"""
    backup = BackupFinal()
    exitosos, fallidos = backup.crear_backup_completo()
    
    print(f"\n✅ RESUMEN DEL BACKUP:")
    print(f"   Exitosos: {exitosos}")
    print(f"   Fallidos: {fallidos}")
    
    if fallidos > 0:
        print("⚠️  Algunos backups fallaron")
        exit(1)  # Código de error para sistemas de monitoreo
    else:
        print("🎉 Todos los backups completados exitosamente")
        exit(0)  # Éxito

if __name__ == "__main__":
    main()
