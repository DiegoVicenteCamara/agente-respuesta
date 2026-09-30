# ADR-004: Landing page en GitHub Pages desde docs/ con deploy por Actions

## Status
accepted

## Date
2026-09-23

## Context
El repo se hace público y el README técnico no basta como vitrina: hace falta
una landing con el pitch del producto, el diagrama de arquitectura, un
quickstart (4 comandos + modo prueba sin voz) y enlaces a docs/specs/ADRs,
sin coste de infra (Pages gratuito) y sin demo en vivo (el coste continuo de
OpenAI/LiveKit no es sostenible por defecto).

Restricciones del issue: página única estática (HTML/CSS sin framework),
servida como `https://<owner>.github.io/<repo>/`, sin secretos y sin
`backend/`/`web/` en el contenido publicado, con enlaces cruzados
README ↔ landing. La redacción/branding final la revisa una persona antes de
publicar (el issue no es `agent-ready`).

## Options Considered

### Option A: Rama `gh-pages` separada con solo el estático
- Pros: aislamiento total; la rama publicada no contiene `backend/`/`web/` ni
  secretos ni historial interno.
- Cons: requiere mantener una segunda rama/origen (o `git subtree`/`ghp-import`)
  a mano o con workflow extra; los enlaces relativos a ADRs/specs no funcionan
  (hay que usar URLs absolutas a `main`); fricción para el agente autónomo y
  para revisiones en PR (el contenido no se revisa en el PR de `main`).

### Option B: `docs/` en `main` + Pages "Deploy from a branch" (`main`/`docs`)
- Pros: cero workflows; `docs/index.html` es la raíz del sitio y los ADRs
  (`docs/decisions/`) enlazan en relativo; revisión en el mismo PR.
- Cons: expone todo `docs/` (incluido `project-log/` interno) tal cual; el
  modo "branch" está fijado a Jekyll por defecto sin `.nojekyll`; depende de un
  ajuste manual en Settings que el agente no puede verificar.

### Option C (elegida): `docs/` en `main` + workflow Actions (`upload-pages-artifact`/`deploy-pages`)
- Pros: el artefacto publicado es solo `docs/` (sin `backend/`/`web/`, sin
  secretos); enlaces relativos a ADRs funcionan en el sitio vivo y en local;
  revisión en el mismo PR de `main`; `.nojekyll` evita el procesado Jekyll;
  es el modo Pages recomendado actualmente (Settings → Pages → Source:
  GitHub Actions).
- Cons: requiere activar Pages en modo Actions una vez (manual); publica
  `docs/project-log/` y `docs/superpowers/` junto a la landing (aceptable en
  repo público; la landing solo enlaza lo curado).

## Decision
Adoptar **Option C**: fuente en `docs/index.html` + `docs/styles.css` (+
`docs/.nojekyll`), workflow `.github/workflows/pages.yml` que sube `docs/`
como artefacto y despliega con `deploy-pages`, y enlaces cruzados README ↔
landing. Los enlaces a ADRs son relativos (`decisions/ADR-xxx`); los enlaces a
ficheros fuera de `docs/` (`SPEC-jev-router.md`, sección `agent-ready` del
README) son URLs absolutas a GitHub. Sin JavaScript, sin demo en vivo, sin
secretos.

## Consequences
- Positive:
  - Coste cero, sin backend en lo publicado, sin secretos en el sitio.
  - Sitio verificable en CI con tests sin red (existencia, secciones Diátaxis,
    enlaces internos resuelven a fichero, sin patrones de secreto).
  - Un solo PR revisa landing + ADR + workflow + tests.
- Negative:
  - Requiere un paso manual único: Settings → Pages → Source "GitHub Actions".
  - `docs/project-log/` queda publicado (ruido interno visible).
- Neutral:
  - La redacción/branding queda pendiente de revisión humana antes de anunciar
    la URL (tal como exige el issue).
  - Si a futuro se quiere ocultar `docs/` interno, migrar a rama `gh-pages`
    con artefacto `docs/landing/` sería una supersesión de este ADR.

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: que Pages cambie su modelo de despliegue, que aparezca contenido en
  `docs/` que no deba ser público, o que se decida añadir demo en vivo.
