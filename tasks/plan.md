# Plan: Jev System 1 dual-model router

Basado en `SPEC-jev-router.md` y `decisions/ADR-001-...`.

## Orden de implementación (dependencias)

1. **Config base** — `backend/config.py`, `.env.example`, `requirements.txt` (sin dependencia de código: los módulos la consumen).
2. **`backend/decision/schemas.py`** — enums, `TriageResult`, `RouteDecision`, `RoutingConfig` (Pydantic + dataclass). Núcleo de tipos que usan el resto.
3. **`backend/decision/jev.py`** — `build_questions()`, `classify()` (langchain-typesafe `TypeSafeClassifier.ainvoke` → aíslalo con try/except + fallback `httpx` a `POST /v1/systemone`), timeout vía `asyncio.wait_for`, normalización.
4. **`backend/decision/router.py`** — `decide()` puro (guard arraíles, política FAST/ORCHESTRATOR/BLOCK/PROPOSE_COMMIT, salvaguarda de confianza) y `route()` asíncrono con el evento `routing_decision`.
5. **`backend/decision/respond.py`** — `quick_answer(goal)` con `gpt-4o-mini` para el camino FAST.
6. **Voz** — `backend/voice/tools.py`: integrar ruteo en `delegate_complex_task`, estado `PENDING` y tool `confirm_execution`.
7. **Orquestador (defensa en profundidad)** — `backend/orchestrator/nodes.py` (`_build_llm(model)`), `tasks.py` (`run_pipeline` re-trieaga y elige modelo), `graph.py` (pasar modelo al planner).
8. **Tests** — en paralelo a 2-7 (mocks), y `pytest -q` al final.
9. **Commits** por capa lógica (`feat(decision)`, `feat(voice)`, `feat(orchestrator)`, `test(decision)`).

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `langchain-typesafe` alpha cambia API | Aislado en `jev.py`; fallback HTTP REST; tests mockean ambas rutas |
| Jev supera 600 ms | `asyncio.wait_for` → fallback fail-open ORCHESTRATOR |
| Baja confianza de Jev | Escalado conservador a ORCHESTRATOR (nunca FAST/BLOCK) |
| Evento de ruteo interrumpe por voz | `priority: silent` |
| Inyección silenciada | Threshold 0.85 configurable; BLOCK antes que cualquier otra regla |

## Verificación por capa

- Capa 2-4: `python -m pytest backend/tests/test_decision.py backend/tests/test_jev_client.py backend/tests/test_router_integration.py -q`.
- Capa 6-7: `python -m pytest backend/tests/test_tools_route.py backend/tests/test_graph.py -q`.
- Global: `python -m pytest -q`; assertion final de importación `python -c "from backend.decision import router"`.
- Manual: `POST /debug/run` y observar `routing_decision` por SSE (opcional, requiere Redis/worker).