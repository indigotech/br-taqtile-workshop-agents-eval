---
name: update-deps
description: Structured dependency-update process for Python/uv projects — batch triage, risk waves, supply-chain checks, breaking-change impact analysis. Use whenever the user asks to update dependencies, bump libs, upgrade packages, check outdated deps, or handle vulnerability findings — e.g. "atualiza as libs", "update dependencies", "bump deps", "tem lib desatualizada?".
---

# update-deps

Update dependencies in risk waves with test gates, instead of lib-by-lib.

`pyproject.toml` pins exact versions (`==`) and `uv.lock` is committed, so every
bump is an edit to `pyproject.toml` plus a re-lock. Use `uv add 'lib==X.Y.Z'`
(`uv add --group dev '…'` for the dev group) rather than editing by hand — it
rewrites the pin and re-locks in one step. **Never hand-edit `uv.lock`.**

## 0. Python and uv runtime (pre-step)

Compare the project's Python version against the current stable release. It
lives in two places — check both: `.python-version` and `requires-python` in
`pyproject.toml`; CI reads `python-version-file`, so it follows `.python-version`
for free. This project runs on students' machines during a workshop, with uv
downloading the interpreter, so confirm uv ships a build for the new version on
macOS, Linux and Windows. A minor bump (3.13 → 3.14) is a major-risk change:
read the "What's New" page for removals and deprecations that hit the code, and
check that every C-extension dependency (`pydantic-core`, `grpcio` if present)
already publishes wheels for it — no wheel means a source build on a lab
machine that has no compiler.

uv itself is pinned in the `uv_build` range in `[build-system]`, and the local
uv (`uv --version`) should fit it. uv ships weekly and its own advisories land
in the triage below, so it is rarely the pin to leave behind.

Add each runtime bump as its own row in the wave-plan checkpoint (step 1) —
apply it only after approval, updating every location consistently.

## 1. Triage (one pass, all libs)

Run once, over both the main dependencies and the `dev` group:

- `uv tree --outdated` at full depth, once — it resolves from `uv.lock` (no
  synced `.venv` needed) and every outdated package lands on some `(latest: …)`
  line, direct or transitive, attributed to the parent that pulls it. Read all
  those lines, not the top-level rows: a direct dep that is also someone's
  transitive is printed once in full and then collapsed to `(*)` **without the
  annotation** wherever it repeats, so `langsmith` can carry its `(latest:)`
  nested under another package and look current at the top level.

  Do not cap the depth. A truncated tree *misses* packages that sit deeper
  (`pyasn1` sits several levels down, under `google-genai`'s auth stack) and *repeats* the
  ones it does reach, since uv only collapses a subtree it has already printed
  in full.

  `make list-outdated-dependencies` (`uv tree --outdated --depth 1`) is the
  quick human read of the same data — the direct deps only, one flat level, so
  every pin carries its own annotation. Convenience, not a second pass: the full
  tree already contains everything it reports.
- **Vulnerabilities and package health** — `uv audit --frozen`, which resolves
  from `uv.lock` (no sync, no export) and queries OSV for every package,
  transitives included. It reports known vulnerabilities *and* adverse project
  statuses (yanked, deprecated, archived) in one pass. Useful flags:
  `--no-dev` / `--only-dev` to separate runtime risk from tooling risk,
  `--output-format json|sarif`, `--ignore-until-fixed <ID>` for an advisory with
  no released fix.

  The command is still **experimental** — it prints a warning (silenced with
  `--preview-features audit-command`) and its output may change, so read it, but
  don't build parsing around the text format.

  `uvx uv-secure uv.lock` complements it with `--max-age-days`, a
  release-staleness signal `uv audit` has no equivalent for. **Always name the
  lockfile.** Given no path it defaults to the working directory and walks it for
  every manifest it finds — which here means the sibling worktree locks under
  `.claude/worktrees/`, each resolved from a different branch, reported as if
  they were this project's. No flag excludes a path (`--ignore-vulns` /
  `--ignore-pkgs` suppress findings, not files), and the per-lock reports are
  near-indistinguishable: no filename in the tables, and the `Checked: N
  dependencies` header collides whenever the branches happen to resolve the same
  package count. Read the whole output, too — vulnerabilities print as their own
  table *above* the maintenance one, so tailing the last lines drops them
  silently. (`pip-audit` is the better-known tool but a poor fit here: pointed at
  a requirements file it spawns a pip-bearing virtualenv to resolve, which fails
  under a sandbox even with `--no-deps`.)
- **Publish date** — PyPI's JSON API, per candidate version:
  `curl -s https://pypi.org/pypi/<lib>/<version>/json | jq '{upload: .urls[0].upload_time_iso_8601, yanked: .info.yanked, yanked_reason: .info.yanked_reason}'`

Classify every lib into:

- **Wave 1 — patch**: patch-only bumps.
- **Wave 2 — minor**: minor bumps with no breaking changes.
- **Wave 3 — major**: major bumps, or any bump whose changelog mentions breaking
  changes. A minor bump of a 0.x lib counts as major — breaking by convention.

While classifying, apply:

- **Semver is a convention, not a rule, on PyPI.** Unlike npm, nothing enforces
  it: projects ship breaking changes in minors, some use CalVer (where the
  "major" is a year and carries no risk signal), and type stubs version
  independently of the lib they describe. Never classify from the version
  numbers alone when a changelog is available — the wave is set by what the
  release notes say, and the number only proposes it.
- **Release-train families**: libs versioned and released together —
  `pydantic` + `pydantic-settings`, `langfuse` + the `opentelemetry-*` packages
  it pulls, a lib and its `types-*` stubs (`toml` + `types-toml`). The family
  updates as a unit, classified by its riskiest member.
- **SDK ↔ server coupling**: the `langfuse` SDK major must match the Langfuse
  server image tag in `docker-compose.yml` (`langfuse:4` / `langfuse-worker:4`).
  A `langfuse` major bump is a Wave 3 item that also bumps both image tags, and
  its gate includes `make clean-langfuse && make run-langfuse` plus one real
  `make run` turn showing up as a trace.
- **Constraint-coupled groups**: a lib plus the packages that depend on it with
  a narrow range (e.g. `google-genai` capping `pydantic` or `httpx`). Python has
  no peer-dependency concept — the constraint
  is a real requirement, so the resolver refuses outright rather than warning:
  a `uv lock` that fails with "no solution found" is this case, and the error
  text names the capping package. The group updates as a unit, targeting the
  newest published **combination** that resolves — which may be an intermediate
  version rather than latest. When no combination improves on current, defer as
  **blocked upstream**, recording which dependent must release support before
  retrying. `uv tree --invert --package <lib>` shows who pulls a package and
  with which range — `--invert` takes no positional argument, the package goes
  in `--package`.
- **Supply-chain cooldown**: `exclude-newer = "7 days"` in `[tool.uv]` already
  enforces this — fresh releases are the main vector for supply-chain attacks,
  and the rolling window covers every resolution, transitives included. Nothing
  to pass per command.

  The two triage channels split cleanly, and that split is the point. **What you
  can take** — `uv tree --outdated` honours the window, so a lib whose only newer
  release is still inside it reads as up to date. Correct: there is no action to
  offer. **What you are exposed to** — `uv audit` queries OSV about the versions
  in `uv.lock`, not about what the resolver would pick, so a vulnerability is
  reported on its own schedule and names the fixing version even when the
  cooldown hides it.

  So an in-window release reaches you only through the audit, and only when it
  matters. That is the one case that overrides the cooldown — and the override
  belongs in `pyproject.toml`, not on the command line:

  ```toml
  # cryptography 50.0.0 fixes CVE-2026-69247 but was published inside the 7-day
  # cooldown above, so resolution would filter it out. Drop this entry once the
  # rolling window reaches 2026-08-07 and the global cutoff covers it.
  [tool.uv.exclude-newer-package]
  cryptography = "2026-08-07T00:00:00Z"
  ```

  `uv lock --exclude-newer-package '<lib>=<date>'` grants the same exemption for
  one invocation, which is enough to produce the lockfile and nothing more. CI
  and every student's `make install` re-derive the window from `pyproject.toml`, so a pin on an
  in-window version with no persisted entry fails outright — *"Because
  cryptography==50.0.0 was published after the exclude newer time and your
  project depends on cryptography==50.0.0, we can conclude that your project's
  requirements are unsatisfiable."* A green local `uv lock` does not protect you
  here; `uv lock --check` is what reproduces it.

  Give every entry the comment above — advisory, and the date the global window
  swallows it — because nothing expires it automatically and a stale exemption
  silently exempts that lib from the cooldown forever. Removing them is part of
  the next run's triage.

  The exemption does **not** extend to the named lib's own dependencies, so when
  the fix needs a fresh transitive too, give the transitive its own entry —
  otherwise the resolver silently settles for an older parent.
- **Yanked releases**: never target a yanked version, and treat a currently
  pinned version showing up as yanked in the audit as a vulnerability-grade
  reason to move.
- **Transitive vulnerabilities**: fix in escalation order — (1) bump the direct
  dependency that pulls the vulnerable package; (2) refresh the transitive
  in-range with `uv lock --upgrade-package <lib>` (lockfile-only, no new
  contract in `pyproject.toml`); (3) only when the patched version is outside
  some parent's range, pin it in `[tool.uv]` — `constraint-dependencies` to
  raise a floor that still fits every range, `override-dependencies` to break a
  parent's cap outright. Either is its own explicit item in the wave plan,
  flagged for removal once parents catch up; an override is a claim that the
  parent's cap is wrong, so it needs a line saying why it is safe here.
- **Health check**: flag deprecated or unmaintained packages — the adverse
  project statuses from the audit, plus `uv-secure uv.lock --max-age-days` to
  surface packages whose newest release is stale. Judge staleness by the
  package: a small, finished library releasing yearly is fine, a framework going
  quiet is not. Destination is defined in Health-check notes, step 4.

**Checkpoint**: show the wave plan to the user (table: lib, current → target,
wave, notes) and wait for approval before touching anything.

## 2. Waves 1–2 (patch, then minor)

Update each wave as a batch, then run the **gate**: derive it from the repo's CI
workflow (`.github/workflows/test.yml`) so it matches what must pass on a PR —
currently `make install`, `make lint-check` (ruff check + format check + mypy
`--strict`), and `make test`. Skip steps that need secrets or external infra and
state which ones you skipped.

Add to the gate, on top of CI:

- `uv lock --check` — asserts the lockfile matches `pyproject.toml`.
- Re-run `uv audit` after bumping, not just before.
- After a `google-genai` bump, one real `make run` turn with a tool call (needs
  `GEMINI_API_KEY`): the tests mock the model, so a changed function-calling
  payload only shows up against the live API.

Because `mypy --strict` runs in the gate, a lib bump can go red purely on
typing: a package that starts shipping `py.typed`, a stub package that tightens
signatures, or a `Protocol` that gained a member. That is a real failure, not
noise — treat it like any other.

A red gate stops the wave — isolate the offending lib, revert it, move it to
Wave 3, and re-run the gate.

## 3. Wave 3 (majors) — one at a time

For each major (or family):

1. Find the breaking changes in **primary sources, never from memory** (training
   data is stale for this): GitHub releases/CHANGELOG of the lib (`gh api` / web
   fetch), official migration guide. Many PyPI projects have no changelog on
   PyPI at all — the project URLs in `curl -s https://pypi.org/pypi/<lib>/json |
   jq .info.project_urls` point at the real one. If no reliable source is found,
   say so — an unverified bump is not a safe bump. When there are several
   majors, fan out the changelog research to parallel subagents on a
   smaller/faster model when available — instruct them to return the
   breaking-changes sections verbatim, not summaries. Impact analysis and effort
   judgment stay in the main session.
2. **Resolution check first**: `uv lock --dry-run` with the new pin before
   committing to the work. A green gate does not prove the lockfile resolves
   from scratch, and the resolver failing here names the capping dependency
   immediately, which is cheaper than discovering it after adapting the code.
3. **Impact analysis**: search the repo for actual usage of the changed APIs.
   "Breaking upstream" ≠ "breaking here" — if the code never touches the changed
   API, update without fear.
4. Estimate effort from real impact (files touched, adaptation size).
5. **Low effort** → update, adapt the code, run the gate. Inspect anything the
   gate touches: a change in the function declarations the tools send to
   Gemini, or in the span structure Langfuse receives, changes what the workshop
   exercises observe, and is a defer even when the code compiles and the tests
   pass.
6. **High effort** → defer: add to the report, do not update.

**Checkpoint**: before starting each major, show the impact summary (breaking
changes found, files affected, effort estimate) and wait for a go.

## 4. Deliverables

- **Diff**: leave changes uncommitted and show a summary — `pyproject.toml`,
  `uv.lock`, and any adapted code. Never commit/push/open PRs without explicit
  user instruction.
- **PR granularity** (when the user asks for PRs): one PR for waves 1–2
  combined. A major joins that PR if its adaptation is small; if it required
  roughly 200+ changed lines, it gets its own PR.
- **Deferred report**: for every deferred major, output a section with — lib and
  version jump, link to migration guide, breaking changes that impact this repo,
  affected files, effort estimate. For anything deferred as blocked upstream,
  name the capping dependency and the version of it that would unblock.
  Formatted to paste directly into a backlog card.
- **Health-check notes**: deprecated or unmaintained packages found during
  triage go in the diff summary — or into the deferred report when they coincide
  with a deferred major.
