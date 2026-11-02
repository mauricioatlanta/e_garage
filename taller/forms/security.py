from django.contrib.auth.forms import SetPasswordForm


class MandatoryPasswordChangeForm(SetPasswordForm):
    """Permite definir clave nueva sin exigir repetir la clave temporal."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full rounded border border-cyan-400/30 bg-slate-950 px-3 py-3 text-slate-100",
                    "autocomplete": "new-password",
                }
            )
