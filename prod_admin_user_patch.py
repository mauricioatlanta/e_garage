from pathlib import Path


path = Path("taller/admin.py")
text = path.read_text()

if "class AdminClienteCreationForm" not in text:
    text = text.replace(
        "import json\n\nfrom django.contrib import admin\n",
        "import json\n\n"
        "from django import forms\n"
        "from django.contrib import admin\n"
        "from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin\n"
        "from django.contrib.auth.forms import UserCreationForm\n"
        "from django.contrib.auth.models import User\n",
    )
    text = text.replace(
        "from django.utils import timezone\n",
        "from django.utils import timezone\nfrom django.utils.crypto import get_random_string\n",
    )

    marker = 'admin_site = MyAdminSite(name="myadmin")\n\n\n'
    block = '''
def generate_admin_temporary_password():
    return f"Eg-{get_random_string(10)}-Aa1!"


class AdminClienteCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email del cliente")
    first_name = forms.CharField(required=False, label="Nombre")
    last_name = forms.CharField(required=False, label="Apellido")
    nombre_taller = forms.CharField(required=False, label="Nombre del negocio", initial="Mi Taller")
    telefono = forms.CharField(required=False, label="WhatsApp / Teléfono")
    pais = forms.ChoiceField(choices=Empresa.PAIS_CHOICES, initial="CL", label="País")
    rubro_principal = forms.ChoiceField(
        choices=ConfiguracionEmpresa.RUBRO_CHOICES,
        initial="WORKSHOP",
        label="Rubro principal",
    )
    plan = forms.ChoiceField(choices=Empresa.PLAN_CHOICES, initial="trial", label="Plan")
    dias_prueba = forms.IntegerField(
        min_value=0,
        initial=14,
        label="Días de prueba",
        help_text="Para clientes creados manualmente desde WhatsApp.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        temp_password = generate_admin_temporary_password()
        for field_name in ("password1", "password2"):
            self.fields[field_name].initial = temp_password
            self.fields[field_name].widget = forms.TextInput(
                attrs={"autocomplete": "new-password", "style": "font-family: monospace;"}
            )
        self.fields["password1"].help_text = (
            "Contraseña temporal autogenerada. Cópiala para enviarla por WhatsApp; "
            "el cliente deberá cambiarla al primer inicio cuando esté activo el bloqueo obligatorio."
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            self.save_related_records(user)
        return user

    def _filtered_defaults(self, model, values):
        fields = {field.name for field in model._meta.fields}
        return {key: value for key, value in values.items() if key in fields}

    def save_related_records(self, user):
        dias_prueba = self.cleaned_data.get("dias_prueba") or 0
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio + timezone.timedelta(days=dias_prueba) if dias_prueba else None
        empresa_defaults = self._filtered_defaults(
            Empresa,
            {
                "nombre_taller": self.cleaned_data.get("nombre_taller") or "Mi Taller",
                "email": self.cleaned_data.get("email", ""),
                "telefono": self.cleaned_data.get("telefono", ""),
                "pais": self.cleaned_data.get("pais") or "CL",
                "plan": self.cleaned_data.get("plan") or "trial",
                "dias_prueba": dias_prueba,
                "suscripcion_activa": True,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "trial_started_at": fecha_inicio,
                "trial_ends_at": fecha_fin,
            },
        )
        empresa, _ = Empresa.objects.get_or_create(user=user, defaults=empresa_defaults)
        perfil_defaults = self._filtered_defaults(
            PerfilUsuario,
            {"pais": self.cleaned_data.get("pais") or "CL", "must_change_password": True},
        )
        PerfilUsuario.objects.update_or_create(user=user, defaults=perfil_defaults)
        rubro_principal = self.cleaned_data.get("rubro_principal") or "WORKSHOP"
        ConfiguracionEmpresa.objects.update_or_create(
            empresa=empresa,
            defaults={
                "rubro_principal": rubro_principal,
                "rubros": [rubro_principal],
                "modules_configured_at": timezone.now(),
            },
        )


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = AdminClienteCreationForm
    add_fieldsets = (
        (
            "Acceso del cliente",
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "email", "first_name", "last_name"),
            },
        ),
        (
            "Configuración comercial inicial",
            {
                "classes": ("wide",),
                "fields": ("nombre_taller", "telefono", "pais", "rubro_principal", "plan", "dias_prueba"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and hasattr(form, "save_related_records"):
            form.save_related_records(obj)


'''
    if marker not in text:
        raise SystemExit("No se encontro el punto de insercion admin_site")
    text = text.replace(marker, marker + block)
    path.write_text(text)

