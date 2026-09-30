# ADR-006: Generación autónoma de issues con agente opencode

## Status
accepted

## Date
2026-09-30

## Context
El proyecto cuenta con un pipeline autónomo (`opencode-label`, `opencode-schedule`,
`opencode-review`) que implementa issues etiquetados `agent-ready`, los entrega como
PR y los mergea cuando se cumple la Definición de Hecho. El "embudo" de entrada de
trabajo dependía de ideas propuestas manualmente (brainstorming en conversación),
una por rama, sin un mecanismo recurrente que *proponga* nuevas mejoras.

Se quiere un generador recurrente de candidatas (features, UX/UI, seguridad y
protección de ramas, documentación, nuevas automatizaciones) que alimente el repo con
issues bien formadas, sin saturar la cola ni delegar decisiones de gobernanza a un
proceso no supervisado.

## Options Considered

### Option A: Workflow `opencode-issues` dedicado (elegido)
- Pros:
  - Reutiliza la plantilla instalada de opencode en CI (install + cache + `opencode
    github run`), el secreto `OPENCODE_API_KEY` y `GH_TOKEN`, sin duplicar infra.
  - Permiso mínimos (`issues: write`, `contents: read`); el agente solo puede crear
    issues via `gh`, no toca código ni ramas.
  - Disparo semanal + `workflow_dispatch` con `category`/`count` para control humano.
  - Triage por política explícita: solo las features llegan a `agent-ready`; el resto
    (seguridad, UX/UI, docs, workflows) esperan aprobación humana.
- Cons:
  - Las candidatas dependen de la calidad del modelo (opencode/big-pickle); malas
    issues requieren limpieza manual.
  - El cron semanal puede acumular issues si no se triagean.

### Option B: Skill local (`.agents/skills/issue-generator`)
- Pros:
  - Se ejecuta bajo demanda en el CLI del desarrollador, con revisión previa a crear.
- Cons:
  - No automatiza la cadencia; depende de que alguien lo invoque. Complementario al
    CI, no sustituto. Se descarta por ahora para mantener un único mecanismo.

### Option C: Generar y etiquetar todo con `agent-ready`
- Pros:
  - Máximo throughput del pipeline.
- Cons:
  - Siembra la cola con trabajo no aprobado (seguridad, gobernanza, docs) — viola el
    gate humano del proyecto. Rechazado.

## Decision
Crear el workflow `.github/workflows/opencode-issues.yml` que ejecuta un agente
opencode con el modelo gratuito `opencode/big-pickle`, autenticado con el secreto
del repo `OPENCODE_API_KEY` (mismo que `opencode-label`/`opencode-schedule`), con
permisos restringidos a `gh` (creación de issues) y sin capacidad de commit/push/PR.

Cadencia: semanal (cron `0 8 * * 1`) + `workflow_dispatch` con inputs `category`
(default `all`) y `count` (default `5`, rango razonable 4-6).

Política de triage: las issues de tipo **feature** (`enhancement`) se etiquetan
además con `agent-ready` y entran solas en el pipeline. Seguridad/protección de
ramas, UX/UI, documentación y nuevos workflows se crean con labels de categoría pero
sin `agent-ready`: requieren aprobación humana antes de implementarse.

Las issues generadas siguen el formato del repo (Contexto / Feature / Diseño corto
clasificado con brainstorming / Criterios de éxito) y se evitan duplicados
consultando las issues abiertas (`gh issue search`).

## Consequences
- Positive:
  - Flujo de mejora continua: el repo se autopropone trabajo bien formado cada semana
    o bajo demanda manual.
  - Reutilización del secreto e infraestructura CI existentes (cero nuevo setup).
  - Superficie de riesgo acotada: permisos de solo lectura + `gh`, nada de git.
  - El gate humano se conserva para todo cambio que afecte gobernanza/proceso.
- Negative:
  - Las features etiquetadas `agent-ready` se implementan solas sin revisión previa de
    diseño humana; queda mitigado porque el pipeline las revisa contra la DoD antes de
    mergear.
  - Posible ruido si el modelo genera issues pobres; mitigado con `workflow_dispatch`
    manual y la política "no filler" del PROMPT.
- Neutral:
  - Nuevos labels del repo: `ux-ui`, `security`, `workflows` (creados con
    `gh label create --force`).

## Review
- Cadence: quarterly
- Next review: 2026-12-30
- Trigger: si el cron genera issues descartadas habitualmente, o si cambia el modelo
  gratuito disponible en opencode, o si se desea alinear la cadencia con sprints.