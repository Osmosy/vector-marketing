---
name: vector-work
description: "Load when working with any Vector ecosystem project — Vector Marketing (AI-агентство, 19 агентов), Vector Meat (ИИ-план мясопереработки), Vector Home (умный дом на GPT-2), Vector Grace (GRACE на GitHub). Routing hub for all Osmosy/vector-* repositories."
---

# Vector Work — экосистема проектов Osmosy

Хаб-навык. Маршрутизирует к нужному проекту, навыку или агенту в экосистеме Vector.

## Проекты

| Проект | Репозиторий | Суть |
|--------|------------|------|
| **Vector Marketing** | `Osmosy/vector-marketing` | AI-маркетинговое агентство: 19 агентов под Osmosy (Hermes) |
| **Vector Meat** | `Osmosy/vector-meat` | План внедрения ИИ на мясоперерабатывающем заводе |
| **Vector Home** | `Osmosy/vector-home` | Умный дом на GPT-2 124M (CPU, без облака) |
| **Vector Grace** | `Osmosy/vector-grace` | GRACE-методология с GitHub-экспортом |

## Связанные навыки

| Навык | Для чего |
|-------|----------|
| `vector-meat-ai-plan` | План внедрения ИИ на мясопереработке |
| `home-assistant-production-patterns` | 7 production-паттернов для HA (из CCOSTAN) |
| `ha-hermes-skills` | 5 Hermes-навыков для Home Assistant |
| `agents-best-practices` | Архитектура агентов, промпт-кеширование, безопасность |
| `grace-methodology` | GRACE: контракт-первичная разработка |
| `free-3d-generation-services` | Топ-5 бесплатных сервисов 3D-генерации |
| `seafile-self-hosted` | Seafile — self-hosted файловое хранилище |

## Vector Marketing — быстрый запуск

```bash
# Клонировать
git clone https://github.com/Osmosy/vector-marketing.git

# Создать профили (4 ключевых для MVP)
hermes profile create market-research --clone
hermes profile create analytics --clone
hermes profile create content --clone
hermes profile create presentation --clone

# Оркестратор — сам Hermes в роли Osmosy
hermes --skills vector-work "Клиент: интернет-магазин. Задача: увеличить заявки на 30%."
```

## Vector Marketing — структура агентов

```
Osmosy (CMO)
  ├── СТРАТЕГИЯ: market-research, analytics
  ├── ПРИВЛЕЧЕНИЕ: performance, yandex-direct, seo, vk-ads, avito, marketplaces
  ├── УПАКОВКА: landing-cro, content, smm-telegram, creative, presentation
  ├── УДЕРЖАНИЕ: crm-retention, reputation
  └── ОПЕРАЦИИ: sales, support, ops
```

## Принципы экосистемы Vector

1. **Русский язык** — все навыки, промпты и ответы на русском
2. **Open-source** — MIT/Apache 2.0, всё на GitHub под Osmosy
3. **CPU-first** — по возможности без GPU (GPT-2 124M вместо Llama 8B)
4. **Self-hosted** — данные локально, без облачных API где возможно
5. **Российская специфика** — Яндекс, Авито, VK, Честный Знак, Меркурий, 152-ФЗ
6. **Production-паттерны** — rate-limiting, duplicate detection, graceful degradation из коробки

## Быстрые команды

```bash
# Аудит любого Vector-проекта
hermes --skills doctor "проверь ~/projects/vector-marketing"

# Развернуть агента
hermes profile create <agent-name> --clone

# Запустить с конкретным навыком
hermes --skills vector-meat-ai-plan "спроектируй пилот для колбасного цеха"
```
