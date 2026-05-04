import logging
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

TZ = ZoneInfo("America/Sao_Paulo")


class SheetWriter:
    def __init__(self, creds_path: str, sheet_id: str, tab_links: str, tab_repo: str):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.sh = self.gc.open_by_key(sheet_id)
        self.tab_links_name = tab_links
        self.tab_repo_name = tab_repo
        self._tab_links = None
        self._tab_repo = None

    @property
    def tab_links(self):
        if self._tab_links is None:
            self._tab_links = self.sh.worksheet(self.tab_links_name)
        return self._tab_links

    @property
    def tab_repo(self):
        if self._tab_repo is None:
            self._tab_repo = self.sh.worksheet(self.tab_repo_name)
        return self._tab_repo

    def load_houses(self) -> dict[str, list[str]]:
        """
        Le a aba 'Repo de Links'. Estrutura esperada:
          Linha de header com 'Casa de Apostas' na coluna A.
          Linhas de dados: A=nome casa, B=campanha, C=tracking, D=link de afiliacao.
        Pra cada casa, gera keywords a partir do nome + dominio do link de afiliacao.
        """
        try:
            rows = self.tab_repo.get_all_values()
        except Exception as e:
            logger.warning("Nao consegui ler aba Repo de Links: %s. Usando fallback.", e)
            return self._fallback_houses()

        header_idx = None
        for i, row in enumerate(rows):
            if row and row[0].strip().lower() in {"casa de apostas", "casa", "nome"}:
                header_idx = i
                break
        if header_idx is None:
            logger.warning("Nao encontrei header 'Casa de Apostas' no Repo de Links. Usando fallback.")
            return self._fallback_houses()

        houses: dict[str, list[str]] = {}
        seen = set()
        for row in rows[header_idx + 1:]:
            if not row or not row[0].strip():
                continue
            casa = row[0].strip()
            if casa.lower() in seen:
                continue
            seen.add(casa.lower())
            affil_url = row[3].strip() if len(row) >= 4 else ""
            houses[casa] = self._derive_keywords(casa, affil_url)

        if not houses:
            return self._fallback_houses()
        return houses

    @staticmethod
    def _derive_keywords(casa: str, affil_url: str) -> list[str]:
        keywords: list[str] = []
        nome = casa.lower().replace(" ", "")
        keywords.append(nome)
        if nome.endswith("bet") and len(nome) > 5:
            stripped = nome[:-3]
            if stripped and stripped not in keywords:
                keywords.append(stripped)
        if affil_url:
            try:
                host = (urlparse(affil_url).hostname or "").lower()
                if host.startswith("www."):
                    host = host[4:]
                if host and host not in keywords:
                    keywords.append(host)
            except Exception:
                pass
        return keywords

    @staticmethod
    def _fallback_houses() -> dict[str, list[str]]:
        return {
            "BetMGM": ["betmgm"],
            "EsportivaBet": ["esportivabet", "esportiva.bet"],
            "Novibet": ["novibet"],
            "Sportingbet": ["sportingbet"],
            "Stake": ["stake.com", "stake.bet", "stake.br"],
        }

    def append_link(
        self,
        canal_origem: str,
        msg_link: str,
        conteudo: str,
        url: str,
        casa: str,
    ) -> None:
        now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
        row = [now, canal_origem, msg_link, conteudo, url, casa, "Pendente"]
        self.tab_links.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Linha adicionada: %s | %s | %s", canal_origem, casa, url)
