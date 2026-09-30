# Spec: Entrada por teléfono real (SIP/PSTN) y llamadas salientes

## Clasificación brainstorming

**Architectural** — nuevo subsistema de acceso (voz vía PSTN además de WebRTC
del navegador) más llamadas salientes. Altera cómo los usuarios llegan al
agente y añade un camino de ejecución (rellamada al colgar).

> NOTA DE APROBACIÓN (HARD-GATE): este diseño se implementa en CI autónoma
> (issue `feat/sip-pstn-telephony`); la aprobación humana queda pendiente en
> la revisión del PR. No fusionar sin revisar las secciones de diseño.

## Objetivo

1. **Entrante:** el agente responde a llamadas SIP reales (trunk inbound +
   dispatch rule de LiveKit) con el mismo flujo de voz/delegación que el
   navegador: `delegate_complex_task` → Celery/LangGraph → eventos Redis
   (`plan_ready`, `subtask_done`, `analysis_ready`) → interrupción proactiva.
2. **Saliente:** si el usuario cuelga con subagentes pendientes, el sistema
   vuelve a llamar a su número (`CreateSIPParticipant`) para contarle el
   resultado.
3. El earcon de aviso es de su propia issue (`feat/earcon-interruption`):
   se reutiliza `play_earcon`, no se duplica.

## Contexto actual

- `backend/voice/agent.py`: un único `AgentServer` + `rtc_session`
  (`voice_entrypoint`) pensado para WebRTC. Sin detección de origen SIP,
  sin registro del número llamante, sin callback al cerrar la sesión.
- `backend/voice/tools.py`: `ACTIVE_TASKS` guarda la tarea Celery por sesión
  (`_session_key`), pero nadie la consulta al terminar la llamada.
- `backend/config.py` / `.env.example`: sin credenciales SIP.
- `backend/api/main.py` + `web/index.html`: sin control para marcar al
  número del usuario.

## Diseño

### Enfoques considerados

1. **Entrypoint SIP separado** (`ServerType.INBOUND` / segundo worker):
   descartado — duplica el flujo de voz y el listener Redis; LiveKit ya
   encamina las llamadas SIP del trunk a rooms normales vía dispatch rule,
   por lo que el mismo `rtc_session` sirve a ambos orígenes.
2. **Elegido: mismo entrypoint + detección de origen + servicio SIP.**
   `voice_entrypoint` detecta al participante SIP (atributos
   `sip.phoneNumber`, kind SIP), registra su número para una posible
   rellamada y añade un `shutdown_callback` que, si quedan tareas activas
   en `ACTIVE_TASKS`, marca vía `CreateSIPParticipant`. La salida vive en
   un módulo nuevo `backend/voice/sip.py`, testeable con mocks del cliente
   LiveKit (cero coste real en verificación).
3. **Rellamada vía Celery beat / watcher Redis**: descartado por ahora —
   añade infraestructura. El `shutdown_callback` del job cubre el criterio
   de éxito con el mecanismo más simple; un watcher se puede añadir en un
   ADR posterior si hacen falta rellamadas cuando el worker de voz ya murió.

### Componentes

```
backend/voice/sip.py       → servicio SIP (nuevo). Sin estado LiveKit global.
  sip_enabled()            → SIP_ENABLED=true y SIP_TRUNK_ID configurado
  normalize_phone()        → valida E.164 (+ prefijo país, dígitos)
  place_outbound_call()    → CreateSIPParticipant (cliente inyectable)
  register_caller() / pop_caller()  → número por clave de sesión
  pending_callback_for()   → teléfono si hay ACTIVE_TASKS pendientes
backend/voice/agent.py     → detecta llamante SIP, registra número,
                             shutdown_callback → rellamada best-effort
backend/voice/tools.py     → sin cambios de comportamiento (se lee ACTIVE_TASKS)
backend/config.py          → SIP_ENABLED, SIP_TRUNK_ID, SIP_NUMBER
.env.example               → documenta las tres variables
backend/api/main.py        → POST /sip/call {phone_number, room?}
web/index.html             → campo de teléfono + botón "Llamar al teléfono"
backend/tests/test_sip.py  → mocks del cliente LiveKit, sin red
```

### Flujos

- **Entrante:** PSTN → trunk inbound LiveKit → dispatch rule → room +
  worker (`voice_entrypoint`) → saludo + `delegate_complex_task` + listener
  Redis idénticos al navegador. `extract_caller_phone(room)` lee el número
  del participante remoto (atributos SIP); si no hay número, todo sigue
  igual (voz intacta).
- **Saliente al colgar:** `ctx.add_shutdown_callback(on_end)` → busca la
  clave de sesión en `ACTIVE_TASKS` → si hay tarea pendiente y hay número
  registrado y `sip_enabled()`, `place_outbound_call` a la misma room con
  identidad `callback-<corto>`. Best-effort: nunca eleva excepciones al
  apagado; solo log.
- **Saliente manual:** `POST /sip/call` valida E.164, exige trunk
  configurado (501 si no) y marca al número indicado.

### Errores

- Sin `SIP_TRUNK_ID` o `SIP_ENABLED=false` → salientes rechazadas con
  `SIPConfigError` / HTTP 501; entrantes WebRTC intactas.
- Teléfono no E.164 → `ValueError` / HTTP 422.
- Fallo de LiveKit en la marcación → se propaga como `RuntimeError` con
  log (endpoint devuelve 502); el shutdown_callback lo traga con log.

### Testing

- `backend/tests/test_sip.py`: normalización E.164, `sip_enabled`,
  `place_outbound_call` con cliente fake (verifica `room_name`,
  `sip_trunk_id`, `sip_call_to`), registro de llamante, endpoint
  `/sip/call` (éxito, sin trunk → 501, teléfono inválido → 422),
  `extract_caller_phone` con room fake y shutdown-callback con tareas
  pendientes / sin pendientes.
- Suite completa `python -m pytest -q` en verde.

## Criterios de éxito

- Llamada SIP entrante atendida con el flujo de delegación intacto.
- `delegate_complex_task` mantiene el despacho Redis (`plan_ready`,
  `subtask_done`, `analysis_ready`).
- Rellamada `CreateSIPParticipant` al colgar con subagentes pendientes.
- Tests en verde (mocks) y ADR creado.
