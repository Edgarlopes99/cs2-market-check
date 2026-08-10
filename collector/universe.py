"""Decide que itens levam pedido extra à Steam.

Sem containers.json curado ainda (isso é Fase 2), a heurística usa o próprio
catálogo da Skinport: um item é "caixa" se a sua market_page for de categoria
container. Confirmado manualmente no FASE0.md: 218 itens, todos caixas reais.
Quando a Fase 2 preencher containers.json, esta função passa a ler de lá.
"""


def container_names(skinport_items: list[dict]) -> list[str]:
    nomes = []
    for item in skinport_items:
        pagina = item.get("market_page") or ""
        if "/container?" in pagina:
            nomes.append(item["market_hash_name"])
    return sorted(nomes)
