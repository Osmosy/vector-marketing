#!/usr/bin/env python3
"""Целостность набора скилл-эвалов: сценарии, критерии, привязка к навыкам.

Сами эвалы судит модель или человек (в CI её нет), поэтому скрипт проверяет то, что проверить
можно машинно, и печатает набор для прогона:

  * у сценария есть prompt.md с frontmatter (tags, runs) и непустым телом;
  * в tags названы существующие навыки репозитория;
  * есть хотя бы один файл критериев в graders/;
  * в критериях есть правило отказа (No-Go / не выдумывать / не отправлять), а не только «текст
    хороший».

Коды выхода: 0 — набор цел, 1 — находки, 2 — нет каталога эвалов.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "tests" / "skill-evals"
SKILLS = ROOT / "skills"

# Хотя бы одно из слов должно быть в критериях: иначе эвал проверяет стиль, а не поведение.
BEHAVIOUR_MARKS = ("no-go", "не выдум", "не отправ", "отказ", "не сочин", "refus", "must not")


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() and value.strip():
            data[key.strip()] = value.strip()
    return data


def skill_exists(name: str) -> bool:
    return any(SKILLS.rglob(f"{name}/SKILL.md"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="только перечислить сценарии")
    args = parser.parse_args()

    if not EVALS.is_dir():
        print(f"нет каталога {EVALS.relative_to(ROOT)}", file=sys.stderr)
        return 2

    cases = sorted(p for p in EVALS.iterdir() if p.is_dir())
    problems: list[str] = []
    for case in cases:
        prompt = case / "prompt.md"
        if not prompt.is_file():
            problems.append(f"{case.name}: нет prompt.md")
            continue
        text = prompt.read_text(encoding="utf-8")
        meta = frontmatter(text)
        body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S).strip()
        if not body:
            problems.append(f"{case.name}: пустое тело промпта")
        tags = [t.strip() for t in meta.get("tags", "[]").strip("[]").split(",") if t.strip()]
        if not tags:
            problems.append(f"{case.name}: в frontmatter нет tags")
        for tag in tags:
            if not skill_exists(tag):
                problems.append(f"{case.name}: tag «{tag}» не соответствует навыку в skills/")
        graders = sorted((case / "graders").glob("*.md")) if (case / "graders").is_dir() else []
        if not graders:
            problems.append(f"{case.name}: нет критериев в graders/")
            continue
        joined = "\n".join(g.read_text(encoding="utf-8").lower() for g in graders)
        # Критерий поведения — либо файл с именем-запретом (no-…, refuses-…), либо явная
        # формулировка отказа в тексте. Стилевые критерии («текст хороший») не считаются.
        named = any(g.name.startswith(("no-", "refuses-")) for g in graders)
        if not named and not any(mark in joined for mark in BEHAVIOUR_MARKS):
            problems.append(f"{case.name}: критерии проверяют стиль, а не отказ "
                            f"(нужен файл no-…/refuses-… или явный запрет в тексте)")

    if args.list:
        for case in cases:
            print(case.name)
        return 0

    for problem in problems:
        print(f"находка: {problem}")
    print(f"сценариев: {len(cases)}, находок: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
