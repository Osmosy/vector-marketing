<div align="center">

<img src="assets/vector-logo.png" alt="Vector Marketing" width="200"/>

# Vector Marketing

**AI-маркетинговое агентство на базе Hermes Agent — 19 профильных агентов под управлением Osmosy**

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://github.com/NousResearch/hermes-agent)
[![Agents: 19](https://img.shields.io/badge/Agents-19-green.svg)](#агенты)
[![Cowork: 141 skills](https://img.shields.io/badge/Cowork-141%20skills-orange.svg)](https://github.com/anthropics/knowledge-work-plugins)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
5. Клиент получает готовый результат: стратегию, отчёт, кампанию, презентацию или документ

## Агенты

| Агент | Блок | Роль |
|-------|------|------|
| market-research | Стратегия | Рынок, ЦА, конкуренты, позиционирование |
| analytics | Стратегия | Метрики, воронки, ROMI, дашборды |
| performance | Привлечение | Медиаплан, бюджетирование, тесты гипотез |
| yandex-direct | Привлечение | Яндекс Директ, семантика, аудит |
| seo | Привлечение | SEO, GEO/AI Search, структура сайта |
| vk-ads | Привлечение | VK Реклама, аудитории, ретаргетинг |
| avito | Привлечение | Авито как performance-канал |
| marketplaces | Привлечение | Ozon, WB, Яндекс Маркет |
| landing-cro | Упаковка | Лендинги, A/B-гипотезы, CTA |
| content | Упаковка | Статьи, SEO-тексты, контент-планы |
| smm-telegram | Упаковка | Telegram/SMM, контент-воронки |
| creative | Упаковка | Креативы, баннеры, AI-промпты |
| presentation | Результат | Презентации, КП, отчёты, PDF/PPTX |
| crm-retention | Удержание | CRM, сегментация, LTV, реактивация |
| reputation | Доверие | Отзывы, рейтинги, SERM |
| sales | Операции | Привлечение клиентов агентства, пайплайн, outreach |
| support | Операции | Поддержка клиентов, KB, эскалация |
| ops | Операции | Задачи, календарь, вендоры, закупки |

## Быстрый старт

```bash
git clone https://github.com/Osmosy/vector-marketing.git
hermes profile create market-research --clone
hermes --skills vector-work "Клиент: интернет-магазин. Задача: увеличить заявки на 30%."
```

## Источники

- Архитектура: `marketing-agency-hermes-structure.docx` (май 2026)
- Кейсы: `Hermes Agent — сборник кейсов.md` (99 кейсов)
- Платформа: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- Навыки: [Cowork Roles](https://github.com/anthropics/knowledge-work-plugins) (141 навык)
- Исследования: [claude-skills/research-ops](https://github.com/alirezarezvani/claude-skills) — enterprise R&D методология (TAM/SAM/SOM, Porter, опросы)
- Соцсети: [social-media-skills](https://github.com/charlie947/social-media-skills) — 17 навыков (tone of voice, посты, Reels, карусели, аналитика)

### Навыки соцсетей → агенты

| Навык | Агент |
|-------|-------|
| voice-builder, newsletter-voice, post-writer, hook-generator, post-formatter, quote-post | content |
| gemini-carousel, gemini-infographic, graphic-designer, youtube-thumbnail, reels-scripting | creative |
| analytics-dashboard, post-scorer, content-matrix, niche-research, profile-optimizer, pinned-comment | smm-telegram |
