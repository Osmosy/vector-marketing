#!/usr/bin/env python3
"""Генератор Hermes-профилей агентов Vector Marketing.

Собирает distribution-дерево (manifest + SOUL.md + skills/) для каждого агента
из agents/*.md и company-brain/, из которого профиль ставится одной командой:

    hermes profile install github.com/Osmosy/vector-marketing#subdirectory=dist/seo --alias

или из локальной копии репозитория:

    hermes profile install ./dist/seo --alias

Запуск:  python3 scripts/build_profiles.py [--out dist] [--agents a,b] [--clean]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent

# Блоки, которые копируются в профиль вместе с SOUL агента.
BRAIN_FILES = (
    "brand-voice.md",
    "anti-slop-rules.md",
    "strategy.md",
    "past-campaigns.md",
    "offers-positioning.md",
    "channels-geo.md",
    "media-list.md",
)

IDENTITY_RE = re.compile(r"^# (.+)$", re.M)


def agent_identity(name: str, text: str) -> str:
    m = IDENTITY_RE.search(text)
    if not m:
        return name
    title = m.group(1).strip()
    return title.split("—")[0].strip() or name


def skill_roots(text: str) -> list[str]:
    """Профильные ссылки на навыки из секции «Инструменты и skills»."""
    m = re.search(r"^## Инструменты и skills\n(.*?)(?=^#{1,2} )", text, re.S | re.M)
    if not m:
        return []
    roots: list[str] = []
    for raw in m.group(1).splitlines():
        line = raw.lstrip("-•* ").strip()
        ref = re.match(r"^\*{0,2}`?([A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)+)", line)
        if not ref:
            continue
        r = ref.group(1).strip("/")
        if r.startswith("skills/"):
            r = r[len("skills/"):]
        if not r.startswith(("cowork-roles", "humblytics-marketing", "pm-skills", "open-seo")):
            continue
        if r not in roots:
            roots.append(r)
    return roots


def resolve_skill(repo_root: Path, ref: str) -> Path | None:
    """Найти каталог навыка по ссылке агента (с учётом реального дерева skills/)."""
    base = repo_root / "skills"
    parts = PurePosixPath(ref).parts
    cand = base / ref
    if cand.is_dir():
        return cand
    if len(parts) == 3:  # cowork-roles/<plugin>/<skill> → cowork-roles/<plugin>/skills/<skill>
        alt = base / parts[0] / parts[1] / "skills" / parts[2]
        if alt.is_dir():
            return alt
    if len(parts) == 2:  # cowork-roles/<skill> — ищем в любом плагине
        hits = sorted(base.glob(f"{parts[0]}/*/skills/{parts[1]}"))
        if hits:
            return hits[0]
    if cand.with_suffix(".md").is_file():  # скилл-файл (vector-work.md)
        return cand.with_suffix(".md")
    return None


def build_one(repo_root: Path, out_root: Path, agent_file: Path, brain_dir: Path) -> tuple[str, int, list[str]]:
    """Собрать dist/<agent>/; вернуть (имя, число навыков, проблемы)."""
    name = agent_file.stem
    text = agent_file.read_text(encoding="utf-8")
    problems: list[str] = []

    target = out_root / name
    if target.exists():
        shutil.rmtree(target)
    (target / "skills").mkdir(parents=True)

    identity = agent_identity(name, text)
    soul = [
        text.rstrip(),
        "",
        "## Общий контекст агентства",
        "",
        "Контекст лежит в каталоге `brain/` внутри этого профиля — читай его перед работой:",
        "",
    ]
    soul += [f"- `brain/{f}`" for f in BRAIN_FILES]
    soul += [
        "",
        "Это общий контекст всех агентов агентства (голос бренда, правила anti-slop, "
        "стратегия, офферы, каналы, медиа-лист). Заполняется под конкретный бизнес — "
        "если файл содержит плейсхолдеры `[...]`, запроси данные у клиента, не додумывай.",
        "",
    ]
    (target / "SOUL.md").write_text("\n".join(soul), encoding="utf-8")

    brain_dst = target / "brain"
    brain_dst.mkdir()
    copied_brain = 0
    for fname in BRAIN_FILES:
        src = brain_dir / fname
        if src.is_file():
            shutil.copy2(src, brain_dst / fname)
            copied_brain += 1
        else:
            problems.append(f"нет company-brain/{fname}")

    refs = skill_roots(text)
    copied = 0
    for ref in refs:
        src = resolve_skill(repo_root, ref)
        if src is None:
            problems.append(f"навык не найден: {ref}")
            continue
        dst = target / "skills" / Path(ref)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst / "SKILL.md")
        copied += 1

    version_note = (
        f"Агент «{identity}» маркетингового агентства Vector Marketing.\n"
        f"SOUL — из agents/{agent_file.name}, навыки — из skills/ репозитория, "
        f"контекст — из company-brain/.\n"
    )
    (target / "README.md").write_text(version_note, encoding="utf-8")

    manifest = [
        f"name: {name}",
        "version: 1.0.0",
        f'description: "Vector Marketing — агент {name} ({identity})"',
        'author: "Osmosy"',
        'license: "MIT"',
        "env_requires:",
        "  - name: DEEPSEEK_API_KEY",
        '    description: "Ключ модели (пример: DeepSeek)"',
        "    required: true",
        "  - name: HERMES_GATEWAY_TOKEN",
        '    description: "Токен мессенджер-канала (нужен только для gateway)"',
        "    required: false",
    ]
    (target / "distribution.yaml").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    (target / ".gitignore").write_text(
        "# Рабочий слой профиля — в git не нужен\n"
        "brain/local/\n"
        ".env\n"
        ".env.EXAMPLE\n",
        encoding="utf-8",
    )
    return name, copied, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Сборка Hermes-профилей агентов Vector Marketing")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--out", default="dist", help="каталог вывода (по умолчанию dist/)")
    ap.add_argument("--agents", default="", help="список агентов через запятую (по умолчанию все)")
    ap.add_argument("--clean", action="store_true", help="удалить каталог вывода перед сборкой")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = (repo_root / args.out).resolve()
    agents_dir = repo_root / "agents"
    brain_dir = repo_root / "company-brain"

    if args.clean and out_root.exists():
        shutil.rmtree(out_root)

    wanted = {a.strip() for a in args.agents.split(",") if a.strip()}
    files = sorted(agents_dir.glob("*.md"))
    if wanted:
        files = [f for f in files if f.stem in wanted]
        missing = wanted - {f.stem for f in files}
        if missing:
            print(f"нет таких агентов: {', '.join(sorted(missing))}")
            return 1
    if not files:
        print("нечего собирать: agents/*.md не найдены")
        return 1

    total_skills = 0
    all_problems: list[str] = []
    for f in files:
        name, copied, problems = build_one(repo_root, out_root, f, brain_dir)
        total_skills += copied
        all_problems += [f"{name}: {p}" for p in problems]
        print(f"  dist/{name:16s} навыков: {copied:2d}  SOUL: {len(f.read_text(encoding='utf-8'))} симв.")

    print(f"\nСобрано профилей: {len(files)}, вложено навыков: {total_skills}, вывод: {out_root}")
    if all_problems:
        print("Проблемы:")
        for p in all_problems:
            print(f"  {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
