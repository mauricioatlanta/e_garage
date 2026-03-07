"""
Panel admin de suscriptores (compat con gestion_taller/urls.py).

Rutas legacy:
- /admin/suscriptores/                         -> admin_suscriptores (listado)
- /admin/suscriptores/<empresa_id>/            -> detalle_suscriptor (real: analytics.admin_views)
- /admin/suscriptores/<empresa_id>/extender/   -> extender_suscripcion_ajax
- /admin/suscriptores/<empresa_id>/actualizar-telefono/ -> actualizar_telefono_ajax
"""

from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils.html import escape
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse

from taller.models import Empresa
from taller.analytics.admin_views import detalle_suscriptor  # noqa: F401 — re-export para urls


@staff_member_required
@require_GET
def admin_suscriptores(request):
    """
    Listado mínimo funcional de empresas (suscriptores) con acceso a detalle.
    No depende de templates para evitar 500 si faltan HTMLs.
    """
    qs = Empresa.objects.all().order_by("-id")[:500]  # seguridad básica

    rows = []
    for e in qs:
        detalle_url = f"/admin/suscriptores/{e.id}/"
        nombre = escape(
            getattr(e, "nombre_taller", "")
            or getattr(e, "nombre", "")
            or getattr(e, "name", "")
            or f"Empresa {e.id}"
        )
        pais = escape(getattr(e, "pais", "") or "")
        email = escape(getattr(e, "email", "") or "")
        rows.append(
            f"<tr>"
            f"<td>{e.id}</td>"
            f"<td><a href='{detalle_url}'>{nombre}</a></td>"
            f"<td>{pais}</td>"
            f"<td>{email}</td>"
            f"</tr>"
        )

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Admin Suscriptores</title>
      <style>
        body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu; padding:24px;}}
        table{{border-collapse:collapse; width:100%;}}
        th,td{{border:1px solid #ddd; padding:10px; text-align:left;}}
        th{{background:#f6f6f6;}}
        a{{text-decoration:none;}}
        .hint{{color:#666; margin-bottom:12px;}}
      </style>
    </head>
    <body>
      <h1>Admin Suscriptores</h1>
      <div class="hint">Listado básico (máx 500). Click en una empresa para ver detalle.</div>
      <table>
        <thead>
          <tr><th>ID</th><th>Empresa</th><th>País</th><th>Email</th></tr>
        </thead>
        <tbody>
          {''.join(rows) if rows else '<tr><td colspan="4">Sin empresas</td></tr>'}
        </tbody>
      </table>
    </body>
    </html>
    """
    return HttpResponse(html)


@staff_member_required
@require_POST
def extender_suscripcion_ajax(request, empresa_id: int):
    """
    POST: dias=30 (default)
    """
    try:
        dias_raw = request.POST.get("dias", "30")
        dias = int(dias_raw)
        if dias <= 0 or dias > 3650:
            return JsonResponse({"ok": False, "error": "dias inválido"}, status=400)

        empresa = Empresa.objects.get(id=empresa_id)
        empresa.extender_suscripcion(dias=dias, enviar_notificacion=True)
        return JsonResponse({"ok": True, "empresa_id": empresa_id, "dias": dias})
    except Empresa.DoesNotExist:
        return JsonResponse({"ok": False, "error": "empresa no encontrada"}, status=404)
    except ValueError:
        return JsonResponse({"ok": False, "error": "dias debe ser entero"}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@staff_member_required
@require_POST
def actualizar_telefono_ajax(request, empresa_id: int):
    """
    POST: telefono=...
    Intenta setear un campo común si existe.
    """
    telefono = (request.POST.get("telefono") or request.POST.get("phone") or "").strip()
    if not telefono:
        return JsonResponse({"ok": False, "error": "telefono requerido"}, status=400)

    try:
        empresa = Empresa.objects.get(id=empresa_id)

        for field in ("telefono", "phone", "telefono_contacto", "phone_number"):
            if hasattr(empresa, field):
                setattr(empresa, field, telefono)
                empresa.save(update_fields=[field])
                return JsonResponse({"ok": True, "empresa_id": empresa_id, "field": field})

        return JsonResponse(
            {"ok": False, "error": "Empresa no tiene campo teléfono conocido"},
            status=400,
        )
    except Empresa.DoesNotExist:
        return JsonResponse({"ok": False, "error": "empresa no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


__all__ = [
    "admin_suscriptores",
    "detalle_suscriptor",
    "extender_suscripcion_ajax",
    "actualizar_telefono_ajax",
]
