#!/usr/bin/env python3
"""Собрать набор для внешней проверки одним файлом.

Запуск: python3 scripts/build_bundle.py --out ~/Загрузки/vector-marketing-for-review.md
        python3 scripts/build_bundle.py --check --out <файл>   # сверить, не писать

Зачем. `docs/for-review.md` показывает проверяющему ключевые файлы и числа, но не
содержимое: чтобы прочитать сам код и документы, он должен получить репозиторий.
Этот скрипт кладёт всё нужное в ОДИН текстовый файл — распаковывать нечего, и
набор воспроизводим командой, а не собран руками. Рукописный набор расходится с
деревом: он стареет молча, поэтому у файла есть режим `--check` для приёмки.

Что попадает в набор. Все файлы, читаемые как UTF-8, кроме исключений (см.
`EXCLUDED_*`): генерируемые артефакты диаграммы и внутренние файлы вендоренных
наборов. Каждое исключение печатается в шапке с причиной — проверяющий видит не
только то, что в наборе, но и то, чего в нём нет и почему. Список файлов берётся
из `git ls-files` (набор привязан к ревизии, мусор вроде `__pycache__` не попадёт
по построению); если репозитория под рукой нет — обход файловой системы с теми же
правилами, иначе скрипт не работал бы в копии дерева, которой пользуются тесты.

`--check` сравнивает файл на диске с тем, что скрипт собрал бы сейчас, и падает с
перечнем расхождений: файл добавлен, пропал, изменился по хешу. Содержимое
сравнивать целиком незачем — таблица хешей в наборе уже это покрывает.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Исключения по файлам набора. Причина печатается в шапке набора: проверяющий
# должен видеть, что именно из репозитория не приложено, и уметь это оспорить.
EXCLUDED_DOC_ARTIFACTS = "генерируемый артефакт диаграммы"
EXCLUDED_SKILL_INTERNALS = "внутренности вендоренного набора"
EXCLUDED_BINARY = "не текст (UTF-8 не читается)"
EXCLUDED_MISSING = "нет в дереве"

SEPARATOR = "=" * 100
BUNDLE_NAME = "vector-marketing-for-review.md"


def _git_ls_files() -> list[str] | None:
    """Отслеживаемые файлы или None, если это не репозиторий (копия без .git)."""
    try:
        proc = subprocess.run(["git", "ls-files"], cwd=ROOT,
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _walk_files() -> list[str]:
    """Обход дерева, когда git недоступен: те же исключения по путям."""
    skip_dirs = {".git", "__pycache__", "dist", ".mypy_cache", ".pytest_cache", "node_modules"}
    found = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.relative_to(ROOT).parts):
            continue
        if path.name.endswith(".pyc"):
            continue
        found.append(path.relative_to(ROOT).as_posix())
    return found


def _all_files() -> list[str]:
    return _git_ls_files() or _walk_files()


def exclusion_reason(rel: str, full: bool) -> str | None:
    """Почему файл не в наборе (None — попадает)."""
    parts = pathlib.PurePosixPath(rel).parts
    if full:
        return None
    if parts[0] == "docs" and pathlib.Path(rel).suffix in {".html", ".png"}:
        return EXCLUDED_DOC_ARTIFACTS
    if parts[0] == "skills" and pathlib.Path(rel).name != "SKILL.md":
        return EXCLUDED_SKILL_INTERNALS
    return None


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def head_commit() -> str:
    """Ревизия для шапки. В копии без .git — прочерк, а не выдуманный хеш."""
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def select(full: bool) -> tuple[list[str], list[tuple[str, str]]]:
    """(файлы набора, исключённые с причинами)."""
    keep: list[str] = []
    drop: list[tuple[str, str]] = []
    for rel in _all_files():
        reason = exclusion_reason(rel, full)
        path = ROOT / rel
        if reason is None and not path.is_file():
            reason = EXCLUDED_MISSING
        if reason is None:
            try:
                path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                reason = EXCLUDED_BINARY
        (drop.append((rel, reason)) if reason else keep.append(rel))
    return keep, drop


def demote_headings(text: str) -> str:
    """Понизить заголовки внутри файла на уровень.

    Иначе оглавление набора смешивается с разделами внутри файлов: читающий не
    отличает «## Хеши файлов набора» (раздел набора) от «## Что нужно знать
    перед правкой» (раздел внутри CONTRIBUTING.md).
    """
    return re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", text, flags=re.M)


def build(full: bool = False) -> str:
    keep, drop = select(full)
    commit = head_commit()
    total = sum((ROOT / rel).stat().st_size for rel in keep)
    when = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")

    lines = [
        "# vector-marketing — набор для внешней проверки",
        "",
        f"Ревизия: `{commit}`" if commit else "Ревизия: не определена (нет `git`/`.git`)",
        f"Собрано: {when}, `python3 scripts/build_bundle.py`.",
        "",
        "## Как читать",
        "",
        "Ниже — содержимое репозитория по файлам; разделитель — строка из `=`.",
        f"Файлов в наборе: {len(keep)}; исключено: {len(drop)}; всего {total} байт "
        f"({total / 1048576:.2f} МБ).",
        "",
        "## Что исключено и почему",
        "",
    ]
    if drop:
        for rel, reason in drop:
            lines.append(f"- `{rel}` — {reason}")
    else:
        lines.append("- ничего: набор полный (`--full`)")

    lines += ["", "## Хеши файлов набора (sha256, полные)", "", "| Файл | Байт | sha256 |", "|---|---|---|"]
    for rel in keep:
        path = ROOT / rel
        lines.append(f"| `{rel}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    lines.append("")

    for rel in keep:
        path = ROOT / rel
        text = demote_headings(path.read_text(encoding="utf-8"))
        lines += [
            "",
            SEPARATOR,
            f"=== ФАЙЛ: {rel} ({path.stat().st_size} байт)",
            SEPARATOR,
            "",
            text.rstrip("\n"),
        ]
    return "\n".join(lines) + "\n"


def parse_bundle(text: str) -> dict[str, str]:
    """Хеши файлов из набора — то, что сверяет `--check`."""
    return {
        rel: digest
        for rel, _size, digest in re.findall(
            r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$", text, re.M
        )
    }


def check(out: pathlib.Path, full: bool = False) -> int:
    if not out.is_file():
        print(f"ОШИБКА: файла нет: {out} — собери python3 scripts/build_bundle.py --out {out}",
              file=sys.stderr)
        return 1
    have = parse_bundle(out.read_text(encoding="utf-8"))
    want = {rel: sha256_file(ROOT / rel) for rel in select(full)[0]}
    problems = []
    for rel in sorted(set(have) | set(want)):
        if rel not in have:
            problems.append(f"  + {rel} — есть в дереве, нет в наборе")
        elif rel not in want:
            problems.append(f"  - {rel} — есть в наборе, но исключён или пропал из дерева")
        elif have[rel] != want[rel]:
            problems.append(f"  ~ {rel} — содержимое изменилось")
    if problems:
        print("\n".join(problems[:20]), file=sys.stderr)
        if len(problems) > 20:
            print(f"  … и ещё {len(problems) - 20}", file=sys.stderr)
        print(f"ОШИБКА: {out} разошёлся с деревом — пересобери "
              f"python3 scripts/build_bundle.py --out {out}", file=sys.stderr)
        return 1
    print(f"{out}: набор сходится с деревом ({len(want)} файлов, --check)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path.cwd() / BUNDLE_NAME,
                    help=f"куда писать набор (по умолчанию ./{BUNDLE_NAME})")
    ap.add_argument("--check", action="store_true",
                    help="не писать: падать, если набор разошёлся с деревом")
    ap.add_argument("--full", action="store_true",
                    help="без исключений (внутренности навыков и артефакты диаграммы тоже)")
    args = ap.parse_args()

    if args.check:
        return check(args.out, args.full)

    text = build(args.full)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    keep, drop = select(args.full)
    size = len(text.encode("utf-8"))
    print(f"{args.out} собран: файлов {len(keep)}, исключено {len(drop)}, "
          f"{size} байт ({size / 1048576:.2f} МБ), ревизия {head_commit() or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
