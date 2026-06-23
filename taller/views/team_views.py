"""
Vistas para gestión de equipo (Team Management)

Permite al Owner:
- Ver lista de miembros del equipo
- Crear nuevos miembros (Técnicos, Vendedores, Admins)
- Editar miembros existentes
- Desactivar miembros (soft delete)
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from taller.auth.decorators_role import RoleRequiredMixin
from taller.forms.team_forms import TeamMemberForm, TeamMemberDeactivateForm
from taller.models.team_member import TeamMember
from taller.models.empresa import Empresa
from taller.templatetags.country_url import reverse_country_url
from taller.utils.email_helper import get_branded_from_email, get_support_reply_to

log = logging.getLogger(__name__)


class TeamListSuccessUrlMixin:
    """Lista de equipo vive bajo namespace país (p. ej. chile:taller:team:), no 'team:' aislado."""

    def get_success_url(self):
        return reverse_country_url(self.request, "team:team_list")


class TeamListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """
    Lista de miembros del equipo.

    Solo accesible para Owner.
    """

    model = TeamMember
    template_name = "taller/team/team_list.html"
    context_object_name = "miembros"
    allowed_roles = ["Owner"]
    permission_denied_message = "Solo el dueño puede ver el equipo."

    def get_queryset(self):
        """
        Filtra miembros por empresa del usuario autenticado.

        🔒 MULTI-TENANT: Solo muestra miembros de MI empresa.
        """
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return TeamMember.objects.none()

        # Incluir al Owner (usuario principal) en la lista
        queryset = (
            TeamMember.objects.filter(empresa=empresa)
            .select_related("user", "creado_por")
            .order_by("-fecha_creacion")
        )

        return queryset

    def get_context_data(self, **kwargs):
        """Agrega información adicional al contexto"""
        context = super().get_context_data(**kwargs)

        empresa = getattr(self.request.user, "empresa", None)
        if empresa:
            # Agregar información del Owner (usuario principal)
            context["owner"] = empresa.user
            context["empresa"] = empresa

            # Estadísticas
            context["total_miembros"] = (
                TeamMember.objects.filter(empresa=empresa, is_active=True).count() + 1
            )  # +1 por el Owner

            context["total_activos"] = TeamMember.objects.filter(
                empresa=empresa, is_active=True
            ).count()

            context["total_desactivados"] = TeamMember.objects.filter(
                empresa=empresa, is_active=False
            ).count()

        return context


class TeamCreateView(TeamListSuccessUrlMixin, LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """
    Crear nuevo miembro del equipo.

    🔒 SOLO EL OWNER puede crear miembros.
    """

    form_class = TeamMemberForm
    template_name = "taller/team/team_form.html"
    allowed_roles = ["Owner"]
    permission_denied_message = "Solo el dueño puede crear nuevos miembros del equipo."

    def get_form_kwargs(self):
        """Pasa empresa y creador al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = getattr(self.request.user, "empresa", None)
        kwargs["creador"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Guarda el miembro del equipo y envía email de bienvenida"""
        # Capturar contraseña ANTES de que se hashee en form.save()
        # En CreateView, siempre es creación nueva (no hay self.object)
        raw_password = form.cleaned_data.get("password")

        try:
            with transaction.atomic():
                team_member = form.save(commit=True)

                log.info(
                    f"[TeamManagement] Usuario {self.request.user.username} creó miembro del equipo: "
                    f"{team_member.user.email} ({team_member.rol}) en empresa {team_member.empresa.id}"
                )

                # Enviar email de bienvenida solo si es creación nueva y hay contraseña
                if raw_password and team_member:
                    try:
                        self.enviar_email_bienvenida(team_member, raw_password)
                        messages.success(
                            self.request,
                            f"✅ Miembro del equipo creado exitosamente: {team_member.user.get_full_name() or team_member.user.email} ({team_member.rol}). "
                            f"Se ha enviado un email con las credenciales a {team_member.user.email}.",
                        )
                    except Exception as email_error:
                        log.warning(
                            f"[TeamManagement] Miembro creado pero error enviando email: {email_error}",
                            exc_info=True,
                        )
                        messages.success(
                            self.request,
                            f"✅ Miembro del equipo creado exitosamente: {team_member.user.get_full_name() or team_member.user.email} ({team_member.rol}). "
                            f"⚠️ No se pudo enviar el email de bienvenida (verificar configuración SMTP).",
                        )
                else:
                    messages.success(
                        self.request,
                        f"✅ Miembro del equipo creado exitosamente: {team_member.user.get_full_name() or team_member.user.email} ({team_member.rol})",
                    )
        except Exception as e:
            log.error(f"[TeamManagement] Error creando miembro del equipo: {e}", exc_info=True)
            messages.error(self.request, f"❌ Error al crear miembro del equipo: {str(e)}")
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def enviar_email_bienvenida(self, team_member, password):
        """
        Envía email de bienvenida al nuevo miembro del equipo con sus credenciales.

        Args:
            team_member: Instancia de TeamMember creada
            password: Contraseña en texto plano
        """
        empresa = team_member.empresa
        usuario = team_member.user

        # Determinar idioma según país de la empresa
        pais = (empresa.pais or "CL").upper()
        if pais == "US":
            subject = f"Welcome to eGarage - {empresa.nombre_taller} Team"
            lang = "en"
        else:
            subject = f"Bienvenido a eGarage - Equipo de {empresa.nombre_taller}"
            lang = "es"

        # Construir URL de login según país
        if pais == "US":
            login_url = self.request.build_absolute_uri("/us/accounts/login/")
        else:
            login_url = self.request.build_absolute_uri("/cl/accounts/login/")

        # Mapear rol a display name
        rol_display_map = {
            "Admin": "Administrador" if lang == "es" else "Administrator",
            "Vendedor": "Vendedor" if lang == "es" else "Sales",
            "Tecnico": "Técnico" if lang == "es" else "Technician",
            "MIXTO": "Mixto (Vendedor + Técnico)" if lang == "es" else "Mixed (Sales + Technician)",
        }
        rol_display = rol_display_map.get(team_member.rol, team_member.rol)

        # Contexto para el template
        context = {
            "nombre": usuario.first_name or usuario.username,
            "empresa": empresa.nombre_taller,
            "username": usuario.email,
            "password": password,
            "rol": rol_display,
            "login_url": login_url,
            "lang": lang,
        }

        try:
            # Renderizar templates
            html_message = render_to_string(
                "taller/emails/team_welcome.html", context, request=self.request
            )
            plain_message = render_to_string(
                "taller/emails/team_welcome.txt", context, request=self.request
            )

            # Crear y enviar email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                to=[usuario.email],
                reply_to=[get_support_reply_to()],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

            log.info(
                f"[TeamManagement] Email de bienvenida enviado exitosamente a {usuario.email} "
                f"para miembro del equipo de {empresa.nombre_taller}"
            )

        except Exception as e:
            log.error(
                f"[TeamManagement] Error enviando email de bienvenida a {usuario.email}: {e}",
                exc_info=True,
            )
            raise  # Re-raise para que el caller sepa que falló


class TeamUpdateView(TeamListSuccessUrlMixin, LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """
    Editar miembro del equipo existente.

    🔒 SOLO EL OWNER puede editar miembros.
    """

    model = TeamMember
    form_class = TeamMemberForm
    template_name = "taller/team/team_form.html"
    allowed_roles = ["Owner"]
    permission_denied_message = "Solo el dueño puede editar miembros del equipo."

    def get_queryset(self):
        """🔒 MULTI-TENANT: Solo permite editar miembros de MI empresa"""
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return TeamMember.objects.none()

        return TeamMember.objects.filter(empresa=empresa)

    def get_form_kwargs(self):
        """Pasa empresa y creador al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = getattr(self.request.user, "empresa", None)
        kwargs["creador"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                old_rol = (
                    TeamMember.objects.filter(pk=self.object.pk)
                    .values_list("rol", flat=True)
                    .first()
                )
                team_member = form.save(commit=True)
                if old_rol and old_rol != team_member.rol:
                    TeamMember.sincronizar_grupos(team_member.user, team_member.rol, old_rol)

                log.info(
                    f"[TeamManagement] Usuario {self.request.user.username} editó miembro del equipo: "
                    f"{team_member.user.email} en empresa {team_member.empresa.id}"
                )

                messages.success(
                    self.request,
                    f"✅ Miembro del equipo actualizado exitosamente: {team_member.user.get_full_name() or team_member.user.email}",
                )
        except Exception as e:
            log.error(f"[TeamManagement] Error editando miembro del equipo: {e}", exc_info=True)
            messages.error(self.request, f"❌ Error al actualizar miembro del equipo: {str(e)}")
            return self.form_invalid(form)

        return redirect(self.get_success_url())


class TeamDeleteView(TeamListSuccessUrlMixin, LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    """
    Desactivar (soft delete) miembro del equipo.

    🔒 SOLO EL OWNER puede desactivar miembros.

    Nota: No se elimina físicamente, solo se desactiva (is_active=False).
    """

    model = TeamMember
    template_name = "taller/team/team_confirm_delete.html"
    allowed_roles = ["Owner"]
    permission_denied_message = "Solo el dueño puede desactivar miembros del equipo."

    def get_queryset(self):
        """🔒 MULTI-TENANT: Solo permite desactivar miembros de MI empresa"""
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return TeamMember.objects.none()

        return TeamMember.objects.filter(empresa=empresa, is_active=True)

    def post(self, request, *args, **kwargs):
        """Desactiva el miembro en lugar de eliminarlo"""
        team_member = self.get_object()

        # No permitir desactivar al Owner (usuario principal)
        if team_member.user == team_member.empresa.user:
            messages.error(request, "❌ No se puede desactivar al dueño del taller.")
            return redirect(self.get_success_url())

        try:
            with transaction.atomic():
                team_member.is_active = False
                team_member.save(update_fields=["is_active"])

                log.info(
                    f"[TeamManagement] Usuario {request.user.username} desactivó miembro del equipo: "
                    f"{team_member.user.email} en empresa {team_member.empresa.id}"
                )

                messages.warning(
                    request,
                    f"⚠️ Usuario {team_member.user.get_full_name() or team_member.user.email} desactivado exitosamente.",
                )
        except Exception as e:
            log.error(f"[TeamManagement] Error desactivando miembro del equipo: {e}", exc_info=True)
            messages.error(request, f"❌ Error al desactivar miembro del equipo: {str(e)}")

        return redirect(self.get_success_url())


class TeamReactivateView(
    TeamListSuccessUrlMixin, LoginRequiredMixin, RoleRequiredMixin, DeleteView
):
    """
    Reactivar miembro del equipo desactivado.

    🔒 SOLO EL OWNER puede reactivar miembros.
    """

    model = TeamMember
    allowed_roles = ["Owner"]
    permission_denied_message = "Solo el dueño puede reactivar miembros del equipo."

    def get_queryset(self):
        """🔒 MULTI-TENANT: Solo permite reactivar miembros de MI empresa"""
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return TeamMember.objects.none()

        return TeamMember.objects.filter(empresa=empresa, is_active=False)

    def post(self, request, *args, **kwargs):
        """Reactiva el miembro"""
        team_member = self.get_object()

        try:
            with transaction.atomic():
                team_member.is_active = True
                team_member.save(update_fields=["is_active"])

                log.info(
                    f"[TeamManagement] Usuario {request.user.username} reactivó miembro del equipo: "
                    f"{team_member.user.email} en empresa {team_member.empresa.id}"
                )

                messages.success(
                    request,
                    f"✅ Usuario {team_member.user.get_full_name() or team_member.user.email} reactivado exitosamente.",
                )
        except Exception as e:
            log.error(f"[TeamManagement] Error reactivando miembro del equipo: {e}", exc_info=True)
            messages.error(request, f"❌ Error al reactivar miembro del equipo: {str(e)}")

        return redirect(self.get_success_url())
