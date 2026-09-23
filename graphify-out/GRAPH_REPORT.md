# Graph Report - AgenteRespuesta  (2026-09-23)

## Corpus Check
- 74 files · ~42,343 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .example 1, (none) 1, .ini 1)

## Summary
- 986 nodes · 1829 edges · 68 communities (54 shown, 14 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 215 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a8b49457`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- decision_log.py
- graph.py
- config.py
- build_spoken_update
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
- test_memory_voice.py
- renderBranding
- publish_recalled
- start-server.sh
- spec-document-reviewer-prompt.md
- mem_get
- test_graph.py
- delegate_complex_task
- ADR-003: Automatización de issues con opencode GitHub agent
- nodes.py
- ADR-004: Memoria persistente de conversaciones por usuario en Redis
- summarize
- Spec: Jev System 1 dual-model router (`jev-router`)
- quick_answer
- test_memory_service.py
- Spec: Memoria persistente de conversaciones por usuario (issue #8)
- voice_entrypoint
- fake_events
- agent.py
- Prompt de delegación — Cancelación por voz de la tarea en curso

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
- `Option B: Triaje solo en el tool de voz `delegate_complex_task`` --references--> `delegate_complex_task()`  [INFERRED]
  decisions/ADR-001-use-jev-system-1-triage-for-dual-model-routing.md → backend/voice/tools.py
- `Contexto actual` --references--> `publish_event()`  [INFERRED]
  docs/superpowers/specs/2026-09-23-conversation-memory-design.md → backend/bus/redis_client.py
- `Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel` --references--> `ClassifyOutcome`  [INFERRED]
  docs/decisions/ADR-002-publicar-causa-de-jev-unavailable-en-routing-decision-detalle.md → backend/decision/jev.py
- `Tu tarea` --references--> `quick_answer()`  [INFERRED]
  tasks/prompts/cost-tracking.md → backend/decision/respond.py
- `Success Criteria` --references--> `route()`  [INFERRED]
  SPEC-jev-router.md → backend/decision/router.py

## Import Cycles
- None detected.

## Communities (68 total, 14 thin omitted)

### Community 0 - "decision_log.py"
Cohesion: 0.15
Nodes (19): main(), normalized_status(), parse_date(), parse_decision(), parse_next_review(), parse_status(), parse_supersedes_to(), parse_title() (+11 more)

### Community 1 - "graph.py"
Cohesion: 0.14
Nodes (24): build_graph(), _fan_out(), _load_memory(), planner(), _publish(), Grafo supervisor en LangGraph. Planifica el objetivo, lanza subagentes de…, research(), ResearchState (+16 more)

### Community 2 - "config.py"
Cohesion: 0.07
Nodes (31): backend_api, debug_run(), debug_stream(), get_token(), index(), BaseModel, API web: sirve la página del navegador y emite tokens JWT de LiveKit., Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz. (+23 more)

### Community 3 - "build_spoken_update"
Cohesion: 0.24
Nodes (11): test_default_priority_is_info(), test_info_builds_message(), test_missing_message_returns_none(), test_silent_no_speech(), test_task_cancelled_is_not_spoken(), test_urgent_uses_attention_prefix(), backend_voice, build_spoken_update() (+3 more)

### Community 4 - "test_decision_log.py"
Cohesion: 0.09
Nodes (30): make_log(), Path, A decision with a past review date appears in due-review output., Timeline output follows a superseding chain from oldest to newest., Review cadence computation handles monthly, quarterly, and annually., Status filtering returns only decisions with the requested status family., Temporary decisions directory fixture helper., Tests for the decision-log skill CLI and helpers. (+22 more)

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

### Community 35 - "RouteAction"
Cohesion: 0.05
Nodes (83): backend_decision, Capa de filtrado, triaje y enrutamiento con Sistema 1 (Jev)., build_questions(), classify(), ClassifyOutcome, _get_classifier(), _http_classify(), _lc_classify() (+75 more)

### Community 36 - "test_tools_route.py"
Cohesion: 0.09
Nodes (44): _decision(), fake_redis(), FakeCtx, _FakeRedis, patch_quick_answer(), patch_route(), _patch(), asyncio (+36 more)

### Community 37 - "test_cost_tracking.py"
Cohesion: 0.07
Nodes (41): CostTracker, current(), estimate_cost_eur(), _model_slug(), ModelUsage, publish_cost_ready(), Recolección ligera de tokens y coste estimado por tarea. Un ``CostTracker`` por…, Callback de LangChain que registra el uso de tokens en el tracker activo.… (+33 more)

### Community 38 - "run_pipeline"
Cohesion: 0.06
Nodes (44): asyncio, Respuesta directa con el modelo económico para la ruta FAST (Tier Low)., BaseModel, Decisión de ruteo: acción, modelo y contexto para observabilidad., RouteDecision, backend_orchestrator, _handle_blocked(), _handle_fast() (+36 more)

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

### Community 48 - "test_memory_voice.py"
Cohesion: 0.18
Nodes (14): _fake_ctx(), _FakeParticipant, Tests de la capa de voz con memoria: bienvenida y resolución de identidad., test_build_welcome_mentions_previous_work(), test_build_welcome_without_memory_uses_base_instructions(), test_resolve_user_id_defaults_to_anonymous(), test_resolve_user_id_falls_back_to_token_claims(), test_resolve_user_id_prefers_human_participant() (+6 more)

### Community 49 - "renderBranding"
Cohesion: 0.40
Nodes (5): brandMarkup(), escapeHtmlText(), renderBranding(), waitingPage(), wrapInFrame()

### Community 50 - "publish_recalled"
Cohesion: 0.17
Nodes (11): publish_event(), Any, publish_recalled(), Publica un evento ``memory_recalled`` (silent) para el panel debbuger., test_publish_recalled_disabled_is_noop(), test_publish_recalled_publishes_silent_event(), _publish_task_cancelled(), Decision (+3 more)

### Community 53 - "mem_get"
Cohesion: 0.27
Nodes (9): get_sync(), mem_get(), mem_set(), Lee un valor con TTL; tolerante a Redis caído (None + log)., Escribe un valor con TTL; tolerante a Redis caído (no-op + log)., test_mem_helpers_roundtrip_with_ttl(), SyncRedis, Riesgos y mitigaciones (+1 more)

### Community 54 - "test_graph.py"
Cohesion: 0.12
Nodes (14): _async_list(), _async_str(), fake_redis(), _FakeRedis, asyncio, fixture, stub_nodes(), fake_chat() (+6 more)

### Community 55 - "delegate_complex_task"
Cohesion: 0.23
Nodes (13): Agent, OrchestratorAgent, cancel_task(), confirm_execution(), delegate_complex_task(), Delega un objetivo complejo a un equipo de subagentes que trabajan en segundo…, Confirma o cancela una acción de alto riesgo pendiente de aprobación. Args:…, Cancela la tarea en curso que los subagentes están ejecutando en segundo plano.… (+5 more)

### Community 56 - "ADR-003: Automatización de issues con opencode GitHub agent"
Cohesion: 0.15
Nodes (12): ADR-003: Automatización de issues con opencode GitHub agent, Consequences, Context, Date, Decision, Option A: GitHub Copilot coding agent (`@copilot`), Option B: Claude Code Action (`anthropics/claude-code-action`), Option C: opencode en CI con `anomalyco/opencode/github@latest` (+4 more)

### Community 57 - "nodes.py"
Cohesion: 0.19
Nodes (12): _build_llm(), chat(), _duckduckgo(), _parse_subtasks(), plan_subtasks(), Any, Nodos del grafo LangGraph: planificador, investigación y síntesis. Cada nodo…, Envía un mensaje a un LLM genérico; si no hay clave o falla, devuelve vacío. (+4 more)

### Community 58 - "ADR-004: Memoria persistente de conversaciones por usuario en Redis"
Cohesion: 0.18
Nodes (10): ADR-004: Memoria persistente de conversaciones por usuario en Redis, Consequences, Context, Date, Option A: Identidad gestionada en el navegador (localStorage) + `/token?identity=`, Option B: Servicio `backend/memory/` con resumen en una clave Redis por usuario, Option C: Checkpointer LangGraph + estado completo de la conversación, Options Considered (+2 more)

### Community 59 - "summarize"
Cohesion: 0.24
Nodes (8): _deterministic(), Actualiza el resumen del usuario con LLM; fallback determinista., summarize(), test_summarize_falls_back_to_deterministic(), test_summarize_truncates_to_max_chars(), test_summarize_uses_llm_when_available(), fake_chat(), Riesgos y mitigaciones

### Community 60 - "Spec: Jev System 1 dual-model router (`jev-router`)"
Cohesion: 0.20
Nodes (9): Boundaries, Code Style, Commands, Objective, Open Questions, Project Structure, Spec: Jev System 1 dual-model router (`jev-router`), Success Criteria (+1 more)

### Community 61 - "quick_answer"
Cohesion: 0.29
Nodes (7): quick_answer(), Devuelve la respuesta del modelo económico a una tarea de complejidad baja., Alcance, Criterios de éxito, Proceso obligatorio, Prompt de delegación — Seguimiento de coste (tokens/€) por tarea, Tu tarea

### Community 62 - "test_memory_service.py"
Cohesion: 0.11
Nodes (20): AsyncRedis, backend_bus, get_async(), Memoria persistente de conversaciones por usuario (issue #8)., _key(), load(), Servicio de memoria persistente de conversaciones por usuario (issue #8). La…, Devuelve el resumen persistido del usuario, o ``None``. (+12 more)

### Community 63 - "Spec: Memoria persistente de conversaciones por usuario (issue #8)"
Cohesion: 0.22
Nodes (8): Configuración, Criterios de éxito, Decisión de diseño, Estructura de proyectos, No-goals (explícitos), Orquestador (grafo), Preguntas abiertas, Spec: Memoria persistente de conversaciones por usuario (issue #8)

### Community 64 - "voice_entrypoint"
Cohesion: 0.25
Nodes (8): AgentSession, _listen_for_updates(), Escucha eventos de los subagentes y habla proactivamente., voice_entrypoint(), Identidad y propagación, Saludo y panel, JobContext, rtc_session

### Community 65 - "fake_events"
Cohesion: 0.29
Nodes (4): fake_events(), _FakeRedisPubSub, memory_redis(), fixture

### Community 66 - "agent.py"
Cohesion: 0.33
Nodes (5): backend_memory, Agente de voz LiveKit que actúa como orquestador conversacional. Flujo: el…, livekit, livekit_agents, livekit_plugins

### Community 67 - "Prompt de delegación — Cancelación por voz de la tarea en curso"
Cohesion: 0.40
Nodes (4): Alcance, Criterios de éxito, Proceso obligatorio, Prompt de delegación — Cancelación por voz de la tarea en curso

## Knowledge Gaps
- **203 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+198 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 487 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RouteAction` connect `RouteAction` to `test_tools_route.py`, `test_cost_tracking.py`, `run_pipeline`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `run_pipeline` to `graph.py`, `config.py`, `RouteAction`, `test_tools_route.py`, `delegate_complex_task`, `Spec: Jev System 1 dual-model router (`jev-router`)`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `RouteDecision` connect `run_pipeline` to `RouteAction`, `test_tools_route.py`, `test_cost_tracking.py`, `ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `RouteAction` (e.g. with `decide()` and `_decision()`) actually correct?**
  _`RouteAction` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `run_pipeline()` (e.g. with `RouteAction` and `Consequences`) actually correct?**
  _`run_pipeline()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `decide()` (e.g. with `ComplexityTier` and `RouteAction`) actually correct?**
  _`decide()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RouteDecision` (e.g. with `decide()` and `_publish_event()`) actually correct?**
  _`RouteDecision` has 7 INFERRED edges - model-reasoned connections that need verification._