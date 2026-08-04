# Test Factories — eGarage

`taller/tests/factories.py` — infraestructura de testing sin dependencias externas.

## Por qué existen

Django `TestCase` aísla cada test en una transacción. El modelo `Empresa` requiere
un `User` (`OneToOneField`, NOT NULL). Sin esta capa, cada test file resolvía la
dependencia a su manera, produciendo colisiones de `user_id` cuando los tests corren
en el mismo proceso.

Las factories garantizan:
- `username` y `email` únicos por llamada (contador de hilo seguro).
- Dependencias mínimas, nada más.
- Compatibles con `TestCase.setUp()` y con pytest fixtures.

---

## Factories disponibles

### `UserFactory(**kwargs) → User`

Crea un `User` con `username` y `email` únicos.

```python
from taller.tests.factories import UserFactory

u = UserFactory()
u = UserFactory(username="alice", email="alice@corp.cl")
```

**Crea automáticamente:** nada (es la factory hoja).  
**No crea:** ninguna relación adicional.

---

### `EmpresaFactory(*, with_config=False, **kwargs) → Empresa`

Crea una `Empresa` con su propio `User`.

```python
from taller.tests.factories import EmpresaFactory

e = EmpresaFactory()                        # Chile, WORKSHOP
e = EmpresaFactory(pais="US")              # USA, moneda auto → USD
e = EmpresaFactory(pais="CL", plan="growth")
e = EmpresaFactory(with_config=True)       # + ConfiguracionEmpresa
e = EmpresaFactory(user=existing_user)     # reutiliza un User existente
```

**Crea automáticamente:** `User` (a menos que se pase `user=`).  
**No crea:** `ConfiguracionEmpresa` (usar `with_config=True` si se necesita).  
**Nota:** `slug`, `fecha_fin`, `moneda` y `zona_horaria` son auto-set por `Empresa.save()`.

---

### `ConfiguracionEmpresaFactory(*, empresa=None, **kwargs) → ConfiguracionEmpresa`

Crea una `ConfiguracionEmpresa` para una `Empresa`.

```python
from taller.tests.factories import EmpresaFactory, ConfiguracionEmpresaFactory

e   = EmpresaFactory()
cfg = ConfiguracionEmpresaFactory(empresa=e)
cfg = ConfiguracionEmpresaFactory(empresa=e, rubro_principal="DETAILING")
cfg = ConfiguracionEmpresaFactory()        # crea su propia Empresa
```

**Crea automáticamente:** `Empresa` (+ `User`) si no se provee `empresa`.  
**Defaults:** `rubro_principal="WORKSHOP"`, `nombre_publico=empresa.nombre_taller`.  
**Equivalente al acceso via workspace:** `empresa.config` (OneToOne reverse).

---

### `ClienteFactory(*, empresa=None, **kwargs) → Cliente`

```python
from taller.tests.factories import EmpresaFactory, ClienteFactory

e  = EmpresaFactory()
c1 = ClienteFactory(empresa=e)
c2 = ClienteFactory(empresa=e, nombre="Juan", email="juan@corp.cl")
c  = ClienteFactory()                     # crea su propia Empresa
```

**Crea automáticamente:** `Empresa` (+ `User`) si no se provee.  
**No crea:** `Vehiculo`, `Documento`.

---

### `VehiculoFactory(*, empresa=None, cliente=None, **kwargs) → Vehiculo`

`cliente` es opcional — `Vehiculo.cliente` es `null=True` en el modelo.

```python
from taller.tests.factories import EmpresaFactory, ClienteFactory, VehiculoFactory

e = EmpresaFactory()
v = VehiculoFactory(empresa=e)                        # sin cliente
v = VehiculoFactory(empresa=e, cliente=ClienteFactory(empresa=e))
v = VehiculoFactory(empresa=e, patente="ABC123", anio=2022)
```

**Crea automáticamente:** `Empresa` (+ `User`) si no se provee.  
**No crea:** `Cliente` automáticamente (pasar explícitamente si se necesita).  
**Patente única:** auto-generada como `"T<n>"` para evitar colisiones.

---

### `DocumentoFactory(*, empresa=None, cliente=None, vehiculo=None, **kwargs) → Documento`

`cliente` es requerido por la BD (NOT NULL). Si no se pasa, la factory lo crea.  
`vehiculo` es opcional.

```python
from taller.tests.factories import (
    EmpresaFactory, ClienteFactory, VehiculoFactory, DocumentoFactory
)

e = EmpresaFactory()
d = DocumentoFactory(empresa=e)           # cliente auto-creado
d = DocumentoFactory(empresa=e, tipo="PRES", estado="EMITIDO")

c = ClienteFactory(empresa=e)
v = VehiculoFactory(empresa=e, cliente=c)
d = DocumentoFactory(empresa=e, cliente=c, vehiculo=v)
```

**Crea automáticamente:** `Empresa` (si falta) + `Cliente` (si falta).  
**No crea:** `Vehiculo` ni líneas de detalle.  
**Nota:** `estado="BORRADOR"` por default para evitar que `Documento.save()` genere número de secuencia.

---

### `RepuestoFactory(*, empresa=None, **kwargs) → Repuesto`

```python
from taller.tests.factories import EmpresaFactory, RepuestoFactory
from decimal import Decimal

e = EmpresaFactory()
r = RepuestoFactory(empresa=e)
r = RepuestoFactory(empresa=e, cantidad_stock=0, stock_minimo=5)
r = RepuestoFactory(empresa=e, precio_venta=Decimal("500.00"))
```

**Crea automáticamente:** `Empresa` (+ `User`) si no se provee.  
**Defaults:** `precio_venta=10000.00`, `cantidad_stock=5`, `stock_minimo=2`.

---

## Patrones comunes

### Test multi-tenant (dos empresas independientes)

```python
from taller.tests.factories import EmpresaFactory, ClienteFactory

class MiTest(TestCase):
    def setUp(self):
        self.empresa_a = EmpresaFactory(pais="CL")
        self.empresa_b = EmpresaFactory(pais="US")
        self.cliente_a = ClienteFactory(empresa=self.empresa_a)
        self.cliente_b = ClienteFactory(empresa=self.empresa_b)
```

### Test de workspace con configuración

```python
from taller.tests.factories import EmpresaFactory, ConfiguracionEmpresaFactory

class WorkspaceTest(TestCase):
    def setUp(self):
        self.empresa = EmpresaFactory(pais="CL")
        self.config  = ConfiguracionEmpresaFactory(
            empresa=self.empresa,
            rubro_principal="DETAILING",
        )
        # Accesible como self.empresa.config
```

### Test de dashboard con widgets

```python
from taller.tests.factories import EmpresaFactory, DocumentoFactory, RepuestoFactory

class DashboardTest(TestCase):
    def setUp(self):
        self.empresa   = EmpresaFactory()
        self.documento = DocumentoFactory(empresa=self.empresa, estado="EMITIDO")
        self.repuesto  = RepuestoFactory(empresa=self.empresa, cantidad_stock=0)
```

---

## Lo que NO reemplaza

- **`conftest.py`** — los fixtures existentes (`empresa_chile`, `empresa_peru`, etc.)
  siguen siendo válidos para tests pytest-style (función + `db` fixture).  
  Las factories son para `TestCase.setUp()` donde los fixtures de pytest no aplican.

- **`TenantIsolationBaseTest` / `RBACSegregationBaseTest`** — base classes con
  lógica de negocio específica (roles de equipo, grupos). No reemplazar con factories.

---

## Qué NO se modifica en producción

Esta capa solo existe dentro de `taller/tests/`. Cero impacto en:
- Modelos de producción
- Migraciones
- Vistas
- Servicios
- Signals
