<div align="center">

<img src="assets/vector-logo.png" alt="Vector Marketing" width="200"/>

# Vector Marketing

**AI-маркетинговое агентство на базе Hermes Agent — 19 профильных агентов под управлением Osmosy (CMO-оркестратор)**

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://github.com/NousResearch/hermes-agent)
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

Общий контекст для всех агентов. **Это реальный рва — ценность в контексте, а не в ботах.** Заполните под свой бизнес.

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

# 6. Запустить через Osmosy
hermes --skills vector-work "Клиент: интернет-магазин. Задача: увеличить заявки на 30%."
```

## Структура репозитория

```
vector-marketing/
├── README.md
├── FUNDAMENTALS.md              ← Context → Harness → Loop
├── agent-description.md
├── company-brain/               ← Общий контекст (реальный рва)
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
├── skills/                       ← Навыки (141+ из Cowork Roles)
└── assets/                       ← Логотипы
```

## Источники

- Архитектура: `marketing-agency-hermes-structure.docx` (май 2026)
- Framework: [@shannholmberg](https://x.com/shannholmberg) / Nous Research — Context → Harness → Loop
- Платформа: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- Навыки: [Cowork Roles](https://github.com/anthropics/knowledge-work-plugins) (141 навык)
- GEO/AEO концепции: [dataaispark-spec/hermes-x-marketing-agency-bots](https://github.com/dataaispark-spec/hermes-x-marketing-agency-bots)
- Исследования: [claude-skills/research-ops](https://github.com/alirezarezvani/claude-skills)
- Соцсети: [social-media-skills](https://github.com/charlie947/social-media-skills)

### Навыки соцсетей → агенты

| Навык | Агент |
|-------|-------|
| voice-builder, newsletter-voice, post-writer, hook-generator, post-formatter, quote-post | content |
| gemini-carousel, gemini-infographic, graphic-designer, youtube-thumbnail, reels-scripting | creative |
| analytics-dashboard, post-scorer, content-matrix, niche-research, profile-optimizer, pinned-comment | smm-telegram |