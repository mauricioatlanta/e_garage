# Arreglar 0075 cuando la tabla taller_registroembudosuscriptor ya existe

La migración 0075_registroembudosuscriptor_and_more intenta crear la tabla que ya existe (p. ej. por 0052). Hay que hacer que esa creación sea solo de estado, sin tocar la BD.

## En el servidor

### 1) Abrir la migración

```bash
nano /srv/egarage/taller/migrations/0075_registroembudosuscriptor_and_more.py
```

### 2) Sustituir solo la primera operación (CreateModel)

**Busca** el primer bloque que empiece por:

```python
        migrations.CreateModel(
            name="RegistroEmbudoSuscriptor",
```

**Sustituye ese bloque entero** (desde `migrations.CreateModel(` hasta el `),` que lo cierra) por esto, **dejando el mismo contenido del CreateModel dentro de state_operations**:

```python
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="RegistroEmbudoSuscriptor",
                    fields=[
                        ("id", models.BigAutoField(...)),  # copia aquí TODOS los fields del CreateModel original
                        # ... resto igual que en el CreateModel original
                    ],
                    options={...},  # igual que el original
                ),
            ],
            database_operations=[
                migrations.RunPython(lambda apps, schema_editor: None, lambda apps, schema_editor: None),
            ],
        ),
```

Es decir: el `CreateModel` completo (con todos sus `fields` y `options`) va **dentro** de `state_operations=[...]`. En `database_operations` solo va el `RunPython` que no hace nada. Así Django actualiza el estado pero no ejecuta `CREATE TABLE`.

### 3) Aplicar de nuevo

```bash
./scripts/manage_prod.sh migrate
```

---

## Alternativa rápida (solo si el resto del estado de la BD ya está bien)

Si en tu BD ya están aplicados los otros cambios (columnas trial_* en empresa, etc.) y solo falla el Create de RegistroEmbudoSuscriptor:

```bash
./scripts/manage_prod.sh migrate taller 0075_registroembudosuscriptor_and_more --fake
```

Eso marca la 0075 como aplicada **sin ejecutar ninguna** de sus operaciones. Si después la app falla por columnas o tablas que falten, tendrás que aplicar la opción de SeparateDatabaseAndState arriba o generar otra migración correctiva.
