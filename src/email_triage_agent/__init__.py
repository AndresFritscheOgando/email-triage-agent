import argparse


def run(index: int) -> None:
    """Run the full agent on one example email and print what it did."""
    from langgraph.errors import GraphRecursionError

    from email_triage_agent.agent import graph
    from email_triage_agent.examples import TRIAGE_EXAMPLES

    email = TRIAGE_EXAMPLES[index - 1]
    print(f"Email {index}: {email['subject']}  (from {email['author']})")

    try:
        # Each agent loop is 2 steps (llm_call + tools); cap it so a confused
        # small model can't loop forever.
        result = graph.invoke({"email_input": email}, {"recursion_limit": 20})
    except GraphRecursionError:
        print("Agent hit the step limit without calling Done.")
        return

    print(f"Triage: {result['classification_decision']}")
    for msg in result.get("messages", [])[1:]:
        for call in getattr(msg, "tool_calls", None) or []:
            print(f"  -> {call['name']}({call['args']})")
        if msg.type == "tool":
            print(f"  <- {msg.content}")


def main() -> None:
    from email_triage_agent.examples import TRIAGE_EXAMPLES

    parser = argparse.ArgumentParser(prog="email-triage-agent")
    commands = parser.add_subparsers(dest="command", required=True)

    run_cmd = commands.add_parser("run", help="run the full agent on an example email")
    run_cmd.add_argument(
        "example",
        type=int,
        nargs="?",
        default=1,
        choices=range(1, len(TRIAGE_EXAMPLES) + 1),
        metavar=f"N (1-{len(TRIAGE_EXAMPLES)})",
        help="which example email to process (default: 1)",
    )
    commands.add_parser("eval", help="score the triage router on the labelled examples")

    args = parser.parse_args()
    if args.command == "run":
        run(args.example)
    else:
        from email_triage_agent.triage import evaluate

        evaluate()
