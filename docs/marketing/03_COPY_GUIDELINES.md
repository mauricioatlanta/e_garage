# Copy Guidelines — eGarage

> Cada frase que escribe eGarage debe pasar esta prueba: ¿Le habla al dueño del negocio, o al software?
> Si le habla al software, reescribir.

---

## Principios

1. **Beneficios antes que funcionalidades.** No describas lo que hace el software; describe lo que consigue el cliente.
2. **Claridad antes que complejidad.** Si necesitas explicar la frase, es demasiado complicada.
3. **Personas antes que tecnología.** El protagonista es el negocio. eGarage es la herramienta.

---

## Vocabulario: nunca → siempre

| Nunca decir | Siempre decir |
|-------------|---------------|
| ERP para talleres mecánicos | La plataforma para hacer crecer tu negocio automotriz |
| Gestión de órdenes | Nunca pierdas el historial de un vehículo |
| Inventario | Encuentra cualquier repuesto en segundos |
| CRM | Conoce cada cliente como si fuera el primero |
| Módulo de reportes | Sabe exactamente cómo va tu negocio hoy |
| Multi-tenant SaaS | Funciona para un taller o para diez sucursales |
| Onboarding | Empieza hoy, sin capacitación |
| Dashboard | Tu negocio de un vistazo |
| Workflow | Así funciona tu taller ahora |

---

## Tono por canal

### Web / landing
- Directo. Primera persona del cliente implícita.
- Oraciones cortas. Una idea por párrafo.
- Sin jerga técnica.

### Redes sociales
- Más cercano. Puede usar "tú" explícito.
- Máximo 3 líneas antes del primer gancho.
- Preguntas retóricas permitidas.

### Email
- Asunto: beneficio concreto, no el nombre de la funcionalidad.
- Cuerpo: contexto → problema → solución → CTA.
- Un solo CTA por email.

### Notificaciones in-app
- Imperativo positivo. ("Tu OT está lista" no "Error: OT completada")
- Sin tecnicismos en mensajes de usuario final.

---

## Reglas absolutas

- No usar "robusto", "potente", "solución integral", "end-to-end", "sinergias".
- No prometer lo que el producto no tiene todavía.
- No comparar directamente con competidores por nombre.
- El CTA principal siempre es una acción del usuario, nunca del software. ("Comenzar gratis", no "Prueba nuestro sistema")

---

## Frases de marca aprobadas

```
La plataforma para hacer crecer tu negocio automotriz.
Controla tu taller, casa de repuestos, desarmaduría o carwash desde cualquier lugar.
Tu operación, ordenada. Tu negocio, en crecimiento.
Más tiempo para ti. Menos errores en tu negocio.
30 días gratis. Sin tarjeta. Configuración en minutos.
```

---

## Adaptación por país

El tono es el mismo en todos los países. El vocabulario local cambia.
Ver `taller/welcome_config.py` → campo `terminology` por `(country, lang)`.

Ejemplos:
- MX: "Vehículo / Refacciones / Hacienda"
- AR: "Auto / Repuestos / AFIP"
- US-EN: "Vehicle / Parts / IRS"
- BR: "Veículo / Peças / NF-e"
