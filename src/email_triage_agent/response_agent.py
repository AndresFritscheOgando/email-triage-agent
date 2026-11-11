"""Response agent: an LLM <-> tools loop that replies to one email.

    START -> llm_call -> tools -> llm_call -> ... -> END
                  \\-> END (no tool call)   \\-> END (Done was called)
"""

import os
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from email_triage_agent.prompts import build_agent_system_prompt
from email_triage_agent.state import State
from email_triage_agent.tools import TOOLS, TOOLS_BY_NAME

# Tool calling needs a stronger model than triage. Override with e.g.
# AGENT_MODEL=qwen2.5:7b once it's pulled in Ollama.
AGENT_MODEL = os.getenv("AGENT_MODEL", "qwen2.5:7b")

llm = init_chat_model(model=AGENT_MODEL, model_provider="ollama", temperature=0.0)
# Ollama ignores tool_choice, so the prompt also tells the model to always
# call a tool. should_continue() handles the case where it doesn't.
llm_with_tools = llm.bind_tools(TOOLS, tool_choice="any")


MAX_NUDGES = 2
NUDGE = HumanMessage(
    "You must respond with a tool call. Call write_email to reply, "
    "or Done if the reply has already been sent."
)


def llm_call(state: State) -> dict:
    """Ask the model for the next tool call.

    Small models sometimes answer with plain (or empty) text instead of a
    tool call. Retry a couple of times with a reminder; the reminder is not
    saved to state.
    """
    messages = [SystemMessage(build_agent_system_prompt()), *state["messages"]]
    response = llm_with_tools.invoke(messages)
    for _ in range(MAX_NUDGES):
        if response.tool_calls:
            break
        response = llm_with_tools.invoke([*messages, NUDGE])
    return {"messages": [response]}


def tool_node(state: State) -> dict:
    """Run every tool call in the last AI message.

    Errors (e.g. bad arguments from a small model) go back to the model as
    a ToolMessage so it can fix the call, instead of crashing the graph.
    """
    results = []
    for call in state["messages"][-1].tool_calls:
        tool = TOOLS_BY_NAME.get(call["name"])
        if tool is None:
            content = f"Error: unknown tool '{call['name']}'."
        else:
            try:
                content = tool.invoke(call["args"])
            except Exception as exc:
                content = f"Error calling {call['name']}: {exc}. Fix the arguments and try again."
        results.append(
            ToolMessage(content=str(content), tool_call_id=call["id"], name=call["name"])
        )
    return {"messages": results}


def should_continue(state: State) -> Literal["tools", "__end__"]:
    """After the model speaks: run its tool calls, or stop if it made none."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def after_tools(state: State) -> Literal["llm_call", "__end__"]:
    """After tools ran: stop if the model called Done, otherwise loop."""
    last_ai = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage))
    if any(call["name"] == "Done" for call in last_ai.tool_calls):
        return END
    return "llm_call"


builder = StateGraph(State)
builder.add_node("llm_call", llm_call)
builder.add_node("tools", tool_node)
builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", should_continue)
builder.add_conditional_edges("tools", after_tools)

response_agent = builder.compile()
