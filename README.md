# Daily Outreach Bot

Finds local businesses, finds their contact email from their own website, and
sends your AI-automation pitch once per day, automatically, for free, on
GitHub Actions. Never emails the same address twice.

## What it does each run
1. Searches DuckDuckGo (free, no API key or billing account needed) for businesses matching `categories` x `cities` in `config.yaml`, filtering out directories/social platforms so it lands on the business's own site.
2. Skips any business already in `sent_log.csv`.
3. Visits each business's real website and looks for a contact email.
4. Sends the pitch email via your Yahoo account.
5. Logs the send so tomorrow's run skips it.
6. Commits the log back to the repo (this is what makes "no repeats" persist across days).

Note on the lead source: DuckDuckGo search results are noisier than a paid
Places API (some searches will surface fewer usable, non-directory sites) —
that's the trade-off for it being free with no billing account. The bot
already filters out common directories/social platforms and rate-limits its
own queries to avoid getting blocked.

## One-time setup (about 5 minutes)

### 1. Get a Yahoo App Password (required — your normal password won't work for SMTP)
- Yahoo Account → Account Security → turn on 2-step verification.
- Then "Generate app password" → choose "Other app" → name it "outreach-bot".
- Copy the 16-character password it gives you.

### 2. Push this folder to a GitHub repo
```
git init
git add .
git commit -m "Initial outreach bot"
git remote add origin <your-repo-url>
git push -u origin main
```

### 3. Add your secret in GitHub
Repo → Settings → Secrets and variables → Actions → New repository secret:
- `YAHOO_APP_PASSWORD` → your app password from step 1

### 4. Edit config.yaml
- Fill in `sender_physical_address` (legally required for compliant commercial email).
- Adjust `categories` and `cities` to your target market.
- Leave `exclude_eu_uk: true` unless you've decided you're comfortable with GDPR/PECR exposure.

### 5. Test it manually before trusting the schedule
Repo → Actions tab → "Daily Outreach" → "Run workflow" (this is the `workflow_dispatch` trigger).
Check `sent_log.csv` afterward to confirm it worked and didn't send anything you don't want it to.

The cron in `.github/workflows/daily-outreach.yml` then runs it automatically every day — no server, no local machine needed, completely free on GitHub's public-repo Actions minutes.

## Important limits to know about

- **Warm-up ramp**: the bot starts at `warmup_start_limit` (10/day) and increases by `warmup_increase_per_day` (10) until it hits `daily_send_limit` (100), rather than blasting 100 from day one. This exists specifically to protect your Yahoo account from being flagged — don't remove it.
- **Yahoo may still throttle or flag a personal account** doing this, regardless of warm-up. If sends start failing or you get a security alert, that's Yahoo's abuse detection. At that point switching the `send_email.py` sender to something built for bulk mail (e.g. Brevo's free 300/day API) is a five-minute swap — the rest of the bot doesn't need to change.
- **Email-finding will miss some businesses** — not every business lists an email on their site. Expect the bot to successfully email fewer than the number of candidates it finds; that's normal, it just moves to the next candidate.
- **Compliance**: the email template includes an unsubscribe line and identifies you as the sender, and the footer plugs in your physical address — check any "unsubscribe"/opt-out replies manually and keep a suppression list if someone asks to stop hearing from you (this bot doesn't currently auto-process replies).
