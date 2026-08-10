"""Grava o snapshot diário em Parquet (comprimido, colunar — muito mais
pequeno que JSON para 22 mil linhas por dia) e mantém data/health.json."""
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DAILY_DIR = DATA_DIR / "daily"
HEALTH_PATH = DATA_DIR / "health.json"


def caminho_snapshot(dia: date) -> Path:
    return DAILY_DIR / f"{dia.year:04d}" / f"{dia.month:02d}" / f"{dia.isoformat()}.parquet"


def gravar_snapshot(dia: date, linhas: list[dict]) -> Path:
    """Escreve o snapshot do dia. Nunca sobrescreve com uma lista vazia —
    isso seria apagar um dia bom com dados vazios, exatamente o que a
    especificação proíbe."""
    if not linhas:
        raise ValueError("Recusa a gravar um snapshot vazio (0 itens) — isso apagaria dados bons.")
    caminho = caminho_snapshot(dia)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(linhas)
    df.to_parquet(caminho, engine="pyarrow", compression="zstd", index=False)
    return caminho


def atualizar_saude(dia: date, n_itens: int, n_steam: int, avisos: list[str]) -> None:
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    estado = {
        "ultimo_snapshot_ok": dia.isoformat(),
        "gravado_em_utc": datetime.now(timezone.utc).isoformat(),
        "n_itens_skinport": n_itens,
        "n_itens_steam": n_steam,
        "avisos": avisos,
    }
    HEALTH_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
