# Operación y Despliegue eGarage

## Comandos operativos
- makemigrations / migrate
- backfill_responsables (dry-run y real)
- ruff, isort, black (lint/format)
- smoke test: login, crear documento, dashboard
- KPIs: técnicos/vendedores efectivos, ventas por mes

## QA y troubleshooting
- "No changes detected" en makemigrations: revisar apps y modelos.
- ContentTypes: limpiar si hay modelos legacy.
- Alias: Mecanico → Tecnico (solo uno en sistema).

## Índices recomendados
- Documento(empresa, fecha_emision)
- Líneas(documento, servicio/repuesto)
- Cliente(empresa)
