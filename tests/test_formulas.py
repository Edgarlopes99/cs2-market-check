import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.formulas import fila_dias, liquido_csfloat, spread


def test_fila_dias_normal():
    assert fila_dias(listings=795, volume_diario=92.28571428571429) == 795 / 92.28571428571429


def test_fila_dias_reprova_limite_default():
    # Revolver Case medido no FASE0.md: 795 listagens, 646 vendas/7d = 92.3/dia -> ~8.6 dias, passa
    dias = fila_dias(listings=795, volume_diario=646 / 7)
    assert dias is not None
    assert round(dias, 1) == 8.6


def test_fila_dias_sem_volume():
    assert fila_dias(listings=100, volume_diario=0) is None


def test_spread_exemplo_manual():
    # ask 2.00, bid aproximado pela mediana 7d 2.33 (Revolver Case, FASE0.md)
    # bid > ask no exemplo real (mercado subiu) -> spread negativo, é válido
    s = spread(ask=2.00, bid=2.33)
    assert round(s, 4) == round((2.00 - 2.33) / 2.00, 4)


def test_spread_reprova_limite_default():
    s = spread(ask=10.0, bid=9.0)
    assert s == 0.1  # exatamente 10%, acima do default de 5% -> reprova


def test_spread_ask_zero():
    assert spread(ask=0, bid=5) is None


def test_liquido_csfloat_formula_da_spec():
    # spec: liquido = bid * (1 - 0.02) * (1 - 0.025)
    bid = 100.0
    esperado = 100.0 * 0.98 * 0.975
    assert round(liquido_csfloat(bid), 6) == round(esperado, 6)


def test_liquido_csfloat_default_comissoes():
    assert round(liquido_csfloat(50.0), 4) == round(50.0 * 0.98 * 0.975, 4)
