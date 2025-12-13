import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from pathlib import Path

BASE_URL = "https://www.csis.org"
PAGE_URL = "https://www.csis.org/analysis"
SEEN_FILE = Path("seen.txt")

if SEEN_FILE.exists():
    seen_links = set(SEEN_FILE.read_text().splitlines())
else:
    seen_links = set()


# Fetch page
response = requests.get(PAGE_URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Find all article rows
rows = soup.find_all("div", class_="views-row")

# Create RSS feed
fg = FeedGenerator()
fg.title("CSIS Analysis Updates")
fg.link(href=PAGE_URL, rel="alternate")
fg.description("Custom RSS feed for CSIS Analysis articles")
fg.language("en")

for row in rows:
    article = row.find("article")
    if not article:
        continue

    # Title + link
    link_tag = article.find("h3").find("a")
    title = link_tag.get_text(strip=True)
    link = BASE_URL + link_tag["href"]
    
    if link in seen_links:
        continue

    # Summary
    summary_tag = article.find("div", class_="search-listing--summary")
    summary = summary_tag.get_text(strip=True) if summary_tag else ""

    # Date (e.g. "— December 12, 2025")
    date_text = article.get_text(" ", strip=True)
    date_match = re.search(r"—\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", date_text)

    if date_match:
        pub_date = datetime.strptime(
            date_match.group(1), "%B %d, %Y"
        ).replace(tzinfo=timezone.utc)
    else:
        pub_date = datetime.now(timezone.utc)

    # Add RSS entry
    fe = fg.add_entry()
    fe.title(title)
    fe.link(href=link)
    fe.guid(link)
    fe.description(summary)
    fe.pubDate(pub_date)

    seen_links.add(link)

# Write RSS file
fg.rss_file("feed.xml")
SEEN_FILE.write_text("\n".join(sorted(seen_links)))

print("feed.xml updated successfully.")
