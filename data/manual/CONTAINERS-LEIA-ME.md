# Como verificar o containers.json

Este ficheiro não é trabalho teu por obrigação — já vem preenchido. Mas os dados
vieram de pesquisa, não de mim a abrir o jogo, e por isso **todas as entradas
começam com `"verified": false`**. A ferramenta funciona já assim, mas marca
como incertos os veredictos que dependam de entradas não verificadas (secção
12 da especificação).

## Como verificar uma entrada

1. Abre [csgostash.com](https://csgostash.com) (ou o site que o substituiu,
   `stash.clash.gg`) e procura o nome exato da caixa.
2. Confirma três coisas:
   - **`still_dropping`** — a caixa aparece na lista de "caixas ativas" / drop
     semanal atual?
   - **`rare_slot`** — o item raro da caixa é faca (`knives`) ou luva (`gloves`)?
   - **`discontinued_date`** — quando é que a caixa saiu do drop gratuito?
3. Se estiver certo, muda `"verified": false` para `"verified": true`.
4. Se estiver errado, corrige o campo e também marca `"verified": true`.

## Por onde começar

Prioridade alta — afeta diretamente o teste 6 (bloqueio absoluto), por isso um
erro aqui é o mais grave:

- **Sealed Dead Hand Terminal**, **Sealed Genesis Terminal**, **Kilowatt Case**,
  **Revolution Case**, **Dreams & Nightmares Case** — as 5 caixas que a
  pesquisa encontrou como ativas agora. Se alguma já não estiver, os testes
  bloqueiam-na incorretamente.
- **Fever Case** e **Gallery Case** — são caixas Armory, não drop gratuito. A
  especificação já avisa para não as tratar como descontinuadas, mas vale a
  pena confirmar que a lógica ainda se aplica.
- **Recoil Case** — pesquisa diz que saiu do pool em março de 2026. Se ainda
  estiver a cair, o teste 6 está a deixar passar uma má compra.

Prioridade baixa — são caixas antigas e descontinuadas há anos, um erro na
data exata não muda o veredicto (`still_dropping: false` está certo com
confiança alta em todas):

- Todas as outras 35, principalmente as datas de `discontinued_date`, que
  vêm de memória e podem estar erradas por um ou dois meses.

## O que já é dado como certo (não precisa de verificação urgente)

- **Prisma Case** e **Glove Case** — os dois exemplos que já vinham na
  especificação original, com os valores exatos de lá.
- O facto de a "rare pool" escondida ter sido removida em dezembro de 2025
  (o que tornou *CS:GO Weapon Case* e *Operation Bravo Case* totalmente
  descontinuadas) — confirmado por três fontes independentes de pesquisa.

## Fora deste ficheiro

Este ficheiro só tem caixas de armas (as que dão facas ou luvas). O coletor
também vê ~370 outros "containers" da Skinport — cápsulas de autocolantes,
souvenir packages — que não entram aqui porque os testes 6/7/8 não se aplicam
a eles.
