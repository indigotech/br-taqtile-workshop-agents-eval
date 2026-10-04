---
name: worktree-flow
description: Delivery workflow for any change to this repository — open an isolated git worktree and branch, delegate the work to a subagent inside it, then merge into main, push, and remove the branch and worktree, all without stopping for approval. Use this whenever the user asks to make, change, add, remove, fix, refactor or implement anything in this repo (code, agent prompts, tests, dataset, docs, config, dependencies) — "faz X", "muda Y", "adiciona Z", "corrige", "implementa", "remove", "spawne um subagente para…" — even small one-line edits and even when they don't mention worktrees or branches. Several independent requests in one message become one subagent each, in parallel. Not for read-only work: questions, explanations, analyses, cost estimates or reviews that change no file.
---

# Worktree flow

This repo ships straight to `main` (no PR / gitflow — the user's call), but every change is still built in isolation: a subagent works in its own git worktree and branch, the main session verifies and merges, then cleans up. The point is that the main checkout is never half-edited, parallel tasks can't trample each other, and the user gets a finished, pushed result without approving each step.

## 1. Preflight (main session)

```bash
git status --short --branch     # main checkout must be clean
git fetch -q origin && git pull -q --ff-only
```

- Uncommitted changes in the main checkout are the user's work in progress, not yours: ask what to do with them before going on. A worktree branches from the committed `HEAD`, so anything uncommitted would silently be left out of the subagent's base.
- If `pull --ff-only` fails, local and remote `main` diverged — stop and tell the user instead of resolving it on your own.

## 2. Delegate (one subagent per independent task)

Spawn each with the Agent tool and `isolation: "worktree"`: the harness creates the worktree under `.claude/worktrees/` and a branch named `worktree-agent-<id>` from the current `HEAD`, and reports both in the completion notification. Independent tasks go out in the same message so they run in parallel.

Give each subagent a complete brief — it starts with none of this conversation:

- **The task** in the user's words plus everything you already know: relevant files, decisions the user made, what to leave alone.
- **Read first**: the root `CLAUDE.md` and the `CLAUDE.md` of every layer it touches, and follow their conventions.
- **Deliberate defects**: the agents are bad on purpose for the workshop. Change prompts or parameters only as far as the task asks, and never document a deliberate defect anywhere in the repo — the instructor's answer key lives outside it, since students read this code.
- **Verify**: `make test-ci` and `make lint-check` must pass in the worktree.
- **No real model API in the worktree**: `.env` is git-ignored, so the worktree has no API key. Tell the subagent not to read the main checkout's `.env` in any way (no `source`, no `--env-file`) — the isolation is deliberate — and to list instead the real-API checks it would run (smoke test, one targeted script); you run them after the merge.
- **Commit, don't push**: one or more commits on its branch, in the repo style — `feat(scope): …` / `fix(scope): …`, message in Portuguese, ending with the attribution line from the system reminder (currently `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`).
- **Parallel siblings**: when several subagents run at once, tell each which files the others own (e.g. "another engineer is changing the users section of `seed.sql`; only touch the cities section") so merges stay mechanical.
- **Report back**: branch, commit hash, files changed, test/lint results, the real-API checks still pending, and anything it deliberately left out.

While they run, tell the user in a line or two what each one is doing.

## 3. Verify and merge (main session)

Subagent reports are claims, not facts — they have been wrong in this repo before (one reported a stale `CLAUDE.md` that was fine). Check before merging:

```bash
git log --oneline main..<branch>    # the commits it says it made exist
git diff --stat main...<branch>      # the scope matches the task
```

Then merge each branch in turn, keeping a merge commit so the history shows where each piece came from:

```bash
git merge --no-edit <branch>
```

- **Conflicts**: resolve them by keeping the intent of both sides (e.g. one branch made the budget come from the conversation, the other converted foreign prices to reais — the merged prompt does both). If the two intents genuinely contradict, ask the user; don't pick a winner silently.
- After all merges: `grep -rn '<<<<<<<\|>>>>>>>' .` must find nothing.

## 4. Gate on the merged result (main checkout, before pushing)

```bash
make install        # only if pyproject.toml or uv.lock changed
make test-ci
make lint-check
```

Then the real-API checks — the main checkout has `.env`:

- `make smoke-test` (~US$ 0.01) whenever the change touches agents, prompts, tools, `app/core`, the dataset or the scripts. Skip it for docs-only or test-only changes and say so.
- Any targeted check a subagent listed as pending. Read a subagent-written script fully before running it.

If the gate fails, fix small, obvious breakage directly on `main` and commit it (`fix(scope): …`). If the fix isn't obvious, undo the merge (`git reset --hard ORIG_HEAD` — safe only because nothing is pushed yet) and report to the user; never push a red `main`.

## 5. Push and clean up

```bash
git push -q origin main
git worktree remove --force .claude/worktrees/<worktree-dir>
git branch -D <branch>
git worktree prune
git status --short --branch     # should read: ## main...origin/main
```

`-D` is fine here because the branch was just merged and pushed; check `git branch --merged main` first if anything looks off. Never push the worktree branches themselves — their commits already live in `main`.

## 6. Report to the user

Short and in the user's language: what changed (by task), the conflicts resolved and how, the gate results (tests, lint, smoke test with token counts when relevant), anything a subagent flagged or that you noticed in real runs (behavior changes, possible defects you didn't touch), the pushed commit(s), and confirmation that the worktrees and branches are gone. If the change alters agent behavior the workshop observes, offer a note for the instructor's answer key — as text for the user to paste, never as a file in the repo.

## When to step out of the flow

- The user explicitly asks for something else ("só me mostra o diff", "não sobe ainda", "faz direto aqui") — follow that; it overrides this skill.
- Read-only requests (explain, analyze, estimate, review) need no worktree.
- Operations on the repo's own git state (cleanup, push what's already committed) are done directly.
