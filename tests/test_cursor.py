import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.cursor import carregar, ordenar_por_antiguidade


def test_itens_nunca_pedidos_vem_primeiro():
    cursor = {"A": "2026-08-01"}
    ordem = ordenar_por_antiguidade(["A", "B"], cursor)
    assert ordem == ["B", "A"]


def test_entre_dois_ja_pedidos_o_mais_antigo_vem_primeiro():
    cursor = {"A": "2026-08-10", "B": "2026-08-01", "C": "2026-08-05"}
    ordem = ordenar_por_antiguidade(["A", "B", "C"], cursor)
    assert ordem == ["B", "C", "A"]


def test_cursor_vazio_mantem_ordem_estavel():
    ordem = ordenar_por_antiguidade(["Z", "A", "M"], {})
    assert ordem == ["Z", "A", "M"]  # sort estável: sem datas, mantém a ordem de entrada


def test_item_do_cursor_que_ja_nao_existe_no_catalogo_e_ignorado():
    cursor = {"Item Descontinuado": "2020-01-01", "A": "2026-08-01"}
    ordem = ordenar_por_antiguidade(["A", "B"], cursor)
    assert "Item Descontinuado" not in ordem
    assert set(ordem) == {"A", "B"}


def test_carregar_ficheiro_inexistente_nao_rebenta(tmp_path, monkeypatch):
    import collector.cursor as cursor_mod
    monkeypatch.setattr(cursor_mod, "CURSOR_PATH", tmp_path / "nao_existe.json")
    assert carregar() == {}


def test_carregar_ficheiro_corrompido_nao_rebenta(tmp_path, monkeypatch):
    import collector.cursor as cursor_mod
    caminho = tmp_path / "corrompido.json"
    caminho.write_text("{isto nao e json valido", encoding="utf-8")
    monkeypatch.setattr(cursor_mod, "CURSOR_PATH", caminho)
    assert carregar() == {}
