# AI agent: a personalized news briefing

## What this is

An agent that decides, on its own, what news is worth telling you about.
It's given one tool (`search_news`) and a goal (politics + tech, plus
discretion for anything else genuinely interesting, fit into an 8-12
minute read) — then it decides what to search, what to include, when
it's done, which single story is the day's most important, and writes
a one-sentence TL;DR. That decision-making is what makes it an agent
rather than a fixed script.

It runs automatically every morning via GitHub Actions and emails you
the result.

## Files

- `news_agent/tools.py` — the search tool. Runs in **mock mode**
  automatically if `NEWS_API_KEY` isn't set, returning canned fixture
  articles so the loop is testable without a key or real network
  calls. `main.py` refuses to send a real briefing while in mock mode
  (see Safety nets below) — it's for local testing only.
- `news_agent/agent.py` — the agent loop: calls the model, runs
  whatever tool it requests, feeds results back, repeats until the
  model calls `finalize_report` with its curated picks. That schema
  requires a `tldr` (one-sentence summary of the day), a `top_story`
  (the single most significant article across all topics), and
  `sections` (the full topic-grouped list). It's also told about
  stories sent in the last 7 days so it can avoid repeating them
  unless there's a genuine update.
- `news_agent/history.py` — persists each day's sent article
  titles/URLs to `history.json` (7-day retention), which is what
  makes the day-to-day de-duplication above possible.
- `news_agent/render.py` — turns the structured report into an HTML
  email: a TL;DR banner, a featured top story, a computed read-time
  estimate (word count ÷ 200wpm — not asked of the model, since that's
  the kind of arithmetic LLMs are bad at), then the topic sections.
- `news_agent/mailer.py` — sends the HTML report via Gmail SMTP.
- `news_agent/main.py` — the entry point. Orchestrates the above, and
  is where all the safety nets below live.
- `test_mailer.py` — an offline test using a mocked SMTP client (no
  real network or Gmail account needed). Already passing.

## Safety nets

Several ways this can fail, and what happens in each case — the
guiding principle is: **never send fake headlines or a blank email;
always tell Kate what broke.**

| Failure | What happens |
|---|---|
| `NEWS_API_KEY` not set (mock mode) | Refuses to run for real; emails an alert instead of sending mock/placeholder articles |
| Anthropic API fails (e.g. low credit balance, rate limit) | Catches the error, emails an alert with guidance to top up, exits cleanly (no raw traceback) |
| A `search_news` call fails mid-run (NewsAPI rate limit, network blip) | That one search returns an error to the agent, which works around it with whatever results it already has, instead of crashing the whole run |
| Agent hits its iteration limit or never calls `finalize_report` | Treated as a failure — emails an alert instead of sending an empty "Your Daily Briefing" |
| Any run fails in GitHub Actions | The workflow **disables its own daily schedule** so it doesn't keep failing (and retrying, and burning NewsAPI's free-tier quota) silently every morning. Fix the underlying issue, then re-enable with `gh workflow enable daily-briefing.yml` (or via the Actions tab in GitHub). Note this also disables manual `workflow_dispatch` runs until re-enabled. |

Alert emails only send if `EMAIL_FROM`/`EMAIL_APP_PASSWORD` are
configured — locally without them, alerts just print to the console
instead of crashing.

## Running it locally

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your real values:
   - `ANTHROPIC_API_KEY` — https://console.anthropic.com
   - `NEWS_API_KEY` — https://newsapi.org/register (free tier: 100
     requests/day, articles from roughly the last month only). Leave
     unset to run in mock mode and just check the loop/layout.
   - `EMAIL_FROM` / `EMAIL_APP_PASSWORD` / `EMAIL_TO` — see "Gmail
     setup" below. Leave unset to write `preview.html` instead of
     sending, so you can check the layout in a browser first.
3. Run it: `python -m news_agent.main`

### Gmail setup

Gmail blocks plain password login for SMTP, so you need an app
password:
1. Turn on 2-Step Verification on your Google account
2. Generate an app password at https://myaccount.google.com/apppasswords
3. Use that 16-character code as `EMAIL_APP_PASSWORD`, not your normal
   password

## Scheduling: GitHub Actions (how it actually runs day to day)

The live schedule is `.github/workflows/daily-briefing.yml`, running
on GitHub's infrastructure — not dependent on any local machine being
awake. It:
1. Checks out the repo, installs dependencies
2. Runs `python -m news_agent.main` with secrets injected as env vars
3. Commits the updated `history.json` back to the repo (Actions
   runners are stateless between runs, so without this step, the
   day-to-day de-dup would reset every run)
4. On failure, disables its own schedule (see Safety nets)

**Setup** (already done for this repo, documented here for
reference/future repos):
```
gh secret set ANTHROPIC_API_KEY --body "..."
gh secret set NEWS_API_KEY --body "..."
gh secret set EMAIL_FROM --body "..."
gh secret set EMAIL_APP_PASSWORD --body "..."
gh secret set EMAIL_TO --body "..."
```

**Timing caveat:** the cron schedule (`0 15 * * *`) is in UTC and
doesn't observe daylight saving. It's currently set for 8:00 AM
Pacific *Daylight* Time; once clocks fall back to Pacific Standard
Time this will fire at 7:00 AM local instead, unless the cron string
is manually changed to `0 16 * * *` for the winter half of the year.

**Manual test run:** `gh workflow run daily-briefing.yml`, then
`gh run watch` to follow it.

## Alternative: local scheduling with launchd (currently unused)

Before moving to GitHub Actions, this ran locally via macOS's
`launchd` (`com.kate.newsagent.plist` + `run_agent.sh`). That setup
still exists in the repo but is **currently disabled** — GitHub
Actions is the live scheduler. Reasons you might prefer this instead:
no GitHub account/repo needed, everything stays on your machine. The
tradeoff: **it only fires if your Mac is awake** — a closed/sleeping
laptop at 8 AM means the job runs whenever it next wakes, not on time.

To use it instead of (or in addition to) GitHub Actions:
1. Confirm the paths in `com.kate.newsagent.plist` match this
   project's actual location and your username
2. `mkdir -p logs`
3. `cp com.kate.newsagent.plist ~/Library/LaunchAgents/`
4. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kate.newsagent.plist`
5. Test immediately: `launchctl kickstart gui/$(id -u)/com.kate.newsagent`,
   then check `logs/stdout.log` and `logs/stderr.log`

To stop it: `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.kate.newsagent.plist`

If you want your Mac to wake itself for this (only reliable when
plugged in): `sudo pmset repeat wakeorpoweron MTWRFSU 07:55:00`

If running both GitHub Actions and this at once, you'll get two
emails a day — pick one.
