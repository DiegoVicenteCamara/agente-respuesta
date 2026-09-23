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
from backend.voice import notifier
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
            text = notifier.build_spoken_update(json.loads(message["data"]))
        except (json.JSONDecodeError, TypeError):
            text = None
        if not text:
            continue
        logger.info("Notificación por voz: %s", text)
        try:
            await session.generate_reply(instructions=text, allow_interruptions=True)
        except Exception:  # noqa: BLE001
            logger.exception("Fallo al inyectar la actualización por voz")


server = AgentServer()


@server.rtc_session(agent_name=settings.agent_name)
async def voice_entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    await session.start(room=ctx.room, agent=OrchestratorAgent())
    asyncio.create_task(_listen_for_updates(session))
    await session.generate_reply(instructions=WELCOME_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(server)