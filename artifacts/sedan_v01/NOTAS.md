# sedan_v01 — resultado y limitaciones

## Resultado

Primera versión artística **mid-poly** de un sedán genérico de cuatro puertas, sin logotipos ni elementos de una marca concreta. Se modeló localmente desde cero con un generador procedural de Blender, sin descargar ni incorporar modelos externos.

Incluye 33 componentes semánticos principales y geometría auxiliar: carrocería, cuatro puertas, capó, tapa de maletero, parachoques, cristales, espejos, ópticas, cuatro ruedas, interior básico y los conjuntos mecánicos solicitados. El archivo fuente conserva colecciones por sistema y propiedades `component_id` exportadas como extras de glTF.

Se entregan seis vistas neutras y seis holográficas: frontal, trasera, lateral izquierda, lateral derecha y dos perspectivas de tres cuartos.

## Métricas verificadas tras reimportar el GLB

- Archivo GLB: 1.868.560 bytes (aprox. 1,78 MiB).
- 146 objetos de malla.
- 53.445 vértices.
- 41.436 triángulos.
- 12 materiales en GLB.
- Dimensiones de contenido: 4,68 m × 2,18 m × 1,465 m. El ancho incluye espejos/ruedas.
- 33/33 identificadores requeridos presentes.
- Escalas negativas: 0.
- Polígonos de área cero después de limpieza: 0.
- Resultado de reimportación automatizada: PASS.

La medición está en `validation_report.json`. No se midió rendimiento móvil ni se afirma que el presupuesto sea apto para un dispositivo objetivo.

## Material neutro y presentación holográfica

El `.blend` contiene materiales neutros y materiales holográficos independientes. El GLB se exportó con los materiales neutros PBR, que constituyen la representación portable verificada.

Los renders holográficos usan materiales cian/emisivos de Blender, tres luces de estudio y un fondo con grilla. La iluminación, el mundo oscuro, los reflejos de Eevee y la grilla de escenario son efectos de presentación de Blender y **no forman parte del GLB**. Los materiales holográficos no deben confundirse con estados comerciales del inventario.

## Limitaciones artísticas conocidas

- Es una v01 mid-poly y no alcanza el nivel fotorrealista ni el microdetalle mecánico de la imagen de referencia.
- La carrocería aún tiene un lenguaje estilizado y algunos paneles muy planos, especialmente techo, frontal y cristales.
- Los pasos de rueda y la silueta son legibles, pero una v02 debería rehacer la superficie exterior con una retopología continua de mejor clase A, mejorar curvatura de techo/parabrisas y ajustar voladizos.
- Las ópticas, parrilla, llantas y mecánica son simplificadas.
- La transparencia del vidrio genera grano visible en algunos renders Eevee por CPU; no es un defecto de topología del GLB.
- No hay animaciones de apertura, aunque los pivotes principales quedaron preparados.
- La validación automatizada confirma geometría/nombres/materiales; no sustituye una revisión manual exhaustiva de colisiones entre todas las superficies.

## Siguiente refinamiento recomendado

Priorizar una pasada artística manual en Blender sobre `sedan_v01.blend`: superficie continua por subdivisión, pasos de rueda integrados, techo y pilares más orgánicos, ópticas con lentes internas, llantas realistas, juntas uniformes y una revisión del habitáculo a través de vidrio limpio. Después conviene crear un LOD para web y medirlo en el hardware móvil objetivo antes de integrarlo en un visor.

## Reproducción y validación

- `build_sedan.py`: reconstruye el activo, los renders y el GLB con Blender 5.2.2 LTS.
- `validate_glb.py`: abre una escena vacía, importa el GLB, mide geometría/materiales/IDs y guarda `sedan_v01_reimport_check.blend`.
- Blender se ejecutó desde la distribución portátil oficial 5.2.2 LTS, verificada contra la suma SHA-256 publicada por Blender Foundation.

Blender no estaba instalado en el Ubuntu 26.04 inspeccionado. El paquete del sistema disponible era Blender 5.0.1 y su instalación requiere una terminal administrativa: `sudo apt update && sudo apt install blender`. Como `sudo` no podía autenticarse de forma no interactiva, se usó la alternativa oficial recomendada por Blender para Linux: descargar el tarball x64, verificar su SHA-256, descomprimirlo en una carpeta temporal y ejecutar directamente el binario. La distribución portátil no forma parte de estos entregables.
