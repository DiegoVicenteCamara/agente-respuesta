# ADR-004: Memoria persistente de conversaciones por usuario en Redis

## Status
accepted

## Date
2026-09-23

## Context
El agente de voz «Respuesta» es multi-sesión y no recuerda nada entre llamadas:
cada vez que un usuario vuelve, el planificador parte de cero y se incurre en el
mismo esfuerzo de investigación. Hasta ahora la identidad del usuario en el
token LiveKit era opcional (siempre generada en el servidor), imposible de
vincular entre sesiones, y el grafo LangGraph convencional no retenía estado.

La issue #8 pide memoria conversacional operativa: resumir lo investigado al
final de cada tarea, recuperarlo al inicio de la siguiente y dárselo al
planificador, sin exponerlo por voz si no aporta.

Restricciones: infraestructura existente Redis (ya se usa para broker Celery y
canal de eventos), coste limitado (resumir con el LLM del subagente, no uno
extra), y la voz no debe leer la memoria completa al usuario.

## Options Considered

### Option A: Identidad gestionada en el navegador (localStorage) + `/token?identity=`
- Pros: refuerzos nulos en el backend; el usuario conserva identidad entre
  sesiones; el servidor sigue generando identidades anónimas si no llega una.
- Cons: no vinculable a cuentas reales (aceptable hoy); localStorage por
  navegador/dominio.
- Rechazo de la alternativa (servidor genera siempre el UUID): imposibilita
  recuperar memoria entre sesiones.

### Option B: Servicio `backend/memory/` con resumen en una clave Redis por usuario
- Pros: clave única `user:{id}:memory` con TTL configurable; `MEMORY_ENABLED`
  permite degrado controlado; fallback determinista sin LLM; publica el evento
  `memory_recalled` silencioso para el panel sin interrumpir la voz.
- Cons: un solo resumen por usuario (no historial completo).
- Rechazado: almacenar el chat completo crecería sin límite y el coste de
  resumir dominaría.

### Option C: Checkpointer LangGraph + estado completo de la conversación
- Pros: estado de ejecución persistente, granular.
- Cons: sobrecarga para lo que aquí se necesita (persistir ejecuciones, no
  conversación); complejidad de configuración sobre Redis ya usado para el
  flujo de eventos; no da contexto planificador de un vistazo.
- Rechazado por over-engineering para el alcance de la issue.

## Decision
Se implementa memoria persistente por usuario apoyada en Redis:

- **Identidad**: el navegador mantiene `respuesta-identity` en `localStorage` y
  la envía como `?identity=` en `/token`; el servidor la respeta y, si falta,
  genera `participant-{uuid}` (renombrado desde `user-{uuid}`). El entrypoint de
  voz resuelve el `user_id` en cascada: participante humano > claims del token >
  `anonymous`.
- **Persistencia**: `backend/memory/service.py` con `load`, `store`,
  `summarize` y `publish_recalled`; clave `user:{id}:memory` con TTL
  (`MEMORY_TTL_DAYS=30`), tamaño acotado (`MEMORY_MAX_CHARS=2000`).
- **Inyección**: `planner` del grafo carga el resumen (si hay `user_id` y
  `MEMORY_ENABLED=true`) y lo adjunta al prompt como contexto.
- **Guardado**: `synthesize` guarda `(user_id, goal, analysis)` tras publicar
  `analysis_ready`.
- **Voz**: el saludo menciona de forma natural el trabajo previo únicamente si
  hay resumen; el panel recibe `memory_recalled` con prioridad `silent`.

La decisión de diseño se documenta en
`docs/superpowers/specs/2026-09-23-conversation-memory-design.md` (aprobada).

## Consequences
- Positive: el planificador ajusta subtareas a lo ya conocido del usuario;
  reutiliza Redis sin nueva infraestructura; cubre un interés real de recuperar
  contexto sin coste extra de LLM.
- Negative: un resumen malo condiciona tareas futuras; identidad por
  `localStorage` no es determinista entre dominios/navegadores; tareas vía
  `/debug/run` no transmiten `user_id`.
- Neutral: `MEMORY_ENABLED` permite apagar el comportamiento completo; el TTL
  limita tanto el espacio como el horizonte de memoria.

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: revisar si se introduce autenticación real de usuarios (entonces la
  identidad debería venir del token, no de localStorage) o si se necesita
  historial multi-resumen por usuario.