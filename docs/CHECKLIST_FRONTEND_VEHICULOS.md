# Checklist Frontend Vehículos (US/CL)

Objetivo: URLs correctas por país, sin duplicación DAL/Select2.

## 1) Endpoints vía data-* (regla de oro)

**Regla:** Todo endpoint se pasa por `data-*` desde Django (via `country_url`) y el JS solo lee `dataset`.

### Templates que deben tener `#vehiculos-endpoints`

```html
<div id="vehiculos-endpoints" style="display:none;"
     data-ep-modelos="{% country_url 'vehiculos:modelos_por_marca_api' app_namespace='direct' %}"
     data-ep-modelos-usa="{% country_url 'vehiculos:api_modelos_usa' app_namespace='direct' %}"
     data-ep-clientes="{% country_url 'vehiculos:api_busqueda_clientes' app_namespace='direct' %}"
     data-ep-crear-cliente="{% country_url 'clientes:crear_cliente' app_namespace='direct' %}"
     data-ep-agregar-motor="{% country_url 'vehiculos:ajax_agregar_motor' app_namespace='direct' %}"
     data-ep-agregar-caja="{% country_url 'vehiculos:ajax_agregar_caja' app_namespace='direct' %}"
     data-ep-motores="{% country_url 'vehiculos:ajax_motores_por_modelo' app_namespace='direct' %}"
     data-ep-cajas="{% country_url 'vehiculos:ajax_cajas_por_modelo' app_namespace='direct' %}"></div>
```

### En JS

```javascript
const ep = document.getElementById('vehiculos-endpoints').dataset;
const endpoint = ep.epModelos;  // camelCase: data-ep-modelos → epModelos
```

## 2) DAL/Select2 duplicado

**Regla:** Si usas DAL, deja que `{{ form.media }}` cargue lo necesario. No cargues Select2 a mano en base + template + bundles al mismo tiempo.

### Buscar duplicados

```bash
rg -n "autocomplete_light|dal_select2|select2(\.full)?\.js|jquery(\.min)?\.js" templates/ taller/static/ frontend/ -S
```

### Verificar en runtime (browser)

- **Network** → filtrar por `select2` y `autocomplete_light`
- **Console:**

```javascript
[...document.scripts].map(s=>s.src).filter(s=>s.includes('select2')||s.includes('autocomplete_light'))
```

Debe cargarse **una sola vez** cada script.

## 3) Test final

### En `/us/en/vehiculos/crear/`

- [ ] Seleccionar marca → modelos cargan (200)
- [ ] Cliente autocomplete funciona (200)
- [ ] Sin errores "DAL duplicate" en consola

### En `/cl/es/vehiculos/crear/`

- [ ] Seleccionar marca → modelos cargan (200)
- [ ] **Nunca** debe aparecer una llamada a `/us/...` en Network
