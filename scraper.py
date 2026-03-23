"""
utils/scraper.py
----------------
BeautifulSoup4 web scraper.
Returns structured dicts per page — safe for Streamlit Cloud.
"""

import requests
from bs4 import BeautifulSoup

_NOISE = {
    "home", "menu", "toggle", "close", "open", "skip", "back to top",
    "cookie", "privacy policy", "terms", "accept all", "deny",
    "×", "✕", "»", "«", "...", "more", "less",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_single_page(url: str) -> dict:
    """Scrape one URL and return a structured dict of UI elements."""
    result = {
        "url": url,
        "title": "",
        "headings": [],
        "buttons": [],
        "inputs": [],
        "prices": [],
        "error": None,
    }
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Title
        result["title"] = soup.title.string.strip() if soup.title else url

        # Headings
        seen, headings = set(), []
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            t = tag.get_text(strip=True)
            if t and len(t) < 120 and t not in seen:
                seen.add(t)
                headings.append(t)
        result["headings"] = headings[:20]

        # Buttons / CTAs
        seen, buttons = set(), []
        for el in soup.find_all(["button", "a", "input"]):
            if el.name == "input" and el.get("type") in ("submit", "button", "reset"):
                t = el.get("value") or el.get("aria-label") or ""
            else:
                t = el.get_text(strip=True) or el.get("aria-label") or ""
            t = t.strip()
            if t and 2 < len(t) < 50 and t.lower() not in _NOISE and t not in seen:
                seen.add(t)
                buttons.append(t)
        result["buttons"] = buttons[:30]

        # Form inputs
        seen, inputs = set(), []
        for inp in soup.find_all(["input", "select", "textarea"]):
            if inp.get("type") in ("hidden", "submit", "button", "reset", "image"):
                continue
            label = (
                inp.get("placeholder") or inp.get("name") or
                inp.get("id") or inp.get("aria-label") or inp.get("type") or ""
            ).strip()
            if label and label not in seen:
                seen.add(label)
                inputs.append(label)
        result["inputs"] = inputs[:20]

        # Prices
        seen, prices = set(), []
        for t in soup.stripped_strings:
            if any(s in t for s in ("$", "£", "€", "₹")):
                t = t.strip()
                if len(t) < 25 and t not in seen:
                    seen.add(t)
                    prices.append(t)
        result["prices"] = prices[:10]

    except requests.exceptions.Timeout:
        result["error"] = f"Timed out — {url} may be slow or unreachable"
    except requests.exceptions.ConnectionError:
        result["error"] = f"Cannot connect to {url}"
    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP {e.response.status_code} from {url}"
    except Exception as e:
        result["error"] = f"Error: {e}"

    return result


def scrape_website(pages: list) -> str:
    """Convert list of page dicts into formatted text for the LLM prompt."""
    sections = []
    for p in pages:
        if p.get("error"):
            sections.append(f"--- Page: {p['url']} ---\nERROR: {p['error']}\n")
            continue
        lines = [
            f"--- Page: {p['url']} ---",
            f"Title: {p.get('title', 'N/A')}",
            "",
            "Headings: " + (", ".join(p.get("headings", [])) or "None found"),
            "",
            "Buttons / CTAs: " + (", ".join(p.get("buttons", [])) or "None found"),
            "",
            "Form Inputs: " + (", ".join(p.get("inputs", [])) or "None found"),
        ]
        if p.get("prices"):
            lines.append("Prices: " + ", ".join(p["prices"]))
        lines.append("")
        sections.append("\n".join(lines))
    return "\n".join(sections)
