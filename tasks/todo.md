# Todo — conversation-memory (issue #8)

- [x] Config: `backend/config.py` (`memory_enabled`, `memory_ttl_days`, `memory_max_chars`) + `.env.example`
  - Verify: import `backend.config.settings.memory_enabled` sin errores
- [x] Bus: `backend/bus/redis_client.py` — `mem_get` / `mem_set` con TTL, tolerantes
  - Verify: `test_memory_service.py` (mini)
- [x] Servicio: `backend/memory/` — load/store/summarize/publish_recalled, no-op desactivado, fallback
  - Verify: `test_memory_service.py`
- [x] Voz: web localStorage identity → `/token?identity=`; `/token` respeta identity (fallback `participant-…`); `tools.py` contextvar `USER_ID` + dispatch; `agent.py` saludo con memoria + evento silent
  - Verify: `test_api.py`, `test_tools_route.py`, `test_memory_voice.py`
- [x] Orquestador: `tasks.py` `run_pipeline(..., user_id=None)`; `nodes.py` `plan_subtasks(..., memory=None)`; `graph.py` state user_id + planner inyecta + synthesize guarda
  - Verify: `test_graph.py` (ext.), `test_tasks_route.py`
- [x] ADR-004 con skill `decision-log` en `docs/decisions/`
  - Verify: `docs/decisions/ADR-004-*.md` existe y acompaña el commit
- [x] `.venv\Scripts\python.exe -m pytest -q` en verde (91 passed)
- [ ] Commits por capa + `graphify update .`