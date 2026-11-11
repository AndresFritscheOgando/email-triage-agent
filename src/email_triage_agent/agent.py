"""The email agent: triage first, then reply only if the email needs it.

    START -> triage_router --respond--------> response_agent -> END
                          \\--ignore/notify--> END
"""

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from email_triage_agent.response_agent import response_agent
from email_triage_agent.state import State
from email_triage_agent.triage import classify
from email_triage_agent.utils import format_email


def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    """Classify the email and route it.

    "respond" hands the email to the response agent; "ignore" and "notify"
    end the run (notify is where a real app would alert the user).
    """
    email = state["email_input"]
    try:
        classification = classify(email).classification
    except Exception:
        # The small model sometimes returns malformed output. Surface the
        # email to the user rather than dropping it or auto-replying.
        classification = "notify"

    update: dict = {"classification_decision": classification}
    if classification == "respond":
        update["messages"] = [
            HumanMessage(f"Respond to this email:\n\n{format_email(email)}")
        ]
        return Command(goto="response_agent", update=update)
    return Command(goto=END, update=update)


builder = StateGraph(State)
builder.add_node("triage_router", triage_router)
builder.add_node("response_agent", response_agent)
builder.add_edge(START, "triage_router")

graph = builder.compile()
