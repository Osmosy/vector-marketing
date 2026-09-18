#!/usr/bin/env python3
"""Тесты скриптов сборки и валидации Vector Marketing.

Скрипты — часть поставки (`INSTALL.md` предлагает их запускать), поэтому их
краевые случаи проверяются так же, как контент: пустой `agents/`, битый YAML
манифеста, дубли имён, ссылки на несуществующих агентов, утечка секрета.

Запуск:  python3 tests/test_scripts.py          (только stdlib, без зависимостей)
Или:     python3 -m pytest tests/ -q             (если pytest установлен)
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _load(module_name: str):
    """Импортировать скрипт по пути (scripts/ не пакет)."""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = _load("validate_agents")
check = _load("check_dist")
build = _load("build_profiles")


def run_script(name: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cwd / "scripts" / f"{name}.py")],
        cwd=cwd, capture_output=True, text=True,
    )


class RepoCopy:
    """Копия репозитория во временном каталоге: тесты не трогают рабочее дерево."""

    def __enter__(self) -> Path:
        self._tmp = Path(tempfile.mkdtemp())
        self.path = self._tmp / "vector-marketing"
        shutil.copytree(
            REPO_ROOT, self.path, ignore=shutil.ignore_patterns(".git", "__pycache__", "dist")
        )
        return self.path

    def __exit__(self, *exc) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)


class BuildProfilesTest(unittest.TestCase):
    def test_cобирает_все_профили(self) -> None:
        with RepoCopy() as repo:
            r = run_script("build_profiles", repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            profiles = sorted(p.name for p in (repo / "dist").iterdir() if p.is_dir())
            expected = sorted(p.stem for p in (repo / "agents").glob("*.md"))
            self.assertEqual(profiles, expected)

    def test_каждый_профиль_несёт_манифест_и_brain(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            brain_files = list((repo / "company-brain").glob("*.md"))
            for profile in (repo / "dist").iterdir():
                if not profile.is_dir():
                    continue
                self.assertTrue((profile / "distribution.yaml").is_file(), profile.name)
                self.assertTrue((profile / "SOUL.md").is_file(), profile.name)
                self.assertEqual(
                    len(list((profile / "brain").glob("*.md"))), len(brain_files), profile.name
                )

    def test_падает_когда_навык_не_найден(self) -> None:
        """Ссылка агента на несуществующий навык — сборка возвращает ошибку."""
        with RepoCopy() as repo:
            agent = repo / "agents" / "seo.md"
            agent.write_text(
                agent.read_text(encoding="utf-8").replace(
                    "## Формат выдачи",
                    "- **skills/pm-skills/nonexistent-skill-for-test** — которого нет\n\n## Формат выдачи",
                ),
                encoding="utf-8",
            )
            r = run_script("build_profiles", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("навык не найден", r.stdout)

    def test_пустой_agents_даёт_ошибку(self) -> None:
        with RepoCopy() as repo:
            for f in (repo / "agents").glob("*.md"):
                f.unlink()
            r = run_script("build_profiles", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("нечего собирать", r.stdout)

    def test_дубли_имён_профилей_не_создают_каталог_дважды(self) -> None:
        """Два агента с одним stem (одно и то же имя) — один профиль, без мусора."""
        with RepoCopy() as repo:
            src = repo / "agents" / "ops.md"
            dup = repo / "agents" / "sub" / "ops.md"
            dup.parent.mkdir()
            dup.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            run_script("build_profiles", repo)
            names = [p.name for p in (repo / "dist").iterdir() if p.is_dir()]
            self.assertEqual(len(names), len(set(names)))


class ValidateAgentsTest(unittest.TestCase):
    def test_чистое_дерево_проходит(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_битый_handoff_ловится(self) -> None:
        with RepoCopy() as repo:
            agent = repo / "agents" / "sales.md"
            agent.write_text(
                agent.read_text(encoding="utf-8").replace("# Handoff", "## Handoff", 1),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("отсутствует секция", r.stdout)

    def test_handoff_на_несуществующего_агента_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            wf = repo / "workflows" / "handoff-protocol.md"
            wf.write_text(
                wf.read_text(encoding="utf-8").replace("@sales →", "@pr →"), encoding="utf-8"
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("@pr", r.stdout)

    def test_число_в_таблице_readme_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "| `pm-skills/` | 40 |", "| `pm-skills/` | 41 |"
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("pm-skills", r.stdout)

    def test_атрибуция_вендоренного_набора_обязательна(self) -> None:
        with RepoCopy() as repo:
            skill = repo / "skills" / "open-seo" / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").split("### Attribution")[0], encoding="utf-8"
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Attribution", r.stdout)

    def test_навык_без_привязки_к_агенту_ловится(self) -> None:
        """Новый навык, к которому не привязан ни один агент, — видимая ошибка."""
        with RepoCopy() as repo:
            skill = repo / "skills" / "orphan-skill-for-test"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: orphan-skill-for-test\ndescription: Test fixture.\n---\n\n# X\n",
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("orphan-skill-for-test", r.stdout)

    def test_таблица_profiles_сверяется_со_сборкой(self) -> None:
        """profiles/README проверяется без dist: считаем по логике сборки."""
        with RepoCopy() as repo:
            pr = repo / "profiles" / "README.md"
            text = pr.read_text(encoding="utf-8")
            # Вставляем выдуманный навык в строку любого агента, не завися от её текста.
            mutated = re.sub(
                r"(\|\s*`?crm-retention`?\s*\|[^|]*\|\s*)([^|]+)(\s*\|)",
                r"\1\2, nonexistent-for-test\3",
                text, count=1,
            )
            self.assertNotEqual(mutated, text, "мутация не применилась")
            pr.write_text(mutated, encoding="utf-8")
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("nonexistent-for-test", r.stdout)

    def test_пометка_заготовка_сверяется_с_фактом(self) -> None:
        """Заготовка не может иметь навыков репозитория — и наоборот."""
        with RepoCopy() as repo:
            # Даём заготовке (yandex-direct) настоящий навык, не сняв пометку.
            agent = repo / "agents" / "yandex-direct.md"
            agent.write_text(
                agent.read_text(encoding="utf-8").replace(
                    "## Формат выдачи",
                    "- **skills/pm-skills/pricing-strategy** — лишний навык для заготовки\n\n## Формат выдачи",
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("заготовкой", r.stdout)

    def test_пустой_профиль_без_пометки_ловится(self) -> None:
        with RepoCopy() as repo:
            for rel in ("README.md", "INSTALL.md", "profiles/README.md"):
                path = repo / rel
                path.write_text(
                    path.read_text(encoding="utf-8").replace("заготовка", "статус"), encoding="utf-8"
                )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("не помечен", r.stdout)

    def test_коллизия_имён_навыков_внутри_профиля_ловится(self) -> None:
        """Два навыка с одним name в одном профиле — один из них недоступен агенту."""
        with RepoCopy() as repo:
            agent = repo / "agents" / "seo.md"
            agent.write_text(
                agent.read_text(encoding="utf-8").replace(
                    "## Формат выдачи",
                    "- **skills/cowork-roles/marketing/seo-audit** — дубль имени с searchfit-версией\n\n## Формат выдачи",
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("дубли имён", r.stdout)

    def test_внешняя_зависимость_должна_быть_в_install(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            install = repo / "INSTALL.md"
            install.write_text(
                install.read_text(encoding="utf-8").replace("`yandex-wordstat`", "Вордстат"),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("yandex-wordstat", r.stdout)


class CheckDistTest(unittest.TestCase):
    def test_нет_dist_даёт_подсказку(self) -> None:
        with RepoCopy() as repo:
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("build_profiles", r.stdout)

    def test_секрет_в_распространении_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            soul = repo / "dist" / "seo" / "SOUL.md"
            soul.write_text(
                soul.read_text(encoding="utf-8")
                + "\nКлюч: sk-proj-AbCdEf0123456789AbCdEf0123456789\n",
                encoding="utf-8",
            )
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("секрет", r.stdout)

    def test_плейсхолдер_не_считается_секретом(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            soul = repo / "dist" / "seo" / "SOUL.md"
            soul.write_text(
                soul.read_text(encoding="utf-8") + "\nКлюч: sk-...впишите свой ключ\n",
                encoding="utf-8",
            )
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_user_owned_путь_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            (repo / "dist" / "seo" / "memories").mkdir()
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("user-owned", r.stdout)

    def test_симлинк_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            target = repo / "dist" / "seo" / "SOUL.md"
            (target.parent / "link.md").symlink_to(target)
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("симлинк", r.stdout)

    def test_битый_манифест_ловится(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            manifest = repo / "dist" / "seo" / "distribution.yaml"
            manifest.write_text("name: not-seo\n", encoding="utf-8")
            r = run_script("check_dist", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("name", r.stdout)


class SecretPatternsTest(unittest.TestCase):
    """Функции скриптов проверяются напрямую: краевые случаи без запуска процесса."""

    def test_настоящие_ключи_ловятся(self) -> None:
        samples = {
            "openai": "sk-proj-AbCdEf0123456789AbCdEf0123456789",
            "github": "ghp_" + "A" * 36,
            "aws": "AKIAIOSFODNN7EXAMPLE",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
        }
        for label, value in samples.items():
            with self.subTest(label=label):
                self.assertTrue(
                    any(p.search(value) for _, p in check.SECRET_PATTERNS), label
                )

    def test_плейсхолдеры_и_имена_переменных_не_ловятся(self) -> None:
        for value in (
            "DEEPSEEK_API_KEY=",
            "api_key_env: ZAI_API_KEY",
            "ключ: sk-...впишите свой",
            "token: your_token_here",
        ):
            with self.subTest(value=value):
                hits = [
                    label for label, p in check.SECRET_PATTERNS
                    if p.search(value) and not any(
                        m in value.lower() for m in check.PLACEHOLDER_MARKERS
                    )
                ]
                self.assertEqual(hits, [], value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
