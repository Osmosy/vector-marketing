---
name: github-repo-research
description: Use when the user asks you to look at, analyze, summarize, or research a GitHub repository — its purpose, architecture, code structure, dependencies, license, or current state. Triggers on phrases like "посмотри <url>", "what does this repo do", "summarize github.com/X/Y", "изучи репо", "what's in this project".
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Github, Repos, Code-Analysis, Architecture, Reverse-Engineering]
    related_skills: [arxiv, research-paper-writing, ocr-and-documents, obsidian]
---

# GitHub Repository Research

Read-only research workflow for any GitHub repository: extract metadata, code structure, dependencies, license terms, and architecture — then synthesize a substance-first report. No code modifications, no PRs, no assumptions.

## When to Use

- "посмотри https://github.com/X/Y" / "что это за репо" / "изучи репо"
- "what's in github.com/X/Y" / "summarize this repo"
- User wants architecture overview, license terms, dependency review, or capability audit
- Comparing a repo to alternatives ("how does X differ from Y")
- Vetting a model/checkpoint release (license, gated weights, sample code, paper)

## When NOT to Use

- Issue triage, PR review, code editing → use github-pr-workflow / github-issues
- Cloning to build/run the code → use spike or executing-plans
- Security audit of a known dependency → use code-review
- The repo has no clear public surface (private, empty, just a redirect)

## Core Principle

Substance over press-release. The user wants what the code DOES and what the LICENSE ALLOWS — not the README's marketing. Always verify against source. Treat benchmarks and benchmarks images as claims, not facts.

## Workflow (Phase Order)

### Phase 1 — Read-Only State Check (in parallel)

Fire independent calls together. The runtime executes them concurrently.

```
1a. Repo metadata via GitHub REST API (no auth required for public repos):
    curl -sS -H "Accept: application/vnd.github+json" \
         -H "X-GitHub-Api-Version: 2022-11-28" \
         https://api.github.com/repos/{owner}/{repo}
    Extract: name, description, stars, forks, watchers, open_issues,
             default_branch, language, size_kb, created_at, pushed_at,
             updated_at, license.spdx_id, topics, archived, disabled.

1b. Root contents via API (avoids cloning when not needed):
    curl -sS https://api.github.com/repos/{owner}/{repo}/contents/
    Note file sizes + types.

1c. README.md via raw URL:
    curl -sS https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md
```

Save everything to `/tmp/{repo}-scan/` so you can re-process without re-fetching.

If `gh` is available: `gh repo view {owner}/{repo}` is faster for metadata + description. Always check `which gh` first.

### Phase 2 — Clone (only if you need code)

```
git clone --depth=1 https://github.com/{owner}/{repo}.git /tmp/{repo}-repo
```

`--depth=1` saves bandwidth and is fine for research (no history needed).
Use the API's `default_branch` value, not assumed `main`.

### Phase 3 — Tree Mapping

```
cd /tmp/{repo}-repo
find . -path ./.git -prune -o -type d -print | sort
find . -path ./.git -prune -o -type f -print | sort
```

Then `wc -l` on source files to spot the biggest modules — those are where the real logic lives.

### Phase 4 — Targeted Reads (in parallel)

Read the smallest set of files that answer the key questions:

| Question | Files |
|----------|-------|
| What does it do? | README.md, top-level `__init__.py` / `main.go` / `lib.rs` |
| Architecture? | `docs/architecture*.md`, main model/class file |
| Dependencies? | `pyproject.toml`, `package.json`, `Cargo.toml`, `requirements.txt`, `go.mod` |
| License? | `LICENSE` / `LICENSE.md` + any `model_licenses/`, `weights_*` files |
| How do I run it? | `run_inference.py`, `Makefile`, `scripts/`, CLI entry point |
| Safety/policy? | `docs/safety.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` |

Read multiple files in parallel — `read_file` calls in one tool block run concurrently. Don't sequentially ask for one file at a time.

### Phase 5 — Synthesize Report

Plain text for terminal output (no markdown headers in CLI mode — see system prompt). Use this structure:

```
REPO META        — stars/forks/license/default branch/pushed date
WHAT IT IS       — 1-2 sentence essence
ARCHITECTURE     — components + how they connect (if code repo)
KEY MODULES      — file → purpose mapping, with line counts
ENTRY POINT      — how to invoke / how to import
DEPENDENCIES     — pinned versions, unusual requirements
LICENSE          — code license vs weights/data license (often DIFFERENT)
BENCHMARKS       — claims only, mark as unverified unless you ran them
RISKS / GOTCHAS  — gated weights, non-commercial clauses, breaking changes
INTERESTING      — design choices worth highlighting
TL;DR            — one paragraph
```

### Phase 6 — Cleanup

```
rm -rf /tmp/{repo}-scan /tmp/{repo}-repo
```

If you cloned into a directory you've `cd`'d into and it was deleted, your shell may show "pwd: error retrieving current directory". This is cosmetic — `cd /` or open a new shell.

## API Quick Reference

| Endpoint | Purpose |
|----------|---------|
| `/repos/{owner}/{repo}` | metadata |
| `/repos/{owner}/{repo}/contents/{path}` | list directory |
| `/repos/{owner}/{repo}/branches` | list branches |
| `/repos/{owner}/{repo}/releases` | releases with notes |
| `/repos/{owner}/{repo}/tags` | git tags |
| `/repos/{owner}/{repo}/license` | license content |
| `raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}` | raw file |

Rate limit: 60 req/hour unauthenticated. For multi-repo scans, set `GITHUB_TOKEN` env var and pass it via a Python `urllib.request.Request` — never put tokens in `curl -H` shell history (see hermes-tooling-quirks skill).

When unauth, budget ~10–12 repos per hour if you fire the parallel Phase-1 trio (metadata + contents + branches + README = 4 calls each). If you hit a 403 secondary rate limit, wait the `retry-after` header value (usually 60s).

## Token Safety (CRITICAL)

Never run `curl -H "Authorization: Bearer ghp_***"` in shell — token leaks into `.bash_history`, scrollback, core dumps. Use:

```python
import urllib.request, os
req = urllib.request.Request(
    "https://api.github.com/repos/X/Y",
    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
             "Accept": "application/vnd.github+json"})
print(urllib.request.urlopen(req).read().decode())
```

Or `execute_code` (Hermes Python runtime — no shell history).

## Common Pitfalls

0. **Bash-quoting breaks `curl | python3 -c "..."`.** Backslash-escapes inside nested quotes produce SyntaxError when python parses the pipe target. Two fixes: (a) save JSON to a file first, then `python3 -c 'import json; ...'`; (b) write the inline script to a file via `write_file`, then `python3 script.py < input.json`. Don't keep trying to escape — not worth the turns.

0a. **Unauth rate limit on multi-repo scans.** 60 req/hour is plenty for ONE repo (3-4 Phase-1 calls) but burns fast if user asks "compare these 5 repos". Either: (1) batch with a single composite query, (2) auth with GITHUB_TOKEN for 5000 req/hour via the urllib pattern below, or (3) state the constraint to the user before starting.

1. **Trusting README claims.** README is marketing. Architecture file and actual `Config` dataclass are facts. Always cross-check.

2. **Confusing code license vs weights license.** Many model repos have Apache-2.0 code + custom non-commercial weights license (e.g., Ideogram 4). Read BOTH and quote the relevant restrictions.

3. **Skipping size/dimension checks.** A 9.3B model with 34 transformer layers and emb_dim 4608 tells you more than "state-of-the-art". Read the actual `Config` dataclass.

4. **Forgetting to verify gated weights.** README says "open weights"? Check the HuggingFace repo. Gated repos need accept-the-license before download — `hf_hub_download` returns 404 without auth.

5. **Reading one file at a time.** When you need README + pyproject + main module + license, batch them into one tool block. Sequential reads waste turns.

6. **Ignoring `pushed_at` vs `updated_at`.** `pushed_at` = last git push. `updated_at` includes GitHub UI changes (description edits, topic changes). For "is this maintained?", trust `pushed_at`.

7. **Markdown-heavy output in CLI.** System prompt: terminal is plain text. Use `═`/`─` rules and indents, not `#` headers and `|table|` rows — they render but look ugly.

8. **Putting tokens in `curl -H`.** See "Token Safety" above. Bash history is forever.

9. **Not cleaning `/tmp`.** Cloned repos accumulate. Always `rm -rf` after synthesis. If your shell's CWD was inside the deleted dir, subsequent commands show `pwd: error retrieving current directory` — cosmetic, `cd /` fixes it.

10. **Treating benchmark images as facts.** `assets/benchmarks/foo.png` is a claim. To verify, you'd need to run the benchmark yourself. Mark as "according to README" in the report.

11. **Mixing code license and weights/data license in one sentence.** Model repos commonly have Apache-2.0 code + custom non-commercial weights license (Ideogram 4, Llama Community License variants). Always quote BOTH separately and flag the asymmetry. The user often assumes "open-source repo = everything is open-source" — make it explicit which parts are which.

10. **Treating benchmark images as facts.** `assets/benchmarks/foo.png` is a claim. To verify, you'd need to run the benchmark yourself. Mark as "according to README" in the report.

11. **Conflating the skill with its first example.** This skill was first used on a text-to-image model repo (Ideogram 4). It's a generic GitHub-repo-analysis workflow — equally applicable to compilers, databases, web frameworks, LLM releases. When the user challenges the category placement ("why research if it's about design?"), the answer is: the skill's name and trigger conditions describe the WORKFLOW class, not the example domain. If you actually need a skill specifically about text-to-image model selection / design / creative use, that's a different skill (e.g. `creative/image-model-selection` or `mlops/inference/model-comparison`). Don't argue about category — point the user at the skill that does match their concern.

## Verification Checklist

- [ ] Repo metadata fetched via API (not just README guess)
- [ ] At least 3 source files actually read (not just listed)
- [ ] License terms quoted, not paraphrased (especially non-commercial / no-distillation clauses)
- [ ] Dependencies listed with versions from `pyproject.toml` / equivalent
- [ ] If model repo: parameter count, architecture depth, text encoder, sampler, CFG scheme
- [ ] `/tmp` cleaned after synthesis
- [ ] Report is substance-first: architecture + license + risks before marketing claims
- [ ] Output is plain text (no markdown headers in CLI mode)

## Output Format (Context-Dependent)

- **CLI / terminal** (default in Hermes CLI mode): plain text, `─`/`═` rules, indented bullets. No `#` headers, no `|table|` rows — they render but look like markdown accidents.
- **Telegram / Discord / messaging platforms**: markdown is fine — the platform renders it. Tables, headers, code fences all work.
- **Obsidian / file artifact**: full markdown with headings, tables, and code blocks.

The system prompt of the active session usually tells you which. When in doubt: shortest, most readable form for the medium.

## Output Template (Terminal)

```
──────────────────────────────────────────────
Итог по https://github.com/{owner}/{repo}
──────────────────────────────────────────────

РЕПО МЕТА
   Stars / Forks / License / Default branch / Pushed

ЧТО ЭТО
   One-paragraph essence.

АРХИТЕКТУРА / МОДЕЛЬ
   Bullet list of components with file refs.

КЛЮЧЕВЫЕ МОДУЛИ
   file.py (N строк) — purpose
   file2.py (M строк) — purpose

ЗАПУСК
   Exact CLI / API entry point.

ЗАВИСИМОСТИ
   lib >= X.Y, ...

ЛИЦЕНЗИЯ
   Код: ...
   Веса/данные: ...
   Ключевые ограничения: ...

БЕНЧМАРКИ
   Claims only, mark unverified.

РИСКИ / НА ЧТО СМОТРЕТЬ
   Numbered list.

ИНТЕРЕСНОЕ
   Design choices worth noting.

──────────────────────────────────────────────
TL;DR: one-sentence summary.
──────────────────────────────────────────────
```

## Related Skills

- `arxiv` — when the repo accompanies a paper (cite the paper too)
- `ocr-and-documents` — if you need to read PDFs in the repo (papers, design docs)
- `obsidian` — for saving the report to Obsidian vault
- `research-paper-writing` — if the report feeds into a paper/literature review
- `github-pr-workflow` — when research leads to actually opening a PR
