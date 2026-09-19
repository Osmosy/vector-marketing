#!/usr/bin/env python3
"""Валидатор SOUL-манифестов агентов Vector Marketing.

Проверяет, что каждый файл в agents/ — корректный SOUL-манифест в формате
Identity → Tools → Format → Rules → Guardrails → Handoff, что перекрёстные
ссылки между агентами разрешаются, а ссылки на навыки ведут на существующие
файлы репозитория.

Запуск:  python3 scripts/validate_agents.py [--repo-root DIR] [--json]
Выход:   0 — всё чисто; 1 — есть ошибки (печатает их список).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

# Обязательные секции SOUL-манифеста (в порядке появления в файле).
REQUIRED_SECTIONS = [
    ("## Инструменты и skills", "tools"),
    ("## Формат выдачи", "format"),
    ("## Правила", "rules"),
    ("# Guardrails", "guardrails"),
    ("# Handoff", "handoff"),
]

# Оба варианта разметки «Формат» — исторически в файлах встречаются оба.
FORMAT_HEADERS = ("## Формат выдачи", "## Формат ответа клиенту")

# H1-заголовок, у которого имя не совпадает с именем файла (легитимное исключение).
IDENTITY_ALIASES = {
    "orchestrator": None,  # заголовок «Osmosy — CMO-оркестратор …», имя не требуется
}

MENTION_RE = re.compile(r"@([a-z0-9][a-z0-9-]*)")
PATHLIKE_PREFIXES = ("skills/", "cowork-roles/", "humblytics-marketing/", "pm-skills/", "open-seo/")
BULLET_RE = re.compile(r"^\s*[-*]\s+\S")

# Наборы, скопированные из чужих репозиториев, обязан нести блок лицензионной
# атрибуции (см. NOTICE.md и THIRD_PARTY_LICENSES/). Список имён не хардкодим:
# новый апстрим, добавленный скриптом, иначе молча выпадал бы из проверки.
ATTRIBUTION_HEADER = "### Attribution"
ATTRIBUTION_SOURCE_MARK = "заимствован из"

# Одиночные вендоренные навыки: по дереву их не отличить от собственных, поэтому
# называем явно. Ошибка в имени валит сборку — молча выпасть из проверки нельзя.
VENDORED_SINGLE = {"open-seo"}

# Слова, похожие на @упоминание агента, но им не являющиеся.
MENTION_EXEMPT = {"mention"}


def plural_ru(n: int, one: str, few: str, many: str) -> str:
    """Русская форма числа: 1 навык / 2 навыка / 5 навыков.

    Без этого валидатор требовал «161 навыков» и «5 навыков» одинаково —
    верная форма в документе считалась расхождением, а неверная проходила.
    """
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def attribution_count(body: str) -> int:
    """Сколько блоков лицензионной атрибуции в SKILL.md."""
    lines = body.splitlines()
    return sum(
        1 for i, line in enumerate(lines)
        if line.strip() == ATTRIBUTION_HEADER
        and ATTRIBUTION_SOURCE_MARK in "\n".join(lines[i:i + 6])
    )


def vendored_sets(repo_root: Path) -> set[str]:
    """Каталоги навыков, скопированные из чужих репозиториев.

    Каталог с двумя и более навыками — вендоренный набор (своих наборов такого
    размера в репозитории нет). Одиночный навык по дереву не отличить от
    собственного, поэтому он попадает сюда только если несёт блок атрибуции или
    прямо назван в VENDORED_SINGLE.
    """
    root = repo_root / "skills"
    vendored: set[str] = set()
    for set_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        skill_files = sorted(set_dir.rglob("SKILL.md"))
        if not skill_files:
            continue
        if len(skill_files) >= 2:
            vendored.add(set_dir.name)
            continue
        if set_dir.name in VENDORED_SINGLE or any(
            attribution_count(f.read_text(encoding="utf-8")) > 0 for f in skill_files
        ):
            vendored.add(set_dir.name)
    return vendored


def bare_skill_names(repo_root: Path) -> dict[str, set[str]]:
    """Имена без пути в секции «Инструменты и skills» — внешние зависимости агента.

    Возвращает {имя: агенты}, исключая имена, которые в этом репозитории
    разрешаются в навык (их копирует build_profiles.py). Такие имена в дистрибутив
    не попадают, поэтому должны быть перечислены в INSTALL.md — иначе агент уедет
    без заявленных инструментов.
    """
    own_slugs = {p.parent.name for p in (repo_root / "skills").rglob("SKILL.md")}
    found: dict[str, set[str]] = {}
    for agent_file in sorted((repo_root / "agents").glob("*.md")):
        text = agent_file.read_text(encoding="utf-8")
        m = re.search(r"^## Инструменты и skills\n(.*?)(?=^#{1,2} )", text, re.S | re.M)
        if not m:
            continue
        for raw in m.group(1).splitlines():
            line = raw.lstrip("-•* ").strip()
            if not line:
                continue
            name = re.split(r"\s+—|\s+-\s|,", line)[0].strip("`* ")
            if not name or "/" in name or name in own_slugs:
                continue
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
                continue
            found.setdefault(name, set()).add(agent_file.stem)
    return found


class AgentDoc:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
        self.lines = text.splitlines()
        self.sections = _split_sections(self.lines)

    def section(self, header: str) -> list[str]:
        return self.sections.get(header, [])


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    """Разбить файл на секции по заголовкам '#'/'##' (без учёта '###')."""
    out: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        if re.match(r"^#{1,2} \S", line):
            current = line.strip()
            out.setdefault(current, [])
        elif current is not None:
            out[current].append(line)
    return out


def _bullets(body: list[str]) -> list[str]:
    return [ln.strip() for ln in body if BULLET_RE.match(ln)]


def validate_agents(repo_root: Path) -> tuple[list[str], list[str]]:
    """Вернуть (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    agents_dir = repo_root / "agents"
    if not agents_dir.is_dir():
        return [f"нет каталога agents/ в {repo_root}"], warnings

    files = sorted(agents_dir.glob("*.md"))
    if not files:
        return ["каталог agents/ пуст"], warnings

    agent_names = {f.stem for f in files}
    docs: dict[str, AgentDoc] = {}

    for path in files:
        name = path.stem
        text = path.read_text(encoding="utf-8")
        doc = AgentDoc(name, text)
        docs[name] = doc

        h1 = next((ln.strip() for ln in doc.lines if ln.startswith("# ")), "")
        if not h1:
            errors.append(f"{name}: нет H1-заголовка (Identity)")
        else:
            title = h1[2:].strip()
            head = title.split("—")[0].strip()
            expected = IDENTITY_ALIASES.get(name, name)
            if expected is not None and head.lower() != expected.lower():
                errors.append(
                    f"{name}: Identity не совпадает с именем файла "
                    f"(заголовок «{title}», ожидалось начало с «{expected}»)"
                )

        if not text.strip():
            errors.append(f"{name}: файл пуст")

        # Обязательные секции: наличие + порядок.
        present: list[tuple[int, str]] = []
        for header, label in REQUIRED_SECTIONS:
            variants = FORMAT_HEADERS if label == "format" else (header,)
            found = next((v for v in variants if v in doc.sections), None)
            if found is None:
                errors.append(f"{name}: отсутствует секция «{header}» ({label})")
                continue
            present.append((doc.lines.index(found), found))
        expected_order = [h for _, h in sorted(present)]
        if present and [h for _, h in present] != expected_order:
            errors.append(
                f"{name}: секции идут не в порядке SOUL "
                f"({' → '.join(h for _, h in present)})"
            )

        # Guardrails / Handoff не должны быть пустыми.
        for header, label in (("# Guardrails", "Guardrails"), ("# Handoff", "Handoff")):
            if header in doc.sections and len(_bullets(doc.section(header))) < 2:
                errors.append(f"{name}: секция {label} содержит меньше двух пунктов")

        # Handoff @mentions разрешаются в существующих агентов.
        for target in sorted(set(MENTION_RE.findall("\n".join(doc.section("# Handoff"))))):
            if target not in agent_names:
                errors.append(
                    f"{name}: Handoff ссылается на @{target}, "
                    f"но агента agents/{target}.md нет"
                )

        # Все @mentions по файлу — тоже проверяем (warning, чтобы не ломать вкусовые упоминания).
        for target in sorted(set(MENTION_RE.findall(text)) - set(MENTION_RE.findall("\n".join(doc.section("# Handoff"))))):
            if target not in agent_names:
                warnings.append(f"{name}: упоминание @{target} вне Handoff — агента нет")

        # Ссылки на навыки, похожие на путь, должны существовать в репозитории.
        for raw_line in doc.section("## Инструменты и skills"):
            line = raw_line.lstrip("-•* ").strip()
            m_ref = re.match(r"^\*{0,2}`?([A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)+)`?\*{0,2}", line)
            if not m_ref:
                continue
            ref = m_ref.group(1).strip("/")
            if ref.startswith("skills/"):
                ref = ref[len("skills/"):]
            rel = PurePosixPath(ref).parts  # may be cowork-roles/<plugin>/<skill> or .../skills/<skill>
            # Сверяем только то, что относится к дереву skills/ этого репозитория.
            repo_sets = {p.name for p in (repo_root / "skills").iterdir() if p.is_dir()}
            if not rel or rel[0] not in repo_sets:
                continue
            candidates = [repo_root / "skills" / ref]
            if len(rel) == 3:  # cowork-roles/<plugin>/<skill> — в репо лежит .../<plugin>/skills/<skill>
                candidates.append(repo_root / "skills" / rel[0] / rel[1] / "skills" / rel[2])
            elif len(rel) == 2:  # cowork-roles/<skill> без плагина — ищем в любом плагине
                candidates += sorted((repo_root / "skills" / rel[0]).glob(f"*/skills/{rel[1]}"))
            if not any(c.is_dir() or c.with_suffix(".md").is_file() for c in candidates):
                errors.append(f"{name}: ссылка на навык «{ref}» не найдена в skills/")

    # README: таблица «## Агенты» должна перечислять ровно те же агенты.
    readme = repo_root / "README.md"
    if readme.is_file():
        md = readme.read_text(encoding="utf-8")
        block = re.search(r"^## Агенты\n(.*?)(?=^## )", md, re.S | re.M)
        if not block:
            warnings.append("README.md: нет секции «## Агенты» — нечего сверять")
        else:
            listed = re.findall(r"^\|\s*`([a-z0-9-]+)`", block.group(1), re.M)
            listed_set = set(listed)
            missing = sorted(agent_names - listed_set)
            extra = sorted(listed_set - agent_names)
            if missing:
                errors.append(f"README: в таблице агентов нет {', '.join(missing)}")
            if extra:
                errors.append(f"README: в таблице агентов лишние {', '.join(extra)}")
            if len(listed) != len(listed_set):
                errors.append("README: дубли в таблице агентов")
        declared = re.search(r"(\d+)\s+профильны", md)
        if declared and int(declared.group(1)) != len(agent_names):
            errors.append(
                f"README: заявлено {declared.group(1)} профильных агентов, "
                f"а в agents/ их {len(agent_names)}"
            )

    # INSTALL.md — документация для внешнего пользователя: она должна оставаться верной.
    install = repo_root / "INSTALL.md"
    if not install.is_file():
        errors.append("нет INSTALL.md — пояснения для внешнего пользователя")
    else:
        doc = install.read_text(encoding="utf-8")
        # 1. Все профили, упомянутые как `hermes profile install ./dist/<x>`, существуют.
        for ref in sorted(set(re.findall(r"\./dist/([a-z0-9-]+)", doc))):
            if ref not in agent_names:
                errors.append(f"INSTALL.md: установка ./dist/{ref}, но агента agents/{ref}.md нет")
        # 2. Таблица «какого агента ставить» перечисляет всех агентов.
        #    Берём именно эту секцию: в разделе про внешние зависимости первый
        #    столбец — тоже имя навыка, и его нельзя путать с агентом.
        section = re.search(
            r"^## Какого агента ставить\n(.*?)(?=^## )", doc, re.S | re.M
        )
        agents_table = section.group(1) if section else ""
        table_rows = set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", agents_table, re.M))
        if table_rows:
            missing = sorted(agent_names - table_rows)
            stale = sorted(table_rows - agent_names)
            if missing:
                errors.append(f"INSTALL.md: в таблице агентов нет {', '.join(missing)}")
            if stale:
                errors.append(f"INSTALL.md: в таблице агентов лишние {', '.join(stale)}")
        # 3. Каждый скрипт, на который ссылается документация, существует.
        for script in sorted(set(re.findall(r"scripts/([A-Za-z0-9_]+\.py)", doc))):
            if not (repo_root / "scripts" / script).is_file():
                errors.append(f"INSTALL.md: ссылка на несуществующий scripts/{script}")
        # 4. Ровно одно утверждение о числе профилей должно сходиться.
        n_declared = re.search(r"Собрать дистрибутивы \((\d+) каталогов", doc)
        if n_declared and int(n_declared.group(1)) != len(agent_names):
            errors.append(
                f"INSTALL.md: заявлено {n_declared.group(1)} каталогов сборки, "
                f"а агентов {len(agent_names)}"
            )

    # Скиллы: у каждого frontmatter с name, совпадающим с именем каталога.
    # Hermes умеет фолбэк на имя каталога, но у нас все скиллы объявляют name явно —
    # расхождение молча ломает привязку скилла к агенту.
    for skill_md in sorted((repo_root / "skills").rglob("SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---", text, re.S)
        rel = skill_md.parent.relative_to(repo_root / "skills")
        if not fm:
            errors.append(f"skills/{rel}: нет YAML-frontmatter")
            continue
        name_m = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
        if not name_m:
            errors.append(f"skills/{rel}: во frontmatter нет поля name")
            continue
        declared = name_m.group(1).strip().strip('"').strip("'")
        if declared != skill_md.parent.name:
            errors.append(
                f"skills/{rel}: name «{declared}» не совпадает с именем каталога "
                f"«{skill_md.parent.name}»"
            )

    # Вендоренные наборы: ровно один блок лицензионной атрибуции на файл.
    # Дубль (склейка двух импортов) и пропуск (копия без уведомления) — обе ошибки:
    # у пользователя, который возьмёт один скилл, не будет ни NOTICE.md, ни текста лицензии.
    vendored = vendored_sets(repo_root)
    for set_dir in sorted(p for p in (repo_root / "skills").iterdir() if p.is_dir()):
        for skill_md in sorted(set_dir.rglob("SKILL.md")):
            body = skill_md.read_text(encoding="utf-8")
            rel = skill_md.relative_to(repo_root / "skills")
            notices = attribution_count(body)
            if notices > 1:
                errors.append(
                    f"skills/{rel}: блоков лицензионной атрибуции {notices} — должен быть один"
                )
            elif notices == 0 and set_dir.name in vendored:
                errors.append(
                    f"skills/{rel}: нет блока «### Attribution» — вендоренный скилл без уведомления"
                )

    # Документация и артефакты не должны разойтись с фактическим составом:
    # числа живут в README, деке и диаграмме, и все они обязаны совпадать с деревом.
    n_agents = len(agent_names)
    n_skills = len(list((repo_root / "skills").rglob("SKILL.md")))
    n_pm = len(list((repo_root / "skills" / "pm-skills").glob("*/SKILL.md"))) if (repo_root / "skills" / "pm-skills").is_dir() else 0
    n_brain = len(list((repo_root / "company-brain").glob("*.md"))) if (repo_root / "company-brain").is_dir() else 0

    artifacts = {
        "README.md": repo_root / "README.md",
        "deck/deck-marketing.py": repo_root / "deck" / "deck-marketing.py",
        "agent-description.md": repo_root / "agent-description.md",
    }
    # Для каждого артефакта — обязательные числа (регуляркой, чтобы не ловить лишнее).
    required_numbers = {
        "README.md": {
            "agents": [f"Agents-{n_agents}", f"#агенты"],
            "skills": [f"Skills-{n_skills}"],
            "pm": [f"{n_pm} методических"],
            "brain": [f"Brain-{n_brain}%20files"],
        },
        "deck/deck-marketing.py": {
            "agents": [f"('{n_agents}', 'агентов')"],
            "skills": [f"('{n_skills}', 'навыков')"],
            "pm": [f"('{n_pm}', 'PM-методик')", f"{n_pm} PM-скиллов"],
        },
        "agent-description.md": {
            "agents": [f"{n_agents} {plural_ru(n_agents, 'агент', 'агента', 'агентов')}"],
            "skills": [f"{n_skills} {plural_ru(n_skills, 'навык', 'навыка', 'навыков')}"],
        },
    }
    for label, path in artifacts.items():
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        for kind, needles in required_numbers.get(label, {}).items():
            if not any(n in body for n in needles):
                errors.append(
                    f"{label}: нет актуального числа для «{kind}» "
                    f"(ждали одно из {needles})"
                )

    # Диаграмма: подпись библиотеки навыков и число PM-методик во вью.
    diag = repo_root / "docs" / "vector-marketing.architecture.json"
    if diag.is_file():
        body = diag.read_text(encoding="utf-8")
        expected_skills = f"{n_skills} {plural_ru(n_skills, 'скилл', 'скилла', 'скиллов')}"
        if expected_skills not in body:
            errors.append(f"диаграмма: нет подписи «{expected_skills}»")
        if f"{n_pm} PM-скиллов" not in body:
            errors.append(f"диаграмма: нет «{n_pm} PM-скиллов» во вью")

    # Числа по наборам навыков: суммарные счётчики проверялись выше, а построчные
    # в таблице README — нет, из-за чего рассинхрон по одному набору проходил CI.
    readme_path = repo_root / "README.md"
    if readme_path.is_file():
        md = readme_path.read_text(encoding="utf-8")
        for set_dir in sorted(p for p in (repo_root / "skills").iterdir() if p.is_dir()):
            actual = len(list(set_dir.rglob("SKILL.md")))
            claim = re.search(rf"\|\s*`{re.escape(set_dir.name)}/`\s*\|\s*(\d+)\s*\|", md)
            if claim and int(claim.group(1)) != actual:
                errors.append(
                    f"README: у набора «{set_dir.name}» заявлено {claim.group(1)} скиллов, "
                    f"а в дереве их {actual}"
                )
        # Вендоренная часть библиотеки: производное от тех же чисел.
        n_vendored = sum(
            len(list((repo_root / "skills" / s).rglob("SKILL.md")))
            for s in sorted(vendored_sets(repo_root))
        )
        n_own = n_skills - n_vendored
        for pattern, kind in (
            (rf"{n_vendored} из сторонних наборов", "вендоренных скиллов"),
            (rf"и {n_own} собственных", "собственных скиллов"),
        ):
            if not re.search(pattern, md):
                errors.append(f"README: нет актуального числа для «{kind}» (ждали «{pattern}»)")
        # Имена, не закреплённые ни за одним агентом, названы прямо: иначе читатель
        # считает, что все навыки дерева попадают в профили. Незакреплённое «по замыслу»
        # перечислено в UNASSIGNED_BY_DESIGN — новый навык без привязки валит сборку.
        unassigned = n_skills - len(attached_skills(repo_root))
        if unassigned > 0 and "не вкладываются" not in md:
            errors.append(
                f"README: не сказано, что {unassigned} навыков не попадают ни в один профиль"
            )
        declared_unassigned = re.search(r"остальные (\d+)\s*\(", md)
        if declared_unassigned and int(declared_unassigned.group(1)) != unassigned:
            errors.append(
                f"README: заявлено {declared_unassigned.group(1)} незакреплённых навыков, "
                f"а фактически {unassigned}"
            )

    # Таблица «Ключевые skills» в profiles/README.md должна совпадать с реальной
    # выдачей сборки — иначе обещание профиля расходится с дистрибутивом.
    profiles_readme = repo_root / "profiles" / "README.md"
    if profiles_readme.is_file():
        pr = profiles_readme.read_text(encoding="utf-8")
        by_agent = attached_by_agent(repo_root)
        for line in pr.splitlines():
            m_row = re.match(r"\|\s*`?([a-z0-9-]+)`?\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", line)
            if not m_row or m_row.group(1) not in agent_names:
                continue
            have = by_agent.get(m_row.group(1), set())
            claimed_cell = m_row.group(2).strip()
            # «внешние: …» — не навыки этого репозитория, они проверяются по INSTALL.md.
            # Часть ячейки до этого маркера сверяем, часть после — нет.
            claimed_cell = re.split(r"\bвнешние\s*:", claimed_cell)[0]
            # «**заготовка** —» — статус профиля, а не имя навыка.
            claimed_cell = re.sub(r"\*\*заготовка\*\*\s*—?", "", claimed_cell)
            if not claimed_cell.strip():
                continue
            # Скобочные пояснения («(11: ai-visibility, …)») — для читателя, не для
            # сверки: убираем их до разбора списка, иначе их содержимое летит в проверку.
            claimed_cell = re.sub(r"\([^)]*\)", "", claimed_cell)
            claimed = {c.strip(" `*;:,") for c in claimed_cell.split(",") if c.strip(" `*;:,")}
            absent = []
            for c in sorted(claimed):
                if c.endswith("*"):
                    # «linkedin-*» — группа навыков: проверяем префикс.
                    if not any(n.startswith(c[:-1]) for n in have):
                        absent.append(c)
                elif c not in have:
                    absent.append(c)
            if absent:
                errors.append(
                    f"profiles/README.md: у «{m_row.group(1)}» указаны навыки, "
                    f"которых сборка не вкладывает — {', '.join(absent)}"
                )

    # Примеры в workflows/ ссылаются на агентов так же, как SOUL-файлы: @mention и
    # delegate_task → <агент>. Раньше пример звал pr и outbound, которых нет.
    workflows_dir = repo_root / "workflows"
    if workflows_dir.is_dir():
        for wf in sorted(workflows_dir.glob("*.md")):
            body = wf.read_text(encoding="utf-8")
            for target in sorted(set(MENTION_RE.findall(body))):
                if target not in agent_names and target not in MENTION_EXEMPT:
                    errors.append(
                        f"workflows/{wf.name}: @{target} — агента agents/{target}.md нет"
                    )
            for target in sorted(set(re.findall(r"delegate_task\s*→\s*([a-z0-9-]+)", body))):
                if target not in agent_names:
                    errors.append(
                        f"workflows/{wf.name}: delegate_task → {target} — "
                        f"агента agents/{target}.md нет"
                    )

    # NOTICE.md — лицензионный документ: он не должен противоречить дереву.
    notice_path = repo_root / "NOTICE.md"
    if notice_path.is_file():
        notice = notice_path.read_text(encoding="utf-8")
        for set_dir in sorted(p for p in (repo_root / "skills").iterdir() if p.is_dir()):
            # Собственные одиночные навыки в таблицу апстримов не входят.
            if set_dir.name not in vendored_sets(repo_root):
                continue
            if f"`{set_dir.name}/`" not in notice:
                errors.append(
                    f"NOTICE.md: вендоренный набор «{set_dir.name}» не упомянут "
                    f"в таблице атрибуции"
                )

    # Внешние зависимости агентов должны быть перечислены в INSTALL.md: они не
    # попадают в дистрибутив, и без этой таблицы профиль уезжает без инструментов.
    install_path = repo_root / "INSTALL.md"
    if install_path.is_file():
        install_body = install_path.read_text(encoding="utf-8")
        for name, agents in sorted(bare_skill_names(repo_root).items()):
            if f"`{name}`" not in install_body:
                errors.append(
                    f"INSTALL.md: внешняя зависимость «{name}» "
                    f"(её зовут: {', '.join(sorted(agents))}) не описана"
                )

    return errors, warnings


def attached_by_agent(repo_root: Path) -> dict[str, list[str]]:
    """Что сборка вложит каждому агенту: {агент: [имена навыков]}.

    Список, а не множество: по нему видно коллизию, когда два навыка из разных
    наборов приносят одно `name` в один профиль (тогда один из них недоступен).
    Считается логикой `build_profiles.py`, а не содержимым `dist/`: в CI валидация
    идёт до сборки, и проверка по каталогу артефакта молча не выполнялась бы.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_build_profiles_for_check", repo_root / "scripts" / "build_profiles.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover — повреждённый скрипт
        return {}
    bp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bp)

    result: dict[str, list[str]] = {}
    for agent_file in sorted((repo_root / "agents").glob("*.md")):
        names: list[str] = []
        text = agent_file.read_text(encoding="utf-8")
        for ref in bp.skill_roots(text, repo_root):
            resolved = bp.resolve_skill(repo_root, ref)
            if resolved is not None:
                names.append(resolved.name)
        result[agent_file.stem] = names
    return result


def attached_skills(repo_root: Path) -> set[str]:
    """Уникальные навыки из дерева `skills/`, которые сборка вкладывает хоть кому-то.

    Считаем по логике сборки, а не по числу вложений в `dist/`: один навык,
    привязанный к трём агентам, — это три вложения, но один уникальный навык.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_build_profiles_for_check", repo_root / "scripts" / "build_profiles.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover — повреждённый скрипт
        return set()
    bp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bp)

    attached: set[str] = set()
    for agent_file in sorted((repo_root / "agents").glob("*.md")):
        text = agent_file.read_text(encoding="utf-8")
        for ref in bp.skill_roots(text, repo_root):
            resolved = bp.resolve_skill(repo_root, ref)
            if resolved is not None and (repo_root / "skills") in resolved.parents:
                attached.add(str(resolved.relative_to(repo_root / "skills")))
    return attached


def _check_unassigned(repo_root: Path, errors: list[str]) -> None:
    """Каждый навык либо попадает к агенту, либо объяснён как незакреплённый.

    Новый навык, к которому не привязан ни один агент, — это либо забытая привязка,
    либо осознанное решение; и то и другое должно быть видно явно.
    """
    attached = attached_skills(repo_root)
    all_skills = {
        str(p.parent.relative_to(repo_root / "skills"))
        for p in (repo_root / "skills").rglob("SKILL.md")
    }
    for rel in sorted(all_skills - attached):
        if rel.split("/")[0] in UNASSIGNED_BY_DESIGN:
            continue
        errors.append(
            f"skills/{rel}: навык не привязан ни к одному агенту и не помечен как "
            f"незакреплённый — добавьте ссылку агенту или внесите набор в UNASSIGNED_BY_DESIGN"
        )


def _check_name_collisions(repo_root: Path, errors: list[str]) -> None:
    """Один навык = одно имя внутри дистрибутива.

    Hermes адресует навык по имени из frontmatter, поэтому два навыка с одинаковым
    `name` в одном профиле делают один из них недоступным: он остаётся в дереве,
    но не выбирается агентом. Проверяем на том, что реально вкладывает сборка.
    """
    by_agent = attached_by_agent(repo_root)
    for agent, names in sorted(by_agent.items()):
        if len(names) != len(set(names)):
            errors.append(f"{agent}: дубли имён навыков в дистрибутиве")
    # Одно и то же имя из разных наборов, попавшее разным агентам, — норма;
    # проблема только внутри одного профиля, её и ловим выше.


def _check_stub_markers(repo_root: Path, errors: list[str]) -> None:
    """Пометка «заготовка» должна совпадать с фактом.

    Заготовка = профиль, которому сборка не вкладывает ни одного навыка репозитория.
    Если такому агенту навык привяжут (или наоборот — у работающего профиля не останется
    ни одного), статус в README/INSTALL/profiles обязан измениться вместе с ним, иначе
    читатель поверит надписи, а не дереву.
    """
    by_agent = attached_by_agent(repo_root)
    marked: set[str] = set()
    for rel in ("README.md", "INSTALL.md", "profiles/README.md"):
        path = repo_root / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "заготовка" not in line:
                continue
            for name in re.findall(r"`([a-z0-9-]+)`", line):
                if name in by_agent:
                    marked.add(name)

    for name in sorted(marked):
        if by_agent[name]:
            errors.append(
                f"{name}: помечен «заготовкой», но сборка вкладывает ему "
                f"{len(by_agent[name])} навык(ов) — обновите статус в документации"
            )
    # Агент без навыков и без пометки — тоже расхождение: он едет пустым молча.
    for name, skills in sorted(by_agent.items()):
        if not skills and name not in marked:
            errors.append(
                f"{name}: профиль без навыков, но не помечен «заготовкой» ни в README, "
                f"ни в INSTALL, ни в profiles/README"
            )


def _check_vendored_single(repo_root: Path, errors: list[str]) -> None:
    """Имена из VENDORED_SINGLE должны существовать: опечатка не должна прятать набор."""
    for name in sorted(VENDORED_SINGLE):
        if not (repo_root / "skills" / name / "SKILL.md").is_file():
            errors.append(
                f"VENDORED_SINGLE: навыка «skills/{name}» нет — правило атрибуции "
                f"молча не применяется"
            )


# Названия наборов/навыков, намеренно не привязанные ни к одному агенту, чтобы факт
# «есть в дереве, но не в дистрибутиве» не выглядел пропуском в привязке.
UNASSIGNED_BY_DESIGN = {
    # наборы целиком
    "github-repo-research", "vector-github-design", "timesfm-marketing",
    # вендоренные наборы, у которых привязана часть навыков
    "humblytics-marketing", "searchfit-seo", "pm-skills", "cowork-roles",
    # одиночные навыки
    "open-seo",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидация SOUL-манифестов агентов")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--json", action="store_true", help="вывести результат в JSON")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors, warnings = validate_agents(repo_root)
    _check_vendored_single(repo_root, errors)
    _check_unassigned(repo_root, errors)
    _check_name_collisions(repo_root, errors)
    _check_stub_markers(repo_root, errors)

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}")
        print(
            f"\nИтог: ошибок {len(errors)}, предупреждений {len(warnings)}, "
            f"агентов проверено: {len(list((repo_root / 'agents').glob('*.md')))}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
