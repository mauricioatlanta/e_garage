# 🔐 Conexión SSH - Primera Vez

## ⚠️ Mensaje de Verificación de Clave

Cuando te conectas por primera vez a un servidor SSH, verás este mensaje:

```
The authenticity of host 'atlantareciclajes.pythonanywhere.com (35.173.69.207)' can't be established.
ED25519 key fingerprint is SHA256:bndRPeZVSkOxHCPsmgC/8x0C8GdLTRGIgTjjJWFe/88.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])
```

## ✅ ¿Qué Hacer?

**Escribe `yes` y presiona Enter.**

Esto agregará la clave del servidor a tu lista de hosts conocidos (`~/.ssh/known_hosts`).

## 🔍 ¿Es Seguro?

**Sí, es seguro.** Este es el comportamiento normal de SSH:
- La primera vez que te conectas a un servidor, SSH te pregunta si confías en él
- La clave mostrada (`SHA256:bndRPeZVSkOxHCPsmgC/8x0C8GdLTRGIgTjjJWFe/88`) es la clave pública del servidor de PythonAnywhere
- Al escribir `yes`, guardas esta clave para futuras conexiones

## 📋 Pasos Completos

```bash
# 1. Conectar (verás el mensaje)
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com

# 2. Escribir "yes" cuando pregunte
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

# 3. Ingresar tu contraseña cuando se solicite
# (la contraseña NO se mostrará mientras escribes)

# 4. Una vez conectado, verás algo como:
# Welcome to PythonAnywhere!
# atlantareciclajes@atlantareciclajes:~$

# 5. Continuar con los comandos
cd /home/atlantareciclajes/apps/egarage/current
python3.10 manage.py collectstatic --noinput
```

## 🔒 Seguridad

- **Solo la primera vez:** Después de escribir `yes`, no volverás a ver este mensaje para este servidor
- **Si cambia la clave:** Si en el futuro la clave del servidor cambia, SSH te advertirá (esto podría indicar un problema de seguridad)
- **Contraseña:** Después de escribir `yes`, se te pedirá tu contraseña de PythonAnywhere

## 🆘 Problemas Comunes

### "Permission denied (publickey)"
- **Causa:** No tienes acceso SSH habilitado en PythonAnywhere
- **Solución:** 
  1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/account/
  2. Busca "SSH access" o "Enable SSH"
  3. Habilita el acceso SSH

### "Connection timed out"
- **Causa:** Problema de red o firewall
- **Solución:** Verifica tu conexión a internet

### "Host key verification failed"
- **Causa:** La clave del servidor cambió (poco común)
- **Solución:** 
  ```bash
  # Eliminar la clave antigua
  ssh-keygen -R atlantareciclajes.pythonanywhere.com
  # Intentar conectar de nuevo
  ```

---

**¡Conexión SSH completada!** 🔐











