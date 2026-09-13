# vector-marketing — часть экосистемы Vector

Маркетинговое AI-агентство на базе Hermes Agent: 19 агентов (18 профильных +
оркестратор Osmosy), 158 навыков, 7 файлов общего контекста (Company Brain).

Содержание — не программа, а исходники агентов: из `agents/*.md`, `company-brain/`
и `skills/` собираются дистрибутивы Hermes-профилей, которые ставятся командой
`hermes profile install`.

## Связанные проекты

- Хаб экосистемы: https://github.com/Osmosy/vector-work
- Методология: https://github.com/Osmosy/vector-agent-ready
- Прогноз спроса: https://github.com/Osmosy/vector-prediction

## Для агентов

- Читай сначала `README.md`, для установки — `INSTALL.md`
- Роли — `agents/*.md` (SOUL-формат: Identity → Tools → Format → Rules → Guardrails → Handoff)
- Навыки — `skills/` (158; вендоренные наборы с атрибуцией в `NOTICE.md`)
- Контекст — `company-brain/`
- Передача задач — `workflows/handoff-protocol.md`
- Перед коммитом прогони проверки: `python3 scripts/validate_agents.py`,
  `python3 scripts/build_profiles.py --clean`, `python3 scripts/check_dist.py`
  (то же выполняет CI в `.github/workflows/validate.yml`)

## Состав

| Что | Сколько |
|-----|---------|
| Агенты | 19 (`agents/`) |
| Навыки | 158 (`skills/`), из них 153 из сторонних наборов |
| Company Brain | 7 файлов (`company-brain/`) |
| Профили в сборке | 19 (`dist/`, генерируется) |
