# Prompt de delegación — Panel web de historial y estado de tareas pasadas

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/task-history-ui`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Ofrecer en la web local un **panel de historial** con las tareas pasadas (objetivo, estado,
resultado final y eventos), aprovechando el flujo de eventos que ya se publica en Redis.

Actualmente `web/index.html` solo muestra la tarea en vivo vía `POST /debug/run` + SSE
(`GET /debug/stream`); los eventos no se guardan y cada tarea nueva pierde el historial.

1. **Persistencia ligera:** al publicar eventos en el bus (`backend/bus/redis_client.py`), además del
   pub/sub, guardar el payload en `task:{task_id}:events` (lista con `LPUSH/RPUSH`) y mantener un
   índice de tareas `tasks:index` (set ordenado por `ts`). Documenta en el diseño si prefieres
   persistirlo en `_publish` o en un único consumidor.
2. **Endpoint histórico** en `backend/api/main.py`: `GET /tasks` → lista de `{task_id, goal, ts,
   last_event, status, analysis}` y `GET /tasks/{task_id}` → eventos ordenados. Esquema mínimo
   (`RunGoal` ya existe); reutiliza los helpers de `redis_client`.
3. **Panel en `web/index.html`:** sección de historial que lista las tareas pasadas, muestra el
   estado y expande los eventos al seleccionar una (mismo estilo visual del grafo existente, sin
   tocar su geometría). Consumo via `fetch("/tasks")`.

## Alcance

- `backend/bus/redis_client.py` — helpers `store_event`, `list_tasks`, `get_task_events` (con `publish_event` tocando lo mínimo).
- `backend/api/main.py` — `GET /tasks` y `GET /tasks/{task_id}`.
- `web/index.html` — panel de historial (fetch). No alterar la escala del grafo.
- `backend/tests/` — tests del API con Redis mock/real para listado y detalle.

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (**bounded**: cambios acotados en código existente de la web + API), presenta el diseño corto en
   chat y **espera aprobación humana (HARD-GATE)** antes de implementar.
2. Sigue `test-driven-development`. No escribas spec (bounded).
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (nuevos tests del API). Verifica el harness del
   grafo Node si tocas la geometría (15 asserts en `tools/...`) — no debe regresar.
4. Commit(s) con la convención del repo (`feat(web)`, `feat(api)`, `test(api)`).
5. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- Una tarea lanzada por el "Modo prueba" aparece en el historial con su cadena de eventos.
- `GET /tasks/{task_id}` devuelve los eventos en orden; `GET /tasks` lista sin romper ante Redis caído
  (degradación elegante, respuesta vacía).
- El grafo existente de la web no cambia de escala (invariantes del harness intactas).
- Tests verdes.