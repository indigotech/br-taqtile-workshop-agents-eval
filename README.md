# Planejador de viagens — workshop de avaliação de agentes

Sistema multi-agente que planeja viagens: consulta as preferências do usuário num SQLite local, clima, eventos e restaurantes, verifica se cabe no orçamento da viagem e reserva a hospedagem. Ele chama o Modelo direto pelo SDK e manda os traces pro Langfuse Cloud.

## Como funciona

Você conversa com um **orquestrador**, que delega cada parte do trabalho a um agente especialista. Cada especialista é exposto ao orquestrador como uma tool:

| Agente | O que faz |
| --- | --- |
| Interpretador de input | Extrai destino, datas, nº de pessoas e preferências |
| Banco | Consulta perfil, preferências, histórico e hospedagens no SQLite |
| Dados públicos | Clima (Open-Meteo), coordenadas (OpenStreetMap) e feriados (Nager.Date) |
| Pesquisa | Sugere eventos e restaurantes no destino |
| Analista de orçamento | Estima os custos e verifica se cabe no orçamento informado pra viagem |
| Ação | Reserva a hospedagem (mock) e registra a decisão no banco |
| Gerador de output | Escreve o roteiro final |

No Langfuse, cada mensagem vira um trace com os agentes, as chamadas ao Modelo e as tools aninhados.

## Requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/). Ele baixa o Python 3.13 sozinho, então não é preciso instalar Python.
- Uma conta gratuita no [Langfuse Cloud](https://cloud.langfuse.com) (plano Hobby), onde ficam os seus traces. Nada do Langfuse roda na sua máquina.
- [Node.js](https://nodejs.org/) 22.22 ou mais novo, só pros evals de LLM como juiz (promptfoo). A instalação ocupa cerca de 2,3 GB em `node_modules/`.
- Uma chave da API do modelo. O padrão é a OpenAI (<https://platform.openai.com/api-keys>); pra usar outro provider compatível com Chat Completions (DeepSeek, Gemini), ajuste `MODEL_BASE_URL` e `MODEL` no `.env`.

## Instalação rápida

Um comando instala o que falta, clona o repositório, instala as dependências (`make install` e `make install-judge`), cria o `.env` e termina rodando os testes (`make test-ci`). Pode rodar de novo à vontade: o que já está pronto é pulado.

**Windows 10/11**, no PowerShell:

```powershell
irm https://raw.githubusercontent.com/indigotech/br-taqtile-workshop-agents-eval/main/scripts/setup_workshop.ps1 | iex
```

O `scripts/setup_workshop.ps1` instala pelo `winget` o Git, o uv, o Node.js 22 e o GNU Make (o Windows pode pedir permissão de administrador), põe a pasta `bin` do Git no PATH, porque o `make` roda as receitas no `sh` que vem com o Git, e clona em `%USERPROFILE%\br-taqtile-workshop-agents-eval`. Sem o `winget`, instale o [App Installer](https://apps.microsoft.com/detail/9NBLGGH4NNS1) antes. Depois, abra um PowerShell novo para o PATH valer e use os comandos `make` normalmente.

Se a máquina precisa ficar no **Node.js 20** (20.19 ou mais novo) e não pode ter o 22, use a variante `scripts/setup_workshop_node20.ps1`:

```powershell
irm https://raw.githubusercontent.com/indigotech/br-taqtile-workshop-agents-eval/main/scripts/setup_workshop_node20.ps1 | iex
```

Ela não instala o Node 22: usa o Node que já existe (e interrompe a instalação se ele for mais antigo que o 20.19) ou, sem Node, instala o 20 pelo `winget`. No lugar do promptfoo fixado no `package.json`, instala o 0.120.19, o último que roda no Node 20.19. O custo: um promptfoo mais antigo que o do resto da turma, e o Node 20, que já saiu de suporte (EOL em abril de 2026). Nessa máquina, reinstale sempre com `make install-judge PROMPTFOO_VERSION=0.120.19`.

**macOS** (Intel ou Apple Silicon), **Linux** (Ubuntu/Debian) ou **WSL2**:

```bash
curl -fsSL https://raw.githubusercontent.com/indigotech/br-taqtile-workshop-agents-eval/main/scripts/setup_workshop.sh | bash
```

O `scripts/setup_workshop.sh` confere git, make e curl (no macOS, pelas Command Line Tools do Xcode; no Linux, pelo `apt-get`), instala sem sudo o uv e o Node.js 22 (pelo nvm) e clona em `~/br-taqtile-workshop-agents-eval`.

Nos dois, `WORKSHOP_DIR` troca a pasta do clone. Se você já baixou o `.env` da turma do Drive (`workshop.env` ou `.env` na pasta Downloads), ele é copiado; senão, o `.env` sai do `sample.env` e você cola a `MODEL_API_KEY`. No fim, o script lista o que falta: as chaves do [Langfuse Cloud](#langfuse-cloud) e o `make run`.

## Setup

Para instalar à mão, sem o script:

```bash
make install        # instala Python e dependências
make setup-env      # cria o .env a partir do sample.env
# edite o .env: preencha MODEL_API_KEY e as chaves do Langfuse (veja abaixo)
make run            # abre o chat no terminal
```

Ao abrir, o chat pergunta seu nome. Quem já tem cadastro (os usuários de exemplo são Ana, Bruno, Carla e Diego) vai direto pra conversa; quem não tem pode se cadastrar ali mesmo, com nome, cidade onde mora e e-mail. O orçamento não fica salvo: muda a cada viagem, então o planejador pergunta quando você não diz.

### Langfuse Cloud

1. Crie uma conta em <https://cloud.langfuse.com> (região EU, plano Hobby gratuito).
2. Crie uma organização e, dentro dela, um projeto: as chaves de API são por projeto.
3. No projeto, abra **Settings > API Keys > Create new API keys**.
4. Cole a public key em `LANGFUSE_PUBLIC_KEY` e a secret key em `LANGFUSE_SECRET_KEY` no `.env`. A secret key só aparece uma vez.

A cada resposta, o chat imprime o link do trace. Com alguma das chaves vazia, o chat roda sem tracing e avisa ao abrir; pra desligar de propósito, coloque `LANGFUSE_TRACING_ENABLED=false` no `.env`.

## Comandos

| Comando | O que faz |
| --- | --- |
| `make run` | Chat no terminal |
| `make run-case-tool-error` | Chat com uma tool falhando em toda chamada (`ERROR_TOOL=search_accommodations`), pra ver um span de erro no Langfuse |
| `make run-case-slow-tool` | Chat com uma tool demorando 5s a mais em toda chamada (`SLOW_TOOL=search_accommodations`), pra ela aparecer como a mais lenta na timeline |
| `make smoke-test` | Roda uma conversa real de ponta a ponta num banco descartável |
| `make run-dataset RUNS=3 CASES=id1,id2` | Roda os casos de `evals/dataset.jsonl` N vezes e salva as saídas em `evals/runs/` |
| `make reset-db` | Recria o banco `data/planner.db` com os dados de exemplo |
| `make test` | Roda os testes (sem chamar a API do Modelo) |
| `make test-model RUNS=3` | Roda os testes de `evals/unit_tests/` chamando o Modelo de verdade (gasta tokens) |
| `make install-judge` | Instala o promptfoo (precisa de Node 22.22+; `PROMPTFOO_VERSION=0.120.19` para o Node 20.19) |
| `make eval-judge ARGS="--repeat 3"` | Roda o eval de LLM como juiz do promptfoo (gasta tokens); `CONFIG=evals/judge/judge_consistency.yaml` roda o de consistência do juiz |
| `make view-judge` | Abre os resultados do promptfoo no navegador |
| `make lint-check` / `make lint-fix` | Lint e checagem de tipos / correção automática |
| `make help` | Lista todos os comandos |

## Avaliando o sistema

`make run-dataset RUNS=3` roda cada caso de `evals/dataset.jsonl` 3 vezes e salva as saídas em `evals/runs/<data-hora>/results.jsonl`, um `RunRecord` por linha. Os evaluators são construídos durante o workshop em cima desses registros.

Cada execução faz uma dúzia ou mais de chamadas ao Modelo. Enquanto estiver ajustando, use `CASES=id1,id2` pra rodar só alguns casos e não gastar a cota gratuita.

### Testes unitários com o Modelo

Testes em pytest que chamam o Modelo de verdade (uma regex na resposta de um agente, a validação de uma saída estruturada) ficam em `evals/unit_tests/`, nunca em `tests/`: os testes de `tests/` não chamam o Modelo e são os que rodam no `make test` e no CI. Os de `evals/unit_tests/` usam o seu `.env` e rodam só com:

```bash
make test-model                                         # todos, cada checagem repetida 3 vezes (RUNS=3)
make test-model RUNS=5 TEST_PATH=evals/unit_tests/test_x.py ARGS="-s -k nome"
```

Sem uma `MODEL_API_KEY` de verdade no `.env`, a pasta inteira é pulada com o motivo. Os testes recebem as fixtures `connection` (um banco SQLite novo e populado por teste, nunca o `data/planner.db`), `model_client` (um `ModelClient()` real) e `runs` (o valor de `RUNS`). Cada teste vira um trace no Langfuse com a tag `unit-test`, se o tracing estiver ligado no `.env`.

Cada execução gasta tokens e a resposta do Modelo muda de uma vez pra outra: repita a checagem `runs` vezes e compare a taxa de acerto com um limite, em vez de depender de uma única resposta.

A mensagem de falha de cada teste mostra o pass@1 (chance de uma execução passar) e o pass^n (chance de todas as n passarem), calculados por `pass_at_k` e `pass_hat_k` em `app/evals/pass_metrics.py`.

### LLM como juiz (promptfoo)

Quando a resposta é texto aberto e a qualidade depende do pedido (sugestões que respeitam as preferências do usuário, por exemplo), regex e similaridade não bastam: um segundo modelo, o juiz, dá a nota seguindo uma rubrica. Os evals ficam em `evals/judge/` e rodam com o [promptfoo](https://www.promptfoo.dev/):

```bash
make install-judge                                              # uma vez, instala o promptfoo
make eval-judge                                                 # agente de pesquisa avaliado pelo juiz
make eval-judge ARGS="--repeat 3"                               # 3 vezes: pass^3 só passa se as 3 passarem
make eval-judge CONFIG=evals/judge/judge_consistency.yaml       # respostas fixas, só o juiz muda
make view-judge                                                 # abre os resultados no navegador
```

O juiz é o mesmo modelo dos agentes, com a chave `MODEL_API_KEY` do `.env`. Cada asserção `llm-rubric` dá uma nota de 0 a 1, e o `threshold` dela é o critério de aprovação. Quando algum teste falha, o `make eval-judge` termina com erro, como o pytest. Os resultados ficam em `.promptfoo/`, dentro do repositório, e nada é enviado pra fora além das chamadas ao Modelo (a telemetria do promptfoo fica desligada).

## Problemas comuns

- **`tracing is off until both are set` ao abrir o chat:** falta `LANGFUSE_PUBLIC_KEY` ou `LANGFUSE_SECRET_KEY` no `.env` (veja [Langfuse Cloud](#langfuse-cloud)).
- **`erro na API do modelo: Error code: 401`:** a `MODEL_API_KEY` do `.env` está errada.
- **`erro na API do modelo: Error code: 429`:** o limite de requisições ou a cota acabou. Espere um minuto ou use outro modelo em `MODEL`.
- **`turno interrompido: atingiu o limite de tokens por turno`:** um turno passou de `MODEL_TOKEN_BUDGET_PER_TURN` (padrão 85 mil tokens, cerca de 2x um turno normal), em geral um agente em loop. A resposta é descartada pra proteger a cota compartilhada; comece uma nova conversa.
- **Trace não aparece no Langfuse:** confira se as chaves são do projeto que você está olhando e se `LANGFUSE_BASE_URL` é `https://cloud.langfuse.com`. Os traces chegam em alguns segundos.
