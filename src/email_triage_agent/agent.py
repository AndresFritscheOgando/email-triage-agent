from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from email_triage_agent.prompts import TRIAGE_USER_PROMPT, build_triage_system_prompt
from email_triage_agent.schemas import RouterSchema

llm = init_chat_model(model="qwen2.5:3b", model_provider="ollama", temperature=0.0)
llm_router = llm.with_structured_output(RouterSchema)

email = {
    "author": "Alice Smith <alice@company.com>",
    "to": "me@company.com",
    "subject": "Quick question about the API docs",
    "email_thread": "Hi, I noticed the /auth endpoint isn't documented. "
    "Was that intentional, or should we add it before the release? Thanks, Alice",
}

messages = [
    SystemMessage(build_triage_system_prompt()),
    HumanMessage(TRIAGE_USER_PROMPT.format(**email)),
]

response = llm_router.invoke(messages)
print(response.classification)
print(response.reasoning)
