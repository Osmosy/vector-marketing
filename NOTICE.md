# Сторонние компоненты и атрибуция

Настоящий репозиторий распространяется под лицензией MIT (см. `LICENSE`).
Ниже перечислены сторонние наборы, фрагменты которых включены в `skills/`.
Каждый из них сохраняет собственную лицензию; полные тексты — в
`THIRD_PARTY_LICENSES/`.

## Что именно взято

| Набор | Лицензия | Взято в `skills/` | Статус |
|-------|----------|-------------------|--------|
| [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | MIT (© 2026 Pawel Huryn) | `pm-skills/` — 40 скиллов | тексты без изменений, сверху добавлен блок РФ-адаптации и `### Attribution` |
| [Humblytics/humblytics-marketing-skills](https://github.com/Humblytics/humblytics-marketing-skills) | MIT (© 2026 Humblytics, Inc.) | `humblytics-marketing/` — 12 скиллов | 11 без изменений, 1 (ad-expert) адаптирован под MCP-маршрут |
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Cowork Roles) | Apache-2.0 | `cowork-roles/` — 66 скиллов из 6 плагинов | файлы без изменений, байт-в-байт |
| [every-app/open-seo](https://github.com/every-app/open-seo) | MIT (© 2026 Ben Senescu) | `open-seo/` | обзор + рабочая установка |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | MIT (© 2025 Alireza Rezvani) | `claude-skills/` — 7 скиллов (LinkedIn-набор + local-seo-manager) | тексты без изменений, сверху `### Attribution`; скиллы с `references/` и `scripts/` |
| [searchfit/searchfit-seo](https://github.com/searchfit/searchfit-seo) | MIT | `searchfit-seo/` — 11 скиллов | тексты без изменений, сверху `### Attribution`; во frontmatter добавлено только поле `name` |
| [charlie947/social-media-skills](https://github.com/charlie947/social-media-skills) | MIT (© 2026 Charlie Hills) | `social-media-skills/` — 17 скиллов | тексты без изменений, сверху `### Attribution`; два скилла с `references/` |

Новые скиллы добавляются скриптом, а не вручную:

```bash
python3 scripts/vendor_skill.py --set <набор> --skills имя1,имя2
```

Скрипт копирует файлы апстрима байт-в-байт, дописывает `### Attribution` в конец SKILL.md
и кладёт текст лицензии апстрима в `THIRD_PARTY_LICENSES/`, если его там ещё нет.

## Использовано как источник идей (файлы не включены)

- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — research-ops: методология исследования, код не вендорился.
- [charlie947/social-media-skills](https://github.com/charlie947/social-media-skills) — 17 скиллов соцсетей: **в репозитории отсутствуют**, см. раздел «Не портировано» в README.
- [dataaispark-spec/hermes-x-marketing-agency-bots](https://github.com/dataaispark-spec/hermes-x-marketing-agency-bots) — концепции GEO/AEO.

## Требования, которые мы соблюдаем

- **MIT** (pm-skills, Humblytics, open-seo): текст лицензии и copyright notice сохраняются;
  для изменённых файлов добавлен явный блок атрибуции.
- **Apache-2.0** (Cowork Roles): сохраняется копия лицензии; вендоренные файлы не изменялись,
  поэтому уведомление об изменениях не требуется. У апстрима файла `NOTICE` нет —
  соответственно, ничего дополнительно переносить не нужно.

Добавляя новый сторонний набор в `skills/`, положите его лицензию в
`THIRD_PARTY_LICENSES/` и допишите строку в таблицу выше.
