"""Agente de voz LiveKit que actúa como orquestador conversacional.

Flujo: el usuario habla por WebRTC (browser -> LiveKit) o por teléfono real
(SIP/PSTN -> trunk inbound -> dispatch rule -> room). El AgentSession usa
el modelo de voz-a-voz OpenAI Realtime. Cuando el usuario pide una tarea
compleja, la herramienta ``delegate_complex_task`` despacha la tarea a Celery
(que ejecuta el grafo LangGraph), y un listener de Redis inyecta por voz las
actualizaciones de los subagentes de forma proactiva.

Si el usuario cuelga (WebRTC o SIP) con subagentes pendientes, el sistema
vuelve a llamar a su número vía ``CreateSIPParticipant`` para contarle el
resultado.
"""

import asyncio
import json
import logging
import uuid

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import openai

from backend.bus import redis_client
from backend.config import settings
from backend.voice import notifier, sip
from backend.voice.earcon import play_earcon
from backend.voice.tools import cancel_task, confirm_execution, delegate_complex_task

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres «Respuesta», un asistente de voz que coordina un equipo de subagentes "
    "en segundo plano. Hablas en español, de forma concisa y natural, como en una "
    "llamada telefónica. Cuando el usuario pida investigar, buscar información, "
    "resumir, comparar o analizar algo, usa la herramienta "
    "delegate_complex_task con el objetivo completo. Tras delegar, confirma "
    "brevemente y NO inventes resultados: espera los avisos que llegarán por voz. "
    "Si pediste confirmación por una acción de riesgo y el usuario responde con su "
    "decisión, llama a la herramienta confirm_execution con esa respuesta. "
    "Si el usuario pide parar, detener o cancelar lo que estás haciendo, llama a "
    "la herramienta cancel_task para detener a los subagentes. "
    "El usuario puede interrumpirte en cualquier momento."
)

WELCOME_INSTRUCTIONS = (
    "Saluda brevemente al usuario y dile que estás listo para poner a tu equipo "
    "de subagentes a trabajar."
)


class OrchestratorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            llm=openai.realtime.RealtimeModel(
                model=settings.openai_realtime_model,
                voice=settings.openai_realtime_voice,
                temperature=0.8,
            ),
            tools=[delegate_complex_task, confirm_execution, cancel_task],
            allow_interruptions=True,
        )


async def _listen_for_updates(session: AgentSession) -> None:
    """Escucha eventos de los subagentes y habla proactivamente."""
    client = redis_client.get_async()
    pubsub = client.pubsub()
    await pubsub.subscribe(settings.event_channel)
    logger.info("Escuchando actualizaciones en el canal %s", settings.event_channel)
    async for message in pubsub.listen():
        if message.get("type") != "message":
            continue
        try:
            payload = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError):
            continue
        try:
            text = notifier.build_spoken_update(payload)
        except (TypeError, AttributeError):
            text = None
        if not text:
            continue
        logger.info("Notificación por voz: %s", text)
        try:
            await play_earcon(session, payload)
            await session.generate_reply(instructions=text, allow_interruptions=True)
        except Exception:  # noqa: BLE001
            logger.exception("Fallo al inyectar la actualización por voz")


def _room_key(ctx: JobContext) -> str:
    """Clave estable del job para el registro de rellamadas (por room)."""
    try:
        return f"room-{ctx.room.name}"
    except AttributeError:
        return f"room-{uuid.uuid4().hex[:8]}"


async def _callback_pending_results(room_name: str, session_key: str) -> None:
    """Rellama al usuario si colgó con subagentes pendientes (best-effort)."""
    phone = sip.pop_caller(session_key)
    if phone is None:
        return
    if not sip.sip_enabled():
        logger.info(
            "Hay resultados pendientes para %s pero SIP no está configurado", phone
        )
        return
    try:
        await sip.place_outbound_call(
            phone,
            room_name,
            participant_identity=f"callback-{uuid.uuid4().hex[:8]}",
        )
    except Exception:  # noqa: BLE001
        logger.exception("Fallo la rellamada saliente al %s", phone)


server = AgentServer()


@server.rtc_session(agent_name=settings.agent_name)
async def voice_entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    await session.start(room=ctx.room, agent=OrchestratorAgent())
    asyncio.create_task(_listen_for_updates(session))
    # Entrada SIP: el trunk inbound encamina la llamada a esta misma room vía
    # dispatch rule; registramos el número llamante para la rellamada al colgar.
    session_key = _room_key(ctx)
    try:
        caller = sip.extract_caller_phone(ctx.room)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo detectar el llamante SIP")
        caller = None
    if caller is not None:
        sip.register_caller(session_key, caller)
        logger.info("Llamada entrante SIP de %s en room %s", caller, ctx.room.name)
    active_before = sip.snapshot_active_task_ids()

    async def _on_session_end(_reason: str) -> None:
        pending = sip.session_pending_task_ids(active_before)
        if not pending:
            sip.pop_caller(session_key)
            return
        logger.info(
            "El usuario colgó con %d subagentes pendientes; rellamando", len(pending)
        )
        try:
            room_name = ctx.room.name
        except AttributeError:
            room_name = ""
        if not room_name:
            sip.pop_caller(session_key)
            return
        await _callback_pending_results(room_name, session_key)

    ctx.add_shutdown_callback(_on_session_end)
    await session.generate_reply(instructions=WELCOME_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(server)