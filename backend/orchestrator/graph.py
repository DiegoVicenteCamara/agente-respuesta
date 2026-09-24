"""Grafo supervisor en LangGraph.

Planifica el objetivo, lanza subagentes de investigación en paralelo (fan-out
con ``Send``) y consolida un informe final. Cada nodo publica eventos en Redis.
"""

import logging
import operator
import time
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from backend.bus import redis_client
from backend.orchestrator import nodes

logger = logging.getLogger(__name__)


class ResearchState(TypedDict, total=False):
    task_id: str
    goal: str
    planner_model: str
    subtasks: list[str]
    results: Annotated[list[dict], operator.add]
    progress: Annotated[list[str], operator.add]
    analysis: str


async def _publish(
    task_id: str,
    event_type: str,
    agent: str,
    message: str,
    priority: str = "info",
    subtask: str | None = None,
    goal: str | None = None,
) -> None:
    try:
        payload = {
            "task_id": task_id,
            "type": event_type,
            "agent": agent,
            "message": message,
            "priority": priority,
            "ts": int(time.time() * 1000),
        }
        if subtask is not None:
            payload["subtask"] = subtask
        if goal is not None:
            payload["goal"] = goal
        await redis_client.publish_event(payload)
    except ConnectionError:
        logger.warning("Redis no disponible; el evento «%s» no se notificó por voz", event_type)
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo publicar el evento «%s» en Redis", event_type)


async def planner(state: ResearchState) -> dict:
    subtasks = await nodes.plan_subtasks(state["goal"], state.get("planner_model"))
    await _publish(
        state["task_id"],
        "plan_ready",
        "planner",
        f"He descompuesto la tarea en {len(subtasks)} frentes de investigación.",
        goal=state["goal"],
    )
    return {"subtasks": subtasks}


async def research(state: ResearchState) -> dict:
    subtask = state["subtask"]
    await _publish(
        state["task_id"],
        "subtask_started",
        "research",
        f"El subagente de investigación ha empezado sobre «{subtask}».",
        priority="silent",
        subtask=subtask,
    )
    snippets = await nodes.run_search(subtask)
    summary = await nodes.chat("\n".join(snippets), nodes.SUMMARY_SYSTEM_PROMPT)
    if not summary:
        summary = "Hallazgos de la búsqueda:\n" + "\n".join(snippets)[:600]
    await _publish(
        state["task_id"],
        "subtask_done",
        "research",
        f"El subagente de investigación ha terminado sobre «{subtask}».",
        subtask=subtask,
    )
    return {
        "results": [{"subtask": subtask, "snippets": snippets, "summary": summary}],
        "progress": [subtask],
    }


async def synthesize(state: ResearchState) -> dict:
    results = state.get("results") or []
    if results:
        merged = "\n\n".join(r["summary"] for r in results)
        analysis = await nodes.chat(merged, nodes.FINAL_SYSTEM_PROMPT)
        if not analysis:
            analysis = "Resumen de los subagentes:\n" + merged[:600]
    else:
        analysis = "No he podido obtener resultados para esta investigación."
    await _publish(
        state["task_id"], "analysis_ready", "synthesize", analysis, priority="info"
    )
    return {"analysis": analysis}


def _fan_out(state: ResearchState) -> list[Send]:
    subtasks = state.get("subtasks") or [state["goal"]]
    return [
        Send(
            "research",
            {"task_id": state["task_id"], "goal": state["goal"], "subtask": sub},
        )
        for sub in subtasks
    ]


def build_graph():
    builder = StateGraph(ResearchState)
    builder.add_node("planner", planner)
    builder.add_node("research", research)
    builder.add_node("synthesize", synthesize)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges("planner", _fan_out, ["research"])
    builder.add_edge("research", "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()