from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from email_triage_agent.examples import TRIAGE_EXAMPLES
from email_triage_agent.prompts import TRIAGE_USER_PROMPT, build_triage_system_prompt
from email_triage_agent.schemas import RouterSchema

llm = init_chat_model(model="qwen2.5:3b", model_provider="ollama", temperature=0.0)
llm_router = llm.with_structured_output(RouterSchema)

system_prompt = build_triage_system_prompt()


def classify(email: dict) -> RouterSchema:
    messages = [
        SystemMessage(system_prompt),
        HumanMessage(TRIAGE_USER_PROMPT.format(**email)),
    ]
    return llm_router.invoke(messages)


def main() -> None:
    correct = 0
    for i, email in enumerate(TRIAGE_EXAMPLES, start=1):
        expected = email["expected"]
        try:
            response = classify(email)
            got = response.classification
            reasoning = response.reasoning
        except Exception as exc:  # small models sometimes return malformed output
            got, reasoning = "ERROR", repr(exc)

        ok = got == expected
        correct += ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {i}. {email['subject']}")
        print(f"       expected={expected}  got={got}")
        if not ok:
            print(f"       reasoning: {reasoning}")

    total = len(TRIAGE_EXAMPLES)
    print(f"\n{correct}/{total} correct ({correct / total:.0%})")


if __name__ == "__main__":
    main()
