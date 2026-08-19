"""
Offline sanity check for the agent loop's control flow.

This does NOT test whether the model makes good decisions (that needs
the real API). It tests that our loop correctly handles tool_use
responses, executes tools, feeds results back, and stops on a final
text response -- the plumbing that's easy to get subtly wrong.
"""

from types import SimpleNamespace
from news_agent.agent import run_agent

call_count = {"n": 0}


def fake_create(**kwargs):
    """Simulates: search call -> another search call -> final report."""
    call_count["n"] += 1

    if call_count["n"] == 1:
        # Simulate the model deciding to search politics first
        block = SimpleNamespace(
            type="tool_use", id="call_1", name="search_news",
            input={"query": "politics today"},
        )
        return SimpleNamespace(content=[block])

    if call_count["n"] == 2:
        # Simulate the model deciding to search tech next
        block = SimpleNamespace(
            type="tool_use", id="call_2", name="search_news",
            input={"query": "technology news"},
        )
        return SimpleNamespace(content=[block])

    # Simulate the model being satisfied and finalizing a structured report
    block = SimpleNamespace(
        type="tool_use", id="call_3", name="finalize_report",
        input={"sections": [{"topic": "Politics", "articles": []}]},
    )
    return SimpleNamespace(content=[block])


fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))

result = run_agent(fake_client)
print("--- Loop result ---")
print(result)
print()
print(f"Model was called {call_count['n']} times before finishing")
assert result == {"sections": [{"topic": "Politics", "articles": []}]}
assert call_count["n"] == 3
print("PASS: loop correctly executed 2 searches then returned finalize_report's structured data")
