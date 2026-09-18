#!/usr/bin/env python3
"""Проверка формы собранных дистрибутивов (dist/) без Hermes CLI.

Зеркалит то, что проверяет установщик `hermes profile install`, но локально:
манифест, обязательные файлы, отсутствие симлинков и user-owned каталогов
внутри дистрибутива. Плюс ищет следы секретов: `.gitignore` внутри
дистрибутива не защищает ничего (установщик его не читает), поэтому ключ,
случайно попавший в SOUL, brain/ или навык, уехал бы к пользователю как есть.

Запуск: python3 scripts/check_dist.py [--dist dist] [--agents 19]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Пути, которые установщик Hermes всё равно вырежет — в дистрибутиве им делать нечего.
FORBIDDEN_TOP_LEVEL = {
    "auth.json", ".env", "memories", "sessions", "state.db", "logs",
    "workspace", "plans", "home", "local", ".git", "node_modules",
}
REQUIRED_FILES = ("distribution.yaml", "SOUL.md")

# Маркеры реального секрета (не плейсхолдера). Каждый — (имя, регулярка).
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ключ OpenAI/Anthropic-вида", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("GitHub-токен", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("ключ AWS", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("ключ Google", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("токен Slack", re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}")),
    ("приватный ключ", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("токен Яндекс-облака", re.compile(r"\bt1\.[A-Za-z0-9_-]{30,}")),
    (
        "присваивание секрета",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*"
            r"[\"']?[A-Za-z0-9_\-+/]{24,}"
        ),
    ),
)

# Строки-плейсхолдеры: документация и `.env.EXAMPLE` намеренно содержат имена переменных.
PLACEHOLDER_MARKERS = (
    "example", "placeholder", "your_", "your-", "<", "***", "xxxx", "...",
    "sk-...", "впишите", "вписать", "замените", "example.com",
)

SCAN_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".sh", ".txt", ".env.example", ""}
MAX_SCAN_BYTES = 512 * 1024


def scan_secrets(agent_dir: Path) -> list[str]:
    """Ищем следы живых ключей в текстовых файлах дистрибутива."""
    findings: list[str] = []
    for path in sorted(agent_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if path.stat().st_size > MAX_SCAN_BYTES:
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(agent_dir)
        for lineno, line in enumerate(body.splitlines(), start=1):
            stripped = line.strip()
            lowered = stripped.lower()
            for label, pattern in SECRET_PATTERNS:
                m = pattern.search(stripped)
                if not m:
                    continue
                # Плейсхолдер рядом со совпадением — это документация, а не секрет.
                window = lowered
                if any(marker in window for marker in PLACEHOLDER_MARKERS):
                    continue
                findings.append(
                    f"{agent_dir.name}: похоже на секрет ({label}) — {rel}:{lineno}"
                )
    return findings



def check(dist_root: Path, expected_agents: int) -> list[str]:
    errors: list[str] = []
    if not dist_root.is_dir():
        return [f"нет каталога {dist_root} — сначала запусти scripts/build_profiles.py"]

    agents = sorted(p for p in dist_root.iterdir() if p.is_dir())
    if not agents:
        return [f"{dist_root} пуст"]

    for agent in agents:
        name = agent.name
        for fname in REQUIRED_FILES:
            if not (agent / fname).is_file():
                errors.append(f"{name}: нет {fname}")

        manifest = agent / "distribution.yaml"
        if manifest.is_file():
            text = manifest.read_text(encoding="utf-8")
            if f"name: {name}" not in text:
                errors.append(f"{name}: в distribution.yaml не совпадает поле name")
            for key in ("version:", "description:", "license:"):
                if key not in text:
                    errors.append(f"{name}: в distribution.yaml нет «{key}»")

        soul = agent / "SOUL.md"
        if soul.is_file():
            first = soul.read_text(encoding="utf-8").splitlines()[:1]
            if not first or not first[0].startswith("# "):
                errors.append(f"{name}: SOUL.md не начинается с H1 (Identity)")

        for entry in agent.iterdir():
            if entry.name in FORBIDDEN_TOP_LEVEL:
                errors.append(f"{name}: в дистрибутиве есть user-owned путь «{entry.name}»")

        for path in agent.rglob("*"):
            if path.is_symlink():
                errors.append(f"{name}: симлинк в дистрибутиве — {path.relative_to(agent)}")

        skills_root = agent / "skills"
        if skills_root.is_dir():
            # Внутри навыка допустимы references/, scripts/, assets/ — важно лишь, чтобы
            # у каждого каталога с файлами был предок-навык (SKILL.md), а не мусор в корне.
            def has_skill_ancestor(path: Path) -> bool:
                cur = path
                while True:
                    if (cur / "SKILL.md").is_file():
                        return True
                    if cur == skills_root or cur.parent == cur:
                        return False
                    cur = cur.parent

            for skill_dir in sorted(p for p in skills_root.rglob("*") if p.is_dir()):
                if not any(c.is_file() for c in skill_dir.iterdir()):
                    continue  # пустые каталоги не считаем
                if not has_skill_ancestor(skill_dir):
                    errors.append(
                        f"{name}: каталог без навыка-предка (SKILL.md) — "
                        f"{skill_dir.relative_to(agent)}"
                    )

        errors.extend(scan_secrets(agent))

    if expected_agents and len(agents) != expected_agents:
        errors.append(f"профилей {len(agents)}, ожидалось {expected_agents}")

    print(f"профилей: {len(agents)}, навыков: {sum(1 for _ in dist_root.rglob('SKILL.md'))}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Проверка формы dist/")
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--agents", type=int, default=19, help="ожидаемое число профилей (0 — не проверять)")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()

    errors = check(Path(args.repo_root) / args.dist, args.agents)
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\nИтог: ошибок {len(errors)}")
        return 1
    print("Итог: dist корректен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
