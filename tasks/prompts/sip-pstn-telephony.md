# Prompt de delegación — Entrada por teléfono real (SIP/PSTN) y llamadas salientes

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/sip-pstn-telephony`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Añadir entrada por **teléfono real (SIP/PSTN)** además del navegador, y **llamadas salientes**
(`CreateSIPParticipant`):

1. Entrante: el agente responde a una llamada SIP entrante (LiveKit SIP), permitiendo delegar tareas
   y recibir las mismas interrupciones proactivas que en el navegador.
2. Saliente: al terminar un subagente después de que el usuario colgó, el sistema vuelve a llamar al
   número del usuario (`CreateSIPParticipant`) para contarle el resultado.
3. Earcon de aviso ya cubierto por su propia feature (`feat/earcon-interruption`) — no lo dupliques.

Diseño guiado por la investigación "Sistemas Multiagente y Voz Interactiva" del proyecto:
plano de voz (<800 ms, LiveKit) desacoplado del plano de ejecución (Celery) vía bus Redis.

## Alcance

- `backend/voice/agent.py` — soporte del agente SIP (`AgentServer`/`AgentSession` para llamadas entrantes).
- `backend/voice/tools.py` — herramienta/servicio para `CreateSIPParticipant` (llamada saliente) y estado.
- `backend/config.py`, `.env.example` — credenciales SIP (número/trunk), `AGENT_NUMBER`, `SIP_PHONE`….
- `backend/api/main.py` + `web/index.html` — control para marcar al número del usuario si hace falta.
- `backend/tests/` — tests (mockeando el cliente LiveKit; sin costes reales).

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (architectural), presenta el diseño en las secciones que sean necesarias y **espera aprobación
   humana (HARD-GATE)** antes de implementar.
2. Sigue `spec-driven-development` (spec en `docs/superpowers/specs/`) y `test-driven-development`.
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (o el de la plataforma) junto al código.
4. Commits por capa lógica con la convención del repo (`feat(voice): …`).
5. Documenta la decisión con la skill `decision-log`
   (CLI: `python .agents/skills/decision-log/scripts/decision_log.py new --title "…" --decisions-dir docs/decisions`)
   → `docs/decisions/ADR-NNN-*.md`, acompañando el commit que la implementa.
6. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- El agente responde a una llamada SIP entrante con el mismo flujo de voz/delegación que el navegador.
- `delegate_complex_task` funciona con el despacho de eventos Redis intacto (`plan_ready`, `subtask_done`, `analysis_ready`).
- Llamada saliente vía `CreateSIPParticipant` cuando el usuario cuelga y quedan subagentes por terminar.
- Tests en verde y ADR creado. Sin costes reales en la verificación (mock).