# ADR-003: Automatización de issues con opencode GitHub agent

## Status
superseded by ADR-004

## Date
2026-09-23

## Context
El proyecto genera issues de funcionalidad (`enhancement`) que requieren que un
agente las implemente de forma manual, sesión por sesión. Se quiere un flujo en
el que el agente tome issues de GitHub **de forma autónoma** y devuelva un Pull
Request listo para revisión, sin necesidad de abrir opencode y darle la tarea a
mano cada vez.

Restricciones y hechos relevantes:

- El repo es **privado** (`DiegoVicenteCamara/agente-respuesta`).
- Ya existe un stack de opencode local: AGENTS.md, skills (`.opencode/skills`,
  `.agents/skills`), plugins (graphify) y `opencode.json`.
- La suite de tests (`pytest`) es unitaria y usa fakes (`_FakeRedis` +
  `monkeypatch`), por lo que corre sin Redis, sin API keys y sin red.
- GitHub ha dejado de ofrecer minutos gratuitos de Actions; el consumo debe ser
  moderado (runner privado, plan free).
- La suscripción de opencode (Zen/Go) da tokens de modelos de alta calidad
  (cliente con más tokens disponibles que una API key de pago por uso).

## Options Considered

### Option A: GitHub Copilot coding agent (`@copilot`)
- Pros: cero configuración de secrets extra; integración nativa de GitHub.
- Cons: sin control del prompt/AGENTS.md; no reutiliza skills, plugins ni el
  flujo de trabajo local de opencode; menos control de coste por issue.

### Option B: Claude Code Action (`anthropics/claude-code-action`)
- Pros: sigue AGENTS.md; bueno para agentes; control del prompt.
- Cons: requiere nueva API key Anthropic; no reutiliza el setup local de
  opencode (plugins/skills).

### Option C: opencode en CI con `anomalyco/opencode/github@latest`
- Pros: reutiliza **toda** la configuración local de opencode (AGENTS.md,
  skills, plugins, `opencode.json`); usa la suscripción opencode (Zen/Go) como
  proveedor recomendado por el propio instalador (`opencode` es prioridad 0);
  eventos nativos `issues` (gate por label) y `schedule` (cola) con creación
  automática de rama + PR; flujo OIDC con la GitHub App de opencode de menor
  privilegio.
- Cons: requiere instalar la GitHub App `opencode-agent` y el secret
  `OPENCODE_API_KEY`; el agente autónomo puede no completar issues ambiguos.

### Option D: Agente self-hosted polling el repo
- Pros: control total del orchestrador.
- Cons: infraestructura extra (runner/daemon) a mantener; reinvención de lo que
  ya ofrece el GitHub agent de opencode.

## Decision
Adoptar **Option C**: dos workflows de GitHub Actions usando la action
`anomalyco/opencode/github@latest` con el proveedor `opencode` (suscripción
Zen/Go) y el modelo `opencode/gpt-6-sol`:

1. `.github/workflows/opencode-label.yml` — se dispara cuando un issue recibe la
   label `agent-ready`; el agente implementa el issue y abre PR (`Closes #N`).
2. `.github/workflows/opencode-schedule.yml` — cron cada 6h que procesa el issue
   `agent-ready` más antiguo sin PR abierto; un issue por run.
3. `.github/workflows/test.yml` — job de CI que corre `pytest` en cada PR y push
   a `main`; es el check obligatorio de branch protection y la garantía de que el
   agente no empuja una rama roja (el prompt le exige dejar la suite verde).

El gate de seguridad es la **label `agent-ready`** (solo los issues marcados
entran en la cola). Los PRs los mergea el humano; nunca se hace merge automático.
Los labels se gestionan (`agent-ready` → `agent-in-progress`) para evitar trabajo
duplicado entre el flujo por label y el scheduler.

## Consequences
- Positive:
  - El agente trabaja con el mismo setup, skills y AGENTS.md que en local.
  - Control de la cola vía label; cero prompts manuales por issue.
  - Tests verdes exigidos antes de abrir el PR; branch protection de respaldo.
  - Se aprovechan los tokens de la suscripción opencode.
- Negative:
  - Dependencia de la disponibilidad de la GitHub App `opencode-agent` y del
    OIDC (el workflow falla si el fixture no está instalado).
  - Issues ambiguos pueden quedar sin implementar (el agente comenta y devuelve
    el issue a `agent-ready`).
  - Consumo de minutos/créditos de Actions y tokens por cada run del scheduler
    (gastos aunque no haya trabajo).
- Neutral:
  - Dos rutas de entrada (label y cron) requieren coordinación de labels para
    evitar duplicados.
  - El modelo usado (`opencode/gpt-6-sol`) es configurable por workflow.

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: que se agote el plan de minutos de Actions, que el proveedor `opencode`
  cambie de precio/modelos, o que aparezca un segundo consumidor de la cola.

Superseded by: [ADR-004](ADR-004-revision-y-merge-automatico-de-prs-con-agente-opencode.md)
