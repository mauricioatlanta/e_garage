# Entorno de Desarrollo

## Versiones soportadas

| Componente | Versión requerida | Notas |
|---|---|---|
| Python | **3.11 o 3.12** | 3.13+ **no soportado** (ver abajo) |
| Django | 4.2.x | Matriz oficial: Python 3.8–3.12 |
| Node.js | 18.x | Solo para Playwright (E2E) |

### Por qué Python 3.13+ está bloqueado

Django 4.2 no soporta Python 3.13 ni 3.14. El síntoma principal es un error en
`Context.__copy__` que rompe el sistema de templates en tests y puede causar
comportamiento indefinido en producción. Detalles técnicos en
`docs/architecture/ADR-002-custom-domains.md`.

La próxima actualización a Django 5.1+ desbloqueará Python 3.13.

---

## Configuración inicial

### Requisito: Python 3.12

**Opción A — pyenv (recomendado):**
```bash
curl https://pyenv.run | bash          # instala pyenv si no lo tienes
pyenv install 3.12
pyenv local 3.12                       # crea .python-version en este directorio
```

**Opción B — deadsnakes PPA (Ubuntu/Debian):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

**Opción C — Homebrew (macOS):**
```bash
brew install python@3.12
```

### Crear el entorno virtual

```bash
# Desde la raíz del proyecto:
bash scripts/bootstrap.sh

# Si tienes varias versiones de Python:
PYTHON=python3.12 bash scripts/bootstrap.sh
```

El script valida la versión, elimina el venv existente si lo hay, e instala
`requirements.txt` y `requirements-dev.txt`.

### Activar manualmente

```bash
source .venv/bin/activate
python --version   # debe mostrar 3.11.x o 3.12.x
```

---

## Verificación rápida

```bash
python manage.py check          # debe pasar sin errores
pytest taller/tests/ -q         # suite completa
```

---

## Variables de entorno

```bash
cp env.example .env
# edita .env con tus valores locales (DB, SECRET_KEY, etc.)
```

`manage.py` carga `.env` automáticamente. En producción se usa `.env.prod`
(controlado por la variable `EGARAGE_ENV=prod`).

---

## Recrear el entorno desde cero

```bash
deactivate                      # si el venv estaba activo
rm -rf .venv
PYTHON=python3.12 bash scripts/bootstrap.sh
source .venv/bin/activate
```

---

## CI/CD

Los workflows de GitHub Actions usan una matriz `[3.11, 3.12]` definida en
`.github/workflows/ci.yml`. Ambas versiones deben pasar antes de hacer merge.

La versión pinada localmente está en `.python-version` (leída por pyenv/asdf).
