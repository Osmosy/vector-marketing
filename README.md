# Vector Marketing

Маркетинговое агентство на базе Hermes Agent. 16 профильных AI-специалистов под управлением Osmosy (Hermes-оркестратор).

## Архитектура

```
Клиент → Osmosy (CMO-оркестратор)
              ├── СТРАТЕГИЯ: market-research, analytics
              ├── ПРИВЛЕЧЕНИЕ: performance, yandex-direct, seo, vk-ads, avito, marketplaces
              ├── УПАКОВКА: landing-cro, content, smm-telegram, creative, presentation
              └── УДЕРЖАНИЕ: crm-retention, reputation
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

## Быстрый старт

```bash
# Клонировать репо
git clone https://github.com/Osmosy/vector-marketing.git

# Создать профили Hermes
hermes profile create market-research --clone
hermes profile create analytics --clone
# ... (все 16 агентов)

# Настроить skills для каждого профиля
hermes -p market-research skills install yandex-wordstat
hermes -p yandex-direct skills install yandex-direct
# ...

# Запустить оркестратор
hermes --profile osmosy "Клиент: интернет-магазин зоотоваров. Задача: увеличить заявки из Яндекса на 30% за квартал."
```

## Подключённые skills и инструменты

**Skills:** marketing-director-ru, evidence-based-seo, yandex-direct, yandex-wordstat, yandex-marketing-apis-ru, social-media-research, ru-text, google-workspace, document-deliverables, powerpoint, maps, airtable, youtube-content, creative/visual

**MCP/API:** DaData MCP, Ozon Seller API, Wildberries API, MPSTATS, YooKassa, Avito API

## Источники

- Архитектура: `marketing-agency-hermes-structure.docx` (май 2026)
- Кейсы экосистемы: `Hermes Agent — сборник кейсов.md` (99 кейсов)
- Платформа: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
