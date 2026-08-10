# cs2-market-check

Ferramenta de análise do mercado de skins de CS2. Mede três coisas e mais nada:
liquidez, preço relativo ao próprio histórico, e concentração da carteira.

**Nunca prevê preços. Nunca diz "comprar".** O veredicto máximo é `PASSA`. Ver
`plano-ferramenta-cs2.md` e `FASE0.md` para a especificação completa e a
justificação das fontes de dados escolhidas.

## Estado atual

**Fase 1 — coletor.** Ainda não há interface. O objetivo desta fase é só
acumular histórico diário o mais cedo possível — cada dia sem coletor a
correr é histórico perdido para sempre.

## O que este repositório contém

- `collector/` — script Python que recolhe o mercado da Skinport (e, para as
  caixas, também da Steam) e grava um snapshot diário
- `data/` — os snapshots. **Dados de mercado públicos, não a tua carteira.**
- `.github/workflows/collect.yml` — corre o coletor todos os dias às 03:00 UTC

**A tua carteira nunca entra aqui.** Custos, quantidades e P&L ficam sempre no
`localStorage` do teu browser (isso chega na Fase 4). O `.gitignore` bloqueia
qualquer ficheiro que pareça ser de carteira.

## Configuração — passo a passo

Cada passo é um comando. Corre-os um de cada vez, por esta ordem.

### 1. Criar o repositório no GitHub (se ainda não existir)

```bash
gh repo create cs2-market-check --public --source=. --remote=origin
```

### 2. Enviar o código

```bash
git add -A
git commit -m "Fase 1: coletor Skinport + Steam"
git push -u origin main
```

### 3. Confirmar que o Actions está ativo

Os repositórios novos já vêm com o Actions ativo por definição. Confirma em
`https://github.com/<o-teu-utilizador>/cs2-market-check/actions` — deves ver
o workflow "Recolha diária" listado (ainda sem execuções).

### 4. Correr a primeira recolha manualmente

Não é preciso esperar pelas 03:00 UTC. Na página do Actions, clica no workflow
"Recolha diária" → botão **Run workflow** → **Run workflow** (verde).

**O que esperar de ver:** ao fim de uns 15-20 minutos (a maior parte do tempo
é a pausa entre pedidos à Steam, para não ser bloqueado), o workflow fica
verde e aparece um novo commit "Snapshot diário AAAA-MM-DD" com um ficheiro
novo dentro de `data/daily/`.

### 5. Verificar que os dados chegaram

```bash
git pull
```

Depois confirma que `data/health.json` tem a data de hoje e que existe um
ficheiro em `data/daily/<ano>/<mês>/<data>.parquet`.

## Não precisas de nenhuma chave de API

A fonte primária (Skinport) não pede registo. A fonte secundária (Steam,
só para as caixas) também não. Não há nada para configurar em segredos do
GitHub nesta fase.

## Verificação de saúde

`data/health.json` guarda sempre a data do último snapshot bem-sucedido. Se
tiver mais de 48 horas, é sinal de que a recolha parou — a Fase 3 vai mostrar
isto como aviso vermelho no topo da página. Por agora, confirma à mão.

## O que esta ferramenta não faz

- Não prevê preços
- Não recomenda compras
- Não substitui olhar para o gráfico de 1 ano antes de decidir
- Não protege de decisões da Valve
- Não diversifica risco — numa queda, a correlação entre itens de CS2 é quase 1

## Correr localmente (para testar antes de fazer push)

```bash
py -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python collector/run.py --dry-run
```

O `--dry-run` recolhe tudo mas não grava nada — só mostra quantos itens
conseguiu obter de cada fonte. Sem o `--dry-run`, grava o snapshot de hoje.

```bash
.venv/Scripts/python -m pytest tests/ -v
```
