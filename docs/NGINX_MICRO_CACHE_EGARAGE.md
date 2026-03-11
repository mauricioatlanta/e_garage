# Nginx para eGarage (Django + Gunicorn)

Configuración pensada para:

- **Login con sesiones** y centro de operaciones
- **Multi-país** (`/cl/`, `/us/`, `/ar/`, etc.)
- **Microcache** solo en landings públicas (no toca rutas internas)
- **Bloqueo de bots y scanners** (/.env, PHP, WordPress, etc.)
- **Rate limit** en login y tráfico general

No toca nada crítico del sistema interno.

---

## 1. Rate limit global (nginx.conf)

Edita el archivo principal de Nginx:

```bash
sudo nano /etc/nginx/nginx.conf
```

Dentro del bloque `http { }` agrega:

```nginx
# ===============================
# RATE LIMIT
# ===============================
limit_req_zone $binary_remote_addr zone=login_zone:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=general_zone:10m rate=15r/s;
```

(O incluye el snippet: `scripts/nginx/egarage_ratelimit_http.snippet.conf`)

---

## 2. Cache y bloqueo (nginx.conf, mismo bloque http {})

Carpeta de cache y zona para microcache:

```bash
sudo mkdir -p /var/cache/nginx/egarage
sudo chown -R www-data:www-data /var/cache/nginx
```

Dentro de `http { }` agrega (o usa `scripts/nginx/egarage_cache_http.snippet.conf`):

```nginx
# ===============================
# MICRO CACHE EGARAGE
# ===============================
proxy_cache_path /var/cache/nginx/egarage
    levels=1:2
    keys_zone=egarage_cache:100m
    max_size=1g
    inactive=60m
    use_temp_path=off;
```

---

## 3. Bloque principal del sitio eGarage

Copia o adapta la configuración completa del sitio desde:

**`scripts/nginx_egarage_example.conf`**

en tu archivo de sitio, por ejemplo:

```bash
sudo nano /etc/nginx/sites-available/egarage
```

Ese archivo incluye:

- Redirección HTTP → HTTPS
- SSL y `client_max_body_size`
- **Bloqueo de scanners** (/.env, .git, wp-login.php, phpinfo, cgi-bin, .php, etc.) con `return 444`
- **Rate limit en login** (`/accounts/login/`, `/us/login/`)
- **Microcache** en landings por país (`/cl/`, `/us/`, `/ar/`, `/mx/`, `/br/`) y en `/`
- **Static** y **media** servidos por Nginx
- **Todo lo demás** → proxy a Gunicorn con rate limit general

Ajusta rutas (socket, alias de static/media) según tu instalación.

---

## 4. Validar y recargar Nginx

```bash
sudo nginx -t
```

Si dice `syntax is ok` y `test is successful`:

```bash
sudo systemctl reload nginx
```

---

## 5. Probar que funciona

1. Abre **https://egarage.cl/cl/** (o cualquier landing de país).
2. En DevTools → **Network** revisa el header **X-Cache-Status**.
3. Primera carga: suele aparecer **MISS** (Django respondió).
4. Recarga rápido: debe aparecer **HIT** (Nginx respondió desde cache).

Eso confirma que el microcache está activo en las landings.

---

## 6. Qué mejoras verás

| Mejora | Efecto |
|--------|--------|
| Menos requests a Django | Landings y `/` servidas desde cache |
| Menos carga en Gunicorn | Tráfico general limitado (15 req/s por IP) |
| Bots PHP/WordPress bloqueados | Respuesta 444, sin gastar backend |
| Protección en login | 5 req/min por IP (fuerza bruta mitigada) |
| Landings más rápidas | Cache 5s en `/` y `/(cl|us|ar|mx|br)/` |

---

## 7. Medir qué te golpean (logs)

IPs que piden rutas basura (scanners):

```bash
awk '$7 ~ /^\/(\.env|\.git\/config|\.env\.prod|\.aws\/credentials|wp-login\.php|wp-config\.php|phpinfo\.php|test\.php|php\.php|vendor\/phpunit|cgi-bin|webui)/ {print $1, $7}' /var/log/nginx/egarage_access.log | sort | uniq -c | sort -nr | head -50
```

Solo 404 (escaneo / rutas inexistentes):

```bash
awk '$9 == 404 {print $1, $7}' /var/log/nginx/egarage_access.log | sort | uniq -c | sort -nr | head -50
```

---

## 8. Mejora extra: compresión Brotli

Cuando el tráfico crezca, en el bloque `http { }` (o en el `server`):

```nginx
brotli on;
brotli_types text/plain text/css application/javascript application/json;
```

Reduce el tamaño de las respuestas ~30–40 %. Requiere módulo Nginx Brotli (`ngx_brotli`).
