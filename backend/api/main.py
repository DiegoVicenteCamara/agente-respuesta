"""API web: sirve la página del navegador y emite tokens JWT de LiveKit."""

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel
from redis.asyncio import Redis

from backend.config import settings

app = FastAPI(title="Respuesta — Agente de voz con subagentes", version="0.1.0")

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


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
    identity = identity or f"user-{uuid.uuid4().hex[:8]}"
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
    await asyncio.to_thread(run_pipeline.delay, task_id=task_id, goal=goal)
    # Registra la tarea en el historial (best-effort, no bloquea el 200).
    try:
        from backend.bus import redis_client

        await asyncio.to_thread(redis_client.register_task, task_id, goal)
    except Exception:  # noqa: BLE001
        pass
    return {"task_id": task_id}


@app.get("/tasks")
async def list_tasks(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    """Historial de tareas pasadas (degradación elegante: [] si Redis falla)."""
    from backend.bus import redis_client

    return await asyncio.to_thread(redis_client.list_tasks, limit)


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Eventos ordenados de una tarea; 404 si no existe."""
    from backend.bus import redis_client

    events = await asyncio.to_thread(redis_client.get_task_events, task_id)
    if events is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"task_id": task_id, "events": events}


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