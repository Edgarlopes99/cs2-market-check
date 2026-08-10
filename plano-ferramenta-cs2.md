# Ferramenta de análise de mercado CS2 — especificação

> Documento para dar ao Claude Code. Escrito em agosto de 2026.

---

## 0. Regra de ouro

**A ferramenta nunca prevê preços.**

Mede três coisas e mais nada:

1. **Liquidez** — consigo sair deste item?
2. **Preço relativo** — está caro ou barato face ao próprio histórico?
3. **Concentração** — estou demasiado exposto a uma coisa só?

No dia em que alguém lhe acrescentar "previsão", "sinal de compra forte" ou um score único de 0–100 que promete performance, a ferramenta deixa de ser útil e passa a ser perigosa. Nenhum dado público prevê preços de skins.

O objetivo não é encontrar vencedores. É **evitar entradas más e posições de que não se consegue sair**.

---

## 1. Arquitetura

Tudo em serviços gratuitos, sem servidor próprio, sem PC ligado.

**Repositório público.** Repositórios públicos têm minutos de GitHub Actions ilimitados; os privados têm limite mensal no plano gratuito. Os dados de mercado são públicos de qualquer forma.

**Mas a carteira nunca vai para o repositório.** Preços de compra, quantidades e P&L são pessoais. Ficam no `localStorage` do browser do utilizador, com exportação/importação por ficheiro JSON para backup. O repositório contém código e preços de mercado; não contém posições nem custos.

```
GitHub repo (público)
├── collector/          Python. Corre por cron no GitHub Actions.
├── data/               Snapshots + histórico de mercado. Público.
├── web/                Página estática. Servida por GitHub Pages.
└── .github/workflows/  Agendamento diário.

Browser do utilizador (privado, nunca sai do PC)
└── localStorage        Carteira: itens, quantidades, custos, teses.
```

**Regra de segurança:** o `.gitignore` deve bloquear qualquer ficheiro de carteira. Se o Claude Code alguma vez sugerir commitar dados de posições, recusar.

**Fluxo diário (03:00 UTC):**

1. Actions acorda
2. Coletor faz 1–3 pedidos às APIs
3. Guarda snapshot em `data/`
4. Calcula scores e verifica regras de alerta
5. Envia alertas se houver
6. Commit dos dados de volta ao repo
7. Pages serve a página atualizada

**Porquê esta arquitetura:**

- GitHub Actions é gratuito e corre sem o PC ligado
- Commitar os dados no repo dá histórico versionado de graça, sem base de dados alojada
- Página estática elimina backend, autenticação e custos
- Se o projeto morrer, os dados ficam legíveis em JSON

**Stack:** Python 3.11+, `httpx`, `pandas`, SQLite (ficheiro no repo) para consultas, HTML+JS simples no frontend. Sem framework pesado.

---

## 2. Fontes de dados

### Fase 0 — verificar antes de escrever código

**Isto é a primeira tarefa e é obrigatória.** As condições dos planos gratuitos mudam. Verificar e documentar o que cada um dá de facto:

| Fonte | O que promete | Verificar |
|---|---|---|
| **cs2.sh** | Bid/ask CSFloat, OHLC 5m–1d, `/v1/archive/csfloat` com vendas reais desde 2022, `/v1/archive/steam` desde 2013, `/v1/liquidity/items` | **O plano grátis dá acesso aos arquivos?** Se sim, resolve o problema do histórico de imediato. |
| **skinstrack** | `/api/v1/free/items` — catálogo CS2 completo com preços Steam, tipo, liquidity score | Limite de pedidos/dia. Frequência de atualização. |
| **steamwebapi.com** | Chave grátis sem cartão. Normaliza CSFloat, Buff, Skinport, DMarket e 20+ mercados no mesmo schema | Limites do plano grátis. |
| **Steam inventory** | `https://steamcommunity.com/inventory/{steamid64}/730/2` | Endpoint não documentado e agressivamente limitado por IP. Testar a partir de um runner do GitHub. |

**Preferência:** endpoints de catálogo completo (1 pedido → milhares de itens) em vez de 1 pedido por item. O limite conta pedidos, não itens.

### Aviso importante sobre listagens vs vendas

A API oficial gratuita da CSFloat é **só de listagens, sem registo de vendas**.

- **Listagem** = o que alguém *pede*
- **Venda** = o que o mercado *pagou*

Preferir sempre dados de venda. Onde só houver listagens, marcar o campo como tal na base de dados e mostrar essa distinção na interface.

---

## 3. Dados que nenhuma API dá

Estes três campos não existem em API nenhuma e têm de ser mantidos à mão num ficheiro `data/manual/containers.json`. São ~40 caixas. Trabalho único de uma tarde.

```json
{
  "Prisma Case": {
    "still_dropping": false,
    "rare_slot": "knives",
    "discontinued_date": "2020-06",
    "notes": "Stiletto, Talon, Ursus, Navaja"
  },
  "Glove Case": {
    "still_dropping": false,
    "rare_slot": "gloves",
    "discontinued_date": "2019-05",
    "notes": ""
  }
}
```

**Campos:**

- `still_dropping` — se ainda cai no jogo, a oferta cresce todos os dias. Reprova automaticamente.
- `rare_slot` — `knives` | `gloves`. Determina a exposição de categoria.
- `discontinued_date` — para calcular há quanto tempo a oferta está fechada.

**Manutenção:** verificar contra as patch notes em `counter-strike.net/news/updates` sempre que houver um update. A ferramenta deve avisar quando detetar um post novo (ver §6).

**Estado conhecido em agosto de 2026 —** ainda em drop ativo: Sealed Dead Hand Terminal, Sealed Genesis Terminal, Kilowatt, Revolution, Dreams & Nightmares. A Fever Case é uma caixa Armory e **não deve ser tratada como descontinuada** — a disponibilidade via Armory afeta a oferta de forma diferente. Confirmar.

---

## 4. Modelo de dados

```sql
items (
  market_hash_name  TEXT PRIMARY KEY,
  item_type         TEXT,      -- container, skin, sticker, capsule, ...
  collection        TEXT,
  still_dropping    BOOLEAN,   -- de containers.json
  rare_slot         TEXT       -- knives | gloves | null
)

prices_daily (
  date              DATE,
  market_hash_name  TEXT,
  ask               REAL,      -- listagem mais baixa
  bid               REAL,      -- buy order mais alta
  volume            INTEGER,   -- unidades vendidas/dia
  listings          INTEGER,   -- listagens ativas
  source            TEXT,
  is_sale_data      BOOLEAN,   -- venda real ou só listagem
  PRIMARY KEY (date, market_hash_name, source)
)

portfolio (
  id, market_hash_name, quantity, cost_eur, acquired_date,
  venue, float_value, pattern_seed, thesis TEXT
)

settings (key, value)          -- limiares ajustáveis

alerts_log (date, type, market_hash_name, message, acknowledged)
```

O campo `thesis` na carteira é obrigatório no formulário. Uma frase: porque é que compraste. Serve para, meses depois, verificar se a razão ainda existe. É a coluna que toda a gente ignora e a que mais evita perdas.

---

## 5. Os 8 testes

Todos os limiares vêm da tabela `settings` e são editáveis na interface. Os valores abaixo são os defaults.

### Testes de saída (consigo vender?)

**1. Fila** — `listings ÷ volume`, em dias
Default: reprova acima de **40 dias**
*Diz-te quantos dias de vendedores estão à tua frente se listares ao preço corrente.*

**2. Spread** — `(ask − bid) ÷ ask`
Default: reprova acima de **5%**
*É o que perdes só por entrar e sair. Um spread de 40% significa que o item só é líquido se aceitares o número de baixo.*

**3. Volume** — unidades/dia
Default: reprova abaixo de **1000/dia** para caixas, **100/dia** para skins
*Sem volume, uma subida de 180% é ruído de duas transações.*

### Testes de preço (está barato?)

**4. Preço vs média** — `ask` contra média de 365 dias
Default: reprova se estiver **acima da média**
*Fallback para 90 dias enquanto não houver 365. Marcar claramente na interface qual está a ser usado.*

**5. Distância ao máximo histórico** — `ask ÷ max(ask)`
Default: avisa se estiver **acima de 80% do ATH**
*Testa se as boas notícias já estão no preço. Um ativo que já teve ganhos enormes tem menos espaço à frente — foi o que aconteceu à Glove Case, que perdeu valor apesar de a oferta estar fechada, porque a subida já tinha acontecido nos anos anteriores.*

### Testes de estrutura (a tese aguenta?)

**6. Ainda cai no jogo** — de `containers.json`
Reprova sempre se `still_dropping = true`
*Oferta a crescer todos os dias. Não há tese possível.*

**7. Alguém está a abrir isto** — tendência de `listings` a 90 dias
Default: avisa se as listagens estiverem **estáveis ou a subir**

*Este é o teste que quase toda a gente esquece. Depois de uma caixa ser descontinuada, a nova oferta pára — mas a oferta só **diminui** se as pessoas continuarem a abrir as que existem. Uma caixa pode ser rara e ser um mau investimento na mesma, se ninguém a quiser abrir. Sem aberturas não há escassez a aumentar: há stock parado sem procura.*

*Proxy: listagens ativas a cair ao longo do tempo = está a ser consumida. Listagens estáveis = ninguém lhe toca.*

**8. Concentração de categoria** — contra a carteira atual
Default: reprova se a categoria já pesar **mais de 40%** da carteira

*Não é uma propriedade do item, é da carteira. O mesmo item passa para uma pessoa e reprova para outra. Exemplo real: uma carteira com 85% de exposição a luvas deve reprovar qualquer caixa cujo `rare_slot` sejam luvas, por muito bons que sejam os outros sete testes.*

### Veredicto

- Qualquer reprova em **6** → `NÃO COMPRAR` (bloqueio absoluto)
- Qualquer reprova em **1, 2, 3, 4, 8** → `NÃO COMPRAR`
- Avisos em **5** ou **7** → `PASSA COM RESERVAS` + mostrar qual
- Tudo limpo → `PASSA`

**A interface nunca deve mostrar "COMPRAR".** O texto máximo é `PASSA` — o filtro elimina más entradas, não identifica vencedores.

---

## 6. Contexto de mercado

Três indicadores no topo do painel. Quando dois estiverem negativos, o painel mostra um aviso global e todos os veredictos `PASSA` passam a `PASSA — mercado em queda`.

| Indicador | Fonte | Sinal negativo |
|---|---|---|
| Jogadores ativos | steamcharts.com/app/730 | Média mensal a descer há 3+ meses |
| Capitalização | csmarketcap.com | A descer há 3+ meses |
| Atividade da Valve | RSS de counter-strike.net/news/updates | Post novo por analisar |

**Detetor de patch notes:** monitorizar o feed. Quando aparecer post novo, criar um alerta a pedir revisão manual do `containers.json`. As alterações mais destrutivas do mercado nos últimos 12 meses — trade-ups de facas e luvas, o fim do rare drop pool, os souvenirs nos trade-ups, a Major Shop — vieram todas daqui, e algumas sem sequer aparecerem nas patch notes.

---

## 7. Módulo de carteira

### Importação

Puxar de `https://steamcommunity.com/inventory/{steamid64}/730/2`.

**Requisitos:** SteamID64 do utilizador, inventário público nas definições de privacidade da Steam.

**Risco técnico conhecido:** o endpoint é não documentado e agressivamente limitado por IP; aplicações com tráfego recebem 429 rapidamente. Os runners do GitHub partilham IPs e podem estar bloqueados.

**Mitigação obrigatória:**
- Sincronizar no máximo 1×/dia
- Cache com fallback para o último snapshot bom
- **Importação CSV manual como alternativa sempre disponível** — se o Steam falhar, a ferramenta continua a funcionar
- Preço de compra e tese não vêm do Steam. São sempre entrada manual.

### Cálculos

**Líquido real CSFloat:**
```
liquido = bid × (1 − 0.02) × (1 − 0.025)
```
2% de comissão de venda, 2,5% de levantamento (escalão mais alto, desce com volume).

**Nunca mostrar P&L contra o preço de listagem ou contra um "reference price".** Sempre contra o `bid` real, que é o que alguém está a pagar agora. A diferença entre os dois chega a 35%.

**Por linha:** custo, líquido atual, P&L em € e %, dias em carteira, tese.

**Agregados:** total líquido, P&L total, e dois alarmes:
- Qualquer linha > 25% da carteira
- Qualquer `rare_slot` > 40% da carteira

---

## 8. Alertas

**Canal: apenas na página. Sem notificações externas.**

Decisão deliberada. Notificações push criam urgência, e urgência é inimiga deste tipo de decisão — foi a pressa que gerou a compra no topo em julho. Um alerta que só aparece quando o utilizador decide abrir a página é lido com calma.

**Implementação:** uma "central de alertas" no topo do painel. Badge com o número de alertas por ler. Cada alerta guarda-se em `alerts_log` com `acknowledged`. Alertas por ler mantêm-se visíveis até serem marcados.

**Não implementar:** email, Telegram, Discord, browser notifications. Se um dia forem pedidos, reler este parágrafo primeiro.

### Regras

| Alerta | Condição | Porquê |
|---|---|---|
| **Sinal de venda** | Item da carteira +15% em 7d **e** volume acima da média de 30d | Subida com volume é o melhor momento de liquidez. É quando se sai bem. |
| **Watchlist entrou** | Item da watchlist passou de reprovado a `PASSA` | Item que estava caro ficou barato |
| **Concentração** | Uma linha passou 25%, ou uma categoria passou 40% | Risco a acumular sem dares conta |
| **Valve mexeu** | Post novo no feed | Rever o `containers.json` |
| **Tese a rever** | Item em carteira há 90 dias sem revisão | Força a verificar se a razão de compra ainda existe |

**Regra de silêncio:** nunca alertar sobre subidas de itens que **não** estão na carteira nem na watchlist. Um alerta de "isto subiu 200%" sobre um item aleatório é um convite a comprar no topo — que é exatamente o erro que esta ferramenta existe para prevenir.

---

## 9. Interface

Página única, estática, três secções.

**Topo — contexto.** Os 3 indicadores de mercado. Aviso global se dois estiverem negativos.

**Meio — carteira.** Tabela por linha: item, qtd, custo, líquido, P&L, dias, tese. Barra de concentração por linha e por categoria. Vermelho quando passa os limiares.

**Fundo — screener.** Tabela ordenável com todos os itens seguidos, colunas: nome, fila, spread, volume, preço, vs média, vs ATH, veredicto. Filtros por tipo e por veredicto. Busca por nome.

**Definições.** Editar os 8 limiares. Guardar em `settings`.

**Regra de apresentação:** cada número mostra sempre a sua unidade e o seu limiar ao lado. Nunca `40`. Sempre `40 dias (limite: 40)`. O objetivo é que o utilizador aprenda a ler os números, não que confie num semáforo.

---

## 10. Fases de construção

**Fase 0 — Verificação de APIs.** Testar as quatro fontes, documentar limites reais, escolher a primária. *Não escrever mais nada antes disto estar feito.*

**Fase 1 — Coletor.** Script Python, snapshot diário, Actions cron, dados versionados em `data/`. Sem interface. Objetivo: começar a acumular histórico o mais cedo possível.

**Fase 2 — `containers.json`.** Preencher as ~40 caixas à mão. Trabalho aborrecido, mas sem isto os testes 6, 7 e 8 não funcionam.

**Fase 3 — Scoring + painel.** Os 8 testes, página estática, definições.

**Fase 4 — Carteira.** Importação Steam + CSV, cálculo do líquido, concentração.

**Fase 5 — Alertas.** Central de alertas na página, sem notificações externas.

**Fase 6 — Contexto.** Jogadores, capitalização, feed da Valve.

A Fase 1 primeiro e sozinha. Cada dia sem coletor é um dia de histórico perdido, e o histórico é a única coisa que não se recupera depois.

---

## 11. Problema do histórico

O teste 4 (preço vs média de 1 ano) é o mais importante e é o que não funciona no dia 1. As APIs grátis dão o preço de hoje, não o do ano passado.

**Três soluções em simultâneo:**

1. **Snapshot diário desde já** — daqui a 12 meses há 365 dias de histórico próprio
2. **Média de 90 dias como métrica de trabalho** até lá, com a interface a indicar claramente qual está a ser usada
3. **Entrada manual dos valores 1Y** para ~10 itens de interesse, para a ferramenta ser útil desde o primeiro dia

**Atalho possível:** se o plano gratuito do cs2.sh der acesso ao `/v1/archive/steam` (mediana e volume da Steam desde 2013) ou ao `/v1/archive/csfloat` (vendas reais desde 2022), o problema desaparece por completo. Verificar na Fase 0.

---

## 12. Instruções para o Claude Code

**O utilizador não escreve código.** Vai correr comandos e usar a ferramenta, nada mais. Isto tem consequências obrigatórias:

**Autonomia.** Não perguntar sobre bibliotecas, estrutura de pastas ou padrões de código. Decidir e explicar em duas linhas o que foi decidido e porquê.

**Um comando por passo.** Cada instrução dada ao utilizador deve ser copiável e colável, uma linha de cada vez. Nunca "configura o ambiente" — sempre o comando exato.

**Falhar em voz alta.** Se uma API não responder, se uma chave estiver errada, se o inventário der 429: mensagem em português claro dizendo o que falhou e o que fazer. Nunca falhar em silêncio nem escrever dados vazios por cima de bons.

**Setup completo no README**, por esta ordem: criar repo, ativar Pages, ativar Actions, obter chaves de API, correr a primeira recolha, abrir a página. Com o que se espera ver em cada passo.

**Verificação de saúde.** A página mostra sempre a data do último snapshot bem-sucedido. Se tiver mais de 48 horas, aviso vermelho no topo. Sem isto, o utilizador pode passar semanas a olhar para dados congelados sem dar por isso.

**O `containers.json` não é trabalho do utilizador.** Gerar uma versão inicial com as ~40 caixas conhecidas, com `still_dropping` e `rare_slot` preenchidos e um campo `verified: false` em cada entrada. A interface mostra quais faltam verificar. O utilizador confirma no csgostash ao seu ritmo, e a ferramenta funciona entretanto — marcando como incertos os veredictos que dependam de entradas não verificadas.

**Testes.** Pelo menos: cálculo da fila, cálculo do spread, cálculo do líquido CSFloat, e os limites dos 8 testes. São as contas de que dependem todas as decisões; se uma estiver errada, a ferramenta mente com confiança.

---

## 13. O que esta ferramenta não faz

Escrever isto no README do projeto:

- Não prevê preços
- Não recomenda compras
- Não substitui olhar para o gráfico de 1 ano antes de decidir
- Não protege de decisões da Valve, que podem apagar qualquer tese de um dia para o outro e sem aviso
- Não diversifica o risco: numa queda, a correlação entre itens de CS2 é praticamente 1, e ter 12 posições não protege de nada

O que faz: impede entradas em itens de que não se sai, e mostra concentração antes de ela custar dinheiro.
