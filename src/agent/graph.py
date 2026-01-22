"""
LangGraph chat graph (template -> real LLM).

- Input:  {"messages": [{"role":"user","content":"hola"}]}
- Output: {"messages": [..., {"role":"assistant","content":"..."}]}

Context:
- my_configurable_param: Reply always with jokes (system prompt-ish)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import StateGraph, END
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class Context(TypedDict):
    """
    Set these when creating assistants OR when invoking the graph.
    """
    my_configurable_param: str


@dataclass
class State:
    """
    Chat-style state.
    """
    messages: List[Dict[str, str]] = field(default_factory=list)


_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


def _to_lc_messages(chatml: List[Dict[str, str]], system_text: str | None) -> List[Any]:
    msgs: List[Any] = []
    if system_text:
        msgs.append(SystemMessage(content=system_text))

    for m in chatml:
        role = (m.get("role") or "").lower()
        content = m.get("content") or ""
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
        else:
            # Si viene algo raro (tool/system), lo tratamos como "user" para no romper
            msgs.append(HumanMessage(content=f"[{role}] {content}"))
    return msgs


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    system_text = (runtime.context or {}).get("my_configurable_param")
    lc_messages = _to_lc_messages(state.messages, system_text)

    resp = await _llm.ainvoke(lc_messages)
    assistant_msg = {"role": "assistant", "content": resp.content}

    return {"messages": state.messages + [assistant_msg]}


graph = (
    StateGraph(State, context_schema=Context)
    .add_node("call_model", call_model)
    .set_entry_point("call_model")
    .add_edge("call_model", END)
    .compile(name="Chat Graph")
)
