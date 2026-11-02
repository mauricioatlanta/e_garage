# Material holográfico Meshy Sedan v01

La geometría fuente y sus proporciones se conservaron. El trabajo se limita a materiales por caras, iluminación, cámaras y curvas auxiliares de contorno. No se añadieron interior ni componentes mecánicos.

## Conservado en GLB

- Material azul de carrocería con transparencia suave.
- Material de cristales con mayor transparencia y tinte azul.
- Neumáticos oscuros, llantas metálicas y faros emisivos.
- Asignación de materiales por caras y metadatos del objeto.

## Dependiente del visor web

- El resplandor alrededor de faros y líneas requiere bloom/postprocesado del visor.
- La transparencia requiere mezcla alfa y depth pre-pass o dithering. La propuesta usa dithering porque la mezcla ordenada deja ver las ruedas opuestas a través de la envolvente cerrada.
- Las curvas auxiliares de contorno permanecen editables en el archivo Blender, pero no se incluyen en el GLB de entrega. En web deben reproducirse con líneas seleccionadas, geometría auxiliar o un pase de silueta. No se recomienda mostrar todas las aristas de la malla.
- La intensidad aparente depende de tone mapping/exposición. Se recomienda fondo casi negro, bloom fino y emisión moderada.

## Limitación de segmentación

El GLB original contiene un único objeto sin materiales. Cristales, puertas, techo, ópticas y carrocería forman una misma isla topológica. Los cristales se delimitaron conservadoramente por caras usando posición y orientación; no existe un límite topológico limpio que garantice coincidencia perfecta con todas las juntas generadas.
