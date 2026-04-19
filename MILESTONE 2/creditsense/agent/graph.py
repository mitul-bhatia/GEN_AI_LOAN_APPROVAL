from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from .nodes import (
    conversation_node,
    guardrail_node,
    policy_node,
    rag_retriever_node,
    report_node,
    translate_node,
)
from .state import AgentState, make_initial_state


def _after_guardrail(state: AgentState) -> str:
    return "conversation" if state.get("is_finance_query", True) else END


def _after_conversation(state: AgentState) -> str:
    return (
        "rag_retriever"
        if state.get("profile_complete", False) and state.get("report_requested", False)
        else END
    )


@lru_cache(maxsize=1)
def get_compiled_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("policy", policy_node)
    graph.add_node("report", report_node)
    graph.add_node("translate", translate_node)

    graph.set_entry_point("guardrail")
    graph.add_conditional_edges(
        "guardrail",
        _after_guardrail,
        {
            "conversation": "conversation",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "conversation",
        _after_conversation,
        {
            "rag_retriever": "rag_retriever",
            END: END,
        },
    )
    graph.add_edge("rag_retriever", "policy")
    graph.add_edge("policy", "report")
    graph.add_edge("report", "translate")
    graph.add_edge("translate", END)

    return graph.compile()


def run_turn(state: AgentState) -> AgentState:
    """Run one agent turn and return fully merged state (no field loss)."""
    graph = get_compiled_graph()
    result = graph.invoke(state)

    # LangGraph may return a partial state when using TypedDict without reducers.
    # Manually merge: start from original state, then overlay every non-None result key.
    merged: AgentState = dict(state)  # type: ignore[assignment]
    for key, value in result.items():
        if value is not None:
            merged[key] = value  # type: ignore[literal-required]

    return merged


__all__ = ["make_initial_state", "run_turn", "get_compiled_graph"]
