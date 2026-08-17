"""Não testa se os factos estão certos (isso só se confirma no csgostash —
ver data/manual/CONTAINERS-LEIA-ME.md). Testa só que a estrutura do ficheiro
é a que o resto do código espera, para um erro de digitação não passar
despercebido."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CONTAINERS_PATH = Path(__file__).resolve().parent.parent / "data" / "manual" / "containers.json"


def _carregar():
    return json.loads(CONTAINERS_PATH.read_text(encoding="utf-8"))


def test_ficheiro_existe_e_e_json_valido():
    dados = _carregar()
    assert isinstance(dados, dict)
    assert len(dados) >= 30  # a spec pede "~40 caixas"


def test_todas_as_entradas_tem_os_campos_obrigatorios():
    dados = _carregar()
    campos = {"still_dropping", "rare_slot", "discontinued_date", "notes", "verified"}
    for nome, entrada in dados.items():
        assert campos <= entrada.keys(), f"{nome} não tem todos os campos obrigatórios"


def test_still_dropping_e_verified_sao_booleanos():
    dados = _carregar()
    for nome, entrada in dados.items():
        assert isinstance(entrada["still_dropping"], bool), nome
        assert isinstance(entrada["verified"], bool), nome


def test_rare_slot_e_knives_ou_gloves():
    dados = _carregar()
    for nome, entrada in dados.items():
        assert entrada["rare_slot"] in ("knives", "gloves"), nome


def test_ativas_nao_tem_discontinued_date():
    dados = _carregar()
    for nome, entrada in dados.items():
        if entrada["still_dropping"]:
            assert entrada["discontinued_date"] is None, f"{nome} está ativa mas tem data de fim"


def test_descontinuadas_tem_discontinued_date_no_formato_ano_mes():
    dados = _carregar()
    for nome, entrada in dados.items():
        if not entrada["still_dropping"]:
            data = entrada["discontinued_date"]
            assert data is not None, f"{nome} está descontinuada mas sem data"
            assert len(data) == 7 and data[4] == "-", f"{nome} tem data em formato inesperado: {data}"


def test_nao_ha_nomes_duplicados_com_espacos_a_mais():
    dados = _carregar()
    nomes_normalizados = [n.strip() for n in dados]
    assert nomes_normalizados == list(dados.keys())
