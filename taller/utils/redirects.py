from django.shortcuts import redirect

from taller.mixins import safe_next_url


def redirect_next(request, fallback):
    next_url = request.POST.get("next") or request.GET.get("next")
    safe_next = safe_next_url(next_url, allowed_hosts={request.get_host()})
    return redirect(safe_next or fallback)
