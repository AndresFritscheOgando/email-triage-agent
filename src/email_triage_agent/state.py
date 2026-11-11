from typing import Literal, TypedDict

from langgraph.graph import MessagesState


class EmailData(TypedDict):
    """One incoming email. These keys match the placeholders in the prompts."""

    author: str
    to: str
    subject: str
    email_thread: str


class State(MessagesState):
    email_input: EmailData
    classification_decision: Literal["ignore", "respond", "notify"]
