# 🚀 Deployment eGarage v2.0 - README

## ⚡ **3 PASOS PARA DEPLOYMENT**

### **1. Subir Archivos**
```bash
scp -r * user@servidor:/var/www/egarage/
```

### **2. Configurar**
```bash
ssh user@servidor
cd /var/www/egarage
cp CONFIGURACION_PRODUCCION.env.example .env
nano .env  # Editar valores
```

### **3. Deploy**
```bash
chmod +x deploy.sh
./deploy.sh
```

**¡Listo!** ⏱️ 30 minutos

---

## 📦 **ARCHIVOS A SUBIR**

```
✅ gestion_taller/
✅ taller/
✅ ubicacion/
✅ templates/
✅ static/
✅ manage.py
✅ requirements.txt
✅ deploy.sh
✅ CONFIGURACION_PRODUCCION.env.example
```

---

## ⚙️ **VALORES EN .env**

```bash
DJANGO_SECRET_KEY=generar-nueva
DEBUG=False
DB_PASSWORD=password-seguro
EMAIL_HOST_PASSWORD=password-email
ALLOWED_HOSTS=egarage.cl,www.egarage.cl
```

---

## ✅ **VERIFICAR**

```bash
curl https://egarage.cl/
curl https://egarage.cl/pe/signup/
```

---

## 📚 **AYUDA**

Ver: **INICIO_DEPLOYMENT.md**

---

**Comando:** `./deploy.sh`  
**Estado:** ✅ Listo  
**Tiempo:** 30 min  

🎉

