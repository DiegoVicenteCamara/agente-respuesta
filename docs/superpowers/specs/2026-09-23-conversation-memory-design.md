# Spec: Memoria persistente de conversaciones por usuario (issue #8)

## Objetivo

Dar al agente de voz «Respuesta» **memoria persistente entre sesiones**: cada usuario
tiene un `user_id` estable y el agente recuerda el resumen de sus conversaciones
anteriores al volver a llamar. La memoria fluye del plano de voz al plano de ejecución
(sin acoplarlos) y se usa en dos puntos del grafo LangGraph:

- **`planner`**: inyecta el resumen previo como contexto en el prompt de planificación.
- **`synthesize`**: genera y persiste un resumen actualizado tras `analysis_ready`.

El feature respeta la arquitectura actual: voz y ejecución siguen comunicándose por el
bus Redis; la memoria es un servicio por debajo del grafo, no lógica dentro del plano de
voz. `MEMORY_ENABLED=false` debe dejar el flujo actual 100 % intacto.

## Contexto actual

- No existe `user_id` en ningún plano. `/token` autogenera `user-{uuid}` por llamada y el
  browser no envía `identity` (`backend/api/main.py:33-44`, `web/index.html:183`).
- `RunContext` de LiveKit no expone la identidad del usuario; la vía es
  `ctx.room.remote_participants` / `ctx.token_claims()` en `voice_entrypoint`
  (`backend/voice/agent.py:84-89`).
- `backend/bus/redis_client.py` solo tiene `publish_event` (pub/sub); faltan get/set con
  TTL.
- `ResearchState` (`backend/orchestrator/graph.py:21-28`), `run_pipeline`
  (`backend/orchestrator/tasks.py:108`), `plan_subtasks` (`nodes.py:81-87`) y `synthesize`
  (`graph.py:95-107`) no conocen `user_id` ni memoria.

## Decisión de diseño

Enfoque elegido (aprobado en brainstorming): **servicio de memoria + estado explícito**.
Descartados: checkpointer de LangGraph en Redis (historiales completos: contradice el
diseño resumen+TTL y la issue) y memoria residente en el plano de voz (viola el desacople
voz/ejecución).

## Estructura de proyectos

```
backend/memory/            → Nuevo módulo (servicio de memoria). Sin LiveKit.
  __init__.py              → re-exporta load/store/summarize
  service.py               → lógica pura + acceso Redis + summarize LLM
backend/bus/redis_client.py            → + mem_get / mem_set (helpers con TTL)
backend/voice/tools.py                 → + USER_ID (contextvar) y propagación en dispatch
backend/voice/agent.py                 → obtiene user_id, saludo con memoria, evento silent
backend/api/main.py                    → /token respeta identity dado
backend/orchestrator/tasks.py          → run_pipeline(..., user_id=None), state inicial
backend/orchestrator/nodes.py          → plan_subtasks(..., memory=None)
backend/orchestrator/graph.py          → ResearchState.user_id, planner inyecta, synthesize guarda
backend/config.py + .env.example       → MEMORY_ENABLED, MEMORY_TTL_DAYS
web/index.html                         → identity en localStorage → /token?identity=
backend/tests/…                        → test_memory_service.py + extensiones
docs/decisions/ADR-004-…               → decisión documentada
```

## Contrato de `backend/memory/`

`backend/memory/service.py`:

- Clave Redis: `user:{user_id}:memory`.
- `async def load(user_id: str) -> str | None`
  Si `MEMORY_ENABLED=false` devuelve `None`. Error de Redis → `None` (tolerante, log).
- `async def store(user_id: str, summary: str, ttl_days: int) -> None`
  No-op si desactivado o summary vacío. Error de Redis → log, sin excepción.
- `async def summarize(goal: str, analysis: str, previous: str | None) -> str`
  LLM vía `nodes.chat` con `MEMORY_SYSTEM_PROMPT` (resumen conciso de temas/preferencias,
  marcar lo que ya se sabía). Si no hay clave API o falla la llamada → resumen determinista
  `f"{goal}: {analysis}"` truncado a `MEMORY_MAX_CHARS` (sin lanzar excepción).
- `async def publish_recalled(user_id: str | None, message: str | None) -> None`
  Evento `memory_recalled` con `priority: silent` (solo panel, la voz no lo repite).

Sin dependencias de LiveKit; la configuración se lee de `settings` al vuelo.

## Identidad y propagación

1. **Web**: `web/index.html` genera o reutiliza `identity` en `localStorage`
   (`respuesta-user-{uuid}`) y lo pasa como `?identity=` al `/token`. Fallback: `/token`
   sigue generando `participant-{uuid}` (renombrado desde `user-…` para no confundir con el
   identity persistido).
2. **Voz**: `voice_entrypoint` resuelve `user_id` en cascada:
   `next(iter(ctx.room.remote_participants.values()))` → `ctx.token_claims().identity` →
   `"anonymous"`. Lo fija en `tools.USER_ID` (contextvar del módulo) antes de usarse.
3. **Tools**: `_dispatch_orchestrator(task_id, goal, user_id)` → `send_task("run_pipeline",
   args=[task_id, goal, user_id], task_id=task_id)`. `delegate_complex_task_core` y
   `confirm_execution_core` leen `USER_ID` y lo pasan.

## Orquestador (grafo)

- `ResearchState`: nuevo campo opcional `user_id`.
- `run_pipeline(task_id, goal, user_id=None)` (`tasks.py:108`): firma ampliada con default.
  `/debug/run` lo omite (se queda sin memoria).
- `planner(state)` (`graph.py:57`): si `memory_enabled` y `user_id` → `load()` y se lo pasa
  a `nodes.plan_subtasks(goal, model, memory)`.
- `nodes.plan_subtasks(goal, model=None, memory=None)` (`nodes.py:81`): si `memory` →
  añade la línea `Contexto de conversaciones previas del usuario: {memory}` al prompt de
  planificación (concisa; el objetivo manda).
- `synthesize(state)` (`graph.py:95`): tras publicar `analysis_ready`, si `memory_enabled`
  y `user_id`: `previous=load` → `summary=summarize(goal, analysis, previous)` →
  `store(user_id, summary, ttl_days)`. Errores → log sin romper el resultado.

## Saludo y panel

- `voice_entrypoint`: si `memory_enabled`, carga el resumen y compone `WELCOME_INSTRUCTIONS`
  con línea sutil («La última vez investigaste X — cuéntame qué necesitas ahora»); ante
  resumen vacío, saludo normal. Publica `memory_recalled` (`priority: silent`) para el panel
  debug. `notifier.build_spoken_update` devuelve `None` para `silent` (contenido en reposo,
  sin doble anuncio).

## Configuración

- `backend/config.py` (patrón de `cost_tracking_enabled`, líneas 42-44):
  - `memory_enabled` = `_get("MEMORY_ENABLED", "true").lower() != "false"`.
  - `memory_ttl_days` = int de `_get("MEMORY_TTL_DAYS", "30")`.
  - `memory_max_chars` = int de `_get("MEMORY_MAX_CHARS", "2000")` (corte del fallback).
- `.env.example`: bloque `MEMORY_ENABLED=true`, `MEMORY_TTL_DAYS=30`, `MEMORY_MAX_CHARS=2000`.

## Testing

- `backend/tests/test_memory_service.py` (nuevo): load/store (clave y TTL correctos),
  summarize (traza LLM / fallback determinista), no-op con `MEMORY_ENABLED=false`, fallo de
  Redis → `None`/log. Mocks en memoria sin `fakeredis` (patrón del repo: monkeypatch de
  `redis_client.mem_get/mem_set/publish_event`).
- `test_graph.py`: `planner` inyecta memoria cuando hay `user_id`; sin `user_id` o desactivado
  → prompt igual que hoy.
- `test_tasks_route.py`: `run_pipeline` acepta user_id y lo deja en el state inicial.
- `test_tools_route.py`: `_dispatch_orchestrator` recibe y propaga user_id.
- `test_api.py`: `/token` respeta el `identity` dado; fallback genera `participant-…`.
- Comando: `.venv\Scripts\python.exe -m pytest -q`. Los flujos FAST/BLOCK/PROPOSE_COMMIT y la
  suite existente no cambian.

## Criterios de éxito

- Segunda llamada del mismo `user_id`: el planificador recibe el resumen previo (verificable
  en test/prompt).
- `MEMORY_ENABLED=false`: flujo actual idéntico al de hoy.
- Resumen persistido tras `analysis_ready` con TTL configurable.
- `user_id` ausente (`anonymous`) → sin memoria, sin errores.
- ADR creado (`docs/decisions/ADR-004-…`) y suite completa verde.

## Riesgos y mitigaciones

- **Timing de identidad**: el participante humano puede tardar en aparecer → cascada de
  fallback y `"anonymous"` nunca rompe el flujo.
- **Coste extra de LLM en `summarize`**: gateado por `MEMORY_ENABLED` + fallback determinista.
- **Conflicto con `feat/cancel-task-by-voice` en `tools.py`**: ya mergeada en main; esta rama
  parte de main.
- **Memory por navegador** (localStorage), no cross-device: fuera de alcance.

## No-goals (explícitos)

- Historiales completos / transcripts (solo resúmenes).
- Memoria cross-device / multi-navegador.
- Recordatorio hablado extenso del historial.
- Soporte de identidad telefónica SIP (llegará con `feat/sip-pstn-telephony`).

## Preguntas abiertas

Ninguna pendiente: las 7 secciones de diseño fueron aprobadas por el usuario el 2026-09-23.