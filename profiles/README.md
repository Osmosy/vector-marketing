# Настройка профилей Hermes

Профиль агента не собирается вручную — он генерируется из репозитория:

```bash
python3 scripts/build_profiles.py --clean          # → dist/<agent>/ (19 профилей)
hermes profile install ./dist/<agent> --alias      # поставить
hermes profile update <agent>                      # обновить после правок в репо
```

Что попадает в `dist/<agent>/`:

| Файл | Источник |
|------|----------|
| `SOUL.md` | `agents/<agent>.md` + блок про общий контекст |
| `brain/*.md` | `company-brain/` (7 файлов) |
| `skills/…` | профильные навыки, на которые ссылается агент |
| `distribution.yaml` | манифест дистрибутива Hermes (name, version, env_requires) |
| `.gitignore` | защита рабочего слоя и `.env` |

Установщик `hermes profile install` сам вырезает `auth.json`, `.env`, `memories/`, `sessions/`,
`logs/` и прочий user-owned слой, даже если он случайно попал в дистрибутив.

## Модель и ключи

Профиль не несёт `config.yaml`: модель и провайдер каждый ставит под себя, чтобы обновление
дистрибутива не сбрасывало локальные настройки. Ключи задаются в `.env` профиля
(установщик создаёт `.env.EXAMPLE` со списком требуемых переменных).

```bash
cp ~/.hermes/profiles/<agent>/.env.EXAMPLE ~/.hermes/profiles/<agent>/.env
# вписать ключи модели
```

## Связка агентов

`orchestrator` (Osmosy) — точка входа: он декомпозирует задачу и делегирует профильным
агентам через `delegate_task`. Остальные профили запускаются и напрямую:

```bash
hermes -p orchestrator --skills vector-work "Клиент: интернет-магазин. Задача: +30% заявок."
hermes -p seo "Семантика для клиента X: кластеры + интент"
```

Между профилями не наследуется конфиг — это осознанная изоляция Hermes. Общий контекст
передаётся данными: `brain/` внутри каждого профиля и `company-brain/` в репозитории.

## Сводная таблица агентов

| Профиль | Блок | Ключевые skills |
|---------|------|----------------|
| orchestrator | Оркестрация | strategy-red-team, vector-work, delegate_task |
| market-research | Стратегия | market-sizing, beachhead-segment, ideal-customer-profile, competitor-analysis |
| analytics | Стратегия | north-star-metric, ab-test-analysis, yandex-marketing-apis-ru, MPSTATS |
| performance | Привлечение | growth-loops, pre-mortem, gtm-motions, campaign-plan |
| yandex-direct | Привлечение | yandex-marketing-apis-ru, yandex-wordstat |
| seo | Привлечение | seo-audit, open-seo, evidence-based-seo, yandex-wordstat |
| vk-ads | Привлечение | social-media-research |
| avito | Привлечение | avito-api, yandex-wordstat |
| marketplaces | Привлечение | ozon-seller-api, wildberries-api, MPSTATS |
| landing-cro | Упаковка | page-cro, ab-test-analysis, privacy-policy (152-ФЗ) |
| content | Упаковка | product-name, evidence-based-seo, humanizer |
| smm-telegram | Упаковка | content-creation, email-sequence |
| creative | Упаковка | html, vector-github-design |
| presentation | Упаковка | powerpoint, document-deliverables |
| crm-retention | Удержание | cohort-analysis, email-sequence |
| reputation | Удержание | maps, DaData, ru-text |
| sales | Операции | account-research, call-prep, pipeline-review, forecast |
| support | Операции | ticket-triage, draft-response, kb-article |
| ops | Операции | task-management, capacity-plan, vendor-review, stakeholder-map |

Актуальный состав — `agents/*.md`; таблица проверяется CI-скриптом
`scripts/validate_agents.py` (расхождение с `agents/` валит сборку).
