# ADR-007 — Guest Identity

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `identity.profile.v1`
- **Sustituye:** —
- **Sustituido por:** —
- **Depende de:** ADR-006 (el modelo de Guest Buyer solo puede definirse después de establecer qué es una Identity persistente)

---

## 1. Dueño del dato

- **Anonymous Session**: `commerce.engine` (estado técnico temporal del navegador o canal).
- **Guest Buyer**: `commerce.engine` (datos mínimos del comprador para el pedido).
- **Identity persistente**: `identity` (si el guest decide crear una cuenta o vincular después de comprar).

No se crea un registro de `identity` automáticamente por cada checkout invitado. La creación de Identity es siempre explícita y voluntaria.

---

## 2. Contexto y problema

Un comprador puede querer comprar sin crear una cuenta. Este caso de uso — llamado *guest checkout* — es estándar en e-commerce y reduce fricciones en la primera compra.

El problema tiene cuatro aristas:

1. **Estructura**: ¿qué datos se guardan de un guest? ¿Dónde?
2. **Privacidad**: ¿se crea un usuario Django por cada checkout invitado? ¿Qué ocurre con esos datos si el guest pide su eliminación?
3. **Continuidad**: ¿puede un guest convertirse en usuario registrado después de comprar? ¿Puede ver sus pedidos anteriores?
4. **Contabilidad**: si se eliminan los datos del guest, ¿los registros contables en ERP siguen siendo válidos?

---

## 3. Capa responsable

| Concepto | Propietario | Ciclo de vida |
|---|---|---|
| Anonymous Session | `commerce.engine` | Temporal. Expira con el navegador o por TTL. |
| Guest Buyer | `commerce.engine` | Persiste mientras el pedido sea relevante. |
| Identity persistente | `identity` | Permanente hasta eliminación explícita por el titular. |

---

## 4. Contratos utilizados

- `identity.profile.v1` — el campo `linkage_status: "guest"` cubre el caso del Guest Buyer que aún no tiene Identity persistente.

---

## 5. Opciones consideradas

### Opción A — Crear un usuario Django por cada checkout invitado

Cada guest checkout genera un registro `User` con email pero sin contraseña. El comprador puede activar la cuenta después.

**Ventaja:** el historial de pedidos queda en el mismo modelo de usuario. Simple de implementar.

**Desventaja:** la base de datos acumula miles de usuarios "vacíos" que nunca se activan. La privacy surface aumenta. Un email mal escrito genera un usuario huérfano. Viola la separación entre sesión técnica y identidad de negocio.

### Opción B — No persistir ningún dato del guest después del pedido

El pedido se crea con nombre y email en los campos del documento. No hay registro de comprador.

**Ventaja:** máxima privacidad. Sin datos extra.

**Desventaja:** el guest no puede recuperar sus pedidos. No puede convertirse en usuario registrado y ver su historial. No hay posibilidad de notificación post-compra.

### Opción C — Anonymous Session → Guest Buyer → Identity opcional (elegida)

Tres conceptos separados con ciclos de vida distintos:

1. **Anonymous Session**: estado técnico del navegador. Soporta el carrito sin registro.
2. **Guest Buyer**: datos mínimos del comprador asociados a un pedido específico. No es un usuario.
3. **Identity persistente**: si el guest decide crear una cuenta (antes, durante o después de comprar), se crea una Identity y puede vincularse al Guest Buyer anterior.

**Ventaja:** sin basura en la base de datos. El guest checkout es posible. La conversión a cuenta es opcional y preserva el historial. La eliminación de datos del guest no rompe registros contables.

---

## 6. Decisión

**Opción C.** Tres conceptos separados.

Secuencia completa:

```
Visitante anónimo
    │
    ▼
Anonymous Session  ──────────────────────────────┐
(carrito sin login)                              │
    │                                            │
    ▼ (llega al checkout)                        │
Guest Buyer                                      │
(nombre, email, teléfono, dirección)             │
    │                                            │
    ▼ (completa el pedido)                       │
Pedido con Guest Buyer                           │
(historial contable en ERP)                      │
    │                                            │
    │ (opcional, puede hacerlo antes,            │
    │  durante o después de comprar)             │
    ▼                                            │
Identity persistente (Buyer registrado)          │
    │                                            │
    └── puede vincular pedidos anteriores ───────┘
        (si el email del Guest Buyer coincide
         y el titular lo confirma)
```

Reglas:

1. El carrito puede existir sin Guest Buyer (sesión anónima).
2. El pedido puede existir con Guest Buyer (no es un usuario).
3. El Guest Buyer conserva los datos mínimos necesarios para la logística del pedido: nombre, email de contacto, dirección de envío.
4. **No se crea un `User` Django por cada checkout invitado.**
5. La conversión de Guest Buyer a Identity requiere una prueba verificable (email confirmado o acción explícita).
6. La vinculación de pedidos anteriores de guest a una Identity nueva requiere confirmación explícita del titular.
7. La eliminación o anonimización de una Identity o Guest Buyer no puede romper registros contables en ERP (el número de pedido, el monto y los ítems deben conservarse; el nombre y email pueden anonimizarse).

---

## 7. Consecuencias positivas

- La base de datos no acumula usuarios huérfanos de checkouts abandonados.
- El guest checkout tiene una ruta clara de conversión a cuenta registrada con historial preservado.
- La eliminación de datos del guest por solicitud GDPR/Ley 19.628 no corrompe los registros contables de ERP.
- El modelo soporta compras B2B donde la empresa compra sin crear cuentas individuales para cada empleado.

---

## 8. Consecuencias negativas y riesgos

- Mayor complejidad conceptual: tres modelos en lugar de uno.
- La conversión de guest a cuenta requiere un flujo de verificación (email de confirmación) que puede tener una tasa de abandono alta.
- Si el guest escribe un email incorrecto durante el checkout, no puede recuperar su pedido.
- El mecanismo de anonimización debe ser implementado en `commerce.engine` para que pueda borrar email/nombre del Guest Buyer sin borrar el pedido.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `commerce.engine` | Implementar `GuestBuyer` como modelo separado de `User`; manejar carrito anónimo |
| `identity` | Soporte para `linkage_status: "guest"` y flujo de conversión a `"unlinked"` o `"linked"` |
| Notificaciones | Email de confirmación de pedido para el guest; email de invitación a crear cuenta |
| Privacidad | Flujo de anonimización de `GuestBuyer` que no afecta el registro de pedido en ERP |

---

## 10. Principios protegidos o modificados

- **Separación de conceptos**: sesión técnica (Anonymous Session), datos de compra (Guest Buyer) e identidad de negocio (Identity) son entidades distintas con propietarios distintos.
- **Principio de Autonomía**: `commerce.engine` gestiona el carrito y el Guest Buyer de forma autónoma. No necesita a `identity` para completar un pedido.
- **write_authority**: `identity` no se escribe durante un guest checkout. Solo se escribe cuando el titular toma una acción explícita.

---

## 11. Qué ocurre si el componente desaparece

Si `commerce.engine` deja de estar disponible:

- El carrito anónimo desaparece (es estado temporal del navegador).
- Los pedidos de guest ya completados están registrados en ERP. El historial contable es íntegro.
- El Guest Buyer persiste hasta la eliminación explícita o hasta que se vincule a una Identity.

Si el servicio de `identity` no está disponible:

- Guest checkout sigue funcionando sin degradación (no depende de `identity`).
- La conversión de guest a cuenta registrada queda en espera hasta que el servicio se restablezca.

---

## 12. Criterios de aceptación arquitectónica

- [ ] Un comprador puede completar un pedido sin crear una cuenta Django.
- [ ] El pedido de un guest conserva nombre, email de contacto y dirección suficientes para el envío.
- [ ] Un guest puede crear una cuenta después de comprar y ver sus pedidos anteriores (previo flujo de verificación de email).
- [ ] La eliminación del nombre y email de un Guest Buyer por solicitud de privacidad no elimina el número de pedido, monto ni ítems del registro contable.
- [ ] No se crea un registro `User` en Django por cada checkout invitado.
- [ ] El carrito anónimo soporta al menos N ítems sin requerir ningún dato del comprador.

---

## 13. Plan de transición

**Fase 1 (inicial):** guest checkout no disponible. El storefront requiere cuenta registrada. Simplifica la implementación inicial.

**Fase 2:** guest checkout disponible. `GuestBuyer` como modelo separado. Flujo de confirmación de pedido por email sin creación de cuenta.

**Fase 3:** conversión de guest a cuenta. Vinculación de pedidos anteriores. Anonimización por solicitud de privacidad.

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- GDPR (UE) y Ley 19.628 (Chile) — derecho al olvido: la anonimización no puede afectar registros contables obligatorios.
- Shopify, WooCommerce, Stripe Checkout: todos implementan guest checkout como flujo de primera clase con conversión opcional a cuenta.
- ADR-006 — define el modelo de Identity que el Guest Buyer puede convertirse en el futuro.
