from __future__ import annotations

from typing import Dict, Any
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from langgraph.graph import StateGraph, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition


class Context(TypedDict, total=False):
    system_prompt: str


# 1) Tool
tavily = TavilySearch(
    max_results=5,
)

tools = [tavily]
tool_node = ToolNode(tools)


# 2) Modelo con tools
llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)


async def chatbot(state: MessagesState, runtime) -> Dict[str, Any]:
    system_prompt = (getattr(runtime, "context", None) or {}).get(
        "system_prompt",
        "Sos un asistente. Si necesitás info actual, usá la herramienta de búsqueda.",
    )

    # Insertamos system al inicio (sin duplicar en cada vuelta)
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [{"role": "system", "content": system_prompt}] + messages

    resp = await llm_with_tools.ainvoke(messages)
    return {"messages": [resp]}


graph = (
    StateGraph(MessagesState, context_schema=Context)
    .add_node("chatbot", chatbot)
    .add_node("tools", tool_node)
    .add_edge("__start__", "chatbot")
    # si el modelo pidió tools -> va a tools, si no -> END
    .add_conditional_edges("chatbot", tools_condition, {"tools": "tools", END: END})
    .add_edge("tools", "chatbot")
    .compile(name="agent")
)
