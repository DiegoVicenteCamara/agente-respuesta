# Prompt de delegación — Seguimiento de coste (tokens/€) por tarea

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/cost-tracking`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Medir el **coste estimado de cada tarea** (tokens → €) y exponerlo: resumen en el evento final y en
el historial. Hoy no hay ninguna contabilidad de uso LLM.

1. **Recuento de tokens:** un callback/recolector (p. ej. `BaseCallbackHandler` de LangChain
   `on_llm_start/on_llm_end`, o conteo con `tiktoken` a falta de metadata) que acumula
   `input_tokens`/`output_tokens` por modelo en `backend/orchestrator/nodes.py` (planner, research,
   synthesize y `respond.quick_answer` del camino `fast`). Modelo económico el objetivo: cero o casi
   cero overhead en el hot path.
2. **Tarificación:** tabla de precios por modelo en config (`PRICING_<MODEL>_PER_1K_IN` /
   `OUT`, defaults aproximados públicos de OpenAI) para convertir tokens → € (configurable).
3. **Publicación:** el pipeline finaliza con un evento `cost_ready` (`priority: silent`) que incluye
   `{task_id, model, tokens_in, tokens_out, cost_eur}`; acumúlese y guárdese en el historial de la
   tarea (ver `feat/task-history-ui`; aqui basta con dejar el dato en el payload).
4. **Superficie mínima:** el coste puede mostrarse en el body del evento; no hace falta UI en esta
   feature (la consume el panel de historial).

## Alcance

- `backend/orchestrator/nodes.py` (+ llamadas `chat`/`quick_answer`) — recolectar tokens.
- `backend/config.py`, `.env.example` — tabla de precios y toggle `COST_TRACKING_ENABLED`.
- `backend/orchestrator/tasks.py` / `backend/voice/tools.py` — emitir `cost_ready` al cerrar la tarea (ambos caminos: orquestador y `fast`).
- `backend/tests/` — `test_cost_tracking.py`: acumulación correcta ~ precio, -plantilla que falla ante `COST_TRACKING_ENABLED=false`.

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (**bounded**: cambios acotados en módulos existentes), presenta el diseño corto en chat y
   **espera aprobación humana (HARD-GATE)** antes de implementar.
2. Sigue `test-driven-development`. No escribas spec (bounded).
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (o el de la plataforma) junto al código.
4. Commits con la convención del repo (`feat(orchestrator)`, `test(orchestrator)`).
5. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- Una tarea completa emite `cost_ready` con tokens y `cost_eur` calculados (orquestador y `fast`).
- Overhead mínimo: la recolección no añade llamadas de red ni bloquea el grafo.
- `COST_TRACKING_ENABLED=false` deja el flujo actual intacto.
- Tests verdes; coste es *estimación*, marcada como tal en el payload (`estimated: true`).