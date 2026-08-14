"""Ponto de entrada do coletor. Corre uma vez por dia via GitHub Actions.

Uso:
    py collector/run.py             recolhe e grava o snapshot de hoje
    py collector/run.py --dry-run   recolhe mas não grava nada, só relata
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.sources import skinport, steam
from collector.sources.skinport import SkinportError
from collector import cursor as cursor_mod
from collector import storage, universe


def construir_linhas(itens: list[dict], vendas: list[dict], dados_steam: dict[str, dict]) -> list[dict]:
    vendas_por_nome = {v["market_hash_name"]: v for v in vendas}
    hoje = date.today().isoformat()
    linhas = []
    for item in itens:
        nome = item["market_hash_name"]
        v = vendas_por_nome.get(nome, {})
        j7 = (v.get("last_7_days") or {})
        j30 = (v.get("last_30_days") or {})
        j90 = (v.get("last_90_days") or {})
        s = dados_steam.get(nome, {})
        linhas.append({
            "date": hoje,
            "market_hash_name": nome,
            "skinport_ask": item.get("min_price"),
            "skinport_listings": item.get("quantity"),
            "skinport_suggested_price": item.get("suggested_price"),
            "skinport_sales_median_7d": j7.get("median"),
            "skinport_sales_volume_7d": j7.get("volume"),
            "skinport_sales_median_30d": j30.get("median"),
            "skinport_sales_volume_30d": j30.get("volume"),
            "skinport_sales_median_90d": j90.get("median"),
            "skinport_sales_volume_90d": j90.get("volume"),
            "steam_ask": s.get("steam_ask"),
            "steam_median_24h": s.get("steam_median_24h"),
            "steam_volume_24h": s.get("steam_volume_24h"),
        })
    return linhas


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    avisos: list[str] = []

    print("A pedir catálogo à Skinport...")
    try:
        itens = skinport.fetch_items()
        vendas = skinport.fetch_sales_history()
    except SkinportError as e:
        print(f"ERRO: {e}")
        print("O snapshot de hoje NÃO foi gravado. Os dados de ontem continuam intactos.")
        return 1
    print(f"  {len(itens)} itens no catálogo, {len(vendas)} com histórico de vendas.")

    caixas = universe.container_names(itens)
    cursor = cursor_mod.carregar()
    ordem = cursor_mod.ordenar_por_antiguidade(caixas, cursor)
    print(f"A pedir preços à Steam para {len(ordem)} caixas, começando pelas há mais tempo sem dados "
          f"(isto demora ~{len(ordem) * 8 // 60} minutos, um pedido de cada vez)...")
    dados_steam, falhas_steam = steam.fetch_priceoverview_batch(ordem)
    print(f"  Steam respondeu para {len(dados_steam)} de {len(ordem)} caixas.")
    if falhas_steam:
        aviso = f"A Steam não respondeu para {len(falhas_steam)} caixas hoje (bloqueio de IP ou item sem dados)."
        print(f"  Aviso: {aviso}")
        avisos.append(aviso)

    linhas = construir_linhas(itens, vendas, dados_steam)

    if dry_run:
        print(f"\n--dry-run: nada foi gravado. Teria escrito {len(linhas)} linhas e atualizado o cursor Steam.")
        return 0

    dia = date.today()
    caminho = storage.gravar_snapshot(dia, linhas)
    storage.atualizar_saude(dia, n_itens=len(linhas), n_steam=len(dados_steam), avisos=avisos)

    for nome in dados_steam:
        cursor[nome] = dia.isoformat()
    cursor_mod.gravar(cursor)

    print(f"\nSnapshot gravado em {caminho} ({len(linhas)} linhas).")
    print(f"data/health.json atualizado às {datetime.now(timezone.utc).isoformat()} UTC.")
    print(f"data/steam_cursor.json atualizado com {len(dados_steam)} itens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
