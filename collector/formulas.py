"""Contas de que todos os testes de scoring dependem (spec secção 5 e 7).
Isoladas aqui e testadas em tests/test_formulas.py porque, se uma estiver
errada, a ferramenta mente com confiança."""


def fila_dias(listings: float, volume_diario: float) -> float | None:
    """Teste 1. Dias de fila se listares ao preço corrente."""
    if volume_diario <= 0:
        return None
    return listings / volume_diario


def spread(ask: float, bid: float) -> float | None:
    """Teste 2. Fração perdida só por entrar e sair."""
    if ask <= 0:
        return None
    return (ask - bid) / ask


def liquido_csfloat(bid: float, comissao_venda: float = 0.02, comissao_levantamento: float = 0.025) -> float:
    """Secção 7. O que fica na mão depois de vender ao bid e levantar."""
    return bid * (1 - comissao_venda) * (1 - comissao_levantamento)
