---
name: timesfm-marketing
description: Use when forecasting marketing metrics (campaign traffic, conversions, sales) or detecting campaign anomalies with TimesFM. Triggers on 'прогноз кампании', 'forecast clicks', 'промо-эффект', 'campaign forecast'.
version: 1.0.0
author: Osmosy
license: MIT
metadata:
  hermes:
    tags: [marketing, timesfm, forecasting, campaigns, anomalies, promo]
    related_skills: [campaign-analytics, paid-ads, marketing-strategist, timesfm-forecasting]
---

# TimesFM Marketing Toolkit

Прогнозирование маркетинговых метрик на TimesFM 2.5 (Google Research):
zero-shot, без обучения, локально на CPU. Промо-календарь учитывается через
ковариаты, аномалии в истории ловятся квантильными интервалами.

Код и проверенный пайплайн: `~/projects/timesfm-pilot/` (README с полным
описанием, campaign_forecast.py, метрики прогона).

## Быстрый запуск (venv уже собран)

```bash
source ~/.venvs/timesfm/bin/activate
cd ~/projects/timesfm-pilot

# прогноз клики+конверсии на 14 дней с промо-календарём и holdout
python campaign_forecast.py --input campaign.csv --date-col date \
    --value-cols clicks,conversions --covariate-col promo \
    --holdout 14 --horizon 14 --outdir out
```

Выход в `out/`: `<col>_forecast.csv` (прогноз + 60/80% интервалы),
`<col>_forecast.png` (график), `<col>_anomalies.csv` (флаги OK/WARNING/
CRITICAL), `metrics.json` (MAE/RMSE/MAPE/покрытие PI + тайминги).

## Требования к данным

- CSV: колонка даты + >= 1 метрическая колонка; минимум **32 точки** истории.
- Ковариат (промо 0/1, праздники): покрывать историю; будущее по умолчанию 0
  («акций нет») — для планового промо добавить строки с датами вперёд.
- XReg требует `return_backcast=True` — уже стоит в campaign_forecast.py;
  при прямом API без backcast будет ValueError.
- XReg-выход включает backcast: горизонт = ПОСЛЕДНИЕ `--horizon` значений.

## Когда применять (маркетинговые кейсы)

1. Прогноз трафика/конверсий кампании — планирование бюджета и KPI.
2. Оценка будущего промо — ковариат-календарь: модель переносит выученный
   подъём на запланированные дни (на тесте: +46,6% при заложенных +40%).
3. Планирование запасов/лидов — горизонт 14–30 дней.
4. Мониторинг аномалий — факт вне 80% PI = скликивание, выгорание креатива,
   вирусный пик. WARNING = вне 60% PI, CRITICAL = вне 80% PI.
5. Бенчмарк для отчёта — `--holdout N` даёт честные метрики точности.

## Чего НЕ делать

- Не причинно-следственный анализ: прогноз ≠ «что будет если поднять бюджет»;
  для causal-выводов — A/B-тесты.
- Не атрибуция и не сегментация.
- Новым кампаниям (< 32 точек) прогноз слаб — агрегируйте сверху.

## Характеристики на машине (замерено 01.09.2026)

- CPU 20 ядер: прогноз 1 ряда ~250 мс, с ковариатом ~1,7–2,9 с,
  батч 100 рядов ~1–2 мин; load модели из кэша 1–2 с.
- VRAM iGPU (16 ГБ) torch-ом НЕ используется (AMD, не CUDA) — только CPU,
  этого достаточно; RAM ~1,5 ГБ, batch_size 8 при 5+ ГБ свободных.
- Ошибка `JAX cuInit 303` в логах безвредна (плагин CUDA на AMD).
- Лицензия: 2.5 = Apache-2.0 (коммерческое ок); TimesFM-3 = некоммерческая.

## Связь с TimesFM-3

TimesFM-3 (Google, 08.2026) добавил нативную мультисерийность: цели +
ковариаты в одном проходе, первое место на Gift-Eval/FEV-Bench/Time.
Веса некоммерческие; для прода использовать 2.5 + XReg (этот тулкит).
При переходе на 3.0: 9 квантилей вместо 10, индексы сдвигаются (q10 = 0).

### Лицензия 3.0: что реально разрешено (текст license v1.0, 04.09.2026)

- **Outputs НЕ являются Derivative** — прогнозы, сделанные 3.0, лицензия
  не ограничивает и использовать их в коммерческих решениях можно.
- Non-Commercial Purpose = «testing, evaluation, research not tied to commercial
  gain... provided the results are not used in commercial decision-making,
  client deliverables, or paid products/services».
- **Запрещено:** использовать модель в производственных/коммерческих
  процессах; дистрибуция модели/деривативов; дистрибуция Outputs
  «for any commercial or production purposes» (т.е. продавать сам прогноз
  как услугу нельзя); дистилляция 3.0 в коммерческую модель.
- Следствие: гибрид «3.0 черновик → 2.5 финал» легален, если 3.0-прогон
  остаётся внутренним исследованием и финальные клиентские цифры даёт 2.5.
- ВАЖНО (04.09, уточнение): внутреннее использование на заводе для планирования
  производства — ЗАПРЕЩЕНО, даже без продажи прогноза. Non-Commercial
  исключает «results used in commercial decision-making» и «production
  deployment». Грань: цифра 3.0 попала в производственный план = нарушение;
  сравнение 3.0 vs 2.5 во внутреннем отчёте = можно.

### Замер 2.5 vs 3.0 на этой машине (04.09.2026, T=400, промо +20%)

- MAE весь горизонт: 2.5 баз 0.120 | 2.5 xreg 0.107 | 3.0 баз 0.128 | **3.0 ковар 0.105**
- Промо-дни: 3.0 ковар ловит лучше на короткой истории (T=200: 0.142 vs 0.381)
- Скорость ковариатного прогноза: 2.5 xreg ~1.3s vs 3.0 ~0.23s (~6x)
- XReg-пайплайн 2.5: прогноз на промо-день без ошибки (+0.004 MAE) при
  выраженном промо-паттерне — для календаря акций 2.5+XReg достаточен.