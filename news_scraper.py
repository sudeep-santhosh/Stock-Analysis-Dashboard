import argparse
import json
from pathlib import Path
import re
import time
from typing import Dict, List, Optional
from difflib import SequenceMatcher
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
import yfinance as yf
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MIN_CONTENT_WORDS = 80
TICKER_ALIASES = {
    "TATAMOTORS.NS": "TMCV.NS",
}
COMPANY_STOPWORDS = {
    "india",
    "limited",
    "ltd",
    "technology",
    "technologies",
    "corp",
    "corporation",
    "inc",
    "company",
    "plc",
    "the",
    "and",
}

BLOCKED_DOMAINS = {
    "reuters.com",
    "business-standard.com",
    "zeebiz.com",
    "goodreturns.in",
    "equitymaster.com",
    "news18.com",
    "firstpost.com",
    "ndtv.com",
    "ndtvprofit.com",
    "investing.com",
    "tmcnet.com",
    "forbes.com",
    "hindustantimes.com",
    "hoodline.com",
    "insidermedia.com",
    "nai500.com",
}


def normalize_ns_ticker(ticker_symbol: str) -> str:
    """
    Normalize and validate NSE tickers. This script intentionally supports
    only Yahoo Finance NSE symbols such as RELIANCE.NS.
    """
    normalized = ticker_symbol.strip().upper()
    if not normalized.endswith(".NS"):
        raise ValueError(
            'Only NSE ticker symbols ending with ".NS" are supported, for example "RELIANCE.NS".'
        )
    return TICKER_ALIASES.get(normalized, normalized)


def get_company_name(ticker_symbol: str) -> str:
    """
    Look up the company's full name from Yahoo Finance metadata.
    Falls back to other fields if longName is missing.
    """
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info or {}

    company_name = (
        info.get("longName")
        or info.get("shortName")
        or info.get("displayName")
        or ticker_symbol.upper()
    )
    return company_name


def build_search_queries(company_name: str, ticker_symbol: str) -> List[str]:
    """
    Build search phrases tuned for Indian market coverage.
    """
    base_symbol = ticker_symbol.removesuffix(".NS")
    queries = [
        company_name,
        f"{company_name} news",
        f"{company_name} NSE",
        f"{base_symbol} NSE news",
        f"{base_symbol} share news",
        f"{company_name} results",
        f"{company_name} market news",
    ]

    seen = set()
    ordered_queries: List[str] = []
    for query in queries:
        normalized = clean_text(query)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered_queries.append(normalized)

    return ordered_queries

def normalize_google_link(raw_link: str) -> Optional[str]:
    """
    Convert Google's wrapped search result URLs into clean article URLs.
    """
    if not raw_link:
        return None

    parsed = urlparse(raw_link)

    if parsed.netloc and "google." not in parsed.netloc:
        return raw_link

    if parsed.path == "/url":
        query_params = parse_qs(parsed.query)
        target = query_params.get("q", [None])[0]
        return target

    if raw_link.startswith("/url?"):
        query_params = parse_qs(urlparse(raw_link).query)
        target = query_params.get("q", [None])[0]
        return target

    if raw_link.startswith("./articles/") or raw_link.startswith("/articles/"):
        return urljoin("https://news.google.com", raw_link)

    if raw_link.startswith("http"):
        return raw_link

    return None

def clean_text(text: str) -> str:
    """
    Normalize whitespace and remove leftover noisy fragments.
    """
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()

def resolve_redirect_url(url: str) -> Optional[str]:
    """
    Follow redirect-style links and return the final destination URL.
    """
    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()
        final_url = response.url
        parsed = urlparse(final_url)
        if parsed.scheme in {"http", "https"} and "google." not in parsed.netloc:
            return final_url
    except requests.RequestException:
        return None

    return None


def search_google_news_rss(queries: List[str], max_links: int = 10) -> List[str]:
    """
    Use Google News RSS as the primary source because it is more stable than
    scraping the standard HTML results page.
    """
    links: List[str] = []
    seen = set()
    for query in queries:
        rss_url = (
            "https://news.google.com/rss/search?"
            f"q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        )

        try:
            response = requests.get(rss_url, headers=DEFAULT_HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"RSS search request failed: {exc}")
            continue

        soup = BeautifulSoup(response.content, "xml")

        for item in soup.find_all("item"):
            link_tag = item.find("link")
            if not link_tag or not link_tag.text:
                continue

            raw_link = link_tag.text.strip()
            clean_link = resolve_redirect_url(raw_link) or normalize_google_link(raw_link) or raw_link
            parsed = urlparse(clean_link)

            if parsed.scheme not in {"http", "https"}:
                continue

            if "google." in parsed.netloc:
                continue

            if is_blocked_domain(clean_link):
                continue

            if clean_link in seen:
                continue

            seen.add(clean_link)
            links.append(clean_link)

            if len(links) >= max_links:
                return links

    return links

def is_blocked_domain(url: str) -> bool:
    """
    Skip domains that repeatedly failed or blocked scraping in prior runs.
    """
    hostname = urlparse(url).netloc.lower().replace("www.", "")
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in BLOCKED_DOMAINS
    )


def search_bing_news_links(queries: List[str], max_links: int = 10) -> List[str]:
    """
    Scrape Bing News results, which often expose direct article links without
    the consent-page issues seen on Google.
    """
    links: List[str] = []
    seen = set()
    page_offsets = [0, 11]

    for query in queries:
        for offset in page_offsets:
            search_url = (
                f"https://www.bing.com/news/search?q={quote_plus(query)}"
                "&qft=sortbydate%3d%221%22&form=YFNR"
            )
            if offset:
                search_url += f"&first={offset}"

            try:
                response = requests.get(search_url, headers=DEFAULT_HEADERS, timeout=15)
                response.raise_for_status()
            except requests.RequestException as exc:
                print(f"Bing News request failed: {exc}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for anchor in soup.select("a.title, .news-card a[href^='http'], .caption a[href^='http']"):
                clean_link = anchor.get("href", "").strip()
                parsed = urlparse(clean_link)

                if parsed.scheme not in {"http", "https"}:
                    continue

                if is_blocked_domain(clean_link):
                    continue

                if clean_link in seen:
                    continue

                seen.add(clean_link)
                links.append(clean_link)

                if len(links) >= max_links:
                    return links

    return links
