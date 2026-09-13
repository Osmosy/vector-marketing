<div align="center">

<img src="assets/vector-logo.png" alt="Vector Marketing" width="200"/>

# Vector Marketing

[![Architecture: live](https://img.shields.io/badge/Architecture-live_diagram-4f8ff7.svg)](https://osmosy.github.io/vector-marketing/docs/vector-marketing.architecture.html)

**AI-маркетинговое агентство на базе Hermes Agent — 19 профильных агентов под управлением Osmosy (CMO-оркестратор)**

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://github.com/NousResearch/hermes-agent)
[![Ecosystem: Vector](https://img.shields.io/badge/Ecosystem-Vector-blue.svg)](https://osmosy.github.io/)
[![Agents: 19](https://img.shields.io/badge/Agents-19-green.svg)](#агенты)
[![Company Brain](https://img.shields.io/badge/Company-Brain-7%20files-purple.svg)](#company-brain)
[![Framework](https://img.shields.io/badge/Framework-Context%E2%86%92Harness%E2%86%92Loop-orange.svg)](FUNDAMENTALS.md)

</div>

---

Маркетинговое агентство на базе Hermes Agent. 19 профильных AI-специалистов под управлением Osmosy (Hermes-оркестратор).

## Архитектура

```
Клиент → Osmosy (CMO-оркестратор)
              ├── СТРАТЕГИЯ: market-research, analytics
              ├── ПРИВЛЕЧЕНИЕ: performance, yandex-direct, seo, vk-ads, avito, marketplaces
              ├── УПАКОВКА: landing-cro, content, smm-telegram, creative, presentation
              ├── УДЕРЖАНИЕ: crm-retention, reputation
              └── ОПЕРАЦИИ: sales, support, ops
```

19 = 18 профильных агентов + `orchestrator` (Osmosy, CMO-оркестратор).

## Как это работает

1. Клиент ставит бизнес-задачу
2. Osmosy (Hermes) декомпозирует и делегирует профильным агентам
3. Каждый агент работает в своём профиле Hermes со своими skills, MCP-инструментами и правилами
4. Osmosy собирает результаты, проверяет противоречия, формирует единый вывод
5. Человек одобряет все внешние действия (публикация, отправка, бюджет)
6. Клиент получает готовый результат: стратегию, отчёт, кампанию, презентацию или документ

## Три слоя (Context → Harness → Loop)

| Слой | Что | Где живёт |
|------|-----|-----------|
| **Context** | Что модель видит в запуске | `company-brain/` + research + бриф |
| **Harness** | Что позволяет агенту действовать | `agents/*.md` + Hermes profile + skills + tools |
| **Loop** | Draft → check → retry | Anti-slop, handoff protocol, cron |

Подробнее: [FUNDAMENTALS.md](FUNDAMENTALS.md)

## Company Brain

Общий контекст для всех агентов. **Это реальный ров — ценность в контексте, а не в ботах.** Заполните под свой бизнес.
Свой рабочий слой держите в `company-brain/local/` — он исключён из git (см. `.gitignore`).

| Файл | Что содержит |
|------|-------------|
| `brand-voice.md` | Голос бренда, запрещённые формулировки, тон по каналам |
| `anti-slop-rules.md` | Чеклист quality gate для каждого драфта |
| `strategy.md` | Миссия, цели, ICP, конкурентное преимущество, каналы |
| `past-campaigns.md` | Журнал прошлых кампаний: что сработало, что нет, уроки |
| `offers-positioning.md` | Офферы, прайс, УТП, позиционирование |
| `channels-geo.md` | Канальный приоритет, гео, GEO (генеративные движки) |
| `media-list.md` | Медиа-лист для PR, Telegram-каналы, подкасты |

## Агенты

| Агент | Блок | Роль |
|-------|------|------|
| `orchestrator` | Оркестрация | CMO: декомпозиция, делегирование, сборка, приоритеты |
| `market-research` | Стратегия | Рынок, ЦА, конкуренты, позиционирование, JTBD |
| `analytics` | Стратегия | Метрики, воронки, ROMI, аномалии, дашборды |
| `performance` | Привлечение | Канальная стратегия, медиаплан, бюджетирование, тесты |
| `yandex-direct` | Привлечение | Директ: семантика, минус-слова, ставки, аудит |
| `seo` | Привлечение | SEO + AEO + GEO (ChatGPT/Perplexity) + Local SEO |
| `vk-ads` | Привлечение | VK Реклама: аудитории, пиксель, лид-формы, ретаргетинг |
| `avito` | Привлечение | Авито: объявления, SEO, продвижение, лиды |
| `marketplaces` | Привлечение | Ozon, WB, Яндекс Маркет: карточки, SEO, юнит-экономика |
| `landing-cro` | Упаковка | Лендинги, первые экраны, формы, CTA, A/B-гипотезы |
| `content` | Упаковка | Статьи, SEO-тексты, контент-планы, tone of voice |
| `smm-telegram` | Упаковка | Telegram/SMM, рубрики, посевы, контент-воронки |
| `creative` | Упаковка | Креативы, баннеры, AI-промпты, сториборды |
| `presentation` | Упаковка | Презентации, КП, отчёты, PDF/PPTX, data storytelling |
| `crm-retention` | Удержание | CRM, сегментация, LTV, реактивация, цепочки |
| `reputation` | Удержание | Отзывы, карты, рейтинги, SERM |
| `sales` | Операции | Привлечение клиентов агентства, пайплайн, outreach |
| `support` | Операции | Поддержка клиентов, KB, эскалация |
| `ops` | Операции | Задачи, календарь, вендоры, закупки |

Каждый агент в формате SOUL: Identity → Tools → Format → Rules → Guardrails → Handoff.

## Передача задач

Два режима handoff (см. [workflows/handoff-protocol.md](workflows/handoff-protocol.md)):

1. **Через Osmosy** — основной режим: delegate_task → сборка → проверка → клиенту
2. **Прямой handoff** — агент → агент через @mentions или Osmosy как релей

Пример полного цикла: [workflows/example-campaign.md](workflows/example-campaign.md)

## Быстрый старт

```bash
git clone https://github.com/Osmosy/vector-marketing.git

# 1. Заполнить company-brain/ под свой бизнес
# 2. Создать профили Hermes
hermes profile create market-research --clone
hermes profile create seo --clone
# ... (19 профилей)

# 3. Вставить agents/<name>.md в профиль Hermes
# 4. Подключить skills (см. profiles/README.md)
# 5. Настроить sign-off gates

# 6. Запустить через профиль Osmosy (оркестратор)
hermes -p osmosy --skills vector-work "Клиент: интернет-магазин. Задача: увеличить заявки на 30%."
```

## Структура репозитория

```
vector-marketing/
├── README.md
├── FUNDAMENTALS.md              ← Context → Harness → Loop
├── agent-description.md
├── LICENSE · NOTICE.md          ← MIT + атрибуция сторонних наборов
├── .gitignore                   ← company-brain/local/ — вне git
├── company-brain/               ← Общий контекст (реальный ров)
│   ├── brand-voice.md
│   ├── anti-slop-rules.md
│   ├── strategy.md
│   ├── past-campaigns.md
│   ├── offers-positioning.md
│   ├── channels-geo.md
│   └── media-list.md
├── agents/                      ← 19 SOUL-файлов (по одному на агента)
│   ├── orchestrator.md
│   ├── market-research.md
│   ├── analytics.md
│   ├── performance.md
│   ├── yandex-direct.md
│   ├── seo.md
│   ├── vk-ads.md
│   ├── avito.md
│   ├── marketplaces.md
│   ├── landing-cro.md
│   ├── content.md
│   ├── smm-telegram.md
│   ├── creative.md
│   ├── presentation.md
│   ├── crm-retention.md
│   ├── reputation.md
│   ├── sales.md
│   ├── support.md
│   └── ops.md
├── workflows/                   ← Handoff protocol + пример кампании
│   ├── handoff-protocol.md
│   └── example-campaign.md
├── profiles/                     ← Настройка профилей Hermes
├── skills/                       ← Навыки (66 из Cowork Roles + 31 PM-скилл)
├── THIRD_PARTY_LICENSES/         ← Тексты лицензий апстримов
└── assets/                       ← Логотипы
```

## PM-скиллы (skills/pm-skills/)

31 методический скилл из [PM Skills Marketplace](https://github.com/phuryn/pm-skills) (MIT, куратор Павел Хурын, The Product Compass) с адаптацией под рынок РФ: тексты апстрима сохранены, сверху добавлен блок РФ-адаптации и `### Attribution`. Апстрим содержит 68 скиллов — взяты методики, релевантные профилю маркетингового агентства (отбор зафиксирован в сообщениях коммитов).

### Исследования и стратегия

| Скилл | Что даёт | Агент |
|-------|----------|-------|
| market-sizing | TAM/SAM/SOM, top-down + bottom-up; источники РФ: Wordstat, MPSTATS, ДaData, Росстат | market-research |
| beachhead-segment | Выбор пляжного сегмента: pain / WTP / winnable share / referral | market-research |
| ideal-customer-profile | ICP из данных: демография, поведение, JTBD, PMF-опросы | market-research |
| customer-journey-map | CJM: стадии, точки контакта, эмоции, барьеры (деливерабл) | market-research |
| competitor-analysis | Разбор конкурентов; разведка РФ: библиотека Директа, MPSTATS, Авито, отзывы, ДaData | market-research |
| interview-script | Глубинные интервью по Mom Test; РФ: телефон/Telegram, вербатим-цитаты только из транскрипта | market-research |
| brainstorm-experiments-new + existing | Дымовые тесты гипотез: XYZ, лендинг+Директ, TG-интеграции, карточки WB/Ozon без рекламы | market-research |
| identify-assumptions-new + existing | Карта рисковых допущений: 8 категорий (новый продукт) / VUVF (существующий) | market-research |
| prioritize-assumptions | Матрица Impact × Risk: что тестировать первым | market-research |
| gtm-strategy | GTM-план: канальная матрица РФ, метрики запуска (ДРР, CPL) | market-research, performance |
| monetization-strategy | 3-5 моделей монетизации + валидационные эксперименты | market-research |
| lean-canvas, business-model | Канвасы для стратегических консультаций клиенту | market-research |
| pricing-strategy | Ценообразование + РФ: MPSTATS-цены, юнит-экономика МП, ДРР, налоги | market-research |
| competitive-battlecard | Батлкарта «мы vs X»; разведка: Директ, MPSTATS, отзывы, ДaData | market-research |

### Метрики и удержание

| Скилл | Что даёт | Агент |
|-------|----------|-------|
| north-star-metric | NSM + 3-5 input metrics, дерево метрик | analytics |
| ab-test-analysis | Статразбор A/B: мощность, SRM, guardrails, ship/extend/stop/revert | analytics, landing-cro |
| cohort-analysis | Retention-кривые, теплокарты когорт из CSV (дополнение к RFM) | crm-retention |
| growth-loops | 5 типов петель (Viral/Usage/Collab/UGC/Referral), loop coefficient | performance |

### Контур качества и рисков

| Скилл | Что даёт | Агент |
|-------|----------|-------|
| pre-mortem | Разбор кампании до запуска: Tigers / Paper Tigers / Elephants | performance |
| strategy-red-team | Атака несущих допущений стратегии: стилман → failure modes | orchestrator |
| privacy-policy | Политика ПДн + 152-ФЗ: согласие, локализация, реестр РКН, утечки 24/72ч | landing-cro |
| shipping-artifacts | Документация AI-сборки перед сдачей: architecture, flows, secrets | landing-cro |
| intended-vs-implemented | Аудит «задокументировано vs реализовано» в коде форм/интеграций | landing-cro |

### Упаковка и операции

| Скилл | Что даёт | Агент |
|-------|----------|-------|
| gtm-motions | Выбор GTM-мотива из 7; РФ: Paid, Inbound, Partners, Outbound, ABM(B2B) | performance |
| product-name | Нейминг + проверка: Роспатент/МКТУ, домены .ru/.рф | content |
| summarize-meeting | Транскрипты звонков → решения, action items, владельцы | sales |
| stakeholder-map | Power/interest сетка + план коммуникаций (крупные проекты) | ops |
| draft-nda | NDA по праву РФ: режим КТ (ФЗ-98), гл. 75 ГК РФ, доступы к кабинетам | ops |

Не портированы: slash-команды (42) — тонкие обёртки над скиллами, функциональность доставлена через привязку скиллов к агентам; дубль-скиллы уже имеющихся навыков (ideas, positioning, sentiment, grammar) и SDLC-домены (PRD, stories, спринты, retro) — вне профиля агентства.

## Источники

- Архитектура: `marketing-agency-hermes-structure.docx` (май 2026)
- Framework: [@shannholmberg](https://x.com/shannholmberg) / Nous Research — Context → Harness → Loop
- Платформа: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- Навыки: [Cowork Roles](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0; в репозитории 66 навыков из 6 плагинов)
- PM-методики: [phuryn/pm-skills](https://github.com/phuryn/pm-skills) (MIT, 31 скилл, адаптация РФ)
- Humblytics: [humblytics-marketing-skills](https://github.com/Humblytics/humblytics-marketing-skills) (MIT, 6 скиллов)
- GEO/AEO концепции: [dataaispark-spec/hermes-x-marketing-agency-bots](https://github.com/dataaispark-spec/hermes-x-marketing-agency-bots)
- Исследования: [claude-skills/research-ops](https://github.com/alirezarezvani/claude-skills) — как источник методологии; код не вендорился
- Соцсети: [social-media-skills](https://github.com/charlie947/social-media-skills) — источник идей, файлы не включены

### Планируемые навыки соцсетей → агенты

> Статус: **не портированы** — этих скиллов в репозитории нет, таблица фиксирует план привязки.

| Навык | Агент |
|-------|-------|
| voice-builder, newsletter-voice, post-writer, hook-generator, post-formatter, quote-post | content |
| gemini-carousel, gemini-infographic, graphic-designer, youtube-thumbnail, reels-scripting | creative |
| analytics-dashboard, post-scorer, content-matrix, niche-research, profile-optimizer, pinned-comment | smm-telegram |