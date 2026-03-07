# Arreglar migración 0080 - ValueError Found wrong number (0) of constraints

## Problema

Al aplicar `taller.0080_alter_documentsequence_unique_together_and_more`, falla con:

```
ValueError: Found wrong number (0) of constraints for taller_documentsequence(empresa_id, tipo)
```

La migración intenta eliminar el constraint `unique_together (empresa, tipo)` pero ese constraint no existe en la BD de producción.

## Solución (dos pasos)

### 1) Subir la migración 0079 al servidor

La migración `taller/migrations/0079_fix_documentsequence_drop_constraint.py` elimina el constraint de forma segura solo si existe (PostgreSQL).

Haz deploy del código para que 0079 esté en `/srv/egarage/taller/migrations/`.

### 2) Editar 0080 en el servidor antes de aplicar

Antes de ejecutar `migrate`, edita 0080:

```bash
nano /srv/egarage/taller/migrations/0080_alter_documentsequence_unique_together_and_more.py
```

**a) Dependencias:** Cambia `dependencies` para que 0080 dependa de 0079 (así 0079 corre antes):

```python
    dependencies = [
        ("taller", "0079_fix_documentsequence_drop_constraint"),  # en lugar de 0078
    ]
```

**b) Elimina** la primera operación `AlterUniqueTogether` (la que pone `unique_together=set()`):

```python
        migrations.AlterUniqueTogether(
            name="documentsequence",
            unique_together=set(),
        ),
```

Guarda y cierra. **No toques** el segundo `AlterUniqueTogether` (el que pone `unique_together={("empresa", "tipo", "serie")}`).

### ⚠️ Cuidado al editar: error de sintaxis frecuente

Al borrar el bloque `AlterUniqueTogether`, es fácil borrar accidentalmente la línea `operations = [` o dejar una coma suelta. **La estructura correcta debe quedar así:**

```python
    dependencies = [
        ...
    ]

    operations = [
        migrations.AddField(
            ...
```

**Evitar:**
- Borrar `operations = [` (quedarían operaciones fuera del atributo)
- Dejar una coma suelta entre `dependencies` y `operations`

Si tras editar ves `SyntaxError: invalid syntax` en la línea de `,`, revisa que exista `operations = [` justo después de `dependencies = [...]` y que no haya comas colgando.

### 3) Aplicar migraciones

```bash
cd /srv/egarage
source venv/bin/activate
./scripts/manage_prod.sh migrate
```

### Orden correcto

1. `0079_fix_documentsequence_drop_constraint` — elimina el constraint viejo (PostgreSQL) si existe
2. `0080_...` (sin la primera operación) — añade `serie`, cambia `tipo`, crea el nuevo `unique_together`
