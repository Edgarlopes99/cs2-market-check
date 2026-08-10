# FASE 0 — Verificação das APIs

**Data dos testes:** 2026-08-07
**Método:** pedidos HTTP reais a partir do PC do Edgar (não simulados, não copiados da documentação).

---

## Resposta curta à pergunta mais importante

> *O plano gratuito do `cs2.sh` dá acesso aos endpoints de arquivo (`/v1/archive/csfloat`, `/v1/archive/steam`)?*

**Não. E é pior do que isso: o cs2.sh não tem plano gratuito nenhum.**

O que existe é um teste de 2 dias do plano *Developer* — e o plano Developer **também não inclui os arquivos**. Os arquivos só existem no plano *Scale*, a **200 $/mês**.

Teste feito:

```
GET https://api.cs2.sh/v1/archive/steam?market_hash_name=Prisma Case
→ HTTP 401 {"error":"unauthorized","message":"missing Authorization header"}
```

Tabela de planos confirmada em cs2.sh/pricing:

| Plano | Preço | Inclui arquivos? |
|---|---|---|
| Teste 2 dias | 0 € | **Não** |
| Developer | 75 $/mês | **Não** |
| Scale | 200 $/mês | Sim |
| Enterprise | sob consulta | Sim |

Isto viola a restrição "tudo em serviços gratuitos". **O cs2.sh está fora.**

---

## Mas encontrei uma fonte que a especificação não previa

Enquanto testava alternativas, testei a **API pública da Skinport**. Não estava na especificação e é, de longe, a melhor fonte encontrada.

**Não precisa de chave. Não precisa de registo. Não precisa de cartão. Não precisa de conta.**

Dois pedidos por dia chegam para quase tudo o que a ferramenta precisa:

### Pedido 1 — catálogo com listagens

```
GET https://api.skinport.com/v1/items?app_id=730&currency=EUR
→ HTTP 200 | 1,0 MB | 1,0 s | 25 163 itens
```

Campos: `market_hash_name`, `min_price`, `max_price`, `mean_price`, `median_price`, `suggested_price`, `quantity`, `updated_at`.

### Pedido 2 — vendas reais

```
GET https://api.skinport.com/v1/sales/history?app_id=730&currency=EUR
→ HTTP 200 | 1,9 MB | 36 094 itens
```

Para cada item, quatro janelas — **24 horas, 7 dias, 30 dias e 90 dias** — cada uma com `min`, `max`, `avg`, `median` e `volume`.

Exemplo real recolhido hoje (Prisma Case):

```json
"last_30_days": { "min": 0.86, "max": 1.38, "avg": 1.12, "median": 1.12, "volume": 7732 },
"last_90_days": { "min": 0.82, "max": 1.52, "avg": 1.21, "median": 1.18, "volume": 42464 }
```

**Isto é `volume` de vendas concretizadas, não de listagens.** É a distinção crítica da secção 2 da especificação, e a Skinport dá o lado certo dela de graça.

### Verificação de que as contas dão

Calculei o teste 1 (fila) com os dados descarregados hoje, sem inventar nada:

| Caixa | Listagens | Vendas/dia (média 30d) | Fila |
|---|---|---|---|
| Prisma Case | 55 576 | 257,7 | **215,6 dias** |
| Revolution Case | 16 885 | 95,5 | **176,7 dias** |
| Glove Case | 7 948 | 54,3 | **146,5 dias** |
| Kilowatt Case | 15 500 | 170,2 | **91,1 dias** |

Todas reprovariam o limite default de 40 dias. As contas funcionam com dados reais.

Confirmei também que os **40 itens com "Case" no nome têm todos dados de venda** — ou seja, a cobertura das ~40 caixas da secção 3 está completa.

### Limites reais

| | |
|---|---|
| Autenticação | Nenhuma |
| Limite | 8 pedidos por 5 minutos (`/v1/items`) |
| Cache | 5 minutos |
| Obrigatório | Compressão Brotli — sem ela devolve **HTTP 406** (confirmado por erro meu no primeiro teste) |
| Custo | 0 € |

Com 1 recolha por dia, gasto 2 dos 8 pedidos disponíveis a cada 5 minutos. Sobra folga de 100×.

---

## As quatro fontes da especificação, uma a uma

### 1. cs2.sh

| | |
|---|---|
| Sem cartão? | **Não** — nem sequer há plano grátis |
| Limite real | Ilimitado, mas a partir de 75 $/mês |
| Vendas ou listagens? | Vendas reais (CSFloat desde 2022, Steam desde 2013) |
| Histórico? | Sim, excelente — **mas só no plano de 200 $/mês** |

**Veredicto: fora.** A qualidade dos dados é a melhor do mercado e não serve de nada a este projeto.

### 2. skinstrack

| | |
|---|---|
| Sem cartão? | Sim, mas exige registo e chave |
| Limite real | **50 pedidos por mês** (≈ 1,6/dia) |
| Vendas ou listagens? | Listagens da Steam + `liquidity score` próprio; sem registo de vendas |
| Histórico? | Não |

Teste feito:

```
GET https://api.skinstrack.com/v1/free/items
→ HTTP 502 (sem chave, servidor instável)
→ HTTP 401 {"success":false,"message":"Invalid API key."} (com chave falsa)
```

**Veredicto: dispensável.** 50 pedidos/mês não chegam para 1 recolha diária (precisaria de 30). E o que dá, a Skinport dá melhor e sem limite prático.

### 3. steamwebapi.com

| | |
|---|---|
| Sem cartão? | Sim — entra-se com a conta Steam |
| Limite real | **2 pedidos/minuto, 5/dia, 10/mês** no plano grátis |
| Vendas ou listagens? | Ambos, agregando 20+ mercados |
| Histórico? | Até 365 dias de histórico Steam por item |

O endpoint `items` (catálogo completo num pedido) está **excluído do plano grátis** — passou a ser só para subscritores.

**Veredicto: uso pontual e cirúrgico.** 10 pedidos/mês não servem para recolha diária. Mas servem exatamente para o ponto 3 da secção 11 da especificação: preencher à mão os valores de 1 ano para ~10 itens de interesse. Dois meses de plano grátis chegam para os 10 itens todos, e são 0 €.

### 4. Steam (inventário e preços)

**Inventário:**

```
GET https://steamcommunity.com/inventory/{steamid64}/730/2
→ HTTP 403 (perfil de teste com inventário privado)
```

O endpoint responde a partir de um IP doméstico. O risco descrito na especificação confirma-se: exige inventário público e é sensível a IP. **Não testei a partir de um runner do GitHub** — só o consigo fazer na Fase 1, quando houver Actions a correr.

**Preços — descoberta secundária útil:**

```
GET https://steamcommunity.com/market/priceoverview/?appid=730&currency=3&market_hash_name=Prisma Case
→ HTTP 200 {"success":true,"lowest_price":"1,88€","volume":"6,357","median_price":"1,88€"}
```

Funciona sem chave e sem registo. Cinco pedidos seguidos passaram todos. O `volume` são vendas reais das últimas 24 horas **em toda a Steam** — cobertura global, ao contrário da Skinport que só vê o próprio mercado.

Limitação: 1 pedido = 1 item, e a Steam corta por IP acima de ~20 pedidos/minuto. Serve para uma lista curta (as ~40 caixas), não para 25 000 itens.

O `itemordershistogram` (que daria as buy orders, e portanto o spread) devolveu `{"success":104}` — precisa de um `item_nameid` interno que só se obtém a partir da página do item, e essa página devolveu **HTTP 302** aos meus pedidos. Fica por resolver.

---

## O buraco que fica

**Não consegui encontrar `bid` (buy order) gratuito.**

A Skinport não tem buy orders — o modelo dela é só listagens. Sem `bid`:

- **Teste 2 (spread)** não é calculável como está especificado
- **O cálculo do líquido da carteira** (secção 7) não é calculável como está especificado

Duas saídas possíveis, e é uma decisão tua:

**A)** Usar a mediana de venda dos últimos 7 dias da Skinport como aproximação ao `bid`. É defensável — é o que o mercado pagou mesmo, recentemente. Não é o que alguém paga *agora*, mas é honesto e está do lado certo (conservador). O spread passa a ser `(listagem mais baixa − mediana de venda 7d) ÷ listagem mais baixa`, e a interface diz claramente que é uma aproximação.

**B)** Insistir no `itemordershistogram` da Steam, resolvendo o problema do `item_nameid`. Dá o bid verdadeiro da Steam, mas é frágil: endpoint não documentado, limitado por IP, e provavelmente bloqueado nos runners do GitHub.

**Recomendo a A.** É a que funciona sem depender de nada frágil, e o princípio da ferramenta é ser conservadora, não precisa.

---

## Recomendação de fonte primária

**Primária: Skinport.** Grátis, sem registo, vendas reais, catálogo completo em 2 pedidos, 90 dias de histórico já incluídos no primeiro dia.

**Secundária: Steam `priceoverview`,** ~40 pedidos/dia só para as caixas, para ter volume global além do volume da Skinport.

**Pontual: steamwebapi grátis,** 10 pedidos/mês para semear o histórico de 1 ano dos itens que te interessam.

**Fora: cs2.sh** (pago) **e skinstrack** (limite inútil).

### O que isto muda na especificação

| Teste | Situação |
|---|---|
| 1 — Fila | **Funciona hoje** |
| 2 — Spread | Funciona com aproximação (decisão A acima) |
| 3 — Volume | **Funciona hoje** |
| 4 — Preço vs média | **Funciona a 90 dias já hoje.** Os 365 dias vêm em 12 meses de snapshots, ou à mão para 10 itens |
| 5 — Distância ao ATH | Máximo de 90 dias hoje; ATH verdadeiro acumula-se com o tempo |
| 6 — Ainda cai no jogo | Não depende de API — vem do `containers.json` |
| 7 — Tendência de listagens | Precisa de 90 dias de snapshots próprios. **Só arranca daqui a 3 meses** |
| 8 — Concentração | Não depende de API — vem da carteira |

Cinco dos oito testes funcionam desde o primeiro dia. Isto é bastante melhor do que a especificação assumia no pior cenário.

**O ponto que se mantém válido e urgente:** o teste 7 e o histórico de 1 ano não se recuperam depois. Cada dia sem coletor é um dia perdido para sempre. A Fase 1 devia arrancar já.

---

## Decisões confirmadas

1. **Bid = mediana de venda a 7 dias** (opção A). A interface marca sempre que é aproximação.
2. **Repositório:** `cs2-market-check`, público.
3. **Universo de recolha:** todos os itens do catálogo Skinport (~22 000), não só as caixas. O volume
   usado no teste 3 vem sempre da Steam (`priceoverview`), nunca da Skinport, porque as escalas são
   incomparáveis (ver secção "O que isto muda").

Não é preciso criar contas nem obter chaves para a Fase 1 — a Skinport não pede nada. Avança-se para o coletor.
