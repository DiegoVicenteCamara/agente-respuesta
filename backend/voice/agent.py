"""Agente de voz LiveKit que actúa como orquestador conversacional.

Flujo: el usuario habla por WebRTC (browser -> LiveKit). El AgenteSession usa
el modelo de voz-a-voz OpenAI Realtime. Cuando el usuario pide una tarea
compleja, la herramienta ``delegate_complex_task`` despacha la tarea a Celery
(que ejecuta el grafo LangGraph), y un listener de Redis inyecta por voz las
actualizaciones de los subagentes de forma proactiva.
"""

import asyncio
import json
import logging

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import openai

from backend.bus import redis_client
from backend.config import settings
from backend.memory import service as memory_service
from backend.voice import notifier
from backend.voice import tools
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


def _resolve_user_id(ctx: JobContext) -> str:
    """Resuelve la identidad: participante > claims del token > ``anonymous``.

    Nunca eleva excepciones: ante sala vacía o claims ausentes devuelve
    ``"anonymous"`` para que el flujo siga sin memoria pero sin errores.
    """
    try:
        participants = getattr(getattr(ctx, "room", None), "remote_participants", None)
        if participants:
            values = list(participants.values()) if hasattr(participants, "values") else list(participants)
            for participant in values:
                identity = getattr(participant, "identity", None)
                if identity:
                    return str(identity)
    except Exception:  # noqa: BLE001
        logger.debug("No se pudo resolver identidad por participante", exc_info=True)
    try:
        claims_fn = getattr(ctx, "token_claims", None)
        claims = claims_fn() if callable(claims_fn) else None
        identity = getattr(claims, "identity", None)
        if isinstance(claims, dict):
            identity = identity or claims.get("identity")
        if identity:
            return str(identity)
    except Exception:  # noqa: BLE001
        logger.debug("No se pudo resolver identidad por claims", exc_info=True)
    return "anonymous"


def build_welcome_instructions(memory: str | None) -> str:
    """Compone el saludo: con memoria menciona el trabajo previo, sin ella la base."""
    if memory and str(memory).strip():
        return (
            f"{WELCOME_INSTRUCTIONS} La última vez investigaste "
            f"{str(memory).strip()} — cuéntame qué necesitas ahora."
        )
    return WELCOME_INSTRUCTIONS


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


server = AgentServer()


@server.rtc_session(agent_name=settings.agent_name)
async def voice_entrypoint(
    ctx: JobContext,
    *,
    session_factory=None,
    agent_factory=None,
) -> None:
    """Punto de entrada de voz: identidad, memoria, bienvenida y listener.

    ``session_factory`` / ``agent_factory`` son puntos de inyección para tests
    (evitan el LLM real de ``AgentSession``/``OrchestratorAgent``).
    """
    user_id = _resolve_user_id(ctx)
    tools.USER_ID.set(None if user_id == "anonymous" else user_id)
    memory = await memory_service.load(None if user_id == "anonymous" else user_id)
    welcome = build_welcome_instructions(memory)
    if memory and user_id != "anonymous":
        await memory_service.publish_recalled(user_id, memory)
    make_session = session_factory or AgentSession
    make_agent = agent_factory or OrchestratorAgent
    session = make_session()
    await session.start(room=ctx.room, agent=make_agent())
    asyncio.create_task(_listen_for_updates(session))
    await session.generate_reply(instructions=welcome)


if __name__ == "__main__":
    agents.cli.run_app(server)