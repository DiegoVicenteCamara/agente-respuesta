"""Nodos del grafo LangGraph: planificador, investigación y síntesis.

Cada nodo publica eventos en Redis (canal ``agent_updates``) que el agente de
voz traduce en interrupciones proactivas habladas.
"""

import asyncio
import json
import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

PLAN_PROMPT = (
    "Descompón el siguiente objetivo en una lista de 2 a 4 subtareas de "
    'investigación independientes. Responde únicamente con JSON válido de la '
    'forma {"subtasks": ["...", "..."]}, sin texto adicional.\n\nObjetivo: '
)

SUMMARY_SYSTEM_PROMPT = (
    "Eres un subagente de análisis. Resume la información recibida en un "
    "párrafo claro y conciso en español, citando lo más relevante."
)

FINAL_SYSTEM_PROMPT = (
    "Actúas como el agente supervisor del equipo. Sintetiza los hallazgos de "
    "tus subagentes en un informe final breve, en español, listo para ser leído "
    "en voz alta."
)


def _build_llm(model: str | None = None) -> Any:
    if not settings.openai_api_key:
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model or settings.openai_planner_model, temperature=0.2, max_retries=0
    )


async def chat(text: str, system: str, model: str | None = None) -> str:
    """Envía un mensaje a un LLM genérico; si no hay clave o falla, devuelve vacío."""
    llm = _build_llm(model)
    if llm is None:
        return ""
    from langchain_core.messages import HumanMessage, SystemMessage

    try:
        resp = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=text)]
        )
        return str(resp.content).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM no disponible (%s); usando contenido bruto", exc)
        return ""


def _parse_subtasks(text: str, goal: str) -> list[str]:
    try:
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start : end + 1])
        subs = [str(s).strip() for s in data.get("subtasks", []) if str(s).strip()]
        if subs:
            return subs[:4]
    except Exception:  # noqa: BLE001
        pass
    return [goal]


async def plan_subtasks(goal: str, model: str | None = None) -> list[str]:
    plan = await chat(
        PLAN_PROMPT + goal,
        "Eres un planificador de tareas de investigación.",
        model=model,
    )
    return _parse_subtasks(plan, goal)


async def run_search(query: str, max_results: int = 5) -> list[str]:
    """Búsqueda web con Tavily si hay clave; si no, DuckDuckGo."""
    if settings.tavily_api_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    TAVILY_ENDPOINT,
                    json={
                        "api_key": settings.tavily_api_key,
                        "query": query,
                        "max_results": max_results,
                    },
                )
                resp.raise_for_status()
            results = resp.json().get("results", [])
            return [
                f"{r.get('title', '')}: {r.get('content', '')[:500]}" for r in results
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tavily falló (%s); probando DuckDuckGo", exc)
    return await _duckduckgo(query, max_results)


async def _duckduckgo(query: str, max_results: int) -> list[str]:
    from duckduckgo_search import DDGS

    def _run() -> list[str]:
        with DDGS() as ddgs:
            rows = ddgs.text(query, max_results=max_results) or []
        return [f"{r.get('title', '')}: {r.get('body', '')[:500]}" for r in rows]

    return await asyncio.to_thread(_run)