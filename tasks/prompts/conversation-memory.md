# Prompt de delegación — Memoria persistente de conversaciones por usuario

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/conversation-memory`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Dar **memoria persistente entre sesiones**: el agente recuerda el historial y las preferencias de cada
usuario entre llamadas y usa ese contexto en el planificador.

1. **Identidad del usuario:** el agente de voz propaga un `user_id` (identidad del participante de
   LiveKit; en `feat/sip-pstn-telephony` será el número de teléfono) hasta la tarea Celery
   (`backend/voice/tools.py` → `backend/orchestrator/tasks.py`).
2. **Resumen persistente:** el nodo `synthesize` genera/actualiza un resumen de la conversación del
   usuario y lo guarda en Redis (`backend/bus/redis_client.py`), clave `user:{user_id}:memory` con TTL
   largo configurable.
3. **Inyección de contexto:** el nodo `planner` (`backend/orchestrator/nodes.py`) recibe el resumen
   previo y lo incorpora al prompt de planificación (concisa, sin desviar la tarea actual).
4. **Nuevas llamadas:** cuando un usuario vuelve a llamar, el agente puede aludir a recuerdos ("la
   última vez investigaste X") con `priority: silent` o una línea sutil en el saludo.

Diseño fiel a la arquitectura: los planos de voz y ejecución siguen desacoplados via bus Redis; la
memoria es un servicio por debajo del grafo, no lógica dentro del plano de voz.

## Alcance

- `backend/memory/` (nuevo) — `store()`, `load()`, `summarize(goal, analysis)` con TTL y claves por `user_id`.
- `backend/bus/redis_client.py` — helpers de lectura/escritura con tipos para la memoria.
- `backend/voice/agent.py` / `backend/voice/tools.py` — propagar `user_id` en la delegación.
- `backend/orchestrator/nodes.py` (+ `graph.py` state) — inyectar memoria en `planner`, guardar en `synthesize`.
- `backend/config.py`, `.env.example` — `MEMORY_TTL_DAYS`, flag `MEMORY_ENABLED`.
- `backend/tests/` — tests con Redis real/mock (hash/fixture de la búsqueda existente).

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (**architectural**: nuevo subsistema), presenta el diseño por secciones y **espera aprobación
   humana (HARD-GATE)** antes de implementar.
2. Sigue `spec-driven-development` (spec en `docs/superpowers/specs/`) y `test-driven-development`.
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (o el de la plataforma) junto al código.
4. Commits por capa lógica (`feat(memory)`, `feat(voice)`, `feat(orchestrator)`).
5. Documenta la decisión con la skill `decision-log`
   (CLI: `python .agents/skills/decision-log/scripts/decision_log.py new --title "…" --decisions-dir docs/decisions`)
   → `docs/decisions/ADR-NNN-*.md`, acompañando el commit que la implementa.
6. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- Un usuario completa una investigación; una segunda llamada del mismo `user_id` recupera el resumen
  y el planificador lo usa (visible en el prompt de prueba).
- `MEMORY_ENABLED=false` deja el flujo actual 100 % intacto.
- Resumen guardado tras `analysis_ready`; TTL respetado; tests verdes y ADR creado.