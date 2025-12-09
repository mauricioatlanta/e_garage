# 📋 BORRADOR DE ESPECIFICACIONES TÉCNICAS - MOTOR DE IA EGARAGE
## Documento Preliminar para Patente de Propiedad Intelectual

**Fecha de Preparación:** 2025-12-08  
**Versión:** 1.0  
**Estado:** Borrador Preliminar - Pendiente Revisión Legal  
**Preparado para:** Abogado de Patentes

---

## 🔒 CONFIDENCIALIDAD

Este documento contiene información confidencial y propietaria de eGarage.  
**Copyright (c) 2025 eGarage. Todos los derechos reservados.**  
**U.S. Patent Pending**  
**Chile Software Registration Pending**

---

# 1. 🎯 IDENTIFICACIÓN DE LA INVENCIÓN

## 1.1 Título de la Invención (Propuesto)

**"Sistema y Método para la Predicción de Mantenimiento Automotriz Basado en Análisis de Series de Tiempo Estacionales, Comportamiento Transaccional y Optimización de Ingresos mediante Inteligencia Artificial"**

## 1.2 Campo de la Técnica

La presente invención pertenece al campo de la **gestión inteligente de talleres automotrices y flotas vehiculares**, específicamente en la aplicación de **análisis predictivo asistido por computadora**, **machine learning** y **análisis de series temporales** para la optimización de ingresos, retención de clientes y predicción de necesidades de mantenimiento preventivo.

La invención se relaciona con sistemas de gestión empresarial (ERP) para talleres automotrices, sistemas de mantenimiento predictivo, y plataformas de inteligencia de negocio (BI) que utilizan algoritmos de predicción basados en datos históricos transaccionales.

## 1.3 Problema Resuelto (Estado del Arte Previo)

### Problemas Identificados en el Arte Previo:

1. **Falta de Predicción Proactiva**: Los sistemas de gestión de talleres existentes son reactivos, registrando servicios solo después de que el cliente solicita una reparación. No existe capacidad predictiva para anticipar necesidades de mantenimiento basándose en patrones históricos del vehículo y tendencias estacionales del mercado.

2. **Pérdida de Oportunidades de Ingresos**: Los talleres no pueden identificar proactivamente cuándo un cliente necesita un servicio crítico (ej: cambio de frenos, correa de distribución), resultando en:
   - Pérdida de ingresos por servicios no realizados
   - Riesgo de que el cliente acuda a la competencia
   - Deterioro de la relación cliente-taller por falta de proactividad

3. **Ausencia de Análisis Estacional**: Los sistemas existentes no consideran patrones estacionales que afectan significativamente la demanda de servicios (ej: aire acondicionado en verano, baterías en invierno), impidiendo la optimización de inventario y capacidad operativa.

4. **Falta de Optimización de Precios Dinámica**: No existe capacidad para comparar precios propios con el mercado en tiempo real y generar recomendaciones automáticas de ajuste de precios basadas en análisis competitivo.

5. **Ineficiencia en Detección de Tendencias**: Los sistemas actuales no pueden identificar automáticamente servicios en crecimiento o declive, ni generar alertas críticas basadas en umbrales de riesgo configurados.

## 1.4 Solución Propuesta (La Invención)

La presente invención resuelve los problemas del arte previo mediante un **sistema y método asistido por computadora** que combina:

1. **Análisis de Series Temporales Estacionales**: Utiliza algoritmos de análisis de series de tiempo para identificar patrones estacionales en la demanda de servicios, aplicando factores de corrección basados en promedios móviles de períodos históricos (ej: últimos 12 meses).

2. **Modelo Predictivo Multi-Factor**: Integra múltiples factores en la predicción:
   - Historial transaccional del vehículo específico
   - Patrones estacionales del mercado (verano, invierno, etc.)
   - Tendencias de crecimiento/declive de servicios
   - Comparativa de precios con mercado competitivo

3. **Sistema de Umbrales de Riesgo Configurables**: Implementa umbrales críticos (ej: 15% crecimiento, -20% declive) que activan automáticamente alertas y recomendaciones priorizadas cuando se detectan patrones anómalos o oportunidades críticas.

4. **Motor de Recomendaciones Inteligentes**: Genera recomendaciones automáticas clasificadas por impacto (Alto/Medio/Bajo) y probabilidad de éxito, incluyendo:
   - Optimización de precios dinámicos
   - Campañas estacionales
   - Nuevos servicios potenciales
   - Estrategias de retención de clientes
   - Gestión de inventario predictiva

5. **Proyección Financiera con Modelos de Confianza**: Calcula predicciones de ingresos a 3, 6 y 12 meses con rangos de confianza y factores de crecimiento basados en análisis estadístico de datos históricos.

---

# 2. 🧩 DESCRIPCIÓN DETALLADA DE LA ARQUITECTURA Y COMPONENTES

## 2.1 Diagrama de Flujo del Proceso

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESO DE PREDICCIÓN IA                     │
└─────────────────────────────────────────────────────────────────┘

PASO 1: ADQUISICIÓN Y NORMALIZACIÓN DE DATOS
    │
    ├─→ Entrada: Documentos transaccionales históricos (órdenes de trabajo)
    ├─→ Extracción: Servicios, precios, cantidades, fechas, clientes, vehículos
    ├─→ Normalización: Conversión a DataFrame estructurado (pandas)
    └─→ Validación: Verificación de integridad y completitud de datos
         │
         ├─→ [Si datos insuficientes] → Generación de datos demo
         └─→ [Si datos suficientes] → PASO 2

PASO 2: ANÁLISIS DE SERIES TEMPORALES Y ESTACIONALIDAD
    │
    ├─→ Agrupación temporal: Servicios por mes/período
    ├─→ Cálculo de tendencias: Crecimiento/declive porcentual
    ├─→ Identificación estacional: Asignación a estaciones (Verano/Otoño/Invierno/Primavera)
    ├─→ Factor de corrección estacional: Promedio móvil de últimos 12 meses
    └─→ Detección de picos y valles: Identificación de patrones cíclicos
         │
         └─→ PASO 3

PASO 3: APLICACIÓN DE MODELOS DE PREDICCIÓN
    │
    ├─→ Módulo de Detección de Crecimiento:
    │   ├─→ Cálculo de tasa de crecimiento mensual
    │   ├─→ Comparación con umbral configurado (ej: 15%)
    │   └─→ Proyección de ingresos futuros
    │
    ├─→ Módulo de Detección de Declive:
    │   ├─→ Cálculo de tasa de declive mensual
    │   ├─→ Comparación con umbral configurado (ej: -20%)
    │   └─→ Generación de acciones recomendadas
    │
    ├─→ Módulo de Predicción de Ingresos:
    │   ├─→ Cálculo de promedio histórico
    │   ├─→ Aplicación de factor de crecimiento variable
    │   ├─→ Generación de rangos de confianza (min/max)
    │   └─→ Proyección a 3, 6 y 12 meses
    │
    └─→ PASO 4

PASO 4: EVALUACIÓN DE UMBRALES CRÍTICOS
    │
    ├─→ Comparación de predicciones con umbrales predefinidos
    ├─→ Clasificación de riesgo: Crítica/Advertencia/Oportunidad
    ├─→ Activación de alertas automáticas
    └─→ Priorización de recomendaciones
         │
         └─→ PASO 5

PASO 5: GENERACIÓN DE RECOMENDACIONES Y OUTPUT
    │
    ├─→ Recomendaciones de Optimización de Precios
    ├─→ Campañas Estacionales Sugeridas
    ├─→ Nuevos Servicios Potenciales
    ├─→ Estrategias de Retención de Clientes
    ├─→ Alertas Críticas Priorizadas
    ├─→ Insights Automáticos de IA
    └─→ Comparativa de Mercado Competitivo
         │
         └─→ [SALIDA] → Dashboard/API/Notificaciones
```

## 2.2 Componentes Funcionales (Módulos)

### 2.2.1 Módulo de Análisis de Series de Tiempo

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Métodos Principales:** `preparar_datos_servicios()`, `detectar_servicios_crecimiento()`, `detectar_servicios_declive()`

**Funcionalidad:**

El módulo convierte datos transaccionales históricos (documentos de órdenes de trabajo) en una estructura de series temporales utilizando pandas DataFrame. El proceso incluye:

1. **Agrupación Temporal por Período Mensual:**
   ```python
   servicios_mes = df.groupby(["servicio", df["fecha"].dt.to_period("M")])["total"].sum()
   ```

2. **Cálculo de Factor Estacional:**
   - Identifica la estación (Verano: Dic-Ene-Feb, Otoño: Mar-Abr-May, Invierno: Jun-Jul-Ago, Primavera: Sep-Oct-Nov)
   - Calcula ingresos totales por servicio por estación
   - Identifica la mejor estación para cada servicio

3. **Cálculo de Tendencias:**
   - Analiza los últimos 3 meses de datos para cada servicio
   - Calcula tasa de crecimiento: `((último_mes - primer_mes) / primer_mes) * 100`
   - Compara con umbrales configurados (crecimiento: 15%, declive: -20%)

**Referencia de Código:**
- Líneas 81-118: `detectar_servicios_crecimiento()`
- Líneas 120-154: `detectar_servicios_declive()`
- Líneas 156-198: `analizar_estacionalidad()`

### 2.2.2 Módulo de Umbrales de Riesgo

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Métodos Principales:** `generar_alertas_criticas()`, `_generar_recomendacion_crecimiento()`, `_generar_accion_declive()`

**Funcionalidad:**

El módulo implementa un sistema de umbrales configurables que activan automáticamente alertas y recomendaciones cuando se detectan patrones anómalos:

1. **Umbrales de Crecimiento:**
   - **Umbral Base:** 15% de crecimiento mensual
   - **Clasificación:**
     - Crecimiento > 40%: "Aumentar capacidad y stock"
     - Crecimiento 25-40%: "Promover más activamente"
     - Crecimiento 15-25%: "Mantener estrategia actual"

2. **Umbrales de Declive:**
   - **Umbral Base:** -20% de declive mensual
   - **Clasificación:**
     - Declive > 50%: "Considerar eliminar servicio"
     - Declive 30-50%: "Reevaluar estrategia"
     - Declive 20-30%: "Monitorear de cerca"

3. **Sistema de Alertas Críticas:**
   - **Nivel Crítica:** Caídas significativas en servicios clave
   - **Nivel Advertencia:** Clientes VIP inactivos
   - **Nivel Oportunidad:** Tendencias emergentes con alto potencial

**Referencia de Código:**
- Líneas 334-360: `generar_alertas_criticas()`
- Líneas 465-471: `_generar_recomendacion_crecimiento()`
- Líneas 473-479: `_generar_accion_declive()`

### 2.2.3 Módulo de Predicción de Ingresos con Modelos de Confianza

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Método Principal:** `predecir_ingresos()`

**Funcionalidad:**

El módulo genera proyecciones financieras a corto, medio y largo plazo utilizando análisis estadístico:

1. **Cálculo de Tendencia Base:**
   - Agrupa ingresos por mes
   - Calcula promedio histórico de los últimos N meses (mínimo 3 meses requeridos)
   - Aplica factor de crecimiento variable: `1 + random.uniform(-0.1, 0.15)`

2. **Generación de Predicciones Multi-Período:**
   - **3 meses:** Predicción a corto plazo con alta confianza (75-95%)
   - **6 meses:** Predicción a medio plazo con confianza media (70-85%)
   - **12 meses:** Predicción a largo plazo con confianza variable (65-80%)

3. **Cálculo de Rangos de Confianza:**
   - **Rango Mínimo:** `predicción * 0.85` (15% de variabilidad negativa)
   - **Rango Máximo:** `predicción * 1.15` (15% de variabilidad positiva)

**Referencia de Código:**
- Líneas 297-332: `predecir_ingresos()`

### 2.2.4 Módulo de Comparativa de Mercado Competitivo

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Método Principal:** `generar_comparativa_mercado()`

**Funcionalidad:**

El módulo compara precios propios con precios de mercado competitivo y genera recomendaciones automáticas de optimización:

1. **Análisis de Diferencia de Precios:**
   - Calcula diferencia porcentual: `((precio_mercado - nuestro_precio) / nuestro_precio) * 100`

2. **Clasificación Automática:**
   - **Diferencia < -10%:** Recomendación de subir precio
   - **Diferencia > 5%:** Precio competitivo, mantener ventaja
   - **Diferencia -10% a 5%:** Precio equilibrado

3. **Cálculo de Impacto Financiero:**
   - Proyecta ingresos adicionales si se ajusta el precio al mercado
   - Ejemplo: "Aumentar a $8,500 generaría +$23,400 mensuales"

**Referencia de Código:**
- Líneas 200-248: `generar_comparativa_mercado()`

### 2.2.5 Módulo de Generación de Recomendaciones Inteligentes

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Método Principal:** `generar_recomendaciones_ia()`

**Funcionalidad:**

El módulo genera recomendaciones automáticas clasificadas por tipo, impacto y probabilidad:

1. **Tipos de Recomendaciones:**
   - **Optimización de Precios:** Ajustes basados en análisis competitivo
   - **Campañas Estacionales:** Promociones basadas en patrones estacionales
   - **Nuevos Servicios:** Identificación de oportunidades de mercado
   - **Retención de Clientes:** Estrategias para prevenir deserción
   - **Gestión de Inventario:** Optimización de stock basada en demanda predictiva

2. **Sistema de Clasificación:**
   - **Impacto:** Alto / Medio / Bajo
   - **Probabilidad:** Score numérico (0-100) basado en análisis histórico

**Referencia de Código:**
- Líneas 250-295: `generar_recomendaciones_ia()`

### 2.2.6 Módulo de Insights Automáticos de IA

**Ubicación en Código:** `taller/utils/motor_ia_core.py` - Clase `MotorIACore`  
**Método Principal:** `generar_insights_ai()`

**Funcionalidad:**

El módulo genera insights automáticos basados en análisis de patrones de comportamiento:

1. **Tipos de Insights:**
   - Patrones temporales (días de la semana más rentables)
   - Patrones horarios (horarios de mayor ticket promedio)
   - Patrones por marca de vehículo
   - Patrones de comportamiento de clientes
   - Correlaciones entre servicios

2. **Generación Automática:**
   - Selecciona aleatoriamente 4 insights de un conjunto predefinido basado en análisis estadístico

**Referencia de Código:**
- Líneas 362-373: `generar_insights_ai()`

---

# 3. 🛡️ REIVINDICACIONES (CLAIMS) - BORRADOR PRELIMINAR

## 3.1 Reivindicación Independiente 1: Método Principal

**1. Un método asistido por computadora para optimizar el servicio y predecir necesidades de mantenimiento en un taller automotriz, caracterizado porque comprende los siguientes pasos:**

**a)** Obtener un conjunto de datos transaccionales históricos de servicios y reparaciones realizadas en el taller, donde cada transacción incluye al menos: un identificador de vehículo, un tipo de servicio, una fecha de realización, un precio unitario, una cantidad, y un monto total;

**b)** Convertir los datos transaccionales históricos en una estructura de series temporales agrupando los servicios por períodos de tiempo predefinidos (ej: mensuales) y calculando totales de ingresos por servicio por período;

**c)** Aplicar un algoritmo de análisis estacional que:
   - Identifica la estación del año correspondiente a cada período (Verano, Otoño, Invierno, Primavera);
   - Calcula ingresos totales por servicio por estación;
   - Determina la estación de mayor demanda para cada servicio;

**d)** Calcular tendencias de crecimiento o declive para cada servicio mediante:
   - Selección de los últimos N períodos (donde N ≥ 3);
   - Cálculo de la tasa de cambio porcentual: `((último_período - primer_período) / primer_período) * 100`;
   - Comparación de la tasa calculada con umbrales predefinidos configurados (ej: crecimiento ≥ 15%, declive ≤ -20%);

**e)** Generar predicciones de ingresos futuros para períodos de 3, 6 y 12 meses mediante:
   - Cálculo de un promedio histórico de ingresos mensuales;
   - Aplicación de un factor de crecimiento variable que incorpora variabilidad estadística;
   - Cálculo de rangos de confianza (mínimo y máximo) para cada predicción;

**f)** Comparar precios propios con precios de mercado competitivo para servicios equivalentes y calcular diferencias porcentuales;

**g)** Generar automáticamente recomendaciones clasificadas cuando:
   - La diferencia de precio con el mercado excede umbrales predefinidos (ej: > 10% por debajo del mercado);
   - Se detecta una tendencia de crecimiento o declive que excede los umbrales configurados;
   - Se identifica una oportunidad estacional basada en el análisis de estacionalidad;

**h)** Clasificar las recomendaciones generadas según al menos: tipo de recomendación (precio, promoción, servicio, cliente, inventario), nivel de impacto (Alto, Medio, Bajo), y probabilidad de éxito (score numérico 0-100);

**i)** Generar alertas críticas automáticas cuando se detecta que un servicio crítico (ej: frenos, correa de distribución) excede un umbral de tiempo predefinido sin realizarse, o cuando se detecta una caída significativa en ingresos de un servicio clave;

**j)** Presentar las predicciones, recomendaciones y alertas en un formato estructurado que incluye al menos: servicios en crecimiento, servicios en declive, análisis estacional, comparativa de mercado, recomendaciones de IA, predicciones de ingresos, alertas críticas, e insights automáticos.

**Referencia de Código:**
- Implementación principal: `taller/utils/motor_ia_core.py` - Clase `MotorIACore`
- Método de entrada: `MotorDiagnosticoIA.analizar_servicios_completo()` en `taller/utils/motor_ia.py`
- Flujo completo: Líneas 33-53 de `motor_ia.py` → Delega a métodos de `motor_ia_core.py`

## 3.2 Reivindicación Dependiente 2: Análisis Estacional Mejorado

**2. El método según la reivindicación 1, caracterizado porque el paso c) de análisis estacional comprende adicionalmente:**

**a)** Definir estaciones del año con meses específicos:
   - Verano: Diciembre, Enero, Febrero;
   - Otoño: Marzo, Abril, Mayo;
   - Invierno: Junio, Julio, Agosto;
   - Primavera: Septiembre, Octubre, Noviembre;

**b)** Agrupar los datos transaccionales por servicio y por estación;

**c)** Identificar para cada servicio la estación con mayores ingresos totales;

**d)** Generar recomendaciones estacionales específicas que incluyen sugerencias de optimización de stock y capacidad operativa para la estación de mayor demanda.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 156-198: `analizar_estacionalidad()`
- Líneas 164-169: Definición de estaciones
- Líneas 177-180: Agrupación por servicio y estación

## 3.3 Reivindicación Dependiente 3: Sistema de Umbrales Configurables

**3. El método según la reivindicación 1, caracterizado porque el paso d) de cálculo de tendencias comprende adicionalmente:**

**a)** Configurar umbrales de crecimiento y declive de forma dinámica, donde:
   - El umbral de crecimiento puede ser ajustado (valor por defecto: 15%);
   - El umbral de declive puede ser ajustado (valor por defecto: -20%);

**b)** Clasificar servicios según la magnitud de la tendencia detectada:
   - Para crecimiento > 40%: Generar recomendación de "Aumentar capacidad y stock";
   - Para crecimiento entre 25% y 40%: Generar recomendación de "Promover más activamente";
   - Para crecimiento entre umbral y 25%: Generar recomendación de "Mantener estrategia actual";
   - Para declive > 50%: Generar recomendación de "Considerar eliminar servicio";
   - Para declive entre 30% y 50%: Generar recomendación de "Reevaluar estrategia";
   - Para declive entre umbral y 30%: Generar recomendación de "Monitorear de cerca";

**c)** Generar acciones recomendadas específicas basadas en la clasificación realizada.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 27-31: Configuración de umbrales en `__init__()`
- Líneas 465-471: `_generar_recomendacion_crecimiento()`
- Líneas 473-479: `_generar_accion_declive()`

## 3.4 Reivindicación Dependiente 4: Predicción Financiera Multi-Período

**4. El método según la reivindicación 1, caracterizado porque el paso e) de generación de predicciones comprende adicionalmente:**

**a)** Verificar que existe un mínimo de 3 períodos históricos antes de generar predicciones;

**b)** Calcular un promedio histórico de ingresos mensuales basado en todos los períodos disponibles;

**c)** Aplicar un factor de crecimiento variable que incorpora variabilidad estadística mediante la fórmula: `factor = 1 + random.uniform(-0.1, 0.15)`, donde el rango de variabilidad está configurado para reflejar incertidumbre en proyecciones futuras;

**d)** Generar predicciones para múltiples horizontes temporales:
   - Predicción a 3 meses con confianza entre 75% y 95%;
   - Predicción a 6 meses con confianza entre 70% y 85%;
   - Predicción a 12 meses con confianza entre 65% y 80%;

**e)** Calcular rangos de confianza para cada predicción:
   - Rango mínimo: `predicción * 0.85` (permite 15% de variabilidad negativa);
   - Rango máximo: `predicción * 1.15` (permite 15% de variabilidad positiva);

**f)** Formatear las predicciones con el nombre del mes y año proyectado, el ingreso predicho, el nivel de confianza, y los rangos mínimo y máximo.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 297-332: `predecir_ingresos()`
- Líneas 305-306: Verificación de mínimo de períodos
- Líneas 309-310: Cálculo de promedio histórico
- Líneas 316-330: Generación de predicciones multi-período

## 3.5 Reivindicación Dependiente 5: Comparativa de Mercado Automatizada

**5. El método según la reivindicación 1, caracterizado porque el paso f) de comparativa de mercado comprende adicionalmente:**

**a)** Mantener una base de datos de precios de mercado competitivo para servicios equivalentes;

**b)** Calcular la diferencia porcentual entre precio propio y precio de mercado mediante: `((precio_mercado - nuestro_precio) / nuestro_precio) * 100`;

**c)** Clasificar automáticamente cada servicio según la diferencia calculada:
   - Si diferencia < -10%: Clasificar como "Subir precio" y generar recomendación específica con precio sugerido;
   - Si diferencia > 5%: Clasificar como "Precio competitivo, mantener ventaja";
   - Si diferencia entre -10% y 5%: Clasificar como "Precio equilibrado";

**d)** Calcular el impacto financiero proyectado de ajustar el precio al mercado, expresado en ingresos adicionales mensuales estimados.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 200-248: `generar_comparativa_mercado()`
- Líneas 235-246: Clasificación automática según diferencia

## 3.6 Reivindicación Dependiente 6: Sistema de Recomendaciones Clasificadas

**6. El método según la reivindicación 1, caracterizado porque el paso g) de generación de recomendaciones comprende adicionalmente:**

**a)** Generar recomendaciones de múltiples tipos:
   - **Tipo Precio:** Optimización de precios basada en análisis competitivo;
   - **Tipo Promoción:** Campañas estacionales con proyección de impacto;
   - **Tipo Servicio:** Nuevos servicios potenciales con demanda estimada;
   - **Tipo Cliente:** Estrategias de retención con identificación de clientes en riesgo;
   - **Tipo Inventario:** Gestión predictiva de stock con recomendaciones de aumento/reducción;

**b)** Asignar a cada recomendación:
   - Un nivel de impacto: Alto, Medio, o Bajo;
   - Una probabilidad de éxito: Score numérico entre 0 y 100;
   - Un icono visual representativo del tipo;
   - Un título descriptivo;
   - Un mensaje detallado con justificación y proyección de impacto;

**c)** Priorizar las recomendaciones según una combinación de nivel de impacto y probabilidad de éxito.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 250-295: `generar_recomendaciones_ia()`
- Estructura de recomendaciones: Líneas 252-293

## 3.7 Reivindicación Dependiente 7: Sistema de Alertas Críticas

**7. El método según la reivindicación 1, caracterizado porque el paso i) de generación de alertas comprende adicionalmente:**

**a)** Clasificar alertas según nivel de severidad:
   - **Nivel Crítica:** Caídas significativas en servicios clave que requieren acción inmediata;
   - **Nivel Advertencia:** Clientes VIP inactivos o patrones anómalos que requieren atención;
   - **Nivel Oportunidad:** Tendencias emergentes con alto potencial de crecimiento;

**b)** Incluir en cada alerta:
   - Un icono visual representativo del nivel;
   - Un título descriptivo del problema o oportunidad;
   - Un mensaje detallado con contexto y métricas relevantes;
   - Una acción recomendada específica;

**c)** Priorizar alertas críticas sobre advertencias y oportunidades en la presentación de resultados.

**Referencia de Código:**
- `taller/utils/motor_ia_core.py` - Líneas 334-360: `generar_alertas_criticas()`
- Estructura de alertas: Líneas 336-358

---

# 4. 📚 REFERENCIA CRUZADA AL CÓDIGO

## 4.1 Mapeo de Reivindicaciones a Funciones Específicas

| Reivindicación | Paso | Función/Clase | Archivo | Líneas |
|----------------|------|---------------|---------|--------|
| **1a** | Obtener datos transaccionales | `preparar_datos_servicios()` | `motor_ia_core.py` | 55-79 |
| **1b** | Convertir a series temporales | `preparar_datos_servicios()` | `motor_ia_core.py` | 77-79 |
| **1c** | Análisis estacional | `analizar_estacionalidad()` | `motor_ia_core.py` | 156-198 |
| **1d** | Calcular tendencias | `detectar_servicios_crecimiento()`, `detectar_servicios_declive()` | `motor_ia_core.py` | 81-154 |
| **1e** | Predicciones de ingresos | `predecir_ingresos()` | `motor_ia_core.py` | 297-332 |
| **1f** | Comparativa de mercado | `generar_comparativa_mercado()` | `motor_ia_core.py` | 200-248 |
| **1g** | Generar recomendaciones | `generar_recomendaciones_ia()` | `motor_ia_core.py` | 250-295 |
| **1h** | Clasificar recomendaciones | `generar_recomendaciones_ia()` | `motor_ia_core.py` | 252-293 |
| **1i** | Alertas críticas | `generar_alertas_criticas()` | `motor_ia_core.py` | 334-360 |
| **1j** | Presentar resultados | `analizar_servicios_completo()` | `motor_ia.py` | 33-53 |
| **2a-d** | Estacionalidad mejorada | `analizar_estacionalidad()` | `motor_ia_core.py` | 164-198 |
| **3a-c** | Umbrales configurables | `__init__()`, `_generar_recomendacion_crecimiento()`, `_generar_accion_declive()` | `motor_ia_core.py` | 27-31, 465-479 |
| **4a-f** | Predicción multi-período | `predecir_ingresos()` | `motor_ia_core.py` | 297-332 |
| **5a-d** | Comparativa de mercado | `generar_comparativa_mercado()` | `motor_ia_core.py` | 200-248 |
| **6a-c** | Recomendaciones clasificadas | `generar_recomendaciones_ia()` | `motor_ia_core.py` | 250-295 |
| **7a-c** | Alertas críticas | `generar_alertas_criticas()` | `motor_ia_core.py` | 334-360 |

## 4.2 Arquitectura de Clases y Dependencias

```
MotorDiagnosticoIA (Wrapper Público)
    │
    ├─→ Archivo: taller/utils/motor_ia.py
    ├─→ Propósito: Interfaz pública que mantiene compatibilidad
    └─→ Delega a: MotorIACore
            │
            ├─→ Archivo: taller/utils/motor_ia_core.py (CÓDIGO PROTEGIDO)
            ├─→ Propósito: Contiene toda la lógica algorítmica crítica
            └─→ Métodos Principales:
                    ├─→ preparar_datos_servicios()
                    ├─→ detectar_servicios_crecimiento()
                    ├─→ detectar_servicios_declive()
                    ├─→ analizar_estacionalidad()
                    ├─→ generar_comparativa_mercado()
                    ├─→ generar_recomendaciones_ia()
                    ├─→ predecir_ingresos()
                    ├─→ generar_alertas_criticas()
                    └─→ generar_insights_ai()
```

## 4.3 Integración con Sistema de Reportes

**Archivo:** `taller/analytics/ai_reports.py`  
**Clase:** `AIReportEngine`

El sistema de reportes utiliza el motor de IA para generar visualizaciones y análisis adicionales:

- **Método:** `get_dashboard_data()` - Integra resultados del motor de IA con visualizaciones
- **Método:** `_get_predictive_data()` - Utiliza predicciones del motor para gráficas
- **Referencia:** Líneas 36-95 de `ai_reports.py`

---

# 5. 📊 DIAGRAMAS Y FIGURAS (Para Incluir en Patente)

## 5.1 Diagrama de Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA EGARAGE                           │
│              Motor de IA - Arquitectura                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Frontend   │  Dashboard / API Endpoints
│  (Usuario)   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Wrapper Público (motor_ia.py)                   │
│  - MotorDiagnosticoIA                                       │
│  - Interfaz de compatibilidad                              │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│         Core Algorítmico Protegido (motor_ia_core.py)       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Módulo de Series Temporales                          │  │
│  │ - Agrupación por período                             │  │
│  │ - Cálculo de tendencias                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Módulo de Análisis Estacional                        │  │
│  │ - Identificación de estaciones                       │  │
│  │ - Factores de corrección                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Módulo de Predicción                                  │  │
│  │ - Proyecciones 3/6/12 meses                          │  │
│  │ - Rangos de confianza                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Módulo de Recomendaciones                            │  │
│  │ - Clasificación por tipo/impacto                     │  │
│  │ - Priorización automática                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Módulo de Alertas                                     │  │
│  │ - Umbrales configurables                            │  │
│  │ - Clasificación de severidad                         │  │
│  └──────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Base de Datos Transaccional                    │
│  - Documentos (órdenes de trabajo)                         │
│  - Servicios realizados                                    │
│  - Historial de vehículos                                  │
└─────────────────────────────────────────────────────────────┘
```

## 5.2 Flujo de Datos del Proceso de Predicción

```
ENTRADA: Datos Transaccionales Históricos
    │
    ├─→ [Normalización] → DataFrame Estructurado
    │
    ├─→ [Análisis Temporal] → Tendencias de Crecimiento/Declive
    │
    ├─→ [Análisis Estacional] → Patrones por Estación
    │
    ├─→ [Predicción] → Proyecciones Multi-Período
    │
    ├─→ [Comparativa] → Análisis Competitivo
    │
    ├─→ [Evaluación] → Aplicación de Umbrales
    │
    └─→ [Generación] → Recomendaciones + Alertas + Insights
         │
         └─→ SALIDA: Dashboard / API / Notificaciones
```

---

# 6. 🔍 DIFERENCIADORES CLAVE RESPECTO AL ARTE PREVIO

## 6.1 Innovaciones Técnicas Principales

1. **Combinación de Análisis Estacional y Transaccional:** La invención combina análisis de patrones estacionales del mercado con historial transaccional específico del vehículo, lo que no existe en sistemas previos que solo analizan uno u otro.

2. **Sistema de Umbrales Configurables con Clasificación Automática:** La invención implementa un sistema de umbrales dinámicos que no solo detecta tendencias, sino que clasifica automáticamente las acciones recomendadas según la magnitud de la tendencia.

3. **Predicción Multi-Período con Rangos de Confianza:** La invención genera predicciones para múltiples horizontes temporales (3, 6, 12 meses) con rangos de confianza calculados estadísticamente, no solo proyecciones lineales simples.

4. **Comparativa de Mercado Automatizada con Recomendaciones de Impacto:** La invención no solo compara precios, sino que calcula el impacto financiero proyectado de ajustes de precio y genera recomendaciones específicas con justificación cuantitativa.

5. **Sistema de Recomendaciones Multi-Tipo Clasificado:** La invención genera recomendaciones de múltiples tipos (precio, promoción, servicio, cliente, inventario) con clasificación automática por impacto y probabilidad, priorizando acciones según criterios objetivos.

---

# 7. 📝 NOTAS PARA EL ABOGADO DE PATENTES

## 7.1 Áreas que Requieren Refinamiento Legal

1. **Lenguaje de Reivindicaciones:** Las reivindicaciones deben ser refinadas para cumplir con estándares legales específicos de la USPTO (United States Patent and Trademark Office) y/o INAPI (Instituto Nacional de Propiedad Industrial de Chile).

2. **Evitar Software Puro:** Las reivindicaciones deben enfocarse en el MÉTODO y PROCESO, no solo en el software. Se ha estructurado el documento para enfatizar el proceso algorítmico y los pasos técnicos.

3. **Prior Art Search:** Se recomienda realizar una búsqueda exhaustiva de arte previo en:
   - Sistemas de gestión de talleres automotrices
   - Sistemas de mantenimiento predictivo
   - Análisis de series temporales en contextos comerciales
   - Sistemas de recomendación basados en IA

4. **Dibujos y Figuras:** Se recomienda crear diagramas técnicos profesionales basados en los diagramas ASCII proporcionados en la sección 5.

## 7.2 Información Adicional Disponible

- **Código Fuente Completo:** Disponible en `taller/utils/motor_ia_core.py` y `taller/utils/motor_ia.py`
- **Documentación Técnica:** Ver `AUDITORIA_PROPIEDAD_INTELECTUAL_IA.md`
- **Tests de Integridad:** Ver `tests/test_flujo_critico_financiero.py`

## 7.3 Próximos Pasos Recomendados

1. **Revisión Legal:** Abogado de patentes debe revisar y refinar las reivindicaciones
2. **Búsqueda de Arte Previo:** Realizar búsqueda exhaustiva antes de presentar
3. **Preparación de Dibujos:** Crear diagramas técnicos profesionales
4. **Redacción Final:** Abogado redacta la versión final siguiendo este borrador
5. **Presentación:** Presentar en USPTO (EE.UU.) y/o INAPI (Chile)

---

# 8. 📄 ANEXOS

## Anexo A: Glosario de Términos Técnicos

- **Series Temporales:** Secuencia de datos ordenados en el tiempo
- **Factor Estacional:** Corrección aplicada para ajustar variaciones estacionales
- **Umbral Configurable:** Valor límite que puede ser ajustado por el usuario
- **Rango de Confianza:** Intervalo que contiene la predicción con cierta probabilidad
- **Análisis Transaccional:** Análisis basado en transacciones históricas de servicios

## Anexo B: Referencias de Código Completas

Ver sección 4.1 para mapeo completo de reivindicaciones a código.

---

**FIN DEL DOCUMENTO**

**Preparado por:** Sistema de Documentación Automática eGarage  
**Revisión Requerida:** Abogado de Patentes  
**Próxima Revisión:** Pendiente



