from __future__ import annotations

from functools import wraps


def inject_country_from_host(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if "country_code" not in kwargs:
            kwargs["country_code"] = getattr(request, "country_from_host", None) or "cl"
        return view_func(request, *args, **kwargs)

    return _wrapped
