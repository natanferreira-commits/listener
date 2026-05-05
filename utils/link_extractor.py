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


def extract_urls_from_message(message) -> list[str]:
    """
    Extrai URLs de uma mensagem Telethon, considerando:
    1. URLs em texto puro (regex)
    2. Hyperlinks formatados (MessageEntityTextUrl) - texto clicavel com URL embutida
    3. URLs marcadas no texto (MessageEntityUrl) - cobertas pelo regex tambem
    4. Botoes inline (KeyboardButtonUrl) - botao com URL
    Retorna lista deduplicada preservando ordem.
    """
    urls: list[str] = []
    text = getattr(message, "message", None) or ""

    urls.extend(extract_urls(text))

    entities = getattr(message, "entities", None) or []
    for entity in entities:
        url = getattr(entity, "url", None)
        if url:
            urls.append(url)

    reply_markup = getattr(message, "reply_markup", None)
    rows = getattr(reply_markup, "rows", None) or []
    for row in rows:
        buttons = getattr(row, "buttons", None) or []
        for button in buttons:
            url = getattr(button, "url", None)
            if url:
                urls.append(url)

    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


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
