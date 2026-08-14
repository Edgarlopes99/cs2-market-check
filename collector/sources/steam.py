"""Fonte secundária: Steam priceoverview. Sem chave, mas 1 pedido por item
e bloqueada por IP acima de ~20 pedidos/minuto (ver FASE0.md).

Usada só para o subconjunto de caixas (universe.container_names), para dar
volume à escala da Steam em vez da escala menor da Skinport.

A ordem dos pedidos vem de collector.cursor.ordenar_por_antiguidade — nunca
alfabética. A primeira versão pedia sempre por ordem alfabética e desistia
de toda a lista ao primeiro bloqueio, o que significava que os itens do
início do alfabeto tinham sempre dados e o resto nunca tinha. Verificado:
417/418 numa execução, 183/418 quinze minutos depois, sempre os mesmos
primeiros nomes.

Agora: recuo exponencial (60s, 120s, 240s) antes de desistir de vez, e
pausa de 8s entre pedidos. Como o repositório é público, os minutos de
Actions são ilimitados — não há pressa.
"""
import time

import httpx

URL = "https://steamcommunity.com/market/priceoverview/"
TIMEOUT = 15.0
PAUSA_ENTRE_PEDIDOS = 8.0
RECUOS_SEGUNDOS = [60, 120, 240]


class SteamBloqueadaError(Exception):
    """A Steam parou de responder (429/403) mesmo depois dos recuos."""


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


def _pedir_com_recuo(client: httpx.Client, market_hash_name: str, currency: int) -> httpx.Response:
    ultimo_erro = None
    for tentativa, espera in enumerate([0] + RECUOS_SEGUNDOS):
        if espera:
            print(f"    Steam bloqueou — a esperar {espera}s antes de tentar de novo...")
            time.sleep(espera)
        resp = client.get(
            URL,
            params={"appid": 730, "currency": currency, "market_hash_name": market_hash_name},
        )
        if resp.status_code not in (429, 403):
            return resp
        ultimo_erro = resp
    raise SteamBloqueadaError(
        f"Steam continuou a devolver HTTP {ultimo_erro.status_code} depois de {len(RECUOS_SEGUNDOS)} recuos"
    )


def fetch_priceoverview(client: httpx.Client, market_hash_name: str, currency: int = 3) -> dict | None:
    """currency=3 é EUR. Devolve None se o item não tiver dados (item raro/novo)."""
    resp = _pedir_com_recuo(client, market_hash_name, currency)
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


def fetch_priceoverview_batch(nomes_ordenados: list[str]) -> tuple[dict[str, dict], list[str]]:
    """nomes_ordenados já deve vir de cursor.ordenar_por_antiguidade. Devolve
    (resultados por nome, nomes que falharam). Só pára tudo se a Steam
    continuar bloqueada depois dos recuos — nesse caso devolve o que já
    tinha conseguido e marca o resto como falha."""
    resultados: dict[str, dict] = {}
    falhas: list[str] = []
    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": "cs2-market-check/1.0"}) as client:
        for i, nome in enumerate(nomes_ordenados):
            if i > 0:
                time.sleep(PAUSA_ENTRE_PEDIDOS)
            try:
                dados = fetch_priceoverview(client, nome)
            except SteamBloqueadaError:
                falhas.extend(nomes_ordenados[i:])
                break
            if dados is None:
                falhas.append(nome)
            else:
                resultados[nome] = dados
    return resultados, falhas
