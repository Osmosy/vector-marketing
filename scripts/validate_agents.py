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
        table_rows = set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", doc, re.M))
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

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Валидация SOUL-манифестов агентов")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--json", action="store_true", help="вывести результат в JSON")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors, warnings = validate_agents(repo_root)

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
