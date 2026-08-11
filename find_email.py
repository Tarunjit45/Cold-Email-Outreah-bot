"""
Given a business website, tries to find a contact email by checking the
homepage and common contact-page paths for mailto: links or email patterns.
"""
import re
import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
CONTACT_PATHS = ["", "/contact", "/contact-us", "/about", "/about-us"]
GENERIC_PREFIXES_TO_SKIP = {"noreply", "no-reply", "donotreply", "example"}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LeadFinderBot/1.0)"}


def _extract_emails(html: str):
    soup = BeautifulSoup(html, "html.parser")
    emails = set()

    for a in soup.select('a[href^="mailto:"]'):
        addr = a["href"].split("mailto:")[1].split("?")[0].strip()
        if addr:
            emails.add(addr)

    emails.update(EMAIL_RE.findall(soup.get_text(" ")))
    return emails


def find_email(website_url: str, timeout: int = 10):
    website_url = website_url.rstrip("/")
    for path in CONTACT_PATHS:
        try:
            resp = requests.get(website_url + path, headers=HEADERS, timeout=timeout)
            if resp.status_code != 200:
                continue
            emails = _extract_emails(resp.text)
            for e in emails:
                prefix = e.split("@")[0].lower()
                if prefix in GENERIC_PREFIXES_TO_SKIP:
                    continue
                if e.lower().endswith((".png", ".jpg", ".gif")):
                    continue
                return e
        except requests.RequestException:
            continue
    return None


if __name__ == "__main__":
    print(find_email("https://example.com"))
