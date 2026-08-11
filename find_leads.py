"""
Finds local business leads using DuckDuckGo search (free, no API key, no billing
account needed). Trade-off vs. a paid Places API: noisier results, so this filters
out directories/social platforms and rate-limits itself to avoid getting blocked.
"""
import time
from urllib.parse import urlparse

from ddgs import DDGS

# Skip results that are directories/aggregators/social platforms, not the
# business's own site (their contact email is rarely findable there anyway,
# and we don't want to accidentally email the platform instead of the owner).
SKIP_DOMAINS = [
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "yelp.com", "yellowpages.com", "tripadvisor.com", "google.com",
    "wikipedia.org", "youtube.com", "pinterest.com", "justdial.com",
    "indiamart.com", "glassdoor.com", "bbb.org", "foursquare.com",
]

EU_UK_HINTS = [
    "uk", "united kingdom", "england", "scotland", "wales", "ireland",
    "germany", "france", "spain", "italy", "netherlands", "belgium",
    "portugal", "poland", "sweden", "austria", "denmark", "finland",
]


def _is_eu_uk(text: str) -> bool:
    return any(hint in (text or "").lower() for hint in EU_UK_HINTS)


def _looks_like_directory(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    return any(skip in domain for skip in SKIP_DOMAINS)


def search_businesses(category: str, city: str, max_results: int = 10):
    """Return a list of dicts: {name, website}"""
    query = f"{category} in {city} official website"
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 3):
                url = r.get("href") or r.get("link")
                title = r.get("title", "")
                if not url or _looks_like_directory(url):
                    continue
                domain = urlparse(url).netloc
                website = f"https://{domain}"
                results.append({"name": title.split(" - ")[0].split("|")[0].strip(), "website": website})
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"DuckDuckGo search failed for '{query}': {e}")
    return results


def find_leads(categories, cities, exclude_eu_uk=True, per_combo=10):
    leads = []
    seen_domains = set()
    for category in categories:
        for city in cities:
            if exclude_eu_uk and _is_eu_uk(city):
                continue
            businesses = search_businesses(category, city, max_results=per_combo)
            for b in businesses:
                domain = urlparse(b["website"]).netloc
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                leads.append({
                    "name": b["name"] or domain,
                    "address": city,
                    "website": b["website"],
                })
            time.sleep(2)  # be polite to DuckDuckGo, avoid rate-limit blocks
    return leads


if __name__ == "__main__":
    found = find_leads(["gym"], ["Kolkata, India"])
    for lead in found:
        print(lead)
