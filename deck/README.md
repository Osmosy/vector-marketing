# Дека Vector Marketing — obsidian-neon

13 слайдов: титул, введение, проблема, решение, три слоя, агенты, PM-скиллы,
гипотезный цикл, контур качества, инструменты РФ, деливераблы, roadmap, финал.

- **PPTX:** `vector-marketing-01-obsidian-neon.pptx` (готовая дека, 13 слайдов)
- **Исходник:** `deck-marketing.py` — контент в `DATA`, дизайн — движок тем
  `~/projects/vector-legal-decks15/engine.py` (тема `01-obsidian-neon`)
- **Сборка:** `build.py` — воспроизводимая, лежит в этой папке (см. ниже)
- **Hero-арт:** `hero-marketing.png` — 1024×576, неоновая воронка + AI-ядро.
  Сгенерирован локально Z-Image-Turbo (ROCm на iGPU); ZAI glm-image в тот момент
  отдавал 429 (insufficient balance)
- **Логотип:** `vector_ray_t.png` — обязателен на титуле и финале

## Пересборка

```bash
~/.venvs/pptx/bin/python deck/build.py          # собрать + положить pptx в deck/
~/.venvs/pptx/bin/python deck/build.py --no-render
```

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
| `art` | `title_hero.png` (весы) | `hero-marketing.png` (воронка) |
| `emblem` | `scales_icon_t.png` (весы) | `vector_ray_t.png` (луч Vector) |
| `footer_brand` | `Vector Legal · Hermes Agent · Osmosy` | `Vector Marketing · Osmosy` |
| `footer_total` | 12 | 13 |

Это то же правило, что зафиксировано в скилле `vector-deck-themes`: при смене темы
обязателен полный контент-слой — сохраняется только палитра и композиция.

## Сверка чисел с репозиторием

Числа на слайдах должны совпадать с фактическим составом (проверено на 13.09.2026):

| Место в деке | Значение | Источник |
|--------------|----------|----------|
| Чипы титула | 19 / 158 / 40 | `agents/`, `skills/`, `skills/pm-skills/` |
| Слайд «Три слоя» | 158 навыков в 6 наборах | `skills/` |
| Слайд PM-скиллов | 40 из 68 | `skills/pm-skills/`, апстрим phuryn/pm-skills |
| Расклад факта | 19 агентов · 40 методик | — |

При изменении состава менять числа в `deck-marketing.py` и пересобирать.
