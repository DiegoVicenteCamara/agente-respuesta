# Todo — conversation-memory (issue #8)

- [ ] Config: `backend/config.py` (`memory_enabled`, `memory_ttl_days`, `memory_max_chars`) + `.env.example`
  - Verify: import `backend.config.settings.memory_enabled` sin errores
- [ ] Bus: `backend/bus/redis_client.py` — `mem_get` / `mem_set` con TTL, tolerantes
  - Verify: `test_memory_service.py` (mini)
- [ ] Servicio: `backend/memory/` — load/store/summarize/publish_recalled, no-op desactivado, fallback
  - Verify: `test_memory_service.py`
- [ ] Voz: web localStorage identity → `/token?identity=`; `/token` respeta identity (fallback `participant-…`); `tools.py` contextvar `USER_ID` + dispatch; `agent.py` saludo con memoria + evento silent
  - Verify: `test_api.py`, `test_tools_route.py`
- [ ] Orquestador: `tasks.py` `run_pipeline(..., user_id=None)`; `nodes.py` `plan_subtasks(..., memory=None)`; `graph.py` state user_id + planner inyecta + synthesize guarda
  - Verify: `test_graph.py` (ext.), `test_tasks_route.py`
- [ ] ADR-004 con skill `decision-log` en `docs/decisions/`
  - Verify: `docs/decisions/ADR-004-*.md` existe y acompaña el commit
- [ ] `.venv\Scripts\python.exe -m pytest -q` en verde
- [ ] Commits por capa + `graphify update .`