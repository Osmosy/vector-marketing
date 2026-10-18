# Дека Vector Marketing — печатная print-bordo + экранная obsidian-neon

13 слайдов: титул, введение, проблема, решение, три слоя, агенты, PM-скиллы,
гипотезный цикл, контур качества, инструменты РФ, деливераблы, roadmap, финал.

- **Основная дека (печать):** `vector-marketing-print-bordo.pptx` — белые слайды,
  бордовая обложка `5C1420`, Cambria/Calibri, без hero-арта. Тема `print-bordo`
  из движка; на бумаге читается, в отличие от тёмной.
- **Экранная дека:** `vector-marketing-01-obsidian-neon.pptx` — неон-синий на
  тёмно-синем, hero-арт воронки; для показа на экране, не для печати
  (`print_safe=False`).
- **Исходник:** `deck-marketing.py` — контент в `DATA`, дизайн — движок тем
  `~/projects/vector-legal-decks15/engine.py`
- **Сборка:** `build.py` — воспроизводимая, собирает обе темы (см. ниже)
- **Hero-арт:** `hero-marketing.png` — 1024×576, неоновая воронка + AI-ядро.
  Используется только в тёмной теме: у печатной арта нет по дизайну.
- **Логотип:** `vector_ray_t.png` — обязателен на титуле и финале обеих дек

## Пересборка

```bash
env -u PYTHONPATH ~/.venvs/pptx/bin/python deck/build.py          # обе темы
```

`env -u PYTHONPATH` нужен в окружении Hermes: его `PYTHONPATH` указывает на
site-packages python3.14, и PIL внутри python3.12-venv падает с
`ImportError: cannot import name '_imaging'`.

Зависимости: venv `~/.venvs/pptx` (python-pptx, Pillow, numpy), движок тем в
`~/projects/vector-legal-decks15/`.

Рендер в PNG для визуальной проверки:

```bash
~/.venvs/pptx/bin/python ~/.hermes/skills/productivity/powerpoint/scripts/pptx_render.py \
    deck/vector-marketing-01-obsidian-neon.pptx --outdir /tmp/mk_render
```

## Почему сборка в репозитории, а не во временном файле

Изначально обёртка сборки жила в `/tmp/build_marketing.py` и была потеряна при очистке
`/tmp`. Пришлось восстанавливать арт и эмблему прямо из готового pptx. Теперь `build.py`
лежит рядом с исходником и воспроизводит деку из файлов репозитория.

## Что обязательно переопределять при сборке этой деки

Тема `01-obsidian-neon` в движке несёт **юридический** контент-слой, и на маркетинговой
деке это брак. `build.py` переопределяет:

| Поле темы | В движке (Vector Legal) | Здесь |
|-----------|-------------------------|-------|
| `art` | `title_hero.png` (весы) | `hero-marketing.png` (воронка); у `print-bordo` — `None` |
| `emblem` | `scales_icon_t.png` (весы) | `vector_ray_t.png` (луч Vector); у `print-bordo` — `None` |
| `footer_brand` | `Vector Legal · Hermes Agent · Osmosy` | `Vector Marketing · Osmosy` |
| `footer_total` | 12 | 13 |

Печатная тема намеренно без арта и эмблемы: в образце
`Обоснование_реальности_плана-4.pptx` их нет, а чужие весы или луч на белом листе
только мешают. Обложка держится на цвете (`cover_bg=5C1420`), не на картинке.

Это то же правило, что зафиксировано в скилле `vector-deck-themes`: при смене темы
обязателен полный контент-слой — сохраняется только палитра и композиция.

## Сверка чисел с репозиторием

Числа на слайдах должны совпадать с фактическим составом (проверено на 20.09.2026):

| Место в деке | Значение | Источник |
|--------------|----------|----------|
| Чипы титула | 19 / 161 / 40 | `agents/`, `skills/`, `skills/pm-skills/` |
| Слайд «Три слоя» | 161 навык в 14 наборах | `skills/` |
| Слайд PM-скиллов | 40 из 68 | `skills/pm-skills/`, апстрим phuryn/pm-skills |
| Расклад факта | 19 агентов · 40 методик | — |

При изменении состава менять числа в `deck-marketing.py` и пересобирать.
