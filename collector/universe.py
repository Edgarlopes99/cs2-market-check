"""Decide que itens levam pedido extra à Steam.

Fase 2 preencheu data/manual/containers.json com as ~40 caixas de armas
reais (facas/luvas), curadas à mão. É essa lista que manda agora — muito
mais precisa e muito mais pequena que a heurística anterior, que apanhava
tudo o que a Skinport chama "container" (419 itens, incluindo cápsulas de
autocolantes e souvenir packages que os testes 6/7/8 nem usam).

Se o ficheiro não existir (por exemplo, antes da Fase 2), cai para a
heurística antiga como rede de segurança, para o coletor nunca parar de
funcionar por falta de curadoria manual.
"""
import json
from pathlib import Path

CONTAINERS_PATH = Path(__file__).resolve().parent.parent / "data" / "manual" / "containers.json"


def _nomes_curados() -> list[str] | None:
    if not CONTAINERS_PATH.exists():
        return None
    try:
        dados = json.loads(CONTAINERS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return sorted(dados.keys())


def _heuristica_generica(skinport_items: list[dict]) -> list[str]:
    nomes = []
    for item in skinport_items:
        pagina = item.get("market_page") or ""
        if "/container?" in pagina:
            nomes.append(item["market_hash_name"])
    return sorted(nomes)


def container_names(skinport_items: list[dict]) -> list[str]:
    curados = _nomes_curados()
    if curados is None:
        return _heuristica_generica(skinport_items)

    # só pede à Steam nomes que o catálogo de hoje reconhece — protege contra
    # erros de digitação no containers.json ou caixas que a Skinport deixou
    # de listar (não deve travar o coletor por causa de um nome errado).
    nomes_no_catalogo = {item["market_hash_name"] for item in skinport_items}
    return sorted(n for n in curados if n in nomes_no_catalogo)
