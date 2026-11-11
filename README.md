# email-triage-agent

A local email assistant built with [LangGraph](https://github.com/langchain-ai/langgraph) and [Ollama](https://ollama.com). It reads an email, decides whether it needs attention, and drafts a reply using tools when it does.

```
START -> triage_router --respond--------> response_agent -> END
                      \--ignore/notify--> END
```

1. **Triage router** (`triage.py`): a small model sorts each email into `ignore`, `notify`, or `respond` using structured output.
2. **Response agent** (`response_agent.py`): for `respond` emails, an LLM/tool loop calls `write_email`, `schedule_meeting`, and `check_calendar_availability` until it calls `Done`.

The tools are placeholders. They return canned strings and don't send email or touch a calendar.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) running locally, with the models pulled:

```sh
ollama pull qwen2.5:3b   # triage
ollama pull qwen2.5:7b   # response agent
```

## Setup

```sh
uv sync
```

## Usage

```sh
# Run the full agent on example email N (1-16, default 1)
uv run email-triage-agent run 2

# Score the triage router against the 16 labelled examples
uv run email-triage-agent eval
```

`run` prints the triage decision and every tool call the agent makes. `eval` prints PASS/FAIL per email and an overall accuracy.

## Configuration

Settings are read from the environment. A `.env` file in the project root is loaded automatically, and real environment variables take precedence.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRIAGE_MODEL` | `qwen2.5:3b` | Ollama model for the triage router |
| `AGENT_MODEL` | `qwen2.5:7b` | Ollama model for the response agent (needs reliable tool calling) |
| `LANGSMITH_TRACING` | unset | Set to `true` to trace runs in LangSmith |
| `LANGSMITH_API_KEY` | unset | LangSmith API key |
| `LANGSMITH_PROJECT` | unset | LangSmith project name |

To change who the assistant works for or how emails are classified, edit `DEFAULT_BACKGROUND` and `DEFAULT_TRIAGE_RULES` in `prompts.py`.

## Project layout

```
src/email_triage_agent/
├── __init__.py        # CLI entry point (run, eval) and .env loading
├── agent.py           # Top-level graph: triage router -> response agent
├── triage.py          # Triage classifier and evaluation
├── response_agent.py  # LLM <-> tools loop
├── tools.py           # Placeholder tools
├── prompts.py         # System prompts, background, and triage rules
├── schemas.py         # Structured output schema for triage
├── state.py           # Graph state and email types
├── examples.py        # Labelled example emails
└── utils.py           # Email formatting helper
```

## Handling small-model failures

Small local models don't always behave, so the graph has some guards:

- Malformed triage output falls back to `notify`, so the email is surfaced to you instead of being dropped or answered automatically.
- If the agent replies without a tool call, it gets up to two reminders to use one.
- Tool errors go back to the model as messages so it can fix its arguments.
- `run` caps the agent at 20 graph steps.
