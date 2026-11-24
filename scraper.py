from collections import Counter
import json
import time
from typing import Any
from urllib.parse import urljoin
from html.parser import HTMLParser

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class _HTTPResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _RequestException(Exception):
    pass


class _HTTPSession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}

    def get(self, url: str, timeout: int) -> _HTTPResponse:
        try:
            request = Request(url, headers=self.headers)
            with urlopen(request, timeout=timeout) as response:
                return _HTTPResponse(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise _RequestException(str(error)) from error


class requests:
    RequestException = _RequestException
    Session = _HTTPSession


class _QuoteHTMLParser(HTMLParser):
    """Extract quote cards and the page's next-page link."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, Any]] = []
        self.next_href: str | None = None
        self._elements: list[tuple[str, set[str]]] = []
        self._record: dict[str, Any] | None = None
        self._card_depth: int | None = None
        self._capture: tuple[str, int] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        in_next = any(name == "li" and "next" in item_classes
                      for name, item_classes in self._elements)
        self._elements.append((tag, classes))
        depth = len(self._elements)

        if tag == "a" and in_next:
            self.next_href = attributes.get("href")

        if tag == "div" and "quote" in classes:
            self._record = {"quote": "", "author": "", "tags": []}
            self.records.append(self._record)
            self._card_depth = depth
        elif self._record is not None:
            if tag == "span" and "text" in classes:
                self._capture = ("quote", depth)
            elif tag == "small" and "author" in classes:
                self._capture = ("author", depth)
            elif tag == "a" and "tag" in classes:
                self._capture = ("tag", depth)

    def handle_data(self, data: str) -> None:
        if self._record is None or self._capture is None:
            return
        field, _ = self._capture
        if field == "tag":
            self._record["tags"].append(data)
        else:
            self._record[field] += data

    def handle_endtag(self, tag: str) -> None:
        depth = len(self._elements)
        if self._capture is not None and depth == self._capture[1]:
            self._capture = None
        if tag == "div" and self._card_depth == depth:
            self._record = None
            self._card_depth = None

        for index in range(len(self._elements) - 1, -1, -1):
            if self._elements[index][0] == tag:
                del self._elements[index:]
                break



class QuoteScraper:
    """Polite scraper for extracting quotes, authors, and tags."""

    SELECTORS = {
        "card": "div.quote",
        "text": "span.text",
        "author": "small.author",
        "tag": "div.tags a.tag",
        "next": "li.next a",
    }

    def __init__(self, base_url: str, delay: float = 1.0) -> None:
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PythonLearningProject/1.0 (+https://quotes.toscrape.com)"
        })

    def get_html(self, url: str) -> str | None:
        try:
            res = self.session.get(url, timeout=10)
            res.raise_for_status()
            return res.text
        except requests.RequestException as error:
            print(f"Skipping {url} due to network error: {error}")
            return None

    def extract_from_html(self, html: str) -> tuple[list[dict[str, Any]], str | None]:
        parser = _QuoteHTMLParser()
        parser.feed(html)
        next_url = (
            urljoin(self.base_url, parser.next_href)
            if parser.next_href
            else None
        )
        return parser.records, next_url

    def run(self) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        current_url: str | None = self.base_url

        while current_url:
            print(f"Scraping: {current_url}")
            html = self.get_html(current_url)
            if not html:
                break

            page_records, current_url = self.extract_from_html(html)
            collected.extend(page_records)

            if current_url:
                time.sleep(self.delay)

        return collected


def export_results(records: list[dict[str, Any]]) -> None:
    with open("quotes.json", "w", encoding="utf-8") as jf:
        json.dump(records, jf, indent=2, ensure_ascii=False)

    with open("quotes.txt", "w", encoding="utf-8") as tf:
        for i, entry in enumerate(records, start=1):
            tags_str = ", ".join(entry["tags"]) or "untagged"
            tf.write(f"[{i}] {entry['quote']}\n    Author: {entry['author']} | Tags: {tags_str}\n\n")


def display_metrics(records: list[dict[str, Any]]) -> None:
    if not records:
        print("No records found.")
        return

    authors = Counter(r["author"] for r in records)
    tags = Counter(tag for r in records for tag in r["tags"])

    top_author, author_hits = authors.most_common(1)[0]
    top_tag, tag_hits = tags.most_common(1)[0]

    print(f"\nTotal quotes saved : {len(records)}")
    print(f"Most quoted author : {top_author} ({author_hits})")
    print(f"Most common tag    : {top_tag} ({tag_hits})")


if __name__ == "__main__":
    scraper = QuoteScraper("https://quotes.toscrape.com/", delay=1.0)
    data = scraper.run()
    export_results(data)
    display_metrics(data)