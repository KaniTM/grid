# Codex Working Rules (Credit-Efficient, High-Quality)

## 0) Tool Choice Gate (Codex vs Browser ChatGPT)

Before starting any task, pick the best value tool that still gets the job done. if a task is too hard, suggest a better model and higher reasoning effort.

**Use Browser ChatGPT (not Codex) when:**

* The task is clarification, definitions, brainstorming, planning, or design discussion (no repo access needed).
* You need concept explanations (Freqtrade/FreqAI behavior, indicators, regime logic, backtest methodology).
* You need review/rewrites of text: docs, TODOs, acceptance criteria, prompt engineering, strategy spec writing.
* The task can be answered without reading/editing local files.

**Use Codex when:**

* The task requires editing code, creating/modifying files, running tests, or navigating the repo to implement changes.
* The task requires multi-file changes or verifying behavior by running local commands/tests.

**Codex behavior requirement:**

* If the task looks “Browser ChatGPT sufficient,” explicitly say:

  * **“This can be done in Browser ChatGPT to save credits”**
  * and provide the exact prompt I should paste there.

---

## 0A) Command Budget + Approval (prevent credit burn)

* Before running any command, propose the exact commands and label them:

  * **Quick** (expected <30s) vs **Heavy** (minutes+).
* Run **Quick** commands automatically when needed; ask approval before **Heavy** commands.
* Batch commands (e.g., one `ruff` run + one `pytest` run). Avoid rerunning the same checks repeatedly unless necessary.
* Prefer targeted checks first:

  * `ruff <touched_paths>`
  * `pytest -q <relevant_tests>`
  * Run full suite only if targeted fails or task explicitly requires it.

---

## 0C) Artifacts + Reproducibility Contract (avoid reruns)

For walk-forward / sims / comparisons:

* Write outputs to deterministic paths, e.g.:

  * `user_data/artifacts/<task_name>/<run_id>/...`
* Record the exact run parameters in a small `run_meta.json` alongside artifacts:

  * seed, timerange, pairlist, mode config, any important flags.
* Print only key artifact paths + summary metrics (no huge logs).

---

## 0D) Secrets / Safety

* Never print, log, or commit secrets (API keys, tokens).
* If a file or command output appears to contain secrets, stop and ask how to handle it.

---

## 0E) Stop Early if Mis-scoped

* If you realize the task requires repo-wide scanning, raw data scanning, or vendor edits:

  * stop immediately and ask for explicit permission instead of continuing.

---

## 0F) “Review Like a PR” After Changes

* After producing a diff, do a quick self-review focusing only on:

  * correctness, determinism/leakage risk, performance, and safety.
* No style nits unless they affect correctness.

---

## 0G) Config Guardrail (avoid accidental expensive settings)

* Use repo config (`.codex/config.toml`) to set safe defaults for model + reasoning effort.
* If using Codex CLI, prefer “cheap vs deep” profiles so switching is intentional.
* Revert to the default “cheap” setting after completing a “deep” task.

---

## 1) Output & Communication (keep it short, but useful)

* Keep output minimal: only **Success/Fail** + key reason(s).
* For backtest / learning / walk-forward tasks: output only the results needed for next steps:

  * key metrics, **comparison deltas vs baseline (when relevant)**, and key artifact paths.
    and no log polling + log output in window, give CLI command so I can check when I want.
* Max 10 bullets per response.
* No explanations unless I explicitly ask. If something is critical, give a 1-line justification.

---

## 2) Scope Control (avoid expensive repo scanning)

* Do not scan the full repo without my explicit approval.
* Do not open/read raw data files unless the task truly needs it and I confirm. do not read Freqtrade/FreqAI files even if I ask for full repo read. only  files we created are important for our work.
* For large downloads / raw data pulls: provide exact commands for me to run locally (don’t do heavy pulls yourself unless I ask).

---

## 3) Allowed Files & Safety Boundaries

* Do not modify vendor code (Freqtrade/FreqAI/core framework files) without my consent.

  * Only modify my strategy / my modules / my scripts by default.
* Do not edit config files unless the task explicitly requires it and you ask first.
* Do not commit or push to GitHub unless I say so. you can suggest git commands for commit and push if you feel it's a good time to do it.

---

## 4) Work Style (plan → execute in small steps)

* At the start of each task, provide a micro-plan (≤5 bullets) and list the exact files you will touch.
* Prefer two-phase execution:

  1. Identify minimal changes + file list (no code yet).
  2. Implement changes file-by-file, smallest viable patch first.
* Use diff-first output (unified diff) when possible, or clearly list modified files and key edits.

---

## 5) Quality Bar (must be correct, not just “done”)

* Add defensive checks + clear log messages where runtime failure is likely:

  * missing columns, NaNs, empty dataframes, exchange/API errors, unexpected schema.
* Must pass: `ruff` and `pytest -q`.

  * If failing, fix before final output.
* Include a short checklist:

  * what changed (1–5 items),
  * which tests/commands were run (or should be run).

---

## 6) Avoid Churn / Risky Refactors

* No sweeping refactors.
* Do not change unrelated formatting.
* If a refactor is truly needed, ask first with a short reason and wait for my decision.

---

## 7) Ambiguity Handling (avoid long back-and-forth, avoid wrong guesses)

* If something is ambiguous:

  * ask at most 2 clarifying questions,
  * otherwise proceed with the best assumption and explicitly state the assumption.

---

## 8) Backtest / Simulation Correctness (deterministic + no leakage)

* Keep backtests/sim deterministic:

  * fixed random seeds,
  * fixed time windows,
  * explicit resampling parameters.
* Avoid time-dependent calls in backtests:

  * do not use `datetime.now()`; pass timestamps as inputs.
* No future-looking features / no data leakage:

  * indicators/features must use past data only (shift/rolling correctly).

---

## 9) Performance Expectations (don’t create slow backtests)

* Prefer vectorized pandas operations.
* Avoid `.apply()` inside loops and per-row Python loops unless unavoidable.

  * If you must loop, state the complexity impact briefly.

---

## 10) Cost Awareness & Model Recommendation

* When a task looks complex (multi-file logic, subtle bugs, leakage risk, router design):

  * recommend upgrading model/reasoning effort briefly.
* Default assumption for routine tasks:

  * **GPT-5.1-Codex-Mini + Medium effort** is fine.
* When it saves credits/time, suggest I run non-critical commands manually (big downloads, long walk-forwards, heavy sims).

---