# Graph Report - AgenteRespuesta  (2026-09-25)

## Corpus Check
- 79 files · ~46,782 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .example 1, (none) 1, .ini 1)

## Summary
- 1100 nodes · 2036 edges · 73 communities (58 shown, 15 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 225 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a600b6a8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- decision_log.py
- graph.py
- config.py
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
- RouteAction
- test_tools_route.py
- test_cost_tracking.py
- run_pipeline
- server.cjs
- Visual Companion Guide
- startServer
- handleRequest
- Brainstorming Ideas Into Designs
- ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)
- helper.js
- handleUpgrade
- stop-server.sh
- agent.py
- renderBranding
- publish_recalled
- start-server.sh
- spec-document-reviewer-prompt.md
- mem_get
- test_graph.py
- Definición de Hecho (DoD)
- ADR-003: Automatización de issues con opencode GitHub agent
- nodes.py
- test_earcon.py
- Spec: Memoria persistente de conversaciones por usuario (issue #8)
- _listen_for_updates
- chat
- redis_client.py
- test_memory_service.py
- earcon.py
- service.py
- run_search
- build_spoken_update
- ADR-004: Memoria persistente de conversaciones por usuario en Redis
- summarize
- should_play
- _FakeSyncRedis
- FakePubSub

## God Nodes (most connected - your core abstractions)
1. `RouteAction` - 55 edges
2. `run_pipeline()` - 24 edges
3. `decide()` - 23 edges
4. `RouteDecision` - 21 edges
5. `route()` - 20 edges
6. `delegate_complex_task_core()` - 20 edges
7. `TargetWorker` - 19 edges
8. `ComplexityTier` - 18 edges
9. `TriageAnswer` - 18 edges
10. `FakeCtx` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Riesgos y mitigaciones` --references--> `mem_get()`  [INFERRED]
  tasks/plan.md → backend/bus/redis_client.py
- `Riesgos y mitigaciones` --references--> `mem_set()`  [INFERRED]
  tasks/plan.md → backend/bus/redis_client.py
- `Tu tarea` --references--> `quick_answer()`  [INFERRED]
  tasks/prompts/cost-tracking.md → backend/decision/respond.py
- `Success Criteria` --references--> `route()`  [INFERRED]
  SPEC-jev-router.md → backend/decision/router.py
- `Decision` --references--> `load()`  [INFERRED]
  docs/decisions/ADR-004-memoria-persistente-de-conversaciones-por-usuario-en-redis.md → backend/memory/service.py

## Import Cycles
- None detected.

## Communities (73 total, 15 thin omitted)

### Community 0 - "decision_log.py"
Cohesion: 0.15
Nodes (19): main(), normalized_status(), parse_date(), parse_decision(), parse_next_review(), parse_status(), parse_supersedes_to(), parse_title() (+11 more)

### Community 1 - "graph.py"
Cohesion: 0.14
Nodes (19): backend_memory, _load_memory(), planner(), _publish(), Grafo supervisor en LangGraph. Planifica el objetivo, lanza subagentes de…, research(), _store_memory(), synthesize() (+11 more)

### Community 2 - "config.py"
Cohesion: 0.07
Nodes (31): backend_api, debug_run(), debug_stream(), get_token(), index(), BaseModel, API web: sirve la página del navegador y emite tokens JWT de LiveKit., Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz. (+23 more)

### Community 3 - "delegate_complex_task"
Cohesion: 0.09
Nodes (26): Agent, OrchestratorAgent, cancel_task(), confirm_execution(), delegate_complex_task(), Delega un objetivo complejo a un equipo de subagentes que trabajan en segundo…, Confirma o cancela una acción de alto riesgo pendiente de aprobación. Args:…, Cancela la tarea en curso que los subagentes están ejecutando en segundo plano.… (+18 more)

### Community 4 - "test_decision_log.py"
Cohesion: 0.08
Nodes (31): make_log(), Path, A decision with a past review date appears in due-review output., Timeline output follows a superseding chain from oldest to newest., Review cadence computation handles monthly, quarterly, and annually., Status filtering returns only decisions with the requested status family., Temporary decisions directory fixture helper., Tests for the decision-log skill CLI and helpers. (+23 more)

### Community 5 - "review_checker.py"
Cohesion: 0.09
Nodes (32): adr_glob(), build_parser(), due_accepted_decisions(), format_due_message(), main(), parse_decision(), parse_next_review(), parse_status() (+24 more)

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

### Community 35 - "RouteAction"
Cohesion: 0.05
Nodes (88): backend_decision, Capa de filtrado, triaje y enrutamiento con Sistema 1 (Jev)., build_questions(), classify(), ClassifyOutcome, _get_classifier(), _http_classify(), _lc_classify() (+80 more)

### Community 36 - "test_tools_route.py"
Cohesion: 0.11
Nodes (40): _decision(), fake_redis(), FakeCtx, _FakeRedis, patch_quick_answer(), patch_route(), _patch(), asyncio (+32 more)

### Community 37 - "test_cost_tracking.py"
Cohesion: 0.06
Nodes (45): CostTracker, current(), estimate_cost_eur(), _model_slug(), ModelUsage, publish_cost_ready(), Recolección ligera de tokens y coste estimado por tarea. Un ``CostTracker`` por…, Callback de LangChain que registra el uso de tokens en el tracker activo.… (+37 more)

### Community 38 - "run_pipeline"
Cohesion: 0.07
Nodes (36): asyncio, Respuesta directa con el modelo económico para la ruta FAST (Tier Low)., backend_orchestrator, _handle_blocked(), _handle_fast(), _inner(), _publish(), Tareas Celery: ejecución duradera del pipeline multiagente. El worker ejecuta… (+28 more)

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
Cohesion: 0.20
Nodes (9): ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle), Consequences, Context, Date, Option A: Log en servidor, sin tocar el payload del evento, Option C: Endpoint de diagnóstico dedicado, Options Considered, Review (+1 more)

### Community 45 - "helper.js"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 46 - "handleUpgrade"
Cohesion: 0.25
Nodes (8): broadcast(), computeAcceptKey(), decodeFrame(), encodeFrame(), handleMessage(), handleUpgrade(), isAllowedWebSocketOrigin(), touchActivity()

### Community 47 - "stop-server.sh"
Cohesion: 0.52
Nodes (6): command_has_server_id(), command_line_for_pid(), is_brainstorm_server(), mark_stopped(), read_expected_server_id(), stop-server.sh script

### Community 48 - "agent.py"
Cohesion: 0.11
Nodes (24): _fake_ctx(), _FakeParticipant, Tests de la capa de voz con memoria: bienvenida y resolución de identidad., test_build_welcome_mentions_previous_work(), test_build_welcome_without_memory_uses_base_instructions(), test_resolve_user_id_defaults_to_anonymous(), test_resolve_user_id_falls_back_to_token_claims(), test_resolve_user_id_prefers_human_participant() (+16 more)

### Community 49 - "renderBranding"
Cohesion: 0.40
Nodes (5): brandMarkup(), escapeHtmlText(), renderBranding(), waitingPage(), wrapInFrame()

### Community 50 - "publish_recalled"
Cohesion: 0.17
Nodes (11): publish_recalled(), Publica un evento ``memory_recalled`` (silent) para el panel debbuger., test_publish_recalled_disabled_is_noop(), test_publish_recalled_publishes_silent_event(), test_dispatch_passes_task_id_to_celery(), _dispatch_orchestrator(), Testing, Orden de implementación (dependencias) (+3 more)

### Community 53 - "mem_get"
Cohesion: 0.28
Nodes (8): get_sync(), mem_get(), mem_set(), Lee un valor con TTL; tolerante a Redis caído (None + log)., Escribe un valor con TTL; tolerante a Redis caído (no-op + log)., test_mem_helpers_roundtrip_with_ttl(), SyncRedis, Todo — conversation-memory (issue #8)

### Community 54 - "test_graph.py"
Cohesion: 0.12
Nodes (17): build_graph(), _run_graph(), _inner(), _async_list(), _async_str(), fake_redis(), _FakeRedis, asyncio (+9 more)

### Community 55 - "Definición de Hecho (DoD)"
Cohesion: 0.33
Nodes (5): Criterios, Cómo funciona la revisión automática (resumen), Definición de Hecho (DoD), Evidencia estructurada (punto 4), Referencias

### Community 56 - "ADR-003: Automatización de issues con opencode GitHub agent"
Cohesion: 0.08
Nodes (24): ADR-003: Automatización de issues con opencode GitHub agent, Consequences, Context, Date, Decision, Option A: GitHub Copilot coding agent (`@copilot`), Option B: Claude Code Action (`anthropics/claude-code-action`), Option C: opencode en CI con `anomalyco/opencode/github@latest` (+16 more)

### Community 57 - "nodes.py"
Cohesion: 0.28
Nodes (7): _duckduckgo(), _fetch_search(), _parse_subtasks(), plan_subtasks(), Nodos del grafo LangGraph: planificador, investigación y síntesis. Cada nodo…, hashlib, httpx

### Community 58 - "test_earcon.py"
Cohesion: 0.18
Nodes (15): disable_earcon(), enable_earcon(), FakeHandle, FakeSession, asyncio, fixture, Tests del earcon (tono previo) antes de interrupciones proactivas. La política…, test_play_earcon_disabled_never_sounds() (+7 more)

### Community 59 - "Spec: Memoria persistente de conversaciones por usuario (issue #8)"
Cohesion: 0.12
Nodes (16): publish_event(), Any, _fan_out(), ResearchState, _publish_task_cancelled(), Configuración, Contexto actual, Criterios de éxito (+8 more)

### Community 60 - "_listen_for_updates"
Cohesion: 0.17
Nodes (9): AgentSession, FakeRedis, FakeVoiceSession, test_listen_disabled_no_earcon_but_replies(), test_listen_plays_earcon_before_reply_for_info(), test_listen_silent_no_earcon_no_reply(), spy_play(), _listen_for_updates() (+1 more)

### Community 61 - "chat"
Cohesion: 0.18
Nodes (12): quick_answer(), Devuelve la respuesta del modelo económico a una tarea de complejidad baja., _build_llm(), chat(), Any, Envía un mensaje a un LLM genérico; si no hay clave o falla, devuelve vacío., Contrato de `backend/memory/`, Alcance (+4 more)

### Community 62 - "redis_client.py"
Cohesion: 0.16
Nodes (16): AsyncRedis, backend_bus, get_async(), Lee resultados cacheados; None en miss o Redis caído (tolerante)., Guarda resultados con TTL; tolerante a Redis caído (no-op + log)., research_cache_get(), research_cache_set(), _research_key() (+8 more)

### Community 63 - "test_memory_service.py"
Cohesion: 0.16
Nodes (8): fake_events(), _FakeRedisPubSub, _FakeSyncRedis, memory_redis(), fixture, Tests del servicio de memoria persistente (issue #8)., test_load_tolerates_redis_error(), test_store_and_load_disabled_are_noops()

### Community 64 - "earcon.py"
Cohesion: 0.17
Nodes (14): AudioFrame, _audio_source(), _gen(), load_audio_frames(), Path, Earcon (tono previo) antes de cada interrupción proactiva por voz. El tono se…, Elige el asset configurado o el tono sintetizado de respaldo., Genera un tono sinusoidal como frames de audio PCM int16 mono. (+6 more)

### Community 65 - "service.py"
Cohesion: 0.21
Nodes (12): Memoria persistente de conversaciones por usuario (issue #8)., _key(), load(), Servicio de memoria persistente de conversaciones por usuario (issue #8). La…, Devuelve el resumen persistido del usuario, o ``None``., Persiste el resumen del usuario con TTL configurable., store(), _ttl_seconds() (+4 more)

### Community 66 - "run_search"
Cohesion: 0.22
Nodes (10): Búsqueda web con Tavily si hay clave; si no, DuckDuckGo. Usa caché Redis por…, Hash SHA-256 de la query normalizada (lowercase + strip)., _research_hash(), run_search(), asyncio, test_research_hash_normalizes(), test_run_search_degrades_when_redis_down(), test_run_search_miss_calls_provider_and_stores() (+2 more)

### Community 67 - "build_spoken_update"
Cohesion: 0.27
Nodes (10): test_default_priority_is_info(), test_info_builds_message(), test_missing_message_returns_none(), test_silent_no_speech(), test_task_cancelled_is_not_spoken(), test_urgent_uses_attention_prefix(), build_spoken_update(), classify() (+2 more)

### Community 68 - "ADR-004: Memoria persistente de conversaciones por usuario en Redis"
Cohesion: 0.18
Nodes (10): ADR-004: Memoria persistente de conversaciones por usuario en Redis, Consequences, Context, Date, Option A: Identidad gestionada en el navegador (localStorage) + `/token?identity=`, Option B: Servicio `backend/memory/` con resumen en una clave Redis por usuario, Option C: Checkpointer LangGraph + estado completo de la conversación, Options Considered (+2 more)

### Community 69 - "summarize"
Cohesion: 0.24
Nodes (8): _deterministic(), Actualiza el resumen del usuario con LLM; fallback determinista., summarize(), test_summarize_falls_back_to_deterministic(), test_summarize_truncates_to_max_chars(), test_summarize_uses_llm_when_available(), fake_chat(), Riesgos y mitigaciones

### Community 70 - "should_play"
Cohesion: 0.29
Nodes (7): parametrize, test_should_play_defaults_to_info(), test_should_play_disabled(), test_should_play_info_urgent_when_enabled(), test_should_play_silent_never(), Dice si este evento debe sonar (flag activo + prioridad audible)., should_play()

### Community 71 - "_FakeSyncRedis"
Cohesion: 0.33
Nodes (3): cache_redis(), _FakeSyncRedis, fixture

## Knowledge Gaps
- **216 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+211 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 537 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RouteAction` connect `RouteAction` to `test_tools_route.py`, `test_cost_tracking.py`, `run_pipeline`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `run_pipeline` to `graph.py`, `config.py`, `RouteAction`, `delegate_complex_task`, `test_cost_tracking.py`, `publish_recalled`, `test_graph.py`, `Spec: Memoria persistente de conversaciones por usuario (issue #8)`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `RouteAction` (e.g. with `decide()` and `_decision()`) actually correct?**
  _`RouteAction` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `run_pipeline()` (e.g. with `RouteAction` and `Consequences`) actually correct?**
  _`run_pipeline()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `decide()` (e.g. with `ComplexityTier` and `RouteAction`) actually correct?**
  _`decide()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RouteDecision` (e.g. with `decide()` and `_publish_event()`) actually correct?**
  _`RouteDecision` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `route()` (e.g. with `RouteDecision` and `RoutingConfig`) actually correct?**
  _`route()` has 5 INFERRED edges - model-reasoned connections that need verification._