"""Helpers shared by the triage router and the response agent."""

from email_triage_agent.state import EmailData


def format_email(email: EmailData) -> str:
    """Render an email as plain text for the response agent."""
    return (
        f"From: {email['author']}\n"
        f"To: {email['to']}\n"
        f"Subject: {email['subject']}\n"
        f"\n"
        f"{email['email_thread']}"
    )
