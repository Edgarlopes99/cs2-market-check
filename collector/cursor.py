"""Guarda quando a Steam respondeu pela última vez a cada item, para o
coletor pedir sempre primeiro a quem está há mais tempo sem dados —
em vez da ordem alfabética fixa, que deixava a cauda do alfabeto sem
dados sempre que a Steam bloqueava a meio (ver FASE0.md / histórico)."""
import json
from pathlib import Path

CURSOR_PATH = Path(__file__).resolve().parent.parent / "data" / "steam_cursor.json"


def carregar() -> dict[str, str]:
    """nome -> data ISO da última resposta boa da Steam. Vazio se não existir ainda."""
    if not CURSOR_PATH.exists():
        return {}
    try:
        return json.loads(CURSOR_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def gravar(cursor: dict[str, str]) -> None:
    CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_PATH.write_text(json.dumps(cursor, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def ordenar_por_antiguidade(nomes: list[str], cursor: dict[str, str]) -> list[str]:
    """Itens nunca pedidos vêm primeiro (data vazia ordena antes de qualquer
    data real). Entre dois já pedidos, o mais antigo vem primeiro. Itens do
    cursor que já não existem no catálogo são simplesmente ignorados."""
    return sorted(nomes, key=lambda n: cursor.get(n, ""))
