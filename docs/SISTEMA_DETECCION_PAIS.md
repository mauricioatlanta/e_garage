# 🌍 Sistema de Detección de País - eGarage

**Fecha:** 27 de Octubre, 2025
**Pregunta:** ¿Cómo reconoce la app que un suscriptor es de USA o de Chile?

---

## 📋 Resumen Ejecutivo

eGarage usa un **sistema multi-nivel de detección de país** que prioriza diferentes fuentes de información para determinar si un usuario/suscriptor es de USA 🇺🇸 o Chile 🇨🇱.

---

## 🔍 Jerarquía de Detección (en orden de prioridad)

```
1️⃣ Prefijo de URL (/us/ o /cl/)           ← MÁS PRIORITARIO
      ↓ Si no hay prefijo
2️⃣ Empresa del usuario (campo pais)
      ↓ Si no está autenticado
3️⃣ Parámetro en URL (?country=US)
      ↓ Si no hay parámetro
4️⃣ País por defecto (CL - Chile)          ← MENOS PRIORITARIO
```

---

## 🛠️ Mecanismos de Detección

### 1️⃣ **Detección por URL** (Más Común)

**Cómo funciona:**
- Usuario visita URL con prefijo de país
- Middleware detecta el prefijo automáticamente
- Asigna el país correspondiente

**Ejemplos:**
```
http://127.0.0.1:8000/us/           → USA 🇺🇸
http://127.0.0.1:8000/us/dashboard/ → USA 🇺🇸
http://127.0.0.1:8000/us/pricing/   → USA 🇺🇸

http://127.0.0.1:8000/cl/           → Chile 🇨🇱
http://127.0.0.1:8000/cl/dashboard/ → Chile 🇨🇱
http://127.0.0.1:8000/cl/precios/   → Chile 🇨🇱
```

**Middleware responsable:**
- `CountryContextMiddleware` en `taller/middleware/country_context.py`
- `CountryMiddleware` en `taller/middleware/country.py`

**Código:**
```python
# En CountryMiddleware
def _get_country_from_url(self, request):
    path = request.path_info
    if path.startswith("/us/"):
        return "US"
    elif path.startswith("/cl/"):
        return "CL"
    return None
```

---

### 2️⃣ **Detección por Empresa** (Usuarios Autenticados)

**Cómo funciona:**
- Usuario se autentica (login)
- Sistema busca su empresa asociada
- Lee el campo `pais` de la empresa
- Usa ese país para todas las operaciones

**Modelo:**
```python
class Empresa(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pais = models.CharField(max_length=2, choices=[
        ('CL', 'Chile'),
        ('US', 'Estados Unidos'),
    ])
    nombre_taller = models.CharField(max_length=200)
    # ... otros campos
```

**Middleware responsable:**
- `EmpresaMiddleware` en `taller/middleware/empresa_middleware.py`

**Código:**
```python
class EmpresaMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.empresa = request.user.empresa
                # Ahora request.empresa.pais está disponible
            except Empresa.DoesNotExist:
                request.empresa = None
        return self.get_response(request)
```

---

### 3️⃣ **Detección por Parámetro en URL**

**Cómo funciona:**
- URL incluye parámetro `?country=US` o `?country=CL`
- Sistema lee el parámetro
- Asigna el país temporalmente

**Ejemplos:**
```
http://127.0.0.1:8000/accounts/login/?country=US  → USA 🇺🇸
http://127.0.0.1:8000/accounts/login/?country=CL  → Chile 🇨🇱
```

**Código:**
```python
# En country_aware_login vista
country_param = request.GET.get("country", "")
if country_param.upper() in ["US", "USA"]:
    request.country = "US"
elif country_param.upper() in ["CL", "CHILE"]:
    request.country = "CL"
```

---

### 4️⃣ **País Por Defecto**

**Cómo funciona:**
- Si ningún método anterior funciona
- Asigna Chile (CL) por defecto

**Código:**
```python
DEFAULT_COUNTRY = "CL"

if not country:
    country = getattr(settings, "DEFAULT_COUNTRY", "CL")
```

---

## 🔄 Flujo Completo de Detección

### Escenario 1: Usuario Nuevo Visitando

```
1. Usuario visita: http://127.0.0.1:8000/
   ↓
2. NO hay prefijo de país
   ↓
3. Usuario NO está autenticado
   ↓
4. NO hay parámetro ?country=
   ↓
5. ✅ Asigna país por defecto: CL (Chile)
   ↓
6. Puede ser redirigido a /cl/ si hay middleware de redirección
```

### Escenario 2: Usuario Selecciona País

```
1. Usuario en: http://127.0.0.1:8000/
   ↓
2. Hace clic en botón "🇺🇸 United States"
   ↓
3. Redirige a: http://127.0.0.1:8000/us/
   ↓
4. ✅ Middleware detecta prefijo /us/
   ↓
5. request.country = "US"
   ↓
6. Todas las vistas usan país USA
```

### Escenario 3: Usuario Ya Registrado

```
1. Usuario hace login
   ↓
2. Sistema busca su Empresa en BD
   ↓
3. Lee: empresa.pais = "US"
   ↓
4. ✅ request.empresa.pais = "US"
   ↓
5. Redirige a: http://127.0.0.1:8000/us/dashboard/
   ↓
6. Todas las funciones usan país de su empresa
```

---

## 🗄️ Almacenamiento del País

### En Base de Datos

**Tabla:** `Empresa`
**Campo:** `pais`

```sql
SELECT user_id, nombre_taller, pais
FROM taller_empresa;

user_id | nombre_taller      | pais
--------|--------------------|-----
1       | Atlanta Auto Shop  | US
2       | Taller Central     | CL
3       | Miami Garage       | US
```

**¿Cuándo se asigna?**
- Durante el **registro** del suscriptor
- El usuario elige su país en el formulario
- Se guarda en `empresa.pais`

---

## 📍 Dónde se Usa el País

### 1. **Templates**
```python
# En cualquier template
{% if request.empresa.pais == 'US' %}
    🇺🇸 Pricing in USD
{% else %}
    🇨🇱 Precios en CLP
{% endif %}
```

### 2. **Vistas**
```python
# En views.py
def dashboard(request):
    pais = request.empresa.pais  # "US" o "CL"

    if pais == "US":
        precios_en_usd()
    else:
        precios_en_clp()
```

### 3. **Modelos**
```python
# En models.py
class Documento:
    def calcular_iva(self):
        pais = self.empresa.pais
        if pais == "CL":
            return self.subtotal * 0.19  # 19% IVA Chile
        else:
            return 0  # USA sin IVA en template
```

### 4. **Precios**
```python
# En precio_suscripcion.py
precio = PrecioSuscripcion.objects.para_pais(request.empresa.pais)
```

---

## 🔐 Proceso de Registro

### ¿Cómo se asigna el país inicialmente?

**Flujo de registro:**

```
1. Usuario visita /us/ o /cl/
   ↓
2. Hace clic en "Sign Up"
   ↓
3. URL: /us/signup/ o /cl/signup/
   ↓
4. Formulario de registro se muestra
   ↓
5. Sistema detecta país desde URL
   ↓
6. Al crear cuenta:
   - Usuario creado
   - Empresa creada con pais = "US" o "CL"
   ↓
7. ✅ Empresa guardada con país asignado
```

**Código simplificado:**
```python
# Durante signup
def signup_view(request):
    # Detectar país desde URL
    if request.path.startswith('/us/'):
        pais = 'US'
    else:
        pais = 'CL'

    # Crear empresa con país
    empresa = Empresa.objects.create(
        user=new_user,
        pais=pais,
        nombre_taller=form.cleaned_data['nombre_taller']
    )
```

---

## 🎯 Middlewares en Orden

**Configuración en `settings.py`:**

```python
MIDDLEWARE = [
    # ... otros middlewares

    # 1. Detecta empresa del usuario
    'taller.middleware.empresa_middleware.EmpresaMiddleware',

    # 2. Detecta país y redirige si es necesario
    'taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware',

    # 3. Establece idioma según país
    'taller.middleware.lang_policy.LanguagePolicyMiddleware',

    # ... otros middlewares
]
```

**Orden de ejecución:**
1. Usuario hace request
2. EmpresaMiddleware → Carga `request.empresa`
3. CountryMiddleware → Detecta `request.country`
4. SimpleCountryRedirect → Redirige si URL no coincide con país
5. LanguagePolicyMiddleware → Establece idioma (EN para US, ES para CL)

---

## 🌐 Ejemplos Prácticos

### Ejemplo 1: Usuario de Atlanta (USA)

**Registro:**
```
1. Visita: http://egarage.com/us/
2. Signup: http://egarage.com/us/signup/
3. Rellena formulario:
   - Nombre: "Atlanta Auto Shop"
   - Email: atlanta@example.com
4. Sistema crea:
   - User: atlanta@example.com
   - Empresa: nombre="Atlanta Auto Shop", pais="US"
```

**Uso posterior:**
```
1. Login: http://egarage.com/accounts/login/
2. Middleware detecta: user.empresa.pais = "US"
3. Redirige a: http://egarage.com/us/dashboard/
4. TODAS las páginas muestran:
   - Precios en USD ($20, $100, $200)
   - Textos en inglés
   - Badge: 🇺🇸 UNITED STATES
   - IVA: 0%
```

---

### Ejemplo 2: Usuario de Santiago (Chile)

**Registro:**
```
1. Visita: http://egarage.com/cl/
2. Signup: http://egarage.com/cl/signup/
3. Rellena formulario:
   - Nombre: "Taller Central"
   - Email: taller@example.cl
4. Sistema crea:
   - User: taller@example.cl
   - Empresa: nombre="Taller Central", pais="CL"
```

**Uso posterior:**
```
1. Login: http://egarage.com/accounts/login/
2. Middleware detecta: user.empresa.pais = "CL"
3. Redirige a: http://egarage.com/cl/dashboard/
4. TODAS las páginas muestran:
   - Precios en CLP ($20.000, $100.000, $200.000)
   - Textos en español
   - Badge: 🇨🇱 CHILE
   - IVA: 19%
```

---

## 🔧 Componentes del Sistema

### 1. **Modelo Empresa**
**Archivo:** `taller/models/empresa.py`

```python
class Empresa(models.Model):
    user = models.OneToOneField(User)
    pais = models.CharField(
        max_length=2,
        choices=[('CL', 'Chile'), ('US', 'Estados Unidos')],
        default='CL'
    )
    nombre_taller = models.CharField(max_length=200)
    # ... más campos
```

**Campo clave:** `pais` - Almacena "US" o "CL"

---

### 2. **EmpresaMiddleware**
**Archivo:** `taller/middleware/empresa_middleware.py`

**Función:** Carga la empresa del usuario en cada request

```python
class EmpresaMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            request.empresa = request.user.empresa
            # Ahora request.empresa.pais está disponible
        return self.get_response(request)
```

**Resultado:** Todas las vistas tienen acceso a `request.empresa.pais`

---

### 3. **CountryContextMiddleware**
**Archivo:** `taller/middleware/country_context.py`

**Función:** Detecta país desde múltiples fuentes

```python
class CountryContextMiddleware:
    def process_request(self, request):
        # 1. Desde URL
        if request.path.startswith('/us/'):
            country = 'US'
        elif request.path.startswith('/cl/'):
            country = 'CL'

        # 2. Desde usuario autenticado
        elif request.user.is_authenticated:
            country = request.user.empresa.pais

        # 3. Default
        else:
            country = 'CL'

        request.country = country
        return None
```

**Resultado:** Todas las vistas tienen acceso a `request.country`

---

### 4. **SimpleCountryRedirectMiddleware**
**Archivo:** `taller/middleware/simple_country_redirect.py`

**Función:** Redirige automáticamente si URL no coincide con país del usuario

**Ejemplo:**
```python
# Usuario con empresa.pais = "US" intenta acceder a /cl/
if user.empresa.pais == "US" and request.path.startswith('/cl/'):
    # Redirige a /us/dashboard/
    return redirect('/us/dashboard/')
```

---

### 5. **CountryAwareLoginView**
**Archivo:** `taller/views/country_aware_auth.py`

**Función:** Login que detecta país y usa template apropiado

```python
def country_aware_login(request):
    # Detectar país desde:
    # 1. Parámetro 'next' en URL
    if next_url.startswith("/us/"):
        request.country = "US"

    # 2. Usuario autenticado
    elif request.user.empresa.pais:
        request.country = request.user.empresa.pais

    # 3. Parámetro country
    elif request.GET.get("country") == "US":
        request.country = "US"

    # 4. Default
    else:
        request.country = "CL"

    # Usar template específico
    if request.country == "US":
        template = "taller/us/en/account/login.html"
    else:
        template = "taller/cl/es/account/login.html"
```

---

## 📊 Tabla Resumen

| Fuente | Prioridad | Cuándo se Usa | Ejemplo |
|--------|-----------|---------------|---------|
| **Prefijo URL** | 🥇 Alta | Siempre que hay /us/ o /cl/ | `/us/dashboard/` |
| **Empresa.pais** | 🥈 Media | Usuario autenticado | `user.empresa.pais = "US"` |
| **Parámetro URL** | 🥉 Baja | Enlaces especiales | `?country=US` |
| **Default** | 4️⃣ Última | Cuando no hay info | Siempre CL |

---

## 🎯 Casos de Uso Reales

### Caso 1: Registro desde Landing Page USA

```
Paso 1: Usuario en USA visita landing
  URL: http://egarage.com/

Paso 2: Selecciona país
  Clic en: 🇺🇸 United States
  URL: http://egarage.com/us/

Paso 3: Hace signup
  URL: http://egarage.com/us/signup/
  Formulario detecta automáticamente país = "US"

Paso 4: Crea cuenta
  Sistema crea:
    - Usuario: joe@example.com
    - Empresa: pais = "US"

Paso 5: Login automático
  Redirige a: http://egarage.com/us/dashboard/

✅ De ahora en adelante:
  - TODAS las páginas en inglés
  - TODOS los precios en USD
  - TODAS las funciones country-aware usan "US"
```

---

### Caso 2: Registro desde Landing Page Chile

```
Paso 1: Usuario en Chile visita landing
  URL: http://egarage.com/

Paso 2: Selecciona país
  Clic en: 🇨🇱 Chile
  URL: http://egarage.com/cl/

Paso 3: Hace signup
  URL: http://egarage.com/cl/signup/
  Formulario detecta automáticamente país = "CL"

Paso 4: Crea cuenta
  Sistema crea:
    - Usuario: juan@example.cl
    - Empresa: pais = "CL"

Paso 5: Login automático
  Redirige a: http://egarage.com/cl/dashboard/

✅ De ahora en adelante:
  - TODAS las páginas en español
  - TODOS los precios en CLP
  - TODAS las funciones country-aware usan "CL"
```

---

## 🔐 Persistencia del País

### ¿Se Puede Cambiar?

**Respuesta:** Depende de tu lógica de negocio.

**Actualmente:**
- País se asigna al registrarse
- Se guarda en la empresa
- **Es permanente** (no cambia automáticamente)

**Si quieres permitir cambio:**
- Agregar función en configuración
- Actualizar `empresa.pais`
- Usuario puede cambiar de US → CL o viceversa

---

## 🧪 Cómo Probar

### Verificar País de un Usuario

**Opción 1: Django Shell**
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from taller.models import Empresa

User = get_user_model()

# Ver país de un usuario
user = User.objects.get(email='atlanta@example.com')
print(f"País: {user.empresa.pais}")  # "US" o "CL"

# Ver todos los usuarios por país
usa_users = Empresa.objects.filter(pais='US')
chile_users = Empresa.objects.filter(pais='CL')

print(f"Usuarios USA: {usa_users.count()}")
print(f"Usuarios Chile: {chile_users.count()}")
```

---

### Verificar Detección en Runtime

**Agregar en tu template:**
```html
<!-- Debug info -->
<div style="position: fixed; bottom: 10px; right: 10px; background: black; color: lime; padding: 10px; font-family: monospace; font-size: 12px;">
    País detectado: {{ request.country }}<br>
    Empresa país: {{ request.empresa.pais }}<br>
    URL: {{ request.path }}
</div>
```

---

## 📚 Archivos Clave

### Modelos
- `taller/models/empresa.py` - Define campo `pais`
- `taller/models/precio_suscripcion.py` - Precios por país

### Middlewares
- `taller/middleware/empresa_middleware.py` - Carga empresa
- `taller/middleware/country_context.py` - Detecta país desde URL
- `taller/middleware/simple_country_redirect.py` - Redirige si necesario
- `taller/middleware/lang_policy.py` - Establece idioma por país

### Vistas
- `taller/views/country_aware_auth.py` - Login con detección de país
- `taller/views_extra/views_suscripciones.py` - Precios por país

### Templates
- `templates/taller/us/en/` - Templates para USA
- `templates/taller/cl/es/` - Templates para Chile

---

## ✅ Resumen

**¿Cómo reconoce la app si un suscriptor es de USA o Chile?**

### Respuesta Corta:
1. **URL:** Si está en `/us/` → USA, si está en `/cl/` → Chile
2. **Empresa:** Campo `pais` en la base de datos (se asigna al registrarse)

### Respuesta Técnica:
1. **Middleware** detecta país desde URL o empresa del usuario
2. **Campo `pais`** en modelo `Empresa` almacena el país permanentemente
3. **Sistema usa el país** para:
   - Precios (USD vs CLP)
   - Idioma (EN vs ES)
   - Templates específicos
   - Cálculos de impuestos (IVA 19% Chile vs 0% USA)
   - Features específicos por país

---

**Documento creado:** 27 de Octubre, 2025
**Sistema:** Multi-país con detección automática ✅
**Países soportados:** USA 🇺🇸 y Chile 🇨🇱





