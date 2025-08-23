# Este archivo elimina todas las migraciones de la app 'taller' excepto __init__.py.
import os
import glob

migrations_dir = os.path.join(os.path.dirname(__file__), 'taller', 'migrations')
for f in glob.glob(os.path.join(migrations_dir, '*.py')):
    if not f.endswith('__init__.py'):
        os.remove(f)
for f in glob.glob(os.path.join(migrations_dir, '*.pyc')):
    os.remove(f)
print('Migraciones eliminadas. Ahora ejecuta makemigrations y migrate.')
