# 🔧 Solución Error NumPy en Servidor

## Problema
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.2
AttributeError: _ARRAY_API not found
```

## Solución Rápida: Ejecutar código directamente

Para evitar el problema de NumPy al ejecutar comandos, usa el shell de Django directamente:

```bash
cd ~/apps/egarage/current
python3.10 manage.py shell --skip-checks
```

O si `--skip-checks` no funciona:

```bash
python3.10 manage.py shell << 'EOF'
# Tu código aquí
EOF
```

## Solución Permanente: Downgrade NumPy

```bash
pip3.10 install --user "numpy<2"
```

Luego reinicia la aplicación:
```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```



