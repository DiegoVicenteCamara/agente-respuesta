# Spec: Jev System 1 dual-model router (`jev-router`)

## Capability Map

| Module id | Responsibility | Depends on |
|---|---|---|
| jev-client | Llamada tipada a Jev (langchain-typesafe + fallback HTTP), timeout, normalización Pydantic | config |
| jev-schema | Primitivas y enums: worker, complexity_tier, risk_index, is_prompt_injection, RouteDecision | — |
| model-router | Política pura de ruteo (FAST/ORCHESTRATOR/BLOCK/PROPOSE_COMMIT) + guardarraíles | jev-client, jev-schema |
| voice-integration | `delegate_complex_task` + `confirm_execution` en el plano de audio | model-router, respond |
| orchestrator-defense | Re-triaje en `run_pipeline`, selección de modelo avanzado | model-router, respond |

Build order: jev-schema → jev-client → model-router → respond → voice-integration/orchestrator-defense → tests.

## Objective

Descongestionar el orquestador LangGraph/Celery añadiendo una capa intermedia de filtrado, triaje y enrutamiento basada en Jev (Sistema 1 de TypeSafe AI). Mantener el presupuesto de latencia acústica (<500-800 ms) y reducir costes de cómputo enrutando tareas triviales al modelo económico (`gpt-4o-mini`) y solo las complejas/alto riesgo al orquestador con modelo avanzado (`gpt-4o`). Añadir guardarraíles deterministas: bloqueo por inyección de instrucciones y flujo Propose-Commit para riesgo crítico.

## Tech Stack

- Python 3.11+; Pydantic (modelos), `langchain-typesafe==0.0.1a3` (cliente primario), `httpx==0.28.1` (fallback HTTP REST, ya presente), `asyncio` (timeouts). Integra con el stack existente: FastAPI, LiveKit/OpenAI Realtime, Celery/Redis, LangGraph.

## Commands

```bash
pip install -r backend/requirements.txt
python -m pytest -q
python -m pytest backend/tests/test_decision.py -q
```

## Project Structure

```
backend/
  decision/            → Capa nueva: schemas.py, jev.py, router.py, respond.py (+ __init__.py)
  voice/tools.py       → ruteo en delegate_complex_task + confirm_execution
  orchestrator/        → tasks.py (re-triaje), nodes.py (_build_llm model override), graph.py
  config.py            → settings nuevos (TYPESAFE_*, OPENAI_FAST/ADVANCED, umbrales, timeout)
  tests/               → test_decision.py, test_jev_client.py, test_router_integration.py,
                         test_tools_route.py, test_graph.py (ext.)
.env.example           → variables nuevas
requirements.txt       → + langchain-typesafe==0.0.1a3
decisions/ADR-001-...  → decisión de arquitectura (accepted)
```

## Code Style

Sigue las convenciones del repo: docstrings en español con triple comilla, imports stdlib→terceros→locales, tipado estricto (módulos con `from __future__ import annotations` opcional), clases Pydantic con atributos tipados, funciones asíncronas con nombres de verbo. No añadir comentarios salvo «noqa» de lint.

Ejemplo de estilo:

```python
class RouteDecision(BaseModel):
    action: RouteAction
    model: str
    reason: str
    fallback: bool = False
    latency_ms: int = 0
```

## Testing Strategy

- Framework: pytest + pytest-asyncio (modo auto configurado en pytest.ini). Testpaths: `backend/tests`.
- Nivel unitario: `decide()` (política pura) con tabla de casos (2x2 tier/worker x riesgo y inyección). `read()`/`build_questions()` sin I/O mockeado.
- Nivel de integración: `route()` con `TypeSafeClassifier` y `httpx` mockeados; emisión de `routing_decision` con `priority: silent`; timeout→fallback ORCHESTRATOR; tool de voz con `celery_app.send_task` monkeypatcheado; `run_pipeline` con re-triaje y modelo avanzado.
- Garantizar tipos estrictos: instantiar `RouteDecision` desde respuestas malformadas debe elevar `ValidationError`/devolver fallback, nunca extraer con `dict.get`.

## Boundaries

- Always: correr `python -m pytest -q` antes de cada commit; respetar tipado estricto; solo enviar `goal` como `state` a Jev (nunca system prompts); eventos de ruteo en `priority: silent`.
- Ask first: cambiar umbrales por defecto; añadir dependencias nuevas; alterar el bus de eventos; tocar la config de Celery.
- Never: enviar claves/secretos a logs o a Jev; degradar BLOCK/PROPOSE_COMMIT por baja confianza; despachar al grafo tareas FAST.

## Success Criteria

- `python -m pytest -q` verde con los casos: fast vs advanced según complejidad, mitigación de inyecciones, confirmaciones de alto riesgo, formato estricto de tipos.
- `delegate_complex_task`: FAST no despacha a Celery y devuelve respuesta del modelo económico; ORCHESTRATOR pasa `complexity_tier` y `planner_model` a `send_task`; BLOCK no envía y rechaza con cortesía; PROPOSE_COMMIT queda en `PENDING` y `confirm_execution(True)` despacha (False no).
- `run_pipeline` re-trieaga: entrada low+risk<umbral → respuesta directa sin construir el grafo; tier=high → planner avanzado.
- Evento `routing_decision` publicado con `task_id`, `route`, `tier`, `risk`, `injection`, `confidence`, `model`, `latency_ms`, `fallback` y `priority=silent`.
- `.env.example` y `config.py` exponen `TYPESAFE_API_KEY`, `TYPESAFE_MODEL`, `OPENAI_FAST_MODEL`, `OPENAI_ADVANCED_MODEL` y umbrales con valores por defecto razonables.

## Open Questions

- `langchain-typesafe==0.0.1a3` es alpha: el fallback HTTP REST absorbe cambios de API; revisar en la próxima revisión del ADR (2026-12-23).
- `target_worker` billing/identity/support sin worker real: mapean a orquestador/escalada hasta que nazcan dichos workers.