#!/usr/bin/env python3
"""
Script de automatización para tareas de mantenimiento
"""
import os
import time
from datetime import datetime

import django
import schedule

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.auditoria import LogAuditoria
from taller.models.empresa import Empresa


def backup_diario():
    """Ejecutar backup diario automático"""
    print(
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Iniciando backup diario..."
    )

    try:
        # Ejecutar backup simple
        os.system("python backup_simple.py")
        print("✅ Backup diario completado")
    except Exception as e:
        print(f"❌ Error en backup diario: {e}")


def limpiar_logs_antiguos():
    """Limpiar logs de auditoría antiguos (más de 90 días)"""
    from datetime import timedelta

    print(
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Limpiando logs antiguos..."
    )

    try:
        fecha_limite = datetime.now() - timedelta(days=90)
        logs_antiguos = LogAuditoria.objects.filter(fecha_hora__lt=fecha_limite)
        cantidad = logs_antiguos.count()

        if cantidad > 0:
            logs_antiguos.delete()
            print(f"✅ {cantidad} logs antiguos eliminados")
        else:
            print("ℹ️ No hay logs antiguos para eliminar")

    except Exception as e:
        print(f"❌ Error limpiando logs: {e}")


def reporte_semanal():
    """Generar reporte semanal automático"""
    print(
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Generando reporte semanal..."
    )

    try:
        # Ejecutar reportes de auditoría
        os.system("python reportes_auditoria.py > reportes/reporte_semanal.txt")
        print("✅ Reporte semanal generado")
    except Exception as e:
        print(f"❌ Error en reporte semanal: {e}")


def verificar_sistema():
    """Verificar estado del sistema"""
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Verificando sistema...")

    try:
        # Verificar empresas y usuarios
        empresas = Empresa.objects.all()
        logs_hoy = LogAuditoria.objects.filter(fecha_hora__date=datetime.now().date())

        print("📊 Estado del sistema:")
        print(f"   - Empresas activas: {empresas.count()}")
        print(f"   - Actividad hoy: {logs_hoy.count()} acciones")

        # Verificar empresas sin actividad reciente
        from datetime import timedelta

        fecha_limite = datetime.now() - timedelta(days=7)

        for empresa in empresas:
            actividad_reciente = LogAuditoria.objects.filter(
                empresa=empresa, fecha_hora__gte=fecha_limite
            ).count()

            if actividad_reciente == 0:
                print(f"⚠️ {empresa.nombre_taller}: Sin actividad en 7 días")

        print("✅ Verificación completada")

    except Exception as e:
        print(f"❌ Error en verificación: {e}")


def configurar_tareas_automaticas():
    """Configurar tareas programadas"""
    print("⚙️ === CONFIGURANDO TAREAS AUTOMÁTICAS ===")

    # Backup diario a las 2:00 AM
    schedule.every().day.at("02:00").do(backup_diario)

    # Limpiar logs antiguos cada domingo a las 3:00 AM
    schedule.every().sunday.at("03:00").do(limpiar_logs_antiguos)

    # Reporte semanal cada lunes a las 8:00 AM
    schedule.every().monday.at("08:00").do(reporte_semanal)

    # Verificación del sistema cada hora
    schedule.every().hour.do(verificar_sistema)

    print("✅ Tareas programadas configuradas:")
    print("   - Backup diario: 02:00")
    print("   - Limpiar logs: Domingos 03:00")
    print("   - Reporte semanal: Lunes 08:00")
    print("   - Verificación: Cada hora")


def ejecutar_mantenimiento_manual():
    """Ejecutar todas las tareas de mantenimiento manualmente"""
    print("🔧 === EJECUTANDO MANTENIMIENTO MANUAL ===")
    print()

    backup_diario()
    print()

    limpiar_logs_antiguos()
    print()

    verificar_sistema()
    print()

    print("🏁 === MANTENIMIENTO COMPLETADO ===")


def modo_daemon():
    """Ejecutar en modo daemon (servicio)"""
    print("🚀 === INICIANDO MODO DAEMON ===")
    configurar_tareas_automaticas()

    print("⏳ Esperando tareas programadas... (Ctrl+C para salir)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Revisar cada minuto
    except KeyboardInterrupt:
        print("\n🛑 Daemon detenido por el usuario")


def main():
    """Función principal"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "daemon":
            modo_daemon()
        elif sys.argv[1] == "manual":
            ejecutar_mantenimiento_manual()
        elif sys.argv[1] == "backup":
            backup_diario()
        elif sys.argv[1] == "verificar":
            verificar_sistema()
        else:
            print("Uso: python automatizacion.py [daemon|manual|backup|verificar]")
    else:
        print("🤖 === SISTEMA AUTOMATIZACIÓN E-GARAGE ===")
        print()
        print("Opciones disponibles:")
        print("  python automatizacion.py daemon    - Ejecutar como servicio")
        print("  python automatizacion.py manual    - Mantenimiento manual")
        print("  python automatizacion.py backup    - Solo backup")
        print("  python automatizacion.py verificar - Solo verificación")
        print()
        print("Ejecutando mantenimiento manual por defecto...")
        print()
        ejecutar_mantenimiento_manual()


if __name__ == "__main__":
    main()
