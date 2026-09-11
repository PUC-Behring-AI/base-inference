# AGENTS.md — base-inference
# Segue AGENTS-base.md v1.0, em PUC-Behring-AI/base-platform/docs/AGENTS-base.md.
# Aquele arquivo carrega os axiomas comuns aos dez repositórios; este carrega o
# que é só desta camada. Em conflito, este vence.
# Base: v0.2.0
# Version: 3.1
# Last updated: 2026-09-10

## Project

**Name:** base-inference — a camada de inferência da base
**Layer:** `inference` · **Role:** base · **Grupo:** 2
**Description:** Servidor de inferência LLM auto-hospedado, com autoscaling de
  réplicas (incluindo scale-to-zero), provisionamento de usuários com budget e
  rate-limit individuais, e interface web. Deploy local via Docker Compose.
**Stack:** Python 3.11+, Docker Compose v2, Ray Serve LLM (2.56.0),
  vLLM (0.22.0, bundled by ray[serve,llm]==2.56.0), LiteLLM (1.85.0), Prometheus, Grafana
**Testing:** pytest 8.x, PyYAML (config schema validation)
**Repository:** https://github.com/PUC-Behring-AI/base-inference

## Architecture (3-Tier)

| Tier | Component | Role | Port |
|------|-----------|------|------|
| Gateway | **LiteLLM** | Auth, virtual keys, budgets, rate-limits, spend tracking | `:4000` (única porta externa) |
| Orchestration | **Ray Serve LLM** | Replica autoscaling (scale-to-zero), GPU placement, multi-model routing, LoRA multiplexing | `:8000` (interna apenas) |
| Engine | **vLLM** | Inference: weights in VRAM, KV cache, token generation | in-process (sem porta) |

Fluxo: `Client → :4000 → LiteLLM → :8000 → Ray Serve → vLLM`

Referência arquitetural completa: `docs/ARCHITECTURE.md`

## Contratos desta camada

Segue a base **v0.2.0**. Definição normativa em
`base-platform/docs/CONTRACTS.md`; mudar um contrato é PR lá, nunca aqui.

| | Direção | O que |
|---|---|---|
| **C2** | expõe, `agents → inference` | Compatível com OpenAI. A chave é função da classificação máxima do contexto — e **esta camada não confia na escolha de quem chama**: serve o que a chave permite. |
| **C5** | expõe, `platform → inference` | Identidade: emitir, consultar e revogar credencial, com orçamento e limite de taxa. |
| **C6** | emite, `all → knowledge` | Proveniência: qual modelo foi endereçado, **sob qual política de chave**, com o identificador de requisição propagado sem alteração. |
| **C4** | emite, `all → platform` | Métrica. **Sem carga útil, nunca** — nem prompt, nem completion, nem identificador que resolva para uma pessoa. |

**Onde esta camada carrega a garantia.** C2 é o ponto de imposição da regra de
roteamento: a decisão é da camada de agentes, e aqui ela não é revalidada — é
substituída por uma política de chave. Um defeito lá em cima não vaza, porque a
credencial que chega não tem permissão de sair da rede.

Não acrescente um caminho que confie num campo da requisição para decidir se
pode chamar provedor externo. Isso devolve a garantia para um `if`.

## Directory Layout

Os marcadores de fase saíram: as fases terminaram, e "Phase 2 ✓" ao lado de um
arquivo dizia quando ele nasceu, não o que ele faz. O que segue é o papel de
cada artefato. `tests/test_docs.py::TestDirectoryTree` falha se um nome listado
aqui não existir em disco.

```
base-inference/
├── base-inference               ← CLI unificada: deploy, status, user, colleague, service
├── AGENTS.md                   ← este arquivo — regras do projeto para agentes
├── README.md                   ← porta de entrada; operação vive no docs/DEPLOY.md
├── .env.example                ← template de configuração, sem segredos
├── .gitignore
├── pyproject.toml              ← pytest, ruff
├── Dockerfile.ray              ← imagem Ray Serve LLM + vLLM
├── serve_config.yaml           ← template do Ray Serve; as entradas são geradas
├── docker-compose.yml          ← o fragmento desta camada: 5 serviços
├── observability/
│   ├── scrape.d/inference.yml  ← alvos que esta camada pede que sejam varridos
│   └── dashboards/vllm.json    ← dashboard do engine (ID 25043)
├── .claude/
│   ├── portao                  ← comando do gate local, lido pelo git-guard
│   └── issue-vizinhas          ← seção exigida no corpo de toda issue nova
├── scripts/
│   ├── render_config.py        ← fonte única dos configs do Ray e do LiteLLM
│   ├── colleague.sh            ← provisionamento de usuários, 6 passos
│   ├── gate.sh                 ← o portão: pytest, shellcheck, ruff, YAML
│   ├── smoke_test.sh           ← verificação pós-deploy, com --wait
│   ├── setup_environment.sh    ← prepara a máquina (Linux)
│   ├── install_service.sh      ← unit systemd
│   └── uninstall_service.sh
├── tests/
│   ├── conftest.py             ← fixtures compartilhadas
│   ├── test_docs.py            ← estrutura da documentação e da árvore
│   ├── test_config_schemas.py  ← schema dos configs e do gerado pelo LiteLLM
│   ├── test_integration.py     ← render, multi-model, orçamento de VRAM
│   ├── test_render_config_units.py ← unidade in-process: caminhos de erro e main()
│   ├── test_engine_config.py   ← dtype, quantização, residência, tool calling
│   ├── test_stack_services.py  ← topologia do Compose, portas, banco
│   ├── test_colleague.py       ← provisionamento, tiers, guardas de injeção
│   ├── test_security.py        ← portas, pinning, fronteiras de confiança
│   ├── test_contract.py        ← contratos REST do LiteLLM, sem GPU
│   ├── test_deploy_dry_run.py  ← dry-run, CLI, consistência do health check
│   └── bats/                   ← suíte de shell (bats)
│       ├── colleague_create.bats    ← provisionamento contra LiteLLM falso
│       ├── colleague_lifecycle.bats ← status, revoke, tiers
│       ├── base_inference_cli.bats  ← roteamento, deploy, status, user, logs
│       └── helpers/
│           ├── common.bash          ← setup: servidor falso, .env, stubs no PATH
│           ├── fake_litellm.py      ← LiteLLM de mentira, com estado real
│           └── bin/docker           ← `docker` de mentira, que grava o que foi pedido
└── docs/
    ├── ARCHITECTURE.md         ← documento vivo de arquitetura
    ├── DEPLOY.md               ← guia de operação
    └── ADR.md                  ← Architecture Decision Records
```

Saíram daqui: `prometheus.yml` e `grafana/` foram para `base-platform` com o
servidor que os lê (C4); `docs/audit_logs/` foi apagado — eram relatórios de
junho cujos achados já viraram issues e fecharam, e um documento que sobrevive
aos próprios achados virou decoração.

## Histórico de fases

Todas concluídas. A tabela existia como plano; o que resta dela é o registro
de como o projeto chegou aqui, e o detalhe vive no histórico estrutural do
`ARCHITECTURE.md` §16.7 e nos ADRs.

| Fase | Entregou |
|------|----------|
| 1–2 | Fundação e build core: Dockerfile, entrypoint, Compose, testes |
| 3 | Deploy AWS — **removido** depois; ver ADR-003 e ADR-004 (superseded) |
| 4 | Monitoramento: Prometheus, Grafana provisionado, DCGM |
| 5 | Documentação: ARCHITECTURE, DEPLOY, ADR |
| Post-5 | Automação: CLI unificada, render duplo |
| Post-6 | Simplificação local-only |
| Post-6b | Systemd, para subir no boot |
| Post-6c | Provisionamento de usuários, config de engine por modelo, PostgreSQL e Open WebUI no Compose, portão local |

O trabalho agora é dirigido por issues, não por fases. `gh issue list` é o
plano.

## Security Constraints (from ARCHITECTURE 

Derivadas da arquitetura. **Não negociáveis.**

| Regra | Fonte |
|-------|-------|
| **`:4000`** é a ÚNICA porta exposta ao host | §9.1 |
| **`:8000`** (Ray ingress) é interna — nunca mapeada em `docker-compose ports` | §9.3 |
| **`:8265`** (Ray dashboard) é interna — acesso via `docker compose exec` ou túnel SSH | §9.2 |
| **`:10001`** (Ray Client) é interna | §9.2 |
| Todas as imagens **pinnadas a tags imutáveis** — nunca `:latest` | §9.1 |
| **Duas fronteiras de confiança**: master key (admin) vs. virtual keys (clientes) | §9.1 |
| TLS termina na borda (reverse proxy local), nunca dentro dos containers | §9.1 |
| Ray cluster tratado como banco sem autorização — qualquer path de rede = root | §9.2 |
| Dashboard bound a `127.0.0.1`, nunca `0.0.0.0` | §9.2 |
| Ray ≥ 2.54.0 obrigatório (fecha CVE-2026-27482) | §9.2 |

## Model Configuration

O modelo é configurável via `.env` com duas variáveis:

| Variável | Exemplo | Obrigatória |
|----------|---------|-------------|
| `MODEL_ID` | `mistral-7b` | Sim |
| `MODEL_SOURCE` | `mistralai/Mistral-7B-Instruct-v0.3` | Sim |

A implementação do templating usa o entrypoint Python `scripts/render_config.py`, que substitui placeholders `${VAR}` por variáveis de ambiente antes de delegar ao Ray Serve.

---

## Testing Strategy

O base-inference usa **pytest 8.x** como executor. A suíte cobre cinco categorias de teste,
cada uma com seu marcador e requisitos de infraestrutura.

### Categorias de Teste

| Marcador | Categoria | O que valida | Requer infraestrutura? | Fase |
|----------|-----------|-------------|----------------------|------|
| `docs` | Documentação | Estrutura de arquivos obrigatórios, seções de documentos vivos, footer de versão | Não — roda com `pip install pytest` | 1 |
| `config` | Schema de configuração | Estrutura YAML de `serve_config.yaml`, `docker-compose.yml`, `.env.example` e `observability/scrape.d/inference.yml` | Não — apenas PyYAML | 1 |
| `integration` | Integração | `render_config.py`: substituição de env vars, validação YAML, dry-run, caminhos de erro; consistência do Compose (build source, pinning, env vars) | Componente unitário: apenas pytest; full suite: Docker + GPU | 2 |
| `security` | Segurança | Isolamento de portas (`:8000`, `:8265`, `:10001` inacessíveis externamente; apenas `:4000` externa; `:9090` não publicada; `:3000` bound a localhost), pin de imagens (`no :latest`), fronteiras de confiança (master_key declarado), binding do dashboard | Verificação de YAML: apenas pytest; verificação de rede: Docker | 2 |
| (none) | Contrato LiteLLM | Simulação de API LiteLLM: rejeição de modelo inexistente, auth ausente, mensagens inválidas, formato de resposta | Não — puro Python com mock | 5 (Tier 4) |
| `deploy` | Dry-run + CLI | Validação de render_config.py, esquema .env, CLI unificada | Não — puro Python + shell | Post-5 |
| (none) | Unidade in-process | `render_config.py` chamado como função, não como subprocesso: cada caminho de erro, cada ramo de validação e o `main()` nos três modos | Não — puro Python | Post-5 |

### Cobertura

O portão exige **95% de statement e de ramo** em `scripts/render_config.py`
(hoje em 100%). O piso mora em `scripts/gate.sh` como `--cov-fail-under=95`,
não no `pyproject.toml`: nessa tabela ele valeria para toda invocação com
`--cov`, e rodar um arquivo só devolveria "FAIL 0%" com os testes verdes.

Duas restrições da ferramenta que não são óbvias e custam uma execução
inteira quando esquecidas:

- **`--cov-branch` vem da linha de comando, nunca de `[tool.coverage.run]`.**
  Parte da suíte roda `render_config.py` como subprocesso, e o `pytest-cov`
  monta a configuração do filho a partir das próprias flags. Ligar `branch`
  só no `pyproject` faz um lado medir ramo e o outro linha, e o run termina
  em `INTERNALERROR: Can't combine statement coverage data with branch data`.
- **Um `.coverage.*` de execução interrompida quebra a próxima.** O gate
  apaga antes de rodar; à mão, `rm -f .coverage .coverage.*`.

A cobertura mede só o Python, que é **um terço** do código executável deste
repositório — `base-inference`, `colleague.sh` e `setup_environment.sh` somam mais
linhas que `render_config.py`. Um relatório de 100% não afirma nada sobre
eles. O shell tem suíte funcional própria (`tests/bats/`), e **não** tem
número de cobertura: medir linha de shell exige `kcov` ou `bashcov`, nenhum
instalado, e instalar ferramenta na máquina de alguém é decisão de quem opera.
Então o que existe sobre o shell é "88 testes exercitam estes caminhos", não
"N% das linhas foi executada" — e as duas frases não são a mesma.

### A suíte de shell (bats)

`bats tests/bats` — 88 testes, sem Docker, sem GPU, sem servidor no ar.

`tests/test_colleague.py` já cobre o que para antes da rede: `--help`,
`tiers`, `--dry-run` e as guardas de injeção. A suíte bats cobre a outra
metade — **as requisições que os scripts de fato enviam** — que é onde
nasceram os defeitos de produção: o servidor não emitia uma única virtual
key, e nenhum teste podia notar, porque nenhum teste pedia uma.

Como ela consegue rodar sem infraestrutura:

- **`helpers/fake_litellm.py` é um servidor HTTP de verdade**, não um `curl`
  stubado. Precisa ser: `colleague.sh` chega ao LiteLLM por dois caminhos —
  `curl` em `_litellm_api` e `urllib` no Python embutido de
  `_litellm_delete_keys_by_alias` — e stubar `curl` deixa o segundo sem
  teste. O segundo é o que morre primeiro quando o proxy está fora.
- **Ele guarda estado real.** Uma key criada por `/key/generate` aparece em
  `/key/list`, é descrita por `/key/info` e é removida por `/key/delete`.
  É isso que torna o passo "limpar as keys anteriores deste alias"
  verificável: com resposta canned, a contagem é a que o falso decidiu, não
  a que o script calculou.
- **`helpers/bin/docker` grava o que foi pedido** e responde os poucos
  subcomandos usados. As asserções são sobre a linha de comando que o script
  *montaria* — é ali que os defeitos moram (um serviço que falta, uma flag de
  profile que nunca é passada).
- **`./base-inference` roda a partir de uma cópia temporária do repositório.**
  `colleague.sh` tem a costura para isso (`BASE_INFERENCE_ENV_FILE`); `./base-inference` não —
  fixa `ENV_FILE="$REPO_DIR/.env"`. Os scripts são **copiados, não
  linkados**: `render_config.py` deriva a raiz de
  `Path(__file__).resolve().parent`, e `resolve()` segue o link de volta ao
  checkout real, que é onde o `--render-all` escreveria.

As asserções são sobre o **payload parseado** que chega ao `/key/generate`,
não sobre as palavras no terminal. Um tier cujos limites são impressos certo
e enviados nulos é exatamente a falha que isso pega: quem opera lê
"300 req/min", quem usa recebe ilimitado, e as duas telas concordam.

Dois testes são de **caracterização**, não endosso — fixam o comportamento
defeituoso que existe hoje, com a issue anotada no corpo, para que a correção
faça o teste virar. Estão rotulados como tal; um teste que finge aprovar um
defeito sem dizer que é um defeito é pior que a ausência dele.

### Como executar

```bash
# Instalar dependências de teste
pip install pytest pytest-cov ruff pyyaml

# O extra equivalente existe, mas `pip install -e '.[dev]'` é recusado em
# Python 3.13: `requires-python` do projeto trava em `<3.13` por causa do
# runtime (Ray/vLLM), enquanto a suíte roda limpa em 3.13.9. Os dois
# ambientes não são o mesmo e a metadata só descreve um.

# Rodar testes rápidos (docs + config) — zero infraestrutura
pytest -m "docs or config" -v

# Rodar todos os testes (inclui integração e segurança simulados)
pytest -v

# Rodar testes de um arquivo específico
pytest tests/test_config_schemas.py -v

# Rodar por marcador
pytest -m config -v

# Cobertura, do jeito que o portão roda (statement + ramo, piso de 95%)
rm -f .coverage .coverage.*
pytest --cov --cov-branch --cov-fail-under=95

# Ver quais linhas e ramos faltam
pytest --cov --cov-branch --cov-report=term-missing

# A suíte de shell (brew install bats-core)
bats tests/bats

# Um arquivo só, com a saída de cada teste que falhar
bats tests/bats/colleague_create.bats --verbose-run
```

### O que cada teste valida

#### `test_docs.py` (— docs)

| Teste | O que verifica |
|-------|---------------|
| `test_exists` | Cada arquivo obrigatório (`docs/ARCHITECTURE.md`, `AGENTS.md`, `README.md`) existe |
| `test_is_markdown` | Arquivos começam com `#` (cabeçalho markdown) |
| `test_contains_sections` | Documentos vivos contêm as seções de governança exigidas (Document Evolution Contract, Structural Change History) |
| `test_has_version_footer` | ARCHITECTURE.md tem footer de versão e tabela de histórico estrutural |
| `test_phase_markers_match_code` | README.md: marcadores de fase (Phase N ✓) correspondem a arquivos existentes no disco |
| `test_directory_listed_files_exist` | Todos os arquivos listados na árvore do README existem |
| `test_adr_exists` | ADR.md existe e não está vazio |
| `test_adr_has_entries` | ADR.md contém pelo menos 4 entradas ADR |
| `test_adr_required_sections` | Cada entrada ADR tem Contexto, Decisão, Alternativa descartada, Consequências |
| `test_adr_references_phase` | Cada entrada ADR referencia a Fase de origem |
| `test_adr_has_status` | Cada entrada ADR tem Status (Accepted/Superseded/Deprecated) |
| `test_license_exists` | LICENSE existe e não está vazio |
| `test_license_is_apache2` | LICENSE é Apache 2.0 |

#### `test_config_schemas.py` (— config)

Cada classe de teste valida a estrutura de um arquivo de configuração contra a especificação na arquitetura:

| Classe | Arquivo alvo | Key assertions |
|--------|-------------|---------------|
| `TestServeConfig` | `serve_config.yaml` | `proxy_location: EveryNode`, `http_options.port: 8000`, `applications` é lista não-vazia |
| `TestDockerCompose` | `docker-compose.yml` | Serviços `ray-head` e `litellm` presentes; `ipc: host` e `shm_size` em ray-head |
| `TestLiteLLMConfig` | saída de `render_litellm_config()` | `model_list` não-vazia, rota para `ray-head:8000`, master_key como referência de env |
| `TestScrapeTargets` | `observability/scrape.d/inference.yml` | é uma **lista** de jobs, não um mapa com `scrape_configs`; cobre `ray-head:8080`, `litellm:4000` e `dcgm-exporter:9400`; todo job rotulado `layer: inference`; sem bloco `global`, que pertence ao backend |
| `TestEnvExample` | `.env.example` | Declara `HF_TOKEN`, `LITELLM_MASTER_KEY`, `MODEL_ID`, `MODEL_SOURCE` |

#### `test_integration.py` (— integration)

| Classe/Teste | O que verifica |
|-------------|---------------|
| `TestRenderConfig.test_render_with_minimal_env` | `render()` substitui placeholders com env vars |
| `TestRenderConfig.test_render_injects_defaults` | Optional vars (GPU_MEMORY_UTILIZATION) usam default quando ausentes |
| `TestRenderConfig.test_render_validates_full_template` | Estrutura do YAML renderizado corresponde a `§5.3` (proxy_location, port, min/max_replicas) |
| `TestRenderConfig.test_dry_run_flag` | `--dry-run` produz YAML válido sem executar serve |
| `TestRenderConfigErrors.test_missing_required_var_fails` | Exit 1 com mensagem se MODEL_ID ausente |
| `TestRenderConfigErrors.test_bad_yaml_template_fails` | Exit 1 se template inválido após substituição |
| `TestRenderSchemaErrors.test_gpu_util_above_range_fails` | GPU_MEMORY_UTILIZATION=1.5 → exit |
| `TestRenderSchemaErrors.test_gpu_util_negative_fails` | GPU_MEMORY_UTILIZATION=-0.5 → exit |
| `TestRenderSchemaErrors.test_max_model_len_non_numeric_fails` | MAX_MODEL_LEN=abc → exit |
| `TestRenderSchemaErrors.test_model_id_with_yaml_special_chars_escaped` | MODEL_ID com `:{}` é escapado, não injetado |
| `TestComposeConsistency.test_ray_head_builds_locally` | ray-head usa build local (Dockerfile.ray) |
| `TestComposeConsistency.test_litellm_uses_pinned_image` | litellm usa tag semver, não :latest |
| `TestComposeConsistency.test_ray_head_passes_vars_to_entrypoint` | ray-head passa MODEL_ID, MODEL_SOURCE, MAX_MODEL_LEN, GPU_MEMORY_UTILIZATION |

#### `test_security.py` (— security)

| Classe/Teste | O que verifica |
|-------------|---------------|
| `TestPortIsolation.test_only_4000_published` | Apenas porta 4000 aparece em `ports:` no Compose |
| `TestPortIsolation.test_ray_ingress_not_published` | Porta 8000 NÃO está em `ports:` |
| `TestPortIsolation.test_dashboard_not_published` | Porta 8265 NÃO está em `ports:` |
| `TestPortIsolation.test_ray_client_not_published` | Porta 10001 NÃO está em `ports:` |
| `TestImagePinning.test_dockerfile_base_image_is_not_on_a_moving_tag` | Nenhum `FROM` do Dockerfile.ray usa tag móvel (`latest`, `main`, `master`, `dev`, `develop`, `edge`, `nightly`, ou tag omitida) |
| `TestImagePinning.test_compose_images_are_not_on_moving_tags` | Nenhum serviço no Compose usa tag móvel |
| `TestImagePinning.test_services_we_reach_into_are_pinned_by_digest` | Open WebUI pinado por `@sha256:` — nosso código depende do schema interno dele (ADR-009) |
| `TestTrustBoundaries.test_generated_config_never_embeds_the_master_key` | o config renderizado nunca contém o valor real da master key |
| `TestDashboardBinding.test_dashboard_host_set_to_localhost` | serve_config.yaml http_options.host=0.0.0.0 (proxy interno)
| `TestMonitoringPortIsolation.test_no_backend_port_is_published` | Nenhuma porta de backend de métrica (9090, 3000) publicada — **nem em loopback**, porque "só no localhost" foi como o Grafana anterior se justificou
| `TestMonitoringPortIsolation.test_no_backend_service_is_defined` | Nenhum `prometheus`, `grafana` ou `langfuse` definido aqui — backend alcançável só pela rede interna continua sendo backend

#### `test_render_config_units.py` (sem marcador)

Chama cada função de `render_config.py` direto, sem subprocesso. É o que
alcança os ramos que a CLI não consegue provocar — um `PermissionError`, um
template em latin-1, o `execlp` que volta em vez de substituir o processo — e
o que satisfaz o Axioma 7 de forma medida em vez de declarada.

Cada teste de falha cobra **as duas metades do diagnóstico**: o status de
saída e o nome da variável em `stderr`. Afirmar só o status passa igualmente
bem no dia em que a mensagem fica em branco, e é a mensagem que diz ao
operador o que mudar.

| Classe | O que verifica |
|-------------|---------------|
| `TestFindTemplate` | Busca em caller/pai/avô/`/app`; ausência lista os caminhos tentados |
| `TestReadFile` | Arquivo ausente, sem permissão e não-UTF-8, cada um com sua mensagem |
| `TestApplyDefaults` | Defaults de opcionais; obrigatórias permanecem ausentes; o schema declara as três certas |
| `TestEngineOption` | Numerada vence a sem número; valor só-espaço não é valor; `n=None` ignora a numerada |
| `TestEscapeYamlValue` | `:`, `{}`, `#` e `\n` são citados e sobrevivem ao round-trip |
| `TestValidate*` | Range e tipo de `GPU_MEMORY_UTILIZATION`, `MAX_MODEL_LEN`, `GPU_COUNT`, `GPU_VRAM_GB` |
| `TestResidentVramBudget` | Cinco modelos scale-to-zero cabem numa GPU; dois residentes não; a mensagem nomeia quais |
| `TestCollectEnv` | Modo único vs multi; todas as faltantes reportadas de uma vez |
| `TestBuildLlmConfigs` | Uma entrada por modelo; declarar N e definir menos é fatal |
| `TestSubstitute` | Marcador só na chave `llm_configs:`; exemplo estático descartado; seção top-level depois dele sobrevive |
| `TestValidateYaml` | YAML malformado, vazio, sem `applications`, sem `llm_configs`, entrada sem identificador — com o índice que falhou |
| `TestLogDiagnostics` | Resumo vai para `stderr`, nunca `stdout` (que carrega o YAML no `--dry-run`) |
| `TestRenderLitellmConfig` | master_key fica como `os.environ/`; nenhum `${...}` sobrevive; os três tiers com limites distintos |
| `TestWriteRenderedFiles` | Escreve os dois, sobrescreve render velho, diretório inválido é fatal |
| `TestMain*` | `--dry-run` não escreve arquivo; `--render-all` escreve os dois; modo normal grava e chama `execlp`; `execlp` que retorna sai != 0 |

### Política de Skipping

Testes que dependem de arquivos de fases futuras usam `pytest.skip()` com mensagem
explicativa — nunca falham pela ausência de algo que ainda será criado.
Isso permite que a suíte rode limpa desde a Fase 1.

### Adicionando Novos Testes

1. Criar arquivo `tests/test_<area>.py`.
 2. Usar o marcador apropriado: `@pytest.mark.docs`, `@pytest.mark.config`,
    `@pytest.mark.integration`, `@pytest.mark.security`.
3. Usar as fixtures compartilhadas de `conftest.py` (`repo_root`, `docs_dir`, `config_files`).
4. Se o teste depende de um arquivo de fase futura, usar `pytest.skip()` se o arquivo não existir.
5. Registrar o novo marcador em `pyproject.toml` se for nova categoria.
6. Atualizar esta seção no AGENTS.md.
7. Se o arquivo é mantido limpo, adicioná-lo à lista do `ruff` em
   `scripts/gate.sh` — fora dela o lint nunca o vê.
8. Código novo em `scripts/` nasce com teste: o portão recusa o PR abaixo de
   95% de statement e de ramo. Preferir chamada in-process a `subprocess` —
   é mais rápido, alcança os caminhos de erro, e um `subprocess` que recebe
   ambiente limpo (`env={"PATH": ...}`) não é medido, porque isso apaga a
   variável que instrumenta o filho.
9. **Comportamento de shell vai para `tests/bats/`, não para um
   `subprocess.run` em Python.** Se o caminho novo fala com o LiteLLM ou com
   o Docker, os helpers já existem: `start_litellm`, `write_env`,
   `make_fake_repo`, `stub_path`. Adicionar um endpoint ao
   `helpers/fake_litellm.py` é preferível a stubar `curl` — o script tem
   caminhos que usam `urllib`, e esses o stub de `curl` não vê.
10. **Um teste que fixa comportamento defeituoso diz que é defeituoso.** No
    corpo, o que está errado e a issue que rastreia. Sem isso ele é
    indistinguível de um teste que endossa o defeito, e a correção parece
    uma regressão.

---

## Stack-Specific Rules

- **Docker Compose v2** obrigatório (`docker compose`, não `docker-compose`).
- **Nunca** expor portas internas (8000, 8265, 10001) no `docker-compose.yml`.
- Toda imagem pinada por tag semver — `:latest` proibido.
- Secrets via `.env` + variáveis de ambiente, nunca hardcoded.
- Configs YAML seguem schemas validados por `tests/test_config_schemas.py`.

---

## O que saiu daqui para a base

Oito seções deste arquivo migraram para
`PUC-Behring-AI/base-platform/docs/AGENTS-base.md` em 10/09/2026. Elas valem em
qualquer repositório da base, e dez cópias delas divergiriam na primeira semana
— é o defeito do `serve_config.yaml` duplicado (ARCHITECTURE §5.3) multiplicado
por dez.

Se você veio procurar uma delas aqui, está lá:

| Seção | Onde está agora |
|---|---|
| Document Evolution Contract | `AGENTS-base.md` |
| Anti-Drift Rule | `AGENTS-base.md` |
| Governance & Maintainability Axioms (0–3) | `AGENTS-base.md` |
| Code Quality Axioms (4–9) | `AGENTS-base.md` |
| Container Image Policy | `AGENTS-base.md` |
| Env Var Convention | `AGENTS-base.md` |
| O portão local | `AGENTS-base.md` |
| Git Conventions | `AGENTS-base.md` |

O que ficou aqui é o que é só desta camada: a topologia de três tiers, a árvore
de diretórios, as restrições de segurança derivadas do `ARCHITECTURE.md` deste
repositório, a configuração de modelo, o que cada arquivo de teste cobre, e as
regras de stack acima.

**Em conflito, este arquivo vence** — quem o escreveu conhece este repositório.
