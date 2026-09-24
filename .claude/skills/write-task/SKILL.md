---
name: write-task
description: Escreve e (após confirmação) cria tasks/issues para este projeto. Use sempre que o usuário pedir para descrever, redigir, planejar ou criar uma task/issue/ticket para este repositório. Garante que o escopo seja consultado, dúvidas de arquitetura sejam levantadas antes de escrever, e a descrição siga o template e o padrão de nomenclatura combinados com o time. É agnóstica de linguagem/stack (infere convenções e comandos dos docs do repo) e de issue tracker (Jira / Linear / GitHub Issues), e pergunta a origem do escopo em vez de assumir.
---

Você é o redator de tasks deste projeto. Esta skill captura o processo de descrição → revisão → criação de issue. Siga **todos** os passos.

Esta skill é **agnóstica de linguagem e stack**. Ela não assume Python, Node, Go ou qualquer framework: no passo 0 ela descobre a stack, as convenções e os comandos do repositório a partir dos docs e do próprio código, e usa isso no restante do fluxo.

---

## Princípio central

A task é um contrato com quem vai implementar. Ela precisa transmitir:

- Por que essa task existe (referência ao escopo/requisito).
- O que está dentro e o que está fora do escopo.
- Decisões já tomadas vs. pontos em aberto (estes **devem** aparecer explicitamente).
- Critérios objetivos de aceitação.
- Dependências de outras tasks.

Não invente respostas para decisões de arquitetura. **Pergunte ao usuário**, e se a resposta ficar pendente, marque o ponto como aberto na própria descrição.

---

## Fluxo

### 0. Descobrir a stack e as convenções do repo (uma vez por sessão)

Antes de escrever qualquer task, levante o contexto técnico do repositório a partir dos docs e do código. **Não hardcode** linguagem, framework ou comandos — infira:

- **Docs de convenção** — leia, se existirem: `REVIEW.md`, `CLAUDE.md` (raiz e subpastas), `CONTRIBUTING.md`, `README.md`, `docs/`. Costumam declarar stack, arquitetura por camadas, sufixos/nomes de módulo e a Definition of Done.
- **Manifesto/lockfile** — identifique linguagem e ferramentas pelo manifesto do projeto: `package.json` (Node/Bun), `pyproject.toml`/`requirements.txt` (Python), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml`/`build.gradle` (JVM), `Gemfile`, etc.
- **Runner de comandos** — descubra como o projeto roda lint/format/test/build/migrations. Procure, nesta ordem: `Makefile`/`Justfile`/`Taskfile`, `scripts` do `package.json`, alvos citados no README. Anote os comandos reais (ex.: `make lint-check`, `npm run test`, `cargo test`, `go test ./...`) — esses viram o **DoD** do template, não invente.
- **Layout e arquitetura** — mapeie as pastas principais e a regra de dependência entre camadas a partir dos docs e da árvore de diretórios. Use os nomes/sufixos reais do repo ao listar arquivos.

Registre mentalmente (ou peça ao usuário se ambíguo): linguagem, framework, comandos de lint/test/build/migration, e o padrão de camadas. Reuse isso nos passos 3, 5 e 8. Se o repo não declarar algo essencial (ex.: como rodar os testes), **pergunte** em vez de assumir.

### 1. Entender o pedido

Antes de qualquer coisa, leia o que o usuário pediu. Identifique:

- Camada: backend (`[BE]`), frontend (`[FE]`), full-stack (`[FS]`), infra (`[Infra]`).
- Feature/domínio: o recurso afetado (ex.: `channels`, ou o domínio novo que está sendo pedido).
- Tipo de trabalho: novo endpoint, alteração de modelo, migration, refactor, etc.

Se algo crítico está ambíguo (ex.: "criar recurso X" — quem pode criar? que campos?), **pergunte antes** em vez de assumir.

### 2. Consultar o escopo (origem configurável)

Esta skill **não assume** uma página de escopo fixa. No início, descubra de onde vem o escopo, nesta ordem de preferência:

1. **O que o usuário forneceu** — se ele colou texto, linkou um doc (Notion, Confluence, Google Docs) ou citou um requisito, use isso. Para links de doc com MCP disponível (ex.: `mcp__claude_ai_Notion__notion-fetch`), puxe o conteúdo.
2. **O próprio repositório** — `README.md`, `REVIEW.md` e o código existente descrevem o que o sistema já faz e suas convenções. Use-os como base de "estado atual".
3. **Pergunte** — se não houver escopo claro nem no pedido nem no repo, peça ao usuário: "Qual é a origem do escopo desta task? (cole o trecho, mande o link, ou descreva o requisito)". Não siga adiante sem entender o requisito que a task atende.

Toda task deve referenciar a origem do escopo (link/doc/requisito) na seção "Referências". Se houver numeração de requisitos (RF/RNF, US, etc.), cite-a.

### 3. Consultar o código antes de descrever

Se a task mexe em código existente (rota/controller, regra de negócio, acesso a dados, model, migration), **leia o arquivo** antes de descrever. Sem isso, a descrição vira teoria.

Se a task cria algo novo (rota, entidade, domínio), **leia a camada mais próxima** — o router existente, o datasource de uma entidade vizinha, o model análogo — para verificar se o recurso já existe sob outro nome e para espelhar o padrão de nomeação e estrutura adotado. Não descreva a criação de algo greenfield sem antes confirmar como o repo nomeia e organiza o equivalente mais próximo.

Aplique as convenções que você levantou no passo 0 — não as reinvente:

- Respeite a **arquitetura por camadas** do repo e a regra de dependência entre elas (a direção permitida vem dos docs/código, não de um padrão fixo).
- Use os **nomes e sufixos reais** do projeto (ex.: o que o repo chama de controller/router, service/use-case, repository/datasource, model/entity).
- Identifique e **reaproveite o que já existe** — helpers, schemas, padrões de validação, clientes de DB/HTTP — em vez de propor recriar.
- Atenção a pontos transversais do repo: auth, tratamento de erros, logging, paginação, migrations — descreva o comportamento esperado conforme o padrão já adotado.

Ao referenciar arquivos na task, use o **caminho real** do repositório.

### 4. Levantar pontos abertos antes de escrever

Antes de redigir a descrição, faça uma rodada de perguntas ao usuário sobre tudo que dependa de decisão de produto/arquitetura e que você ainda não tenha confirmado. Exemplos do que **sempre** vale confirmar:

- **Regras de acesso** — quem pode chamar? Há restrição por escopo/recurso?
- **Comportamento em ações destrutivas** (somente operações de write/delete) — soft delete vs. hard delete? cascata? idempotência?
- **Contrato da interface** — para endpoints/RPCs: recurso vs. ação, prefixo/rota, verbo/método, código de sucesso.
- **Validações de entrada** (somente se a task recebe input) — políticas de campo, obrigatoriedade, valores default, formato (UUID, enum).
- **Mudanças de schema/dados** (somente se a task cria/altera modelo ou migration) — exige migration? altera coluna/enum existente? é reversível?
- **Campos retornados** — incluir metadados? expor campos novos na resposta (e a convenção de naming do repo)?

Faça perguntas curtas e objetivas, em texto. Se houver mais de uma decisão a tomar, considere usar `AskUserQuestion` para apresentar opções com recomendações.

Quando recomendar um caminho, dê **1-2 razões** e cite a alternativa de forma honesta — não apresente como decidido.

### 5. Escrever a descrição

Use o template abaixo. Mantenha em português, markdown limpo, sem emojis. Conciso mas completo.

#### Seções obrigatórias (toda task)

- Contexto
- Escopo
- Fora do escopo
- Critérios de aceitação
- Referências

#### Seções condicionais (regra clara de quando incluir)

- **Contrato** — se a task expõe endpoint HTTP/REST.
- **Fluxo** — se há ≥3 passos com ordem importando. Caso contrário, descreva em prosa dentro de Escopo.
- **Pontos em aberto** — se houver decisão pendente. Se vazia, **OMITIR a seção** (não deixar "N/A").
- **Dependências** — se houver. Não citar tasks no corpo de outras seções (ver regra no passo 8).

#### Regra de não-redundância

Cada regra de negócio aparece **em exatamente um lugar**:

- **Fluxo** — sequência ordenada do happy path. Sem regras de validação inline, sem edge cases.
- **Escopo > Contrato** — request/response/erros. Regras de validação de payload moram no schema descrito aqui, não em seção própria.
- **Critérios de aceitação** — forma verificável das regras. Lista o que será testado, não re-descreve a regra.

**Seções proibidas:**

- "Comportamento esperado" — redundante com Fluxo + Contrato. Se há invariante/edge case que não cabe em nenhum dos dois, vire um item específico nas AC.
- "Regras de validação detalhadas" — vai no schema do Contrato.

#### Template

```markdown
# [BE] METHOD /path — resumo curto

## Contexto

Por que essa task existe. Cite o requisito/escopo de origem.

**Assunções desta task:** quando aplicável, liste premissas que mudam o comportamento (ex.: modelo já existe no banco, recurso pai já implementado).

## Pontos em aberto (omitir se vazio)

Tudo que ainda não foi confirmado, **explicitamente marcado**. Exemplos:

- #1 — Soft delete ou hard delete? Pendente: PM.
- #2 — Endpoint exige auth de admin — proposta: sim; pendente de validação.

Outras seções referenciam por âncora (ex.: "[ver ponto em aberto #1]") em vez de repetir a dúvida.

## Fluxo (se ≥3 passos com ordem importando)

Passo a passo numerado do happy path.

## Escopo

### Camadas a tocar

Liste os arquivos concretos a criar/alterar, usando os caminhos e a nomenclatura
reais do repo (camada de apresentação, regra de negócio, acesso a dados, schema/migration).

### Contrato (se a task expõe endpoint/interface)

**Request**
Método, rota/identificador, headers/params relevantes, body com exemplos. Validações de entrada descritas aqui (no schema de payload).

**Response (código de sucesso)**
Exemplo de payload retornado.

**Erros**
Lista de códigos/erros com o motivo de cada.

## Fora do escopo (outras tasks)

Lista de coisas próximas que **não** entram nesta task. Diferencia "fora deste recorte" de "fora do projeto".

## Critérios de aceitação

Lista verificável e **específica desta task**:

- [ ] Comportamento principal funciona.
- [ ] Cada regra de acesso/validação testada.
- [ ] Cada erro previsível retorna o código esperado.

NÃO incluir em AC (são DoD do projeto, aplicam-se a qualquer task):

- Lint/format/typecheck e testes passando — usando os comandos reais do repo levantados no passo 0.
- Code review / PR aberto.
- Migration/mudança de schema testada (se o repo tiver esse fluxo).
- Documentação atualizada.

## Dependências (se houver)

Espelho legível dos links de dependência criados no tracker (ver passo 8). Não é fonte de verdade.

## Referências

- Escopo: <link ou descrição do requisito de origem> — <ID do requisito, se houver>.
```

### 6. Nomenclatura

**Limite duro:** summary ≤ 70 caracteres (boards costumam truncar por aí). Se não couber, a task provavelmente está fazendo coisas demais — considerar dividir.

Título sempre começa com prefixo de camada entre colchetes:

- `[BE]` — backend.
- `[FE]` — frontend.
- `[FS]` — full-stack.
- `[Infra]` — infraestrutura/CI/CD.

**Domínio entre colchetes (`[Channels]`, `[Auth]`, etc.):** só incluir se o usuário pedir explicitamente. Default = sem domínio.

**Fórmula:** `[Camada] <âncora curta> — <verbo + objeto>`

- Âncora = método+rota (endpoints) **ou** nome do recurso/tela (FE) **ou** nome do artefato (model, migration, pipeline).
- Para endpoints autoexplicativos, o trecho após o `—` pode ser omitido.

Exemplos válidos (genéricos — adapte à rota/recurso real do repo):

- `[BE] POST /api/v1/<recurso>`
- `[BE] GET /api/v1/<recurso> — listar com filtro`
- `[BE] Modelo de domínio <Entidade>`
- `[BE] Migration para tabela de <recurso>`
- `[Infra] Pipeline de CI para a API`

Diretrizes:

- Para endpoints, método + rota é a âncora — não repetir o que a rota já diz.
- Evitar verbos genéricos ("ajustar", "melhorar") sem objeto direto.
- Manter consistente com tasks recentes do board em caso de dúvida.

### 7. Revisar antes de subir

Antes de criar a issue:

- Releia a descrição em texto e mostre ao usuário.
- Pergunte: "Quer que eu crie a issue?" ou aceite uma confirmação direta ("pode subir").
- **Gate de pontos em aberto:** se a seção "Pontos em aberto" não estiver vazia, pergunte: "Há N pontos em aberto. Criar mesmo assim (vira backlog de refinamento), ou prefere resolver agora?" — default é **não criar**, resolver primeiro.
- Aceite ajustes — frequentemente o usuário vai apertar/relaxar regras depois de ver a descrição inteira. Quando isso acontecer, reescreva a descrição **inteira** atualizada (não só o trecho mudado), porque o time prefere copiar a versão final completa.

### 8. Criar a issue (agnóstico de tracker)

Esta skill **não assume** um tracker fixo. Pergunte (ou confirme, se o usuário já indicou) onde criar:

> "Onde quer criar essa issue? (Jira / Linear / GitHub Issues / só a descrição)"

Então use o caminho correspondente:

- **Jira** — `mcp__claude_ai_Atlassian__createJiraIssue` com `cloudId`, `projectKey`, `issueTypeName: Task`, `summary` (≤70 chars), `contentFormat: markdown`, `description`. Confirme `cloudId`/`projectKey` com o usuário se não souber.
- **Linear** — `mcp__claude_ai_Linear__save_issue` com o `team` correto, `title` e `description` (markdown). Confirme o time se não souber.
- **GitHub Issues** — `gh issue create --title "<summary>" --body-file <arquivo.md>` no repo atual. Escreva o markdown num arquivo temporário no scratchpad e passe via `--body-file` para preservar a formatação.
- **Só a descrição** — não crie nada; entregue o markdown final para o usuário copiar.

**Dependências:** para cada item em "Dependências", crie o link nativo do tracker escolhido:

- Jira: `mcp__claude_ai_Atlassian__createIssueLink` (`is blocked by` para predecessoras, `relates to` para vizinhas).
- Linear: relação via `save_issue` / relations.
- GitHub: referência por número (`#NN`) ou task list no corpo.

A seção "Dependências" no markdown é apenas espelho legível — os links no tracker são a fonte de verdade. Se uma dep não tem link criado, ela não existe.

Após criar, responda ao usuário com a chave/URL da issue e um resumo de 1 linha.

---

## Heurísticas que evitam erros recorrentes

- **Não esconda decisões pendentes.** Se você precisou supor algo, mova para "Pontos em aberto" e referencie por âncora — nunca dilua "(confirmar com PM)" no meio de um bullet de regra.
- **AC é o que diferencia esta task das outras.** Se um item se aplicaria a qualquer task do projeto, é DoD, não AC — fora da lista.
- **Não invente APIs/colunas/serviços.** Antes de citar um método utilitário, schema ou coluna do banco, confirme que existe (Read/Bash).
- **Reaproveite o que já está no código.** Se já existe um datasource, um schema de resposta ou um padrão de regra de negócio, cite por nome em vez de pedir para criar de novo.
- **Idempotência e mudanças de schema são clássicos pontos de atenção.** Sempre que a task mexe em recurso compartilhado, enum ou schema do banco, descreva o comportamento esperado e se a mudança é reversível.
- **Siga a convenção de API do repo.** Se o time evita verbo na URL, respeite (ações em massa via método HTTP no recurso, não `/recurso/acao`). Na dúvida, espelhe endpoints existentes.
- **Respeite a regra de dependência das camadas** conforme levantada no passo 0 — a apresentação não acessa dados direto, a regra de negócio não depende do framework de transporte.
- **Não comemore antes da hora.** Confirme com o usuário antes de criar a issue; revise o texto.

---

## O que NÃO fazer

- Não criar a issue sem revisão explícita do usuário.
- Não assumir um tracker ou board específico — sempre pergunte/confirme antes de criar.
- Não inventar números de issue em referências — só citar IDs que você sabe que existem na conversa atual ou que o usuário forneceu.
- Não criar epics, sub-tasks ou outros tipos de issue além de `Task` sem solicitação.
- Não copiar trechos de tasks anteriores sem revisar se o contexto ainda se aplica.
- Não citar uma issue no corpo do Contexto/Escopo sem também criar o link de dependência — menção solta sem link quebra o rastreamento.
- Não diluir dúvida no meio de um bullet de regra — mover para "Pontos em aberto" e deixar a regra como TBD com âncora.
- Não criar seções "Comportamento esperado" ou "Regras de validação detalhadas" — são redundantes com Fluxo + Contrato + AC.
- Não incluir itens de DoD do projeto (lint/typecheck/test com os comandos do repo, code review, migration testada) na lista de Critérios de aceitação.
- Não incluir domínio entre colchetes no summary a não ser que o usuário peça.
