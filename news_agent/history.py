"""
Tracks which articles have already been sent, so tomorrow's agent can
avoid repeating a story it covered yesterday unless there's a genuine
update. Stored as a flat JSON file keyed by date.
"""

import json
from datetime import date, timedelta
from pathlib import Path

HISTORY_PATH = Path(__file__).resolve().parent.parent / "history.json"
RETENTION_DAYS = 7


def _load() -> dict:
    if not HISTORY_PATH.exists():
        return {}
    with open(HISTORY_PATH) as f:
        return json.load(f)


def recent_articles(days: int = RETENTION_DAYS) -> list[dict]:
    """Returns [{title, url, date}, ...] for articles sent in the last `days` days."""
    history = _load()
    cutoff = date.today() - timedelta(days=days)
    out = []
    for date_str, articles in history.items():
        if date.fromisoformat(date_str) < cutoff:
            continue
        for a in articles:
            out.append({"title": a["title"], "url": a["url"], "date": date_str})
    return out


def record_sent(articles: list[dict]) -> None:
    """Appends today's sent articles (list of {title, url}) and prunes old entries."""
    history = _load()
    today_str = date.today().isoformat()
    history[today_str] = [{"title": a["title"], "url": a["url"]} for a in articles]

    cutoff = date.today() - timedelta(days=RETENTION_DAYS)
    history = {d: a for d, a in history.items() if date.fromisoformat(d) >= cutoff}

    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
