# Что проверить (для внешней проверки)

Хеши ниже описывают дерево той ревизии, в которой лежит сам этот файл (он генерируется из того же дерева, что и коммитится, — поэтому хеш HEAD на момент сборки здесь называть нельзя: он на один коммит позади). Ревизию получить так: `git log -1 --format=%H -- docs/for-review.md`. Если присланный архив совпадает по хешам, он из этой ревизии, а не из кеша.

## Файлы

| Файл | Байт | sha256 |
|---|---|---|
| `README.md` | 30257 | `8ea63f58c6937f9e…` |
| `NOTICE.md` | 5549 | `9c3fa33994e8e9b2…` |
| `INSTALL.md` | 20936 | `0d284fd1bfead3a0…` |
| `agent-description.md` | 2001 | `e542339142b40642…` |
| `CONTRIBUTING.md` | 10351 | `f7c0e43c076a0cd7…` |
| `SECURITY.md` | 6167 | `94802b00787afbac…` |
| `FUNDAMENTALS.md` | 6128 | `08b01dd184674590…` |
| `KEYS.md` | 7120 | `c43bdb8c88435422…` |
| `scripts/validate_agents.py` | 60663 | `7b1a911dd302094a…` |
| `scripts/build_profiles.py` | 10769 | `f4047bd381824c8e…` |
| `scripts/check_dist.py` | 8032 | `76d836c895bb3efc…` |
| `tests/test_scripts.py` | 84088 | `0c94f55ad6d03d8e…` |
| `.github/workflows/validate.yml` | 2362 | `cba6b7735907f648…` |
| `profiles/README.md` | 7232 | `c8edaf24371bcb67…` |

## Ключевые числа

- агентов **19** (`agents/*.md`)
- навыков **165** (`skills/**/SKILL.md`) в 18 наборах
- PM-методик 40 (`skills/pm-skills/*/SKILL.md`)
- файлов Company Brain 8 (`company-brain/*.md`)
- в собранных дистрибутивах: профилей 19, навыков 151 (analytics, avito, content, creative…)
- тестов: 95 (`python3 tests/test_scripts.py`)

## Навыки по наборам

| Набор | SKILL.md |
|---|---|
| `article-distribution` | 1 |
| `claude-skills` | 7 |
| `community-post-generator` | 1 |
| `content-calendar` | 1 |
| `content-repurposer` | 1 |
| `cowork-roles` | 66 |
| `geo-visibility` | 1 |
| `github-repo-research` | 1 |
| `humblytics-marketing` | 12 |
| `open-seo` | 1 |
| `pm-skills` | 40 |
| `publish-pipeline` | 1 |
| `searchfit-seo` | 11 |
| `social-media-skills` | 17 |
| `timesfm-marketing` | 1 |
| `vector-github-design` | 1 |
| `vector-work` | 1 |
| `yandex-wordstat` | 1 |

## Что сверить отдельно

- Арифметика README: сторонних навыков 158 + собственных 7 = 165 (в README заявлено 165)
- Сторонних наборов: 11 (по NOTICE), собственных навыков: 7 — в таблице README собственные названы поимённо, и валидатор требует, чтобы каждый каталог `skills/` был назван хотя бы в одном из двух списков.
- Разбивка по наборам выше сверяется валидатором построчно (таблица README → дерево), а не только по сумме: перестановка между наборами валит CI.

## Как проверить, не запуская репозиторий

- `sha256sum -c docs/SHA256SUMS` — сверка присланных файлов с хешами из репозитория (таблица выше усечена до 16 символов и для проверки не годится).
- Хеши и числа выше сверяются с архивом; строка с коммитом сверяется с `git log`.

Проверки, которые прогоняет CI (и которые можно повторить локально):

- `python3 scripts/validate_agents.py` — SOUL-манифесты, числа README и NOTICE, лицензии вендоренных наборов, диаграмма.
- `python3 tests/test_scripts.py` — сборка профилей и валидатор.
- `python3 scripts/build_profiles.py --clean && python3 scripts/check_dist.py` — форма дистрибутивов (манифест, симлинки, следы секретов).
- `python3 scripts/build_for_review.py --check` — этот файл воспроизводится из дерева.

Прогон CI: https://github.com/Osmosy/vector-marketing/actions/workflows/validate.yml — прогон ревизии, в которой лежит этот файл, первый в списке (шаги и их вывод видны там же).