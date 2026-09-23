# ADR-002: Publicar causa de jev_unavailable en routing_decision (detalle)

## Status
accepted

## Date
2026-09-23

## Context
El ruteo dual (ADR-001) escala todo al orquestador cuando el triaje Jev no
produce respuesta (`reason="jev_unavailable"`, `fallback=true`). Hasta ahora el
único observable era ese motivo genérico: no se distinguía entre clave no
configurada, timeout, errores de transporte (langchain_typesafe / HTTP) o
respuesta no normalizable. Diagnosticarlo exigía mirar logs del worker, y la
causa raíz más común (ausencia de `TYPESAFE_API_KEY`) no era evidente ni en el
panel debug ni en el payload del evento `routing_decision`.

Objetivo: que el panel debug y el bus de eventos expliquen por qué no hubo
triaje, manteniendo el comportamiento fail-open actual (todo sigue yendo al
orquestador) y dejando la activación real de Jev a solas de `TYPESAFE_API_KEY`
en `.env` + reinicio.

## Options Considered

### Option A: Log en servidor, sin tocar el payload del evento
- Pros: cambio mínimo, cero impacto en el contrato del evento.
- Cons: las causas no llegan al panel debug (la UI solo consume el bus); el
  usuario no distingue clave ausente de timeout sin abrir logs.

### Option B: Campo `detail` en `RouteDecision`, propagado al evento y al panel
- Pros: observabilidad end-to-end (bus → UI) sin superficie de API nueva; campo
  opcional → no rompe consumidores del payload; fail-open intacto; introduce
  `ClassifyOutcome` como contrato explícito del cliente Jev.
- Cons: el `detail` puede contener texto de excepciones de terceros (ruido);
  añade un campo a cada evento `routing_decision` (JSON ligeramente mayor).

### Option C: Endpoint de diagnóstico dedicado
- Pros: puede exponer métricas y estados detallados a demanda.
- Cons: superficie de API extra sin consumo real; overkill para una causa que se
  explica en una línea; el plan lo descartó explícitamente.

## Decision
Se adopta la Opción B. `route()` consume un `ClassifyOutcome(answer, detail)`
de `jev.classify()` y propaga `detail` a `fallback_decision()` y al payload
`routing_decision` (campo nuevo `detail`). El panel debug renderiza el detalle
atenuado bajo el mensaje del agente. Además:
- `ROUTING_TIMEOUT_MS` pasa de 600 a 2000 ms por defecto para que, con clave
  real, las dos llamadas a Jev no venzan antes de reencauçar el camino FAST.
- Aviso `warning` único al arrancar si falta `TYPESAFE_API_KEY`.

## Consequences
- Positive: la causa de `jev_unavailable` se ve en el panel debug y en el bus;
  con clave real el camino Sistema 1 queda listo sin tocar código.
- Negative: `detail` puede arrastrar texto de excepciones de servicios de
  terceros (mínimo ruido; la UI lo muestra atenuado).
- Neutral: campo opcional y compatible hacia atrás; a fecha de hoy lo consume
  solo la UI.

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: si TypeSafe cambia el formato de diagnósticos, o se incorpora un
  segundo Sistema 1 que comparta el campo `detail`.