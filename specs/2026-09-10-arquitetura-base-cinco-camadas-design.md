# Uma base reutilizável em cinco camadas, e a GALP 122 como primeira instância

**Data:** 2026-09-10
**Estado:** proposto, aguardando aprovação
**Relação com `2026-09-04-plataforma-portavel-design.md`:** complementa. Aquela spec
governa a elasticidade da camada de inferência e continua valendo por inteiro; esta
governa a divisão em camadas, os repositórios e o contrato entre eles.

---

## 1. O problema

Hoje existe um servidor de inferência que funciona e quatro grupos prontos para
trabalhar em coisas que não existem. O contrato com a GALP (projeto 25961-4 — GALP 122)
pede uma plataforma de avaliação de risco geológico assistida por IA: caracterização
de fatores, cálculo de LoK e PoS, recuperação de evidência, trilha de auditoria. O que
está construído é uma das camadas dela, e a mais genérica das quatro.

Há um segundo problema, que não dói ainda e vai doer no próximo projeto. A organização
tem 25 repositórios; vários são aplicações de IA com necessidade idêntica de estrutura
— base de dados, orquestração de agentes, servidor de inferência, interface. **Nenhum
compartilha uma base, e não é por escolha: não existe base para compartilhar.** Medido
nesta sessão: zero repositórios marcados como template, zero topics, nenhuma propriedade
de organização definida. Cada frente nova recomeça.

O terceiro problema é o que a GALP está de fato comprando, e é o mais caro de errar. A
regra central do contrato (Questionamentos T2D, p. 6) é que dado confidencial da GALP
nunca transita por API externa de modelo. Hoje essa regra não tem dono: ela não é do
armazenamento, não é da inferência e não é da interface. Uma regra sem repositório dono
é uma regra que cada grupo implementa por conta, e o dia em que um não implementar, o
vazamento não reprova teste nenhum — porque nenhuma camada testa a fronteira da outra.

## 2. O que fica verdadeiro ao final

Um pesquisador do instituto que precise de uma plataforma de IA nova declara a ontologia e
os formulários da sua área, escreve só o cálculo que é dela, e recebe as quatro camadas
funcionando. Não reconstrói nenhuma.

Uma correção de segurança na base alcança todas as instâncias por atualização de versão, e
existe uma lista de quem ainda não atualizou.

Um relatório confidencial da GALP não alcança a OpenAI nem a Anthropic — **e isso
continua verdadeiro mesmo com um defeito na camada de aplicação**, porque a credencial
que carrega aquela requisição não tem permissão de sair.

Quatro grupos trabalham em paralelo sem se bloquear, e o que impede um de quebrar o outro
é um teste, não uma conversa.

## 3. As decisões

Três palavras têm sentido fixo daqui em diante, porque a primeira versão desta spec as
confundiu e produziu um erro de projeto: **base** é o conjunto de motores reusáveis;
**instância** é uma plataforma implantada, com prefixo próprio; **domínio** é a área de
aplicação — avaliação de risco geológico — e não nomeia repositório nenhum.

### 3.1 São cinco camadas, e a que faltava é a que importa

O desenho inicial tinha três: dados/conhecimento, inferência, interface. Falta a camada
de aplicação — FastAPI, orquestração de agentes, MCP, guardrails — que a própria proposta
entregue à GALP descreve (p. 8) e que é onde o produto mora.

A alternativa era distribuí-la: cada camada expõe os próprios agentes. Ela é descartada
por um motivo mecânico, não estético. Alguém decide **qual modelo chamar**. Se essa
decisão vive na interface, a interface pode mandar um relatório de prospecto para fora.
Se vive na inferência, o gateway precisa conhecer a classificação do dado, que é
informação da camada de conhecimento. A decisão só é enforçável num lugar que fica
*entre* as três — e distribuí-la significa replicá-la em três repositórios, o que produz
três oportunidades de errar e nenhum teste que cubra as três.

As cinco camadas, com o nome que cada uma carrega em todo repositório, contrato e
propriedade:

| Camada | Possui | **Não** possui |
|---|---|---|
| `knowledge` | Ingestão, relacional, vetorial, grafo RDF, object store, **atribuição da classificação de sensibilidade na origem**, backends de observabilidade | Noção de fluxo de negócio. Não chama modelo. |
| `inference` | Servir tokens: Ray Serve, vLLM, KubeRay, LiteLLM, chaves virtuais, orçamento, elasticidade, **imposição da política de roteamento** | Não conhece o domínio. Não lê a base de conhecimento. |
| `agents` | Fluxos, orquestração, MCP, guardrails, **decisão** de roteamento, trilha de auditoria, explicabilidade | Não persiste conhecimento. Não gerencia GPU. Não renderiza. |
| `interface` | Sessão, layout, formulários, visualização, tela de auditoria | **Não fala com `knowledge` nem com `inference`.** Uma seta só sai daqui. |
| `platform` | Contratos, portão, testes entre camadas, trem de release | Nenhuma linha de lógica de produto. |

A restrição da `interface` é a que torna a auditoria de vazamento tratável. Com uma seta
só, a pergunta "por onde um dado confidencial poderia sair?" tem resposta finita.

### 3.2 Base e instância: os repositórios vêm em pares

A base publica o **motor**; a instância traz o que é só dela. Percorrendo as cinco
camadas, todas têm a mesma forma — um motor que não sabe nada do negócio e um ponto de
extensão declarado.

A alternativa era o *template repository*: a instância clica em "Use this template", ganha
uma cópia e é dona dela. É mais simples hoje e mais barato de construir. Custa o
seguinte, projetado para frente: a divergência é permanente e invisível. No primeiro
conserto de segurança na base, cinco instâncias ficam desatualizadas e ninguém consegue
listar quais — porque uma cópia não guarda de onde veio.

Há um segundo motivo, e ele torna o par obrigatório em vez de preferível. **A metodologia
GRA e a taxonomia de sensibilidade da GALP são confidenciais.** Não podem morar num
repositório de base que se quer reutilizar e eventualmente abrir. A fronteira
público/privado cai exatamente entre motor e instância — a mesma linha que a escolha de
dependência versionada já desenha.

**A fronteira é reuso, não código versus configuração.** Isso precisa estar dito porque a
leitura errada é natural e cara. O repositório de instância **carrega código de domínio**,
não apenas declarações: a GALP 122 pede cálculo de LoK e de PoS, validação de questionário
e regras de metodologia, e isso é software — não cabe em YAML e não deve ser tentado em
YAML. O que separa as duas colunas é uma pergunta só: *serve a mais de uma instância?* Se
serve, é motor. Se não, é instância — seja um arquivo de ontologia ou dois mil linhas de
Python.

```
        BASE (reusável)                    INSTÂNCIA G122 (privada)
  ┌─────────────────────────────┐    ┌──────────────────────────────────┐
  │ base-platform   contratos   │◄───│ g122-platform   schemas          │
  │ base-knowledge  motores     │◄───│ g122-knowledge  ontologia        │
  │ base-inference  Ray/vLLM    │◄───│ g122-inference  modelos          │
  │ base-agents     runtime     │◄───│ g122-agents     fluxos, LoK, PoS │
  │ base-interface  shell       │◄───│ g122-interface  formulários      │
  └─────────────────────────────┘    └──────────────────────────────────┘
     serve a toda instância               serve só a esta
```

Cada grupo passa a ter dois repositórios: o motor da sua camada e a instância G122 dela.

**O custo disso, dito por inteiro: a G122 fica mais lenta de construir.** Toda vez que um
grupo precisar de algo que o motor não expressa, o caminho deixa de ser "escrevo no
repositório da instância" e passa a ser "abro um ponto de extensão no motor, versiono, e
então uso". Esse é o preço de ter uma base, e ele é cobrado inteiro na primeira instância,
que é justamente a que tem prazo contratual.

**A regra que contém esse custo, e ela é vinculante:** *o motor só ganha um ponto de
extensão quando duas instâncias pedem o mesmo, ou quando a primeira pede algo que é
confidencial e por isso não pode entrar no motor.* Até lá, a instância escreve código no
repositório dela. Um motor guiado por dados projetado antes da segunda instância é uma API
de plugin para plugins que não existem — generaliza-se o que era fácil e engessa-se o que
não era.

### 3.3 A regra de roteamento é decidida num lugar e imposta em outro

`agents` decide; `inference` impõe. As duas, e não uma.

O mecanismo da imposição já existe neste repositório e não custa nada: o LiteLLM emite
chaves virtuais com política de acesso por modelo — é o que o `colleague.sh` usa hoje
para os *access grants* do Open WebUI (ADR-009, ADR-010). Em vez de uma família de
chaves, duas: `local-only`, que alcança apenas os modelos servidos pelo vLLM, e
`external`, que alcança GPT/Claude/Gemini.

A camada de agentes escolhe a chave a partir da classificação máxima presente no
contexto da requisição. A camada de inferência não confia nessa escolha — ela apenas
serve o que a chave permite.

Sem a segunda metade, a promessa da p. 6 depende de um `if` estar correto em código que
quatro pessoas editam. Com ela, depende de uma política no gateway, testável sozinha, sem
subir a aplicação.

```
  Pessoa (VPN) ──► interface ──C3──► agents ──C2──► inference ──► GPT/Claude
                                        │                ▲          (só com
                                        C1               │        chave external)
                                        ▼                │
                                    knowledge ───────────┘
                              (classificação nasce aqui)
```

### 3.4 Trem de release único, com cadência fixa

Nada chega a produção sozinho: `base-platform` declara a versão de cada camada e um merge
nele é o release. A GALP recebe um número de versão só.

A alternativa era release independente barrado por contrato, que dá mais autonomia aos
quatro grupos. Ela é descartada porque a plataforma é entregue a um cliente que precisa
saber o que está rodando, e porque a regra de roteamento atravessa três camadas — um
release parcial pode publicar a decisão sem a imposição.

**O custo, e ele é o modo previsível de essa escolha falhar:** a camada mais lenta dita o
ritmo das quatro. O grupo de interface termina uma tela na terça e ela sai três semanas
depois porque `knowledge` está no meio de uma migração. Depois de duas ocorrências, os
grupos param de esperar e implantam por fora — e aí não há nem autonomia declarada nem
garantia real.

**A contenção é cadência fixa.** O trem parte no dia marcado com o que estiver pronto;
quem não embarcou pega o próximo. **O trem nunca espera.** Isso preserva a versão única e
tira do desenho a espera indefinida.

A cadência proposta é **semanal**, e ela é uma decisão desta spec e não uma sugestão — um
trem sem data marcada é um trem que espera. Ela é revista uma vez, depois da primeira
viagem em E3, quando existir uma medição em vez de um palpite.

### 3.5 O agrupamento no GitHub, e o que ele não tem

Medido nesta sessão: **o GitHub não tem pastas nem subgrupos de repositórios.** Não existe
equivalente ao subgrupo do GitLab. O que existe, e o estado de cada um nesta organização:

- **Custom properties** de organização — o schema responde `[]`: disponível, nunca usado.
  É o mais próximo de pasta que existe, porque filtra de verdade
  (`?q=props.camada:knowledge`).
- **Repositório `.github` com `profile/README.md`** — não existe. É a página que o GitHub
  renderiza na entrada da organização.
- **Topics** — zero em 25 repositórios.
- **Template repository** — zero. É mecanismo de replicação, não de agrupamento, e a
  decisão de 3.2 o descarta como forma de consumo.

A decisão é combinar os três primeiros: propriedades para a máquina filtrar,
`profile/README.md` como vitrine, e `base-platform` como o índice detalhado. Organização
separada fica adiada; ela passa a valer no dia em que um cliente precisar de acesso a uma
instância sem enxergar as outras, e migrar depois custa mover repositórios, não redesenhar.

### 3.6 Nomes

Padrão `<prefixo>-<camada>`, com as cinco camadas de 3.1. A base usa `base-`; cada
instância usa o **código do contrato** — `g122-`, de GALP 122 / 25961-4.

As três alternativas e o que cada uma custaria no dia em que os eixos divergirem.
`gra-` nomearia a metodologia, que é propriedade da GALP e existe antes deste projeto:
carregá-la num repositório do instituto mistura o que é nosso com o que é deles — a mesma
fronteira que 3.2 existe para deixar limpa — e não comporta o dia em que a metodologia GRA
for aplicada para outro cliente. `galp-` nomearia o cliente, e colide se a GALP contratar
uma segunda plataforma. `gra-ia-` nomearia o produto, e é a mais defensável das três;
perde só por vazar a metodologia no nome de um repositório.

**O custo do código de contrato é ser opaco, e ele se paga com uma linha:** o índice em
`base-platform` mapeia cada prefixo de instância para o que ele é, e é a primeira tabela
do arquivo. Sem ela, `g122` é um enigma para quem chegar em seis meses.

`idia-server` passa a `base-inference`. Medido: existem 437 ocorrências de `idia` no
repositório e apenas 28 de `idia-server`. **O CLI `./idia`, o volume `idia_hf_cache` e o
container `idia-webui` não mudam** — `idia` continua sendo o nome da ferramenta do
instituto, e o prefixo é convenção de repositório. As duas coisas foram desacopladas de
propósito, porque amarrá-las tornaria a escolha do nome uma decisão de custo em vez de uma
decisão de clareza.

Das 28, duas categorias custam: `install_service.sh` e `uninstall_service.sh` usam
`idia-server` como nome de unit do systemd. Uma máquina já provisionada não ganha o nome
novo sozinha — fica com um serviço órfão subindo a stack antiga. O rename carrega um passo
de migração, não um `sed`.

## 4. A ordem do trabalho

Cada etapa destrava a seguinte. A ordem é dependência, não preferência.

**E0 — O grupo existe e é visível.** As propriedades de organização são definidas, o
`profile/README.md` nasce, `base-platform` nasce com os contratos e o processo de adaptação,
e `idia-server` vira `base-inference`. Vem primeiro porque é o que dá aos quatro grupos um
lugar para ler antes de um lugar para escrever.

**E1 — Os contratos existem antes do código.** `base-platform` carrega C1–C4 como schema
versionado, mais um falso executável de cada camada. Vem antes de E2 porque quatro
repositórios vazios criados sem contrato são quatro grupos escrevendo contra interfaces
imaginadas, e a dívida de integração nasce na segunda-feira.

**E2 — O portão é um só.** O `scripts/gate.sh` de hoje vira artefato compartilhado,
consumido pelos dez repositórios por versão. Vem antes de E3 porque um portão replicado
diverge na primeira semana — é literalmente o defeito que o `serve_config.yaml` já teve
(ARCHITECTURE §5.3), e replicá-lo por dez multiplica por dez.

**E3 — Os esqueletos sobem juntos.** As cinco camadas base respondem com dados falsos, o
`base-platform` prova que os falsos não mentiram, e o trem faz a primeira viagem. É o
primeiro momento em que "tudo sobe junto" é medido em vez de afirmado.

**E4 — A G122 aterrissa.** Os cinco repositórios de instância nascem e recebem a
metodologia GRA: ontologia, taxonomia, formulários, os fluxos, e **o código de cálculo de
LoK e PoS** — que é software, não declaração (3.2). A partir daqui os quatro grupos
trabalham em paralelo de verdade.

**E5 — As fronteiras erradas são corrigidas.** O Open WebUI sai de `inference` para
`interface`; o `colleague.sh` se parte na costura que ele hoje atravessa. Fica por último
porque é o único item que mexe em algo que funciona, e mexer nele antes de E3 remove a
única prova viva que o projeto tem.

## 5. O que está medido e o que não está

Esta seção existe porque documento que apresenta cinco valores como igualmente confirmados,
tendo medido três, é pior do que documento sem tabela.

**Medido nesta sessão:**

- O `idia-server` tem 2.622 linhas executáveis (`idia`, `scripts/`, `render_config.py`),
  mais de 5.000 de teste, 7 serviços de Compose, 16 issues abertas e 13 ADRs.
- 437 ocorrências de `idia`, 28 de `idia-server`, distribuídas em 32 arquivos.
- A organização tem 25 repositórios; zero templates, zero topics, schema de propriedades
  vazio, sem repositório `.github`.
- `GRA-AI-prototypes` (12 MB, HTML), `kif` e `quail` existem e ocupam parte destas caixas.
- O token em uso tem `admin:org`, `repo` e `delete_repo` — todas as ações de E0 são
  executáveis.

**Não medido, e esta spec não deve ser lida como se fosse:**

- **Se `kif` e `quail` servem como dependência de `base-knowledge` e `base-agents`.** A
  suposição desta spec é que sim, e ela não foi verificada contra a API de nenhum dos dois.
  Se estiver errada, muda o conteúdo dos motores, não a topologia.
- **Se o Open WebUI serve como `base-interface`** ou se a interface da G122 exige um
  frontend próprio. Depende dos formulários, que não existem.
- **O esforço de E4.** Nenhuma estimativa aqui foi calculada contra o volume real da
  metodologia GRA.
- **Nada sobre custo, cota de GPU ou cluster.** Continua valendo o que a spec de 2026-09-04
  já registra como não medido, incluindo a cota de GPU na conta AWS (issue #31).

## 6. Fora de escopo, deliberadamente

- **Organização separada para a base.** Adiada em 3.5, com o gatilho escrito.
- **Segunda instância.** A base é desenhada para receber uma, e a regra de 3.2 impede que
  ela seja projetada para uma que não existe.
- **SSO e identidade institucional.** Continua fora, pelo motivo da spec anterior.
- **Multi-tenant.** Continua fora. A fronteira base/instância não é fronteira de
  isolamento de inquilino, e confundir as duas é a decisão cara de adiar mal.

---

## Apêndice — mecanismo

Nada abaixo é necessário para julgar o que está acima.

### Os quatro contratos

Vivem em `base-platform`, não na camada que os implementa. Mudar um é um PR lá, com
`CODEOWNERS` exigindo aprovação dos dois grupos afetados — é o que impede uma camada de
quebrar a outra em silêncio.

| | De → Para | Invariante |
|---|---|---|
| **C1** | `knowledge` → `agents` | Toda resposta carrega `classification` e `provenance`. Não existe caminho de leitura sem classificação. |
| **C2** | `agents` → `inference` | OpenAI-compatible. A chave é função da classificação máxima do contexto. |
| **C3** | `interface` → `agents` | A única seta que sai da interface. |
| **C4** | todas → `knowledge` | Telemetria: traces e métricas. Direção única, sem resposta. |

### Os pontos de extensão, por camada

É a metade **declarativa** do "processo de adaptação" que uma instância nova preenche. A
outra metade é código de domínio no repositório da instância, e 3.2 explica por que as
duas coexistem.

| Camada | A instância declara |
|---|---|
| `knowledge` | `ontology/` (RDF/OWL), `connectors/` (fontes), `taxonomy.yaml` (classes de sensibilidade **e a política de chave de cada classe**) |
| `inference` | `models.yaml` (modelos servidos e política de chave por classe) |
| `agents` | `flows/`, `prompts/`, `tools/` (declaração MCP) |
| `interface` | `forms/`, `views/` |
| `platform` | `schemas/` (payloads de C1–C4), `versions.yaml` |

`taxonomy.yaml` é onde a regra de roteamento vira parâmetro: uma classe declara
`key-policy: local-only`, e é o motor de inferência que a impõe. A regra fica configurável
por instância sem deixar de ser imposta pelo motor.

### Testar sem subir a plataforma

Cada camada testa contra um **falso** do vizinho, não contra o vizinho. O molde existe:
`tests/bats/helpers/fake_litellm.py` e o `docker` de mentira em `tests/bats/helpers/bin/`.
Os quatro grupos rodam a suíte inteira num laptop sem GPU e sem cluster.

`base-platform` roda o único teste que ninguém mais pode rodar: as camadas reais juntas,
provando que os falsos não mentiram.

### Custom properties

Duas propriedades, definidas uma vez em `orgs/PUC-Behring-AI/properties/schema`:

- `camada` — enum: `platform`, `knowledge`, `inference`, `agents`, `interface`
- `papel` — enum: `base`, `instancia`

Isso dá `?q=props.papel:base` como a listagem do grupo, e `?q=props.camada:knowledge` como
a listagem de uma camada através das instâncias. É metadado de organização: quem edita
precisa de permissão, ao contrário de topic.

### Fronteiras erradas hoje, e por que E5 é último

- O **Open WebUI** roda no `docker-compose.yml` do servidor de inferência, publicado na
  3001 (ADR-013). É interface morando em `inference`.
- O **`colleague.sh`** (676 linhas) faz duas coisas de camadas diferentes num comando:
  emite chave virtual no LiteLLM (`inference`) e cria conta com *access grants* no SQLite
  do Open WebUI (`interface`). Os dois lados estão acoplados por nome de container fixo.

São exatamente a costura entre duas camadas, e hoje são um script só. Nenhum bloqueia esta
spec; ambos precisam estar nela como dívida nomeada, ou viram surpresa do grupo de
interface.

### Fontes

- Questionamentos T2D — v2 (projeto 25961-4 / GALP 122), p. 2–3 (dados e stack), p. 6
  (controle central de confidencialidade), p. 8–9 (arquitetura de referência, metodologia).
- `specs/2026-09-04-plataforma-portavel-design.md` — elasticidade e portabilidade da camada
  de inferência.
- `docs/ADR.md` — ADR-009 (visibilidade por access grant), ADR-010 (`colleague.sh`),
  ADR-013 (Open WebUI no Compose).
- `docs/ARCHITECTURE.md` §5.3 — o custo medido de uma definição duplicada.
