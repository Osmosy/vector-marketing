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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
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

    def test_число_наборов_в_деке_ловится(self) -> None:
        """«161 навык в 8 наборах» жило в деке молча: число наборов не проверялось.

        Дек — клиентский материал, и это было единственное число в репозитории,
        расходившееся с деревом (наборов 14).
        """
        with RepoCopy() as repo:
            for rel in ("deck/deck-marketing.py", "deck/README.md"):
                path = repo / rel
                body = path.read_text(encoding="utf-8")
                self.assertIn("161 навык в 14 наборах", body, rel)
                path.write_text(
                    body.replace("161 навык в 14 наборах", "161 навык в 8 наборах", 1),
                    encoding="utf-8",
                )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("наборов в skills/ — 14", r.stdout)

    def test_готовые_профили_в_install_сверяются(self) -> None:
        """«Готовых к работе — 17 профилей из 19»: число выводимо из логики сборки."""
        with RepoCopy() as repo:
            install = repo / "INSTALL.md"
            body = install.read_text(encoding="utf-8")
            self.assertIn("Готовых к работе — 17 профилей из 19", body)
            install.write_text(
                body.replace(
                    "Готовых к работе — 17 профилей из 19",
                    "Готовых к работе — 18 профилей из 19",
                    1,
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("готовых профилей", r.stdout)

    def test_заготовка_в_install_сверяется_с_фактом(self) -> None:
        """Снятая пометка «заготовка» у профиля без навыков — ошибка."""
        with RepoCopy() as repo:
            install = repo / "INSTALL.md"
            body = install.read_text(encoding="utf-8")
            self.assertIn("| **заготовка** |", body)
            install.write_text(
                body.replace("| **заготовка** |", "| работает |", 1), encoding="utf-8"
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("заготовкой", r.stdout)

    def test_brain_в_install_и_profiles_сверяется(self) -> None:
        """INSTALL и profiles/README были вне валидатора — число brain не сверялось."""
        with RepoCopy() as repo:
            for rel in ("INSTALL.md", "profiles/README.md"):
                path = repo / rel
                body = path.read_text(encoding="utf-8")
                self.assertIn("`company-brain/` (8 файлов)", body, rel)
                path.write_text(
                    body.replace("`company-brain/` (8 файлов)", "`company-brain/` (7 файлов)", 1),
                    encoding="utf-8",
                )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("company-brain", r.stdout)

    def test_лицензия_в_таблице_readme_сверяется_с_notice(self) -> None:
        """`Apache-2.0` → `MIT` у cowork-roles проходило CI: это было утверждение о лицензии."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            body = readme.read_text(encoding="utf-8")
            self.assertIn("| `cowork-roles/` | 66 | Apache-2.0 |", body)
            readme.write_text(
                body.replace("| `cowork-roles/` | 66 | Apache-2.0 |", "| `cowork-roles/` | 66 | MIT |", 1),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("cowork-roles", r.stdout)
            self.assertIn("Apache-2.0", r.stdout)

    def test_число_скиллов_в_notice_сверяется_с_деревом(self) -> None:
        """NOTICE — лицензионный документ и источник списка вендоренных наборов.

        Проверялось только упоминание набора: `pm-skills/ — 40 скиллов` → 41
        проходило CI молча (мутация из TASK-2, воспроизведена).
        """
        with RepoCopy() as repo:
            notice = repo / "NOTICE.md"
            body = notice.read_text(encoding="utf-8")
            self.assertIn("`pm-skills/` — 40 скиллов", body)
            notice.write_text(
                body.replace("`pm-skills/` — 40 скиллов", "`pm-skills/` — 41 скиллов", 1),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("pm-skills", r.stdout)
            self.assertIn("41", r.stdout)

    def test_отсутствие_числа_в_notice_ловится(self) -> None:
        """Переформулировкой строки проверку обойти нельзя."""
        with RepoCopy() as repo:
            notice = repo / "NOTICE.md"
            notice.write_text(
                notice.read_text(encoding="utf-8").replace(
                    "`open-seo/` — 1 скилл", "`open-seo/` — скилл", 1
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("open-seo", r.stdout)

    def test_вендоренный_набор_обязан_быть_в_таблице_readme(self) -> None:
        """Набор, выпавший из таблицы целиком, — потеря атрибуции в README."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            body = readme.read_text(encoding="utf-8")
            self.assertIn("| `open-seo/` | 1 |", body)
            readme.write_text(
                "\n".join(l for l in body.splitlines() if not l.startswith("| `open-seo/`")),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("open-seo", r.stdout)

    def test_таблица_company_brain_сверяется_с_каталогом(self) -> None:
        """Бейдж проверялся, состав таблицы — нет: ровно этот класс давал 7 против 8."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "| `legal-compliance.md` |", "| `legal-compliance-x.md` |", 1
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("legal-compliance.md", r.stdout)

    def test_дерево_структуры_сверяется_с_каталогом_brain(self) -> None:
        """Третья копия списка brain — в блоке «Структура репозитория»."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "│   ├── media-list.md", "│   ├── media-list-x.md", 1
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("media-list.md", r.stdout)

    def test_лишняя_строка_в_таблице_brain_ловится(self) -> None:
        """Обратная сторона: строка про несуществующий файл — тоже ошибка."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "| `media-list.md` |",
                    "| `media-list-ghost.md` |\n| `media-list.md` |",
                    1,
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("media-list-ghost.md", r.stdout)

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

    def test_число_вложений_в_профили_ловится(self) -> None:
        """«146 вложений» и примеры по агентам сверяются с логикой сборки.

        Именно это число разошлось молча: README говорил «`smm-telegram` — 25»,
        а сборка вкладывала 26, и CI проходил.
        """
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "всего 146 вложений", "всего 145 вложений"
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("вложений в профили", r.stdout)

    def test_число_навыков_у_агента_в_readme_ловится(self) -> None:
        with RepoCopy() as repo:
            readme = repo / "README.md"
            body = readme.read_text(encoding="utf-8")
            self.assertIn("`market-research` получает 29", body)
            readme.write_text(
                body.replace("`market-research` получает 29", "`market-research` получает 30"),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("market-research", r.stdout)

    def test_незакреплённые_навыки_сверяются_с_фактом(self) -> None:
        """Счётчик «остальные N никуда не вкладываются» — не декорация."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "остальные 37 никуда", "остальные 38 никуда"
                ),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("незакреплённых", r.stdout)

    def test_собственный_набор_обязан_быть_назван(self) -> None:
        """Сумма «7 собственных» сходится и когда один набор выпал из README."""
        with RepoCopy() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("timesfm-marketing", "timesfm-x", 1),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("timesfm-marketing", r.stdout)

    def test_файл_лицензии_вендоренного_набора_обязателен(self) -> None:
        """Без текста лицензии атрибуция в SKILL.md ссылается в пустоту."""
        with RepoCopy() as repo:
            (repo / "THIRD_PARTY_LICENSES" / "every-app-open-seo-MIT.txt").unlink()
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("THIRD_PARTY_LICENSES", r.stdout)

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
            # Даём заготовке (vk-ads) настоящий навык, не сняв пометку.
            agent = repo / "agents" / "vk-ads.md"
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
                install.read_text(encoding="utf-8").replace("`avito-api`", "API Авито"),
                encoding="utf-8",
            )
            r = run_script("validate_agents", repo)
            self.assertEqual(r.returncode, 1)
            self.assertIn("avito-api", r.stdout)


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


def _load_skill_script(rel: str):
    """Импортировать скрипт навыка по пути внутри skills/ (навыки — не пакет)."""
    path = REPO_ROOT / "skills" / rel
    spec = importlib.util.spec_from_file_location("_skill_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WordstatSkillTest(unittest.TestCase):
    """Краевые случаи skills/yandex-wordstat: счётчик лимита и привод типов.

    Лимит API — 100 запросов в час; прогон, который упирается в отказ посреди работы,
    теряет собранное, поэтому счётчик обязан резать запросы ДО вызова API и видеть
    расход, накопленный прошлыми запусками (состояние на диске, а не в процессе).
    """

    def setUp(self) -> None:
        self.ws = _load_skill_script("yandex-wordstat/scripts/wordstat.py")

    def test_числа_из_api_приходят_строками(self) -> None:
        """protobuf JSON отдаёт int64 строкой: без приведения арифметика ломается."""
        self.assertEqual(self.ws._as_int("1234"), 1234)
        self.assertEqual(self.ws._as_int(""), 0)
        self.assertEqual(self.ws._as_int(None), 0)
        self.assertEqual(self.ws._as_float("0.0000123"), 1.23e-05)
        self.assertEqual(self.ws._as_float(None), 0.0)

    def test_дата_превращается_в_timestamp(self) -> None:
        self.assertEqual(self.ws._rfc3339("2026-08-01"), "2026-08-01T00:00:00Z")
        self.assertEqual(
            self.ws._rfc3339("2026-08-01T00:00:00Z"), "2026-08-01T00:00:00Z"
        )
        with self.assertRaises(ValueError):
            self.ws._rfc3339("01.08.2026")

    def test_бюджет_переживает_перезапуск_процесса(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "requests.json"
            first = self.ws.Budget(state, budget=3)
            first.spend()
            first.spend()
            second = self.ws.Budget(state, budget=3)  # новый процесс, тот же файл
            self.assertEqual(second.used_last_hour(), 2)
            second.spend()
            with self.assertRaises(self.ws.WordstatError):
                second.check()

    def test_часовой_лимит_режет_до_запроса(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "requests.json"
            budget = self.ws.Budget(state, budget=90)
            budget.stamps = [time.time() for _ in range(self.ws.HOURLY_LIMIT)]
            budget._save()
            fresh = self.ws.Budget(state, budget=90)
            with self.assertRaises(self.ws.WordstatError):
                fresh.check()

    def test_старые_запросы_в_лимит_не_считаются(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "requests.json"
            budget = self.ws.Budget(state, budget=90)
            budget.stamps = [time.time() - 7200 for _ in range(50)]  # два часа назад
            budget._save()
            self.assertEqual(self.ws.Budget(state, 90).used_last_hour(), 0)

    def test_дерево_регионов_разворачивается_рекурсивно(self) -> None:
        tree = [
            {"id": "225", "label": "Россия", "children": [{"id": "213", "label": "Москва"}]},
            {"id": "2", "label": "Санкт-Петербург"},
        ]
        self.assertEqual(
            self.ws._flatten_regions(tree),
            [
                {"id": "225", "label": "Россия"},
                {"id": "213", "label": "Москва"},
                {"id": "2", "label": "Санкт-Петербург"},
            ],
        )

    def test_без_ключей_скрипт_объясняет_что_задать(self) -> None:
        """Ни ключа, ни folderId — не трейсбек, а подсказка про переменные окружения."""
        script = REPO_ROOT / "skills" / "yandex-wordstat" / "scripts" / "wordstat.py"
        env = {k: v for k, v in os.environ.items()
               if k not in ("WORDSTAT_API_KEY", "WORDSTAT_FOLDER_ID")}
        r = subprocess.run(
            [sys.executable, str(script), "top", "тест"],
            capture_output=True, text=True, env=env, cwd=str(script.parent),
        )
        self.assertEqual(r.returncode, 1)
        self.assertIn("WORDSTAT_API_KEY", r.stderr)

    def test_ошибки_api_расшифровываются_по_коду(self) -> None:
        """Ориентир — code из тела ответа, а не HTTP-статус."""
        for code, needle in ((3, "обязательные поля"), (8, "квота"), (16, "ключ")):
            body = json.dumps({"code": code, "message": f"сообщение {code}"})
            text = self.ws.Wordstat._explain(400, body)
            self.assertIn(needle, text, code)


class ArticleDistributionSkillTest(unittest.TestCase):
    """Краевые случаи skills/article-distribution: разметка и учёт посевов.

    Посевы без разметки и журнала не измеряются: через месяц нельзя сказать,
    какая площадка дала переходы. Поэтому проверяем именно те места, где учёт
    молча теряет данные — канонизацию источника, слияние существующих query-
    параметров и подсчёт публикаций без метрик.
    """

    def setUp(self) -> None:
        self.sl = _load_skill_script("article-distribution/scripts/seed_log.py")

    def test_источник_канонизируется(self) -> None:
        """«vc», «vc.ru» и «VC» — одна площадка, иначе метрика расползается."""
        for value in ("VC", "vc.ru", "vc", "vc.RU"):
            self.assertEqual(self.sl.canonical_source(value), "vc", value)
        self.assertEqual(self.sl.canonical_source("Zen"), "dzen")
        self.assertEqual(self.sl.canonical_source("tg"), "telegram")
        self.assertEqual(self.sl.canonical_source("нечто"), "нечто")

    def test_utm_добавляется_к_существующим_параметрам(self) -> None:
        url = self.sl.build_utm("https://a.ru/p?x=1#frag", "Habr", "camp", "longread")
        self.assertIn("x=1", url)
        self.assertIn("utm_source=habr", url)
        self.assertIn("utm_medium=content", url)
        self.assertIn("utm_campaign=camp", url)
        self.assertIn("utm_content=longread", url)
        self.assertTrue(url.endswith("#frag"))

    def test_utm_на_невалидном_url_отклоняется(self) -> None:
        for bad in ("not-a-url", "/blog/post", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.sl.build_utm(bad, "habr", "camp")

    def test_сводка_складывает_площадку_и_считает_ctr(self) -> None:
        """Публикации по одной площадке — одна строка; CTR и CR считаются из сумм."""
        rows = [
            {"platform": "vc", "impressions": 100, "clicks": 10, "leads": 1},
            {"source": "VC", "impressions": 300, "clicks": 20, "leads": 2},
            {"platform": "habr"},  # без метрик — публикация всё равно считается
        ]
        data = self.sl.summarize(rows)
        self.assertEqual(set(data), {"vc", "habr"})
        self.assertEqual(data["vc"]["publications"], 2)
        self.assertEqual(data["vc"]["clicks"], 30)
        self.assertEqual(data["vc"]["ctr"], 0.075)
        self.assertEqual(data["vc"]["cr"], 0.1)
        self.assertEqual(data["habr"]["publications"], 1)
        self.assertEqual(data["habr"]["ctr"], 0.0)

    def test_битая_строка_журнала_не_роняет_сводку(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seed.jsonl"
            path.write_text(
                json.dumps({"platform": "habr", "clicks": 5}) + "\n" + "{не json}\n",
                encoding="utf-8",
            )
            rows = self.sl.load_log(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(self.sl.summarize(rows)["habr"]["clicks"], 5.0)

    def test_неизвестная_площадка_не_пишется_в_журнал(self) -> None:
        """Опечатка в площадке не должна создавать фантомную строку отчёта."""
        script = REPO_ROOT / "skills" / "article-distribution" / "scripts" / "seed_log.py"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "seed.jsonl"
            r = subprocess.run(
                [sys.executable, str(script), "--log", str(log), "add",
                 "--platform", "хабр", "--title", "Тест", "--url", "https://e.ru/x"],
                capture_output=True, text=True, cwd=str(script.parent),
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("неизвестна", r.stderr)
            self.assertFalse(log.exists(), "журнал не должен получить запись")

    def test_алиас_площадки_при_записи_канонизируется(self) -> None:
        script = REPO_ROOT / "skills" / "article-distribution" / "scripts" / "seed_log.py"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "seed.jsonl"
            r = subprocess.run(
                [sys.executable, str(script), "--log", str(log), "add",
                 "--platform", "vc.ru", "--title", "Кейс", "--url", "https://e.ru/x"],
                capture_output=True, text=True, cwd=str(script.parent),
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            row = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["platform"], "vc")


class GeoVisibilitySkillTest(unittest.TestCase):
    """Краевые случаи skills/geo-visibility: разбор ответов моделей.

    Каждая эвристика появилась после конкретного ложного результата на живом
    прогоне, поэтому проверяются именно ложные срабатывания: бренд-омоним,
    «github» как форма бренда, источники без ссылок, слепое дописывание /v1.
    """

    def setUp(self) -> None:
        self.gp = _load_skill_script("geo-visibility/scripts/geo_probe.py")
        self.brand = {
            "name": "Vector Marketing",
            "aliases": ["vector-marketing", "Osmosy"],
            "sites": ["https://github.com/Osmosy/vector-marketing"],
        }

    def test_платформа_не_становится_формой_бренда(self) -> None:
        """«github» в ответе — про хостинг, а не про бренд."""
        forms = self.gp.brand_forms({"name": "X", "sites": ["https://github.com/Osmosy/repo"]})
        self.assertNotIn("github", forms)
        self.assertIn("osmosy", forms)
        self.assertIn("repo", forms)

    def test_упоминание_ищется_по_границе_слова(self) -> None:
        """«вектор» не должен находиться внутри «векторный»."""
        hits = self.gp.find_mentions("векторный подход и Вектор отдельно", ["вектор"])
        self.assertEqual(len(hits), 1)

    def test_омоним_помечается_а_не_считается_знанием(self) -> None:
        """Живой случай: модель описала чужую компанию с тем же названием."""
        text = ("Vector Marketing — американская компания прямых продаж, связанная "
                "с Cutco Corporation, основана в 1981 году.")
        b = self.gp.analyze_answer(text, self.brand, [])["brand"]
        self.assertTrue(b["mentioned"])
        self.assertTrue(b["ambiguousEntity"], "омоним должен быть помечен")
        self.assertFalse(b["distinguishingMatch"])

    def test_различающий_алиас_снимает_подозрение_на_омоним(self) -> None:
        text = "Vector Marketing от Osmosy — маркетинговое агентство на Hermes Agent."
        b = self.gp.analyze_answer(text, self.brand, [])["brand"]
        self.assertTrue(b["distinguishingMatch"])
        self.assertFalse(b["ambiguousEntity"])

    def test_связи_нет_распознаётся_в_живой_формулировке(self) -> None:
        """Дословных шаблонов мало: нужен предмет + отрицание в одном предложении."""
        text = ("Коротко: публично подтверждённой связи между проектом Vector Marketing "
                "и компанией Osmosy нет.")
        self.assertTrue(self.gp.detect_unknown_claim(text))

    def test_наличие_данных_не_считается_их_отсутствием(self) -> None:
        for text in (
            "Есть данные о компании Vector Marketing: агентство на Hermes Agent.",
            "Vector Marketing часто критикуют: слабая поддержка и жалобы клиентов.",
        ):
            with self.subTest(text=text[:40]):
                self.assertFalse(self.gp.detect_unknown_claim(text))

    def test_тональность_берётся_из_окна_вокруг_упоминания(self) -> None:
        pos = self.gp.analyze_answer("Vector Marketing — надёжное решение, рекомендуют.", self.brand, [])
        neg = self.gp.analyze_answer("Vector Marketing: слабый продукт, жалобы клиентов.", self.brand, [])
        self.assertEqual(pos["brand"]["sentiment"], "positive")
        self.assertEqual(neg["brand"]["sentiment"], "negative")

    def test_источники_без_ссылок_собираются_слаги(self) -> None:
        """В живом прогоне все ответы называли репозитории слагом, без URL."""
        text = "Смотрите e2b-dev/ai-marketing-agency и VRSEN/agency-swarm."
        slugs = self.gp.source_slugs(text)
        self.assertIn("e2b-dev/ai-marketing-agency", slugs)
        self.assertIn("VRSEN/agency-swarm", slugs)

    def test_хвостовая_пунктуация_снимается_со_слага(self) -> None:
        self.assertEqual(self.gp.source_slugs("это Marketing/Cutco."), ["Marketing/Cutco"])

    def test_markdown_ссылки_дают_домен(self) -> None:
        text = "Источник: [разбор](https://habr.com/ru/articles/123/) и http://example.com/a"
        self.assertEqual(self.gp.cited_domains(text), ["habr.com", "example.com"])

    def test_версия_api_не_дублируется(self) -> None:
        cases = {
            "https://api.deepseek.com": "https://api.deepseek.com/v1",
            "https://api.z.ai/api/paas/v4": "https://api.z.ai/api/paas/v4",
            "http://127.0.0.1:11434/": "http://127.0.0.1:11434/v1",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(self.gp.normalize_base_url(raw), expected)

    def test_сводка_разделяет_знание_омоним_и_незнание(self) -> None:
        runs = [
            {"model": "m", "analysis": {
                "brand": {"mentioned": True, "firstPosition": 1, "sentiment": "neutral",
                          "ambiguousEntity": True, "claimsUnknown": True},
                "competitors": {"C": {"mentioned": True}}, "citedDomains": ["habr.com"],
                "sourceSlugs": ["a/b"]}},
            {"model": "m", "analysis": {
                "brand": {"mentioned": False, "firstPosition": None, "sentiment": None,
                          "ambiguousEntity": False, "claimsUnknown": False},
                "competitors": {"C": {"mentioned": False}}, "citedDomains": [],
                "sourceSlugs": []}},
        ]
        s = self.gp.summarize(runs, "X")["models"]["m"]
        self.assertEqual(s["prompts"], 2)
        self.assertEqual(s["mentioned"], 1)
        self.assertEqual(s["ambiguous"], 1)
        self.assertEqual(s["claimsUnknown"], 1)
        self.assertEqual(s["mentionRate"], 0.5)
        self.assertEqual(s["topCitedDomains"], ["habr.com"])

    def test_конфиг_без_промптов_или_моделей_отклоняется(self) -> None:
        script = REPO_ROOT / "skills" / "geo-visibility" / "scripts" / "geo_probe.py"
        with tempfile.TemporaryDirectory() as tmp:
            for cfg, needle in (
                ({"brand": {"name": "X"}, "prompts": [], "models": [{"name": "m", "base_url": "http://x", "model": "y"}]}, "prompts"),
                ({"brand": {"name": "X"}, "prompts": ["p"], "models": []}, "models"),
                ({"prompts": ["p"], "models": [{"name": "m", "base_url": "http://x", "model": "y"}]}, "brand.name"),
            ):
                with self.subTest(needle=needle):
                    path = Path(tmp) / "cfg.json"
                    path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
                    r = subprocess.run(
                        [sys.executable, str(script), "--config", str(path)],
                        capture_output=True, text=True, cwd=str(script.parent),
                    )
                    self.assertEqual(r.returncode, 1)
                    self.assertIn(needle, r.stderr)

    def test_dry_run_не_делает_запросов(self) -> None:
        """План вызовов проверяется без обращений к провайдеру."""
        script = REPO_ROOT / "skills" / "geo-visibility" / "scripts" / "geo_probe.py"
        cfg = {"brand": {"name": "X"}, "prompts": ["p1", "p2"],
               "models": [{"name": "m", "base_url": "http://127.0.0.1:1", "model": "y",
                           "api_key_env": ""}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cfg.json"
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(script), "--config", str(path), "--dry-run"],
                capture_output=True, text=True, cwd=str(script.parent), timeout=60,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("вызовов: 2", r.stderr)
            self.assertEqual(r.stdout.count("←"), 2)


class CompanyBrainTest(unittest.TestCase):
    """Company Brain: состав файлов и его синхронность с документацией.

    Новый файл brain уезжает в профили только если он в BRAIN_FILES, а число
    файлов заявлено в пяти местах. Проверяем связку целиком: файл на диске
    без строки в BRAIN_FILES — молча не доедет до агента.
    """

    def test_каждый_файл_brain_попадает_в_сборку(self) -> None:
        on_disk = {p.name for p in (REPO_ROOT / "company-brain").glob("*.md")}
        declared = set(build.BRAIN_FILES)
        missing = sorted(on_disk - declared)
        self.assertEqual(
            missing, [],
            f"файлы company-brain не перечислены в BRAIN_FILES и не доедут до профилей: {missing}",
        )
        absent = sorted(declared - on_disk)
        self.assertEqual(absent, [], f"BRAIN_FILES ссылается на отсутствующие файлы: {absent}")

    def test_правовой_контур_есть_в_brain(self) -> None:
        """38-ФЗ — сквозное требование, а не достояние одного навыка."""
        path = REPO_ROOT / "company-brain" / "legal-compliance.md"
        self.assertTrue(path.is_file(), "нет company-brain/legal-compliance.md")
        body = path.read_text(encoding="utf-8")
        for needle in ("38-ФЗ", "18.1", "152-ФЗ", "пометк"):
            with self.subTest(needle=needle):
                self.assertIn(needle, body)

    def test_рабочий_разбор_по_рекламе_доступен_из_скилла(self) -> None:
        """Памятка в brain ссылается на разбор, который лежит в навыке посевов."""
        for rel in ("skills/article-distribution/references/rf-law.md",
                    "skills/article-distribution/references/platform-rules.md"):
            with self.subTest(rel=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), rel)

    def test_число_файлов_brain_совпадает_с_документацией(self) -> None:
        n = len(list((REPO_ROOT / "company-brain").glob("*.md")))
        claims = {
            "README.md": f"Company-Brain-{n}%20files",
            "INSTALL.md": f"company-brain/` ({n} файлов)",
            "profiles/README.md": f"company-brain/` ({n} файлов)",
            "agent-description.md": f"| Company Brain | {n} файлов",
        }
        for rel, needle in claims.items():
            with self.subTest(rel=rel):
                self.assertIn(needle, (REPO_ROOT / rel).read_text(encoding="utf-8"))


class KeysManifestTest(unittest.TestCase):
    """env_requires собирается из навыков агента, а не выдаётся всем одинаково.

    Ошибка тут не видна глазом: профиль ставится, работает, но ключ для его
    навыка установщик не спрашивает — агент уезжает без рабочего инструмента.
    """

    def test_манифест_содержит_ключи_навыка_агента(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            seo = (repo / "dist" / "seo" / "distribution.yaml").read_text(encoding="utf-8")
            self.assertIn("WORDSTAT_API_KEY", seo)
            self.assertIn("WORDSTAT_FOLDER_ID", seo)
            self.assertIn("DEEPSEEK_API_KEY", seo)

    def test_манифест_не_содержит_чужих_ключей(self) -> None:
        """Агент без навыка Wordstat не должен запрашивать его ключ."""
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            orch = (repo / "dist" / "orchestrator" / "distribution.yaml").read_text(encoding="utf-8")
            self.assertNotIn("WORDSTAT_API_KEY", orch)

    def test_env_обязательность_сохраняется(self) -> None:
        with RepoCopy() as repo:
            run_script("build_profiles", repo)
            text = (repo / "dist" / "seo" / "distribution.yaml").read_text(encoding="utf-8")
            block = text.split("WORDSTAT_API_KEY")[1]
            self.assertIn("required: true", block[:200])
            tail = text.split("HERMES_GATEWAY_TOKEN")[1]
            self.assertIn("required: false", tail[:200])

    def test_карта_env_ссылается_на_существующие_навыки(self) -> None:
        """Опечатка в имени навыка молча отключает правило — проверяем имена."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bp_env", SCRIPTS / "build_profiles.py"
        )
        bp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bp)
        slugs = {p.parent.name for p in (REPO_ROOT / "skills").rglob("SKILL.md")}
        for slug in bp.ENV_BY_SKILL:
            with self.subTest(slug=slug):
                self.assertIn(slug, slugs)

    def test_keys_doc_описывает_все_переменные_манифеста(self) -> None:
        """KEYS.md — то, что читает внешний пользователь; он не должен отставать."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_bp_keys", SCRIPTS / "build_profiles.py"
        )
        bp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bp)
        declared = {v[0] for v in bp.BASE_ENV}
        for vars_for_skill in bp.ENV_BY_SKILL.values():
            declared |= {v[0] for v in vars_for_skill}
        body = (REPO_ROOT / "KEYS.md").read_text(encoding="utf-8")
        for var_name in sorted(declared):
            with self.subTest(var=var_name):
                self.assertIn(f"`{var_name}`", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
