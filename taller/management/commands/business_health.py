"""
Métricas operativas / SaaS a partir de User y Empresa (sin herramientas externas).

Uso:
  python manage.py business_health
  python manage.py business_health --days 7
  python manage.py business_health --exclude-staff
  python manage.py business_health --assume-arpu 20
  python manage.py business_health --verbose
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum
from django.utils import timezone

from taller.models import Empresa

PAID_PLANS = ("basic", "premium", "enterprise")


class Command(BaseCommand):
    help = (
        "Resumen de salud del negocio: usuarios, empresas, suscripciones y MRR desde valor_mensual."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Ventana para 'nuevos' usuarios y empresas (por defecto 30).",
        )
        parser.add_argument(
            "--exclude-staff",
            action="store_true",
            help="Excluir is_staff del conteo de usuarios.",
        )
        parser.add_argument(
            "--assume-arpu",
            type=float,
            default=None,
            metavar="USD",
            help="Opcional: proyectar ingreso de nuevos usuarios como nuevos_usuarios * ARPU (solo informativo).",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Lista empresas activas ambiguas (no trial según comando, ni basic/premium/enterprise).",
        )

    def handle(self, *args, **options):
        days = max(1, options["days"])
        exclude_staff = options["exclude_staff"]
        assume_arpu = options["assume_arpu"]
        verbose = options["verbose"]

        User = get_user_model()
        now = timezone.now()
        since = now - timedelta(days=days)

        user_qs = User.objects.all()
        if exclude_staff:
            user_qs = user_qs.filter(is_staff=False)

        total_users = user_qs.count()
        new_users = user_qs.filter(date_joined__gte=since).count()

        emp_qs = Empresa.objects.all()
        total_empresas = emp_qs.count()
        new_empresas = emp_qs.filter(fecha_inicio__gte=since).count()

        active_sub = emp_qs.filter(suscripcion_activa=True).count()
        paying = emp_qs.filter(suscripcion_activa=True, plan__in=PAID_PLANS)
        paying_count = paying.count()

        trial_filter = Q(plan="trial")
        try:
            Empresa._meta.get_field("is_trial")
        except FieldDoesNotExist:
            pass
        else:
            trial_filter = trial_filter | Q(is_trial=True)

        trial_active = emp_qs.filter(suscripcion_activa=True).filter(trial_filter).count()

        active_emp = emp_qs.filter(suscripcion_activa=True)
        ambiguous_active = active_emp.exclude(plan__in=PAID_PLANS).exclude(trial_filter)
        ambiguous_count = ambiguous_active.count()

        conversion_pct = (paying_count / total_empresas * 100) if total_empresas else 0.0

        self.stdout.write(self.style.SUCCESS("--- eGarage · business_health ---"))
        self.stdout.write(f"Ventana: últimos {days} días (hasta {now:%Y-%m-%d %H:%M %Z})")
        if exclude_staff:
            self.stdout.write("(Usuarios: sin staff)")
        self.stdout.write("")
        self.stdout.write(f"Usuarios totales:           {total_users}")
        self.stdout.write(f"Usuarios nuevos ({days}d):   {new_users}")
        self.stdout.write("")
        self.stdout.write(f"Empresas (talleres) totales: {total_empresas}")
        self.stdout.write(f"Empresas nuevas ({days}d):   {new_empresas}")
        self.stdout.write(f"Suscripción activa:          {active_sub}")
        self.stdout.write(f"En trial (activa):           {trial_active}")
        self.stdout.write(f"Planes de pago activos:      {paying_count}")
        self.stdout.write(f"Tasa conversión (pago/total empresas): {conversion_pct:.1f}%")
        if ambiguous_count:
            self.stdout.write(
                self.style.WARNING(
                    f"Activas sin trial ni plan de pago (revisar `plan` en BD): {ambiguous_count}"
                )
            )
        self.stdout.write(self.style.MIGRATE_LABEL("-------------------------------"))

        self.stdout.write("Distribución `plan` (solo suscripción activa):")
        plan_rows = active_emp.values("plan").annotate(n=Count("id")).order_by("-n", "plan")
        plan_labels = dict(Empresa.PLAN_CHOICES)
        for row in plan_rows:
            p = row["plan"] or "(vacío)"
            label = plan_labels.get(row["plan"], "")
            suffix = f" — {label}" if label else ""
            self.stdout.write(f"  {p}: {row['n']}{suffix}")

        self.stdout.write(self.style.MIGRATE_LABEL("-------------------------------"))

        self.stdout.write("MRR declarado (suma valor_mensual, solo planes de pago activos):")
        any_mrr = False
        for code, label in Empresa.MONEDA_CHOICES:
            total = paying.filter(moneda=code).aggregate(s=Sum("valor_mensual"))["s"]
            if total is not None and total > 0:
                any_mrr = True
                self.stdout.write(f"  {label}: {total}")

        if paying_count and not any_mrr:
            self.stdout.write(
                self.style.WARNING(
                    "  (Sin valor_mensual > 0 en planes de pago; revisa datos en admin.)"
                )
            )

        if verbose and ambiguous_count:
            self.stdout.write(self.style.MIGRATE_LABEL("-------------------------------"))
            self.stdout.write(
                "Detalle activas ambiguas (id, nombre_taller, plan, is_trial, valor_mensual):"
            )
            qs = ambiguous_active.order_by("id")
            for e in qs.select_related("user"):
                it = getattr(e, "is_trial", None)
                self.stdout.write(
                    f"  #{e.id} {e.nombre_taller!r} plan={e.plan!r} is_trial={it!r} "
                    f"valor_mensual={e.valor_mensual} {e.moneda}"
                )

        if assume_arpu is not None and assume_arpu > 0:
            projected = new_users * assume_arpu
            self.stdout.write(self.style.MIGRATE_LABEL("-------------------------------"))
            self.stdout.write(
                f"Proyección informal: {new_users} nuevos usuarios × {assume_arpu} = {projected} (unidades ARPU)"
            )
