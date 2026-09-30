# Graph Report - AgenteRespuesta  (2026-09-23)

## Corpus Check
- 67 files · ~38,326 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .example 1, (none) 1, .ini 1)

## Summary
- 874 nodes · 1587 edges · 64 communities (49 shown, 15 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 165 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cc306952`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- decision_log.py
- graph.py
- main.py
- agent.py
- test_decision_log.py
- due_accepted_decisions
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
- fake_redis
- renderBranding
- Plan: Jev System 1 dual-model router
- start-server.sh
- spec-document-reviewer-prompt.md
- todo.md
- test_graph.py
- review_checker.py
- ADR-003: Automatización de issues con opencode GitHub agent
- nodes.py
- _get
- test_api.py
- tasks.py
- chat
- redis_client.py
- main

## God Nodes (most connected - your core abstractions)
1. `RouteAction` - 53 edges
2. `decide()` - 24 edges
3. `RouteDecision` - 22 edges
4. `run_pipeline()` - 22 edges
5. `route()` - 21 edges
6. `TargetWorker` - 19 edges
7. `delegate_complex_task_core()` - 19 edges
8. `ComplexityTier` - 18 edges
9. `TriageAnswer` - 18 edges
10. `FakeCtx` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Option B: Triaje solo en el tool de voz `delegate_complex_task`` --references--> `delegate_complex_task()`  [INFERRED]
  decisions/ADR-001-use-jev-system-1-triage-for-dual-model-routing.md → backend/voice/tools.py
- `Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel` --references--> `ClassifyOutcome`  [INFERRED]
  docs/decisions/ADR-002-publicar-causa-de-jev-unavailable-en-routing-decision-detalle.md → backend/decision/jev.py
- `Decision` --references--> `classify()`  [INFERRED]
  docs/decisions/ADR-002-publicar-causa-de-jev-unavailable-en-routing-decision-detalle.md → backend/decision/jev.py
- `Tu tarea` --references--> `quick_answer()`  [INFERRED]
  tasks/prompts/cost-tracking.md → backend/decision/respond.py
- `Decision` --references--> `fallback_decision()`  [INFERRED]
  docs/decisions/ADR-002-publicar-causa-de-jev-unavailable-en-routing-decision-detalle.md → backend/decision/router.py

## Import Cycles
- None detected.

## Communities (64 total, 15 thin omitted)

### Community 0 - "decision_log.py"
Cohesion: 0.15
Nodes (19): main(), normalized_status(), parse_date(), parse_decision(), parse_next_review(), parse_status(), parse_supersedes_to(), parse_title() (+11 more)

### Community 1 - "graph.py"
Cohesion: 0.19
Nodes (17): build_graph(), _fan_out(), planner(), _publish(), Grafo supervisor en LangGraph. Planifica el objetivo, lanza subagentes de…, research(), ResearchState, synthesize() (+9 more)

### Community 2 - "main.py"
Cohesion: 0.17
Nodes (12): asyncio, debug_run(), BaseModel, API web: sirve la página del navegador y emite tokens JWT de LiveKit., Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz., RunGoal, fastapi, fastapi_responses (+4 more)

### Community 3 - "agent.py"
Cohesion: 0.05
Nodes (49): Agent, AgentSession, AsyncRedis, backend_bus, get_async(), test_default_priority_is_info(), test_info_builds_message(), test_missing_message_returns_none() (+41 more)

### Community 4 - "test_decision_log.py"
Cohesion: 0.09
Nodes (30): make_log(), Path, A decision with a past review date appears in due-review output., Timeline output follows a superseding chain from oldest to newest., Review cadence computation handles monthly, quarterly, and annually., Status filtering returns only decisions with the requested status family., Temporary decisions directory fixture helper., Tests for the decision-log skill CLI and helpers. (+22 more)

### Community 5 - "due_accepted_decisions"
Cohesion: 0.21
Nodes (13): adr_glob(), due_accepted_decisions(), format_due_message(), parse_decision(), parse_title(), Any, date, Path (+5 more)

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
Cohesion: 0.14
Nodes (13): Configuración, Cómo notifica (ergonomía de la investigación), Ejecución (4 terminales), Estructura, Manual (4 terminales), Modo prueba (sin voz, sin créditos OpenAI), Probar, Requisitos (Fase 0 — alta en servicios) (+5 more)

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
Cohesion: 0.06
Nodes (84): backend_decision, Capa de filtrado, triaje y enrutamiento con Sistema 1 (Jev)., build_questions(), classify(), ClassifyOutcome, _get_classifier(), _http_classify(), _lc_classify() (+76 more)

### Community 36 - "test_tools_route.py"
Cohesion: 0.09
Nodes (44): _decision(), fake_redis(), FakeCtx, _FakeRedis, patch_quick_answer(), patch_route(), _patch(), asyncio (+36 more)

### Community 37 - "test_cost_tracking.py"
Cohesion: 0.07
Nodes (40): CostTracker, current(), estimate_cost_eur(), _model_slug(), ModelUsage, publish_cost_ready(), Recolección ligera de tokens y coste estimado por tarea. Un ``CostTracker`` por…, Callback de LangChain que registra el uso de tokens en el tracker activo.… (+32 more)

### Community 38 - "run_pipeline"
Cohesion: 0.08
Nodes (28): run_pipeline(), ainvoke(), _decision(), fake_redis(), _FakeRedis, patch_quick_answer(), _patch(), patch_route() (+20 more)

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
Cohesion: 0.17
Nodes (11): ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle), Consequences, Context, Date, Decision, Option A: Log en servidor, sin tocar el payload del evento, Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel, Option C: Endpoint de diagnóstico dedicado (+3 more)

### Community 45 - "helper.js"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 46 - "handleUpgrade"
Cohesion: 0.25
Nodes (8): broadcast(), computeAcceptKey(), decodeFrame(), encodeFrame(), handleMessage(), handleUpgrade(), isAllowedWebSocketOrigin(), touchActivity()

### Community 47 - "stop-server.sh"
Cohesion: 0.52
Nodes (6): command_has_server_id(), command_line_for_pid(), is_brainstorm_server(), mark_stopped(), read_expected_server_id(), stop-server.sh script

### Community 48 - "fake_redis"
Cohesion: 0.33
Nodes (3): fake_redis(), _FakeRedis, fixture

### Community 49 - "renderBranding"
Cohesion: 0.40
Nodes (5): brandMarkup(), escapeHtmlText(), renderBranding(), waitingPage(), wrapInFrame()

### Community 50 - "Plan: Jev System 1 dual-model router"
Cohesion: 0.50
Nodes (3): Plan: Jev System 1 dual-model router, Riesgos y mitigaciones, Verificación por capa

### Community 54 - "test_graph.py"
Cohesion: 0.15
Nodes (9): _async_list(), _async_str(), fake_redis(), _FakeRedis, asyncio, fixture, stub_nodes(), test_pipeline_publishes_and_synthesizes() (+1 more)

### Community 55 - "review_checker.py"
Cohesion: 0.16
Nodes (14): parse_next_review(), parse_status(), Cron-compatible review reminder for ADR decision logs., Return the body text immediately following a Markdown level-2 heading., Parse the status value from an ADR document., Parse the next review date from the Review section., section_after_heading(), argparse (+6 more)

### Community 56 - "ADR-003: Automatización de issues con opencode GitHub agent"
Cohesion: 0.15
Nodes (12): ADR-003: Automatización de issues con opencode GitHub agent, Consequences, Context, Date, Decision, Option A: GitHub Copilot coding agent (`@copilot`), Option B: Claude Code Action (`anthropics/claude-code-action`), Option C: opencode en CI con `anomalyco/opencode/github@latest` (+4 more)

### Community 57 - "nodes.py"
Cohesion: 0.20
Nodes (10): _build_llm(), _duckduckgo(), _parse_subtasks(), plan_subtasks(), Any, Nodos del grafo LangGraph: planificador, investigación y síntesis. Cada nodo…, Búsqueda web con Tavily si hay clave; si no, DuckDuckGo., run_search() (+2 more)

### Community 58 - "_get"
Cohesion: 0.22
Nodes (8): debug_stream(), get_token(), index(), SSE: reenvía los eventos del bus de agentes al navegador., _get(), Settings, FileResponse, StreamingResponse

### Community 59 - "test_api.py"
Cohesion: 0.24
Nodes (6): backend_api, _dummy_settings(), test_debug_run_dispatches_to_celery(), test_token_endpoint(), test_token_requires_credentials(), fastapi_testclient

### Community 60 - "tasks.py"
Cohesion: 0.27
Nodes (8): Respuesta directa con el modelo económico para la ruta FAST (Tier Low)., backend_orchestrator, _handle_blocked(), _handle_fast(), _inner(), _publish(), Tareas Celery: ejecución duradera del pipeline multiagente. El worker ejecuta…, celery

### Community 61 - "chat"
Cohesion: 0.24
Nodes (9): quick_answer(), Devuelve la respuesta del modelo económico a una tarea de complejidad baja., chat(), Envía un mensaje a un LLM genérico; si no hay clave o falla, devuelve vacío., Alcance, Criterios de éxito, Proceso obligatorio, Prompt de delegación — Seguimiento de coste (tokens/€) por tarea (+1 more)

### Community 62 - "redis_client.py"
Cohesion: 0.22
Nodes (8): get_sync(), publish_event(), Any, json, redis, redis_asyncio, SyncRedis, typing

### Community 63 - "main"
Cohesion: 0.29
Nodes (7): build_parser(), main(), ArgumentParser, Run the review checker and always exit successfully., Return the decisions directory from an argument, environment, or default., Build and return the command-line parser., resolve_decisions_dir()

## Knowledge Gaps
- **188 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+183 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 444 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RouteAction` connect `RouteAction` to `tasks.py`, `test_cost_tracking.py`, `run_pipeline`, `test_tools_route.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `run_pipeline` to `graph.py`, `main.py`, `agent.py`, `RouteAction`, `tasks.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `RouteDecision` connect `RouteAction` to `test_tools_route.py`, `test_cost_tracking.py`, `run_pipeline`, `ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `RouteAction` (e.g. with `decide()` and `_decision()`) actually correct?**
  _`RouteAction` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `decide()` (e.g. with `ComplexityTier` and `RouteAction`) actually correct?**
  _`decide()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `RouteDecision` (e.g. with `decide()` and `_publish_event()`) actually correct?**
  _`RouteDecision` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `run_pipeline()` (e.g. with `RouteAction` and `Consequences`) actually correct?**
  _`run_pipeline()` has 9 INFERRED edges - model-reasoned connections that need verification._