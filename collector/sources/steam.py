"""Fonte secundária: Steam priceoverview. Sem chave, mas 1 pedido por item
e bloqueada por IP acima de ~20 pedidos/minuto (ver FASE0.md).

Usada só para o subconjunto de caixas (universe.container_names), para dar
volume à escala da Steam em vez da escala menor da Skinport.

Se a Steam bloquear o runner, isto falha item a item sem derrubar a recolha
do dia inteiro — collector/run.py trata cada falha como "sem dado Steam
hoje para este item", nunca como erro fatal.
"""
import time

import httpx

URL = "https://steamcommunity.com/market/priceoverview/"
TIMEOUT = 15.0
PAUSA_ENTRE_PEDIDOS = 3.5  # segundos; fica bem abaixo do limite ~20/min observado


class SteamBloqueadaError(Exception):
    """A Steam parou de responder (429/403) — parar de insistir por hoje."""


def _parse_preco(texto: str | None) -> float | None:
    if not texto:
        return None
    limpo = texto.replace("€", "").replace(",", ".").strip()
    try:
        return float(limpo)
    except ValueError:
        return None


def _parse_volume(texto: str | None) -> int | None:
    if not texto:
        return None
    try:
        return int(texto.replace(",", "").replace(".", ""))
    except ValueError:
        return None


def fetch_priceoverview(client: httpx.Client, market_hash_name: str, currency: int = 3) -> dict | None:
    """currency=3 é EUR. Devolve None se o item não tiver dados (item raro/novo)."""
    resp = client.get(
        URL,
        params={"appid": 730, "currency": currency, "market_hash_name": market_hash_name},
    )
    if resp.status_code in (429, 403):
        raise SteamBloqueadaError(f"Steam devolveu HTTP {resp.status_code} — provavelmente bloqueio por IP")
    if resp.status_code != 200:
        return None
    body = resp.json()
    if not body.get("success"):
        return None
    return {
        "steam_ask": _parse_preco(body.get("lowest_price")),
        "steam_median_24h": _parse_preco(body.get("median_price")),
        "steam_volume_24h": _parse_volume(body.get("volume")),
    }


def fetch_priceoverview_batch(nomes: list[str]) -> tuple[dict[str, dict], list[str]]:
    """Devolve (resultados por nome, nomes que falharam). Nunca lança por um
    único item falhar — só lança SteamBloqueadaError se a Steam bloquear o IP,
    e nesse caso pára e devolve o que já tinha conseguido."""
    resultados: dict[str, dict] = {}
    falhas: list[str] = []
    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": "cs2-market-check/1.0"}) as client:
        for i, nome in enumerate(nomes):
            if i > 0:
                time.sleep(PAUSA_ENTRE_PEDIDOS)
            try:
                dados = fetch_priceoverview(client, nome)
            except SteamBloqueadaError:
                falhas.extend(nomes[i:])
                break
            if dados is None:
                falhas.append(nome)
            else:
                resultados[nome] = dados
    return resultados, falhas
