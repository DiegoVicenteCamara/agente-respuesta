# ADR-007: Hacer el repositorio público (go-public: licencia, secretos, gobernanza)

## Status
proposed

## Date
2026-10-02

## Context
El repo es privado y su única vitrina es el README. Tiene una arquitectura
publicable (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) y una
automatización de issues (`agent-ready`) diferenciadora. Hacerlo público es una
decisión con trade-offs — visibilidad vs. mantenimiento y revisión de secretos —
por eso se clasifica como **spike** en `brainstorming` y requiere aprobación
humana (licencia y branding quedan fuera de la automatización; este issue NO es
`agent-ready`, lo gestiona una persona).

Nota de numeración: la issue pedía "ADR-005", pero ese número ya está ocupado
por "Revisión y merge automático de PRs con agente opencode" (y existe ADR-006
de generación autónoma de issues), así que la decisión go-public se registra
como ADR-007, el siguiente número libre.

Hechos relevantes para la auditoría (rama de trabajo, 2026-10-02):

- `.gitignore` cubría `.env`, `logs/`, `.venv/`, `__pycache__/`, `dist/`,
  `build/` — pero no variantes (`.env.*`), claves (`*.pem`, `*.key`) ni
  credenciales. Se endurece en esta misma PR.
- `.env` no está en el índice git; `node_modules` (bajo `.opencode/`) tampoco.
  `.env.example` solo contiene placeholders (`TU_...`, vacíos).
- Los 4 workflows opencode + `test.yml`/`pages.yml` consumen secretos solo vía
  `${{ secrets.* }}` hacia entorno; ninguno hace `echo`/`print` de secretos en
  logs (verificado por inspección; `opencode-issues.yml` además instruye
  "Never reveal or print secrets").
- Barrido de patrones (`sk-…`, `ghp_…`, `github_pat_…`, `BEGIN PRIVATE KEY`) en
  el árbol actual: sin hallazgos reales (solo aserciones en
  `backend/tests/test_landing.py` y placeholders dummy en
  `.opencode/node_modules/effect` no trackeado).
- Historial: el runner de CI entrega un clon shallow (1 commit visible), así
  que la auditoría del historial completo (`git log -p`, `git filter-repo` si
  aparece algo) debe confirmarla un humano con clon completo **antes** de
  accionar el interruptor a público.

## Options Considered

### Option A: Publicar con MIT + gobernanza mínima (propuesta de la issue)
- Pros: máxima reutilización (permite forks comerciales y demos); un fichero
  LICENSE + CONTRIBUTING/CoC/SECURITY + templates `agent-ready` es el estándar
  que esperan colaboradores y el pipeline autónomo; coste mínimo.
- Cons: cualquiera puede copiar el código sin contribuir de vuelta; hay que
  mantener issues/PRs externos y moderar conforme al CoC.

### Option B: Publicar con copyleft (GPL/AGPL)
- Pros: obliga a liberar derivados; protege contra apropiación cerrada.
- Cons: fricción para adopción comercial y para reutilizar snippets en otros
  proyectos; la issue propone MIT y cambiarlo ahora reabre la decisión de
  branding/licencia que es potestad humana.

### Option C: Seguir privado / publicar solo la landing
- Pros: cero riesgo de filtrar secretos y cero mantenimiento externo.
- Cons: se pierde la visibilidad del diferenciador (`agent-ready`, ADR-003/005/006)
  y la colaboración; la landing ya es pública y enlaza a un repo invisible.

## Decision
Adoptar **Option A como propuesta pendiente de aprobación humana**: preparar el
repo para público con licencia **MIT** (propuesta de la issue — el merge de
esta PR equivale a la aprobación de licencia/branding por el mantenedor),
gobernanza mínima y auditoría de secretos:

1. `LICENSE` (MIT, © 2026 Diego Vicente Cámara), `CONTRIBUTING.md` (flujo
   `agent-ready`, desarrollo local, higiene de secretos), `CODE_OF_CONDUCT.md`
   (Contributor Covenant 2.1), `SECURITY.md` (reporte privado, alcance,
   higiene de secretos).
2. `.gitignore` endurecido (`.env.*` con excepción `!.env.example`, `*.pem`,
   `*.key`, credenciales, `.vscode/`, `.idea/`, `.DS_Store`).
3. Plantillas `.github/ISSUE_TEMPLATE/` (`feature` con label `agent-ready` +
   secciones Contexto/Feature/Diseño/Criterios/Prompt delegación; `bug`;
   `security` en triaje humano; `docs-ux-workflow`) + `config.yml` con enlace a
   SECURITY.md, `PULL_REQUEST_TEMPLATE.md` con checklist DoD y `FUNDING.yml`
   (placeholder comentado).
4. Badges en README (`test.yml`, `pages.yml`, licencia MIT). Sin badge de
   coverage: no hay workflow de coverage que respaldarlo (no inventar badges).
5. `topics` del repo (p. ej. `livekit`, `openai-realtime-api`, `langgraph`,
   `celery`, `redis`, `opencode`, `voice-ai`) y el interruptor privado→público
   **no son ficheros**: los aplica un humano en Settings antes/después del
   merge (documentado aquí porque no es automatizable por PR).
6. Test `backend/tests/test_go_public.py` que fija la auditoría: ficheros
   presentes, `.gitignore` cubre secretos, workflows sin volcado de secretos,
   sin patrones de claves en contenido trackeado, ADR-007 presente.

**HARD-GATE de aprobación humana**: el spike exige el visto bueno del
mantenedor en la revisión de esta PR (licencia MIT + marca). Sin ese
"aprobado", esta PR es solo una propuesta y el repo sigue privado.

## Consequences
- Positive:
  - Repo publicable con un estándar de gobernanza reconocible (licencia,
    contribución, conducta, seguridad, templates).
  - El pipeline `agent-ready` queda documentado para colaboradores externos.
  - La auditoría queda fijada en tests: futuros secretos/commits que la rompan
    hacen fallar el CI.
- Negative:
  - Mantener issues/PRs externos, moderar según el CoC y vigilar que no se
    cuelen secretos en contribuciones.
  - MIT permite forks cerrados sin retorno.
  - El historial completo debe re-auditarse con clon full antes de publicar;
    si aparece un secreto hay que rotarlo y reescribir con `git filter-repo`.
- Neutral:
  - `FUNDING.yml` queda como placeholder comentado hasta decidir vía de
    financiación.
  - `topics` y visibilidad se configuran a mano en GitHub Settings.

## Review
- Cadence: quarterly
- Next review: 2027-01-02
- Trigger: publicar el repo, recibir la primera contribución externa o detectar
  un secreto filtrado (revisar licencia/gobernanza entonces).
