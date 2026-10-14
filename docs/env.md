# Variables de entorno y modelo de precios

Referencia operativa del `.env` (issue #50). Fuente de verdad del código:
`backend/config.py` (`Settings`) y `backend/orchestrator/cost.py`.
Copia con `cp .env.example .env` y rellena solo las claves que uses;
los valores de abajo son los **defaults del código**, no secretos.

> Sin secretos aquí: los placeholders están en `.env.example`. No pegues
> claves reales en docs ni en issues.

## Tabla completa (34 claves leídas en `backend/config.py`)

| Variable | Default en código | Qué controla / cuándo cambiarla |
|---|---|---|
| `LIVEKIT_URL` | `""` (vacío) | URL del proyecto LiveKit Cloud (`wss://<sub>.livekit.cloud`). Obligatoria para voz y `GET /token`. |
| `LIVEKIT_API_KEY` | `""` | Key de LiveKit (Settings → Keys). Obligatoria para voz. |
| `LIVEKIT_API_SECRET` | `""` | Secret de LiveKit. Obligatorio para firmar `GET /token`. |
| `OPENAI_API_KEY` | `""` | Clave OpenAI. Obligatoria para Realtime, planner y fallback (`quick_answer`/`chat`). |
| `OPENAI_REALTIME_MODEL` | `gpt-realtime` | Modelo de voz del worker (`backend/voice/agent.py`). Cambiar solo si OpenAI renombra el modelo. |
| `OPENAI_REALTIME_VOICE` | `coral` | Voz de Realtime. Cambiar por preferencia (p. ej. otra voz disponible). |
| `OPENAI_PLANNER_MODEL` | `gpt-4o-mini` | Planificador del grafo LangGraph. Subir a `gpt-4o` si los planes salen pobres. |
| `TAVILY_API_KEY` | `""` | Búsqueda web Tavily. Vacío → DuckDuckGo (más lento, a veces vacío). Poner clave para investigación fiable. |
| `REDIS_URL` | `redis://localhost:6379/0` | Broker Celery + bus pub/sub. Cambiar a Redis Cloud (Upstash) en despliegue. |
| `EVENT_CHANNEL` | `agent_updates` | Canal pub/sub de eventos (`plan_ready`, `subtask_done`, `analysis_ready`, `cost_ready`). Cambiar solo si colisiona con otro servicio en el mismo Redis. |
| `AGENT_NAME` | `agente-respuesta` | Nombre del worker LiveKit. Debe coincidir con la clave del CLI `lk agent dev`. |
| `HTTP_PORT` | `7860` | Puerto de `uvicorn backend.api.main:app`. Cambiar si el puerto está ocupado. |
| `TYPESAFE_API_KEY` | `""` | Clave de TypeSafe (Jev, Sistema 1). Vacía → el triaje usa heurística local. |
| `TYPESAFE_MODEL` | `jev-latest` | Modelo Jev para el triaje. Fijar versión si se necesita reproducibilidad. |
| `TYPESAFE_BASE_URL` | `https://api.typesafe.ai` | Endpoint de TypeSafe. Cambiar solo para mock/staging. |
| `OPENAI_FAST_MODEL` | `gpt-4o-mini` | Modelo económico de la ruta `FAST`. Cambiar si se quiere otro coste/calidad. |
| `OPENAI_ADVANCED_MODEL` | `gpt-4o` | Modelo avanzado de la ruta `ORCHESTRATOR`. Cambiar si se quiere otro flagship. |
| `ROUTING_RISK_FAST` | `0.5` | Riesgo < umbral y tier=low → modelo económico. Bajar para ser más conservador. |
| `ROUTING_RISK_CRITICAL` | `1.5` | Riesgo ≥ umbral → Propose-Commit (pide confirmación). Bajar para confirmar más a menudo. |
| `ROUTING_INJECTION_THRESHOLD` | `0.85` | Score de inyección ≥ umbral → bloquea/confirma. Bajar solo si hay muchos falsos negativos. |
| `ROUTING_CONFIDENCE_MIN` | `0.6` | Confianza baja → escala al orquestador. Subir para ser más conservador. |
| `ROUTING_TIMEOUT_MS` | `600` | Timeout duro de la llamada a Jev. Subir en redes lentas; bajar para voz más rápida. |
| `COST_TRACKING_ENABLED` | `true` | `false` desactiva callbacks y el evento `cost_ready` dejando el flujo intacto. |
| `COST_EUR_PER_USD` | `1.0` | Factor USD→EUR aplicado en `estimate_cost_eur`. Ajustar al tipo de cambio real (p. ej. `0.92`). |
| `PRICING_GPT_4O_MINI_PER_1M_IN` | `0.15` | USD por 1M tokens de entrada para `gpt-4o-mini`. Calibrar con https://platform.openai.com/pricing. |
| `PRICING_GPT_4O_MINI_PER_1M_OUT` | `0.60` | USD por 1M tokens de salida para `gpt-4o-mini`. Idem. |
| `PRICING_GPT_4O_PER_1M_IN` | `2.50` | USD por 1M tokens de entrada para `gpt-4o`. Idem. |
| `PRICING_GPT_4O_PER_1M_OUT` | `10.00` | USD por 1M tokens de salida para `gpt-4o`. Idem. |
| `MEMORY_ENABLED` | `true` | `false` deja el flujo sin memoria persistente por usuario. |
| `MEMORY_TTL_DAYS` | `30` | TTL de la clave `user:{user_id}:memory`. Bajar para olvidar antes (privacidad/coste). |
| `MEMORY_MAX_CHARS` | `2000` | Corte del resumen determinista de respaldo. Bajar para prompts más cortos. |
| `CACHE_TTL_SECONDS` | `86400` | TTL de `research:{hash}` (24 h). Bajar para noticias frescas; subir para ahorrar Tavily. |
| `EARCON_ENABLED` | `false` | `true` reproduce un tono breve antes de interrupciones `info`/`urgent`. |
| `EARCON_PATH` | `""` | Ruta opcional a un `.wav`; vacío usa el tono sintetizado. |

Verificación: cada fila coincide con `backend/config.py` (`_get("<NOMBRE>", "<default>")`;
precios vía `_load_pricing()` con claves `PRICING_<SLUG>_PER_1M_IN/OUT`) y cada
nombre existe en `.env.example` (test `backend/tests/test_env_docs.py`).

## Modelo de precios (`cost_ready`)

`backend/orchestrator/cost.py` acumula por tarea (`CostTracker` en `contextvar`)
el uso de tokens que registra `TokenUsageCallback` (metadata del proveedor o
`tiktoken` como respaldo). Al cerrar la tarea, `publish_cost_ready(task_id, model)`
publica en Redis el evento:

```json
{ "type": "cost_ready", "priority": "silent", "agent": "cost",
  "tokens_in": 1000, "tokens_out": 200, "cost_eur": 0.0003, "estimated": true }
```

Fórmula (`estimate_cost_eur`):

```
usd = in/1M * PRICING_<SLUG>_PER_1M_IN + out/1M * PRICING_<SLUG>_PER_1M_OUT
eur = round(usd * COST_EUR_PER_USD, 6)
```

El slug es `model.upper().replace("-", "_").replace(".", "_")`
(p. ej. `gpt-4o-mini` → `GPT_4O_MINI`); modelos sin entrada en la tabla
cuestan `0.0` (desconocido = gratis en la estimación, no real).

Cómo calibrar con precios reales de OpenAI:

1. Abre https://platform.openai.com/pricing y anota el precio por 1M in/out
   del modelo que uses en `OPENAI_FAST_MODEL` / `OPENAI_ADVANCED_MODEL`.
2. Actualiza las cuatro claves `PRICING_*` en tu `.env` (USD por millón).
3. Ajusta `COST_EUR_PER_USD` a tu tipo de cambio (p. ej. `0.92`).
4. Lanza una tarea en Modo prueba y comprueba el mensaje
   `Coste estimado: X € (N tokens in / M tokens out)` del evento `cost_ready`.
5. Si desactivas el seguimiento (`COST_TRACKING_ENABLED=false`), el evento
   deja de emitirse y el pipeline sigue igual.
