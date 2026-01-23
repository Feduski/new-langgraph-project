from __future__ import annotations

from typing import Annotated, Any, Dict
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage, AIMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime


class Context(TypedDict, total=False):
    my_configurable_param: str


class State(TypedDict):
    # clave: el UI espera esto
    messages: Annotated[list[AnyMessage], add_messages]


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    cfg = (runtime.context or {}).get("my_configurable_param", "NO_CFG")
    # Respuesta dummy para testear memoria/threads
    return {
        "messages": [AIMessage(content=f"OK. cfg={cfg}. Recibí {len(state['messages'])} mensajes.")]
    }


graph = (
    StateGraph(State, context_schema=Context)
    .add_node("call_model", call_model)
    .add_edge("__start__", "call_model")
    .compile(name="agent")
)
