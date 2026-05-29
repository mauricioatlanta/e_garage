"""
Formularios para gestión de equipo (Team Management)
"""

from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from taller.models.team_member import TeamMember
from taller.services.plan_change_service import PlanLimitValidation


class TeamMemberForm(forms.ModelForm):
    """
    Formulario para crear/editar miembros del equipo.

    Características:
    - Asigna automáticamente la empresa del creador
    - Permite seleccionar el Rol de una lista limpia
    - Valida que el email no esté duplicado
    - No permite crear Owners (solo el creador original es Owner)
    - [CANDADO] Valida los límites del plan activo antes de crear nuevos usuarios
    """

    # Campos del formulario
    email = forms.EmailField(
        required=True, label="Email", help_text="El email se usará como nombre de usuario"
    )

    first_name = forms.CharField(required=True, label="Nombre", max_length=150)

    last_name = forms.CharField(required=True, label="Apellido", max_length=150)

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Contraseña Temporal",
        help_text="El usuario podrá cambiar su contraseña después de iniciar sesión",
        min_length=8,
    )

    rol = forms.ChoiceField(
        choices=[
            ("Admin",    "Administrador"),
            ("Vendedor", "Vendedor"),
        ],
        required=True,
        label="Rol en el Negocio",
        help_text="El rol determina qué permisos tendrá el usuario",
    )

    notas = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Notas",
        help_text="Notas adicionales sobre este miembro del equipo",
    )

    class Meta:
        model = TeamMember
        fields = ["email", "first_name", "last_name", "password", "rol", "notas"]

    def __init__(self, *args, empresa=None, creador=None, **kwargs):
        """
        Inicializa el formulario con empresa y creador.
        """
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        self.creador = creador

        # Si estamos editando, mostrar datos del usuario existente
        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.user.email
            self.fields["email"].widget.attrs["readonly"] = True
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["rol"].initial = self.instance.rol
            self.fields["password"].required = False
            self.fields["password"].help_text = "Dejar vacío para mantener la contraseña actual"

    def clean_email(self):
        """Valida que el email no esté duplicado en la misma empresa"""
        email = self.cleaned_data.get("email").strip().lower()

        if not email:
            raise ValidationError("El email es obligatorio")

        # Verificar si el usuario ya existe
        existing_user = User.objects.filter(email__iexact=email).first()

        if self.instance and self.instance.pk:
            # Estamos editando: permitir si es el mismo usuario
            if existing_user and existing_user != self.instance.user:
                # Verificar si ya está en esta empresa
                if (
                    TeamMember.objects.filter(empresa=self.empresa, user=existing_user)
                    .exclude(pk=self.instance.pk)
                    .exists()
                ):
                    raise ValidationError("Este email ya está registrado en tu equipo.")
        else:
            # Estamos creando: verificar duplicados
            if existing_user:
                # Verificar si ya está en esta empresa
                if TeamMember.objects.filter(
                    empresa=self.empresa, user=existing_user, is_active=True
                ).exists():
                    raise ValidationError("Este usuario ya es miembro de tu equipo.")

        return email

    def clean(self):
        """Validaciones adicionales y candado de suscripciones"""
        cleaned_data = super().clean()

        # Si estamos creando, password es obligatorio
        es_creacion = not (self.instance and self.instance.pk)
        if es_creacion and not cleaned_data.get("password"):
            raise ValidationError("La contraseña es obligatoria al crear un nuevo usuario")

        # 🔒 CANDADO DE PLANES: Si es una creación y tenemos la empresa, validamos los cupos reales
        if es_creacion and self.empresa:
            can_add, count, limite = PlanLimitValidation.can_add_user(self.empresa)
            if not can_add:
                raise ValidationError(
                    f"No puedes agregar más usuarios. Tu plan actual permite un máximo de {limite} "
                    f"usuarios administrativos y actualmente tienes {count} activos."
                )

        return cleaned_data

    def save(self, commit=True):
        """Guarda el miembro del equipo y crea/actualiza el usuario asociado."""
        email = self.cleaned_data["email"].strip().lower()
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        password = self.cleaned_data.get("password")
        rol = self.cleaned_data["rol"]
        notas = self.cleaned_data.get("notas", "")

        # Obtener o crear usuario
        user, created = User.objects.get_or_create(
            email__iexact=email,
            defaults={
                "username": email,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )

        # Si el usuario ya existía, actualizar datos
        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email
            user.save()

        # Si se proporcionó nueva contraseña, actualizarla
        if password:
            user.set_password(password)
            user.save()

        # Obtener o crear TeamMember
        team_member, created = TeamMember.objects.get_or_create(
            user=user,
            empresa=self.empresa,
            defaults={
                "rol": rol,
                "notas": notas,
                "creado_por": self.creador,
            },
        )

        # Si ya existía, actualizar datos
        if not created:
            team_member.rol = rol
            team_member.notas = notas
            team_member.is_active = True
            team_member.save()

        self.instance = team_member
        return team_member


class TeamMemberDeactivateForm(forms.Form):
    """Formulario simple para desactivar un miembro del equipo."""
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
        label="Motivo de Desactivación",
        help_text="Explique brevemente por qué se desactiva a este miembro del equipo",
    )
