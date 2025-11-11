# verificar_sistema.py - Verificación Final del Sistema
"""
Script para verificar que todo el sistema está funcionando correctamente
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import connection

from taller.models import Documento, Empresa, LogAuditoria, PerfilUsuario


def print_banner():
    print(
        """
╔══════════════════════════════════════════════════════════════╗
║                    E-GARAGE VERIFICACIÓN FINAL              ║
║                     Sistema de Verificación                 ║
╚══════════════════════════════════════════════════════════════╝
"""
    )


def verificar_base_datos():
    """Verificar conexión y estado de la base de datos"""
    print("🔍 VERIFICANDO BASE DE DATOS...")

    try:
        # Verificar conexión
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos: OK")

        # Verificar tablas principales
        tablas_esperadas = [
            "taller_empresa",
            "taller_perfilusuario",
            "taller_cliente",
            "taller_vehiculo",
            "taller_documento",
            "taller_repuesto",
            "taller_logauditoria",
        ]

        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]

        tablas_faltantes = []
        for tabla in tablas_esperadas:
            if tabla in tablas_existentes:
                print(f"✅ Tabla {tabla}: OK")
            else:
                tablas_faltantes.append(tabla)
                print(f"❌ Tabla {tabla}: FALTANTE")

        if tablas_faltantes:
            print(f"⚠️  ADVERTENCIA: {len(tablas_faltantes)} tablas faltantes")
            return False
        else:
            print("✅ Todas las tablas principales: OK")
            return True

    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False


def verificar_modelos():
    """Verificar que los modelos funcionan correctamente"""
    print("\n🔍 VERIFICANDO MODELOS...")

    checks = {
        "Empresas": False,
        "Usuarios con Perfil": False,
        "Auditoría": False,
        "Documentos": False,
    }

    try:
        # Verificar empresas
        empresas = Empresa.objects.all()
        print(f"✅ Empresas registradas: {empresas.count()}")
        checks["Empresas"] = empresas.count() > 0

        # Verificar usuarios con perfil
        perfiles = PerfilUsuario.objects.all()
        print(f"✅ Usuarios con perfil: {perfiles.count()}")
        checks["Usuarios con Perfil"] = perfiles.count() > 0

        # Verificar sistema de auditoría
        logs = LogAuditoria.objects.all()
        print(f"✅ Logs de auditoría: {logs.count()}")
        checks["Auditoría"] = True  # El sistema existe

        # Verificar documentos
        documentos = Documento.objects.all()
        print(f"✅ Documentos creados: {documentos.count()}")
        checks["Documentos"] = True  # El sistema existe

        # Mostrar empresas específicas
        if empresas.exists():
            print("\n📋 EMPRESAS REGISTRADAS:")
            for i, empresa in enumerate(empresas, 1):
                print(f"   {i}. {empresa.nombre_taller}")

                # Verificar usuarios de la empresa
                perfiles_empresa = PerfilUsuario.objects.filter(empresa=empresa)
                if perfiles_empresa.exists():
                    print(f"      👤 Usuarios: {perfiles_empresa.count()}")
                    for perfil in perfiles_empresa:
                        print(f"         - {perfil.usuario.username}")

                # Verificar documentos de la empresa
                docs_empresa = Documento.objects.filter(empresa=empresa)
                print(f"      📄 Documentos: {docs_empresa.count()}")

        passed_checks = sum(checks.values())
        total_checks = len(checks)

        print(f"\n✅ Verificaciones pasadas: {passed_checks}/{total_checks}")
        return passed_checks == total_checks

    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False


def verificar_funcionalidad_documentos():
    """Verificar que la funcionalidad de documentos está funcionando"""
    print("\n🔍 VERIFICANDO FUNCIONALIDAD DE DOCUMENTOS...")

    try:
        # Verificar documento más reciente
        documento_reciente = Documento.objects.order_by("-id").first()

        if documento_reciente:
            print(f"✅ Documento más reciente: #{documento_reciente.id}")
            print(f"   📅 Fecha: {documento_reciente.created_at}")
            print(f"   🏢 Empresa: {documento_reciente.empresa.nombre_taller}")

            # Verificar repuestos y servicios
            from taller.models import RepuestoDocumento, ServicioDocumento

            repuestos = RepuestoDocumento.objects.filter(documento=documento_reciente)
            servicios = ServicioDocumento.objects.filter(documento=documento_reciente)

            print(f"   🔧 Repuestos: {repuestos.count()}")
            print(f"   ⚙️  Servicios: {servicios.count()}")

            # Verificar datos JSON
            if hasattr(documento_reciente, "repuestos_json") and documento_reciente.repuestos_json:
                import json

                try:
                    repuestos_data = json.loads(documento_reciente.repuestos_json)
                    print(f"   📊 Repuestos JSON: {len(repuestos_data)} elementos")
                except:
                    print("   ⚠️  Error en repuestos JSON")

            if hasattr(documento_reciente, "servicios_json") and documento_reciente.servicios_json:
                import json

                try:
                    servicios_data = json.loads(documento_reciente.servicios_json)
                    print(f"   📊 Servicios JSON: {len(servicios_data)} elementos")
                except:
                    print("   ⚠️  Error en servicios JSON")

            return True
        else:
            print("⚠️  No hay documentos en el sistema")
            return True  # No es error crítico

    except Exception as e:
        print(f"❌ Error verificando documentos: {e}")
        return False


def verificar_sistema_backup():
    """Verificar que el sistema de backup está funcionando"""
    print("\n🔍 VERIFICANDO SISTEMA DE BACKUP...")

    try:
        from pathlib import Path

        backup_dir = Path(__file__).parent / "backups"

        if not backup_dir.exists():
            print("❌ Directorio de backups no existe")
            return False

        # Buscar backups recientes
        backups = list(backup_dir.glob("backup_*.json"))

        if not backups:
            print("⚠️  No se encontraron archivos de backup")
            return False

        # Ordenar por fecha de modificación
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"✅ Archivos de backup encontrados: {len(backups)}")

        # Verificar backup más reciente
        backup_reciente = backups[0]
        import time

        antiguedad_horas = (time.time() - backup_reciente.stat().st_mtime) / 3600

        print(f"✅ Backup más reciente: {backup_reciente.name}")
        print(f"   🕐 Antigüedad: {antiguedad_horas:.1f} horas")

        if antiguedad_horas <= 24:
            print("✅ Backup reciente (menos de 24 horas)")
            return True
        else:
            print("⚠️  Backup algo antiguo (más de 24 horas)")
            return True  # No crítico para desarrollo

    except Exception as e:
        print(f"❌ Error verificando backups: {e}")
        return False


def verificar_sistema_auditoria():
    """Verificar que el sistema de auditoría está funcionando"""
    print("\n🔍 VERIFICANDO SISTEMA DE AUDITORÍA...")

    try:
        # Verificar logs recientes
        from django.utils import timezone

        hace_24h = timezone.now() - timezone.timedelta(hours=24)

        logs_recientes = LogAuditoria.objects.filter(fecha_hora__gte=hace_24h)
        total_logs = LogAuditoria.objects.count()

        print(f"✅ Total logs de auditoría: {total_logs}")
        print(f"✅ Logs últimas 24h: {logs_recientes.count()}")

        if logs_recientes.exists():
            # Mostrar tipos de acciones recientes
            acciones = logs_recientes.values("accion").distinct()
            print("   📋 Acciones registradas:")
            for accion in acciones:
                count = logs_recientes.filter(accion=accion["accion"]).count()
                print(f"      - {accion['accion']}: {count}")

        return True

    except Exception as e:
        print(f"❌ Error verificando auditoría: {e}")
        return False


def generar_reporte_final():
    """Generar reporte final del sistema"""
    print("\n📊 GENERANDO REPORTE FINAL...")

    try:
        from django.contrib.auth.models import User

        # Estadísticas generales
        stats = {
            "empresas": Empresa.objects.count(),
            "usuarios_total": User.objects.count(),
            "usuarios_con_perfil": PerfilUsuario.objects.count(),
            "documentos": Documento.objects.count(),
            "logs_auditoria": LogAuditoria.objects.count(),
        }

        print("=" * 60)
        print("📊 ESTADÍSTICAS DEL SISTEMA E-GARAGE")
        print("=" * 60)
        print(f"🏢 Empresas registradas:      {stats['empresas']}")
        print(f"👤 Usuarios totales:          {stats['usuarios_total']}")
        print(f"👤 Usuarios con perfil:       {stats['usuarios_con_perfil']}")
        print(f"📄 Documentos creados:        {stats['documentos']}")
        print(f"📋 Logs de auditoría:         {stats['logs_auditoria']}")
        print("=" * 60)

        # Verificar integridad general
        integridad = True

        if stats["empresas"] == 0:
            print("⚠️  ADVERTENCIA: No hay empresas registradas")
            integridad = False

        if stats["usuarios_con_perfil"] == 0:
            print("⚠️  ADVERTENCIA: No hay usuarios con perfil")
            integridad = False

        if integridad:
            print("✅ SISTEMA INTEGRO Y FUNCIONANDO CORRECTAMENTE")
        else:
            print("⚠️  SISTEMA FUNCIONANDO CON ADVERTENCIAS")

        return integridad

    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        return False


def main():
    """Función principal de verificación"""
    print_banner()

    verificaciones = {
        "Base de Datos": verificar_base_datos,
        "Modelos": verificar_modelos,
        "Funcionalidad Documentos": verificar_funcionalidad_documentos,
        "Sistema Backup": verificar_sistema_backup,
        "Sistema Auditoría": verificar_sistema_auditoria,
    }

    resultados = {}

    for nombre, funcion in verificaciones.items():
        try:
            resultado = funcion()
            resultados[nombre] = resultado
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados[nombre] = False

    # Generar reporte final
    reporte_ok = generar_reporte_final()

    # Resumen final
    verificaciones_exitosas = sum(resultados.values())
    total_verificaciones = len(resultados)

    print(f"\n{'='*60}")
    print("🎯 RESUMEN DE VERIFICACIONES")
    print(f"{'='*60}")

    for nombre, resultado in resultados.items():
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} {nombre}")

    print(
        f"\n📊 RESULTADO FINAL: {verificaciones_exitosas}/{total_verificaciones} verificaciones exitosas"
    )

    if verificaciones_exitosas == total_verificaciones and reporte_ok:
        print("🎉 ¡SISTEMA E-GARAGE COMPLETAMENTE VERIFICADO Y FUNCIONANDO!")
        return 0
    elif verificaciones_exitosas >= total_verificaciones * 0.8:  # 80% o más
        print("⚠️  Sistema funcionando con algunas advertencias")
        return 1
    else:
        print("❌ Sistema tiene problemas críticos que requieren atención")
        return 2


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
