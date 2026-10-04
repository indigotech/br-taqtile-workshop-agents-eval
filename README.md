# Planejador de viagens — workshop de avaliação de agentes

Sistema multi-agente que planeja viagens: consulta as preferências do usuário num SQLite local, clima, eventos e restaurantes, verifica se cabe no orçamento da viagem e reserva a hospedagem. Ele chama o Modelo direto pelo SDK e manda os traces pra um Langfuse local.

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
- [Docker](https://docs.docker.com/get-docker/) com Compose, só pro Langfuse. A primeira execução baixa cerca de 1,5 GB de imagens.
- Uma chave da API do modelo. O padrão é a OpenAI (<https://platform.openai.com/api-keys>); pra usar outro provider compatível com Chat Completions (DeepSeek, Gemini), ajuste `MODEL_BASE_URL` e `MODEL` no `.env`.

## Setup

```bash
make install        # instala Python e dependências
make setup-env      # cria o .env a partir do sample.env
# edite o .env e preencha MODEL_API_KEY
make run-langfuse   # sobe o Langfuse em http://localhost:3000
make run            # abre o chat no terminal
```

Ao abrir, o chat pergunta seu nome. Quem já tem cadastro (os usuários de exemplo são Ana, Bruno, Carla e Diego) vai direto pra conversa; quem não tem pode se cadastrar ali mesmo, com nome, cidade onde mora e e-mail. O orçamento não fica salvo: muda a cada viagem, então o planejador pergunta quando você não diz.

Pra entrar no Langfuse use `workshop@example.com` / `workshop123`. As chaves de API já vêm configuradas no `sample.env`, então não precisa gerar nenhuma. A cada resposta, o chat imprime o link do trace.

Sem Docker, dá pra rodar sem observabilidade: coloque `LANGFUSE_TRACING_ENABLED=false` no `.env`.

## Comandos

| Comando | O que faz |
| --- | --- |
| `make run` | Chat no terminal |
| `make run-case-tool-error` | Chat com uma tool falhando em toda chamada (`ERROR_TOOL=search_accommodations`), pra ver um span de erro no Langfuse |
| `make run-case-slow-tool` | Chat com uma tool demorando 5s a mais em toda chamada (`SLOW_TOOL=search_accommodations`), pra ela aparecer como a mais lenta na timeline |
| `make smoke-test` | Roda uma conversa real de ponta a ponta num banco descartável |
| `make run-dataset RUNS=3 CASES=id1,id2` | Roda os casos de `evals/dataset.jsonl` N vezes e salva as saídas em `evals/runs/` |
| `make reset-db` | Recria o banco `data/planner.db` com os dados de exemplo |
| `make run-langfuse` / `make stop-langfuse` | Sobe / para o Langfuse local |
| `make clean-langfuse` | Remove o Langfuse e todos os traces |
| `make test` | Roda os testes (sem chamar a API do Modelo) |
| `make test-model RUNS=3` | Roda os testes de `evals/unit_tests/` chamando o Modelo de verdade (gasta tokens) |
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

## Problemas comuns

- **Porta 3000 ocupada:** troque `LANGFUSE_PORT` e a porta de `LANGFUSE_BASE_URL` no `.env` (por exemplo, pra 3300) e rode `make run-langfuse` de novo.
- **`erro na API do modelo: Error code: 401`:** a `MODEL_API_KEY` do `.env` está errada.
- **`erro na API do modelo: Error code: 429`:** o limite de requisições ou a cota acabou. Espere um minuto ou use outro modelo em `MODEL`.
- **`turno interrompido: atingiu o limite de tokens por turno`:** um turno passou de `MODEL_TOKEN_BUDGET_PER_TURN` (padrão 85 mil tokens, cerca de 2x um turno normal), em geral um agente em loop. A resposta é descartada pra proteger a cota compartilhada; comece uma nova conversa.
- **Langfuse não abre logo depois do `make run-langfuse`:** a primeira subida leva de 1 a 2 minutos enquanto os bancos inicializam.
