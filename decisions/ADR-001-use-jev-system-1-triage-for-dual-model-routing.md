# ADR-001: Use Jev System 1 triage for dual-model routing

## Status
accepted

## Date
2026-09-23

## Context
El sistema de voz (LiveKit + OpenAI Realtime) delega toda tarea al orquestador LangGraph/Celery (planner -> research -> synthesize), incluso las triviales. Esto descarrila el presupuesto de latencia acústica (<500-800 ms) y quema cómputo de `gpt-4o-mini`/`gpt-4o` en tareas que no lo requieren. Tampoco existe un filtro de inyección de instrucciones ni una diferenciación coste/latencia entre tareas de un paso y tareas analíticas multi-paso.

Jev (TypeSafe AI, `POST https://api.typesafe.ai/v1/systemone`, paquete `langchain-typesafe`) es un modelo Sistema 1: lee estado natural y devuelve decisiones tipadas calibradas (Choice/Score/Noul) en 70-500 ms, sin generar texto libre y con todas las preguntas evaluadas en paralelo contra un mismo `state`.

## Options Considered

### Option A: Triaje solo en la entrada del orquestador (Celery `run_pipeline`)
- Pros: sin tocar el plano de audio; migración simple.
- Cons: la tarea ya viajó por el tool de voz y el LLM realtime; no ayuda a la latencia acústica, y el orquestador sigue siendo el punto de entrada para todo.

### Option B: Triaje solo en el tool de voz `delegate_complex_task`
- Pros: la decisión se toma antes de dejar el plano de audio; máximo control de latencia; las tareas triviales nunca tocan Celery.
- Cons: sin re-verificación en el plano de ejecución; una clave rotada o un fallo en el tool deja plana la seguridad.

### Option C: Triaje en el tool de voz + re-triaje en `run_pipeline` (defensa en profundidad)
- Pros: primera decisión en el audio (mismo presupuesto), segunda en el ejecutor (consistencia e inyección detectada ante cambios de estado); `POST /debug/run` se beneficia idéntico.
- Cons: dos llamadas a Jev por tarea (coste marginal pequeño: output gratis, input ~$0.042/Mtok).

## Decision
Adoptar la **Opción C**, con un paquete `backend/decision/` modular y puro (sin dependencias de LiveKit/LangGraph):

- Cliente tipado `jev.py`: `TypeSafeClassifier` (langchain-typesafe) como primario y fallback HTTP REST a `/v1/systemone` vía `httpx`; timeout duro configurable (600 ms por defecto); normalización Pydantic estricta. Único `state` enviado: el `goal` del usuario (nunca system prompts), aislando directivas maliciosas del estado.
- Esquema `schemas.py`: primitivas `target_worker` (Choice extensible: dialogue/research/billing/identity/support), `complexity_tier` (Choice low/high), `risk_index` (Score 0=lectura/1=reversible/2=mutation crítica), `is_prompt_injection` (Noul). Hoy solo `dialogue` y `research` tienen worker real; el resto cae en orquestador/escalada.
- Política pura `router.py`: `is_prompt_injection >= 0.85` -> BLOCK; `risk >= 1.5` o (`risk >= 1.0` y tier=high) -> PROPOSE_COMMIT; `dialogue` + low + `risk < 0.5` -> FAST (modelo económico, sin Celery); resto -> ORCHESTRATOR (planner avanzado si tier=high). Confianza < 0.6 en cualquier respuesta -> escalado conservador a ORCHESTRATOR. Timeout/error de Jev -> fallback fail-open a ORCHESTRATOR (nunca FAST/BLOCK degradado).
- Integración: tool de voz `delegate_complex_task` (FAST responde directo con `gpt-4o-mini`; ORCHESTRATOR despacha a Celery con tier/model; BLOCK rechaza; PROPOSE_COMMIT pide confirmación explícita vía `confirm_execution`) y re-triaje al entrar en `run_pipeline`. Evento `routing_decision` (priority `silent`) en el bus Redis para observabilidad sin interrumpir por voz.
- Modelos configurables por env: `OPENAI_FAST_MODEL=gpt-4o-mini`, `OPENAI_ADVANCED_MODEL=gpt-4o` (se eligió gpt-4o frente a o-series/Claude para no añadir proveedor y mantener el coste acotado a tier=high).

## Consequences
- Positive:
  - Tareas triviales se resuelven en el plano de voz (ruta rápida), sin grafo ni broker; descongestión real del orquestador.
  - Enrutamiento dual bajo control estricto de presupuesto de latencia (Jev ~70-500 ms; timeout 600 ms con fallback).
  - Guardarraíles deterministas y testeables (inyección, riesgo crítico, confianza baja).
  - `langchain-typesafe==0.0.1a3` aislado tras `jev.py`: si su API alpha cambia o falla, el fallback HTTP REST lo absorbe.
- Negative:
  - Dos llamadas a Jev por tarea delegada (audio + ejecutor); coste de input adicional (mínimo: $0.042/Mtok, output gratis), y el tiempo de la llamada del ejecutor se paga sobre la latencia de `run_pipeline`.
  - El flujo PROPOSE_COMMIT añade una tool de confirmación nueva en el plano de voz (más superficie).
- Neutral:
  - `target_worker` con vocabulario más amplio que la implementación actual; la tabla de mapeo limita hoy a dialogue/research.
  - Los eventos `routing_decision` amplían el canal `agent_updates` con un tipo nuevo (ignorado por el notificador de voz al ser `silent`).

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: si `langchain-typesafe` estabiliza su API y cambia la firma de `invoke`/`ainvoke`, o si aparecen workers de dominio (billing/identity/support) que requieran ampliar la tabla de mapeo de `target_worker`.