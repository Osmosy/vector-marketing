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


def write_sums() -> pathlib.Path:
    """docs/SHA256SUMS — полные хеши файлов набора, пригодные для `sha256sum -c`.

    В таблице for-review хеши усечены до 16 символов: этого хватает на глаз, но
    проверить ими нельзя. Файл контрольных сумм — то, чем проверяющий реально
    сверяет архив одной командой.
    """
    out = ROOT / "docs" / "SHA256SUMS"
    rows = []
    for rel in KEY_FILES:
        path = ROOT / rel
        if path.is_file():
            rows.append(f"{sha256(path)}  {rel}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return out


def ci_run_url() -> str:
    """Ссылка на последний успешный прогон CI по текущему коммиту.

    «Все проверки прогнаны локально» внешнему проверяющему ничего не доказывает:
    локальный прогон не воспроизводим с его стороны. Ссылка на прогон — доказуема.
    Без gh или сети возвращаем пустую строку, а не выдуманный адрес.
    """
    try:
        proc = subprocess.run(
            ["gh", "run", "list", "--limit", "20", "--json",
             "conclusion,headSha,workflowName,url,databaseId"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    try:
        runs = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return ""
    head = head_commit()
    for run in runs:
        if (run.get("headSha", "").startswith(head)
                and run.get("conclusion") == "success"
                and run.get("workflowName") == "validate"):
            return run.get("url", "")
    return ""


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


# Строки, привязанные к HEAD: файл называет коммит, на котором собран, и прогон CI
# по нему. Обе меняются самим фактом коммита, поэтому в сверке не участвуют —
# иначе `--check` падал бы всегда сразу после коммита файла (проверено).
HEAD_BOUND_PREFIXES = ("Коммит: ", "Прогон CI на этом коммите: ")


def stable(text: str) -> str:
    """Содержимое без строк, привязанных к HEAD (см. докстринг модуля)."""
    return "\n".join(
        l for l in text.splitlines() if not l.startswith(HEAD_BOUND_PREFIXES)
    )


def build() -> str:
    c, d = counts(), dist_counts()
    commit = head_commit()
    url = ci_run_url()
    # Обе ветки начинаются с одного префикса: строка привязана к HEAD и исключена из
    # сверки. Иначе в CI (где нет `gh`) генерировался бы текст с другим началом, и
    # `--check` падал бы на расхождении, которого нет в дереве.
    ci_note = (
        f"Прогон CI на этом коммите: {url} (workflow `validate`, conclusion `success`)."
        if url else
        "Прогон CI на этом коммите: ссылку подставить не удалось (нет `gh` или сети) — "
        "результат воспроизводится командами ниже."
    )
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
        f"{own} — в таблице README собственные названы поимённо, и валидатор требует, "
        f"чтобы каждый каталог `skills/` был назван хотя бы в одном из двух списков.",
        "- Разбивка по наборам выше сверяется валидатором построчно (таблица README → "
        "дерево), а не только по сумме: перестановка между наборами валит CI.",
        "",
        "## Как проверить, не запуская репозиторий",
        "",
        "- `sha256sum -c docs/SHA256SUMS` — сверка присланных файлов с хешами из "
        "репозитория (таблица выше усечена до 16 символов и для проверки не годится).",
        "- Хеши и числа выше сверяются с архивом; строка с коммитом сверяется с `git log`.",
        "",
        "Проверки, которые прогоняет CI (и которые можно повторить локально):",
        "",
        "- `python3 scripts/validate_agents.py` — SOUL-манифесты, числа README и NOTICE, "
        "лицензии вендоренных наборов, диаграмма.",
        "- `python3 tests/test_scripts.py` — сборка профилей и валидатор.",
        "- `python3 scripts/build_profiles.py --clean && python3 scripts/check_dist.py` — "
        "форма дистрибутивов (манифест, симлинки, следы секретов).",
        "- `python3 scripts/build_for_review.py --check` — этот файл воспроизводится из дерева.",
        "",
        ci_note,
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
        sums = ROOT / "docs" / "SHA256SUMS"
        want = "\n".join(
            f"{sha256(ROOT / rel)}  {rel}" for rel in KEY_FILES if (ROOT / rel).is_file()
        ) + "\n"
        have = sums.read_text(encoding="utf-8") if sums.is_file() else ""
        if have != want:
            print("ОШИБКА: docs/SHA256SUMS разошёлся с деревом — пересобери "
                  "python3 scripts/build_for_review.py", file=sys.stderr)
            return 1
        print("docs/for-review.md и docs/SHA256SUMS совпадают с деревом (--check)")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    sums = write_sums()
    print(f"docs/for-review.md пересобран: {len(KEY_FILES)} файлов, коммит {head_commit()}")
    print(f"docs/SHA256SUMS перезаписан: {len(KEY_FILES)} полных хешей")
    return 0


if __name__ == "__main__":
    sys.exit(main())
