# Planejador de rolê — workshop de avaliação de agentes

Sistema multi-agente que planeja um fim de semana: consulta orçamento e preferências do usuário num SQLite local, clima, eventos e restaurantes, verifica se cabe no orçamento e reserva a hospedagem. Ele chama o Gemini direto pelo SDK `google-genai`, sem framework de agentes, e manda os traces pra um Langfuse local.

> Esse sistema **não é bom de propósito**. O workshop é sobre encontrar onde ele erra, com evals, e corrigir.

## Como funciona

Você conversa com um **orquestrador**, que delega cada parte do trabalho a um agente especialista. Cada especialista é exposto ao orquestrador como uma tool:

| Agente | O que faz |
| --- | --- |
| Interpretador de input | Extrai destino, datas, nº de pessoas e preferências em JSON |
| Banco | Consulta orçamento, preferências, histórico e hospedagens no SQLite |
| Dados públicos | Clima (Open-Meteo), coordenadas (OpenStreetMap) e feriados (Nager.Date) |
| Pesquisa | Busca eventos e restaurantes com o Google Search do Gemini |
| Analista de orçamento | Estima os custos e verifica se cabe no orçamento |
| Ação | Reserva a hospedagem (mock) e registra a decisão no banco |
| Gerador de output | Escreve o roteiro final |

No Langfuse, cada mensagem vira um trace com os agentes, as chamadas ao Gemini e as tools aninhados.

## Requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/). Ele baixa o Python 3.13 sozinho, então não é preciso instalar Python.
- [Docker](https://docs.docker.com/get-docker/) com Compose, só pro Langfuse. A primeira execução baixa cerca de 1,5 GB de imagens.
- Uma chave da API do Gemini: <https://aistudio.google.com/apikey>.

## Setup

```bash
make install        # instala Python e dependências
make setup-env      # cria o .env a partir do sample.env
# edite o .env e preencha GEMINI_API_KEY
make run-langfuse   # sobe o Langfuse em http://localhost:3000
make run            # abre o chat no terminal
```

Pra entrar no Langfuse use `workshop@example.com` / `workshop123`. As chaves de API já vêm configuradas no `sample.env`, então não precisa gerar nenhuma. A cada resposta, o chat imprime o link do trace.

Sem Docker, dá pra rodar sem observabilidade: coloque `LANGFUSE_TRACING_ENABLED=false` no `.env`.

## Comandos

| Comando | O que faz |
| --- | --- |
| `make run` | Chat no terminal |
| `make smoke-test` | Roda uma conversa real de ponta a ponta num banco descartável |
| `make reset-db` | Recria o banco `data/planner.db` com os dados de exemplo |
| `make run-langfuse` / `make stop-langfuse` | Sobe / para o Langfuse local |
| `make clean-langfuse` | Remove o Langfuse e todos os traces |
| `make test` | Roda os testes (sem chamar a API do Gemini) |
| `make lint-check` / `make lint-fix` | Lint e checagem de tipos / correção automática |
| `make help` | Lista todos os comandos |

## Problemas comuns

- **Porta 3000 ocupada:** troque `LANGFUSE_PORT` e a porta de `LANGFUSE_BASE_URL` no `.env` (por exemplo, pra 3300) e rode `make run-langfuse` de novo.
- **`erro na API do Gemini: 400 INVALID_ARGUMENT`:** a `GEMINI_API_KEY` do `.env` está errada.
- **`erro na API do Gemini: 429`:** a cota gratuita acabou. Espere um minuto ou use outro modelo em `GEMINI_MODEL`.
- **Langfuse não abre logo depois do `make run-langfuse`:** a primeira subida leva de 1 a 2 minutos enquanto os bancos inicializam.
