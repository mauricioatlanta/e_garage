from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from taller.models.documento import Documento

class Command(BaseCommand):
    help = "Intenta editar 1-3 documentos existentes y reporta si el formulario falla y por qué."

    def add_arguments(self, parser):
        parser.add_argument("--user", default="testuser_usa")
        parser.add_argument("--limit", type=int, default=3)

    def handle(self, *args, **opts):
        U = get_user_model()
        user = U.objects.filter(username=opts["user"]).first() or U.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No hay usuarios."))
            return

        c = Client()
        c.force_login(user)

        qs = Documento.objects.all().order_by("-id")[:opts["limit"]]
        if not qs:
            self.stdout.write(self.style.ERROR("No hay documentos para probar."))
            return

        for doc in qs:
            # Usar la nueva ruta unificada del sistema
            url = reverse("documentos:documento_editar", args=[doc.pk])  # form/{pk}/
            
            self.stdout.write(f"[DOC {doc.pk}] Probando edición de {doc.tipo}-{doc.numero} (empresa: {doc.empresa.nombre_taller if doc.empresa else 'N/A'})")
            
            # Payload mínimo usando valores actuales del doc:
            payload = {
                "tipo": doc.tipo,  # ⚠️ si 'tipo' es read-only en UI, el form aún lo espera
                "fecha_emision": (doc.fecha_emision or timezone.now().date()).isoformat(),
                "cliente": getattr(doc.cliente, "pk", ""),
                "vehiculo": getattr(doc.vehiculo, "pk", ""),
                "tecnico_responsable": getattr(doc.tecnico_responsable, "pk", "") or "",
                "pagado": "on" if getattr(doc, "pagado", False) else "",
            }
            # Simula US tax widgets si aplica
            payload["apply_sales_tax"] = "1" if getattr(doc, "country", None) == "US" else ""
            payload["sales_tax_rate"] = "8.5"  # tolerante; el server normaliza

            # Nota: si usas arrays de líneas por JS, este probe solo verifica campos del Documento.
            # Si el form exige líneas, añade aquí un mínimo según tu protocolo.

            resp = c.post(url, payload, follow=True)
            status = resp.status_code
            ok = (status in (302, 200)) and ("Corrige los errores" not in (resp.content.decode(errors="ignore")))
            self.stdout.write(f"[DOC {doc.pk}] POST {url} -> status={status} ok={ok}")

            # Si fue inválido y es un TemplateResponse, intenta extraer el contexto
            try:
                ctx = getattr(resp, "context", None)
                if ctx and "form" in ctx and ctx["form"].errors:
                    self.stdout.write(self.style.WARNING(f"Errors: {ctx['form'].errors.as_json()}"))
                else:
                    # Rely on server logs (previo paso)
                    self.stdout.write(self.style.WARNING("Sin ctx de errores; revisa logs del servidor."))
            except Exception:
                self.stdout.write(self.style.WARNING("No se pudo leer contexto; revisa logs del servidor."))
