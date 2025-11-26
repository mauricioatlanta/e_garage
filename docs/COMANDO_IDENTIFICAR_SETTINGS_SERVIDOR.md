# 🔍 Identificar archivo de settings sin ejecutar Django

Como Django no puede iniciar debido al error, usa estos comandos en el servidor para identificar qué archivo de settings está usando:

## Método 1: Verificar manage.py

```bash
cd ~/apps/egarage/current
grep -n "DJANGO_SETTINGS_MODULE" manage.py
```

Esto mostrará qué archivo de settings usa por defecto. Probablemente será:
- `gestion_taller.settings`
- `gestion_taller.compacto.settings`
- O lo que esté configurado en una variable de entorno

## Método 2: Verificar variable de entorno

```bash
echo $DJANGO_SETTINGS_MODULE
```

Si no muestra nada, Django usa el valor por defecto de `manage.py`.

## Método 3: Verificar qué archivos de settings existen

```bash
cd ~/apps/egarage/current
find gestion_taller -name "settings*.py" -type f
```

## Método 4: Editar directamente (más rápido)

Como `manage.py` probablemente usa `gestion_taller.settings` por defecto, edita directamente:

```bash
cd ~/apps/egarage/current
nano gestion_taller/settings.py
```

Busca la línea:
```python
"django.contrib.auth.middleware.AuthenticationMiddleware",
```

Y agrega después:
```python
"allauth.account.middleware.AccountMiddleware",
```

**Guardar:** Ctrl+O, Enter, Ctrl+X

Si ese archivo no existe o no tiene la línea de MIDDLEWARE, intenta con:
```bash
nano gestion_taller/compacto/settings.py
```



