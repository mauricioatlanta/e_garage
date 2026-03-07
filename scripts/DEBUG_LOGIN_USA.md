# Debug login USA (/us/login/)

## A) Arreglar el `!` en la contraseña (bash history expansion)

Si la contraseña contiene `!`, bash interpreta `!texto` como historial y rompe la variable. **PASS queda vacía o mal** y el POST va con password incorrecta.

**Elige una:**

- **Opción 1 (recomendada):** desactivar history expansion en la sesión
  ```bash
  set +H
  PASS='Cambiar1234!justenvios_us'
  ```
- **Opción 2:** escapar el `!`
  ```bash
  PASS="Cambiar1234\!justenvios_us"
  ```
- **Opción 3:** comillas simples (el `!` no se expande dentro de `'...'`)
  ```bash
  PASS='Cambiar1234!justenvios_us'
  ```

Si ya viste el error, ejecuta `set +H` y vuelve a asignar `PASS`.

---

## B) Verificar si el usuario existe en la DB

Ejecutar en el servidor (donde está el proyecto Django):

```bash
cd /srv/egarage  # o la ruta del proyecto
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
print('count=', U.objects.count())
print('justenvios username=', list(U.objects.filter(username__iexact='justenvios').values_list('id','username','email','is_active')[:5]))
print('justenvios email=', list(U.objects.filter(email__iexact='justenvios@gmail.com').values_list('id','username','email','is_active')[:5]))
"
```

**Interpretación:**

- Si ambos salen `[]` → no existe ese usuario (o estás en otra DB/entorno/tenant).
- Si aparece un registro → el curl debería mostrar `x-found-id` con ese id.

Pega la salida de este comando para saber si: el usuario no existe, existe con otro username/email, o existe y el problema es autenticación/backends.

---

## C) Repetir el curl con PASS bien seteada

```bash
set +H
LOGIN="justenvios"
PASS='Cambiar1234!justenvios_us'

curl -sk -c /tmp/cj.txt https://egarage.cl/us/login/ -o /tmp/login.html
CSRF=$(rg -o "name=\"csrfmiddlewaretoken\" value=\"[^\"]+\"" /tmp/login.html | head -n1 | sed -E 's/.*value=\"([^\"]+)\".*/\1/')

curl -sk -b /tmp/cj.txt -c /tmp/cj.txt \
  -e https://egarage.cl/us/login/ \
  -H "Referer: https://egarage.cl/us/login/" \
  --data-urlencode "csrfmiddlewaretoken=$CSRF" \
  --data-urlencode "login=$LOGIN" \
  --data-urlencode "password=$PASS" \
  https://egarage.cl/us/login/ -D- -o /dev/null \
| rg -n "HTTP/|x-usa-login-view|x-found-by|x-found-id|x-pwd-ok|x-active-ok|location:"
```

Con PASS correcta y usuario existente deberías ver `x-found-id` con valor y, si todo va bien, `x-usa-login-view: 1` y `location:` al dashboard.
