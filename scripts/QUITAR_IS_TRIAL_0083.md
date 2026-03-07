# Quitar is_trial de la migración 0083 (evitar DuplicateColumn)

**Motivo:** `is_trial` ya lo maneja `0082_empresa_is_trial_if_not_exists`. Si queda también en 0083, falla por columna duplicada.

---

## Si el script dejó la migración con sintaxis rota (SyntaxError / “Perhaps you forgot a comma?”)

### Fix mecánico (recomendado): regenerar 0083

```bash
cd /srv/egarage  # o la raíz del proyecto
rm -f taller/migrations/0083_alter_documentsequence_unique_together_and_more.py
python manage.py makemigrations taller
```

Revisa si la nueva 0083 incluye otra vez `is_trial`:

```bash
rg -n "name='is_trial'|model_name='empresa'" taller/migrations/0083_*.py
```

Si **no** aparece `is_trial` → listo.  
Si **sí** incluye `is_trial` → quítalo a mano (Opción B) y valida con `py_compile` (abajo).

---

## Opción A – Script (solo si la migración está intacta)

El script ahora **no toca la coma del elemento anterior** y valida sintaxis con `py_compile` al final.

En el servidor, desde la raíz del proyecto:

```bash
python scripts/remove_is_trial_from_0083.py /srv/egarage/taller/migrations/0083_alter_documentsequence_unique_together_and_more.py
```

Si falla la validación, usa el fix mecánico de arriba.

---

## Opción B – Manual con nano

```bash
nano /srv/egarage/taller/migrations/0083_alter_documentsequence_unique_together_and_more.py
```

Dentro de `operations = [ ... ]` **elimina por completo** este bloque (sin reemplazarlo por nada):

```python
migrations.AddField(
    model_name='empresa',
    name='is_trial',
    field=models.BooleanField(...),
),
```

Guarda (Ctrl+O, Enter) y cierra (Ctrl+X).

**Validar sintaxis** (sin ejecutar Django):

```bash
python -m py_compile /srv/egarage/taller/migrations/0083_*.py
```

Si no imprime nada → OK. Si hay error → revisa que no queden comas dobles ni `],` raro.
