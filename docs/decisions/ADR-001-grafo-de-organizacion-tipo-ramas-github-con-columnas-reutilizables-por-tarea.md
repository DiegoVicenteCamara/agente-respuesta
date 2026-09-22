# ADR-001: Grafo de organización tipo ramas GitHub con columnas reutilizables por tarea

## Status
accepted

## Date
2026-09-22

## Context
El panel "Organización · orquestador y subagentes" de `web/index.html` visualizaba
las subtareas como ramas por tarea con forma de trapecio con cuello en L
(horizontal + vertical + esquina), que el usuario percibió como "cuadrados".

Además, cada subtarea reservaba un lane global creciente a la derecha
(`hist.lanes++`): al acumularse tareas el ancho `W` del `viewBox` crecía y, como el
`<svg>` se renderiza con `width:100%`, la proporción `px/unidad = anchoContenedor /
W` se reducía. Resultado: el dibujo completo (incluidas tareas ya cerradas) se
encogía y las filas se volvían ilegibles a medida que se ejecutaban más tareas.

El modelo usado en esta sesión no soporta entrada de imágenes (error de clipboard),
por lo que las decisiones de forma deben quedar documentadas en texto, no dependiendo
de capturas que no pueden leerse.

## Options Considered

### Option A: Diagonales redondeadas estilo GitHub
- Pros: silueta clásica de git; cambia poco el trazado actual (polilínea).
- Cons: conserva segmentos rectos y vértices perceptibles; no cumple la petición de
  "curva totalmente redondeada".

### Option B: Curva fluida en S/U con splines cuadráticas (SELECCIONADA)
- Pros: sin ningún vértice recto; salida y retorno tangentes a la rama principal
  (efecto flujo de commits de GitHub); todas las ramas con la misma geometría y ancho.
- Cons: patrón de path más complejo (segmentos `Q`); requiere calibrar la profundidad
  de curva (NEK) frente al espaciado de commits (SP) para no degenerar en un trazo plano.

### Option C: Mantener el trapecio con esquinas redondeadas
- Pros: mínima resistencia al cambio.
- Cons: aún se percibe como una caja alargada; no aporta el look de "flujo".

### Asignación de columnas

#### Option 1: lane global creciente (estado previo)
- Pros: nunca se solapan ramas concurrentes.
- Cons: `W` crece ilimitadamente → la escala global se reduce con cada tarea.

#### Option 2: columnas reutilizables por tarea con "columna libre más próxima" (SELECCIONADA)
- Pros: `W` fijo (MAX_COLS=4) → escala y ancho de rama constantes, el dibujo nunca se
  encoge; las tareas secuenciales vuelven a usar la columna más próxima libre; las
  tareas simultáneas usan columnas distintas (la primera no ocupada de izquierda a
  derecha); al terminar una tarea su columna queda libre.
- Cons: si hubiera más de `MAX_COLS` tareas concurrentes la última columna se
  comparte (degradación aceptada, no ocurre en el demo).

## Decision
En `web/index.html` se reemplaza el trazado cuadrangular por una rama fluida en S/U
con splines cuadráticas (`Q`), con `NEK = min(anchoColumna, 13)` y `SP = 34`, salida
y retorno tangentes a la rama principal. Cada subtarea de una tarea diverge desde el
punto de merge de la anterior (flujo continuo, mismo ancho).

Las columnas se asignan por tarea con el pool `hist.cols`: la tarea ocupa la columna
libre más próxima a la izquierda al recibir `plan_ready` y la libera al recibir
`analysis_ready`/`urgent`. `W = laneX(MAX_COLS-1) + 430` queda fijo, garantizando
escala constante aunque se ejecuten muchas tareas.

Se documentó esta elección en `docs/decisions/` (this ADR) porque el modelo no puede
leer imágenes y la decisión visual debía quedar reproducible en texto.

## Consequences
- Positive:
  - El grafo conserva tamaño de ramas y escala constantes sin importar cuántas tareas
    se ejecuten.
  - Las ramas tienen forma fluida redondeada coherente con "como ramas de GitHub".
  - Regla de columnas predecible: primero se reutiliza la columna más próxima libre;
    las tareas simultáneas nunca comparten columna salvo >4 concurrentes.
- Negative:
  - La curva S/U añade lógica de trazado (`Q`, NEK calibrado) que exige cuidado si se
    cambia `SP` o `LANE_OFF` en el futuro.
  - Las tareas concurrentes > MAX_COLS comparten la última columna (superposición).
- Neutral:
  - Cada subtarea se dibuja sobre la misma columna de su tarea (un "canal" continuo
    tipo commit) en lugar de una columna exclusiva por subtarea.

## Review
- Cadence: quarterly
- Next review: 2026-12-22
- Trigger: si el demo llega a ejecutar más de 4 tareas simultáneas, o si se cambia
  `SP`/`LANE_OFF`/`MAX_COLS` en `web/index.html`.