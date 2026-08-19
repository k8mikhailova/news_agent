"""
Turns the agent's structured report ({"tldr", "top_story", "sections"})
into an HTML email. Uses inline styles throughout because most email
clients strip <style> blocks or ignore external CSS.
"""

from datetime import date

WORDS_PER_MINUTE = 200

_TLDR_TEMPLATE = """
<div style="font-size: 14px; color: #333; line-height: 1.5; background: #f7f7f7;
            border-radius: 6px; padding: 12px 14px; margin-bottom: 24px;">
  <strong>Today in brief:</strong> {tldr}
</div>
"""

_TOP_STORY_TEMPLATE = """
<div style="margin-bottom: 32px; padding: 16px; border: 1px solid #eee; border-radius: 8px;">
  <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;
              color: #1a56db; font-weight: 700; margin-bottom: 8px;">Top Story</div>
  <a href="{url}" style="font-size: 19px; font-weight: 700; color: #1a56db; text-decoration: underline;">
    {title}
  </a>
  <div style="font-size: 13px; color: #888; margin-top: 2px;">{source}</div>
  <p style="font-size: 14px; color: #333; line-height: 1.5; margin: 8px 0 0 0;">
    {summary_text}
  </p>
  <a href="{url}" style="font-size: 13px; color: #1a56db; text-decoration: none;">Read full article &rarr;</a>
</div>
"""

_ARTICLE_TEMPLATE = """
<div style="margin-bottom: 18px;">
  <a href="{url}" style="font-size: 16px; font-weight: 600; color: #1a56db; text-decoration: underline;">
    {title}
  </a>
  <div style="font-size: 13px; color: #888; margin-top: 2px;">{source}</div>
  <p style="font-size: 14px; color: #333; line-height: 1.5; margin: 6px 0 0 0;">
    {summary_text}
  </p>
  <a href="{url}" style="font-size: 13px; color: #1a56db; text-decoration: none;">Read full article &rarr;</a>
</div>
"""

_SECTION_TEMPLATE = """
<div style="margin-bottom: 32px;">
  <h2 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em;
             color: #666; border-bottom: 2px solid #eee; padding-bottom: 8px; margin-bottom: 16px;">
    {topic}
  </h2>
  {articles_html}
</div>
"""

_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0; background: #f5f5f5;">
  <div style="max-width: 600px; margin: 0 auto; padding: 32px 24px; background: #ffffff;
              font-family: -apple-system, Helvetica, Arial, sans-serif;">
    <h1 style="font-size: 20px; margin: 0 0 4px 0; color: #1a1a1a;">Your Daily Briefing</h1>
    <div style="font-size: 13px; color: #999; margin-bottom: 20px;">{date_str} &middot; ~{read_minutes} min read</div>
    {tldr_html}
    {top_story_html}
    {sections_html}
    <div style="font-size: 12px; color: #bbb; margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee;">
      Curated by your news agent.
    </div>
  </div>
</body>
</html>
"""


def _word_count(report: dict) -> int:
    total = len(report.get("tldr", "").split())
    top_story = report.get("top_story")
    if top_story:
        total += len(top_story.get("summary_text", "").split())
    for section in report.get("sections", []):
        for a in section["articles"]:
            total += len(a["summary_text"].split())
    return total


def render_html(report: dict) -> str:
    top_story = report.get("top_story")
    top_story_url = top_story["url"] if top_story else None

    sections_html = ""
    for section in report.get("sections", []):
        articles = [a for a in section["articles"] if a["url"] != top_story_url]
        if not articles:
            continue
        articles_html = "".join(
            _ARTICLE_TEMPLATE.format(
                url=a["url"], title=a["title"],
                source=a["source"], summary_text=a["summary_text"],
            )
            for a in articles
        )
        sections_html += _SECTION_TEMPLATE.format(topic=section["topic"], articles_html=articles_html)

    tldr_html = _TLDR_TEMPLATE.format(tldr=report["tldr"]) if report.get("tldr") else ""
    top_story_html = _TOP_STORY_TEMPLATE.format(**top_story) if top_story else ""

    read_minutes = max(1, round(_word_count(report) / WORDS_PER_MINUTE))

    return _PAGE_TEMPLATE.format(
        date_str=date.today().strftime("%A, %B %d, %Y"),
        read_minutes=read_minutes,
        tldr_html=tldr_html,
        top_story_html=top_story_html,
        sections_html=sections_html,
    )
