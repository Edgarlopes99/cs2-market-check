import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import collector.universe as universe_mod
from collector.universe import container_names


def _item(nome, container=True):
    pagina = "https://skinport.com/market/container?item=X" if container else "https://skinport.com/market?item=X"
    return {"market_hash_name": nome, "market_page": pagina}


def test_sem_containers_json_usa_heuristica_generica(tmp_path, monkeypatch):
    monkeypatch.setattr(universe_mod, "CONTAINERS_PATH", tmp_path / "nao_existe.json")
    itens = [_item("Prisma Case"), _item("AK-47 | Redline", container=False)]
    assert container_names(itens) == ["Prisma Case"]


def test_com_containers_json_usa_lista_curada(tmp_path, monkeypatch):
    caminho = tmp_path / "containers.json"
    caminho.write_text('{"Prisma Case": {}, "Glove Case": {}}', encoding="utf-8")
    monkeypatch.setattr(universe_mod, "CONTAINERS_PATH", caminho)
    # o catálogo de hoje só tem a Prisma Case -> Glove Case fica de fora,
    # mesmo estando no containers.json (proteção contra nomes desatualizados)
    itens = [_item("Prisma Case"), _item("Outra Coisa Qualquer")]
    assert container_names(itens) == ["Prisma Case"]


def test_containers_json_corrompido_cai_para_heuristica(tmp_path, monkeypatch):
    caminho = tmp_path / "containers.json"
    caminho.write_text("{isto nao e json valido", encoding="utf-8")
    monkeypatch.setattr(universe_mod, "CONTAINERS_PATH", caminho)
    itens = [_item("Prisma Case")]
    assert container_names(itens) == ["Prisma Case"]


def test_containers_json_real_intersecta_com_catalogo():
    # usa o ficheiro real do repositório, sem monkeypatch
    itens = [_item("Prisma Case"), _item("Kilowatt Case"), _item("Item Que Nao Existe")]
    resultado = container_names(itens)
    assert "Prisma Case" in resultado
    assert "Kilowatt Case" in resultado
    assert "Item Que Nao Existe" not in resultado
