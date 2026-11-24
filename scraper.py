from collections import Counter
import json
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://quotes.toscrape.com/"
HEADERS = {"User-Agent": "StudentScraper/1.0 (+https://quotes.toscrape.com)"}

SELECTORS = {
    "card": "div.quote",
    "text": "span.text",
    "author": "small.author",
    "tag": "div.tags a.tag",
    "next": "li.next a",
}

def get_page(session, url):
    try:
        res = session.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except requests.RequestException as err:
        print(f"Failed to load {url}: {err}")
        return None

def parse_quotes(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for card in soup.select(SELECTORS["card"]):
        quote_el = card.select_one(SELECTORS["text"])
        author_el = card.select_one(SELECTORS["author"])
        if quote_el is None or author_el is None:
            continue

        quote = quote_el.get_text(strip=True).strip("“”\"")
        author = author_el.get_text(strip=True)
        tags = [t.get_text(strip=True) for t in card.select(SELECTORS["tag"]) if t]

        items.append({"quote": quote, "author": author, "tags": tags})

    next_el = soup.select_one(SELECTORS["next"])
    next_url = urljoin(BASE_URL, str(next_el["href"])) if next_el and next_el.has_attr("href") else None
    return items, next_url

def scrape_all():
    all_quotes = []
    url = BASE_URL
    session = requests.Session()

    while url:
        print(f"Scraping {url}")
        html = get_page(session, url)
        if not html:
            break

        page_quotes, url = parse_quotes(html)
        all_quotes.extend(page_quotes)

        if url:
            time.sleep(1)

    return all_quotes

def save_outputs(quotes):
    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)

    with open("quotes.txt", "w", encoding="utf-8") as f:
        for i, q in enumerate(quotes, start=1):
            tags = ", ".join(q["tags"]) if q["tags"] else "no tags"
            f.write(f"{i}. {q['quote']} - {q['author']} ({tags})\n")

def show_stats(quotes):
    if not quotes:
        print("No quotes saved.")
        return

    top_author, author_n = Counter(q["author"] for q in quotes).most_common(1)[0]
    top_tag, tag_n = Counter(t for q in quotes for t in q["tags"]).most_common(1)[0]

    print(f"\nTotal quotes: {len(quotes)}")
    print(f"Top author: {top_author} ({author_n})")
    print(f"Top tag: {top_tag} ({tag_n})")

if __name__ == "__main__":
    data = scrape_all()
    save_outputs(data)
    show_stats(data)
