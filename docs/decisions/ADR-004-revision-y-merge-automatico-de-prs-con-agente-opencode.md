# ADR-004: Revisión y merge automático de PRs con agente opencode

## Status
accepted

## Date
2026-09-24

## Context
El proyecto implementa issues de forma autónoma (`ADR-003`): un agente opencode
abre una PR para cada issue y hasta ahora el merge lo hacía un humano, sin gate
automático que compruebe si la tarea cumple la Definición de Hecho (DoD) del
proyecto.

Se quiere que las PRs se **revisen y mergeen de forma 100% automática** cuando
cumplan la DoD, con dos requisitos duros:

- La DoD del proyecto exige evidencias registradas en la issue, CI verde,
  integración sin conflictos y documentación actualizada.
- Antes de mergear hay que **traer `main` sobre la rama** y, si hay conflictos,
  resolverlos sin pisar el trabajo de otras issues.

Restricciones y hechos relevantes:

- Branch protection de `main`: exige PR + check `test` (pytest). **No** requiere
  review humano. En el futuro se añadirá un agente revisor que sí publique
  review, pero el merge automático no debe depender de ello.
- La acción `anomalyco/opencode/github@latest` soporta eventos `pull_request` y
  puede commitear sobre el head de la misma PR.
- Los pushes hechos con el token de la opencode App (modo OIDC que ya usa el
  repo) **sí** re-disparan workflows (`test.yml` y el propio revisor), lo que
  permite revalidar CI tras resolver conflictos — pero obliga a controlar
  bucles y carreras.
- El repo usa merge commits sobre `main` (sin squash) y ramas de PR efímeras.

## Options Considered

### Option A: Workflow por evento de PR con agente opencode revisor
- Pros: feedback inmediato por PR; reutiliza todo el stack existente
  (AGENTS.md, skills, plugins, acción `opencode/github`); merge 100% autónomo;
  el concurrency global evita pisar trabajo concurrente.
- Cons: bucles y carreras por re-disparo de eventos (se mitigan con guard de
  idempotencia por SHA y un único grupo de concurrency).

### Option B: Barrido por scheduler (cron) que procesa PRs abiertas
- Pros: anti-bucles por diseño; lote procesado sin carreras.
- Cons: latencia de hasta 6h por PR; hay que descubrir PRs abiertas y su
  estado; re-disparo manual necesario tras cada push; UX peor durante el ciclo
  de iteración. No se alinea con el requisito de revisión en cada evento.

### Option C: Dos fases (CI + gate humano con label de aprobación)
- Pros: conserva un punto de control humano.
- Cons: no es "merge 100% automático" como exige el proyecto; añade piezas y
  estados superfluos; el humano se convierte en cuello de botella.

## Decision
Adoptar **Option A**: un workflow `.github/workflows/opencode-review.yml` que:

1. Se dispara en `pull_request` (`opened`, `synchronize`, `reopened`,
   `ready_for_review`) y `workflow_dispatch` (revisión manual con `pr_number`).
2. Ejecuta un job `guard` que omite PRs de forks, drafts, base `!= main`,
   ya mergeadas, o cuyo `head.sha` ya fue revisado (marcador en comentario).
3. Usa `concurrency: group: opencode-review, cancel-in-progress: false` —
   **un solo revisor a la vez** en todo el repo — para nunca pisar el trabajo
   de otras issues entre ramas concurrentes.
4. Ejecuta la acción `anomalyco/opencode/github@latest` (modelo
   `opencode/gpt-6-sol`) con un prompt que: verifica los 5 criterios de la DoD
   contra la evidencia estructurada de la issue; hace `git merge origin/main`
   sobre la rama y resuelve conflictos integrando ambos lados; pushea el merge;
   espera el check `test` en verde (`gh pr checks --watch`); y hace
   `gh pr merge --merge --delete-branch` si todo cumple.
5. Si la DoD no se cumple, comenta en la PR **qué falla y qué soluciones** y
   **no** mergea.

La Definición de Hecho y su evidencia estructurada se documentan en
`docs/definition-of-done.md`; los agentes implementadores (`opencode-label` y
`opencode-schedule`) quedan obligados a publicar el comentario de evidencias
para que sus PRs pasen la revisión automática.

Este ADR **supersede ADR-003** en lo referente al destino de las PRs: donde
ADR-003 decía *"Los PRs los mergea el humano; nunca se hace merge automático"*,
ahora el merge automático es la norma cuando se cumple la DoD. El resto del
flujo de implementación autónoma descrito en ADR-003 se mantiene.

## Consequences
- Positive:
  - Merge 100% autónomo cuando se cumple la DoD, sin cuello de botella humano.
  - Gate objetivo y reproducible (evidencia estructurada + CI + sin conflictos).
  - `main` siempre se trae y los conflictos se resuelven con integración
    cuidadosa, sin pisar trabajo de otras issues.
  - Reutiliza el stack opencode existente sin infraestructura nueva.
- Negative:
  - El revisor solo es tan bueno como su prompt y la evidencia: issues sin
    evidencias correctas no se mergearán (queda el comentario explicativo).
  - El merge automático requiere confianza en el agente; ante criterios
    ambiguos nunca mergea (falla en modo seguro).
  - Cada PR genera consumo de minutos/tokens de Actions además del de
    implementación.
- Neutral:
  - La revisión vuelve a ejecutarse en cada push, dentro del mismo grupo de
    concurrency.
  - La política de merge queda expresada en código (workflow) y en docs (DoD),
    auditables y versionados.

## Review
- Cadence: quarterly
- Next review: 2026-12-24
- Trigger: que un agente revisor humano-compatible publique reviews formales
  (replantear si mergear o esperar), o que los checks de branch protection
  cambien.