# Базовый профиль для агента Vector Marketing

Каждый агент разворачивается как отдельный профиль Hermes:

```bash
hermes profile create <agent-name> --clone
```

## Настройка SOUL.md для агента

```
Ты — <role> агентства Vector Marketing. Твоя специализация: <specialization>.

Базовые правила:
1. Отвечай на русском языке
2. Работай только по своей специализации. Если задача вне твоей зоны — сообщи Osmosy (оркестратору)
3. Используй только фактические данные. Если данных нет — запроси, не додумывай
4. Формат выдачи: конкретные выводы, а не общие рассуждения
5. Указывай источники данных
```

## Подключение skills

```bash
# Для каждого агента — свой набор
hermes -p <agent-name> skills install <skill-name>
```

## Сводная таблица агентов

| Профиль | Блок | Ключевые skills |
|---------|------|----------------|
| market-research | Стратегия | yandex-wordstat, social-media-research, DaData, maps |
| analytics | Стратегия | yandex-marketing-apis-ru, google-workspace, MPSTATS |
| performance | Привлечение | marketing-director-ru, yandex-marketing-apis-ru |
| yandex-direct | Привлечение | yandex-direct, yandex-wordstat |
| seo | Привлечение | evidence-based-seo, yandex-wordstat |
| vk-ads | Привлечение | social-media-research |
| avito | Привлечение | avito-api |
| marketplaces | Привлечение | ozon-seller-api, wildberries-api, MPSTATS, YooKassa |
| landing-cro | Упаковка | creative/visual skills, ru-text |
| content | Упаковка | ru-text, evidence-based-seo, humanizer |
| smm-telegram | Упаковка | social-media-research, ru-text |
| creative | Упаковка | creative/visual skills |
| presentation | Результат | powerpoint, document-deliverables, google-workspace |
| crm-retention | Удержание | google-workspace, DaData |
| reputation | Доверие | maps, DaData |

## Модели

- **Основные агенты (research, analytics, content, presentation):** deepseek-v4-pro
- **Тяжёлые агенты (performance, seo — анализ объёмов):** glm-5.1:cloud или minimax-m2.7
- **Лёгкие агенты (avito, reputation — поиск данных):** deepseek-v4-flash:cloud
