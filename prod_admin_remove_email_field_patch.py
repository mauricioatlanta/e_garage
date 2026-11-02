from pathlib import Path


path = Path("taller/admin.py")
text = path.read_text()

text = text.replace('    email = forms.EmailField(required=False, label="Email del cliente")\n', "")
text = text.replace(
    '        fields = ("username", "email", "first_name", "last_name")\n',
    '        fields = ("username", "first_name", "last_name")\n',
)
text = text.replace(
    '    def clean_email(self):\n'
    '        email = (self.cleaned_data.get("email") or "").strip().lower()\n'
    '        return email or self.cleaned_data.get("username", "")\n\n',
    "",
)
text = text.replace(
    '        user.email = self.cleaned_data.get("email", "")\n',
    '        user.email = self.cleaned_data.get("username", "")\n',
)
text = text.replace(
    '"email": self.cleaned_data.get("email", ""),\n',
    '"email": self.cleaned_data.get("username", ""),\n',
)
text = text.replace(
    '"fields": ("username", "password1", "password2", "email", "first_name", "last_name"),',
    '"fields": ("username", "password1", "password2", "first_name", "last_name"),',
)

path.write_text(text)
