from __future__ import annotations

from typing import Any, Dict
from typing_extensions import TypedDict

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph
from langgraph.graph.message import MessagesState


class Context(TypedDict, total=False):
    system_prompt: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


async def call_model(state: MessagesState, runtime) -> Dict[str, Any]:
    system_prompt = (getattr(runtime, "context", None) or {}).get(
        "system_prompt",
        "Sos un asistente útil. Respondé en una sola línea.",
    )

    # armamos el input “estándar”: system + historial
    messages = [{"role": "system", "content": system_prompt}]
    for m in state["messages"]:
        messages.append(m)

    resp = await llm.ainvoke(messages)

    return {"messages": [resp]}  # <- CLAVE: devuelve messages


graph = (
    StateGraph(MessagesState, context_schema=Context)
    .add_node("call_model", call_model)
    .add_edge("__start__", "call_model")
    .compile(name="agent")
)
