"""
Comando de Django para listar todas las suscripciones activas por país.
Incluye:
- Suscripciones activas (modelo Suscripcion)
- Empresas con suscripciones activas (modelo Empresa)
- Cuentas de prueba (trials)
- Usuarios registrados por país
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion
from taller.models.empresa import Empresa
from taller.models.trial import TrialRegistro


class Command(BaseCommand):
    help = "Lista todas las suscripciones activas por país, incluyendo cuentas de prueba y usuarios registrados"

    def obtener_nombre_pais(self, codigo):
        """Obtiene el nombre del país a partir del código"""
        paises = {
            "CL": "Chile",
            "US": "Estados Unidos",
            "MX": "México",
            "PE": "Perú",
            "CO": "Colombia",
            "EC": "Ecuador",
            "BR": "Brasil",
            "VE": "Venezuela",
        }
        return paises.get(codigo, codigo)

    def formatear_fecha(self, fecha):
        """Formatea una fecha para mostrar"""
        if not fecha:
            return "N/A"
        if hasattr(fecha, "strftime"):
            return fecha.strftime("%Y-%m-%d %H:%M:%S")
        return str(fecha)

    def verificar_suscripcion_vencida(self, suscripcion):
        """Verifica si una suscripción está vencida"""
        if hasattr(suscripcion, "esta_vencida"):
            return suscripcion.esta_vencida()
        if hasattr(suscripcion, "fecha_fin") and suscripcion.fecha_fin:
            return timezone.now().date() > suscripcion.fecha_fin
        return False

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("📊 REPORTE DE SUSCRIPCIONES ACTIVAS"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"Fecha de consulta: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("")

        # Obtener todos los países únicos de las empresas
        paises_empresas = set(Empresa.objects.values_list("pais", flat=True).distinct())
        paises_todos = sorted(paises_empresas) if paises_empresas else ["CL", "US", "MX"]

        # Estadísticas generales
        total_suscripciones = Suscripcion.objects.filter(activa=True).count()
        total_empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()
        total_trials_activos = TrialRegistro.objects.filter(prueba_activa=True).count()
        total_usuarios = User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).count()

        self.stdout.write("📈 ESTADÍSTICAS GENERALES")
        self.stdout.write("-" * 80)
        self.stdout.write(
            f"Total Suscripciones Activas (modelo Suscripcion): {total_suscripciones}"
        )
        self.stdout.write(f"Total Empresas con Suscripción Activa: {total_empresas_activas}")
        self.stdout.write(f"Total Trials Activos: {total_trials_activos}")
        self.stdout.write(f"Total Usuarios Registrados (no staff/superuser): {total_usuarios}")
        self.stdout.write("")

        # Por cada país
        for pais_codigo in paises_todos:
            pais_nombre = self.obtener_nombre_pais(pais_codigo)
            self.stdout.write("=" * 80)
            self.stdout.write(self.style.WARNING(f"🌍 PAÍS: {pais_nombre} ({pais_codigo})"))
            self.stdout.write("=" * 80)

            # 1. Suscripciones del modelo Suscripcion
            self.stdout.write("\n📋 SUSCRIPCIONES (Modelo Suscripcion)")
            self.stdout.write("-" * 80)
            suscripciones = Suscripcion.objects.filter(
                activa=True, user__empresa__pais=pais_codigo
            ).select_related("user", "user__empresa")

            if suscripciones.exists():
                for idx, susc in enumerate(suscripciones, 1):
                    vencida = self.verificar_suscripcion_vencida(susc)
                    estado = "❌ VENCIDA" if vencida else "✅ ACTIVA"
                    es_trial = (
                        susc.es_prueba() if hasattr(susc, "es_prueba") else susc.tipo == "trial"
                    )

                    self.stdout.write(f"\n  {idx}. {estado} - {susc.user.username}")
                    self.stdout.write(f"     Email: {susc.user.email}")
                    self.stdout.write(f"     Tipo: {susc.tipo} {'(TRIAL)' if es_trial else ''}")
                    self.stdout.write(
                        f"     Fecha Inicio: {self.formatear_fecha(susc.fecha_inicio)}"
                    )
                    self.stdout.write(f"     Fecha Fin: {self.formatear_fecha(susc.fecha_fin)}")
                    if hasattr(susc.user, "empresa"):
                        empresa = susc.user.empresa
                        self.stdout.write(f"     Empresa: {empresa.nombre_taller}")
                        self.stdout.write(f"     Ciudad: {empresa.direccion or 'N/A'}")
            else:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  No hay suscripciones activas en este país")
                )

            # 2. Empresas con suscripción activa
            self.stdout.write("\n🏢 EMPRESAS CON SUSCRIPCIÓN ACTIVA")
            self.stdout.write("-" * 80)
            empresas = Empresa.objects.filter(
                pais=pais_codigo, suscripcion_activa=True
            ).select_related("user")

            if empresas.exists():
                for idx, emp in enumerate(empresas, 1):
                    vencida = (
                        timezone.now() > emp.fecha_expiracion
                        if hasattr(emp, "fecha_expiracion")
                        else False
                    )
                    estado = "❌ VENCIDA" if vencida else "✅ ACTIVA"
                    es_trial = emp.plan == "trial"

                    self.stdout.write(f"\n  {idx}. {estado} - {emp.nombre_taller}")
                    self.stdout.write(f"     Usuario: {emp.user.username}")
                    self.stdout.write(f"     Email: {emp.user.email}")
                    self.stdout.write(f"     Plan: {emp.plan} {'(TRIAL)' if es_trial else ''}")
                    self.stdout.write(
                        f"     Fecha Inicio: {self.formatear_fecha(emp.fecha_inicio)}"
                    )
                    self.stdout.write(f"     Fecha Fin: {self.formatear_fecha(emp.fecha_fin)}")
                    self.stdout.write(
                        f"     Días Restantes: {emp.dias_restantes if hasattr(emp, 'dias_restantes') else 'N/A'}"
                    )
                    self.stdout.write(f"     Dirección: {emp.direccion or 'N/A'}")
                    self.stdout.write(f"     Teléfono: {emp.telefono or 'N/A'}")
            else:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  No hay empresas con suscripción activa en este país")
                )

            # 3. Trials activos
            self.stdout.write("\n🧪 CUENTAS DE PRUEBA (TRIALS) ACTIVAS")
            self.stdout.write("-" * 80)
            # Intentar relacionar trials con empresas por email
            trials = TrialRegistro.objects.filter(prueba_activa=True)
            trials_pais = []
            for trial in trials:
                # Buscar si hay una empresa con el mismo email
                empresa_trial = Empresa.objects.filter(email=trial.email, pais=pais_codigo).first()
                if empresa_trial:
                    trials_pais.append((trial, empresa_trial))

            if trials_pais:
                for idx, (trial, empresa) in enumerate(trials_pais, 1):
                    dias_rest = (
                        trial.dias_restantes() if hasattr(trial, "dias_restantes") else "N/A"
                    )
                    self.stdout.write(f"\n  {idx}. ✅ ACTIVA - {trial.nombre}")
                    self.stdout.write(f"     Email: {trial.email}")
                    self.stdout.write(f"     Teléfono: {trial.telefono}")
                    self.stdout.write(
                        f"     Fecha Registro: {self.formatear_fecha(trial.fecha_registro)}"
                    )
                    self.stdout.write(
                        f"     Fecha Activación: {self.formatear_fecha(trial.fecha_activacion)}"
                    )
                    self.stdout.write(f"     Días Restantes: {dias_rest}")
                    self.stdout.write(
                        f"     Empresa: {empresa.nombre_taller if empresa else 'N/A'}"
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  No hay trials activos registrados en este país")
                )

            # 4. Usuarios registrados (no staff/superuser)
            self.stdout.write("\n👥 USUARIOS REGISTRADOS")
            self.stdout.write("-" * 80)
            usuarios = User.objects.filter(
                is_active=True, is_staff=False, is_superuser=False, empresa__pais=pais_codigo
            ).select_related("empresa")

            if usuarios.exists():
                for idx, user in enumerate(usuarios, 1):
                    tiene_suscripcion = hasattr(user, "suscripcion") and user.suscripcion.activa
                    tiene_empresa = hasattr(user, "empresa")
                    estado_susc = (
                        "✅ Con Suscripción" if tiene_suscripcion else "⚠️  Sin Suscripción"
                    )

                    self.stdout.write(f"\n  {idx}. {estado_susc} - {user.username}")
                    self.stdout.write(f"     Email: {user.email}")
                    self.stdout.write(f"     Nombre: {user.first_name} {user.last_name}")
                    self.stdout.write(
                        f"     Fecha Registro: {self.formatear_fecha(user.date_joined)}"
                    )
                    if tiene_empresa:
                        self.stdout.write(f"     Empresa: {user.empresa.nombre_taller}")
                        self.stdout.write(f"     Plan Empresa: {user.empresa.plan}")
            else:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  No hay usuarios registrados en este país")
                )

            self.stdout.write("")

        # Resumen final
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN FINAL"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"Total de países con actividad: {len(paises_todos)}")
        self.stdout.write(
            f"Países: {', '.join([self.obtener_nombre_pais(p) for p in paises_todos])}"
        )
        self.stdout.write("")

        # Listar todos los trials activos (sin importar país)
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🧪 TODAS LAS CUENTAS DE PRUEBA ACTIVAS (TRIALS)"))
        self.stdout.write("=" * 80)
        todos_trials = TrialRegistro.objects.filter(prueba_activa=True).order_by("fecha_registro")
        if todos_trials.exists():
            for idx, trial in enumerate(todos_trials, 1):
                empresa_trial = Empresa.objects.filter(email=trial.email).first()
                pais_trial = empresa_trial.pais if empresa_trial else "N/A"
                self.stdout.write(
                    f"\n  {idx}. {trial.nombre} ({self.obtener_nombre_pais(pais_trial)})"
                )
                self.stdout.write(f"     Email: {trial.email}")
                self.stdout.write(
                    f"     Fecha Registro: {self.formatear_fecha(trial.fecha_registro)}"
                )
                self.stdout.write(
                    f"     Fecha Activación: {self.formatear_fecha(trial.fecha_activacion)}"
                )
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  No hay trials activos en el sistema"))

        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ Reporte completado"))
        self.stdout.write("=" * 80)
