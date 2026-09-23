# Plan: Memoria persistente de conversaciones por usuario (issue #8)

Basado en `docs/superpowers/specs/2026-09-23-conversation-memory-design.md`.

## Orden de implementación (dependencias)

1. **Config base** — `backend/config.py` (`memory_enabled`, `memory_ttl_days`, `memory_max_chars`) + `.env.example` bloque `MEMORY_*`. Sin dependencia de código.
2. **Bus Redis** — `backend/bus/redis_client.py`: `mem_get(key)` / `mem_set(key, value, ttl_seconds)`, tolerantes a `ConnectionError`. Dependencia de `config`.
3. **Servicio `backend/memory/`** — `service.py`: `load`, `store`, `summarize`, `publish_recalled`; no-op con `MEMORY_ENABLED=false`; fallback determinista si falla el LLM. Depende de 1-2 y de `nodes.chat`.
4. **Voz** — `web/index.html` (identity localStorage → `?identity=`), `backend/api/main.py /token` (respeta identity; fallback `participant-…`), `backend/voice/tools.py` (contextvar `USER_ID` + propagación en `_dispatch_orchestrator`), `backend/voice/agent.py` (`voice_entrypoint` resuelve user_id, saludo con memoria, evento `memory_recalled` silent). Depende de 3.
5. **Orquestador** — `backend/orchestrator/tasks.py` (`run_pipeline(..., user_id=None)` + state inicial), `nodes.py` (`plan_subtasks(..., memory=None)`), `graph.py` (`ResearchState.user_id`, `planner` inyecta, `synthesize` guarda tras `analysis_ready`). Depende de 3.
6. **Tests** — en paralelo a 2-5 (mocks en memoria, patrón `_FakeRedis` existente), `pytest -q` al final.
7. **Docs** — ADR-004 en `docs/decisions/` (skill `decision-log`) acompañando el commit de implementación; commits por capa lógica (`feat(config)`, `feat(bus)`, `feat(memory)`, `feat(voice)`, `feat(orchestrator)`, `test(…)`).

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Timing del participante humano (identidad tardía) | Cascada de fallback: `remote_participants` → `token_claims().identity` → `"anonymous"` |
| Coste extra de LLM en `summarize` | Gateado por `MEMORY_ENABLED`; fallback determinista truncado |
| Redis caído | `mem_get`/`mem_set` tolerantes (None/log); `publish_recalled` no rompe |
| Ruptura de flujos existentes | `user_id=None` por defecto; sin user_id o desactivado → prompt idéntico al de hoy |
| `memory_recalled` hablado por la voz | `priority: silent` (panel solo) |

## Verificación por capa

- Capa 2-3: `python -m pytest backend/tests/test_memory_service.py -q`.
- Capa 4: `python -m pytest backend/tests/test_api.py backend/tests/test_tools_route.py -q`.
- Capa 5: `python -m pytest backend/tests/test_graph.py backend/tests/test_tasks_route.py -q`.
- Global: `.venv\Scripts\python.exe -m pytest -q`; `graphify update .`.