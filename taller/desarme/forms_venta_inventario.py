# Formulario de confirmación de venta desde inventario (cliente existente o cliente rápido + observaciones).

from django import forms

from taller.models.clientes import Cliente


INPUT_CLASS = (
    "w-full rounded-2xl border border-cyan-400/20 bg-[#07101c]/90 "
    "px-4 py-3 text-sm text-white outline-none transition "
    "focus:border-cyan-300 placeholder:text-slate-500"
)


class ConfirmarVentaDesdeInventarioForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        required=False,
        label="Cliente existente",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )

    crear_cliente_rapido = forms.BooleanField(
        required=False,
        label="Crear cliente rápido",
        widget=forms.HiddenInput(),
    )

    cliente_nombre = forms.CharField(
        required=False,
        label="Nombre cliente",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: Juan Pérez / Taller Los Amigos / Empresa X",
            }
        ),
    )

    cliente_rut = forms.CharField(
        required=False,
        label="RUT / ID",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: 12.345.678-9",
            }
        ),
    )

    cliente_telefono = forms.CharField(
        required=False,
        label="Teléfono",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: +56 9 1234 5678",
            }
        ),
    )

    cliente_email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: cliente@email.com",
            }
        ),
    )

    cliente_direccion = forms.CharField(
        required=False,
        label="Dirección",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Ej: Calle 123, Viña del Mar",
            }
        ),
    )

    observaciones = forms.CharField(
        required=False,
        label="Observaciones",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": INPUT_CLASS,
                "placeholder": "Notas internas de la venta...",
            }
        ),
    )

    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa is not None:
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa).order_by(
                "nombre"
            )

    def clean(self):
        cleaned = super().clean()

        cliente = cleaned.get("cliente")
        crear_cliente_rapido = cleaned.get("crear_cliente_rapido")
        cliente_nombre = (cleaned.get("cliente_nombre") or "").strip()

        if not cliente and not cliente_nombre:
            raise forms.ValidationError(
                "Debes seleccionar un cliente existente o ingresar un cliente rápido."
            )

        if crear_cliente_rapido or cliente_nombre:
            if not cliente_nombre:
                self.add_error("cliente_nombre", "Ingresa el nombre del cliente.")
            cleaned["usar_cliente_rapido"] = True
        else:
            cleaned["usar_cliente_rapido"] = False

        return cleaned
