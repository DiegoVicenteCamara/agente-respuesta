---
name: project-log
description: "Bitácora de avances y retrospectivas semanales de proyecto. Consolida el progreso del periodo evaluando lo planificado frente a lo ejecutado, documentando logros, desvíos o bloqueos y lecciones aprendidas. Usar para cerrar una semana de trabajo, generar reportes de avance, retrospectivas de sprint o mantener un historial limpio del estado del proyecto."
---

# Bitácora de Avances y Retrospectivas (project-log)

## Overview

Mantiene un historial limpio del estado del proyecto **semana a semana**. Cada
entrada consolida el progreso del periodo evaluando **lo planificado frente a lo
ejecutado**, de modo que cualquier persona (o una sesión futura del agente)
pueda reconstruir el avance real del proyecto sin tener que leer todo el
historial de la conversación.

Esta bitácora resuelve problemas recurrentes:

- El avance real queda enterrado en chats, commits y tareas pendientes.
- No existe una única fuente de verdad sobre qué se logró y qué no.
- Los retrasos se repiten porque nadie documentó por qué ocurrieron.
- Las retrospectivas se olvidan y los ajustes tácticos nunca se aplican.

## Estructura de salida

Toda entrada usa exactamente estas tres secciones:

1. **Logros del periodo** — Hitos alcanzados. Lo que se terminó, validó o
   entregó durante la semana.
2. **Desvíos o Bloqueos** — Dónde hubo retrasos y por qué. Qué no se cumplió
   frente a lo planificado, con causa concreta.
3. **Lecciones aprendidas** — Qué falló en el proceso y qué ajuste táctico se
   implementará. Un aprendizaje sin ajuste no es una lección, es una queja.

## Naming y ubicación

Cada entrada se guarda en un archivo Markdown por semana:

```text
docs/project-log/YYYY-MM-DD.md
```

- `YYYY-MM-DD` es la fecha del domingo (último día) de la semana que se cierra.
- Si la carpeta `docs/project-log/` no existe, créala.
- No edites entradas pasadas para reescribir historia; corregir un error se
  documenta en la lección aprendida de la semana siguiente.

## Workflow

### 1. Reunir la fuente de verdad

Recopila evidencia de lo ocurrido en el periodo antes de escribir:

- Plan/tareas planificadas: `tasks/plan.md`, `tasks/todo.md`, o el backlog
  vigente (lo planificado).
- Ejecución real: `git log --oneline --since "<inicio de semana>"`,
  ramas mergeadas, commits, PRs, archivos creados/modificados y resultados de
  tests (lo ejecutado).
- Bitácora anterior si existe, para arrastrar bloqueos pendientes y validar
  ajustes tácticos comprometidos.
- Entrevista corta: si el usuario puede explicarlo, pregunta brevemente qué se
  terminó, qué se atrasó y por qué, antes de inferir desde git.

### 2. Comparar planificado vs ejecutado

Para cada ítem planificado determina su estado:

- **Cumplido** → candidato a Logro.
- **Parcial / Atrasado / Bloqueado** → candidato a Desvío con causa.
- **No planificado pero entregado** → Logro (márcalo explícitamente como
  surgido fuera del plan).

Sé objetivo: un Desvío exige causa concreta ("dependencia externa pendiente",
"estimación corta", "cambio de alcance"), no vaguedades como "no dio tiempo".

### 3. Redactar la entrada

Usa la plantilla del final de este documento. Reglas de redacción:

- Listas con viñetas cortas y verbos en pasado para Logros y Desvíos.
- Cada Lección aprendida lleva su Ajuste táctico: de qué porqué, la lección
  y el cambio concreto que se implementará la próxima semana.
- Mantén el formato `Página de estado` al inicio: resumen en una línea, fecha
  del periodo, y avance acumulado vs plan global si se conoce.

### 4. Guardar y entregar

Guarda el archivo y provee la ruta al usuario para que lo revise y edite en su
editor habitual. No reescribas entradas anteriores salvo que el usuario lo pida
explícitamente.

## Plantilla de entrada

```markdown
# Bitácora — Semana del [LUNES] al [DOMINGO]

## Página de estado
- **Fecha de cierre**: [YYYY-MM-DD]
- **Resumen**: [una línea: estado general del proyecto]
- **Avance acumulado**: [entregables completados] / [entregables planificados]

## Logros del periodo
- [Hito alcanzado, con evidencia si aplica: PR #x, test verde, entregable]
- [Otro hito]

## Desvíos o Bloqueos
- **[Ítem]** — Retrasado por: [causa concreta].
- **[Ítem]** — Bloqueado por: [causa concreta + qué lo destrabaría].

## Lecciones aprendidas
- **Lección**: [qué falló en el proceso]
  **Ajuste táctico**: [cambio concreto a implementar la próxima semana]

## Bloqueos que continúan
- [Ítem arrastrado de la semana anterior, si aplica]
```

## Ejemplo de entrada

```markdown
# Bitácora — Semana del 2026-09-14 al 2026-09-20

## Página de estado
- **Fecha de cierre**: 2026-09-20
- **Resumen**: Backend de agente de respuesta operativo; frontend de historial en curso.
- **Avance acumulado**: 2 / 4 entregables planificados.

## Logros del periodo
- Endpoint de respuestas v1 mergeado (PR #12), tests pasando (14/14).
- Bitácora automatizada como proyecto de ejemplo (documento del ciclo).

## Desvíos o Bloqueos
- **Frontend de historial** — Retrasado por: estimación corta del servicio de
  eventos; 2 días adicionales.
- **Firma de proveedor** — Bloqueado por: contrato pendiente de aprobación legal.

## Lecciones aprendidas
- **Lección**: se estimaron tareas del frontend sin descomponer el consumo del
  evento, subestimando la integración.
  **Ajuste táctico**: toda tarea frontend nueva incluirá una tarea de spike de
  integración de 0.5 días antes de estimar.

## Bloqueos que continúan
- Firma de proveedor (dependencia externa).
```

## Criterios de verificación

- [ ] Una entrada nueva por semana en `docs/project-log/YYYY-MM-DD.md`.
- [ ] Las tres secciones obligatorias presentes: Logros, Desvíos o Bloqueos,
      y Lecciones aprendidas.
- [ ] Cada Desvío incluye una causa concreta.
- [ ] Cada Lección aprendida incluye un Ajuste táctico accionable.
- [ ] Se respetó la entrada anterior (no reescrita) y se arrastraron bloqueos
      pendientes.
- [ ] La ruta del archivo se entregó al usuario.

## Notas

- La bitácora prioriza la honestidad sobre la simetría: un periodo sin logros
  pero con lecciones claras es una entrada válida.
- Usa lenguaje del proyecto: si el equipo conversa en español, redacta en
  español; si usa otro idioma en el código/PRs, mantén la nomenclatura de los
  ítems como aparecen en el repositorio.