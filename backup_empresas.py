#!/usr/bin/env python3
"""
Sistema de backup automático por empresa
"""
import os
import django
import json
from datetime import datetime, timedelta
import zipfile
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.core import serializers
from taller.models.empresa import Empresa
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.auditoria import LogAuditoria


class BackupEmpresa:
    """
    Clase para manejar backups automáticos por empresa
    """
    
    def __init__(self, empresa_id=None):
        self.empresa_id = empresa_id
        self.backup_dir = os.path.join(os.getcwd(), 'backups')
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Crear directorio de backups si no existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def crear_backup_empresa(self, empresa_id):
        """
        Crear backup completo de una empresa específica
        """
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{empresa.nombre_taller.replace(' ', '_')}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            print(f"🔄 Creando backup para: {empresa.nombre_taller}")
            
            # 1. Backup de datos de empresa
            self._backup_empresa_data(empresa, backup_path)
            
            # 2. Backup de clientes
            self._backup_clientes(empresa, backup_path)
            
            # 3. Backup de vehículos
            self._backup_vehiculos(empresa, backup_path)
            
            # 4. Backup de documentos
            self._backup_documentos(empresa, backup_path)
            
            # 5. Backup de logs de auditoría
            self._backup_auditoria(empresa, backup_path)
            
            # 6. Crear metadata del backup
            self._crear_metadata(empresa, backup_path, timestamp)
            
            # 7. Comprimir backup
            zip_path = self._comprimir_backup(backup_path, backup_name)
            
            # 8. Limpiar directorio temporal
            shutil.rmtree(backup_path)
            
            print(f"✅ Backup creado: {zip_path}")
            return zip_path
            
        except Empresa.DoesNotExist:
            print(f"❌ Empresa con ID {empresa_id} no encontrada")
            return None
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def _backup_empresa_data(self, empresa, backup_path):
        """Backup datos de la empresa"""
        data = serializers.serialize('json', [empresa], indent=2)
        with open(os.path.join(backup_path, 'empresa.json'), 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"   📋 Empresa exportada")
    
    def _backup_clientes(self, empresa, backup_path):
        """Backup clientes de la empresa"""
        clientes = Cliente.objects.filter(empresa=empresa)
        if clientes.exists():
            data = serializers.serialize('json', clientes, indent=2)
            with open(os.path.join(backup_path, 'clientes.json'), 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"   👥 {clientes.count()} clientes exportados")
        else:
            print(f"   👥 No hay clientes para exportar")
    
    def _backup_vehiculos(self, empresa, backup_path):
        """Backup vehículos de la empresa"""
        try:
            vehiculos = Vehiculo.objects.filter(empresa=empresa)
        if vehiculos.exists():
            data = serializers.serialize('json', vehiculos, indent=2)
            with open(os.path.join(backup_path, 'vehiculos.json'), 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"   🚗 {vehiculos.count()} vehículos exportados")
        else:
            print(f"   🚗 No hay vehículos para exportar")
    
    def _backup_documentos(self, empresa, backup_path):
        """Backup documentos y sus items"""
        documentos = Documento.objects.filter(empresa=empresa)
        if documentos.exists():
            # Exportar documentos
            data = serializers.serialize('json', documentos, indent=2)
            with open(os.path.join(backup_path, 'documentos.json'), 'w', encoding='utf-8') as f:
                f.write(data)
            
            # Exportar repuestos de documentos
            repuestos = RepuestoDocumento.objects.filter(documento__empresa=empresa)
            if repuestos.exists():
                data = serializers.serialize('json', repuestos, indent=2)
                with open(os.path.join(backup_path, 'repuestos_documentos.json'), 'w', encoding='utf-8') as f:
                    f.write(data)
            
            # Exportar servicios de documentos
            servicios = ServicioDocumento.objects.filter(empresa=empresa)
            if servicios.exists():
                data = serializers.serialize('json', servicios, indent=2)
                with open(os.path.join(backup_path, 'servicios_documentos.json'), 'w', encoding='utf-8') as f:
                    f.write(data)
            
            print(f"   📄 {documentos.count()} documentos exportados")
            print(f"   📦 {repuestos.count()} repuestos exportados")
            print(f"   🔧 {servicios.count()} servicios exportados")
        else:
            print(f"   📄 No hay documentos para exportar")
    
    def _backup_auditoria(self, empresa, backup_path):
        """Backup logs de auditoría"""
        logs = LogAuditoria.objects.filter(empresa=empresa)
        if logs.exists():
            data = serializers.serialize('json', logs, indent=2)
            with open(os.path.join(backup_path, 'auditoria.json'), 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"   📊 {logs.count()} logs de auditoría exportados")
        else:
            print(f"   📊 No hay logs de auditoría para exportar")
    
    def _crear_metadata(self, empresa, backup_path, timestamp):
        """Crear metadata del backup"""
        metadata = {
            'empresa': {
                'id': empresa.id,
                'nombre': empresa.nombre_taller,
                'direccion': empresa.direccion,
                'telefono': empresa.telefono,
                'email': empresa.email
            },
            'backup': {
                'fecha_creacion': timestamp,
                'version': '1.0',
                'tipo': 'backup_completo'
            },
            'estadisticas': {
                'clientes': Cliente.objects.filter(empresa=empresa).count(),
                'vehiculos': Vehiculo.objects.filter(empresa=empresa).count(),
                'documentos': Documento.objects.filter(empresa=empresa).count(),
                'repuestos': RepuestoDocumento.objects.filter(documento__empresa=empresa).count(),
                'servicios': ServicioDocumento.objects.filter(empresa=empresa).count(),
                'logs_auditoria': LogAuditoria.objects.filter(empresa=empresa).count()
            }
        }
        
        with open(os.path.join(backup_path, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   ℹ️ Metadata creada")
    
    def _comprimir_backup(self, backup_path, backup_name):
        """Comprimir backup en ZIP"""
        zip_path = f"{backup_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def backup_todas_empresas(self):
        """Crear backup de todas las empresas"""
        empresas = Empresa.objects.all()
        backups_creados = []
        
        print(f"🏭 Iniciando backup de {empresas.count()} empresas...")
        
        for empresa in empresas:
            backup_path = self.crear_backup_empresa(empresa.id)
            if backup_path:
                backups_creados.append(backup_path)
        
        print(f"✅ Backups completados: {len(backups_creados)}")
        return backups_creados
    
    def limpiar_backups_antiguos(self, dias_antiguedad=30):
        """Eliminar backups más antiguos que X días"""
        fecha_limite = datetime.now() - timedelta(days=dias_antiguedad)
        eliminados = 0
        
        for archivo in os.listdir(self.backup_dir):
            if archivo.startswith('backup_') and archivo.endswith('.zip'):
                archivo_path = os.path.join(self.backup_dir, archivo)
                fecha_archivo = datetime.fromtimestamp(os.path.getctime(archivo_path))
                
                if fecha_archivo < fecha_limite:
                    os.remove(archivo_path)
                    eliminados += 1
                    print(f"🗑️ Eliminado backup antiguo: {archivo}")
        
        print(f"🧹 {eliminados} backups antiguos eliminados")
        return eliminados


def main():
    """Función principal para ejecutar backups"""
    print("💾 === SISTEMA DE BACKUP AUTOMÁTICO ===")
    print()
    
    backup_system = BackupEmpresa()
    
    # Opción 1: Backup de todas las empresas
    print("Opción 1: Backup de todas las empresas")
    backup_system.backup_todas_empresas()
    
    print()
    
    # Opción 2: Limpiar backups antiguos
    print("Opción 2: Limpiar backups antiguos (>30 días)")
    backup_system.limpiar_backups_antiguos(30)
    
    print()
    print("🏁 === BACKUP COMPLETADO ===")


if __name__ == '__main__':
    main()
