# ADR-006 — Identity Linkage Key

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `identity.profile.v1`
- **Sustituye:** —
- **Sustituido por:** —
- **Precede a:** ADR-007 (la identidad guest depende de cómo se define la identidad persistente)

---

## 1. Dueño del dato

El servicio de **Identity** es el único propietario del registro de identidad. Ni ERP Core ni Commerce Engine pueden crear, modificar o eliminar identidades directamente. ERP Core y Commerce Engine son consumidores del contrato `identity.profile.v1` y pueden *consultar* o *sugerir* vínculos, pero no confirmarlos unilateralmente.

---

## 2. Contexto y problema

En eGarage existen dos conceptos de "persona que pertenece a una empresa":

- **Cliente ERP**: persona que trae su auto al taller. Existe en `erp.core`. Tiene historial de órdenes de trabajo.
- **Buyer Commerce**: persona que compra en el storefront online. Existe en `commerce.engine`. Tiene historial de pedidos.

En muchos casos son la misma persona. Un mecánico que también compra repuestos online, o el dueño de un auto que tanto lleva el vehículo al taller como compra accesorios online, puede ser simultáneamente Cliente ERP y Buyer Commerce.

El problema es: **¿cómo detectar y gestionar esa coincidencia sin forzar una fusión de datos y sin usar identificadores que pueden cambiar?**

Si se usa el email como clave primaria de vínculo:
- Una persona puede tener múltiples emails.
- Un email puede cambiar.
- Dos personas distintas pueden compartir un email en sistemas diferentes (error de entrada de datos histórico).

Si se usa el RUT (Chile) o EIN (USA) como clave:
- No aplica a compradores extranjeros.
- No aplica a visitantes sin RUT registrado.
- El ERP puede tener RUTs mal formateados.

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `identity` | Propietario del `identity_id` y de los vínculos. Valida y confirma vínculos. |
| `erp.core` | Consumidor. Puede consultar si un `cliente_id` tiene `identity_id`. |
| `commerce.engine` | Consumidor. Puede consultar si un `buyer_id` tiene `identity_id`. |

---

## 4. Contratos utilizados

- `identity.profile.v1` — define la estructura del `identity_id` y los identificadores verificables.

---

## 5. Opciones consideradas

### Opción A — Email como clave primaria de vínculo

Si un Buyer y un Cliente tienen el mismo email, se consideran la misma persona y se vinculan automáticamente.

**Ventaja:** simple. Sin servicio de identidad separado.

**Desventaja:** el email puede cambiar. Una persona puede tener múltiples emails en distintos sistemas. La fusión automática puede vincular dos personas distintas. Irreversible si no hay mecanismo de desvinculación.

### Opción B — RUT / EIN como clave primaria

Si un Buyer y un Cliente tienen el mismo RUT (CL) o EIN (US), se vinculan.

**Ventaja:** identificador nacional más estable que el email.

**Desventaja:** no aplica a todos los países de eGarage. No aplica a visitantes sin documento registrado. Los RUTs en el ERP pueden estar mal formateados o ausentes.

### Opción C — `identity_id` interno e inmutable, con identificadores verificables separados (elegida)

La clave canónica es un `identity_id` generado por el servicio de identidad. Email, teléfono, RUT y EIN son **identificadores verificables**: pueden usarse para *sugerir* un vínculo, pero no son la clave primaria.

Un vínculo entre Buyer y Cliente requiere:
1. Una coincidencia de identificador verificable (email, RUT, etc.).
2. Una acción explícita de confirmación (ej: el comprador confirma por email que es el mismo cliente).
3. El servicio de identidad registra el vínculo y el método de verificación.

**Ventaja:** `identity_id` nunca cambia aunque el email cambie. La fusión es explícita y reversible. Soporta múltiples identificadores por persona. Soporta todos los países sin cambio de esquema.

---

## 6. Decisión

**Opción C.** `identity_id` es la clave canónica e inmutable. Los identificadores verificables (email, teléfono, RUT, EIN) son auxiliares y modificables.

Modelo:

```json
{
  "identity_id": "idn-uuid-7f3a2b",
  "identifiers": [
    {
      "type": "email",
      "value_normalized": "cliente@example.com",
      "verified": true
    },
    {
      "type": "rut",
      "value_normalized": "12345678-5",
      "country": "CL",
      "verified": false
    }
  ],
  "links": [
    {
      "system": "commerce",
      "entity_type": "buyer",
      "entity_id": "buyer-451",
      "status": "active"
    },
    {
      "system": "erp",
      "entity_type": "customer",
      "entity_id": "customer-983",
      "status": "active"
    }
  ],
  "linkage_status": "linked",
  "created_at": "2026-07-30T20:00:00Z",
  "linked_at": "2026-07-30T20:05:00Z"
}
```

Reglas de vínculo:

1. Una coincidencia de email puede producir una **sugerencia de vínculo**. No puede producir una fusión automática e irreversible.
2. La confirmación del vínculo requiere una acción verificable por parte del titular (ej: clic en email de confirmación).
3. Un vínculo puede deshacerse (*unlink*) sin borrar los registros individuales de Buyer o Cliente.
4. Un `identity_id` puede tener vínculos con múltiples sistemas simultáneamente.

---

## 7. Consecuencias positivas

- Un cliente puede cambiar su email en el storefront sin perder su historial de pedidos en Commerce ni su vínculo con ERP.
- Dos personas distintas con emails similares no se fusionan accidentalmente.
- El modelo soporta escenarios B2B (un taller que compra repuestos puede tener una identity vinculada tanto al propietario como al encargado de compras).
- El servicio de identidad puede evolucionar de forma independiente sin cambiar los modelos de ERP ni de Commerce.

---

## 8. Consecuencias negativas y riesgos

- Mayor complejidad conceptual que usar email directamente.
- Requiere un servicio de identidad (puede ser simple al inicio: una tabla Django con los campos del contrato).
- La confirmación explícita de vínculo puede tener una tasa de conversión baja — muchos compradores no vincularán su cuenta online con su ficha de cliente del taller.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `identity` | Nuevo servicio (o tabla Django inicial); gestiona `identity_id` y vínculos |
| `erp.core` (Cliente) | Añadir campo opcional `identity_id` como referencia externa |
| `commerce.engine` (Buyer) | Añadir campo opcional `identity_id` como referencia externa |
| Notificaciones | El flujo de confirmación de vínculo requiere un email transaccional |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: el vínculo no es responsabilidad ni de ERP ni de Commerce. Existe un servicio separado que lo gestiona.
- **Separabilidad**: si el servicio de identidad desaparece, Buyer y Cliente siguen funcionando de forma independiente. Solo se pierde la capacidad de vincularlos y de consultar la identidad cruzada.
- **write_authority**: solo `identity` puede confirmar o deshacer un vínculo. ERP y Commerce no escriben en el registro de identidad.

---

## 11. Qué ocurre si el componente desaparece

Si el servicio de identidad deja de estar disponible:

- Buyer en Commerce sigue funcionando. El comprador puede comprar, ver pedidos y gestionar su cuenta.
- Cliente en ERP sigue funcionando. El taller puede gestionar órdenes de trabajo, facturar y atender clientes.
- La capacidad de vincular ambas identidades queda suspendida hasta que el servicio se restablezca.
- Los vínculos existentes (almacenados como `identity_id` en Buyer y Cliente) siguen siendo válidos como referencia, aunque no se puedan actualizar.

---

## 12. Criterios de aceptación arquitectónica

- [ ] Un Buyer puede cambiar su email sin perder su historial de pedidos en Commerce.
- [ ] Dos Identities con el mismo email no se fusionan automáticamente sin acción del titular.
- [ ] El vínculo entre un Buyer y un Cliente requiere una confirmación verificable (ej: email confirmado).
- [ ] Un vínculo puede deshacerse sin eliminar el Buyer ni el Cliente.
- [ ] Una `identity` puede tener más de un identificador del mismo tipo (ej: dos emails) con estados distintos (verificado / no verificado).
- [ ] Un Buyer sin vínculo con un Cliente puede comprar y recibir pedidos normalmente.

---

## 13. Plan de transición

**Fase 1 (inicial):** el servicio de identidad es una tabla Django simple (`IdentityProfile`) con los campos del contrato. Sin flujo de vínculo automático. Los Buyers y los Clientes son registros independientes.

**Fase 2:** flujo de sugerencia de vínculo por email. El comprador recibe un email de confirmación cuando se detecta una coincidencia con un Cliente ERP.

**Fase 3:** vínculo por RUT verificado. Soporte para múltiples identificadores. Posible integración con proveedores de identidad externos (Google, Apple, etc.).

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- GDPR y Ley 19.628 (Chile) sobre datos personales: el vínculo de identidades entre sistemas requiere base legal (consentimiento del titular).
- Patrón Identity Map: Martin Fowler, *Patterns of Enterprise Application Architecture*.
- Auth0 / Clerk como referencia de identidad federada con múltiples identificadores por usuario.
