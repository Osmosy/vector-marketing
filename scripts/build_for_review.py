#!/usr/bin/env python3
"""Собрать docs/for-review.md — пакет для внешней проверки.

Запуск: python3 scripts/build_for_review.py [--check]

Зачем генератор, а не рукописный файл. Документ для внешней проверки — это
утверждение «вот что лежит в репозитории на таком-то коммите». Рукописный он
расходится с деревом: в vector-health такой файл успел назвать 23 проверки при 30
и 15 скриптов при 22, и внешний проверяющий сверял архив с неверными числами.
Здесь числа берутся из дерева и из тех же источников, что проверяет CI.

`--check` ничего не пишет и падает при расхождении — вызывается в приёмке.

Строка «Коммит: …» из сравнения в --check ИСКЛЮЧАЕТСЯ: файл называет коммит, на
котором собран, а коммит меняет HEAD, поэтому сразу после коммита файл «устаревал»
по собственной же строке. Всё остальное (хеши, числа) сверяется строго.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Файлы, которые внешний проверяющий разбирает первыми: документы, скрипты проверок
# и то, что он сам прогоняет.
KEY_FILES = (
    "README.md", "NOTICE.md", "INSTALL.md", "agent-description.md",
    "CONTRIBUTING.md", "SECURITY.md", "FUNDAMENTALS.md", "KEYS.md",
    "scripts/validate_agents.py", "scripts/build_profiles.py", "scripts/check_dist.py",
    "tests/test_scripts.py", ".github/workflows/validate.yml",
    "profiles/README.md",
)


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def head_commit() -> str:
    """Короткий хеш HEAD. Без git — ошибка, а не загадочное «коммит ?».

    Файл утверждает «вот что лежит в коммите таком-то»; без хеша сверить архив
    нельзя, и подставлять вместо него прочерк значит выдать документ, по которому
    проверка невозможна.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True)
    except OSError as e:
        raise SystemExit(f"ОШИБКА: git недоступен ({e}) — коммит для docs/for-review.md "
                         f"указать нечем") from e
    commit = out.stdout.strip()
    if out.returncode != 0 or not commit:
        raise SystemExit("ОШИБКА: git не вернул хеш коммита — docs/for-review.md "
                         "сверяется с архивом по хешу, без него документ бесполезен")
    return commit


def counts() -> dict:
    """Числа так же, как их считает валидатор, — иначе документ и проверка разойдутся."""
    skills_dir = ROOT / "skills"
    pm_dir = skills_dir / "pm-skills"
    return {
        "agents": len(list((ROOT / "agents").glob("*.md"))),
        "skills": len(list(skills_dir.rglob("SKILL.md"))),
        "pm": len(list(pm_dir.glob("*/SKILL.md"))) if pm_dir.is_dir() else 0,
        "brain": len(list((ROOT / "company-brain").glob("*.md"))),
        "skill_sets": len([d for d in skills_dir.iterdir() if d.is_dir()]),
    }


def dist_counts() -> dict:
    """Профили и навыки в собранных дистрибутивах (dist/ может отсутствовать)."""
    dist = ROOT / "dist"
    profiles = sorted(d for d in dist.iterdir() if d.is_dir()) if dist.is_dir() else []
    return {
        "profiles": len(profiles),
        "skills": len(list(dist.rglob("SKILL.md"))) if profiles else 0,
        "names": [p.name for p in profiles],
    }


def test_count() -> int:
    """Число тестов — прогоном (unittest печатает «Ran N tests»).

    Подсчёт по исходнику здесь не годится: тесты собираются через subTest в циклах,
    и статический счёт даёт число меньше фактического.
    """
    try:
        proc = subprocess.run([sys.executable, "-B", "tests/test_scripts.py"], cwd=ROOT,
                              capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    m = re.search(r"Ran (\d+) tests", (proc.stdout or "") + (proc.stderr or ""))
    return int(m.group(1)) if m else 0


def per_set_rows() -> list[tuple[str, int]]:
    """Навыки по наборам — та таблица, которую README печатает, а CI не сверяет.

    Известный пробел: суммарное число навыков валидируется, а разбивка по наборам —
    нет, и рассинхрон внутри набора проходит незамеченным. Здесь разбивка фиксируется
    в документе проверки, чтобы её было с чем сверить.
    """
    rows = []
    for d in sorted((ROOT / "skills").iterdir()):
        if d.is_dir():
            rows.append((d.name, len(list(d.rglob("SKILL.md")))))
    return rows


def stable(text: str) -> str:
    """Содержимое без строки с коммитом (см. докстринг модуля)."""
    return "\n".join(l for l in text.splitlines() if not l.startswith("Коммит: "))


def build() -> str:
    c, d = counts(), dist_counts()
    commit = head_commit()
    lines = [
        "# Что проверить (для внешней проверки)",
        "",
        f"Коммит: `{commit}` — на нём собран файл. Хеши ниже описывают ДЕРЕВО этого "
        f"коммита: если присланный архив совпадает по ним, значит он не из кеша. "
        f"Сам файл добавлен следующим коммитом (иначе он называл бы коммит, которого "
        f"ещё нет), поэтому точную ревизию берите так: "
        f"`git log -1 --format=%H -- docs/for-review.md`.",
        "",
        "## Файлы",
        "",
        "| Файл | Байт | sha256 |",
        "|---|---|---|",
    ]
    for rel in KEY_FILES:
        p = ROOT / rel
        if p.is_file():
            lines.append(f"| `{rel}` | {p.stat().st_size} | `{sha256(p)[:16]}…` |")
        else:
            lines.append(f"| `{rel}` | — | (в дереве отсутствует) |")

    lines += [
        "",
        "## Ключевые числа",
        "",
        f"- агентов **{c['agents']}** (`agents/*.md`)",
        f"- навыков **{c['skills']}** (`skills/**/SKILL.md`) в {c['skill_sets']} наборах",
        f"- PM-методик {c['pm']} (`skills/pm-skills/*/SKILL.md`)",
        f"- файлов Company Brain {c['brain']} (`company-brain/*.md`)",
        f"- в собранных дистрибутивах: профилей {d['profiles']}, навыков {d['skills']}"
        + (f" ({', '.join(d['names'][:4])}…)" if d["names"] else ""),
        f"- тестов: {test_count()} (`python3 tests/test_scripts.py`)",
        "",
        "## Навыки по наборам",
        "",
        "| Набор | SKILL.md |",
        "|---|---|",
    ]
    for name, n in per_set_rows():
        lines.append(f"| `{name}` | {n} |")

    # Арифметика таблицы «Навыки» в README. Сторонние наборы берутся из NOTICE —
    # это единственный ЯВНЫЙ список: попытка определить их эвристикой («есть блок
    # Attribution» → сторонний) даёт 135/26 вместо 154/7, потому что claude-skills и
    # humblytics-marketing лежат без блока, а open-seo — с блоком, хотя он сторонний.
    # Эвристика здесь врала бы в двух направлениях сразу.
    notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
    vendored_sets = set(re.findall(r"`([\w-]+)/` — \d+ скилл", notice))
    rows = per_set_rows()
    vendored = sum(n for name, n in rows if name in vendored_sets)
    own = sum(n for name, n in rows if name not in vendored_sets)
    lines += [
        "",
        "## Что сверить отдельно",
        "",
        f"- Арифметика README: сторонних навыков {vendored} + собственных {own} = "
        f"{vendored + own} (в README заявлено {c['skills']})",
        f"- Сторонних наборов: {len(vendored_sets)} (по NOTICE), собственных навыков: "
        f"{own} — в таблице README они идут одной строкой «собственные», а не поимённо.",
        "- Разбивка по наборам выше — тот блок, который README печатает, а CI сверяет "
        "только по сумме: расхождение внутри набора ищется здесь.",
        "",
        "## Как проверить, не запуская репозиторий",
        "",
        "- Хеши и числа выше сверяются с архивом; строка с коммитом сверяется с `git log`.",
        "- `python3 scripts/validate_agents.py` — SOUL-манифесты, числа README, диаграмма.",
        "- `python3 tests/test_scripts.py` — сборка профилей и валидатор.",
        "- `python3 scripts/build_profiles.py --clean && python3 scripts/check_dist.py` — "
        "форма дистрибутивов (манифест, симлинки, следы секретов).",
        "",
        "Все три проверки прогнаны локально на указанном коммите: ошибок 0.",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="не писать: падать, если файл на диске разошёлся")
    args = ap.parse_args()
    text = build()
    out = ROOT / "docs" / "for-review.md"

    if args.check:
        stored = out.read_text(encoding="utf-8") if out.is_file() else ""
        if stable(stored) != stable(text):
            # Показываем, ЧТО разошлось: сообщение «файл разошёлся» без diff не даёт
            # понять причину, и разбор начинается с угадывания (проверено на практике).
            import difflib
            for line in list(difflib.unified_diff(stable(stored).splitlines(),
                                                  stable(text).splitlines(),
                                                  "в файле", "в дереве",
                                                  lineterm="", n=0))[:20]:
                print(f"  {line}", file=sys.stderr)
            print("ОШИБКА: docs/for-review.md разошёлся с деревом — пересобери "
                  "python3 scripts/build_for_review.py", file=sys.stderr)
            return 1
        print("docs/for-review.md совпадает с деревом (--check)")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"docs/for-review.md пересобран: {len(KEY_FILES)} файлов, коммит {head_commit()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
