# Дека Vector Marketing — obsidian-neon

13 слайдов: титул, введение, проблема, решение, три слоя, агенты, PM-скиллы,
гипотезный цикл, контур качества, инструменты РФ, деливераблы, roadmap, финал.

- **PPTX:** vector-marketing-01-obsidian-neon.pptx (готовая дека)
- **Исходник:** deck-marketing.py — контент в DATA, дизайн через engine.py
  (~/projects/vector-legal-decks15/, тема 01-obsidian-neon)
- **Hero-арт:** hero-marketing.png — неоновая воронка + AI-ядро (2048×1152).
  Сгенерирован локально (PIL): ZAI glm-image вернул 429 (insufficient balance),
  fallback-генерация в теме obsidian-neon. При пополнении баланса можно
  перегенерить через glm-image и пересобрать одной командой.

Пересборка:
```bash
~/.venvs/pptx/bin/python /tmp/build_marketing.py   # или deck_builder.py deck-marketing.py 01-obsidian-neon
```

Логотип Vector Ray на титуле и финале — обязательный элемент (vector_ray_t.png,
регенерация: ~/.hermes/skills/vector-deck-themes/scripts/prep-vector-ray-logo.py).
