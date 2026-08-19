"""
The agent loop.

The model is given ONE tool (search_news) and told what Kate cares about.
It decides for itself: what to search, how many results are worth
including, whether anything outside politics/tech is worth a slot, and
when it's done -- at which point it stops calling tools and writes the
final report as plain text.
"""

import anthropic
from news_agent.tools import search_news

MODEL = "claude-sonnet-5"
MAX_ITERATIONS = 6  # safety guardrail so a confused agent can't loop forever

SYSTEM_PROMPT = """\
You are Kate's personal daily news curator.

Her core interests are POLITICS and TECH news. You also have discretion
to include up to 1-2 other stories if something is genuinely significant
or unusually interesting -- don't pad the report with filler just to fill
a quota.

Use the search_news tool to find current articles. You decide:
- what specific queries to run (you can run several)
- which articles are actually worth including (skip routine/low-value stories)
- whether anything outside politics/tech earns a spot today

Aim for around 4-6 articles per section (politics and tech) so the
briefing has enough breadth to be worth reading -- don't stop after
just one or two per topic unless the news is genuinely thin that day.

When you have enough information, call finalize_report with your
curated selections instead of calling search_news again. The whole
report should be readable in 8-12 minutes (roughly 1200-2000 words
across all sections combined) -- keep summary_text to 1-3 tight
sentences per article so the extra headlines don't bloat the length.

In finalize_report you must also provide:
- tldr: one sentence naming the 2-4 biggest headlines of the day,
  written for someone with 30 seconds who may not read further.
- top_story: the single most significant article across ALL topics
  today, regardless of which section it belongs to -- pick this by
  real-world importance, not by which topic happens to be listed
  first. It should also appear normally within its section.

You may be given a list of stories already covered in recent days.
Do not repeat one of those unless there's a genuine new development
-- if so, make the summary explicitly about what changed (e.g. "Update:
...") rather than restating what was already reported.

If a search_news call returns an error, don't retry it endlessly --
try a different query or proceed to finalize_report with whatever
good results you already have.
"""

TOOLS = [
    {
        "name": "search_news",
        "description": "Search for recent news articles matching a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query, e.g. 'US politics today'"},
                "max_results": {"type": "integer", "description": "How many articles to return", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "finalize_report",
        "description": "Submit the final curated briefing once you've gathered and selected enough articles. Calling this ends the process.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tldr": {
                    "type": "string",
                    "description": "One sentence naming the 2-4 biggest headlines of the day.",
                },
                "top_story": {
                    "type": "object",
                    "description": "The single most significant article across all topics today.",
                    "properties": {
                        "title": {"type": "string"},
                        "summary_text": {"type": "string"},
                        "source": {"type": "string"},
                        "url": {"type": "string"},
                        "topic": {"type": "string", "description": "Which section this story also belongs to"},
                    },
                    "required": ["title", "summary_text", "source", "url", "topic"],
                },
                "sections": {
                    "type": "array",
                    "description": "One entry per topic (e.g. Politics, Tech, plus any discretionary topic).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "articles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "summary_text": {"type": "string", "description": "1-3 sentence summary in your own words"},
                                        "source": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                    "required": ["title", "summary_text", "source", "url"],
                                },
                            },
                        },
                        "required": ["topic", "articles"],
                    },
                },
            },
            "required": ["tldr", "top_story", "sections"],
        },
    },
]


def run_agent(client: anthropic.Anthropic, recent_history: list[dict] | None = None) -> dict:
    """Runs the agent loop and returns the final report as structured data
    (see finalize_report's schema above) -- not freeform text.

    recent_history: optional list of {title, url, date} for articles sent
    in prior days, used to steer the agent away from repeats.
    """
    user_message = "Give me today's personalized news briefing."
    if recent_history:
        covered = "\n".join(f"- {a['title']} ({a['date']})" for a in recent_history)
        user_message += (
            "\n\nStories already covered in recent days -- don't repeat these "
            "unless there's a genuine new development:\n" + covered
        )

    messages = [{"role": "user", "content": user_message}]

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls = [block for block in response.content if block.type == "tool_use"]

        finalize_call = next((c for c in tool_calls if c.name == "finalize_report"), None)
        if finalize_call:
            return finalize_call.input  # {"sections": [...]}

        if not tool_calls:
            # Model stopped without finalizing -- shouldn't normally happen
            # since we require finalize_report, but guard against it anyway.
            return {"sections": [], "error": "Model stopped without calling finalize_report."}

        # The model wants to search. Append its request, execute each
        # tool call, and feed the results back for the next iteration.
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for call in tool_calls:
            if call.name == "search_news":
                try:
                    result = search_news(**call.input)
                except Exception as e:
                    # e.g. NewsAPI rate limit or network failure -- tell the
                    # model so it can proceed with whatever it already has,
                    # rather than crashing the whole run over one bad query.
                    result = {"error": f"search_news failed: {e}"}
            else:
                result = {"error": f"unknown tool {call.name}"}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})

    return {"sections": [], "error": "Agent hit the iteration limit without finishing."}
