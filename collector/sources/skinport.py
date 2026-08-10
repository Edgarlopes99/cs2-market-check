"""Fonte primária: API pública da Skinport. Sem chave, sem registo.

Dois pedidos cobrem o catálogo inteiro:
  /v1/items         -> listagens ativas (ask, quantidade)
  /v1/sales/history  -> vendas reais (mediana, volume) em janelas de 24h/7d/30d/90d

Ver FASE0.md para os números medidos e os limites reais confirmados.
"""
import httpx

BASE_URL = "https://api.skinport.com/v1"
TIMEOUT = 30.0


class SkinportError(Exception):
    pass


def _get(client: httpx.Client, path: str, params: dict) -> list[dict]:
    resp = client.get(f"{BASE_URL}{path}", params=params)
    if resp.status_code != 200:
        raise SkinportError(
            f"Skinport {path} devolveu HTTP {resp.status_code}: {resp.text[:200]}"
        )
    return resp.json()


def fetch_items(currency: str = "EUR") -> list[dict]:
    """Catálogo com listagens ativas. Um item por market_hash_name."""
    with httpx.Client(timeout=TIMEOUT) as client:
        return _get(client, "/items", {"app_id": 730, "currency": currency})


def fetch_sales_history(currency: str = "EUR") -> list[dict]:
    """Vendas reais por item, em janelas de 24h/7d/30d/90d."""
    with httpx.Client(timeout=TIMEOUT) as client:
        return _get(client, "/sales/history", {"app_id": 730, "currency": currency})
