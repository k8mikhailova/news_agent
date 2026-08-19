"""
Entry point. For now this just prints the report to your console --
we'll wire up email delivery once this part is producing reports you're
happy with. Getting the content right is the hard part; email is just
plumbing on top.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # must run before importing news_agent.tools, which reads NEWS_API_KEY at import time

import anthropic
from news_agent.agent import run_agent
from news_agent.render import render_html
from news_agent.mailer import send_email
from news_agent import history, tools


def _alert(subject: str, message: str) -> None:
    """Tells Kate something's wrong instead of sending a fake/broken briefing."""
    print(f"ALERT: {subject} -- {message}")
    if os.environ.get("EMAIL_FROM") and os.environ.get("EMAIL_APP_PASSWORD"):
        send_email(f"<p>{message}</p>", subject=f"News Agent Alert: {subject}")


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        _alert("Missing ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY isn't set, so no briefing could be generated.")
        raise SystemExit(1)

    if tools.MOCK_MODE:
        _alert(
            "NEWS_API_KEY missing",
            "NEWS_API_KEY isn't set, so the agent would only see placeholder test "
            "articles. Refusing to send a fake briefing -- set NEWS_API_KEY and re-run.",
        )
        raise SystemExit(1)

    client = anthropic.Anthropic(api_key=api_key)
    try:
        report = run_agent(client, recent_history=history.recent_articles())
    except anthropic.APIError as e:
        _alert(
            "Anthropic API call failed",
            f"{e}\nIf this is a low-balance or rate-limit error, top up at "
            "https://console.anthropic.com and re-run.",
        )
        raise SystemExit(1)

    if report.get("error") or not report.get("sections"):
        _alert(
            "Agent didn't produce a usable report",
            f"{report.get('error', 'no sections returned')}\nNot sending an empty/broken email.",
        )
        raise SystemExit(1)

    html = render_html(report)
    n_articles = sum(len(s["articles"]) for s in report.get("sections", []))
    print(f"Report ready: {len(report.get('sections', []))} sections, {n_articles} articles.")

    all_articles = [a for s in report["sections"] for a in s["articles"]]
    history.record_sent(all_articles)

    if os.environ.get("EMAIL_FROM") and os.environ.get("EMAIL_APP_PASSWORD"):
        send_email(html)
        print("Emailed to", os.environ.get("EMAIL_TO", os.environ["EMAIL_FROM"]))
    else:
        with open("preview.html", "w") as f:
            f.write(html)
        print("EMAIL_FROM/EMAIL_APP_PASSWORD not set — wrote preview.html instead of sending.")
