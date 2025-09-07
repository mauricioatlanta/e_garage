# 🧪 FIXTURES Y TESTS MATRIX - ESTRUCTURA COMPLETA

## 📊 ESTRUCTURA DE FIXTURES PROPUESTA

### Base de Datos por País

```python
# scripts/generate_fixtures.py
"""
Script para generar fixtures completas por país
Ejecutar: python manage.py runscript generate_fixtures --script-args CL US
"""

CHILE_SERVICES = {
    'categories': [
        {
            'code': 'MANT',
            'names': {
                'es': {
                    'name': 'Mantención',
                    'aliases': ['mantencion', 'revision', 'service', 'chequeo']
                }
            },
            'subcategories': [
                {
                    'code': 'ACEITE',
                    'names': {
                        'es': {
                            'name': 'Cambio de Aceite',
                            'aliases': ['aceite', 'lubricante', 'oil change']
                        }
                    },
                    'services': [
                        {
                            'code': 'ACEITE_MOTOR',
                            'names': {
                                'es': {
                                    'name': 'Cambio aceite motor',
                                    'aliases': ['aceite motor', 'lubricacion motor']
                                }
                            },
                            'estimated_time': 30,
                            'base_price': 25000
                        }
                    ]
                }
            ]
        },
        {
            'code': 'REPARACION',
            'names': {
                'es': {
                    'name': 'Reparaciones',
                    'aliases': ['reparacion', 'arreglo', 'fix', 'repair']
                }
            }
        }
    ]
}

USA_SERVICES = {
    'categories': [
        {
            'code': 'MAINT',
            'names': {
                'en': {
                    'name': 'Maintenance',
                    'aliases': ['maintenance', 'service', 'checkup', 'tune-up']
                }
            },
            'subcategories': [
                {
                    'code': 'OIL',
                    'names': {
                        'en': {
                            'name': 'Oil Change',
                            'aliases': ['oil', 'lube', 'lubrication', 'oil service']
                        }
                    },
                    'services': [
                        {
                            'code': 'ENGINE_OIL',
                            'names': {
                                'en': {
                                    'name': 'Engine Oil Change',
                                    'aliases': ['motor oil', 'engine lube']
                                }
                            },
                            'estimated_time': 30,
                            'base_price': 35  # USD
                        }
                    ]
                }
            ]
        }
    ]
}

def generate_fixtures_for_country(country_code, services_data):
    """Genera fixtures JSON para un país específico"""
    fixtures = []
    
    for cat_data in services_data['categories']:
        # Crear categoría
        categoria = {
            "model": "taller.categoriaservicio",
            "pk": generate_pk(),
            "fields": {
                "country": country_code,
                "code": cat_data['code'],
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
        fixtures.append(categoria)
        
        # Crear nombres de categoría
        for lang, name_data in cat_data['names'].items():
            name_obj = {
                "model": "taller.categoriaservicioname",
                "pk": generate_pk(),
                "fields": {
                    "categoria": categoria["pk"],
                    "language": lang,
                    "name": name_data['name'],
                    "aliases": name_data.get('aliases', [])
                }
            }
            fixtures.append(name_obj)
    
    return fixtures
```

### Fixtures por Archivo

```
fixtures/
├── 00_base_countries.json          # Países base (CL, US)
├── 01_base_languages.json          # Idiomas base (es, en)
├── 02_base_users.json              # Usuarios de prueba
├── chile/
│   ├── 10_categories_cl.json       # Categorías Chile
│   ├── 11_subcategories_cl.json    # Subcategorías Chile
│   ├── 12_services_cl.json         # Servicios Chile
│   ├── 13_names_es.json            # Nombres en español
│   ├── 14_vehicle_brands_cl.json   # Marcas vehículos Chile
│   └── 15_test_clients_cl.json     # Clientes de prueba Chile
├── usa/
│   ├── 20_categories_us.json       # Categorías USA
│   ├── 21_subcategories_us.json    # Subcategorías USA
│   ├── 22_services_us.json         # Servicios USA
│   ├── 23_names_en.json            # Nombres en inglés
│   ├── 24_vehicle_brands_us.json   # Marcas vehículos USA
│   └── 25_test_clients_us.json     # Clientes de prueba USA
└── 99_demo_documents.json          # Documentos de ejemplo
```

## 🧪 TESTS MATRIX COMPLETOS

### Test Base Class

```python
# tests/base_multilang_test.py
from django.test import TestCase, Client
from django.urls import reverse
from taller.models import *
from taller.search_engines import ServiceSearchEngine

class MultiLangTestBase(TestCase):
    """Clase base para tests multilenguaje"""
    
    fixtures = [
        'fixtures/00_base_countries.json',
        'fixtures/01_base_languages.json', 
        'fixtures/02_base_users.json',
        'fixtures/chile/10_categories_cl.json',
        'fixtures/chile/11_subcategories_cl.json',
        'fixtures/chile/12_services_cl.json',
        'fixtures/chile/13_names_es.json',
        'fixtures/usa/20_categories_us.json',
        'fixtures/usa/21_subcategories_us.json',
        'fixtures/usa/22_services_us.json',
        'fixtures/usa/23_names_en.json',
    ]
    
    COUNTRIES = ['CL', 'US']
    LANGUAGES = ['es', 'en']
    
    def setUp(self):
        self.client = Client()
        self.test_combinations = [
            ('CL', 'es'),  # Chile - Español
            ('US', 'en'),  # USA - Inglés
        ]
    
    def _get_url_for_country(self, country, view_name, **kwargs):
        """Genera URL con prefijo de país"""
        country_prefix = country.lower()
        return f'/{country_prefix}/' + reverse(view_name, kwargs=kwargs).lstrip('/')
    
    def _set_country_context(self, country, language):
        """Establece contexto de país/idioma en el cliente"""
        session = self.client.session
        session['current_country'] = country
        session['current_language'] = language
        session.save()
```

### Tests de CRUD Matrix

```python
# tests/test_crud_matrix.py
class CRUDMatrixTest(MultiLangTestBase):
    """Tests CRUD en todas las combinaciones país×idioma"""
    
    def test_client_crud_matrix(self):
        """Test CRUD de clientes en todos los países"""
        for country, language in self.test_combinations:
            with self.subTest(country=country, language=language):
                self._test_client_crud(country, language)
    
    def _test_client_crud(self, country, language):
        """Test completo CRUD para un país/idioma específico"""
        self._set_country_context(country, language)
        
        # CREATE
        client_data = {
            'name': f'Test Client {country}',
            'email': f'test.{country.lower()}@example.com',
            'phone': '+1234567890' if country == 'US' else '+56912345678',
            'country': country
        }
        
        url = self._get_url_for_country(country, 'client_create')
        response = self.client.post(url, client_data)
        self.assertEqual(response.status_code, 302)  # Redirect after create
        
        # READ
        client = Cliente.objects.filter(country=country).first()
        self.assertIsNotNone(client)
        self.assertEqual(client.country, country)
        
        detail_url = self._get_url_for_country(country, 'client_detail', pk=client.pk)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        
        # UPDATE
        client_data['name'] = f'Updated Client {country}'
        update_url = self._get_url_for_country(country, 'client_update', pk=client.pk)
        response = self.client.post(update_url, client_data)
        self.assertEqual(response.status_code, 302)
        
        client.refresh_from_db()
        self.assertEqual(client.name, f'Updated Client {country}')
        
        # DELETE
        delete_url = self._get_url_for_country(country, 'client_delete', pk=client.pk)
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(Cliente.objects.filter(pk=client.pk).exists())
    
    def test_vehicle_crud_matrix(self):
        """Test CRUD de vehículos en todos los países"""
        for country, language in self.test_combinations:
            with self.subTest(country=country, language=language):
                self._test_vehicle_crud(country, language)
    
    def test_service_crud_matrix(self):
        """Test CRUD de servicios en todos los países"""
        for country, language in self.test_combinations:
            with self.subTest(country=country, language=language):
                self._test_service_crud(country, language)
```

### Tests de Búsqueda Fuzzy

```python
# tests/test_search_matrix.py
class SearchMatrixTest(MultiLangTestBase):
    """Tests de búsqueda en todas las combinaciones"""
    
    def test_fuzzy_search_matrix(self):
        """Test búsqueda fuzzy en todos los idiomas"""
        search_cases = {
            'CL': {
                'es': [
                    ('aceite', ['cambio de aceite', 'aceite motor']),
                    ('mantencion', ['mantención', 'mantenimiento']),
                    ('frenos', ['freno', 'brake', 'pastillas']),
                    ('neumaticos', ['neumático', 'llanta', 'tire']),
                    ('revision', ['revisión técnica', 'inspección']),
                ]
            },
            'US': {
                'en': [
                    ('oil', ['oil change', 'engine oil', 'lubrication']),
                    ('maintenance', ['service', 'checkup', 'tune-up']),
                    ('brake', ['brakes', 'brake service', 'brake pads']),
                    ('tire', ['tires', 'wheel', 'tire service']),
                    ('inspection', ['check', 'diagnostic', 'test']),
                ]
            }
        }
        
        for country, lang_data in search_cases.items():
            for language, test_cases in lang_data.items():
                with self.subTest(country=country, language=language):
                    engine = ServiceSearchEngine(country, language)
                    
                    for query, expected_matches in test_cases:
                        with self.subTest(query=query):
                            results = engine.search(query)
                            result_names = [r.get_name(language).lower() for r in results]
                            
                            # Al menos uno de los matches esperados debe estar
                            found_match = any(
                                any(expected.lower() in name for name in result_names)
                                for expected in expected_matches
                            )
                            self.assertTrue(
                                found_match,
                                f"Query '{query}' no encontró matches esperados {expected_matches} en {result_names}"
                            )
    
    def test_cross_country_isolation(self):
        """Verificar que búsquedas no crucen países"""
        # Buscar servicio específico de Chile desde USA
        cl_engine = ServiceSearchEngine('CL', 'es')
        cl_results = cl_engine.search('aceite motor')
        
        us_engine = ServiceSearchEngine('US', 'en')
        us_results = us_engine.search('aceite motor')  # Buscar término español en USA
        
        # Los resultados de USA no deben incluir servicios de Chile
        us_service_countries = {r.country for r in us_results}
        self.assertNotIn('CL', us_service_countries)
    
    def test_alias_search_effectiveness(self):
        """Test que aliases funcionen correctamente"""
        alias_tests = [
            ('CL', 'es', 'mantencion', 'mantención'),  # Alias sin tilde
            ('CL', 'es', 'oil change', 'cambio de aceite'),  # Alias en inglés
            ('US', 'en', 'lube', 'lubrication'),  # Alias corto
            ('US', 'en', 'tune-up', 'maintenance'),  # Alias compuesto
        ]
        
        for country, language, alias, expected_service in alias_tests:
            with self.subTest(country=country, language=language, alias=alias):
                engine = ServiceSearchEngine(country, language)
                results = engine.search(alias)
                
                result_names = [r.get_name(language).lower() for r in results]
                self.assertTrue(
                    any(expected_service.lower() in name for name in result_names),
                    f"Alias '{alias}' no encontró '{expected_service}' en {result_names}"
                )
```

### Tests de Consistencia

```python
# tests/test_consistency_matrix.py
class ConsistencyMatrixTest(MultiLangTestBase):
    """Tests de consistencia de datos entre países"""
    
    def test_document_consistency_validation(self):
        """Test que documentos no mezclen países"""
        # Crear cliente en Chile
        cl_client = Cliente.objects.create(
            name='Cliente Chile',
            country='CL',
            email='chile@test.com'
        )
        
        # Crear vehículo en USA
        us_vehicle = Vehiculo.objects.create(
            country='US',
            placa='US123',
            # ... otros campos
        )
        
        # Intentar crear documento mezclando países debe fallar
        with self.assertRaises(ValidationError):
            documento = Documento.objects.create(
                cliente=cl_client,
                vehiculo=us_vehicle,  # ERROR: Países diferentes
                # ... otros campos
            )
    
    def test_service_hierarchy_consistency(self):
        """Test que jerarquía servicio→subcategoría→categoría sea consistente"""
        for country in self.COUNTRIES:
            with self.subTest(country=country):
                servicios = Servicio.objects.filter(country=country)
                
                for servicio in servicios:
                    # Verificar que subcategoría tenga mismo país
                    self.assertEqual(
                        servicio.subcategoria.country,
                        servicio.country,
                        f"Servicio {servicio} y subcategoría tienen países diferentes"
                    )
                    
                    # Verificar que categoría tenga mismo país
                    self.assertEqual(
                        servicio.subcategoria.categoria.country,
                        servicio.country,
                        f"Servicio {servicio} y categoría tienen países diferentes"
                    )
    
    def test_name_objects_consistency(self):
        """Test que objetos *Name referencien objetos del mismo país"""
        for country in self.COUNTRIES:
            with self.subTest(country=country):
                # Test categorías
                categorias = CategoriaServicio.objects.filter(country=country)
                for categoria in categorias:
                    names = CategoriaServicioName.objects.filter(categoria=categoria)
                    self.assertTrue(names.exists(), f"Categoría {categoria} sin nombres")
                
                # Test servicios
                servicios = Servicio.objects.filter(country=country)
                for servicio in servicios:
                    names = ServicioName.objects.filter(servicio=servicio)
                    self.assertTrue(names.exists(), f"Servicio {servicio} sin nombres")
```

### Tests de Performance

```python
# tests/test_performance_matrix.py
class PerformanceMatrixTest(MultiLangTestBase):
    """Tests de performance en escenarios reales"""
    
    def test_search_performance(self):
        """Test que búsquedas sean rápidas en todos los países"""
        import time
        
        queries = ['aceite', 'oil', 'frenos', 'brake', 'revision', 'service']
        
        for country, language in self.test_combinations:
            with self.subTest(country=country, language=language):
                engine = ServiceSearchEngine(country, language)
                
                for query in queries:
                    start_time = time.time()
                    results = engine.search(query)
                    search_time = time.time() - start_time
                    
                    # Búsquedas deben ser < 100ms
                    self.assertLess(
                        search_time, 0.1,
                        f"Búsqueda '{query}' en {country}/{language} tardó {search_time:.3f}s"
                    )
    
    def test_context_loading_performance(self):
        """Test que carga de contexto sea eficiente"""
        import time
        from django.test import RequestFactory
        from taller.context_processors import unified_context
        
        factory = RequestFactory()
        
        for country, language in self.test_combinations:
            with self.subTest(country=country, language=language):
                request = factory.get(f'/{country.lower()}/')
                request.session = {
                    'current_country': country,
                    'current_language': language
                }
                
                start_time = time.time()
                context = unified_context(request)
                load_time = time.time() - start_time
                
                # Carga de contexto debe ser < 50ms
                self.assertLess(
                    load_time, 0.05,
                    f"Contexto {country}/{language} tardó {load_time:.3f}s"
                )
                
                # Verificar que contexto tenga datos esperados
                self.assertIn('current_country', context)
                self.assertIn('current_language', context)
                self.assertEqual(context['current_country'], country)
```

## 🏃‍♂️ COMANDO DE EJECUCIÓN COMPLETO

```bash
# Cargar todas las fixtures
python manage.py loaddata fixtures/00_base_countries.json
python manage.py loaddata fixtures/01_base_languages.json  
python manage.py loaddata fixtures/02_base_users.json
python manage.py loaddata fixtures/chile/*.json
python manage.py loaddata fixtures/usa/*.json
python manage.py loaddata fixtures/99_demo_documents.json

# Ejecutar tests matrix completos
python manage.py test tests.test_crud_matrix -v 2
python manage.py test tests.test_search_matrix -v 2  
python manage.py test tests.test_consistency_matrix -v 2
python manage.py test tests.test_performance_matrix -v 2

# Ejecutar todos los tests multilenguaje
python manage.py test tests.test_*_matrix -v 2 --parallel
```

## 📊 MÉTRICAS DE ÉXITO

- ✅ Tests matrix: 100% de cobertura país×idioma
- ✅ Performance: < 100ms búsquedas, < 50ms contexto
- ✅ Consistencia: 0 datos cruzados entre países
- ✅ Fuzzy search: > 90% precisión con aliases
- ✅ Fixtures: Datos reales para demo en CL/US

¿Quieres que genere algunos de estos archivos ahora, o prefieres tener la estructura completa documentada para implementar después?
