# Troubleshooting del deploy (rutas y comandos)

Si al seguir la documentación de deploy ves errores como los siguientes, tu servidor **no usa** la ruta `/srv/egarage` o no tiene `sudo`. Usa esta guía.

## Errores típicos

- `cd: /srv/egarage: No such file or directory`
- `python: can't open file '.../manage.py': No such file or directory`
- `sudo: command not found`

## 1. Descubrir la ruta real del proyecto

En el servidor, el proyecto puede estar en otro sitio (por ejemplo en tu home). Ejecuta:

```bash
# Buscar manage.py
find ~ -name "manage.py" -type f 2>/dev/null | head -5

# O si sabes que está en una carpeta tipo e_garage / egarage:
find ~ -type d -name "e_garage" 2>/dev/null
find ~ -type d -name "egarage" 2>/dev/null
```

Cuando encuentres la ruta (ej. `/home/atlantareciclajes/e_garage`), **usa esa** en todos los comandos.

Ejemplo con la ruta en tu home:

```bash
cd ~/e_garage
# o la ruta exacta que te haya devuelto find, ej.:
# cd /home/atlantareciclajes/e_garage

# Activar venv si existe
[ -d venv/bin ] && source venv/bin/activate

python manage.py collectstatic --noinput
```

## 2. Reiniciar la app sin `sudo` (hosting compartido)

En muchos hostings compartidos (PythonAnywhere, algunos VPS sin root, etc.) **no existe `sudo`**. El reinicio se hace de otra forma:

### PythonAnywhere

- Entra en la pestaña **Web** del panel.
- Pulsa el botón **Reload** de tu app (o “Reload egarage” / el nombre que tenga).

No hace falta ningún comando en la consola para reiniciar.

### Otro hosting (Passenger, uWSGI, etc.)

- **Passenger:** tocar un archivo para forzar recarga, por ejemplo:  
  `touch tmp/restart.txt` (desde la raíz del proyecto).
- **uWSGI con archivo .sock:** suele haber un script o botón en el panel (cPanel, Plesk, etc.) para “Restart application”.
- Si te dieron una **consola** y un usuario sin sudo, pregunta al proveedor: “¿Cómo reinicio la aplicación Django/Gunicorn?”.

### Si sí tienes systemd pero con otro nombre de servicio

En algunos servidores el servicio no se llama `gunicorn` sino `egarage-gunicorn`:

```bash
sudo systemctl restart egarage-gunicorn
# o
sudo systemctl restart gunicorn-e_garage
```

Para listar servicios relacionados:

```bash
sudo systemctl list-units --all | grep -E "gunicorn|egarage"
```

## 3. Resumen según tu caso

| Situación | Qué hacer |
|-----------|-----------|
| No existe `/srv/egarage` | Usar la ruta donde está el proyecto (ej. `~/e_garage`) en todos los `cd` y comandos. |
| No existe `manage.py` en el directorio actual | Hacer `cd` a la ruta del proyecto antes de ejecutar `python manage.py ...`. |
| `sudo: command not found` | No usar `sudo`. Reiniciar desde el panel (p. ej. Reload en PythonAnywhere) o con el método que indique tu hosting. |

## 4. Comandos genéricos (sustituir RUTA_PROYECTO)

```bash
cd RUTA_PROYECTO
source venv/bin/activate
python manage.py collectstatic --noinput
# Reinicio: según hosting (panel Reload, touch tmp/restart.txt, o sudo systemctl restart ...)
```

Sustituye `RUTA_PROYECTO` por la ruta real (ej. `/home/atlantareciclajes/e_garage`).
