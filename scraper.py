from collections import Counter
import json
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://quotes.toscrape.com/"
HEADERS = {"User-Agent": "StudentScraper/1.0 (+https://quotes.toscrape.com)"}

# keeping selectors here so if the site changes I only fix one place
SELECTORS = {
    "card": "div.quote",
    "text": "span.text",
    "author": "small.author",
    "tag": "div.tags a.tag",
    "next": "li.next a",
}

def fetch_html(session, url):
    try:
        res = session.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except requests.RequestException as err:
        print(f"error fetching {url}: {err}")
        return None

def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    page_quotes = []

    for card in soup.select(SELECTORS["card"]):
        quote_el = card.select_one(SELECTORS["text"])
        author_el = card.select_one(SELECTORS["author"])

        # check for None so get_text() doesn't crash on missing elements
        if quote_el is None or author_el is None:
            continue

        quote = quote_el.get_text(strip=True).strip("“”\"")
        author = author_el.get_text(strip=True)
        tags = [t.get_text(strip=True) for t in card.select(SELECTORS["tag"]) if t]

        page_quotes.append({
            "quote": quote,
            "author": author,
            "tags": tags,
        })

    next_el = soup.select_one(SELECTORS["next"])
    next_url = urljoin(BASE_URL, str(next_el["href"])) if next_el and next_el.has_attr("href") else None
    return page_quotes, next_url

def print_report(all_quotes):
    if not all_quotes:
        print("no quotes found")
        return

    top_author, author_count = Counter(q["author"] for q in all_quotes).most_common(1)[0]
    top_tag, tag_count = Counter(t for q in all_quotes for t in q["tags"]).most_common(1)[0]

    print(f"\nquotes saved: {len(all_quotes)}")
    print(f"top author: {top_author} ({author_count})")
    print(f"top tag: {top_tag} ({tag_count})")


def main():
    all_quotes = []
    url = BASE_URL
    session = requests.Session()

    while url:
        print(f"getting {url}")
        html = fetch_html(session, url)
        if not html:
            break

        page_quotes, url = parse_page(html)
        all_quotes.extend(page_quotes)

        # wait 1s between pages so we don't hit the server too fast
        if url:
            time.sleep(1)

    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(all_quotes, f, indent=2, ensure_ascii=False)

    with open("quotes.txt", "w", encoding="utf-8") as f:
        for i, q in enumerate(all_quotes, start=1):
            tags = ", ".join(q["tags"]) if q["tags"] else "none"
            f.write(f"{i}. \"{q['quote']}\" - {q['author']} | tags: {tags}\n")

    print_report(all_quotes)


if __name__ == "__main__":
    main()
