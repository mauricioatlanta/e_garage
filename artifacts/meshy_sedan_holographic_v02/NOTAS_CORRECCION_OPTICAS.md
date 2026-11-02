# Corrección localizada de ópticas — Meshy Sedan holographic v02

## Causa

La malla fuente no contiene faros independientes ni cavidades ópticas limpias. En v01 una selección espacial de 316 caras irregulares recibió material emisivo; por eso los focos aparecían como manchas blancas dentadas. Aumentar la emisión habría amplificado el defecto.

## Corrección

- Las 316 caras originales se reasignaron a una carcasa oscura, sin borrarlas ni alterar la silueta.
- Se añadieron dos conjuntos simétricos e independientes ajustados a la superficie frontal.
- Cada conjunto contiene carcasa angular baja, lente azul semitransparente, dos elementos ópticos metálicos y una firma cian fina.
- La firma usa emisión moderada (`0.70`). Los renders no emplean bloom de compositor, por lo que la óptica sigue siendo legible con resplandor desactivado.
- En vistas oblicuas se oculta para render únicamente el conjunto lejano para compensar la falta de oclusión de la envolvente transparente. Ambos conjuntos existen, son simétricos y se entregan en Blender y GLB.
- Las luces traseras no mostraban el defecto emisivo de v01 y no fueron modificadas.

La carrocería, proporciones, cristales, ruedas y materiales holográficos aprobados permanecen sin cambios. No se realizó despiece ni se añadió mecánica.

## GLB

El GLB conserva las ópticas como objetos/materiales separados. La apariencia final de transparencia y emisión todavía depende del orden alfa, tone mapping y configuración de bloom del visor. Las firmas son geometría real y siguen siendo visibles sin bloom.
