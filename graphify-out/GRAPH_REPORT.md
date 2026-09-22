# Graph Report - AgenteRespuesta  (2026-09-22)

## Corpus Check
- 38 files · ~16,216 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .example 1, (none) 1, .ini 1)

## Summary
- 416 nodes · 599 edges · 30 communities (18 shown, 12 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d728c176`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- decision_log.py
- graph.py
- main.py
- agent.py
- test_decision_log.py
- review_checker.py
- Decision Log
- Bitácora de Avances y Retrospectivas (project-log)
- Spec-Driven Development
- Respuesta — Agente de voz con subagentes proactivos
- ADR Format Guide
- Review Cadence Rules
- ADR-NNN: Decision Title
- stub_nodes
- compute_next_review
- Agent Skills (OpenCode)
- Summarize Meeting
- graphify.js
- opencode.json

## God Nodes (most connected - your core abstractions)
1. `Decision Log` - 16 edges
2. `parse_decision()` - 13 edges
3. `ADR Format Guide` - 11 edges
4. `Respuesta — Agente de voz con subagentes proactivos` - 11 edges
5. `resolve_decisions_dir()` - 10 edges
6. `load_decisions()` - 10 edges
7. `build_parser()` - 10 edges
8. `build_graph()` - 10 edges
9. `create_decision()` - 9 edges
10. `command_timeline()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `get_token()` --references--> `_get()`  [EXTRACTED]
  backend/api/main.py → backend/config.py
- `test_silent_no_speech()` --calls--> `build_spoken_update()`  [EXTRACTED]
  backend/tests/test_notifier.py → backend/voice/notifier.py
- `test_info_builds_message()` --calls--> `build_spoken_update()`  [EXTRACTED]
  backend/tests/test_notifier.py → backend/voice/notifier.py
- `test_urgent_uses_attention_prefix()` --calls--> `build_spoken_update()`  [EXTRACTED]
  backend/tests/test_notifier.py → backend/voice/notifier.py
- `test_missing_message_returns_none()` --calls--> `build_spoken_update()`  [EXTRACTED]
  backend/tests/test_notifier.py → backend/voice/notifier.py

## Import Cycles
- None detected.

## Communities (30 total, 12 thin omitted)

### Community 0 - "decision_log.py"
Cohesion: 0.05
Nodes (76): add_supersede_link(), adr_glob(), build_parser(), build_timeline_chains(), command_due_review(), command_list(), command_new(), command_search() (+68 more)

### Community 1 - "graph.py"
Cohesion: 0.06
Nodes (46): asyncio, get_sync(), publish_event(), Any, backend_orchestrator, build_graph(), _fan_out(), planner() (+38 more)

### Community 2 - "main.py"
Cohesion: 0.07
Nodes (29): backend_api, debug_run(), debug_stream(), get_token(), index(), API web: sirve la página del navegador y emite tokens JWT de LiveKit., Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz., SSE: reenvía los eventos del bus de agentes al navegador. (+21 more)

### Community 3 - "agent.py"
Cohesion: 0.08
Nodes (31): Agent, AgentSession, AsyncRedis, backend_bus, get_async(), test_default_priority_is_info(), test_info_builds_message(), test_missing_message_returns_none() (+23 more)

### Community 4 - "test_decision_log.py"
Cohesion: 0.09
Nodes (29): make_log(), Path, A decision with a past review date appears in due-review output., Timeline output follows a superseding chain from oldest to newest., Review cadence computation handles monthly, quarterly, and annually., Status filtering returns only decisions with the requested status family., Temporary decisions directory fixture helper., Tests for the decision-log skill CLI and helpers. (+21 more)

### Community 5 - "review_checker.py"
Cohesion: 0.10
Nodes (30): adr_glob(), build_parser(), due_accepted_decisions(), format_due_message(), main(), parse_decision(), parse_next_review(), parse_status() (+22 more)

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

### Community 13 - "stub_nodes"
Cohesion: 0.20
Nodes (4): fake_redis(), _FakeRedis, stub_nodes(), fixture

### Community 14 - "compute_next_review"
Cohesion: 0.28
Nodes (9): add_months(), compute_next_review(), is_leap_year(), date, Return True when a year is a Gregorian leap year., Compute the next review date for a cadence, or blank for on-trigger., Render a new ADR Markdown document from the embedded template., Add calendar months to a date, clamping the day at month end. (+1 more)

### Community 15 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 16 - "Summarize Meeting"
Cohesion: 0.33
Nodes (5): Context, Instructions, Notes, Purpose, Summarize Meeting

### Community 17 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

## Knowledge Gaps
- **90 isolated node(s):** `$schema`, `plugins`, `Overview`, `Quick start`, `When to create an ADR` (+85 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 246 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `$schema`, `plugins`, `Overview` to the rest of the system?**
  _90 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `decision_log.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052289815447710185 - nodes in this community are weakly interconnected._
- **Should `graph.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06458635703918723 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07057057057057058 - nodes in this community are weakly interconnected._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0761904761904762 - nodes in this community are weakly interconnected._
- **Should `test_decision_log.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0907258064516129 - nodes in this community are weakly interconnected._
- **Should `review_checker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1010752688172043 - nodes in this community are weakly interconnected._