# AI agent: a personalized news briefing

## What this is

An agent that decides, on its own, what news is worth telling you about.
It's given one tool (`search_news`) and a goal (politics + tech, plus
discretion for anything else genuinely interesting, fit into a 5-10
minute read) — then it decides what to search, what to include, and
when it's done. That decision-making is what makes it an agent rather
than a fixed script.

## Files

- `news_agent/tools.py` — the search tool. Runs in **mock mode**
  automatically until you add a `NEWS_API_KEY`, so you can test
  everything else first without needing a key yet.
- `news_agent/agent.py` — the actual agent loop: calls the model, runs
  whatever tool it requests, feeds results back, repeats until the
  model calls `finalize_report` with its curated, structured picks.
- `news_agent/render.py` — turns the structured report into a clean
  HTML email layout.
- `news_agent/mailer.py` — sends the HTML report via Gmail SMTP.
- `news_agent/main.py` — run this. Sends the email if credentials are
  set; otherwise writes `preview.html` so you can check it looks right
  first.
- `test_agent_loop.py`, `test_mailer.py` — offline tests using fake
  clients (no API key or real network needed). Already passing.

## Running it for real

1. `pip install -r requirements.txt`
2. Get an Anthropic API key: https://console.anthropic.com
   `export ANTHROPIC_API_KEY=your_key_here`
3. Run it in mock mode first (no news API key needed yet) to see the
   agent's *decision-making* and layout with fake articles:
   `python -m news_agent.main`
   → since email credentials aren't set yet, this writes `preview.html`
   instead of sending. Open it in a browser to check the layout.
4. When you're ready for real articles: get a free NewsAPI.org key
   (https://newsapi.org/register) and
   `export NEWS_API_KEY=your_key_here` — mock mode turns off
   automatically.
5. To actually receive it by email:
   - Turn on 2-Step Verification on your Google account
   - Generate an app password at https://myaccount.google.com/apppasswords
   - `export EMAIL_FROM=you@gmail.com`
   - `export EMAIL_APP_PASSWORD=your_16_char_app_password`
   - (optional) `export EMAIL_TO=someone_else@example.com` — defaults
     to sending to yourself
   - Run `python -m news_agent.main` again — it'll send instead of
     writing a preview.

## What's next (not built yet)

Nothing — email delivery and scheduling are both done. See below.

## Scheduling it to run daily at 8:00 AM (Mac)

macOS's native way to schedule background jobs is **launchd**, not cron
— cron still works but modern macOS gates it behind Full Disk Access
permissions that are annoying to grant correctly. Here's the setup:

1. Put this whole project folder somewhere permanent, e.g. `~/news_agent`
2. Create your real secrets file: `cp .env.example .env`, then fill in
   your actual API keys and app password (see steps above)
3. Create a logs folder: `mkdir ~/news_agent/logs`
4. Edit `com.kate.newsagent.plist` — replace `YOUR_USERNAME` (two
   places) with your actual Mac username and confirm the path matches
   where you put the project
5. Copy it into place and load it:
   ```
   cp com.kate.newsagent.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.kate.newsagent.plist
   ```
6. Test it immediately without waiting for 8am:
   ```
   launchctl start com.kate.newsagent
   ```
   Then check `logs/stdout.log` and `logs/stderr.log` for what happened.

**Important caveat:** launchd only fires if your Mac is awake. If your
laptop is closed or asleep at 8:00 AM, the job won't run until it wakes
up (it won't auto-catch-up). If you want your Mac to wake itself for
this:
```
sudo pmset repeat wakeorpoweron MTWRFSU 07:55:00
```
This wakes the Mac at 7:55 daily, five minutes before the job fires.
(It needs to be plugged in or have a battery for this to work reliably
depending on your Mac model — test it once and check.)

**To stop/uninstall later:**
```
launchctl unload ~/Library/LaunchAgents/com.kate.newsagent.plist
```

## Note on where this needs to run

This was drafted in a sandboxed environment with no internet access,
so the live API calls and actual email sending haven't been tested
end-to-end yet — only the offline logic has (all tests pass). The
wrapper script's env-loading logic was tested offline too; launchd
itself is Mac-only and can't be tested outside macOS. Run this on your
own Mac, or in Claude Code, where it can reach the real internet.
