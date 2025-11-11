# 🌎 API Unificada de Ubicaciones - Multi-País

## 📍 **ENDPOINT PRINCIPAL**

```
GET /api/locations
```

**Descripción:** API unificada para obtener estados/departamentos y ciudades de todos los países soportados.

---

## 📊 **PARÁMETROS**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `country` | string | ✅ Sí | Código de país (CL, US, BR, PE, VE) |
| `state` | string | ❌ No | Código de estado/departamento (ej: GA, LIM, SP) |

---

## 🔄 **COMPORTAMIENTO**

### **Caso 1: Solo `country` → Devuelve Estados/Departamentos**

```http
GET /api/locations?country=PE
```

**Respuesta:**
```json
{
  "states": [
    {
      "id": 1,
      "name": "Lima",
      "code": "LIM"
    },
    {
      "id": 2,
      "name": "Arequipa",
      "code": "ARE"
    },
    {
      "id": 3,
      "name": "Cusco",
      "code": "CUS"
    }
    // ... más estados
  ]
}
```

---

### **Caso 2: `country` + `state` → Devuelve Ciudades**

```http
GET /api/locations?country=PE&state=LIM
```

**Respuesta:**
```json
{
  "cities": [
    {
      "id": 101,
      "name": "Lima"
    },
    {
      "id": 102,
      "name": "Callao"
    },
    {
      "id": 103,
      "name": "San Juan de Lurigancho"
    }
    // ... más ciudades
  ]
}
```

---

## 🌐 **EJEMPLOS POR PAÍS**

### **🇨🇱 Chile**

```javascript
// Obtener regiones de Chile
fetch('/api/locations?country=CL')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // [{id: 1, name: "Región Metropolitana", code: "RM"}, ...]
  });

// Obtener ciudades de la Región Metropolitana
fetch('/api/locations?country=CL&state=RM')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    // [{id: 1, name: "Santiago"}, {id: 2, name: "Providencia"}, ...]
  });
```

---

### **🇺🇸 USA**

```javascript
// Obtener estados de USA
fetch('/api/locations?country=US')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // [{id: 1, name: "California", code: "CA"}, 
    //  {id: 2, name: "New York", code: "NY"}, ...]
  });

// Obtener ciudades de Georgia
fetch('/api/locations?country=US&state=GA')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    // [{id: 101, name: "Atlanta"}, {id: 102, name: "Savannah"}, ...]
  });
```

---

### **🇧🇷 Brasil**

```javascript
// Obtener estados do Brasil
fetch('/api/locations?country=BR')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // [{id: 1, name: "São Paulo", code: "SP"}, 
    //  {id: 2, name: "Rio de Janeiro", code: "RJ"}, ...]
  });

// Obtener cidades de São Paulo
fetch('/api/locations?country=BR&state=SP')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    // [{id: 201, name: "São Paulo"}, {id: 202, name: "Campinas"}, ...]
  });
```

---

### **🇵🇪 Perú**

```javascript
// Obtener departamentos de Perú
fetch('/api/locations?country=PE')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // [{id: 1, name: "Lima", code: "LIM"}, 
    //  {id: 2, name: "Arequipa", code: "ARE"}, ...]
  });

// Obtener ciudades de Lima
fetch('/api/locations?country=PE&state=LIM')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    // [{id: 301, name: "Lima"}, {id: 302, name: "Callao"}, ...]
  });
```

---

### **🇻🇪 Venezuela**

```javascript
// Obtener estados de Venezuela
fetch('/api/locations?country=VE')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // [{id: 1, name: "Distrito Capital", code: "DC"}, 
    //  {id: 2, name: "Miranda", code: "MI"}, ...]
  });

// Obtener ciudades del Distrito Capital
fetch('/api/locations?country=VE&state=DC')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    // [{id: 401, name: "Caracas"}, ...]
  });
```

---

## 🔗 **ENDPOINTS ALTERNATIVOS**

### **Obtener Estados por País (REST-style)**

```http
GET /api/locations/states/<country_code>/
```

**Ejemplo:**
```javascript
fetch('/api/locations/states/PE/')
  .then(r => r.json())
  .then(data => {
    console.log(data.states);
    // Incluye sales_tax de cada estado
  });
```

**Respuesta:**
```json
{
  "states": [
    {
      "id": 1,
      "name": "Lima",
      "code": "LIM",
      "sales_tax": 18.0
    }
    // ...
  ]
}
```

---

### **Obtener Ciudades por Estado (REST-style)**

```http
GET /api/locations/cities/<state_id>/
```

**Ejemplo:**
```javascript
fetch('/api/locations/cities/25/')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    console.log(data.state);  // Nombre del estado
    console.log(data.country);  // Código de país
  });
```

**Respuesta:**
```json
{
  "cities": [
    {
      "id": 301,
      "name": "Lima",
      "population": 10000000,
      "is_capital": true
    }
    // ...
  ],
  "state": "Lima",
  "country": "PE"
}
```

---

## 📝 **EJEMPLO COMPLETO EN FORMULARIO**

### **HTML:**

```html
<select id="country">
  <option value="">Seleccione país...</option>
  <option value="CL">Chile</option>
  <option value="US">USA</option>
  <option value="BR">Brasil</option>
  <option value="PE">Perú</option>
  <option value="VE">Venezuela</option>
</select>

<select id="state" disabled>
  <option value="">Seleccione estado...</option>
</select>

<select id="city" disabled>
  <option value="">Seleccione ciudad...</option>
</select>
```

---

### **JavaScript:**

```javascript
const countrySelect = document.getElementById('country');
const stateSelect = document.getElementById('state');
const citySelect = document.getElementById('city');

// Cargar estados cuando se selecciona país
countrySelect.addEventListener('change', function() {
  const country = this.value;
  
  // Limpiar selects dependientes
  stateSelect.innerHTML = '<option value="">Cargando...</option>';
  citySelect.innerHTML = '<option value="">Seleccione ciudad...</option>';
  stateSelect.disabled = true;
  citySelect.disabled = true;
  
  if (country) {
    // Cargar estados del país
    fetch(`/api/locations?country=${country}`)
      .then(response => response.json())
      .then(data => {
        stateSelect.innerHTML = '<option value="">Seleccione estado...</option>';
        
        data.states.forEach(state => {
          const option = document.createElement('option');
          option.value = state.code;  // Usar código como value
          option.textContent = state.name;
          option.dataset.stateId = state.id;  // Guardar ID para ciudades
          stateSelect.appendChild(option);
        });
        
        stateSelect.disabled = false;
      })
      .catch(error => {
        console.error('Error cargando estados:', error);
        stateSelect.innerHTML = '<option value="">Error cargando estados</option>';
      });
  }
});

// Cargar ciudades cuando se selecciona estado
stateSelect.addEventListener('change', function() {
  const country = countrySelect.value;
  const stateCode = this.value;
  
  // Limpiar ciudades
  citySelect.innerHTML = '<option value="">Cargando...</option>';
  citySelect.disabled = true;
  
  if (country && stateCode) {
    // Cargar ciudades del estado
    fetch(`/api/locations?country=${country}&state=${stateCode}`)
      .then(response => response.json())
      .then(data => {
        citySelect.innerHTML = '<option value="">Seleccione ciudad...</option>';
        
        data.cities.forEach(city => {
          const option = document.createElement('option');
          option.value = city.id;
          option.textContent = city.name;
          citySelect.appendChild(option);
        });
        
        citySelect.disabled = false;
      })
      .catch(error => {
        console.error('Error cargando ciudades:', error);
        citySelect.innerHTML = '<option value="">Error cargando ciudades</option>';
      });
  }
});
```

---

## ⚡ **VENTAJAS DE ESTA API**

### **1. Unificada:**
- ✅ Un solo endpoint para todos los países
- ✅ No necesitas saber las diferencias entre países
- ✅ Código frontend reutilizable

### **2. Consistente:**
- ✅ Siempre devuelve `{states: [...]}` o `{cities: [...]}`
- ✅ Estructura predecible
- ✅ Fácil de documentar

### **3. Flexible:**
- ✅ Query params (simple)
- ✅ Path params alternativos (REST-style)
- ✅ Incluye metadata útil (sales_tax, population)

### **4. Escalable:**
- ✅ Fácil agregar más países
- ✅ Fácil agregar más campos
- ✅ Optimizado con índices

---

## 🔍 **EJEMPLOS DE QUERIES**

### **jQuery:**

```javascript
// Cargar estados
$.get('/api/locations', {country: 'PE'}, function(data) {
    data.states.forEach(state => {
        $('#state').append(
            $('<option>').val(state.code).text(state.name)
        );
    });
});
```

### **Fetch API:**

```javascript
// Async/await
async function loadStates(country) {
    const response = await fetch(`/api/locations?country=${country}`);
    const data = await response.json();
    return data.states;
}

async function loadCities(country, stateCode) {
    const response = await fetch(`/api/locations?country=${country}&state=${stateCode}`);
    const data = await response.json();
    return data.cities;
}

// Uso
const states = await loadStates('PE');
const cities = await loadCities('PE', 'LIM');
```

### **Axios:**

```javascript
// Con Axios
axios.get('/api/locations', {
    params: {country: 'BR', state: 'SP'}
}).then(response => {
    console.log(response.data.cities);
});
```

---

## 🚀 **USO EN REACT/VUE**

### **React:**

```jsx
import { useState, useEffect } from 'react';

function LocationSelector() {
  const [country, setCountry] = useState('');
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  
  // Cargar estados cuando cambia país
  useEffect(() => {
    if (country) {
      fetch(`/api/locations?country=${country}`)
        .then(r => r.json())
        .then(data => setStates(data.states));
    }
  }, [country]);
  
  const loadCities = (stateCode) => {
    fetch(`/api/locations?country=${country}&state=${stateCode}`)
      .then(r => r.json())
      .then(data => setCities(data.cities));
  };
  
  return (
    <>
      <select onChange={(e) => setCountry(e.target.value)}>
        <option value="">Seleccione país</option>
        <option value="CL">Chile</option>
        <option value="US">USA</option>
        <option value="BR">Brasil</option>
        <option value="PE">Perú</option>
        <option value="VE">Venezuela</option>
      </select>
      
      <select onChange={(e) => loadCities(e.target.value)}>
        <option value="">Seleccione estado</option>
        {states.map(s => (
          <option key={s.id} value={s.code}>{s.name}</option>
        ))}
      </select>
      
      <select>
        <option value="">Seleccione ciudad</option>
        {cities.map(c => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
    </>
  );
}
```

---

## 🛡️ **MANEJO DE ERRORES**

### **Error: Country no proporcionado**

```http
GET /api/locations
```

**Respuesta:** `400 Bad Request`
```json
{
  "error": "Parameter \"country\" is required"
}
```

---

### **Error: Estado no encontrado**

```http
GET /api/locations?country=PE&state=INVALID
```

**Respuesta:** `200 OK`
```json
{
  "cities": []
}
```

*Nota: Devuelve array vacío en lugar de error 404 para mejor UX*

---

### **Error: País no válido**

```http
GET /api/locations?country=XX
```

**Respuesta:** `200 OK`
```json
{
  "states": []
}
```

---

## 📋 **ENDPOINTS ALTERNATIVOS (REST-STYLE)**

### **1. Estados por País**

```http
GET /api/locations/states/<country_code>/
```

**Ejemplos:**
```javascript
// Perú
fetch('/api/locations/states/PE/')
  .then(r => r.json())
  .then(data => console.log(data.states));

// Brasil
fetch('/api/locations/states/BR/')
  .then(r => r.json())
  .then(data => console.log(data.states));
```

**Respuesta incluye sales_tax:**
```json
{
  "states": [
    {
      "id": 1,
      "name": "Lima",
      "code": "LIM",
      "sales_tax": 18.0
    }
  ]
}
```

---

### **2. Ciudades por Estado ID**

```http
GET /api/locations/cities/<state_id>/
```

**Ejemplo:**
```javascript
fetch('/api/locations/cities/25/')
  .then(r => r.json())
  .then(data => {
    console.log(data.cities);
    console.log(data.state);  // Nombre del estado
    console.log(data.country);  // Código de país
  });
```

**Respuesta incluye metadata:**
```json
{
  "cities": [
    {
      "id": 301,
      "name": "Lima",
      "population": 10000000,
      "is_capital": true
    }
  ],
  "state": "Lima",
  "country": "PE"
}
```

---

## 🗺️ **CÓDIGOS DE ESTADOS/DEPARTAMENTOS**

### **Chile (CL):**
- RM - Región Metropolitana
- VAL - Valparaíso
- BIO - Biobío
- *... 13 regiones más*

### **USA (US):**
- CA - California
- NY - New York
- TX - Texas
- FL - Florida
- GA - Georgia
- *... 45 estados más*

### **Brasil (BR):**
- SP - São Paulo
- RJ - Rio de Janeiro
- MG - Minas Gerais
- BA - Bahia
- *... 23 estados más*

### **Perú (PE):**
- LIM - Lima
- ARE - Arequipa
- CUS - Cusco
- LAL - La Libertad
- *... 21 departamentos más*

### **Venezuela (VE):**
- DC - Distrito Capital
- MI - Miranda
- CAR - Carabobo
- ZUL - Zulia
- *... 20 estados más*

---

## 🔧 **INTEGRACIÓN CON FORMULARIOS**

### **Formulario de Cliente:**

```javascript
// En formulario de cliente
function setupLocationFields(countryCode) {
    const stateSelect = document.getElementById('id_estado');
    const citySelect = document.getElementById('id_ciudad');
    
    // Cargar estados
    fetch(`/api/locations?country=${countryCode}`)
        .then(r => r.json())
        .then(data => {
            stateSelect.innerHTML = '<option value="">Seleccione...</option>';
            data.states.forEach(state => {
                const opt = document.createElement('option');
                opt.value = state.id;
                opt.textContent = state.name;
                opt.dataset.code = state.code;
                stateSelect.appendChild(opt);
            });
        });
    
    // Listener para ciudades
    stateSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const stateCode = selectedOption.dataset.code;
        
        if (stateCode) {
            fetch(`/api/locations?country=${countryCode}&state=${stateCode}`)
                .then(r => r.json())
                .then(data => {
                    citySelect.innerHTML = '<option value="">Seleccione...</option>';
                    data.cities.forEach(city => {
                        const opt = document.createElement('option');
                        opt.value = city.id;
                        opt.textContent = city.name;
                        citySelect.appendChild(opt);
                    });
                    citySelect.disabled = false;
                });
        }
    });
}

// Detectar país automáticamente
const userCountry = '{{ request.user.empresa.pais }}';  // Django template
setupLocationFields(userCountry);
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

- [✅] API creada en `taller/ubicacion/api.py`
- [✅] URLs configuradas en `taller/ubicacion/urls.py`
- [✅] Montada en `gestion_taller/urls.py` como `/api/locations`
- [✅] Soporta query params (simple)
- [✅] Soporta path params (REST-style)
- [✅] Incluye metadata útil (sales_tax, population)
- [✅] Manejo de errores consistente
- [✅] Documentación completa

---

## 🎯 **URLS FINALES**

```
✅ /api/locations?country=CL
✅ /api/locations?country=US&state=GA
✅ /api/locations/states/PE/
✅ /api/locations/cities/25/
```

---

## 🌟 **BENEFICIOS**

1. **Simplicidad:** Un endpoint para todo
2. **Consistencia:** Misma estructura para todos los países
3. **Flexibilidad:** Query params o path params
4. **Escalabilidad:** Fácil agregar más países
5. **Performance:** Queries optimizados con índices
6. **Metadata:** Incluye sales_tax, population, etc.

---

## 📚 **ARCHIVOS CREADOS**

- ✅ `taller/ubicacion/api.py` - Vistas de la API
- ✅ `taller/ubicacion/urls.py` - URLs de la API
- ✅ `API_UBICACIONES_UNIFICADA.md` - Documentación completa

---

## 🎉 **RESUMEN**

✅ **API unificada funcionando** para 5 países  
✅ **3 endpoints disponibles** (query, states, cities)  
✅ **Documentación completa** con ejemplos  
✅ **JavaScript ready** para formularios  
✅ **React/Vue ready** para SPAs  

**Siguiente:** Integrar en formularios de clientes y empresas

