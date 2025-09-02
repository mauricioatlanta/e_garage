# 🇨🇱 Marcas y Modelos de Vehículos para Chile

## 📋 Descripción

Este conjunto de datos contiene **30 marcas** y **300 modelos** específicos del mercado chileno, optimizados para talleres automotrices en Chile.

## 🚗 Marcas Incluidas

### 🏭 Fabricantes Principales
- **Toyota** - Corolla, Yaris, Hilux, RAV4, Land Cruiser
- **Chevrolet** - Sail, Aveo, Spark, Cruze, Silverado
- **Ford** - Escort, Focus, Fiesta, Mustang, Ranger
- **Hyundai** - Accent, Elantra, Sonata, Tucson, Santa Fe
- **Nissan** - Sunny, Sentra, Versa, X-Trail, Navara
- **Honda** - Civic, Accord, Fit, CR-V, Pilot

### 🏎️ Marcas Premium
- **Audi** - A3, A4, A6, Q2, Q3, Q5, Q7, Q8, TT, e-tron
- **BMW** - Serie 1-8, X1-X7, M Series
- **Mercedes-Benz** - Clase A, B, C, E, S, CLA, GLA, GLC, GLE, Sprinter
- **Volvo** - S40, S60, S80, S90, XC40, XC60, XC90

### 🌏 Marcas Asiáticas
- **BYD** - Dolphin, Seal, Yuan Plus, Tang, Song, Han
- **Changan** - Alsvin, CS15, CS35, CS55, CS75, UNI-T
- **Chery** - Tiggo 2-8, Arrizo 3-7, QQ, Fulwin
- **Great Wall** - Wingle, Poer, Haval H1-H6, Hover
- **JAC** - T6, T8, Sunray, Refine, S2-S5, J3-J5
- **Kia** - Rio, Cerato, Optima, Picanto, Soul, Sportage
- **Mazda** - 2, 3, 6, CX-3, CX-30, CX-5, CX-7, CX-9
- **Mitsubishi** - Lancer, Galant, Mirage, Outlander, ASX
- **Suzuki** - Alto, Celerio, Baleno, Swift, Jimny, Vitara

### 🇪🇺 Marcas Europeas
- **Citroën** - C3, C4, C5, C-Elysée, Berlingo, DS3, DS4
- **Fiat** - Uno, Palio, Siena, Punto, 500, Panda, Cronos
- **Opel** - Corsa, Astra, Vectra, Kadett, Mokka, Insignia
- **Peugeot** - 206, 207, 208, 301, 306, 307, 308, 405, 406, 508
- **Renault** - 4, 5, 9, 11, 19, Clio, Mégane, Symbol, Koleos, Duster
- **Volkswagen** - Gol, Voyage, Polo, Virtus, Golf, Bora, Passat, Tiguan

### 🚙 Marcas Especializadas
- **Daihatsu** - Charade, Cuore, Terios, Rocky, Sirion
- **Isuzu** - Trooper, Rodeo, D-Max, MU-X, KB, Faster
- **Jeep** - Wrangler, Cherokee, Grand Cherokee, Compass, Renegade
- **Mahindra** - Scorpio, Bolero, Pik Up, Thar, XUV300-700
- **MG** - MG3, MG5, MG6, MG GT, ZS, HS, RX5, Marvel R
- **SsangYong** - Korando, Musso, Actyon, Rexton, Tivoli, XLV
- **Subaru** - Leone, Justy, Impreza, Legacy, Forester, Outback, WRX

## 🛠️ Instalación y Uso

### Método 1: Comando Django (Recomendado)

```bash
# Cargar datos específicos para Chile
python manage.py cargar_modelos_chile
```

### Método 2: Fixture JSON

```bash
# Cargar desde fixture
python manage.py loaddata fixtures/marcas_modelos_chile.json
```

### Método 3: Script Python

```python
# Ejecutar script directamente
python actualizar_modelos_chile.py
```

## 📊 Estadísticas

- **✅ 30 marcas** principales del mercado chileno
- **✅ 300 modelos** específicos (10 por marca)
- **✅ Cobertura completa** del parque automotriz chileno
- **✅ Incluye vehículos eléctricos** (BYD, Audi e-tron)
- **✅ Marcas premium y económicas**
- **✅ Vehículos comerciales y de pasajeros**

## 🎯 Casos de Uso

### 1. **Formularios de Registro de Vehículos**
```javascript
// Autocompletado de marca → modelo
fetch('/vehiculos/api/modelos/?marca_id=1')
  .then(response => response.json())
  .then(modelos => {
    // Cargar modelos en select
  });
```

### 2. **Reportes y Analytics**
```python
# KPIs por marca
from taller.models import Vehiculo, Marca

# Vehículos por marca
vehiculos_por_marca = Vehiculo.objects.values('marca__nombre').annotate(
    total=Count('id')
).order_by('-total')
```

### 3. **Filtros de Búsqueda**
```python
# Búsqueda de vehículos por marca/modelo
vehiculos = Vehiculo.objects.filter(
    marca__nombre__icontains='Toyota',
    modelo__nombre__icontains='Corolla'
)
```

## 🔧 Personalización

### Agregar Nuevos Modelos
```python
from taller.models import Marca, Modelo

# Obtener marca
marca = Marca.objects.get(nombre='Toyota', country='CL')

# Crear nuevo modelo
Modelo.objects.create(
    nombre='Nuevo Modelo',
    marca=marca,
    country='CL'
)
```

### Agregar Nuevas Marcas
```python
# Crear nueva marca
Marca.objects.create(
    nombre='Nueva Marca',
    country='CL'
)
```

## 📈 Beneficios

1. **🎯 Relevancia Local** - Modelos específicos del mercado chileno
2. **⚡ Rapidez** - Carga instantánea en formularios
3. **📊 Precisión** - Datos reales del parque automotriz
4. **🔄 Flexibilidad** - Fácil actualización y mantenimiento
5. **🌍 Escalabilidad** - Base para otros países

## 🚀 Próximos Pasos

- [ ] Agregar años de fabricación por modelo
- [ ] Incluir información de motores y cajas
- [ ] Agregar categorías (SUV, Sedán, Pickup, etc.)
- [ ] Integrar con APIs de fabricantes
- [ ] Crear dataset para otros países

---

**📞 Soporte:** Para consultas sobre este dataset, contactar al equipo de desarrollo.

**🔄 Actualizaciones:** Este dataset se actualiza trimestralmente con las nuevas marcas y modelos del mercado chileno.
