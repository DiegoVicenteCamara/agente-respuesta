"""API web: sirve la página del navegador y emite tokens JWT de LiveKit."""

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel
from redis.asyncio import Redis

from backend.bus import redis_client
from backend.config import settings

app = FastAPI(title="Respuesta — Agente de voz con subagentes", version="0.1.0")

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

logger = logging.getLogger(__name__)

#: Tareas de prueba lanzadas desde el panel web pendientes de terminar.
#: Se usa para resolver 404 en cancelaciones sin tarea en curso cuando
#: Redis aún no tiene eventos de la tarea (o está caído).
DEBUG_TASKS: set[str] = set()


class RunGoal(BaseModel):
    goal: str


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/token")
async def get_token(
    room: str = Query("demo", description="Nombre de la sala WebRTC"),
    identity: str | None = Query(None, description="Identidad opcional del usuario"),
) -> dict:
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(
            status_code=500,
            detail="LIVEKIT_API_KEY / LIVEKIT_API_SECRET no configurados en .env",
        )
    identity = identity or f"participant-{uuid.uuid4().hex[:8]}"
    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_ttl(settings.token_ttl)
        .with_grants(VideoGrants(room_join=True, room=room))
    )
    return {
        "token": token.to_jwt(),
        "wsUrl": settings.livekit_url,
        "room": room,
        "identity": identity,
    }


@app.post("/debug/run")
async def debug_run(body: RunGoal) -> dict:
    """Lanza una tarea de prueba a los subagentes (Celery) sin pasar por la voz."""
    goal = body.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="El objetivo no puede estar vacío")
    from backend.orchestrator.tasks import run_pipeline

    task_id = f"web-{uuid.uuid4().hex[:8]}"
    # apply_async con task_id explícito para que revoke(task_id) funcione
    # (delay no fija el id del mensaje Celery y la cancelación no llegaría).
    await asyncio.to_thread(
        run_pipeline.apply_async,
        kwargs={"task_id": task_id, "goal": goal},
        task_id=task_id,
    )
    DEBUG_TASKS.add(task_id)
    return {"task_id": task_id}


@app.post("/debug/cancel/{task_id}")
async def debug_cancel(task_id: str) -> dict:
    """Revoca una tarea de prueba en curso y publica `task_cancelled` en el bus."""
    from backend.orchestrator.tasks import celery_app

    task_id = task_id.strip()
    if not task_id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    goal: str | None = None
    has_events = False
    already_finished = False
    try:
        detail = await redis_client.get_task_events(task_id)
        events = detail.get("events", [])
        has_events = bool(events)
        goal = detail.get("goal")
        if not goal:
            for ev in events:
                if ev.get("goal"):
                    goal = ev["goal"]
                    break
        already_finished = any(
            ev.get("type") in ("analysis_ready", "blocked", "task_cancelled")
            or ev.get("priority") == "urgent"
            for ev in events
        )
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo leer eventos para cancelar task_id=%s", task_id)

    known_in_memory = task_id in DEBUG_TASKS
    if already_finished:
        DEBUG_TASKS.discard(task_id)
        raise HTTPException(
            status_code=404, detail="Tarea no encontrada o sin tarea en curso"
        )
    if not known_in_memory and not has_events:
        raise HTTPException(
            status_code=404, detail="Tarea no encontrada o sin tarea en curso"
        )

    try:
        await asyncio.to_thread(
            celery_app.control.revoke, task_id, terminate=True, signal="SIGTERM"
        )
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo revocar la tarea task_id=%s", task_id)

    message = f"Tarea cancelada: {goal}" if goal else "Tarea cancelada"
    payload = {
        "task_id": task_id,
        "type": "task_cancelled",
        "agent": "orchestrator",
        "message": message,
        "priority": "info",
        "ts": int(time.time() * 1000),
    }
    if goal:
        payload["goal"] = goal
    try:
        await redis_client.publish_event(payload)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo publicar task_cancelled task_id=%s", task_id)

    DEBUG_TASKS.discard(task_id)
    return {"task_id": task_id, "cancelled": True}


@app.get("/tasks")
async def list_tasks() -> list[dict]:
    """Historial de tareas pasadas: resumen por tarea, creación reciente primero."""
    try:
        return await redis_client.list_tasks()
    except Exception:  # noqa: BLE001
        return []


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Eventos ordenados de una tarea pasada."""
    try:
        detail = await redis_client.get_task_events(task_id)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if not detail["events"]:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"task_id": task_id, "goal": detail["goal"], "events": detail["events"]}


@app.get("/debug/stream")
async def debug_stream() -> StreamingResponse:
    """SSE: reenvía los eventos del bus de agentes al navegador."""

    async def event_gen():
        client = Redis.from_url(
            settings.redis_url, decode_responses=True, socket_timeout=1
        )
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(settings.event_channel)
            yield "event: open\ndata: {}\n\n"
            while True:
                await asyncio.sleep(0.05)
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=0.2
                )
                if msg and msg.get("type") == "message":
                    yield f"data: {msg['data']}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.aclose()
                await client.aclose()
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")