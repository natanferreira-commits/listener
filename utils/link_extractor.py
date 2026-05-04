import re
from urllib.parse import urlparse

URL_REGEX = re.compile(
    r"(?:https?://|(?<![\w.])www\.)[^\s<>\"')\]]+",
    re.IGNORECASE,
)


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    found = URL_REGEX.findall(text)
    urls = []
    for raw in found:
        u = raw.strip().rstrip(".,;:!?)")
        if not u.startswith(("http://", "https://")):
            u = "https://" + u
        urls.append(u)
    return urls


def domain_of(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def match_house(url: str, houses: dict[str, list[str]]) -> str:
    """
    houses: dict mapeando nome da casa -> lista de domínios/keywords associados.
    Ex: {"Stake": ["stake.com", "stake.bet"], "BetMGM": ["betmgm.com"]}
    Retorna o nome da casa ou "" se nada bater.
    """
    host = domain_of(url)
    if not host:
        return ""
    for house, keywords in houses.items():
        for kw in keywords:
            kw = kw.lower().strip()
            if not kw:
                continue
            if kw in host or kw in url.lower():
                return house
    return ""
