from django.shortcuts import redirect
from allauth.account.views import ConfirmEmailView

class CustomEmailConfirmView(ConfirmEmailView):
    def dispatch(self, request, *args, **kwargs):
        if 'key' not in kwargs:
            return redirect('/accounts/confirm-email/empty/')
        return super().dispatch(request, *args, **kwargs)
