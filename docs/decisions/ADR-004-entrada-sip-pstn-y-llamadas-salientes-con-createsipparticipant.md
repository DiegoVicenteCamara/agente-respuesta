# ADR-004: Entrada SIP/PSTN y llamadas salientes con CreateSIPParticipant

## Status
accepted

## Date
2026-09-23

## Context
El agente solo acepta voz WebRTC desde el navegador. La investigación del
proyecto ("Sistemas Multiagente y Voz Interactiva") pide entrada por teléfono
real (SIP/PSTN) y rellamadas cuando el usuario cuelga con subagentes
pendientes, manteniendo voz (<800 ms, LiveKit) y ejecución (Celery)
desacoplados vía el bus Redis. El earcon de aviso vive en su propia issue y
queda fuera de este ADR.

## Options Considered

### Option A: Entrypoint SIP separado (segundo worker / ServerType distinto)
- Pros: aislamiento total entre WebRTC y PSTN.
- Cons: duplica el flujo de voz y el listener Redis; LiveKit ya encamina el
  trunk inbound a rooms normales vía dispatch rule, así que el desdoblamiento
  no aporta nada.

### Option B (elegida): Mismo entrypoint + detección de origen + servicio SIP
- Pros: un solo flujo de voz/delegación para navegador y teléfono; módulo
  `backend/voice/sip.py` testeable con mocks (cero coste); `SIP_ENABLED=false`
  deja el comportamiento actual intacto.
- Cons: la rellamada al colgar depende del `shutdown_callback` del job de voz;
  si el worker muere abruptamente no hay rellamada (se acepta; un watcher
  Celery/Redis queda como evolución futura).

### Option C: Watcher Celery/Redis para rellamadas (sin callback en voz)
- Pros: rellamada incluso si el worker de voz cae.
- Cons: infraestructura nueva (beat/watcher, estado persistente) para un
  criterio de éxito que el shutdown_callback ya cubre. Descartada por YAGNI.

## Decision
Mismo `rtc_session` para WebRTC y SIP (el trunk inbound + dispatch rule de
LiveKit llevan la llamada a una room normal); `extract_caller_phone` detecta
el número llamante y se registra por room; al cerrar la sesión, si hay
task_ids creados durante el job que siguen en `ACTIVE_TASKS`, se marca vía
`CreateSIPParticipant` a la misma room (best-effort, nunca eleva). Salientes
manuales vía `POST /sip/call`. Config: `SIP_ENABLED`, `SIP_TRUNK_ID`,
`SIP_NUMBER` (alias `AGENT_NUMBER`).

## Consequences
- Positive: teléfono real entrante con delegación intacta (`plan_ready`,
  `subtask_done`, `analysis_ready`); rellamada automática al colgar; tests
  con mocks sin costes.
- Negative: sin watcher persistente no hay rellamada si el worker de voz
  muere de forma abrupta; el número llamante depende de los atributos SIP
  que exponga el trunk.
- Neutral: con `SIP_ENABLED=false` (defecto) todo el flujo anterior sigue
  idéntico; la web gana un control de marcación manual.

## Review
- Cadence: quarterly
- Next review: 2026-12-23
- Trigger: reevaluar (watcher Celery/Redis) si se pierden rellamadas por
  caídas del worker de voz, o al dar de alta el trunk productivo.
