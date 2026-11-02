# RUNBOOK PRODUCCIÓN – eGarage

## HEALTHCHECK (Básico)
```bash
bash /srv/egarage/scripts/prod_healthcheck.sh
```

## DIAGNÓSTICO AVANZADO (Desktop + Mobile + Logs)
Este script simula dispositivos móviles y verifica errores en tiempo real en Gunicorn.
```bash
bash /srv/egarage/scripts/diag_full.sh
```

## DEPLOY
```bash
bash /srv/egarage/scripts/deploy_prod.sh
```

## ROLLBACK
```bash
bash /srv/egarage/scripts/rollback_prod.sh
```

## LOGS
```bash
journalctl -u gunicorn -n 100 --no-pager
```

## ERRORES CRÍTICOS
### Signup falla
1. Revisar existencia de `templates/components/ayuda_contextual.html`.
2. Revisar logs de Gunicorn para `TemplateDoesNotExist`.

### Login redirige mal
1. Revisar `gestion_taller/urls.py`.
2. Buscar redirecciones a `/accounts/` que rompan el contexto de país.

### 500 General
1. Revisar includes en `templates/base.html`.
2. Verificar estado de migraciones pendientes.

## ENDPOINTS CRÍTICOS
- USA Login: `/us/login/`
- USA Signup: `/us/signup/`
- Chile Home: `/cl/es/`

## REGLA DE ORO
**Si login o signup fallan -> PRODUCCIÓN CAÍDA**
