# Diretrizes de Code Review

> O plugin taqtile-cr lê este arquivo automaticamente
> para adaptar a análise ao contexto do projeto.

---

## Projeto

- **Nome:** br-taqtile-workshop-agents-eval (planejador de rolê)
- **Tipo:** backend-python (aplicação de terminal, sem API HTTP)
- **Layout:** single-repo
- **Linguagem principal:** Python

**Contexto importante:** é o ponto de partida de um workshop de avaliação de agentes. Os agentes são implementados **mal feitos de propósito** — prompts vagos, temperatura alta, orquestração ambígua, tool calls redundantes — para que os alunos detectem e corrijam esses defeitos com evals. O código, por outro lado, segue todas as convenções abaixo.

---

## Stack

### Backend Python

- **Framework:** nenhum — loop de tool calling próprio sobre o SDK `google-genai` (Gemini), sem LangChain/LangGraph/ADK
- **Transporte:** CLI (chat no terminal, `app/cli.py`)
- **ORM/DB:** `sqlite3` da stdlib, SQL escrito à mão (`app/data/schema.sql` + `seed.sql`); sem migrations, `make reset-db` recria o banco
- **Validação:** Pydantic v2 (+ `pydantic-settings`)
- **AI/ML (se aplica):** `google-genai` (Gemini) com function calling manual; Langfuse v4 (OpenTelemetry) para observabilidade, rodando local via `docker-compose.yml`
- **Logger:** `logging` stdlib configurado em `app/core/logging.py` (`setup_logging()`); cada módulo usa `logger = logging.getLogger(__name__)` com formatação `%` lazy
- **Errors:** falhas de tool viram `error` devolvido ao modelo (`ToolRegistry.execute` nunca levanta); erros da API do Gemini são tratados no CLI sem derrubar a conversa
- **Auth:** — (sem autenticação; o usuário é escolhido no início do chat)
- **Nomes/sufixos de módulo aceitos:**
  - `*_agent.py` → agente concreto com factory `build_*_agent` (camada `agents`)
  - `*_tool.py` → tool concreta, subclasse de `Tool[Input, Output]` (camada `tools`)
  - `*_data_source.py` → acesso ao SQLite (camada `data`)
  - `models.py` → modelos Pydantic das linhas do banco (camada `data`)
- **Paginação:** —
- **i18n de erros:** hardcoded; mensagens de log em inglês, prompts e textos para o usuário em português
- **Tipagem:** mypy strict (`[tool.mypy] strict = true`, com plugin `pydantic.mypy`)
- **Testes:** pytest, com `ScriptedGeminiClient` (`tests/helpers.py`) no lugar da API real e um SQLite temporário por teste

---

## Estrutura e Arquitetura

### Estrutura de Pastas

```
app/
├── core/                 # config, logging, Langfuse, cliente Gemini, Tool/ToolRegistry, loop de tools, Agent
├── data/                 # schema.sql, seed.sql, conexão SQLite, modelos e datasources
├── tools/                # tools concretas (*_tool.py)
├── agents/               # agentes concretos (*_agent.py) e seus prompts
└── cli.py                # entrypoint e composition root
scripts/                  # utilitários de linha de comando (reset do banco)
tests/                    # espelha app/
```

### Camadas e responsabilidades

- **`core/`** — primitivas reutilizadas por todos os agentes. Único lugar que chama o SDK do Gemini e abre observações do Langfuse.
- **`data/`** — todo acesso ao SQLite e (futuramente) às APIs públicas externas. Converte linhas/respostas em modelos Pydantic na borda.
- **`tools/`** — funções expostas ao modelo; o `input_model` vira a function declaration.
- **`agents/`** — prompt + tools + parâmetros de modelo de cada agente.

### Regra de dependências

- `core/` não importa de nenhuma outra camada de `app/`
- `data/` importa só de `core/`
- `tools/` importa de `data/` e `core/`
- `agents/` importa de `tools/`, `data/` e `core/`
- `cli.py` pode importar de qualquer camada

---

## Padrões e Convenções

### Modelos

- `BaseModel` é o único tipo de modelo — sinalizar 🟠 `NamedTuple`, `TypedDict` ou `dataclass`
- Valores transitórios com `ConfigDict(frozen=True)`
- `dict[str, Any]` só para payload realmente aberto (argumentos crus de function call, saída serializada de tool, metadata do Langfuse); linhas do SQLite e respostas de API externa são validadas num modelo na borda
- Preferir `Model.model_validate(...)` ao construtor por keyword, exceto ao compor de várias fontes

### Tools e agentes

- Todo campo do `input_model` de uma tool tem `Field(description=...)` — é o que o modelo lê
- Toda chamada ao Gemini passa por `GeminiClient.generate`, e toda execução de tool por `ToolRegistry.execute` — chamar o SDK direto perde o trace
- Datasources nomeiam as colunas do `SELECT` e usam placeholders `?`

### Variáveis de ambiente

- Toda nova variável deve ser adicionada **em todos** os pontos abaixo, na mesma PR:
  - `app/core/config.py` — campo na `Settings`
  - `sample.env` — entrada documentada
  - `test.env` — valor usado pelos testes
- Sinalizar 🟠 quando uma var aparecer em só parte desses arquivos
- Segredos reais nunca vão em `sample.env`/`test.env` (as chaves do Langfuse local são fixas e públicas de propósito)

### Testes

- Nunca chamar a API real do Gemini nos testes
- Mínimo: happy path + principal edge case (ex.: usuário inexistente, argumento inválido)

---

## O Que NÃO Comentar no Review

> O plugin respeita esta lista e não produzirá comentários sobre estes tópicos.

- Formatação e espaçamento (Ruff formatter)
- Ordem de imports (Ruff)
- Regras de estilo/lint cobertas por Ruff
- Checagem de tipos já coberta pelo mypy (strict)
- **Qualidade do comportamento dos agentes** — prompts vagos, temperatura alta, orquestração que pula etapas, tool calls redundantes e respostas ruins podem ser defeitos intencionais do workshop. Só comentar se a PR declarar que está corrigindo esse comportamento
- Credenciais fixas no `docker-compose.yml` e `sample.env` do Langfuse local (stack descartável, só escuta em localhost)

---

## Arquivos Não Analisados

- `uv.lock`

---

## Severidades

| Emoji | Nível      | Significado                                   | Bloqueia merge? |
| ----- | ---------- | --------------------------------------------- | --------------- |
| 🔴    | Crítico    | Bug, segurança, perda de dados, regressão     | Sim             |
| 🟠    | Importante | Problema de design/arquitetura                | Idealmente sim  |
| 🟡    | Sugestão   | Melhoria de qualidade, legibilidade           | Não             |
| 🟢    | Dica       | Oportunidade de aprendizado                   | Não             |
| 💚    | Elogio     | Algo feito particularmente bem                | —               |
