"""URLFetcher — busca e extrai texto limpo de URLs para summarize_document."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class URLFetcher:
    """
    Busca conteudo de URL e extrai texto limpo via BeautifulSoup.
    Usado por summarize_document quando recebe URL em vez de texto.
    """

    def __init__(self, timeout: float = 30.0, max_chars: int = 100_000):
        self._timeout = timeout
        self._max_chars = max_chars

    async def fetch_text(self, url: str) -> Optional[str]:
        """
        Busca URL e extrai texto limpo.
        Retorna None se falhar.
        """
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": "IntelliCare-SuperZ/1.0 (Medical Research Bot)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")

            if "application/json" in content_type:
                return resp.text[:self._max_chars]

            if "text/plain" in content_type:
                return resp.text[:self._max_chars]

            # HTML → extract text
            return self._extract_text_from_html(resp.text)

        except Exception as e:
            logger.error("URLFetcher falhou para %s: %s", url, e)
            return None

    def _extract_text_from_html(self, html: str) -> str:
        """Extrai texto limpo de HTML usando BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Remove scripts, styles, nav, footer
            for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Try article first, then main, then body
            content = soup.find("article") or soup.find("main") or soup.find("body")
            if content is None:
                content = soup

            text = content.get_text(separator="\n", strip=True)

            # Limpar whitespace excessivo
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            clean = "\n".join(lines)

            return clean[:self._max_chars]
        except ImportError:
            logger.warning("beautifulsoup4 nao instalado — retornando HTML bruto truncado")
            return html[:self._max_chars]
        except Exception as e:
            logger.error("Falha ao parsear HTML: %s", e)
            return html[:self._max_chars]
