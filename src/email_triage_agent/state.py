from langgraph.graph import MessagesState
from typing import Literal, TypedDict


class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]

class EmailData(TypedDict):
    id: str
    thread_id: str
    from_email: str
    subject: str
    page_content: str
    send_time: str
    to_email: str
