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
from news_agent import history

if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "Set your ANTHROPIC_API_KEY environment variable first.\n"
            "Get one at https://console.anthropic.com"
        )

    client = anthropic.Anthropic(api_key=api_key)
    report = run_agent(client, recent_history=history.recent_articles())

    if report.get("error"):
        print(f"Agent didn't finish cleanly: {report['error']}")

    html = render_html(report)
    n_articles = sum(len(s["articles"]) for s in report.get("sections", []))
    print(f"Report ready: {len(report.get('sections', []))} sections, {n_articles} articles.")

    if report.get("sections"):
        all_articles = [a for s in report["sections"] for a in s["articles"]]
        history.record_sent(all_articles)

    if os.environ.get("EMAIL_FROM") and os.environ.get("EMAIL_APP_PASSWORD"):
        send_email(html)
        print("Emailed to", os.environ.get("EMAIL_TO", os.environ["EMAIL_FROM"]))
    else:
        with open("preview.html", "w") as f:
            f.write(html)
        print("EMAIL_FROM/EMAIL_APP_PASSWORD not set — wrote preview.html instead of sending.")
