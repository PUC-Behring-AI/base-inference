# Plano de implementação — documentação da base e das instâncias

> **Para quem executa:** use `superpowers:subagent-driven-development` para tocar
> tarefa a tarefa. Os passos usam caixa (`- [ ]`) para acompanhamento.

**Objetivo:** Fazer nascer os onze repositórios da arquitetura em cinco camadas,
cada um contendo **apenas documentação** — nenhuma linha de código de produto.

**Abordagem:** A organização ganha metadado que a torna filtrável; `base-platform`
nasce como a fonte única dos contratos e do processo de adaptação; `idia-server`
é renomeado e fechado; os oito repositórios restantes nascem com README e adendo
de `AGENTS.md` apontando para a base.

**Ferramentas:** `gh` CLI (token já tem `admin:org`, `repo`, `delete_repo`),
Markdown. Nada além disso.

**Spec de origem:** `specs/2026-09-10-arquitetura-base-cinco-camadas-design.md`
(aprovada em 2026-09-10). Este plano cobre a metade documental de E0 e E1.

---

## Idioma — regra deste plano

**Todo conteúdo de repositório é em inglês.** README, `AGENTS.md`, `docs/`,
`CODEOWNERS`, nomes de arquivo, nomes e valores de propriedade da organização,
descrições de repositório, mensagens de commit.

**Duas exceções, e o motivo de cada uma:**

- **`specs/`** permanece em PT-BR. É o registro de decisão, escrito para quem
  aprova, e o `idia-server` já tem uma spec em PT-BR (`2026-09-04`). Misturar
  idioma dentro de `specs/` é pior do que a fronteira.
- **`.claude/noturno`** permanece em PT-BR. É adendo a um prompt em PT-BR de um
  sistema que o dono do repositório escreveu; traduzir só metade quebra a leitura.

Se qualquer uma das duas estiver errada, corrija antes da Tarefa 3 — depois dela
o custo é reescrever em vez de escrever.

**Consequência nos nomes de arquivo**, em relação a como a spec os cita:

| Spec (PT-BR) | Repositório (EN) |
|---|---|
| `docs/ARQUITETURA.md` | `docs/ARCHITECTURE.md` |
| `docs/CONTRATOS.md` | `docs/CONTRACTS.md` |
| `docs/ADAPTACAO.md` | `docs/ADAPTATION.md` |
| propriedade `camada` | propriedade `layer` |
| propriedade `papel` | propriedade `role` |
| valor `instancia` | valor `instance` |

---

## O que este plano NÃO faz

Escrito porque a fronteira foi pedida explicitamente e é fácil de atravessar sem
perceber.

- **Nenhum código de produto.** Sem FastAPI, sem schema SQL, sem manifesto Helm,
  sem esquema de agente.
- **Nenhum contrato executável.** C1–C4 entram como *prosa e tabela* em
  `docs/CONTRACTS.md`. Virar JSON Schema versionado é E1, plano seguinte.
- **Nenhum falso executável.** Idem — é E1.
- **O portão compartilhado não é extraído.** `scripts/gate.sh` continua onde
  está. E2 é outro plano.

---

## Estrutura de arquivos

Onze repositórios em `PUC-Behring-AI`. Todos privados, exceto `.github`.

```
PUC-Behring-AI/
├── .github/                       CRIAR — público (exigência do GitHub)
│   └── profile/README.md          a vitrine da organização
│
├── base-platform/                 CRIAR — a fonte
│   ├── README.md                  índice; primeira tabela = mapa de prefixos
│   ├── CODEOWNERS                 veto por grupo sobre o próprio contrato
│   ├── .claude/issue-vizinhas
│   ├── docs/ARCHITECTURE.md       as cinco camadas, diagramas, roteamento
│   ├── docs/CONTRACTS.md          C1–C4 e como se muda um
│   ├── docs/ADAPTATION.md         como nasce uma instância
│   ├── docs/AGENTS-base.md        a parte comum do AGENTS.md
│   └── specs/2026-09-10-...md     a spec (PT-BR), movida para cá
│
├── base-inference/                RENOMEAR de idia-server, fechar
├── base-knowledge/                CRIAR
├── base-agents/                   CRIAR
├── base-interface/                CRIAR
│
├── g122-platform/                 CRIAR
├── g122-knowledge/                CRIAR
├── g122-inference/                CRIAR
├── g122-agents/                   CRIAR
└── g122-interface/                CRIAR
```

Cada repositório de camada (os nove que não são `base-platform`) recebe três
arquivos e nada mais: `README.md`, `AGENTS.md`, `.claude/issue-vizinhas`.

---

## Fase A — a organização fica filtrável

### Tarefa 1: Definir as propriedades customizadas da organização

**Onde:** API da organização, sem arquivo local.

- [ ] **Passo 1: Confirmar que o schema está vazio**

```bash
gh api orgs/PUC-Behring-AI/properties/schema
```

Esperado: `[]`. Se vier qualquer coisa, **pare** — alguém definiu propriedades
entre a escrita deste plano e agora, e cada `PATCH` substitui o schema inteiro.
Nesse caso, some as duas propriedades abaixo ao que já existe.

- [ ] **Passo 2: Criar as duas propriedades**

```bash
gh api --method PATCH orgs/PUC-Behring-AI/properties/schema --input - <<'JSON'
{
  "properties": [
    {
      "property_name": "layer",
      "value_type": "single_select",
      "required": false,
      "description": "Architecture layer this repository belongs to",
      "allowed_values": ["platform", "knowledge", "inference", "agents", "interface"]
    },
    {
      "property_name": "role",
      "value_type": "single_select",
      "required": false,
      "description": "base = reusable engine; instance = deployed platform",
      "allowed_values": ["base", "instance"]
    }
  ]
}
JSON
```

- [ ] **Passo 3: Verificar**

```bash
gh api orgs/PUC-Behring-AI/properties/schema --jq '.[].property_name'
```

Esperado, duas linhas: `layer` e `role`.

**Se o Passo 2 devolver `422`**, a forma do corpo mudou desde a escrita deste
plano. O `GET` do Passo 1 é a fonte: crie uma propriedade pela interface web,
releia o schema, e use a forma que ele devolver. Não invente variações do JSON
por tentativa.

---

### Tarefa 2: Criar o repositório `.github` com a vitrine da organização

**Arquivos:**
- Criar: `.github/profile/README.md`

- [ ] **Passo 1: Confirmar que o repositório não existe**

```bash
gh api repos/PUC-Behring-AI/.github
```

Esperado: `404 Not Found`. Se existir, **pare** e leia o conteúdo antes de tocar.

- [ ] **Passo 2: Criar o repositório**

O `.github` precisa ser **público** para o GitHub renderizar o perfil da
organização. É a única exceção à regra "tudo privado", e ela é deliberada: o
perfil não contém nada além de nomes de repositório e descrições de uma linha.

```bash
gh repo create PUC-Behring-AI/.github --public \
  --description "Organisation profile and shared configuration"
git clone git@github.com:PUC-Behring-AI/.github.git ~/Documents/Github/puc-behring-github
cd ~/Documents/Github/puc-behring-github
mkdir -p profile
```

- [ ] **Passo 3: Escrever `profile/README.md`**

```markdown
# PUC-Behring AI Institute

Applied artificial intelligence research — PUC-Rio.

## The platform base

Five reusable engines that any AI project here is assembled on top of, rather
than rebuilt.

| Repository | Layer | What it does |
|---|---|---|
| `base-platform` | `platform` | Inter-layer contracts, quality gate, release train. **Start here.** |
| `base-knowledge` | `knowledge` | Relational, vector, RDF graph, object store — and the sensitivity classification of every record |
| `base-inference` | `inference` | Ray Serve + vLLM + LiteLLM: serving models with elasticity and a key per person |
| `base-agents` | `agents` | Agent runtime, MCP wiring, guardrails, audit trail |
| `base-interface` | `interface` | Application shell: session, forms, visualisation |

Always-current listing:
[`props.role:base`](https://github.com/orgs/PUC-Behring-AI/repositories?q=props.role%3Abase)

## Instances

An **instance** is a deployed platform assembled on the base. The prefix is the
code of the contract that funds it.

| Prefix | Project |
|---|---|
| `g122-` | GALP 122 / 25961-4 — AI-assisted exploratory geological risk assessment |

Listing:
[`props.role:instance`](https://github.com/orgs/PUC-Behring-AI/repositories?q=props.role%3Ainstance)

## Everything else

The remaining repositories are independent research projects, predating the base
or outside it. They carry neither the `layer` nor the `role` property.
```

- [ ] **Passo 4: Commitar e verificar**

```bash
git add profile/README.md
git commit -m "docs: add organisation profile with the base platform index"
git push
```

Abra `https://github.com/PUC-Behring-AI` e confirme que o texto aparece na
página. Se não aparecer, o caminho está errado: tem de ser exatamente
`profile/README.md`, não `README.md`.

---

## Fase B — `base-platform`, a fonte

### Tarefa 3: Criar `base-platform` com o índice

**Arquivos:**
- Criar: `base-platform/README.md`

- [ ] **Passo 1: Criar o repositório, privado**

```bash
gh repo create PUC-Behring-AI/base-platform --private \
  --description "Inter-layer contracts, shared gate and release train for the base"
git clone git@github.com:PUC-Behring-AI/base-platform.git ~/Documents/Github/base-platform
cd ~/Documents/Github/base-platform
```

- [ ] **Passo 2: Escrever `README.md`**

A **primeira tabela do arquivo é o mapa de prefixos**, e isso não é preferência
de layout: a spec escolheu um código de contrato opaco (`g122`) e pagou essa
opacidade com esta tabela. Movê-la para baixo devolve o problema.

```markdown
# base-platform

What binds the five layers together: the contracts, the gate and the release
train.

This repository holds **no product logic**. If it acquires any, that logic has
become a layer and must move out.

## Prefixes — read this first

| Prefix | What it is |
|---|---|
| `base-` | The reusable base. Engines that serve more than one instance. |
| `g122-` | Instance **GALP 122 / 25961-4** — AI-assisted exploratory geological risk assessment platform, built on the GRA methodology. Private: it carries the client's methodology and sensitivity taxonomy. |

## The eleven repositories

| Repository | Layer | Team | Role |
|---|---|---|---|
| `base-platform` | `platform` | — | Contracts, gate, release |
| `base-knowledge` | `knowledge` | Team 1 | Data and knowledge engine |
| `base-inference` | `inference` | Team 2 | Inference engine |
| `base-agents` | `agents` | Team 3 | Agent engine |
| `base-interface` | `interface` | Team 4 | Interface engine |
| `g122-platform` | `platform` | — | Instance schemas |
| `g122-knowledge` | `knowledge` | Team 1 | Ontology, connectors, taxonomy |
| `g122-inference` | `inference` | Team 2 | Served models and key policy |
| `g122-agents` | `agents` | Team 3 | GRA flows, LoK and PoS computation |
| `g122-interface` | `interface` | Team 4 | Forms and visualisations |
| `.github` | — | — | Organisation profile (the only public one) |

## Where to start

| You want to | Read |
|---|---|
| Understand the whole architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Know what your layer owes its neighbour | [`docs/CONTRACTS.md`](docs/CONTRACTS.md) |
| Create a new instance | [`docs/ADAPTATION.md`](docs/ADAPTATION.md) |
| Work as an agent in any of these repos | [`docs/AGENTS-base.md`](docs/AGENTS-base.md) |
| Know why any of this exists | [`specs/`](specs/) — in Portuguese, the decision record |

## State

Documentation only. Executable contracts, fakes and the shared gate do not exist
yet — they are stages E1 and E2 of the spec.
```

- [ ] **Passo 3: Commitar**

```bash
git add README.md
git commit -m "docs: add base-platform index with the prefix map"
git push
```

---

### Tarefa 4: `docs/ARCHITECTURE.md`

**Arquivos:**
- Criar: `base-platform/docs/ARCHITECTURE.md`

- [ ] **Passo 1: Escrever o arquivo**

Este documento é a §3 da spec transposta para quem vai trabalhar, não para quem
vai aprovar. Onde divergir da spec, a spec vence.

```markdown
# The five-layer architecture

## Vocabulary

Three words with fixed meaning. Confusing them produces a design error — it
already did once.

- **base** — the set of reusable engines.
- **instance** — one deployed platform, with its own prefix.
- **domain** — the field of application. It names no repository.

## The layers

| Layer | Owns | Does **not** own |
|---|---|---|
| `knowledge` | Ingestion, relational, vector, RDF graph, object store, assignment of the sensitivity classification at the source, observability backends | No notion of business flow. Never calls a model. |
| `inference` | Ray Serve, vLLM, KubeRay, LiteLLM, virtual keys, budgets, elasticity, enforcement of the routing policy | Knows nothing about the domain. Never reads the knowledge base. |
| `agents` | Flows, orchestration, MCP, guardrails, the routing decision, audit trail, explainability | Persists no knowledge. Manages no GPU. Renders nothing. |
| `interface` | Session, layout, forms, visualisation, audit view | Does not talk to `knowledge` or `inference`. Exactly one arrow leaves here. |
| `platform` | Contracts, gate, cross-layer tests, release train | Not one line of product logic. |

The `interface` restriction is what makes leak auditing tractable. With one
arrow, "where could confidential data get out?" has a finite answer.

## Base and instance

    BASE (reusable)                    INSTANCE G122 (private)
    ┌─────────────────────────────┐    ┌──────────────────────────────────┐
    │ base-platform   contracts   │◄───│ g122-platform   schemas          │
    │ base-knowledge  engines     │◄───│ g122-knowledge  ontology         │
    │ base-inference  Ray/vLLM    │◄───│ g122-inference  models           │
    │ base-agents     runtime     │◄───│ g122-agents     flows, LoK, PoS  │
    │ base-interface  shell       │◄───│ g122-interface  forms            │
    └─────────────────────────────┘    └──────────────────────────────────┘
       serves every instance                serves only this one

**The boundary is reuse, not code versus configuration.** An instance repository
carries domain *code*, not only declarations: G122 requires LoK and PoS
computation, questionnaire validation and methodology rules. That is software.

One question separates the columns: *does it serve more than one instance?* If
it does, it is an engine. If it does not, it belongs to the instance — whether
it is an ontology file or two thousand lines of Python.

**Binding rule:** an engine gains an extension point only when two instances ask
for the same thing, or when the first asks for something confidential that
therefore cannot live in the engine. Until then, the instance writes code in its
own repository.

## The routing rule: decided in one place, enforced in another

`agents` decides; `inference` enforces. Both, not one.

    Person (VPN) ──► interface ──C3──► agents ──C2──► inference ──► GPT/Claude
                                          │                ▲        (only with an
                                          C1               │        external key)
                                          ▼                │
                                      knowledge ───────────┘
                              (classification originates here)

The gateway issues two families of virtual key: `local-only`, which reaches only
locally served models, and `external`, which reaches GPT/Claude/Gemini. The
agent layer picks the key from the highest classification present in the
context. The inference layer **does not trust that choice** — it serves what the
key permits.

Without the second half, the guarantee rests on an `if` being correct in code
that four teams edit. With it, it rests on a gateway policy, testable on its own.

## Release

A single versioned train: `base-platform` declares the version of each layer, and
a merge there is the release. Cadence is **weekly**. The train departs on the
scheduled day with whatever is ready; whoever missed it takes the next one.
**The train never waits.**

## Source

`specs/2026-09-10-arquitetura-base-cinco-camadas-design.md` (Portuguese). Where
this document diverges from it, the spec wins.
```

- [ ] **Passo 2: Commitar**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: add the five-layer architecture reference"
git push
```

---

### Tarefa 5: `docs/CONTRACTS.md`

**Arquivos:**
- Criar: `base-platform/docs/CONTRACTS.md`

- [ ] **Passo 1: Escrever o arquivo**

```markdown
# The inter-layer contracts

Four contracts. All of them live **here**, not in the layer that implements them.

## Why here

A contract that lives in the layer implementing it has a single owner, and that
owner can change it alone. The consumer finds out at the rebase. Living here,
changing a contract is a pull request in this repository, and `CODEOWNERS`
requires approval from **both** affected teams.

## The four

| | From → To | Invariant |
|---|---|---|
| **C1** | `knowledge` → `agents` | Every response carries `classification` and `provenance`. **There is no read path without a classification.** |
| **C2** | `agents` → `inference` | OpenAI-compatible. The key is a function of the highest classification in the context. |
| **C3** | `interface` → `agents` | The only arrow leaving the interface. |
| **C4** | all → `knowledge` | Telemetry: traces and metrics. One direction, no response. |

### C1 — evidence retrieval

The consumer (`agents`) needs to know, for every retrieved passage, **where it
came from** and **how sensitive it is**. Both travel with the content, in the
same response, always — not as an optional field and not in a separate call.

An optional field here is equivalent to an absent one: a consumer that forgets to
read it produces an unclassified path, and nothing fails.

### C2 — inference

OpenAI-compatible protocol, so that any client built on the OpenAI SDK works
unchanged.

What this contract adds to the protocol: **the credential is not free**. The
caller chooses between `local-only` and `external` based on the highest
classification present in the context. The inference layer does not validate that
choice — it serves what the key permits, and that is what makes the rule enforced
rather than agreed.

### C3 — the product API

The interface talks to `agents` and to nothing else. There is no "just for this
screen", "just for autocomplete", "just in development" exception. The exception
destroys the property the contract exists to provide.

### C4 — telemetry

Traces and metrics flow to the backends hosted in `knowledge`. One direction: no
layer reads another's telemetry at runtime.

## How to change a contract

1. Open a pull request **in this repository**, changing `docs/CONTRACTS.md` and,
   once it exists, the corresponding schema.
2. `CODEOWNERS` requires approval from the two teams the contract binds.
3. The merge here is what authorises the layers to change.

Changing the implementation before the contract inverts the order and turns the
contract into documentation of what already happened.

## State

**Prose and tables only.** Versioned schemas and executable fakes are stage E1 of
the spec and do not exist yet. Until they do, this file is the only source, and
it is normative.
```

- [ ] **Passo 2: Commitar**

```bash
git add docs/CONTRACTS.md
git commit -m "docs: add the four inter-layer contracts"
git push
```

---

### Tarefa 6: `docs/ADAPTATION.md`

**Arquivos:**
- Criar: `base-platform/docs/ADAPTATION.md`

- [ ] **Passo 1: Escrever o arquivo**

```markdown
# How an instance is born

An instance is a platform deployed on top of the base. This document is what
someone follows to create the second one.

## 1. Pick the prefix

The code of the contract funding the project, lowercase, no spaces. `g122` comes
from GALP 122.

Do not use the methodology name (it mixes what is the client's with what is ours)
nor the client name (it collides if they commission two platforms).

**Add the line to the prefix map in this repository's `README.md`, in the first
table.** Without it, the prefix is a riddle to whoever arrives later.

## 2. Create the five repositories

`<prefix>-platform`, `-knowledge`, `-inference`, `-agents`, `-interface`.
Private, unless explicitly decided otherwise.

Apply the organisation properties to each one:

    gh api --method PATCH repos/PUC-Behring-AI/<repo>/properties/values --input - <<JSON
    {"properties":[{"property_name":"layer","value":"<layer>"},{"property_name":"role","value":"instance"}]}
    JSON

## 3. Fill in the extension points

This is the **declarative** half of adaptation. The other half is domain code,
and section 4 covers it.

| Layer | The instance declares |
|---|---|
| `knowledge` | `ontology/` (RDF/OWL), `connectors/` (sources), `taxonomy.yaml` |
| `inference` | `models.yaml` (served models and key policy per class) |
| `agents` | `flows/`, `prompts/`, `tools/` (MCP declarations) |
| `interface` | `forms/`, `views/` |
| `platform` | `schemas/` (C1–C4 payloads), `versions.yaml` |

**`taxonomy.yaml` is the most important file on that list.** It is where the
routing rule becomes a parameter: each sensitivity class declares the key policy
that applies to it.

    classes:
      - name: public
        key-policy: external
      - name: client-confidential
        key-policy: local-only

The inference engine enforces the policy. The instance decides which classes
exist and what each one permits — it does not decide *whether* the policy is
enforced.

## 4. Write the code that is only yours

Computation, validation, methodology rules. This lives in the instance repository
and should not be squeezed into YAML.

**When you need something the engine cannot express**, the rule is: open an
extension point in the engine only when **two** instances ask for the same thing,
or when what you need is confidential and therefore cannot live in the engine.
Until then, write it in your own repository.

An engine generalised from a single case stiffens what was hard and abstracts
what was easy.

## 5. Board the train

`base-platform` declares the version of each layer. The instance boards the weekly
cadence like any other.
```

- [ ] **Passo 2: Commitar**

```bash
git add docs/ADAPTATION.md
git commit -m "docs: add the instance adaptation process"
git push
```

---

### Tarefa 7: `docs/AGENTS-base.md` — a parte comum, extraída

**Arquivos:**
- Criar: `base-platform/docs/AGENTS-base.md`
- Ler (não modificar ainda): `idia-server/AGENTS.md`

O `AGENTS.md` atual tem ~700 linhas. Dez cópias divergem na primeira semana — é
o mesmo defeito do `serve_config.yaml` duplicado, multiplicado por dez. Ele nasce
partido: a parte comum aqui, o adendo em cada repositório.

- [ ] **Passo 1: Ler o original e separar**

```bash
grep -n '^## ' ~/Documents/Github/idia-server/AGENTS.md
```

Vão para `AGENTS-base.md` (valem em qualquer repositório da base):

- `Document Evolution Contract`
- `Anti-Drift Rule (AXIOM)`
- `Governance & Maintainability Axioms` (as quatro)
- `Code Quality Axioms` (as seis)
- `Container Image Policy`
- `Env Var Convention`
- `Testing Strategy` — só as categorias e a política de skipping
- `O portão local`
- `Git Conventions`

Ficam no repositório de origem (são específicos da inferência):

- `Project`, `Architecture (3-Tier)`, `Directory Layout`, `Histórico de fases`
- `Security Constraints` (derivam do `ARCHITECTURE.md` daquele repo)
- `Model Configuration`
- `Testing Strategy` — a parte que descreve cada arquivo de teste
- `Stack-Specific Rules`

- [ ] **Passo 2: Escrever o cabeçalho de `AGENTS-base.md`**

```markdown
# AGENTS-base.md — rules common to every base repository

Version: 1.0 · 2026-09-10

This file is the shared half of each repository's `AGENTS.md`. Every repo has its
own `AGENTS.md` that **points here** and adds what is specific to it.

**The repository addendum wins** on conflict: whoever wrote it knows that
repository.

This file is versioned. A repository declares which version it follows, on the
first line of its own `AGENTS.md`. That is what makes it possible to tell who is
behind — the one thing ten loose copies never allow.

---
```

- [ ] **Passo 3: Copiar as seções, e traduzir apenas o que estiver em PT-BR**

Copie cada uma das nove seções do Passo 1, em ordem. As que já estão em inglês
vão literalmente. As que estão em PT-BR (`O portão local`, partes de
`Testing Strategy`) são traduzidas — **traduzidas, não reescritas**. São axiomas
já calibrados; reescrever de passagem é como um deles se perde.

Ajuste referências a caminhos específicos do `idia-server`
(`scripts/render_config.py`, `serve_config.yaml`) para formulação genérica, e
registre ao final de cada seção que houve generalização.

- [ ] **Passo 4: Verificar que nada se perdeu**

```bash
grep -c '^### ' ~/Documents/Github/base-platform/docs/AGENTS-base.md
```

Esperado: pelo menos 11 (4 axiomas de governança + 6 de qualidade + 1 de
evolução de documento). Se vier menos, uma seção ficou para trás.

- [ ] **Passo 5: Commitar**

```bash
git add docs/AGENTS-base.md
git commit -m "docs: extract the shared half of AGENTS.md into a versioned base"
git push
```

---

### Tarefa 8: `CODEOWNERS`, `.claude/`, e a spec

**Arquivos:**
- Criar: `base-platform/CODEOWNERS`
- Criar: `base-platform/.claude/issue-vizinhas`
- Copiar: a spec, para `base-platform/specs/`

- [ ] **Passo 1: Escrever `CODEOWNERS`**

Os times ainda não existem no GitHub. Este arquivo cria a estrutura e deixa os
donos comentados — um `CODEOWNERS` apontando para times inexistentes bloqueia
todo PR sem dizer por quê.

```
# CODEOWNERS — who must approve what.
#
# Each team holds a VETO over its own layer's contract. This is what stops one
# layer from changing what its neighbour consumes without the neighbour knowing.
#
# The teams below DO NOT EXIST on GitHub yet. Uncomment each line once the
# matching team is created (`gh api orgs/PUC-Behring-AI/teams`). A rule pointing
# at a non-existent team blocks the pull request without explaining why.

# Everything, by default, needs someone.
# *                        @PUC-Behring-AI/platform

# The contracts: both sides approve.
# /docs/CONTRACTS.md       @PUC-Behring-AI/knowledge @PUC-Behring-AI/inference @PUC-Behring-AI/agents @PUC-Behring-AI/interface

# Architecture and adaptation process: a change here changes all ten repos.
# /docs/ARCHITECTURE.md    @PUC-Behring-AI/platform
# /docs/ADAPTATION.md      @PUC-Behring-AI/platform
# /docs/AGENTS-base.md     @PUC-Behring-AI/platform
```

- [ ] **Passo 2: Criar o opt-in do guard de issues**

```bash
mkdir -p .claude
printf '### Vizinhas\n' > .claude/issue-vizinhas
```

O conteúdo é o cabeçalho literal que o `git-guard` procura no corpo da issue. Ele
fica em PT-BR porque é o valor que o hook compara, não prosa — mudá-lo
desarmaria o guard.

- [ ] **Passo 3: Copiar a spec**

```bash
mkdir -p specs
cp ~/Documents/Github/idia-server/.claude/worktrees/spec-arquitetura-base/specs/2026-09-10-arquitetura-base-cinco-camadas-design.md specs/
```

A spec passa a morar aqui porque governa dez repositórios, não um. A cópia em
`base-inference` sai na Tarefa 11.

- [ ] **Passo 4: Commitar**

```bash
git add CODEOWNERS .claude/issue-vizinhas specs/
git commit -m "docs: add CODEOWNERS skeleton, issue guard opt-in and the governing spec"
git push
```

- [ ] **Passo 5: Aplicar as propriedades**

```bash
gh api --method PATCH repos/PUC-Behring-AI/base-platform/properties/values --input - <<'JSON'
{"properties":[{"property_name":"layer","value":"platform"},{"property_name":"role","value":"base"}]}
JSON
gh api repos/PUC-Behring-AI/base-platform/properties/values --jq '.[] | "\(.property_name)=\(.value)"'
```

Esperado: `layer=platform` e `role=base`.

---

## Fase C — o rename e o fechamento

### Tarefa 9: Renomear `idia-server` para `base-inference`

**Antes de começar:** trabalhe no checkout principal
(`~/Documents/Github/idia-server`), não numa worktree. Confirme que ele está
limpo e em `main`.

- [ ] **Passo 1: Reconfirmar que não há fork nem estrela**

```bash
gh api repos/PUC-Behring-AI/idia-server --jq '{forks:.forks_count,stars:.stargazers_count,watchers:.subscribers_count}'
```

Esperado: tudo zero — foi o que se mediu em 2026-09-10. **Se algum for maior que
zero, pare.** Tornar privado um repositório com fork apaga os forks, e isso
destrói trabalho de outra pessoa.

- [ ] **Passo 2: Renomear**

```bash
gh repo rename base-inference --repo PUC-Behring-AI/idia-server
```

O GitHub cria redirecionamento do nome antigo. O diretório local **não** é
renomeado; corrija o remote:

```bash
cd ~/Documents/Github/idia-server
git remote set-url origin git@github.com:PUC-Behring-AI/base-inference.git
git remote -v
```

- [ ] **Passo 3: Aplicar as propriedades**

```bash
gh api --method PATCH repos/PUC-Behring-AI/base-inference/properties/values --input - <<'JSON'
{"properties":[{"property_name":"layer","value":"inference"},{"property_name":"role","value":"base"}]}
JSON
```

---

### Tarefa 10: Fechar o repositório **e** reescrever `.claude/noturno` — no mesmo commit

**Arquivos:**
- Modificar: `.claude/noturno` (permanece em PT-BR — ver a regra de idioma)

Esta tarefa junta duas coisas de propósito. O `.claude/noturno` justifica todas
as suas restrições com *"E ELE É PÚBLICO. Verificado em 09/09/2026"*. Fechar o
repositório sem tocar nesse arquivo deixa uma afirmação falsa, datada e confiante
— **dentro do texto anexado ao prompt de uma sessão autônoma**. É assim que
alguém afrouxa a regra certa pelo motivo errado, seis meses depois.

Estado medido em 2026-09-10: o agente está carregado, mas o plist fixa
`NOTURNO_REPO=anaxsouza/zapper`, e o log confirma a cada execução. Este repo está
inscrito e fora de serviço. O problema é latente, não ativo.

- [ ] **Passo 1: Reescrever a justificativa**

Substitua o bloco que começa em `# E ELE É PÚBLICO.` por:

```
# ELE ERA PÚBLICO ATÉ 10/09/2026, e hoje é privado. A primeira versão deste
# arquivo derivou todo o seu escopo da visibilidade pública, e essa premissa
# caiu. O que NÃO caiu, e é maior:
#
# - Este repositório deixou de ser um e virou um de DEZ, todos na mesma
#   organização e no mesmo disco. Um deles (g122-knowledge) carrega metodologia
#   e taxonomia de sensibilidade de um cliente, sob contrato.
# - Por isso a regra de contaminação cruzada abaixo NÃO afrouxa com o fechamento
#   do repo. Ela endurece: agora há nove vizinhos, não zero.
# - As restrições de escopo (`so-labels`, os caminhos proibidos) permanecem
#   enquanto ninguém as remedir contra a condição nova. Mantê-las apertadas sem
#   motivo verificado é aceitável; afrouxá-las sem motivo verificado não é.
```

- [ ] **Passo 2: Endurecer a regra de contaminação cruzada**

Localize o item que começa com `# - Só o trabalho DESTE repositório pertence a
ele.` e acrescente, logo abaixo:

```
#   Isto vale com força redobrada agora que existem nove repositórios irmãos.
#   Nada de g122-* entra aqui em nenhuma forma: nem código, nem nome de arquivo,
#   nem trecho de corpo de PR, nem exemplo em comentário. A base é agnóstica por
#   contrato, e um vazamento de instância para motor não é bug de estilo.
```

- [ ] **Passo 3: Fechar o repositório**

```bash
gh api --method PATCH repos/PUC-Behring-AI/base-inference -F private=true
gh api repos/PUC-Behring-AI/base-inference --jq .visibility
```

Esperado: `private`.

- [ ] **Passo 4: Commitar as duas coisas juntas**

```bash
git add .claude/noturno
git commit -m "chore(noturno): the repo went private, so restate why the scope is narrow

The file justified every restriction with 'this repo is PUBLIC', verified on
09/09. That premise died today. The bigger reason did not: this repo is now one
of ten, one of which carries a client's confidential methodology. The
cross-contamination rule hardens rather than relaxes."
git push
```

- [ ] **Passo 5: Verificar que a noite ainda não aponta para cá**

```bash
grep -A1 NOTURNO_REPO ~/Library/LaunchAgents/dev.anaxsouza.noturno.plist
```

Esperado: `anaxsouza/zapper`. Se tiver mudado, releia o arquivo reescrito antes
da próxima madrugada.

---

### Tarefa 11: Consertar as 28 referências ao nome antigo

**Arquivos:**
- Modificar: `docs/DEPLOY.md` (17), `scripts/install_service.sh` (2),
  `idia` (2), `docs/ADR.md` (2), `AGENTS.md` (2),
  `scripts/uninstall_service.sh` (1), `pyproject.toml` (1),
  `.claude/settings.local.json` (1)
- Remover: `specs/2026-09-10-arquitetura-base-cinco-camadas-design.md` (foi para
  `base-platform` na Tarefa 8)

- [ ] **Passo 1: Confirmar a contagem antes**

```bash
grep -rIn 'idia-server' --exclude-dir=.git . | wc -l
```

Esperado: 28. Se divergir, o repositório mudou desde 2026-09-10 — releia antes
de substituir.

- [ ] **Passo 2: Tratar o nome da unit do systemd separadamente**

`install_service.sh` e `uninstall_service.sh` usam `idia-server` como **nome da
unit do systemd**. Uma máquina já provisionada tem `idia-server.service` rodando
e não ganha o nome novo sozinha — fica com um serviço órfão subindo a stack
antiga.

Não faça `sed` aqui. Em `scripts/install_service.sh`, antes de instalar a unit
nova, acrescente:

```bash
# Name migration: until 2026-09-10 the unit was called idia-server.service.
# A host provisioned before that would end up with both, and the old one would
# bring up the previous stack underneath the new one.
if systemctl list-unit-files 2>/dev/null | grep -q '^idia-server\.service'; then
    echo "found the old idia-server.service unit — disabling it"
    sudo systemctl disable --now idia-server.service || true
    sudo rm -f /etc/systemd/system/idia-server.service
    sudo systemctl daemon-reload
fi
```

- [ ] **Passo 3: Substituir o resto**

```bash
grep -rIl 'idia-server' --exclude-dir=.git . \
  | grep -v -e 'install_service.sh' -e 'uninstall_service.sh' \
  | xargs sed -i '' 's|idia-server|base-inference|g'
```

- [ ] **Passo 4: Renomear a unit nos dois scripts, à mão**

Em `install_service.sh` e `uninstall_service.sh`, troque o nome da unit de
`idia-server.service` para `base-inference.service` — **exceto** dentro do bloco
de migração do Passo 2, que precisa continuar citando o nome antigo.

- [ ] **Passo 5: Apontar o `AGENTS.md` para a base**

Substitua as três primeiras linhas de `AGENTS.md` por:

```markdown
# AGENTS.md — base-inference
# Follows AGENTS-base.md v1.0, at PUC-Behring-AI/base-platform/docs/AGENTS-base.md.
# That file carries the axioms shared by all ten repositories; this one carries
# what belongs to this layer alone. On conflict, this file wins.
```

E remova daqui as nove seções que foram para a base na Tarefa 7.

- [ ] **Passo 6: Remover a spec, que agora mora em base-platform**

```bash
git rm specs/2026-09-10-arquitetura-base-cinco-camadas-design.md
```

- [ ] **Passo 7: Rodar o portão**

```bash
./scripts/gate.sh
```

Esperado: `Portão passou.` O `tests/test_docs.py` valida estrutura de
documentação e pode reprovar se uma seção esperada saiu do `AGENTS.md` — se
reprovar, ajuste o teste no mesmo commit, e diga no corpo do commit qual asserção
mudou e por quê.

- [ ] **Passo 8: Commitar**

```bash
git add -A
git commit -m "refactor: rename idia-server to base-inference across the repo

Includes a systemd unit migration step: a host provisioned before today has
idia-server.service installed, and it would keep running the old stack next to
the new unit."
git push
```

---

## Fase D — os oito repositórios restantes

### Procedimento de criação — vale para as Tarefas 12 a 19

Cada tarefa desta fase executa estes seis passos. Eles estão aqui uma vez para
que uma correção não precise ser feita oito vezes; cada tarefa traz **todos** os
valores que substitui, e nenhuma tarefa depende de você ter lido outra.

Substitua `<REPO>`, `<DESCRIPTION>`, `<LAYER>` e `<ROLE>` pelos valores da tarefa.

```bash
# 1. create and clone
gh repo create PUC-Behring-AI/<REPO> --private --description "<DESCRIPTION>"
git clone git@github.com:PUC-Behring-AI/<REPO>.git ~/Documents/Github/<REPO>
cd ~/Documents/Github/<REPO>

# 2. README.md   — use the "README template" below with this task's values
# 3. AGENTS.md   — use the "AGENTS.md template" below

# 4. issue guard opt-in
mkdir -p .claude && printf '### Vizinhas\n' > .claude/issue-vizinhas

# 5. organisation properties
gh api --method PATCH repos/PUC-Behring-AI/<REPO>/properties/values --input - <<JSON
{"properties":[{"property_name":"layer","value":"<LAYER>"},{"property_name":"role","value":"<ROLE>"}]}
JSON

# 6. commit
git add -A
git commit -m "docs: bootstrap <REPO> with its boundary and contracts"
git push
```

Ao final de cada tarefa, confirme que nada além de documentação entrou:

```bash
gh api repos/PUC-Behring-AI/<REPO>/languages --jq 'length'
```

Esperado: `0`.

### README template

```markdown
# <REPO>

<ONE LINE: what it is>

**Layer:** `<LAYER>` · **Role:** <base | instance> · **Team:** <N>

## What this repository owns

<LIST>

## What it explicitly does NOT own

<LIST — this section is not decoration: it is what stops the layer from growing
into its neighbour>

## Contracts

| | Direction | What |
|---|---|---|
<ROWS>

Normative definition:
[`base-platform/docs/CONTRACTS.md`](https://github.com/PUC-Behring-AI/base-platform/blob/main/docs/CONTRACTS.md)

## State

Documentation only. Not one line of code.

## Further reading

- Full architecture: `base-platform/docs/ARCHITECTURE.md`
- Agent rules: this repo's `AGENTS.md` plus `base-platform/docs/AGENTS-base.md`
```

### AGENTS.md template

```markdown
# AGENTS.md — <REPO>
# Follows AGENTS-base.md v1.0, at PUC-Behring-AI/base-platform/docs/AGENTS-base.md.
# That file carries the axioms shared by all ten repositories; this one carries
# what belongs to this layer alone. On conflict, this file wins.

## Project

**Name:** <REPO>
**Layer:** `<LAYER>`
**State:** documentation only — no code.

## What must not enter this repository

<THE "does NOT own" LIST FROM THE README, phrased as an enforceable restriction>

## Contracts this repository must honour

<LIST>

Changing a contract is a pull request in `base-platform`, never here.
```

---

### Tarefa 12: `base-knowledge`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `base-knowledge` · `<LAYER>` = `knowledge` · `<ROLE>` = `base`
- `<DESCRIPTION>` = *Data and knowledge engine: relational, vector, RDF graph, object store*
- One line: *Data and knowledge engine. It stores, indexes and classifies; it does not reason.*
- Team 1
- **Owns:** source ingestion; relational PostgreSQL; vector index
  (pgvector/Milvus); RDF graph (Apache Jena); object store; **assignment of the
  sensitivity classification at the source**; observability backends (Langfuse,
  Prometheus, Vault)
- **Does NOT own:** any notion of business flow; never calls a language model;
  does not decide routing — it only supplies the classification that makes the
  decision possible
- **Contracts:** C1, exposes, `knowledge → agents`, evidence retrieval with
  mandatory `classification` and `provenance` · C4, receives, `all → knowledge`,
  telemetry

---

### Tarefa 13: `base-agents`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `base-agents` · `<LAYER>` = `agents` · `<ROLE>` = `base`
- `<DESCRIPTION>` = *Agent orchestration engine: runtime, MCP, guardrails, audit trail*
- One line: *Agent engine. It decides what to do and with which model; it neither stores nor serves.*
- Team 3
- **Owns:** orchestration runtime; MCP wiring (servers and clients); input and
  output guardrails; **the routing decision, taken from the classification**;
  audit trail; explainability of generated suggestions
- **Does NOT own:** persists no knowledge (asks Team 1); manages no GPU or model
  (asks Team 2); renders nothing; **does not enforce** routing — enforcement
  belongs to inference, and trusting the decision made here would void the
  guarantee
- **Contracts:** C1, consumes · C2, consumes · C3, exposes · C4, emits

---

### Tarefa 14: `base-interface`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `base-interface` · `<LAYER>` = `interface` · `<ROLE>` = `base`
- `<DESCRIPTION>` = *Application shell: session, forms, visualisation, audit view*
- One line: *Interface engine. Exactly one arrow leaves here.*
- Team 4
- **Owns:** user session and authentication; layout and navigation;
  schema-driven form rendering; visualisation; audit view
- **Does NOT own:** **never talks to `knowledge` or `inference`, under any
  circumstance** — not "just for this screen", not "just in development". That
  restriction is what makes "where could confidential data get out?" a finite
  question; decides no routing; stores no domain data
- **Contracts:** C3, consumes · C4, emits

---

### Tarefa 15: `g122-platform`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `g122-platform` · `<LAYER>` = `platform` · `<ROLE>` = `instance`
- `<DESCRIPTION>` = *Schemas and versions for the GALP 122 instance*
- One line: *Payload schemas and the version list for the G122 instance.*
- No fixed owning team
- **Owns:** `schemas/` with the concrete C1–C4 payloads for this instance;
  `versions.yaml` pinning the version of each layer
- **Does NOT own:** does not redefine the contracts — their shape belongs to
  `base-platform`, and changing it is a pull request there; no product logic
- **Contracts:** implements the C1–C4 payloads

---

### Tarefa 16: `g122-knowledge`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `g122-knowledge` · `<LAYER>` = `knowledge` · `<ROLE>` = `instance`
- `<DESCRIPTION>` = *Ontology, connectors and sensitivity taxonomy for GALP 122*
- One line: *G122's knowledge: geological ontology, sources, and who may leave the network.*
- Team 1
- **Owns:** `ontology/` (RDF/OWL for the geological domain); `connectors/`
  (public dumps, licensed bibliography, GALP internal reports);
  **`taxonomy.yaml`** — the sensitivity classes and the key policy of each
- **Does NOT own:** no engine — PostgreSQL, index and graph come from
  `base-knowledge` by version
- **Notice at the top of the README:** *This repository carries a client's
  methodology and sensitivity taxonomy under contract with GALP. Nothing here is
  ever copied into a `base-*` repository.*

---

### Tarefa 17: `g122-inference`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `g122-inference` · `<LAYER>` = `inference` · `<ROLE>` = `instance`
- `<DESCRIPTION>` = *Served models and key policy for the GALP 122 instance*
- One line: *Which models G122 serves, and which key each data class receives.*
- Team 2
- **Owns:** `models.yaml` — locally served models and the map from sensitivity
  class to key policy (`local-only` / `external`)
- **Does NOT own:** no engine — Ray, vLLM and LiteLLM come from `base-inference`
  by version; does not decide routing, only declares what each class permits

---

### Tarefa 18: `g122-agents`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `g122-agents` · `<LAYER>` = `agents` · `<ROLE>` = `instance`
- `<DESCRIPTION>` = *GRA flows, LoK and PoS computation, prompts and tools*
- One line: *The product: the risk assessment flows and the computation behind them.*
- Team 3
- **Owns:** `flows/` (characterisation, assessment, justification records);
  **the LoK and PoS computation code**; questionnaire validation and GRA
  methodology rules; `prompts/`; `tools/` (MCP declarations)
- **Does NOT own:** no runtime — it comes from `base-agents` by version
- **Mandatory note in the README:** *This is the repository where "an instance is
  just configuration" is false and dangerous. LoK and PoS computation is
  software, with tests. Do not try to express it in YAML.*
- **Notice at the top of the README:** *This repository carries a client's
  methodology and sensitivity taxonomy under contract with GALP. Nothing here is
  ever copied into a `base-*` repository.*

---

### Tarefa 19: `g122-interface`

- [ ] Execute o **Procedimento de criação** com:

- `<REPO>` = `g122-interface` · `<LAYER>` = `interface` · `<ROLE>` = `instance`
- `<DESCRIPTION>` = *Forms and visualisations for the risk assessment*
- One line: *The GRA screens: questionnaires, LoK, PoS, justifications.*
- Team 4
- **Owns:** `forms/` (the GRA questionnaires as schema); `views/` (risk
  visualisation and audit trail view)
- **Does NOT own:** no shell — it comes from `base-interface` by version;
  **never talks to `g122-knowledge` or `g122-inference`**

---

## Fase E — verificação

### Tarefa 20: A listagem por propriedade devolve o que deve

- [ ] **Passo 1: Ler a propriedade de cada um dos dez**

Este passo usa o endpoint por repositório, o mesmo do Passo 5 do Procedimento —
se a escrita funcionou, a leitura funciona.

```bash
for r in base-platform base-knowledge base-inference base-agents base-interface \
         g122-platform g122-knowledge g122-inference g122-agents g122-interface; do
  printf '%-18s ' "$r"
  gh api "repos/PUC-Behring-AI/$r/properties/values" \
    --jq '[.[] | "\(.property_name)=\(.value)"] | join(" ")'
done
```

Esperado: dez linhas, cada uma com `layer=<algo>` e `role=<base|instance>`. Uma
linha vazia é um repositório que ficou sem propriedade e não vai aparecer em
filtro nenhum.

- [ ] **Passo 2: Conferir o filtro da interface web**

**Não verificado na escrita deste plano** — não havia repositório com propriedade
para testar contra. Abra:

```
https://github.com/orgs/PUC-Behring-AI/repositories?q=props.role%3Abase
```

Esperado: cinco repositórios. Se a sintaxe do filtro não for essa, corrija os
dois links em `.github/profile/README.md` (Tarefa 2) — eles apontam para esta
mesma consulta e ficariam quebrados na vitrine da organização.

- [ ] **Passo 3: Conferir a visibilidade**

```bash
gh repo list PUC-Behring-AI --limit 60 --json name,visibility \
  --jq '.[] | select(.name|test("^(base|g122)-")) | "\(.name) \(.visibility)"'
```

Esperado: dez linhas, todas `PRIVATE`.

- [ ] **Passo 4: Conferir que o perfil renderiza**

Abra `https://github.com/PUC-Behring-AI` num navegador. O texto da Tarefa 2 tem
de aparecer acima da lista de repositórios.

- [ ] **Passo 5: Conferir que nenhum repo novo tem código**

```bash
for r in base-platform base-knowledge base-agents base-interface \
         g122-platform g122-knowledge g122-inference g122-agents g122-interface; do
  n=$(gh api "repos/PUC-Behring-AI/$r/languages" --jq 'length')
  echo "$r languages=$n"
done
```

Esperado: `languages=0` em todos. Qualquer número maior significa que entrou
código nesta fase, contra o escopo declarado no topo deste plano.

- [ ] **Passo 6: Conferir que nenhum repo base cita a instância**

A base é agnóstica por contrato. Uma menção a `g122` num repositório `base-*` é
vazamento de instância para motor.

```bash
for r in base-platform base-knowledge base-agents base-interface; do
  echo "== $r"
  grep -rin 'g122\|GALP\|GRA\b' ~/Documents/Github/$r --exclude-dir=.git || echo "  limpo"
done
```

Esperado: `limpo` em `base-knowledge`, `base-agents` e `base-interface`.
`base-platform` **pode** citar — é onde mora o mapa de prefixos, e é o único.

---

## Dívida que este plano deixa aberta, deliberadamente

Vira issue em `base-platform` ao final, não fica na cabeça de ninguém.

1. **Os times do GitHub não existem**, e o `CODEOWNERS` está comentado. Enquanto
   isso, nenhum PR tem revisor obrigatório e o veto por camada é combinado, não
   imposto.
2. **Os contratos são prosa.** Sem schema versionado, "toda resposta carrega
   `classification`" é promessa, não invariante.
3. **O portão não foi extraído.** Nove repositórios não têm portão nenhum.
4. **`AGENTS-base.md` não tem mecanismo de versão.** Um repo pode declarar que
   segue a v1.0 e estar seguindo outra coisa; nada confere.
5. **O `.claude/noturno` de `base-inference` mantém restrições calibradas para
   uma condição que mudou.** A Tarefa 10 corrige a justificativa, não recalibra
   o escopo — isso exige medir de novo.
6. **`kif` e `quail` continuam sem verificação** como dependências de
   `base-knowledge` e `base-agents` (§5 da spec).
7. **A spec fica em PT-BR num conjunto de repositórios em inglês.** Decidido na
   regra de idioma no topo deste plano, e é a fronteira mais provável de alguém
   querer mudar depois.
