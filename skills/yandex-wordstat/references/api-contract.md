# Контракт API Wordstat (Yandex Cloud Search API v2)

Сверено с двумя официальными источниками (оба — репозитории Яндекса, не сторонние гайды):

- proto-контракт: `yandex-cloud/cloudapi` → `yandex/cloud/searchapi/v2/wordstat_service.proto`;
- квоты и лимиты: `yandex-cloud/docs` → `ru/_includes/search-api-limits.md`.

Проверено живыми запросами к `searchapi.api.cloud.yandex.net` (в т.ч. коды ошибок —
с намеренно неверным ключом и с пропущенными обязательными полями).

## Эндпоинты

| Метод | Путь | Назначение |
|-------|------|-----------|
| `GetTop` | `POST /v2/wordstat/topRequests` | топ фраз за 30 дней + ассоциации |
| `GetDynamics` | `POST /v2/wordstat/dynamics` | частота во времени |
| `GetRegionsDistribution` | `POST /v2/wordstat/regions` | распределение по регионам |
| `GetRegionsTree` | `POST /v2/wordstat/getRegionsTree` | дерево регионов (бесплатно) |

Аутентификация: `Authorization: Api-Key <ключ сервисного аккаунта>`, роль
`search-api.webSearchUser`. `folderId` передаётся **в теле** запроса (поле `folderId`;
в proto — `folder_id`); заголовок `x-yandex-folder-id` не проверялся как обязательный,
тело работает.

## Обязательные и необязательные поля

### `topRequests`
| Поле | Обяз. | Тип / ограничение |
|------|-------|-------------------|
| `phrase` | да | ≤ 400 символов |
| `numPhrases` | **да** | 1..2000; ответ усечётся до 250 фраз |
| `regions` | нет | список ID регионов, ≤ 100 |
| `devices` | нет | ≤ 3 значения из `DEVICE_ALL\|DEVICE_DESKTOP\|DEVICE_PHONE\|DEVICE_TABLET` |
| `folderId` | да (для запроса к API) | ≤ 50 символов, фактически 20 |

Ответ: `totalCount` (int64), `results[] {phrase, count}`, `associations[] {phrase, count}`.

### `dynamics`
| Поле | Обяз. | Тип |
|------|-------|-----|
| `phrase` | да | ≤ 400 символов |
| `period` | **да** | `PERIOD_MONTHLY\|PERIOD_WEEKLY\|PERIOD_DAILY` |
| `fromDate` | **да** | Timestamp, RFC 3339 (`2026-08-01T00:00:00Z`) |
| `toDate` | нет | Timestamp |
| `regions`, `devices`, `folderId` | нет | как в `topRequests` |

Ответ: `results[] {date, count, share}` — `share` это доля запросов от всех запросов
Яндекса.

### `regions`
| Поле | Обяз. | Тип |
|------|-------|-----|
| `phrase` | да | ≤ 400 символов |
| `region` | нет | `REGION_ALL\|REGION_CITIES\|REGION_REGIONS` |
| `devices`, `folderId` | нет | |

Ответ: `results[] {region, count, share, affinityIndex}`. `affinityIndex` — отношение
доли фразы в регионе к её доле по стране: >1 — спрос выше среднего.

### `getRegionsTree`
Тело: только `folderId`. Ответ: `regions[] {id, label, children[]}` (рекурсивно).
Бесплатный метод, в часовую квоту статистики не входит — кэшируйте на диск.

## Квоты и лимиты (официальные)

| Ограничение | Значение |
|-------------|----------|
| Запросов статистики в час | 100 |
| Запросов статистики в секунду | 10 |
| Максимум результатов в ответе | 250 |
| Максимум ассоциаций | 20 |
| Максимальное количество слов в запросе | см. `_includes` в `yandex-cloud/docs` (плейсхолдер `search-api-request-w`) |
| Максимальная длина запроса | плейсхолдер `search-api-request-ch` в той же доке |

Оплата — депозит: списание по факту запросов, неиспользованное не сгорает. Цены и
тарифы живут в разделе `search-api` биллинга и меняются — берите их в консоли
облака, а не из сторонних статей (в них встречаются цифры вида «500 ₽ на 4-5 месяцев»,
невыверяемые по первоисточнику).

## Коды ошибок (проверено живыми вызовами)

| `code` | HTTP | Что означает | Что делать |
|--------|------|--------------|------------|
| 3 | 400 | `InvalidArgument`: пропущено обязательное поле или значение вне диапазона (`num_phrases: Value must be in the range of 1 to 2000`, `phrase: Field is required`, `period: Field is required`) | проверить тело запроса |
| 7 | 403 | нет прав | у сервисного аккаунта должна быть роль `search-api.webSearchUser` |
| 8 | 429 | `rate quota limit exceed: allowed 100 requests` | дождаться слота, уменьшить бюджет |
| 16 | 401 | `Unknown api key` | проверить `WORDSTAT_API_KEY` |

Важно: ошибки приходят и с HTTP 200/4xx, а тело всегда `{code, message, details}` —
скрипт разбирает `code`, а не HTTP-статус.

## Настройка доступа (сервисный аккаунт, не личный OAuth)

1. Yandex Cloud → создать **сервисный аккаунт**.
2. Выдать роль `search-api.webSearchUser`.
3. Создать **API-ключ** этого сервисного аккаунта (значение показывается один раз).
4. Взять **ID каталога** (`b1g…`, 20 символов) — он идёт в `WORDSTAT_FOLDER_ID`.
5. Пополнить баланс каталога.
6. Проверить:

```bash
curl -s -X POST 'https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests' \
  -H "Authorization: Api-Key $WORDSTAT_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"phrase":"тест","numPhrases":5,"folderId":"'"$WORDSTAT_FOLDER_ID"'"}'
```

OAuth-путь (приложение в `oauth.yandex.ru` → IAM-токен на 12 часов) встречается в
сторонних гайдах и для регулярных прогонов не нужен: сервисный аккаунт живёт дольше
и не привязан к пользователю.

## Границы API

- `topRequests`/`regions` всегда дают данные за **последние 30 дней**; окно не настраивается.
- Seed — это **фраза**. «Собрать семантику по сайту» требует отдельного шага: получить
  seed-фразы из карты сайта/страниц и подать их в `collect`. API этого не делает.
- Прямого доступа к сырым строкам отчёта «что ещё искали с…» нет: ассоциации
  ограничены 20 записями на запрос.
