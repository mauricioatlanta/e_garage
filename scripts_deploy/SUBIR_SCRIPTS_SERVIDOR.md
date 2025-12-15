# 📤 SUBIR SCRIPTS AL SERVIDOR

## Problema
Los scripts `1_backup_FIXED.sh` y `2_actualizar_ESTRUCTURA_COMPLETA.sh` no están en el servidor.

## Solución: Subir con FileZilla

### Paso 1: Conectar con FileZilla

1. Abre **FileZilla**
2. Conecta a:
   - **Host**: `atlantareciclajes.pythonanywhere.com`
   - **Puerto**: `22` (SFTP)
   - **Usuario**: `atlantareciclajes`
   - **Contraseña**: [tu contraseña]

### Paso 2: Navegar a la carpeta de scripts

- **En el servidor**: `/home/atlantareciclajes/scripts_deploy/`
- Si la carpeta no existe, créala

### Paso 3: Subir los scripts necesarios

**En tu PC**: `E:\projecto\e_garage\scripts_deploy\`

**Sube estos archivos** (arrastra desde tu PC al servidor):

1. ✅ `1_backup_FIXED.sh`
2. ✅ `2_actualizar_ESTRUCTURA_COMPLETA.sh`
3. ✅ `3_verificar_FIXED.sh` (opcional, pero recomendado)
4. ✅ `4_rollback.sh` (opcional, pero recomendado)
5. ✅ `0_detectar_ruta.sh` (opcional)

### Paso 4: Dar permisos de ejecución

En la consola de PythonAnywhere, ejecuta:

```bash
cd /home/atlantareciclajes/scripts_deploy/
chmod +x *.sh
```

### Paso 5: Verificar que están subidos

```bash
ls -la *.sh
```

Deberías ver:
- `1_backup_FIXED.sh`
- `2_actualizar_ESTRUCTURA_COMPLETA.sh`
- etc.

### Paso 6: Ejecutar los scripts

```bash
./1_backup_FIXED.sh
./2_actualizar_ESTRUCTURA_COMPLETA.sh
```

---

## Alternativa: Subir todos los scripts de una vez

Si prefieres, puedes subir toda la carpeta `scripts_deploy/` completa:

1. **En FileZilla**: Arrastra toda la carpeta `scripts_deploy/` desde tu PC
2. **Destino en servidor**: `/home/atlantareciclajes/`
3. **En la consola**:
   ```bash
   cd /home/atlantareciclajes/scripts_deploy/
   chmod +x *.sh
   ```

---

## Verificación Rápida

Después de subir, verifica:

```bash
cd /home/atlantareciclajes/scripts_deploy/
ls -la 1_backup_FIXED.sh 2_actualizar_ESTRUCTURA_COMPLETA.sh
```

Si ves los archivos listados, están subidos correctamente.











