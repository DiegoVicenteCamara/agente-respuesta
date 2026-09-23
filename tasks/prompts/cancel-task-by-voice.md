# Prompt de delegación — Cancelación por voz de la tarea en curso

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/cancel-task-by-voice`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Permitir que el usuario **cancele por voz** la tarea en curso (p. ej. «para», «cancela lo que
estés haciendo»), de modo que los subagentes se detengan y el agente confirme lo hecho.

1. **Registro de la tarea activa:** al delegar (tool `delegate_complex_task`), guardar
   `{task_id, goal}` en un registro por sesión (patrón del dict `PENDING` ya existente en
   `backend/voice/tools.py`). Mismo `task_id` que el que se envía a Celery.
2. **Herramienta `cancel_task`:** nueva `@function_tool()` expuesta en `OrchestratorAgent`
   (`backend/voice/agent.py`) con instrucción en `SYSTEM_PROMPT`. Al invocarla:
   - `celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")` (o `revoke` sin
     `terminate` si las subtareas registran puntos de cancelación pacíficos — decide en el diseño).
   - Publica un evento `task_cancelled` con `priority: info` para que el agente confirme por voz el
     resultado de la cancelación.
   - Elimina el `task_id` del registro de la sesión.
3. **Mensajes:** si no hay tarea activa, `NO_ACTIVE_TASK_MESSAGE` cortés.

## Alcance

- `backend/voice/tools.py` — registro de tarea activa + `cancel_task_core` + tool `cancel_task`.
- `backend/voice/agent.py` — registrar la tool en la lista de herramientas y mencionarla en el prompt del sistema.
- `backend/orchestrator/tasks.py` — confirmar que `revoke` no rompe eventos; opcional punto de cancelación en el grafo.
- `backend/tests/` — `test_tools_route.py`/nuevo test: cancelación con/ sin tarea activa, evento `task_cancelled` publicado.

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (**bounded**: cambio bien acotado en código existente), presenta el diseño corto en chat y
   **espera aprobación humana (HARD-GATE)** antes de implementar. Si descubres complejidad oculta
   (p. ej. cancelar tareas ya en fan-out), súbela a architectural y dila.
2. Sigue `test-driven-development`. No escribas spec (bounded).
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (o el de la plataforma) junto al código.
4. Commit(s) con la convención del repo (`feat(voice)`, `test(voice)`).
5. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- «Para/cancela» → la tarea activa se revoca, el registro de sesión se limpia y el agente responde.
- Sin tarea activa → mensaje cortés y sin efectos colaterales.
- El evento `task_cancelled` llega por el mismo canal Redis que el resto (mismo formato de payload).
- Tests verdes sin tocar los flujos `fast`/`block`/`propose_commit` existentes.