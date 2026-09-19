#!/usr/bin/env python3
"""Wordstat через Yandex Cloud Search API v2 — сбор поисковой семантики.

Официальный API: https://searchapi.api.cloud.yandex.net/v2/wordstat/*
Контракт полей — из proto `yandex/cloud/searchapi/v2/wordstat_service.proto`
(репозиторий yandex-cloud/cloudapi), а не из сторонних гайдов.

Запуск: python3 wordstat.py --help
Только stdlib. Ключ и каталог — через переменные окружения или флаги.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://searchapi.api.cloud.yandex.net/v2/wordstat"

# Лимиты из официальной документации (ru/_includes/search-api-limits.md):
# статистика Wordstat — 100 запросов в час, 10 в секунду. getRegionsTree бесплатен
# и в лимит не входит. Держим запас 10% — 90 запросов на прогон.
HOURLY_LIMIT = 100
DEFAULT_BUDGET = 90

DEVICES = ("all", "desktop", "phone", "tablet")
DEVICE_ENUM = {
    "all": "DEVICE_ALL",
    "desktop": "DEVICE_DESKTOP",
    "phone": "DEVICE_PHONE",
    "tablet": "DEVICE_TABLET",
}
PERIOD_ENUM = {
    "monthly": "PERIOD_MONTHLY",
    "weekly": "PERIOD_WEEKLY",
    "daily": "PERIOD_DAILY",
}
REGION_ENUM = {
    "all": "REGION_ALL",
    "cities": "REGION_CITIES",
    "regions": "REGION_REGIONS",
}


class WordstatError(RuntimeError):
    """Ошибка API или конфигурации: печатается без трейсбека."""


def _as_int(value) -> int:
    """int64 в JSON приходит строкой (protobuf JSON-маппинг) — приводим явно."""
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _rfc3339(value: str) -> str:
    """Дата → Timestamp для API: '2026-08-01' → '2026-08-01T00:00:00Z'."""
    value = value.strip()
    if "T" in value:
        return value if value.endswith("Z") or "+" in value else value + "Z"
    datetime.strptime(value, "%Y-%m-%d")  # валидация формата
    return f"{value}T00:00:00Z"


class Budget:
    """Локальный счётчик запросов в скользящем часе.

    Серверный лимит — 100 запросов в час; без локального счётчика прогон
    на 300 seed-фраз упирается в `code 8` на середине и теряет уже собранное.
    """

    def __init__(self, state_file: Path, budget: int):
        self.state_file = state_file
        self.budget = budget
        self.stamps: list[float] = self._load()

    def _load(self) -> list[float]:
        if not self.state_file.is_file():
            return []
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        now = time.time()
        return [float(t) for t in data.get("stamps", []) if now - float(t) < 3600]

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps({"stamps": self.stamps}, ensure_ascii=False), encoding="utf-8"
        )

    def used_last_hour(self) -> int:
        now = time.time()
        self.stamps = [t for t in self.stamps if now - t < 3600]
        return len(self.stamps)

    def check(self) -> None:
        used = self.used_last_hour()
        if used >= HOURLY_LIMIT:
            wait = int(3600 - (time.time() - min(self.stamps)) + 1)
            raise WordstatError(
                f"исчерпан часовой лимит API: {used}/{HOURLY_LIMIT} запросов за последний час; "
                f"следующий слот примерно через {wait} с. Собранное сохраните и продолжите позже"
            )
        if used >= self.budget:
            raise WordstatError(
                f"достигнут бюджет прогона: {used} из {self.budget} запросов "
                f"(лимит API {HOURLY_LIMIT}/час, запас 10%). "
                f"Продолжить: --budget больше, либо новый прогон после сброса часа"
            )

    def spend(self) -> None:
        self.stamps.append(time.time())
        self._save()


class Wordstat:
    def __init__(self, api_key: str, folder_id: str, cache_dir: Path, budget: Budget,
                 delay: float = 0.3, dry_run: bool = False):
        self.api_key = api_key
        self.folder_id = folder_id
        self.cache_dir = cache_dir
        self.budget = budget
        self.delay = delay
        self.dry_run = dry_run
        self.requests_made = 0

    # --- транспорт ---------------------------------------------------------
    def _call(self, method: str, body: dict[str, object]) -> dict:
        body: dict[str, object] = dict(body)
        if method != "getRegionsTree":
            body.setdefault("folderId", self.folder_id)
        if self.dry_run:
            print(f"    [dry-run] POST {method} {json.dumps(body, ensure_ascii=False)}")
            return {}
        self.budget.check()
        req = urllib.request.Request(
            f"{API}/{method}",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            raise WordstatError(self._explain(exc.code, raw)) from None
        except urllib.error.URLError as exc:
            raise WordstatError(f"сеть недоступна: {exc.reason}") from None
        self.budget.spend()
        self.requests_made += 1
        if self.delay:
            time.sleep(self.delay)
        return payload

    @staticmethod
    def _explain(http_code: int, raw: str) -> str:
        """Человекочитаемая расшифровка ошибки API (коды — из gRPC-контракта)."""
        try:
            data = json.loads(raw)
            code = data.get("code")
            message = (data.get("message") or "").strip()
        except ValueError:
            return f"HTTP {http_code}: {raw[:300]}"
        hints = {
            3: "проверьте обязательные поля запроса (phrase, numPhrases, period, fromDate)",
            8: f"исчерпана квота: статистика — {HOURLY_LIMIT} запросов в час",
            16: "ключ не принят: проверьте WORDSTAT_API_KEY и роль search-api.webSearchUser",
            7: "нет прав: у сервисного аккаунта должна быть роль search-api.webSearchUser",
        }
        hint = hints.get(code, "")
        return f"HTTP {http_code}, code {code}: {message}" + (f" — {hint}" if hint else "")

    # --- методы ------------------------------------------------------------
    def regions_tree(self) -> list[dict]:
        """Дерево регионов. Бесплатный метод — кэшируем, в лимит не считается."""
        cache = self.cache_dir / "regions-tree.json"
        if cache.is_file():
            return json.loads(cache.read_text(encoding="utf-8")).get("regions", [])
        data = self._call("getRegionsTree", {})
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data.get("regions", [])

    def top(self, phrase: str, num: int = 100, regions: list[str] | None = None,
            devices: list[str] | None = None) -> dict:
        """Топ запросов за последние 30 дней + похожие запросы (ассоциации)."""
        body: dict[str, object] = {"phrase": phrase, "numPhrases": num}
        if regions:
            body["regions"] = regions
        if devices:
            body["devices"] = [DEVICE_ENUM[d] for d in devices]
        data = self._call("topRequests", body)
        return {
            "phrase": phrase,
            "totalCount": _as_int(data.get("totalCount")),
            "results": [
                {"phrase": r.get("phrase", ""), "count": _as_int(r.get("count"))}
                for r in data.get("results", [])
            ],
            "associations": [
                {"phrase": r.get("phrase", ""), "count": _as_int(r.get("count"))}
                for r in data.get("associations", [])
            ],
        }

    def dynamics(self, phrase: str, period: str, from_date: str, to_date: str | None = None,
                 regions: list[str] | None = None, devices: list[str] | None = None) -> dict:
        """Частота запроса во времени: месяц/неделя/день + доля от всех запросов."""
        body: dict[str, object] = {
            "phrase": phrase,
            "period": PERIOD_ENUM[period],
            "fromDate": _rfc3339(from_date),
        }
        if to_date:
            body["toDate"] = _rfc3339(to_date)
        if regions:
            body["regions"] = regions
        if devices:
            body["devices"] = [DEVICE_ENUM[d] for d in devices]
        data = self._call("dynamics", body)
        return {
            "phrase": phrase,
            "period": period,
            "results": [
                {
                    "date": (r.get("date") or "")[:10],
                    "count": _as_int(r.get("count")),
                    "share": round(_as_float(r.get("share")), 10),
                }
                for r in data.get("results", [])
            ],
        }

    def regions_distribution(self, phrase: str, mode: str = "all",
                             devices: list[str] | None = None) -> dict:
        """География запроса + affinity_index (регион против страны)."""
        body: dict[str, object] = {"phrase": phrase, "region": REGION_ENUM[mode]}
        if devices:
            body["devices"] = [DEVICE_ENUM[d] for d in devices]
        data = self._call("regions", body)
        labels = {str(r["id"]): r["label"] for r in _flatten_regions(self.regions_tree())}
        return {
            "phrase": phrase,
            "results": [
                {
                    "region": str(r.get("region", "")),
                    "label": labels.get(str(r.get("region", "")), ""),
                    "count": _as_int(r.get("count")),
                    "share": round(_as_float(r.get("share")), 10),
                    "affinityIndex": round(_as_float(r.get("affinityIndex")), 4),
                }
                for r in data.get("results", [])
            ],
        }


def _flatten_regions(tree: list[dict]) -> list[dict]:
    """Плоский список {id, label} из дерева регионов (рекурсивно)."""
    out: list[dict] = []
    for node in tree:
        out.append({"id": node.get("id", ""), "label": node.get("label", "")})
        out.extend(_flatten_regions(node.get("children") or []))
    return out


def _client(args) -> Wordstat:
    api_key = args.api_key or os.getenv("WORDSTAT_API_KEY", "").strip()
    folder_id = (args.folder_id or os.getenv("WORDSTAT_FOLDER_ID", "")).strip()
    if not api_key:
        raise WordstatError(
            "нет ключа API: задайте WORDSTAT_API_KEY или флаг --api-key. "
            "Ключ — сервисный аккаунт Yandex Cloud с ролью search-api.webSearchUser "
            "(подробности — references/api-contract.md)"
        )
    if not folder_id:
        raise WordstatError(
            "нет folderId: задайте WORDSTAT_FOLDER_ID или флаг --folder-id "
            "(20 символов, ID каталога Yandex Cloud; лишний пробел из UI ломает запрос)"
        )
    cache_dir = Path(args.cache_dir).expanduser()
    budget = Budget(cache_dir / "requests.json", args.budget)
    return Wordstat(api_key, folder_id, cache_dir, budget, args.delay, args.dry_run)


def _emit(data, pretty: bool, out: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"записано: {path}")
    else:
        print(text)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Wordstat через Yandex Cloud Search API v2 (семантика, динамика, гео)"
    )
    ap.add_argument("--api-key", help="или переменная WORDSTAT_API_KEY")
    ap.add_argument("--folder-id", help="или переменная WORDSTAT_FOLDER_ID")
    ap.add_argument("--cache-dir", default="~/.cache/wordstat",
                    help="кэш дерева регионов и счётчик часового лимита")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                    help=f"максимум запросов на прогон (лимит API {HOURLY_LIMIT}/час)")
    ap.add_argument("--delay", type=float, default=0.3, help="пауза между запросами, с")
    ap.add_argument("--pretty", action="store_true", help="человекочитаемый JSON")
    ap.add_argument("--out", help="сохранить результат в файл")
    ap.add_argument("--dry-run", action="store_true", help="показать запросы без вызовов API")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_scope(p):
        p.add_argument("--regions", default="", help="ID регионов через запятую (225 — вся Россия)")
        p.add_argument("--devices", default="", help="all|desktop|phone|tablet, через запятую")

    p_top = sub.add_parser("top", help="топ запросов за 30 дней + похожие запросы")
    p_top.add_argument("phrase")
    p_top.add_argument("--num", type=int, default=100, help="1..2000 (больше 250 API не вернёт)")
    add_scope(p_top)

    p_dyn = sub.add_parser("dynamics", help="частота запроса во времени (сезонность)")
    p_dyn.add_argument("phrase")
    p_dyn.add_argument("--period", choices=sorted(PERIOD_ENUM), default="monthly")
    p_dyn.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    p_dyn.add_argument("--to", dest="to_date", help="YYYY-MM-DD (по умолчанию — сегодня)")
    add_scope(p_dyn)

    p_reg = sub.add_parser("regions", help="география запроса + affinity index")
    p_reg.add_argument("phrase")
    p_reg.add_argument("--mode", choices=sorted(REGION_ENUM), default="all")
    p_reg.add_argument("--devices", default="")

    sub.add_parser("regions-tree", help="дерево регионов (бесплатный метод, кэшируется)")

    p_col = sub.add_parser("collect", help="пакетный сбор семантики по списку seed-фраз")
    p_col.add_argument("--seeds", nargs="+", help="seed-фразы (или --seeds-file)")
    p_col.add_argument("--seeds-file", help="файл: по одной фразе в строке")
    p_col.add_argument("--num", type=int, default=100)
    p_col.add_argument("--expand", action="store_true",
                       help="после топа раскрывать верхние вложенные фразы (2-й проход)")
    p_col.add_argument("--top-n", type=int, default=5, help="сколько фраз раскрывать при --expand")
    add_scope(p_col)

    args = ap.parse_args()
    try:
        ws = _client(args)
        regions = [r.strip() for r in getattr(args, "regions", "").split(",") if r.strip()]
        devices = [d.strip() for d in getattr(args, "devices", "").split(",") if d.strip()]
        for d in devices:
            if d not in DEVICES:
                raise WordstatError(f"устройство «{d}» не из списка {', '.join(DEVICES)}")

        if args.cmd == "top":
            result = ws.top(args.phrase, args.num, regions, devices)
        elif args.cmd == "dynamics":
            result = ws.dynamics(args.phrase, args.period, args.from_date, args.to_date,
                                 regions, devices)
        elif args.cmd == "regions":
            result = ws.regions_distribution(args.phrase, args.mode, devices)
        elif args.cmd == "regions-tree":
            result = {"regions": ws.regions_tree()}
        else:  # collect
            seeds = list(args.seeds or [])
            if args.seeds_file:
                path = Path(args.seeds_file).expanduser()
                if not path.is_file():
                    raise WordstatError(f"нет файла seed-фраз: {path}")
                seeds += [
                    line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
            if not seeds:
                raise WordstatError("нет seed-фраз: --seeds или --seeds-file")
            collected = []
            for seed in seeds:
                print(f"  [{ws.requests_made}] {seed} …", file=sys.stderr, flush=True)
                item = ws.top(seed, args.num, regions, devices)
                print(
                    f"      фраз: {len(item['results'])}, всего за 30 дней: {item['totalCount']}, "
                    f"ассоциаций: {len(item['associations'])}",
                    file=sys.stderr,
                )
                if args.expand and item["results"]:
                    item["children"] = {}
                    for child in item["results"][: args.top_n]:
                        child_phrase = child["phrase"]
                        nested = ws.top(child_phrase, args.num, regions, devices)
                        item["children"][child_phrase] = nested["results"]
                        print(f"      ↳ {child_phrase}: {len(nested['results'])} фраз",
                              file=sys.stderr)
                collected.append(item)
            result = {
                "collectedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "requestsMade": ws.requests_made,
                "budgetUsed": f"{ws.budget.used_last_hour()}/{HOURLY_LIMIT} за последний час",
                "seeds": collected,
            }
        _emit(result, args.pretty, args.out)
        return 0
    except WordstatError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("прервано", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
