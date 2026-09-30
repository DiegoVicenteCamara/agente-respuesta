# Graph Report - AgenteRespuesta  (2026-09-25)

## Corpus Check
- 84 files · ~50,041 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .example 1, (none) 1, .ini 1)

## Summary
- 1223 nodes · 2314 edges · 86 communities (68 shown, 18 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 248 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9bbc19ee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- decision_log.py
- graph.py
- main.py
- delegate_complex_task
- test_decision_log.py
- review_checker.py
- Decision Log
- Bitácora de Avances y Retrospectivas (project-log)
- Spec-Driven Development
- Respuesta — Agente de voz con subagentes proactivos
- ADR Format Guide
- Review Cadence Rules
- ADR-NNN: Decision Title
- load_decisions
- compute_next_review
- Agent Skills (OpenCode)
- Summarize Meeting
- graphify.js
- opencode.json
- build_parser
- Path
- ADR-001: Grafo de organización tipo ramas GitHub con columnas reutilizables por tarea
- create_decision
- Bitácora — Semana del 2026-09-21 al 2026-09-27
- router.py
- test_tools_route.py
- test_cost_tracking.py
- test_tasks_route.py
- server.cjs
- Visual Companion Guide
- startServer
- handleRequest
- Brainstorming Ideas Into Designs
- ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)
- helper.js
- handleUpgrade
- stop-server.sh
- test_voice_entrypoint.py
- renderBranding
- mem_get
- start-server.sh
- spec-document-reviewer-prompt.md
- get_task_events
- test_graph.py
- Definición de Hecho (DoD)
- ADR-003: Automatización de issues con opencode GitHub agent
- schemas.py
- test_earcon.py
- run_pipeline
- _listen_for_updates
- chat
- test_research_cache.py
- _FakeSyncRedis
- earcon.py
- test_memory_service.py
- redis_client.py
- build_spoken_update
- ADR-004: Memoria persistente de conversaciones por usuario en Redis
- summarize
- should_play
- test_notifier_flow.py
- FakePubSub
- publish_event
- _get
- pytest
- test_api.py
- RouteAction
- jev.py
- fake_redis
- Spec: Memoria persistente de conversaciones por usuario (issue #8)
- Spec: Jev System 1 dual-model router (`jev-router`)
- fake_redis
- fake_redis
- agent.py
- _patch

## God Nodes (most connected - your core abstractions)
1. `RouteAction` - 57 edges
2. `RouteDecision` - 24 edges
3. `run_pipeline()` - 24 edges
4. `publish_event()` - 23 edges
5. `decide()` - 23 edges
6. `delegate_complex_task_core()` - 21 edges
7. `route()` - 20 edges
8. `TargetWorker` - 19 edges
9. `voice_entrypoint()` - 19 edges
10. `ComplexityTier` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Option B: Triaje solo en el tool de voz `delegate_complex_task`` --references--> `delegate_complex_task()`  [INFERRED]
  decisions/ADR-001-use-jev-system-1-triage-for-dual-model-routing.md → backend/voice/tools.py
- `Contexto actual` --references--> `publish_event()`  [INFERRED]
  docs/superpowers/specs/2026-09-23-conversation-memory-design.md → backend/bus/redis_client.py
- `Alcance` --references--> `publish_event()`  [INFERRED]
  tasks/prompts/task-history-ui.md → backend/bus/redis_client.py
- `Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel` --references--> `ClassifyOutcome`  [INFERRED]
  docs/decisions/ADR-002-publicar-causa-de-jev-unavailable-en-routing-decision-detalle.md → backend/decision/jev.py
- `Testing Strategy` --references--> `build_questions()`  [INFERRED]
  SPEC-jev-router.md → backend/decision/jev.py

## Import Cycles
- None detected.

## Communities (86 total, 18 thin omitted)

### Community 0 - "decision_log.py"
Cohesion: 0.15
Nodes (19): main(), normalized_status(), parse_date(), parse_decision(), parse_next_review(), parse_status(), parse_supersedes_to(), parse_title() (+11 more)

### Community 1 - "graph.py"
Cohesion: 0.11
Nodes (28): backend_memory, build_graph(), _fan_out(), _load_memory(), planner(), _publish(), Grafo supervisor en LangGraph. Planifica el objetivo, lanza subagentes de…, research() (+20 more)

### Community 2 - "main.py"
Cohesion: 0.14
Nodes (14): debug_run(), BaseModel, API web: sirve la página del navegador y emite tokens JWT de LiveKit., Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz., RunGoal, fastapi, fastapi_responses, fastapi_staticfiles (+6 more)

### Community 3 - "delegate_complex_task"
Cohesion: 0.15
Nodes (17): Agent, OrchestratorAgent, cancel_task(), confirm_execution(), delegate_complex_task(), Delega un objetivo complejo a un equipo de subagentes que trabajan en segundo…, Confirma o cancela una acción de alto riesgo pendiente de aprobación. Args:…, Cancela la tarea en curso que los subagentes están ejecutando en segundo plano.… (+9 more)

### Community 4 - "test_decision_log.py"
Cohesion: 0.08
Nodes (31): make_log(), Path, A decision with a past review date appears in due-review output., Timeline output follows a superseding chain from oldest to newest., Review cadence computation handles monthly, quarterly, and annually., Status filtering returns only decisions with the requested status family., Temporary decisions directory fixture helper., Tests for the decision-log skill CLI and helpers. (+23 more)

### Community 5 - "review_checker.py"
Cohesion: 0.10
Nodes (31): adr_glob(), build_parser(), due_accepted_decisions(), format_due_message(), main(), parse_decision(), parse_next_review(), parse_status() (+23 more)

### Community 6 - "Decision Log"
Cohesion: 0.08
Nodes (23): ADR format, Common pitfalls, Consequences, Context, Date, Decision, Decision Log, File delivery (+15 more)

### Community 7 - "Bitácora de Avances y Retrospectivas (project-log)"
Cohesion: 0.14
Nodes (13): 1. Reunir la fuente de verdad, 2. Comparar planificado vs ejecutado, 3. Redactar la entrada, 4. Guardar y entregar, Bitácora de Avances y Retrospectivas (project-log), Criterios de verificación, Ejemplo de entrada, Estructura de salida (+5 more)

### Community 8 - "Spec-Driven Development"
Cohesion: 0.14
Nodes (13): Common Rationalizations, Keeping the Spec Alive, Overview, Phase 0: Scope Check, Phase 1: Specify, Phase 2: Plan, Phase 3: Tasks, Phase 4: Implement (+5 more)

### Community 9 - "Respuesta — Agente de voz con subagentes proactivos"
Cohesion: 0.13
Nodes (14): Configuración, Cómo notifica (ergonomía de la investigación), Ejecución (4 terminales), Estructura, Implementación autónoma de issues (opencode en CI), Manual (4 terminales), Modo prueba (sin voz, sin créditos OpenAI), Probar (+6 more)

### Community 10 - "ADR Format Guide"
Cohesion: 0.17
Nodes (11): ADR Format Guide, Complete example, Consequences, Context, Date, Decision, File name and title, Options Considered (+3 more)

### Community 11 - "Review Cadence Rules"
Cohesion: 0.18
Nodes (10): annually, Cadence options, Calendar-month calculation, Choosing the right cadence, How due review detection works, monthly, on-trigger, quarterly (+2 more)

### Community 12 - "ADR-NNN: Decision Title"
Cohesion: 0.18
Nodes (10): ADR-NNN: Decision Title, Consequences, Context, Date, Decision, Option A: [name], Option B: [name], Options Considered (+2 more)

### Community 13 - "load_decisions"
Cohesion: 0.15
Nodes (17): build_timeline_chains(), command_timeline(), due_reviews(), filter_decisions(), format_table(), format_timeline(), load_decisions(), Any (+9 more)

### Community 14 - "compute_next_review"
Cohesion: 0.28
Nodes (9): add_months(), compute_next_review(), is_leap_year(), date, Return True when a year is a Gregorian leap year., Compute the next review date for a cadence, or blank for on-trigger., Render a new ADR Markdown document from the embedded template., Add calendar months to a date, clamping the day at month end. (+1 more)

### Community 15 - "Agent Skills (OpenCode)"
Cohesion: 0.29
Nodes (6): Agent Skills (OpenCode), Core Rules, Documentación obligatoria (para siempre documentar las cosas), Execution Model, graphify, Intent → Skill Mapping

### Community 16 - "Summarize Meeting"
Cohesion: 0.33
Nodes (5): Context, Instructions, Notes, Purpose, Summarize Meeting

### Community 17 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 30 - "build_parser"
Cohesion: 0.19
Nodes (16): build_parser(), command_due_review(), command_list(), command_new(), command_search(), command_supersede(), ArgumentParser, Handle the new subcommand. (+8 more)

### Community 31 - "Path"
Cohesion: 0.19
Nodes (15): add_supersede_link(), adr_glob(), find_adr_path(), next_adr_number(), parse_adr_number(), Path, Read UTF-8 text from a file., Find the ADR file path for a number or raise a clear error. (+7 more)

### Community 32 - "ADR-001: Grafo de organización tipo ramas GitHub con columnas reutilizables por tarea"
Cohesion: 0.13
Nodes (14): ADR-001: Grafo de organización tipo ramas GitHub con columnas reutilizables por tarea, Asignación de columnas, Consequences, Context, Date, Decision, Option 1: lane global creciente (estado previo), Option 2: columnas reutilizables por tarea con "columna libre más próxima" (SELECCIONADA) (+6 more)

### Community 33 - "create_decision"
Cohesion: 0.22
Nodes (9): create_decision(), DecisionLogError, Create a new sequential ADR file and return its path., Replace the content of the Status section with a new status value., Raised when a decision-log operation cannot be completed., Convert a title to a filesystem-safe kebab-case slug., replace_status(), slugify() (+1 more)

### Community 34 - "Bitácora — Semana del 2026-09-21 al 2026-09-27"
Cohesion: 0.29
Nodes (6): Bitácora — Semana del 2026-09-21 al 2026-09-27, Bloqueos que continúan, Desvíos o Bloqueos, Lecciones aprendidas, Logros del periodo, Página de estado

### Community 35 - "router.py"
Cohesion: 0.13
Nodes (24): ClassifyOutcome, Resultado de ``classify``: el triaje y, si no hay, por qué no lo hay., fallback_decision(), _publish_event(), Política de enrutamiento dual (FAST / ORCHESTRATOR / BLOCK / PROPOSE_COMMIT).…, Decisión de fallback fail-open: todo se escala al orquestador., Clasifica el ``goal``, decide el ruteo y publica el evento de observabilidad., route() (+16 more)

### Community 36 - "test_tools_route.py"
Cohesion: 0.08
Nodes (47): BaseModel, Decisión de ruteo: acción, modelo y contexto para observabilidad., RouteDecision, _decision(), fake_redis(), FakeCtx, _FakeRedis, patch_quick_answer() (+39 more)

### Community 37 - "test_cost_tracking.py"
Cohesion: 0.05
Nodes (46): CostTracker, current(), estimate_cost_eur(), _model_slug(), ModelUsage, publish_cost_ready(), Recolección ligera de tokens y coste estimado por tarea. Un ``CostTracker`` por…, Callback de LangChain que registra el uso de tokens en el tracker activo.… (+38 more)

### Community 38 - "test_tasks_route.py"
Cohesion: 0.22
Nodes (13): _decision(), patch_quick_answer(), patch_route(), _patch(), fixture, Defensa en profundidad en run_pipeline: re-triaje y selección de modelo., test_blocked_task_is_refused(), test_fast_task_is_answered_without_building_graph() (+5 more)

### Community 39 - "server.cjs"
Cohesion: 0.08
Nodes (24): clients, CONTENT_DIR, crypto, debounceTimers, frameTemplate, fs, helperScript, http (+16 more)

### Community 40 - "Visual Companion Guide"
Cohesion: 0.10
Nodes (19): Browser Events Format, Cards (visual designs), Cleaning Up, CSS Classes Available, Design Tips, File Naming, How It Works, Mock elements (wireframe building blocks) (+11 more)

### Community 41 - "startServer"
Cohesion: 0.16
Nodes (12): browserLauncherForPlatform(), chmodOwnerOnly(), companionUrl(), generateToken(), initialToken(), maybeOpenBrowser(), preferredPort(), randomPort() (+4 more)

### Community 42 - "handleRequest"
Cohesion: 0.22
Nodes (11): bootstrapPage(), getNewestScreen(), handleRequest(), isAuthorized(), isFullDocument(), isRegularFileInsideContentDir(), parseCookies(), pathnameOf() (+3 more)

### Community 43 - "Brainstorming Ideas Into Designs"
Cohesion: 0.18
Nodes (10): After the Design (architectural path), Anti-Pattern: "Too Simple To Need Approval", Brainstorming Ideas Into Designs, Checklist, Establish Shared Understanding, Process Flow, Red Flags, The Process (+2 more)

### Community 44 - "ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)"
Cohesion: 0.18
Nodes (10): ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle), Consequences, Context, Date, Option A: Log en servidor, sin tocar el payload del evento, Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel, Option C: Endpoint de diagnóstico dedicado, Options Considered (+2 more)

### Community 45 - "helper.js"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 46 - "handleUpgrade"
Cohesion: 0.25
Nodes (8): broadcast(), computeAcceptKey(), decodeFrame(), encodeFrame(), handleMessage(), handleUpgrade(), isAllowedWebSocketOrigin(), touchActivity()

### Community 47 - "stop-server.sh"
Cohesion: 0.52
Nodes (6): command_has_server_id(), command_line_for_pid(), is_brainstorm_server(), mark_stopped(), read_expected_server_id(), stop-server.sh script

### Community 48 - "test_voice_entrypoint.py"
Cohesion: 0.06
Nodes (50): _fake_ctx(), _FakeParticipant, Tests de la capa de voz con memoria: bienvenida y resolución de identidad., test_build_welcome_mentions_previous_work(), test_build_welcome_without_memory_uses_base_instructions(), test_resolve_user_id_defaults_to_anonymous(), test_resolve_user_id_falls_back_to_token_claims(), test_resolve_user_id_prefers_human_participant() (+42 more)

### Community 49 - "renderBranding"
Cohesion: 0.40
Nodes (5): brandMarkup(), escapeHtmlText(), renderBranding(), waitingPage(), wrapInFrame()

### Community 50 - "mem_get"
Cohesion: 0.32
Nodes (7): mem_get(), mem_set(), Lee un valor con TTL; tolerante a Redis caído (None + log)., Escribe un valor con TTL; tolerante a Redis caído (no-op + log)., test_mem_helpers_roundtrip_with_ttl(), Riesgos y mitigaciones, Todo — conversation-memory (issue #8)

### Community 53 - "get_task_events"
Cohesion: 0.13
Nodes (15): AsyncRedis, get_task(), Eventos ordenados de una tarea pasada., get_async(), get_task_events(), _make_client(), Any, Eventos ordenados de una tarea (vacío si la tarea no existe). (+7 more)

### Community 54 - "test_graph.py"
Cohesion: 0.11
Nodes (15): _async_list(), _async_str(), fake_redis(), _FakeRedis, asyncio, fixture, stub_nodes(), fake_chat() (+7 more)

### Community 55 - "Definición de Hecho (DoD)"
Cohesion: 0.33
Nodes (5): Criterios, Cómo funciona la revisión automática (resumen), Definición de Hecho (DoD), Evidencia estructurada (punto 4), Referencias

### Community 56 - "ADR-003: Automatización de issues con opencode GitHub agent"
Cohesion: 0.08
Nodes (24): ADR-003: Automatización de issues con opencode GitHub agent, Consequences, Context, Date, Decision, Option A: GitHub Copilot coding agent (`@copilot`), Option B: Claude Code Action (`anthropics/claude-code-action`), Option C: opencode en CI con `anomalyco/opencode/github@latest` (+16 more)

### Community 57 - "schemas.py"
Cohesion: 0.14
Nodes (22): _normalize(), Convierte las respuestas tipadas de Jev en un ``TriageAnswer`` estricto., ComplexityTier, DecisionNormalizationError, Esquema tipado de la capa de decisión (triaje Sistema 1 / Jev). Define los…, La respuesta de Jev no pudo normalizarse a un triaje estricto., Trabajador de dominio al que debe atenderse la solicitud. Hoy solo ``dialogue``…, Complejidad operativa de la tarea: decide el costo del modelo. (+14 more)

### Community 58 - "test_earcon.py"
Cohesion: 0.18
Nodes (15): disable_earcon(), enable_earcon(), FakeHandle, FakeSession, asyncio, fixture, Tests del earcon (tono previo) antes de interrupciones proactivas. La política…, test_play_earcon_disabled_never_sounds() (+7 more)

### Community 59 - "run_pipeline"
Cohesion: 0.19
Nodes (12): run_pipeline(), ADR-001: Use Jev System 1 triage for dual-model routing, Consequences, Context, Date, Decision, Option A: Triaje solo en la entrada del orquestador (Celery `run_pipeline`), Option B: Triaje solo en el tool de voz `delegate_complex_task` (+4 more)

### Community 60 - "_listen_for_updates"
Cohesion: 0.17
Nodes (9): AgentSession, FakeRedis, FakeVoiceSession, test_listen_disabled_no_earcon_but_replies(), test_listen_plays_earcon_before_reply_for_info(), test_listen_silent_no_earcon_no_reply(), spy_play(), _listen_for_updates() (+1 more)

### Community 61 - "chat"
Cohesion: 0.13
Nodes (15): quick_answer(), Devuelve la respuesta del modelo económico a una tarea de complejidad baja., _build_llm(), chat(), Any, Envía un mensaje a un LLM genérico; si no hay clave o falla, devuelve vacío., Contrato de `backend/memory/`, Orden de implementación (dependencias) (+7 more)

### Community 62 - "test_research_cache.py"
Cohesion: 0.08
Nodes (29): get_sync(), Lee resultados cacheados; None en miss o Redis caído (tolerante)., Guarda resultados con TTL; tolerante a Redis caído (no-op + log)., research_cache_get(), research_cache_set(), _research_key(), _duckduckgo(), _fetch_search() (+21 more)

### Community 63 - "_FakeSyncRedis"
Cohesion: 0.18
Nodes (5): fake_events(), _FakeRedisPubSub, _FakeSyncRedis, memory_redis(), fixture

### Community 64 - "earcon.py"
Cohesion: 0.17
Nodes (14): AudioFrame, _audio_source(), _gen(), load_audio_frames(), Path, Earcon (tono previo) antes de cada interrupción proactiva por voz. El tono se…, Elige el asset configurado o el tono sintetizado de respaldo., Genera un tono sinusoidal como frames de audio PCM int16 mono. (+6 more)

### Community 65 - "test_memory_service.py"
Cohesion: 0.15
Nodes (18): Memoria persistente de conversaciones por usuario (issue #8)., _key(), load(), publish_recalled(), Devuelve el resumen persistido del usuario, o ``None``., Persiste el resumen del usuario con TTL configurable., Publica un evento ``memory_recalled`` (silent) para el panel debbuger., store() (+10 more)

### Community 66 - "redis_client.py"
Cohesion: 0.13
Nodes (22): asyncio, backend_bus, backend_decision, Capa de filtrado, triaje y enrutamiento con Sistema 1 (Jev)., Respuesta directa con el modelo económico para la ruta FAST (Tier Low)., Servicio de memoria persistente de conversaciones por usuario (issue #8). La…, backend_orchestrator, Nodos del grafo LangGraph: planificador, investigación y síntesis. Cada nodo… (+14 more)

### Community 67 - "build_spoken_update"
Cohesion: 0.24
Nodes (11): test_default_priority_is_info(), test_info_builds_message(), test_missing_message_returns_none(), test_silent_no_speech(), test_task_cancelled_is_not_spoken(), test_urgent_uses_attention_prefix(), backend_voice, build_spoken_update() (+3 more)

### Community 68 - "ADR-004: Memoria persistente de conversaciones por usuario en Redis"
Cohesion: 0.18
Nodes (10): ADR-004: Memoria persistente de conversaciones por usuario en Redis, Consequences, Context, Date, Option A: Identidad gestionada en el navegador (localStorage) + `/token?identity=`, Option B: Servicio `backend/memory/` con resumen en una clave Redis por usuario, Option C: Checkpointer LangGraph + estado completo de la conversación, Options Considered (+2 more)

### Community 69 - "summarize"
Cohesion: 0.24
Nodes (8): _deterministic(), Actualiza el resumen del usuario con LLM; fallback determinista., summarize(), test_summarize_falls_back_to_deterministic(), test_summarize_truncates_to_max_chars(), test_summarize_uses_llm_when_available(), fake_chat(), Riesgos y mitigaciones

### Community 70 - "should_play"
Cohesion: 0.29
Nodes (7): parametrize, test_should_play_defaults_to_info(), test_should_play_disabled(), test_should_play_info_urgent_when_enabled(), test_should_play_silent_never(), Dice si este evento debe sonar (flag activo + prioridad audible)., should_play()

### Community 71 - "test_notifier_flow.py"
Cohesion: 0.17
Nodes (16): FakePubSub, FakeRedis, FakeSession, _msg(), asyncio, Flujo de notificaciones de voz: filtrado por prioridad en el listener. Cubre…, Inyecta Redis fake + earcon no-op y ejecuta el listener hasta agotar., _run_listen() (+8 more)

### Community 73 - "publish_event"
Cohesion: 0.25
Nodes (17): list_tasks(), publish_event(), Deriva estado y análisis final a partir de los eventos de una tarea., Tareas en el historial, de creación más reciente a más antigua., _summarize(), _event(), json_to_dict(), test_blocked_task_is_done_with_block_message() (+9 more)

### Community 74 - "_get"
Cohesion: 0.15
Nodes (12): debug_stream(), get_token(), index(), list_tasks(), Historial de tareas pasadas: resumen por tarea, creación reciente primero., SSE: reenvía los eventos del bus de agentes al navegador., _get(), Settings (+4 more)

### Community 75 - "pytest"
Cohesion: 0.17
Nodes (9): client_with_redis(), fixture, test_get_task_detail(), test_get_task_detail_degrades_when_redis_down(), test_get_tasks_degrades_when_redis_down(), _broken_client(), test_get_tasks_lists_summary(), fakeredis (+1 more)

### Community 76 - "test_api.py"
Cohesion: 0.24
Nodes (7): backend_api, _dummy_settings(), test_debug_run_dispatches_to_celery(), test_token_endpoint(), test_token_requires_credentials(), test_token_returns_provided_identity(), fastapi_testclient

### Community 77 - "RouteAction"
Cohesion: 0.28
Nodes (19): decide(), _decision(), Aplica los guardarraíles y determina la acción de despacho. Orden de…, Acción de despacho resultante de la política de ruteo., RouteAction, parametrize, Tests de la política pura de ruteo (sin I/O)., test_dialogue_high_tier_uses_advanced_model() (+11 more)

### Community 78 - "jev.py"
Cohesion: 0.24
Nodes (11): build_questions(), classify(), _get_classifier(), _http_classify(), _lc_classify(), Any, Cliente tipado hacia Jev (Sistema 1 de TypeSafe AI). Transporte primario:…, Clasifica el ``goal`` bajo timeout duro; sin clave o sin transporte útil,… (+3 more)

### Community 80 - "Spec: Memoria persistente de conversaciones por usuario (issue #8)"
Cohesion: 0.20
Nodes (9): Configuración, Criterios de éxito, Decisión de diseño, Estructura de proyectos, Identidad y propagación, No-goals (explícitos), Preguntas abiertas, Saludo y panel (+1 more)

### Community 81 - "Spec: Jev System 1 dual-model router (`jev-router`)"
Cohesion: 0.22
Nodes (8): Boundaries, Code Style, Commands, Objective, Open Questions, Project Structure, Spec: Jev System 1 dual-model router (`jev-router`), Tech Stack

### Community 82 - "fake_redis"
Cohesion: 0.33
Nodes (3): fake_redis(), _FakeRedis, fixture

### Community 84 - "agent.py"
Cohesion: 0.40
Nodes (4): Agente de voz LiveKit que actúa como orquestador conversacional. Flujo: el…, livekit, livekit_agents, livekit_plugins

## Knowledge Gaps
- **219 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+214 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 578 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RouteAction` connect `RouteAction` to `redis_client.py`, `router.py`, `test_tools_route.py`, `test_cost_tracking.py`, `test_tasks_route.py`, `test_voice_entrypoint.py`, `schemas.py`, `run_pipeline`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `run_pipeline` to `graph.py`, `main.py`, `router.py`, `redis_client.py`, `test_cost_tracking.py`, `test_tasks_route.py`, `test_tools_route.py`, `delegate_complex_task`, `RouteAction`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `voice_entrypoint()` connect `test_voice_entrypoint.py` to `test_memory_service.py`, `graph.py`, `Spec: Memoria persistente de conversaciones por usuario (issue #8)`, `agent.py`, `_listen_for_updates`, `chat`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `RouteAction` (e.g. with `decide()` and `_decision()`) actually correct?**
  _`RouteAction` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `RouteDecision` (e.g. with `decide()` and `_publish_event()`) actually correct?**
  _`RouteDecision` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `run_pipeline()` (e.g. with `RouteAction` and `Consequences`) actually correct?**
  _`run_pipeline()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `publish_event()` (e.g. with `Contexto actual` and `Alcance`) actually correct?**
  _`publish_event()` has 2 INFERRED edges - model-reasoned connections that need verification._