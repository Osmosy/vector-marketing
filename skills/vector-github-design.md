---
name: vector-github-design
description: "Load when creating or updating any Osmosy/vector-* GitHub repository README. Mandatory unified design: centered logo, title, description, badges row, separator. Based on russian-vector template."
---

# Vector GitHub Design — обязательный стиль репозиториев

Единый дизайн для всех репозиториев экосистемы Vector (Osmosy).

## Шаблон README

```markdown
<div align="center">

<img src="assets/vector-logo.png" alt="Название" width="200"/>

# Название проекта

**Краткое описание — одна строка, суть проекта**

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://github.com/NousResearch/hermes-agent)
[![Ключевая метрика](https://img.shields.io/badge/Метрика-Значение-green.svg)](ссылка)
[![Доп. метрика](https://img.shields.io/badge/Метрика-Значение-orange.svg)](ссылка)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

Содержание README...
```

## Правила

1. **Лого:** `assets/vector-logo.png` — Vector Ray из Загрузок, 1536×1024. Отображается width="200".
2. **Выравнивание:** `<div align="center">` для шапки с лого, названием и бейджами.
3. **Разделитель:** `---` после закрывающего `</div>`.
4. **Бейджи:** минимум 3 штуки. Первый — Hermes Agent (синий). Цвета: blue/green/orange/yellow. Ссылки на релевантные ресурсы.
5. **Название:** H1 (`#`), короткое, без подзаголовков.
6. **Описание:** жирным (`**`), одна строка, суть проекта.
7. **Лицензия:** MIT для своих, Apache 2.0 для форков.

## Файлы логотипа

В каждом репо должны быть:
- `assets/vector-logo.png` — полный размер (1536×1024)
- `assets/vector-logo-sm.png` — уменьшенный (384×256, для README если полный не грузится)

Исходник: `~/Загрузки/vector ray.png` (MD5: `bec3d5845f639890330e6c33c05a20cd`).

## Цвета бейджей

| Цвет | Для чего |
|------|----------|
| `blue` | Hermes Agent (обязательный, всегда первый) |
| `green` | Ключевая метрика (количество агентов, ролей, стадий) |
| `orange` | Дополнительная метрика (навыки, источники) |
| `yellow` | Лицензия |

## Существующие репозитории

| Репо | Статус |
|------|--------|
| `Osmosy/russian-vector` | Эталон |
| `Osmosy/vector-marketing` | Соответствует |
| `Osmosy/vector-work` | Соответствует |
| `Osmosy/vector-meat` | Соответствует |
| `Osmosy/vector-home` | Требует обновления |
| `Osmosy/vector-grace` | Требует обновления |

## Команда для нового репо

```bash
mkdir -p ~/projects/vector-NAME/assets
cp ~/Загрузки/vector\ ray.png ~/projects/vector-NAME/assets/vector-logo.png
python3 -c "
from PIL import Image
img = Image.open('~/Загрузки/vector ray.png')
img.resize((384, 256), Image.LANCZOS).save('~/projects/vector-NAME/assets/vector-logo-sm.png')
"
# Затем создать README по шаблону выше
```
