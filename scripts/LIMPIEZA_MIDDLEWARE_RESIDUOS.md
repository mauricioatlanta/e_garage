# Limpieza de residuos de middleware (ejecutar en servidor)

Comandos para limpiar duplicados y archivos residuales en el servidor de producción.

## 1. Eliminar archivos .save (residuos de editor/backup)

```bash
cd /srv/egarage
rm -f taller/middleware/*.save* 2>/dev/null || true
```

## 2. Mover deploy_atlantareciclajes a backup (si existe en servidor y no se usa en runtime)

> ⚠️ Solo si `deploy_atlantareciclajes/` existe en el servidor y NO es parte del runtime.
> El runtime usa `taller/middleware/` como fuente.

```bash
cd /srv/egarage
mkdir -p _backup_residuos
mv deploy_atlantareciclajes _backup_residuos/ 2>/dev/null || true
```

## 3. Eliminar carpeta anidada middleware/middleware (si existe)

```bash
cd /srv/egarage
rm -rf deploy_atlantareciclajes/taller/middleware/middleware 2>/dev/null || true
```

## 4. Confirmar que settings apuntan al middleware canónico

```bash
grep -Rni "EmpresaMiddleware\|VerificarSuscripcionMiddleware" gestion_taller/ taller/ | head -n 20
```

Debe mostrar rutas como `taller.middleware.empresa_middleware` y `taller.middleware.verificar_suscripcion`.

## Single source of truth

- **Oficial**: `taller/middleware/*.py`
- **No usar**: copias en deploy_atlantareciclajes, tools/maintenance (re-export únicamente)
