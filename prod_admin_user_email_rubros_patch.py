from pathlib import Path


path = Path("taller/admin.py")
text = path.read_text()

if "ADMIN_CLIENT_RUBRO_CHOICES" not in text:
    text = text.replace(
        "def generate_admin_temporary_password():\n"
        "    return f\"Eg-{get_random_string(10)}-Aa1!\"\n\n\n"
        "class AdminClienteCreationForm(UserCreationForm):",
        "def generate_admin_temporary_password():\n"
        "    return f\"Eg-{get_random_string(10)}-Aa1!\"\n\n\n"
        "ADMIN_CLIENT_RUBRO_CHOICES = (\n"
        "    (\"WORKSHOP\", \"Taller mecánico\"),\n"
        "    (\"DESARMADURIA\", \"Desarmaduría\"),\n"
        "    (\"TIRE\", \"Vulcanización\"),\n"
        "    (\"BODYSHOP\", \"Bodyshop\"),\n"
        "    (\"RECYCLING\", \"Recicladora\"),\n"
        ")\n\n\n"
        "class AdminClienteCreationForm(UserCreationForm):",
    )

text = text.replace(
    "choices=ConfiguracionEmpresa.RUBRO_CHOICES,\n"
    "        initial=\"WORKSHOP\",\n"
    "        label=\"Rubro principal\",",
    "choices=ADMIN_CLIENT_RUBRO_CHOICES,\n"
    "        initial=\"WORKSHOP\",\n"
    "        label=\"Rubro principal\",",
)

if "def clean_username(self):" not in text:
    text = text.replace(
        "        self.fields[\"password1\"].help_text = (\n"
        "            \"Contraseña temporal autogenerada. Cópiala para enviarla por WhatsApp; \"\n"
        "            \"el cliente deberá cambiarla al primer inicio cuando esté activo el bloqueo obligatorio.\"\n"
        "        )\n\n"
        "    def save(self, commit=True):",
        "        self.fields[\"password1\"].help_text = (\n"
        "            \"Contraseña temporal autogenerada. Cópiala para enviarla por WhatsApp; \"\n"
        "            \"el cliente deberá cambiarla al primer inicio cuando esté activo el bloqueo obligatorio.\"\n"
        "        )\n"
        "        self.fields[\"username\"].label = \"Correo electrónico / usuario\"\n"
        "        self.fields[\"username\"].help_text = \"Debe ser el correo del cliente. Se usará para iniciar sesión.\"\n\n"
        "    def clean_username(self):\n"
        "        username = super().clean_username().strip().lower()\n"
        "        email_field = forms.EmailField()\n"
        "        email_field.clean(username)\n"
        "        return username\n\n"
        "    def clean_email(self):\n"
        "        email = (self.cleaned_data.get(\"email\") or \"\").strip().lower()\n"
        "        return email or self.cleaned_data.get(\"username\", \"\")\n\n"
        "    def save(self, commit=True):",
    )

path.write_text(text)
