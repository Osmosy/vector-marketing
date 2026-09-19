#!/usr/bin/env python3
"""Журнал посевов статей: UTM-разметка, учёт публикаций, метрики по площадкам.

Зачем: «посевы» без журнала и разметки не измеряются — через месяц нельзя
сказать, какая площадка дала переходы и заявки, а какая только показы.
Скрипт ведёт одну плоскую базу (JSONL) и считает сводку по площадкам.

Запуск: python3 seed_log.py --help
Только stdlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

DEFAULT_LOG = "~/.local/share/vector-marketing/seed-log.jsonl"

# Площадки, для которых в скилле зафиксированы проверенные правила.
KNOWN_PLATFORMS = {
    "habr": "Хабр",
    "vc": "vc.ru",
    "dzen": "Дзен",
    "medium": "Medium",
    "tenchat": "TenChat",
    "linkedin": "LinkedIn",
    "telegram": "Telegram-канал",
    "blog": "свой блог",
    "other": "другое",
}

# utm_source → человекочитаемое имя в отчёте.
SOURCE_ALIASES = {
    "habr": "habr",
    "vc": "vc",
    "vc.ru": "vc",
    "dzen": "dzen",
    "zen": "dzen",
    "medium": "medium",
    "tenchat": "tenchat",
    "linkedin": "linkedin",
    "tg": "telegram",
    "telegram": "telegram",
    "blog": "blog",
}


def canonical_source(value: str) -> str:
    """Привести utm_source к каноническому имени площадки.

    Без этого «vc», «vc.ru» и «VC» уезжают в отчёт тремя строками, и метрика
    площадки расползается на дубли.
    """
    key = value.strip().lower()
    return SOURCE_ALIASES.get(key, key)


def build_utm(base_url: str, platform: str, campaign: str, content: str = "",
              term: str = "", source: str = "") -> str:
    """Размеченный URL: utm_source=площадка, utm_medium=content, utm_campaign=<кампания>.

    Разметка обязательна: посевы оцениваются по переходам и заявкам, а не по
    числу публикаций. `content` различает форматы одного материала на площадке.
    """
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"нужен абсолютный URL, получено «{base_url}»")
    params = [
        ("utm_source", canonical_source(source or platform)),
        ("utm_medium", "content"),
        ("utm_campaign", campaign.strip()),
    ]
    if content:
        params.append(("utm_content", content.strip()))
    if term:
        params.append(("utm_term", term.strip()))
    query = parts.query
    extra = urlencode(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       f"{query}&{extra}" if query else extra, parts.fragment))


def load_log(path: Path) -> list[dict]:
    """Прочитать журнал. Битые строки не роняют отчёт — они возвращаются отдельно."""
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue  # повреждённая строка не должна ломать сводку
    return rows


def append_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Сводка по площадкам: публикации, показы, переходы, заявки, CTR, конверсия.

    impressions/clicks/leads заполняются по факту (вручную или из Метрики);
    строки без метрик тоже считаются — иначе площадка, где публикация вышла,
    но данные ещё не сняты, исчезнет из отчёта.
    """
    agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"publications": 0.0, "impressions": 0.0, "clicks": 0.0, "leads": 0.0}
    )
    for row in rows:
        src = canonical_source(str(row.get("source") or row.get("platform") or "other"))
        slot = agg[src]
        slot["publications"] += 1
        for key in ("impressions", "clicks", "leads"):
            try:
                slot[key] += float(row.get(key) or 0)
            except (TypeError, ValueError):
                pass
    for slot in agg.values():
        slot["ctr"] = round(slot["clicks"] / slot["impressions"], 4) if slot["impressions"] else 0.0
        slot["cr"] = round(slot["leads"] / slot["clicks"], 4) if slot["clicks"] else 0.0
    return dict(sorted(agg.items()))


def cmd_add(args) -> int:
    platform = canonical_source(args.platform)
    if platform not in KNOWN_PLATFORMS:
        print(f"ошибка: площадка «{args.platform}» неизвестна; "
              f"доступны: {', '.join(sorted(KNOWN_PLATFORMS))} "
              f"(алиасы: vc.ru→vc, zen→dzen, tg→telegram)", file=sys.stderr)
        return 1
    row = {
        "date": args.date or date.today().isoformat(),
        "platform": platform,
        "source": canonical_source(args.platform),
        "title": args.title,
        "url": args.url,
        "account": args.account or "",
        "format": args.format or "",
        "marked_as_ads": bool(args.marked_as_ads),
        "impressions": args.impressions,
        "clicks": args.clicks,
        "leads": args.leads,
    }
    append_row(Path(args.log).expanduser(), row)
    print(f"записано: {row['date']} {row['platform']} — {row['title']}")
    return 0


def cmd_summary(args) -> int:
    rows = load_log(Path(args.log).expanduser())
    if args.platform:
        rows = [r for r in rows if canonical_source(str(r.get("platform", ""))) == args.platform]
    if not rows:
        print("журнал пуст — нечего считать")
        return 0
    data = summarize(rows)
    print(f"{'площадка':<12} {'публ.':>6} {'показы':>8} {'переходы':>9} {'заявки':>7} {'CTR':>7} {'CR':>7}")
    for src, s in data.items():
        print(f"{src:<12} {int(s['publications']):>6} {int(s['impressions']):>8} "
              f"{int(s['clicks']):>9} {int(s['leads']):>7} {s['ctr']:>7.2%} {s['cr']:>7.2%}")
    total = {k: sum(s[k] for s in data.values()) for k in ("publications", "impressions", "clicks", "leads")}
    print(f"{'ИТОГО':<12} {int(total['publications']):>6} {int(total['impressions']):>8} "
          f"{int(total['clicks']):>9} {int(total['leads']):>7}")
    # Публикации без заполненных метрик — самая частая причина «посевы не работают».
    empty = [r for r in rows if not any(r.get(k) for k in ("impressions", "clicks", "leads"))]
    if empty:
        print(f"\nбез метрик: {len(empty)} публикация(й) — снимите показы/переходы "
              f"(Метрика по utm_source или статистика площадки), иначе вывод неполный")
    unmarked = [r for r in rows if not r.get("marked_as_ads")]
    if unmarked:
        print(f"без пометки рекламы: {len(unmarked)} — проверьте, не является ли "
              f"материал рекламой по 38-ФЗ (см. references/platform-rules.md)")
    return 0


def cmd_utm(args) -> int:
    try:
        print(build_utm(args.base, args.platform, args.campaign, args.content, args.term, args.source))
    except ValueError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_platforms(_args) -> int:
    for key, label in sorted(KNOWN_PLATFORMS.items()):
        print(f"{key:<10} {label}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Журнал посевов статей и метрики по площадкам")
    ap.add_argument("--log", default=DEFAULT_LOG, help=f"файл журнала (по умолчанию {DEFAULT_LOG})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="записать публикацию")
    p_add.add_argument("--platform", required=True, help="ключ площадки (см. platforms)")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--url", required=True, help="URL публикации с UTM (см. utm)")
    p_add.add_argument("--date", help="YYYY-MM-DD (по умолчанию — сегодня)")
    p_add.add_argument("--account", help="аккаунт, с которого опубликовано")
    p_add.add_argument("--format", help="формат: лонгрид, пост, кейс, дайджест…")
    p_add.add_argument("--marked-as-ads", action="store_true",
                       help="материал помечен как реклама/спонсорский (38-ФЗ)")
    p_add.add_argument("--impressions", type=int, default=0)
    p_add.add_argument("--clicks", type=int, default=0)
    p_add.add_argument("--leads", type=int, default=0)
    p_add.set_defaults(func=cmd_add)

    p_sum = sub.add_parser("summary", help="сводка по площадкам")
    p_sum.add_argument("--platform", help="только одна площадка")
    p_sum.set_defaults(func=cmd_summary)

    p_utm = sub.add_parser("utm", help="сгенерировать размеченный URL")
    p_utm.add_argument("--base", required=True, help="URL материала на своём сайте")
    p_utm.add_argument("--platform", required=True)
    p_utm.add_argument("--campaign", required=True)
    p_utm.add_argument("--content", default="", help="различить форматы одного материала")
    p_utm.add_argument("--term", default="")
    p_utm.add_argument("--source", default="", help="переопределить utm_source")
    p_utm.set_defaults(func=cmd_utm)

    sub.add_parser("platforms", help="список площадок").set_defaults(func=cmd_platforms)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
