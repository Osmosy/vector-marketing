#!/usr/bin/env python3
"""Вендоринг скиллов из апстримов: копия в skills/<набор>/<имя>/ + блок атрибуции.

Копирует байт-в-байт, ничего не переписывая в апстримном тексте: адаптация
и атрибуция добавляются ДОПОЛНИТЕЛЬНЫМ блоком в конец файла.

Запуск: python3 scripts/vendor_skill.py --help
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

UPSTREAMS = {
    "social-media-skills": {
        "repo": "charlie947/social-media-skills",
        "ref": "HEAD",
        "license": "MIT (© 2026 Charlie Hills)",
        "license_url": "https://raw.githubusercontent.com/charlie947/social-media-skills/HEAD/LICENSE",
        "license_file": "charlie947-social-media-skills-MIT.txt",
        "layout": "skills/<name>",
    },
    "pm-skills": {
        "repo": "phuryn/pm-skills",
        "ref": "HEAD",
        "license": "MIT (© 2026 Pawel Huryn)",
        "license_url": "https://raw.githubusercontent.com/phuryn/pm-skills/HEAD/LICENSE",
        "license_file": "phuryn-pm-skills-MIT.txt",
        "layout": "pm-*/skills/<name>",   # путь ищется по имени скилла
    },
    "claude-skills": {
        "repo": "alirezarezvani/claude-skills",
        "ref": "HEAD",
        "license": "MIT (© 2025 Alireza Rezvani)",
        "license_url": "https://raw.githubusercontent.com/alirezarezvani/claude-skills/HEAD/LICENSE",
        "license_file": "alirezarezvani-claude-skills-MIT.txt",
        "layout": None,
    },
    "searchfit-seo": {
        "repo": "searchfit/searchfit-seo",
        "ref": "HEAD",
        "license": "MIT",
        "license_url": "https://raw.githubusercontent.com/searchfit/searchfit-seo/HEAD/LICENSE",
        "license_file": "searchfit-seo-MIT.txt",
        "layout": "skills/<name>",
    },
    "humblytics-marketing": {
        "repo": "Humblytics/humblytics-marketing-skills",
        "ref": "HEAD",
        "license": "MIT (© 2026 Humblytics, Inc.)",
        "license_url": "https://raw.githubusercontent.com/Humblytics/humblytics-marketing-skills/HEAD/LICENSE",
        "license_file": "humblytics-marketing-skills-MIT.txt",
        "layout": "skills/<name>",
    },
}

REPO_ROOT = Path(__file__).resolve().parent.parent


def gh_tree(repo: str) -> list[dict]:
    import subprocess
    out = subprocess.run(["gh", "api", f"repos/{repo}/git/trees/HEAD?recursive=1"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh api failed for {repo}: {out.stderr.strip()}")
    return json.loads(out.stdout)["tree"]


def _paths(repo: str) -> list[str]:
    return [t["path"] for t in gh_tree(repo)]


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def resolve_path(set_name: str, skill: str) -> str:
    """Найти каталог скилла в апстриме (у pm-skills он лежит в pm-*/skills/<name>)."""
    cfg = UPSTREAMS[set_name]
    paths = _paths(cfg["repo"])
    # зеркала не берём — только основное дерево
    mirrors = (".hermes/", ".gemini/", ".codex/", ".claude/", ".vibe/")
    cands = [p for p in paths
             if p.endswith(f"skills/{skill}/SKILL.md") and not p.startswith(mirrors)]
    if not cands:
        base = cfg["layout"].replace("<name>", skill) if cfg["layout"] else None
        cands = [p for p in paths if base and p.startswith(base)]
    if not cands:
        raise SystemExit(f"{set_name}: скилл «{skill}» не найден в апстриме")
    # самый короткий путь = основное дерево
    return sorted(cands, key=len)[0].rsplit("/", 1)[0]


def files_of(set_name: str, skill: str) -> list[str]:
    """Только файлы (blob), без каталогов: дерево API отдаёт и directory-записи."""
    cfg = UPSTREAMS[set_name]
    root = resolve_path(set_name, skill)
    return sorted(t["path"] for t in gh_tree(cfg["repo"])
                  if t.get("type") == "blob"
                  and (t["path"] == root or t["path"].startswith(root + "/")))


ATTRIBUTION = """
### Attribution

Скилл заимствован из [{repo}](https://github.com/{repo}) ({license}).
Текст апстрима сохранён как есть; РФ-адаптация (если есть) и этот блок — добавления
сверху, исходные строки не переписывались. Взято {date}.
"""


def vendor(set_name: str, skill: str, date: str, dry_run: bool) -> tuple[int, str]:
    cfg = UPSTREAMS[set_name]
    root = resolve_path(set_name, skill)
    members = files_of(set_name, skill)
    target = REPO_ROOT / "skills" / set_name / skill
    copied = 0
    for rel in members:
        # rel == root → файл SKILL.md самого скилла; иначе — вложенный файл
        inner = rel[len(root):].lstrip("/")
        dest = target / inner if inner else target / "SKILL.md"
        url = f"https://raw.githubusercontent.com/{cfg['repo']}/{cfg['ref']}/{rel}"
        if dry_run:
            print(f"    [dry] {rel} → {dest.relative_to(REPO_ROOT)}")
            copied += 1
            continue
        if rel.endswith(".md"):
            data = fetch(url).decode("utf-8")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(data, encoding="utf-8")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(fetch(url))
        copied += 1

    if dry_run:
        return copied, root

    # атрибуция дописывается в конец SKILL.md (апстримный текст не правим)
    skill_md = target / "SKILL.md"
    body = skill_md.read_text(encoding="utf-8")
    marker = "### Attribution"
    if marker not in body:
        body = body.rstrip() + "\n" + ATTRIBUTION.format(
            repo=cfg["repo"], license=cfg["license"], date=date)
        skill_md.write_text(body, encoding="utf-8")

    # лицензия апстрима — в THIRD_PARTY_LICENSES/, если её ещё нет
    lic_dir = REPO_ROOT / "THIRD_PARTY_LICENSES"
    lic_dir.mkdir(exist_ok=True)
    lic_path = lic_dir / cfg["license_file"]
    if not lic_path.is_file():
        try:
            lic_path.write_bytes(fetch(cfg["license_url"]))
        except Exception as exc:
            return copied, f"{root} (лицензия не скачалась: {exc})"
    return copied, root


def main() -> int:
    ap = argparse.ArgumentParser(description="Вендоринг скиллов из апстримов с атрибуцией")
    ap.add_argument("--set", required=True, choices=sorted(UPSTREAMS))
    ap.add_argument("--skills", required=True, help="имена через запятую")
    ap.add_argument("--date", default="2026-09")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    for skill in skills:
        n, root = vendor(args.set, skill, args.date, args.dry_run)
        print(f"  {args.set}/{skill:24s} файлов: {n:2d}  ← {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
