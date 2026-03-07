# Stub para servidor: taller/middleware/login_country_fix.py

Si en el servidor falta este archivo y Gunicorn entra en crash-loop al cargar MIDDLEWARE, crea el archivo con el contenido de abajo. **Importante:** la clase debe llamarse `FixLoginCountryRedirectMiddleware` (settings_prod.py la referencia así).

## 1) Crear paquete middleware (si no existe)

```bash
sudo mkdir -p /srv/egarage/taller/middleware
sudo touch /srv/egarage/taller/middleware/__init__.py
```

## 2) Crear el archivo (misma clase que en el repo)

```bash
sudo tee /srv/egarage/taller/middleware/login_country_fix.py > /dev/null <<'PY'
# taller/middleware/login_country_fix.py (stub mínimo si el archivo no está en deploy)


def _country_from_path(path: str):
    if not path or len(path) < 4:
        return None
    if path[0] == "/" and path[3] == "/":
        cc = path[1:3].lower()
        if cc.isalpha():
            return cc
    return None


class FixLoginCountryRedirectMiddleware:
    """
    Reescribe Location de redirecciones a /accounts/login/ para incluir prefijo país.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        location = response.get("Location", "")
        if not location:
            return response
        req_cc = _country_from_path(request.path)
        if not req_cc:
            return response
        if location.startswith("/accounts/login/"):
            response["Location"] = location.replace(
                "/accounts/login/", f"/{req_cc}/accounts/login/", 1
            )
        elif location.startswith("/cl/accounts/login/") and req_cc != "cl":
            response["Location"] = location.replace(
                "/cl/accounts/login/", f"/{req_cc}/accounts/login/", 1
            )
        return response
PY
```

## 3) Verificar referencia en settings

En el repo (y en el servidor si usas el mismo código) debe estar:

```text
"taller.middleware.login_country_fix.FixLoginCountryRedirectMiddleware"
```

**No** solo `taller.middleware.login_country_fix` (falta el nombre de la clase).

Comprobar en el servidor:

```bash
grep -n "login_country_fix" /srv/egarage/gestion_taller/settings_prod.py
```

Debe verse algo como: `"taller.middleware.login_country_fix.FixLoginCountryRedirectMiddleware"`.

## 4) Reiniciar Gunicorn

```bash
sudo systemctl restart gunicorn
sudo systemctl status gunicorn --no-pager -l
```

## 5) Probar redirección

```bash
curl -sI https://egarage.cl/compat/settings/ | grep -i "location:"
# Esperado: location: /cl/es/settings/#financial
```
