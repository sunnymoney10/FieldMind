"""HTML -> evidence text. Drops navigation, headers, footers, forms and link-heavy blocks so menus
and directory boilerplate never become evidence. Ported from the automated-002 proof (evidence.blocks),
unchanged in behaviour so normalized text and its SHA-256 match that run's captures."""
import hashlib

try:
    from bs4 import BeautifulSoup
except ImportError:  # the core worker stays standard-library; only HTML normalization needs bs4
    BeautifulSoup = None

DROP = "script,style,noscript,nav,header,footer,aside,form,[role=navigation],[role=banner],[role=contentinfo]"


def blocks(html):
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is needed to normalize HTML (pip install beautifulsoup4)")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select(DROP):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    out = []
    for tag in root.find_all(["p", "address", "h1", "h2", "h3", "li"]):
        if tag.name == "li" and tag.find(["p", "address"]):
            continue
        text = " ".join(tag.get_text(" ", strip=True).split())
        if not 18 <= len(text) <= 1800:
            continue
        linked = sum(len(a.get_text(" ", strip=True)) for a in tag.find_all("a"))
        if linked / max(len(text), 1) > .55:
            continue
        if text not in out:
            out.append(text)
    return out


def normalize(html):
    """(normalized_text, sha256) — one evidence block per line."""
    text = "\n".join(blocks(html))
    return text, hashlib.sha256(text.encode()).hexdigest()


def looks_like_challenge(html):
    import re
    return bool(re.search(r"checking the site connection security|verify you are human", html or "", re.I))
