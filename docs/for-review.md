# Что проверить (для внешней проверки)

Коммит: `58957ba` — на нём собран файл. Хеши ниже описывают ДЕРЕВО этого коммита: если присланный архив совпадает по ним, значит он не из кеша. Сам файл добавлен следующим коммитом (иначе он называл бы коммит, которого ещё нет), поэтому точную ревизию берите так: `git log -1 --format=%H -- docs/for-review.md`.

## Файлы

| Файл | Байт | sha256 |
|---|---|---|
| `README.md` | 28556 | `ac4e43f3de576db1…` |
| `NOTICE.md` | 4207 | `992109d48201ad43…` |
| `INSTALL.md` | 20900 | `350522a4912e848a…` |
| `agent-description.md` | 1997 | `022358b16d3becb7…` |
| `CONTRIBUTING.md` | 8793 | `5050096fe1dab47b…` |
| `SECURITY.md` | 6167 | `94802b00787afbac…` |
| `FUNDAMENTALS.md` | 6128 | `08b01dd184674590…` |
| `KEYS.md` | 7120 | `c43bdb8c88435422…` |
| `scripts/validate_agents.py` | 41551 | `9655bb98b0304ba9…` |
| `scripts/build_profiles.py` | 10769 | `f4047bd381824c8e…` |
| `scripts/check_dist.py` | 8032 | `76d836c895bb3efc…` |
| `tests/test_scripts.py` | 41826 | `4e4fcf71b8e07cf7…` |
| `.github/workflows/validate.yml` | 1459 | `533b460af7961239…` |
| `profiles/README.md` | 7232 | `c8edaf24371bcb67…` |

## Ключевые числа

- агентов **19** (`agents/*.md`)
- навыков **161** (`skills/**/SKILL.md`) в 14 наборах
- PM-методик 40 (`skills/pm-skills/*/SKILL.md`)
- файлов Company Brain 8 (`company-brain/*.md`)
- в собранных дистрибутивах: профилей 19, навыков 146 (analytics, avito, content, creative…)
- тестов: 62 (`python3 tests/test_scripts.py`)

## Навыки по наборам

| Набор | SKILL.md |
|---|---|
| `article-distribution` | 1 |
| `claude-skills` | 7 |
| `cowork-roles` | 66 |
| `geo-visibility` | 1 |
| `github-repo-research` | 1 |
| `humblytics-marketing` | 12 |
| `open-seo` | 1 |
| `pm-skills` | 40 |
| `searchfit-seo` | 11 |
| `social-media-skills` | 17 |
| `timesfm-marketing` | 1 |
| `vector-github-design` | 1 |
| `vector-work` | 1 |
| `yandex-wordstat` | 1 |

## Что сверить отдельно

- Арифметика README: сторонних навыков 154 + собственных 7 = 161 (в README заявлено 161)
- Сторонних наборов: 7 (по NOTICE), собственных навыков: 7 — в таблице README они идут одной строкой «собственные», а не поимённо.
- Разбивка по наборам выше — тот блок, который README печатает, а CI сверяет только по сумме: расхождение внутри набора ищется здесь.

## Как проверить, не запуская репозиторий

- Хеши и числа выше сверяются с архивом; строка с коммитом сверяется с `git log`.
- `python3 scripts/validate_agents.py` — SOUL-манифесты, числа README, диаграмма.
- `python3 tests/test_scripts.py` — сборка профилей и валидатор.
- `python3 scripts/build_profiles.py --clean && python3 scripts/check_dist.py` — форма дистрибутивов (манифест, симлинки, следы секретов).

Все три проверки прогнаны локально на указанном коммите: ошибок 0.