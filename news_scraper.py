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