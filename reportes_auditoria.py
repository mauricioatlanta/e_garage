#!/usr/bin/env python3
"""
Sistema de reportes de auditoría
"""
import os
from datetime import datetime, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from django.contrib.auth.models import User

from taller.models.auditoria import LogAuditoria
from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario


class ReporteAuditoria:
    """
    Generador de reportes de auditoría
    """

    def __init__(self, empresa_id=None):
        self.empresa_id = empresa_id

    def reporte_actividad_usuario(self, usuario_id, dias=30):
        """
        Reporte de actividad de un usuario específico
        """
        fecha_desde = datetime.now() - timedelta(days=dias)
        usuario = User.objects.get(id=usuario_id)
        perfil = PerfilUsuario.objects.get(user=usuario)

        logs = LogAuditoria.objects.filter(
            usuario=usuario, fecha_hora__gte=fecha_desde
        ).order_by("-fecha_hora")

        print("📊 === REPORTE ACTIVIDAD USUARIO ===")
        print(f"👤 Usuario: {usuario.username}")
        print(f"🏢 Empresa: {perfil.empresa.nombre_taller}")
        print(f"📅 Período: Últimos {dias} días")
        print(f"📋 Total actividades: {logs.count()}")
        print()

        # Resumen por acción
        acciones = {}
        for log in logs:
            if log.accion not in acciones:
                acciones[log.accion] = 0
            acciones[log.accion] += 1

        print("🔍 RESUMEN POR ACCIÓN:")
        for accion, cantidad in sorted(acciones.items()):
            print(f"   {accion}: {cantidad}")
        print()

        # Actividades recientes
        print("⏰ ACTIVIDADES RECIENTES:")
        for log in logs[:10]:
            fecha_str = log.fecha_hora.strftime("%d/%m/%Y %H:%M")
            print(f"   {fecha_str} - {log.accion} {log.modelo}: {log.descripcion}")

        return logs

    def reporte_documentos_empresa(self, empresa_id, dias=30):
        """
        Reporte de actividad de documentos por empresa
        """
        fecha_desde = datetime.now() - timedelta(days=dias)
        empresa = Empresa.objects.get(id=empresa_id)

        logs = LogAuditoria.objects.filter(
            empresa=empresa, modelo="DOCUMENTO", fecha_hora__gte=fecha_desde
        ).order_by("-fecha_hora")

        print("📋 === REPORTE DOCUMENTOS EMPRESA ===")
        print(f"🏢 Empresa: {empresa.nombre_taller}")
        print(f"📅 Período: Últimos {dias} días")
        print(f"📄 Total actividades documentos: {logs.count()}")
        print()

        # Actividad por usuario
        usuarios_actividad = {}
        for log in logs:
            username = log.usuario.username
            if username not in usuarios_actividad:
                usuarios_actividad[username] = {
                    "CREATE": 0,
                    "UPDATE": 0,
                    "VIEW": 0,
                    "DELETE": 0,
                }
            if log.accion in usuarios_actividad[username]:
                usuarios_actividad[username][log.accion] += 1

        print("👥 ACTIVIDAD POR USUARIO:")
        for username, actividad in usuarios_actividad.items():
            total = sum(actividad.values())
            print(f"   {username}: {total} actividades")
            for accion, cantidad in actividad.items():
                if cantidad > 0:
                    print(f"     - {accion}: {cantidad}")
        print()

        # Documentos más accedidos
        docs_accedidos = {}
        for log in logs:
            if log.objeto_id:
                doc_id = log.objeto_id
                if doc_id not in docs_accedidos:
                    docs_accedidos[doc_id] = 0
                docs_accedidos[doc_id] += 1

        print("📊 DOCUMENTOS MÁS ACCEDIDOS:")
        docs_ordenados = sorted(
            docs_accedidos.items(), key=lambda x: x[1], reverse=True
        )
        for doc_id, accesos in docs_ordenados[:5]:
            print(f"   Documento ID {doc_id}: {accesos} accesos")

        return logs

    def reporte_seguridad(self, dias=7):
        """
        Reporte de eventos de seguridad
        """
        fecha_desde = datetime.now() - timedelta(days=dias)

        # Intentos de acceso denegado
        accesos_denegados = LogAuditoria.objects.filter(
            modelo="ACCESO_DENEGADO", fecha_hora__gte=fecha_desde
        ).order_by("-fecha_hora")

        # Logins
        logins = LogAuditoria.objects.filter(
            accion="LOGIN", fecha_hora__gte=fecha_desde
        ).order_by("-fecha_hora")

        print("🔒 === REPORTE SEGURIDAD ===")
        print(f"📅 Período: Últimos {dias} días")
        print(f"❌ Accesos denegados: {accesos_denegados.count()}")
        print(f"🔑 Logins: {logins.count()}")
        print()

        if accesos_denegados.exists():
            print("⚠️ INTENTOS DE ACCESO DENEGADO:")
            for log in accesos_denegados[:10]:
                fecha_str = log.fecha_hora.strftime("%d/%m/%Y %H:%M")
                ip = log.ip_address or "IP desconocida"
                print(
                    f"   {fecha_str} - {log.usuario.username} ({ip}): {log.descripcion}"
                )
            print()

        # IPs más activas
        ips_actividad = {}
        for log in LogAuditoria.objects.filter(fecha_hora__gte=fecha_desde):
            if log.ip_address:
                if log.ip_address not in ips_actividad:
                    ips_actividad[log.ip_address] = 0
                ips_actividad[log.ip_address] += 1

        if ips_actividad:
            print("🌐 IPs MÁS ACTIVAS:")
            ips_ordenadas = sorted(
                ips_actividad.items(), key=lambda x: x[1], reverse=True
            )
            for ip, actividad in ips_ordenadas[:5]:
                print(f"   {ip}: {actividad} acciones")

        return accesos_denegados, logins

    def reporte_uso_sistema(self, dias=30):
        """
        Reporte general de uso del sistema
        """
        fecha_desde = datetime.now() - timedelta(days=dias)

        total_logs = LogAuditoria.objects.filter(fecha_hora__gte=fecha_desde)

        print("📈 === REPORTE USO SISTEMA ===")
        print(f"📅 Período: Últimos {dias} días")
        print(f"📊 Total actividades: {total_logs.count()}")
        print()

        # Actividad por empresa
        empresas_actividad = {}
        for log in total_logs:
            empresa = log.empresa.nombre_taller
            if empresa not in empresas_actividad:
                empresas_actividad[empresa] = 0
            empresas_actividad[empresa] += 1

        print("🏢 ACTIVIDAD POR EMPRESA:")
        empresas_ordenadas = sorted(
            empresas_actividad.items(), key=lambda x: x[1], reverse=True
        )
        for empresa, actividad in empresas_ordenadas:
            print(f"   {empresa}: {actividad} actividades")
        print()

        # Actividad por día
        actividad_diaria = {}
        for log in total_logs:
            fecha = log.fecha_hora.date()
            if fecha not in actividad_diaria:
                actividad_diaria[fecha] = 0
            actividad_diaria[fecha] += 1

        print("📅 ACTIVIDAD POR DÍA (últimos 7 días):")
        fechas_ordenadas = sorted(
            actividad_diaria.items(), key=lambda x: x[0], reverse=True
        )
        for fecha, actividad in fechas_ordenadas[:7]:
            fecha_str = fecha.strftime("%d/%m/%Y")
            print(f"   {fecha_str}: {actividad} actividades")

        # Usuarios más activos
        usuarios_actividad = {}
        for log in total_logs:
            username = log.usuario.username
            if username not in usuarios_actividad:
                usuarios_actividad[username] = 0
            usuarios_actividad[username] += 1

        print()
        print("👤 USUARIOS MÁS ACTIVOS:")
        usuarios_ordenados = sorted(
            usuarios_actividad.items(), key=lambda x: x[1], reverse=True
        )
        for username, actividad in usuarios_ordenados[:5]:
            print(f"   {username}: {actividad} actividades")

        return total_logs

    def exportar_reporte_csv(self, logs, nombre_archivo):
        """
        Exportar logs a archivo CSV
        """
        import csv

        with open(nombre_archivo, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Fecha",
                    "Usuario",
                    "Empresa",
                    "Acción",
                    "Modelo",
                    "Objeto ID",
                    "Descripción",
                    "IP",
                ]
            )

            for log in logs:
                writer.writerow(
                    [
                        log.fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
                        log.usuario.username,
                        log.empresa.nombre_taller,
                        log.accion,
                        log.modelo,
                        log.objeto_id or "",
                        log.descripcion,
                        log.ip_address or "",
                    ]
                )

        print(f"📁 Reporte exportado a: {nombre_archivo}")


def main():
    """Función principal para generar reportes"""
    print("📊 === SISTEMA REPORTES AUDITORÍA ===")
    print()

    reporte = ReporteAuditoria()

    # Reporte general de uso
    print("1️⃣ Reporte general de uso del sistema")
    reporte.reporte_uso_sistema(30)
    print()

    # Reporte de seguridad
    print("2️⃣ Reporte de seguridad")
    reporte.reporte_seguridad(7)
    print()

    # Reportes por empresa (si hay empresas)
    empresas = Empresa.objects.all()
    if empresas.exists():
        print("3️⃣ Reportes por empresa")
        for empresa in empresas[:2]:  # Primeras 2 empresas
            print(f"\n--- {empresa.nombre_taller} ---")
            reporte.reporte_documentos_empresa(empresa.pk, 15)

    print()
    print("🏁 === REPORTES COMPLETADOS ===")


if __name__ == "__main__":
    main()
