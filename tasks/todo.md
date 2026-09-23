# Todo — jev-router

- [ ] Config: `backend/config.py` + `.env.example` + `requirements.txt` (langchain-typesafe==0.0.1a3)
  - Verify: `python -c "import langchain_typesafe"` tras `pip install`
- [ ] `backend/decision/schemas.py` — enums, TriageResult, RouteDecision, RoutingConfig
  - Verify: pytest de tipos / import sin errores
- [ ] `backend/decision/jev.py` — build_questions, classify (langchain-typesafe + fallback HTTP, timeout)
  - Verify: `test_jev_client.py`
- [ ] `backend/decision/router.py` — decide() puro + route() async con evento routing_decision
  - Verify: `test_decision.py`, `test_router_integration.py`
- [ ] `backend/decision/respond.py` — quick_answer(goal) con modelo económico
  - Verify: import + uso en FAST
- [ ] Voz: `backend/voice/tools.py` — ruteo en delegate_complex_task, PENDING, confirm_execution
  - Verify: `test_tools_route.py`
- [ ] Orquestador: `nodes.py`, `tasks.py`, `graph.py` — re-triaje y modelo advanced
  - Verify: `test_graph.py` (ext.), `test_tools_route.py`
- [ ] `python -m pytest -q` en verde
- [ ] Commits por capa + `graphify update .`