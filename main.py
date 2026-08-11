"""
Daily outreach run:
1. Load config + dedup log
2. Find candidate leads via Google Places
3. Skip anyone already contacted
4. Find their email from their website
5. Send the pitch (respecting the warm-up ramp)
6. Log every send so tomorrow's run never repeats it
"""
import csv
import json
import os
import sys
from datetime import date, datetime

import yaml

from find_leads import find_leads
from find_email import find_email
from send_email import send_email

CONFIG_PATH = "config.yaml"
LOG_PATH = "sent_log.csv"
STATE_PATH = "state.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_sent_emails():
    if not os.path.exists(LOG_PATH):
        return set()
    with open(LOG_PATH, newline="") as f:
        return {row["email"].lower() for row in csv.DictReader(f)}


def append_log(rows):
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "business", "email", "status"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def load_state():
    if not os.path.exists(STATE_PATH):
        state = {"start_date": date.today().isoformat()}
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
        return state
    with open(STATE_PATH) as f:
        return json.load(f)


def todays_limit(cfg, state):
    start = datetime.fromisoformat(state["start_date"]).date()
    days_elapsed = (date.today() - start).days
    limit = cfg["warmup_start_limit"] + cfg["warmup_increase_per_day"] * days_elapsed
    return min(limit, cfg["daily_send_limit"])


def main():
    cfg = load_config()
    state = load_state()
    limit = todays_limit(cfg, state)
    print(f"Today's send limit (warm-up ramp): {limit}")

    already_sent = load_sent_emails()
    print(f"Already contacted so far: {len(already_sent)}")

    candidates = find_leads(
        cfg["categories"], cfg["cities"],
        exclude_eu_uk=cfg.get("exclude_eu_uk", True),
        per_combo=15,
    )
    print(f"Candidate businesses found: {len(candidates)}")

    sent_today = []
    for biz in candidates:
        if len(sent_today) >= limit:
            break
        email = find_email(biz["website"])
        if not email or email.lower() in already_sent:
            continue

        owner_name_guess = biz["name"]  # Places API doesn't give owner names;
        # falls back to business name, which reads naturally in the greeting.
        body = cfg["body_template"].format(name=owner_name_guess, business=biz["name"])

        try:
            send_email(
                to_email=email,
                subject=cfg["subject"],
                body=body,
                from_name=cfg["sender_name"],
                from_email=cfg["sender_email"],
            )
            status = "sent"
        except Exception as e:
            print(f"Failed to send to {email}: {e}")
            status = "failed"

        sent_today.append({
            "date": date.today().isoformat(),
            "business": biz["name"],
            "email": email,
            "status": status,
        })
        already_sent.add(email.lower())

    append_log(sent_today)
    successes = sum(1 for r in sent_today if r["status"] == "sent")
    print(f"Done. Sent {successes} new emails today.")


if __name__ == "__main__":
    sys.exit(main())
