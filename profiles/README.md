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
| `scripts/…` | вспомогательные скрипты навыка, если они есть у апстрима (например, `nap_checker.py` у local-seo-manager) |
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

| Профиль | Блок | Ключевые skills (в дистрибутиве) |
|---------|------|--------------------------------|
| orchestrator | Оркестрация | strategy-red-team, article-distribution, geo-visibility, vector-work |
| market-research | Стратегия | yandex-wordstat, geo-visibility, market-sizing, swot-analysis, pestle-analysis, porters-five-forces, user-personas, ideal-customer-profile, customer-journey-map, competitor-analysis, gtm-strategy, lean-canvas, business-model, competitive-battlecard, competitive-brief (27 из набора pm-skills) |
| analytics | Стратегия | geo-visibility, north-star-metric, ab-test-analysis, revenue-attributor, analytics-dashboard, post-scorer, performance-report |
| performance | Привлечение | growth-loops, pre-mortem, gtm-motions, gtm-strategy, marketing-strategist, ad-expert, campaign-plan |
| yandex-direct | Привлечение | yandex-wordstat (семантика по спросу); внешние: yandex-direct, yandex-marketing-apis-ru |
| seo | Привлечение | yandex-wordstat, article-distribution, geo-visibility, ai-visibility, technical-seo, on-page-seo, keyword-clustering, internal-linking, schema-markup, broken-links, content-strategy, seo-audit, seo-strategist, content-translation, local-seo-manager |
| vk-ads | Привлечение | **заготовка** — внешние: social-media-research, yandex-marketing-apis-ru |
| avito | Привлечение | yandex-wordstat (частотные формулировки и гео); внешние: avito-api |
| marketplaces | Привлечение | pricing-strategy (юнит-экономика МП); внешние: ozon-seller-api, wildberries-api, MPSTATS |
| landing-cro | Упаковка | page-cro, cro-optimizer, heatmap-analyst, funnel-reporter, ab-test-analysis, ab-test-generator, privacy-policy, shipping-artifacts, intended-vs-implemented |
| content | Упаковка | yandex-wordstat, article-distribution, product-name, copywriting, content-brief, value-prop-statements, brand-review, draft-content |
| smm-telegram | Упаковка | article-distribution, linkedin-profile, linkedin-content, linkedin-engagement, linkedin-strategy, linkedin-analytics, linkedin-skills, voice-builder, post-writer, hook-generator, content-matrix, newsletter-voice, post-formatter, quote-post, pinned-comment, niche-research, profile-optimizer, post-scorer, content-creation (25 всего) |
| creative | Упаковка | gemini-carousel, gemini-infographic, graphic-designer, youtube-thumbnail, reels-scripting |
| presentation | Упаковка | **заготовка** — внешние: powerpoint, document-deliverables |
| crm-retention | Удержание | cohort-analysis, email-sequence, email-sequences |
| reputation | Удержание | article-distribution (посевы и упоминания); внешние: maps, DaData, ru-text |
| sales | Операции | account-research, call-prep, pipeline-review, forecast, draft-outreach, call-summary, create-an-asset, summarize-meeting, competitive-intelligence, daily-briefing |
| support | Операции | ticket-triage, draft-response, kb-article, customer-research, customer-escalation |
| ops | Операции | task-management, capacity-plan, vendor-review, stakeholder-map, draft-nda, status-report, start, update, process-doc, runbook, risk-assessment, change-request, compliance-tracking, process-optimization |

**Заготовка** — профиль без навыков репозитория: `vk-ads`, `presentation`. Роль и SOUL описаны, но всё, на что они опираются, — внешние
зависимости (см. [INSTALL.md](../INSTALL.md#внешние-зависимости-профиля)). Профиль поставится
и запустится, но работать ему нечем: **разработаем позже**. Исключение — `marketplaces`: 1
навык репозитория (`pricing-strategy`), поэтому он в статусе «работает», фактически тоже почти пустой.

Актуальный состав — `agents/*.md`; таблица проверяется CI-скриптом
`scripts/validate_agents.py` (расхождение с `agents/` валит сборку).
