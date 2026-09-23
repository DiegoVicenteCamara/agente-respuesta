# Prompt de delegación — Earcon (tono previo) antes de cada interrupción proactiva

Repositorio: `DiegoVicenteCamara/agente-respuesta` · Rama: `feat/earcon-interruption`.
Proyecto: agente de IA por voz (LiveKit + OpenAI Realtime + LangGraph/Celery/Redis) que descompone
tareas complejas, las delega a subagentes en segundo plano e interrumpe al usuario por voz.

## Tu tarea

Añadir un **earcon** (tono breve) antes de cada interrupción proactiva por voz, como propone la
investigación "Sistemas Multiagente y Voz Interactiva": el usuario debe percibir que se aproxima una
novedad antes de que el agente hable, reduciendo el sobresalto del barge-in.

Comportamiento esperado:

- En `backend/voice/agent.py`, `_listen_for_updates()` reproduce el tono justo **antes** de
  `session.generate_reply(...)` para eventos con `priority` `info` o `urgent` (no para `silent`).
- El tono se reproduce a través del `AgentSession`/room (no por el altavoz del servidor), para que la
  persona en la llamada lo oiga. Define el API concreto con la API real de LiveKit Agents en tu diseño.
- Configurable y desactivado por defecto (evita sorprender): flag `EARCON_ENABLED` en
  `backend/config.py` + `.env.example`, y opcional `EARCON_PATH` al asset de audio.

## Alcance

- `backend/voice/agent.py` — insertar el earcon en `_listen_for_updates()`.
- `backend/config.py`, `.env.example` — flag/asset de configuración.
- `backend/tests/test_notifier.py` (o un nuevo `test_earcon.py`) — verifica que se emite tono solo
  para `info`/`urgent`, sin cambiar la política existente en `backend/voice/notifier.py`.

## Proceso obligatorio

1. Lee `AGENTS.md` (registra la skill `brainstorming`). Invoca `brainstorming`, clasifica la idea
   (**bounded**: cambio bien acotado en código existente), presenta el diseño corto en chat y
   **espera aprobación humana (HARD-GATE)** antes de implementar.
2. Sigue `test-driven-development`. No escribas spec (bounded).
3. Tests: `.venv\Scripts\python.exe -m pytest -q` (o el de la plataforma) junto al código.
4. Commit único con la convención del repo (`feat(voice): …`).
5. Ejecuta `graphify update .` tras modificar código.

## Criterios de éxito

- Se reproduce el tono antes de cada interrupción `info`/`urgent`; los eventos `silent` no suenan.
- Con `EARCON_ENABLED=false` la conducta actual queda intacta.
- Tests verdes; `notifier.build_spoken_update` no se modifica (política intacta).