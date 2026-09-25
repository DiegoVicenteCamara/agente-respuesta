# Respuesta — Agente de voz con subagentes proactivos

[![Sitio público](https://img.shields.io/badge/sitio-GitHub%20Pages-blue)](https://diegovicentecamara.github.io/agente-respuesta/)
> **Sitio público (landing):** https://diegovicentecamara.github.io/agente-respuesta/ — pitch, arquitectura, quickstart y docs. La landing enlaza aquí y viceversa (ver [ADR-004](docs/decisions/ADR-004-landing-page-en-github-pages-desde-docs-con-deploy-por-actions.md)).

Un agente de IA que funciona como si estuvieras en una llamada con una persona:
recibes una llamada desde tu navegador, le pides una tarea compleja (investigar,
resumir, comparar…) y un **orquestador la descompone y delega a subagentes en
segundo plano** (búsqueda web + síntesis). Cuando un subagente avanza, el agente
**te interrumpe por voz** con la novedad, respetando los turnos de conversación.

Arquitectura fiel a la investigación *"Sistemas Multiagente y Voz Interactiva"*:
los planos de **voz** (síncrono, <800 ms) y de **ejecución** (asíncrono) están
desacoplados mediante un bus de eventos Redis.

```
[Navegador (LiveKit) ⇄ WebRTC] → backend (FastAPI /token)
                                        │
                    Worker de voz LiveKit (OpenAI Realtime API)
                        ├─ tool delegate_complex_task → despacha a Celery
                        └─ listener Redis → habla proactivamente
                                        │
                              Redis (pub/sub + broker)
                                        │
         Celery worker → LangGraph (supervisor + subagentes en paralelo)
             planner → research (fan-out) → synthesize (publican eventos)
```

## Stack

| Componente | Tecnología |
|---|---|
| Voz en tiempo real | LiveKit Agents 1.8 + OpenAI Realtime API (voz-a-voz) |
| Orquestación multiagente | LangGraph (grafo supervisor con fan-out en paralelo) |
| Ejecución duradera | Celery (worker) + Redis (broker y bus de eventos) |
| Búsqueda web | Tavily (si hay clave) o DuckDuckGo (sin clave) |
| Web del navegador | FastAPI + `livekit-client` |

## Requisitos (Fase 0 — alta en servicios)

1. **LiveKit Cloud** → https://cloud.livekit.io (plan gratuito).
   En *Settings → Keys* copia `LIVEKIT_URL` (`wss://<sub>.livekit.cloud`),
   `LIVEKIT_API_KEY` y `LIVEKIT_API_SECRET`.
2. **OpenAI** → https://platform.openai.com/api-keys. Una clave para el modelo
   de voz `gpt-realtime` y para el planificador `gpt-4o-mini`.
3. **Tavily** (opcional) → https://app.tavily.com. Sin clave se usa DuckDuckGo.
4. **Redis local** → con **Docker Desktop** (Windows): `docker run -d --name agente-redis -p 6379:6379 --restart unless-stopped redis:7-alpine`
   (o un Redis en la nube gratuito: Upstash / Redis Cloud).
5. LiveKit CLI (para probar el agente en modo dev):
   `curl -sSL https://get.livekit.io/cli | bash` y `lk cloud auth`.

## Configuración

```bash
cp .env.example .env
# rellena LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, OPENAI_API_KEY
```

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

> Nota: probado con Python 3.14. Si algún wheel fallara, usa Python 3.12/3.13.

## Ejecución (4 terminales)

```bash
# 1. Redis
redis-server
```

### Windows + Docker (un solo comando)

```powershell
powershell -ExecutionPolicy Bypass -File tools\start_dev.ps1        # sin voz
powershell -ExecutionPolicy Bypass -File tools\start_dev.ps1 -Voice # con voz
```

Lanza el contenedor Redis, el worker de Celery y la web (ocultos, con logs en
`logs/`). Estado y parada:

```powershell
powershell -File tools\status.ps1           # estado de la web y el worker
powershell -File tools\status.ps1 -kill     # detiene web + worker
```

### Manual (4 terminales)

```bash
# 1. Redis
redis-server

# 2. Worker de subagentes (LangGraph en Celery)
.venv/bin/celery -A backend.orchestrator.tasks.celery_app worker -P solo -l info

# 3. Agente de voz (LiveKit); modos: dev / start / console
.venv/bin/python -m backend.voice.agent dev

# 4. Backend web + token
.venv/bin/uvicorn backend.api.main:app --port 7860
```

> Para el modo `dev`, instala el CLI de LiveKit y ejecuta `lk agent dev`
> desde la raíz del proyecto (entrega una URL de consola para hablar con el
> agente desde el navegador). El nombre del agente es `agente-respuesta`
> (`AGENT_NAME` en `.env`).

## Probar

1. Abre http://localhost:7860 en el navegador.
2. Pulsa **Llamar** → permites el micrófono → el agente te saluda por voz.
3. Dile algo como:
   *«Investiga las últimas novedades sobre agentes de IA en español y
   resúmelo»*.
4. El agente confirma, el grafo descompone la tarea, lanza subagentes en
   paralelo y **te interrumpe por voz** en cuanto hay avances
   (*plan_ready*, *subtask_done*, *analysis_ready*).

Los eventos que genera cada nodo se ven en la terminal del worker Celery.

## Modo prueba (sin voz, sin créditos OpenAI)

La web incluye un panel **"Modo prueba"**: escribe un objetivo, pulsa
**Iniciar tarea** y verás en vivo los avisos proactivos del orquestador
(`plan_ready` → `subtask_done` → `analysis_ready`) llegando por el mismo bus
Redis y con la misma prioridad (`silent`/`info`/`urgent`) que usaría la voz.
Detrás, el endpoint `POST /debug/run` despacha la tarea a Celery y
`GET /debug/stream` (SSE) la reenvía al navegador.

> La búsqueda usa DuckDuckGo si no hay `TAVILY_API_KEY`; suele tardar o
> devolver vacío aleatoriamente — los eventos se siguen emitiendo igualmente.

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Estructura

```
backend/
  api/main.py              # FastAPI: /token (JWT LiveKit) y página web
  config.py                # Carga de .env y ajustes
  bus/redis_client.py      # Clientes Redis (pub/sub y broker)
  orchestrator/
    graph.py               # Grafo LangGraph (planner/research/synthesize)
    nodes.py               # Nodos: planificador, búsqueda web, síntesis
    tasks.py               # Tarea Celery run_pipeline
  voice/
    agent.py               # Worker de voz (AgentServer + AgentSession)
    tools.py               # Herramienta delegate_complex_task
    notifier.py            # Política de notificación proactiva por voz
  tests/                   # Tests unitarios
web/index.html             # Cliente del navegador (livekit-client)
```

## Cómo notifica (ergonomía de la investigación)

- **`priority: silent`** → se actualiza estado, no interrumpe.
- **`priority: info`** → habla con prefacio cortés *«Disculpa que te
  interrumpa…»* respetando el barge-in (`allow_interruptions=True`).
- **`priority: urgent`** → *«Necesito tu atención…»*.

## Implementación autónoma de issues (opencode en CI)

Los issues del repo marcos con la label **`agent-ready`** son implementados de
forma autónoma por un agente opencode y devueltos como un Pull Request listo
para revisión. Ver `docs/decisions/ADR-003-...` y
`docs/decisions/ADR-005-...` para el diseño completo.

- **`agent-ready`** → el workflow `opencode-label` se dispara y el agente
  implementa el issue (rama `opencode/issue<N>-<ts>` + PR con `Closes #N`).
- **Scheduler** (`opencode-schedule`, cada 6h) → procesa el issue `agent-ready`
  más antiguo sin PR abierto, 1 por run.
- **CI** (`test`) → corre `pytest` en cada PR y push a `main`; check obligatorio
  de branch protection. El agente debe dejar la suite verde antes de abrir el PR.
- **Revisión y merge automático** (`opencode-review`) → un agente revisor
  comprueba la Definición de Hecho del proyecto (`docs/definition-of-done.md`),
  trae `main` sobre la rama resolviendo conflictos en verde y, si todo cumple,
  mergea la PR automáticamente. Si algo no cumple, comenta en la PR qué falla y
  qué soluciones y deja la PR abierta sin mergear.
- Labels: `agent-ready` → `agent-in-progress` mientras trabaja; si falla, se
  restaura `agent-ready`.

Setup (una vez): instalar la GitHub App `opencode-agent` en el repo, crear el
secret `OPENCODE_API_KEY` (suscripción opencode Zen/Go) y los labels
`agent-ready` / `agent-in-progress`; activar branch protection en `main`
(exigir PR y check `test`; el review lo realiza el agente revisor).

## Siguiente paso natural

Entrada por **teléfono real (SIP/PSTN)** con llamadas salientes
(`CreateSIPParticipant`) cuando el usuario cuelga y los subagentes terminan, y
un **earcon** (tono previo) antes de hablar, como propone la investigación.