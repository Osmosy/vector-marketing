#!/usr/bin/env python3
"""GEO-прогон: как генеративные движки отвечают про бренд и конкурентов.

Отвечает на вопросы, которые нельзя закрыть рассуждением:
  - упоминается ли бренд в ответах на профильные промпты;
  - на каком месте относительно конкурентов;
  - в каком тональном контексте;
  - на какие источники опирается модель (откуда пойдёт цитирование).

Работает через любой OpenAI-совместимый эндпоинт: облачный или локальный.
Разбор ответов детерминированный (regex/эвристики), без «на глаз»: сырые ответы
сохраняются рядом со сводкой, чтобы вывод можно было перепроверить.

Запуск: python3 geo_probe.py --help
Только stdlib.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Тональные маркеры вокруг упоминания бренда. Списки сознательно короткие:
# расплывчатый словарь даёт ложные срабатывания, а вывод должен быть защитимым.
POSITIVE_MARKERS = (
    "лучш", "надёжн", "надежн", "рекоменд", "популярн", "удобн", "качествен",
    "хорош", "эффективн", "лидир", "сильн", "подход", "безопасн", "гибк",
)
NEGATIVE_MARKERS = (
    "устарел", "слаб", "проблем", "недостат", "минус", "жалоб", "плох",
    "не работает", "риск", "дорог", "не рекоменд", "спорн", "уязвим",
)

# Ранжированные списки: «1. …», «- …», «**Название**».
LIST_ITEM_RE = re.compile(r"(?m)^\s{0,4}(?:\d{1,2}[.)]|[-*•]|\*\*[^*]{2,60}\*\*)\s*")
URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?:[/\w\-?=&%.]*)?")
MD_LINK_RE = re.compile(r"\[[^\]]{1,80}\]\(\s*(https?://[^)\s]+)\s*\)")
# Модели часто называют источник без ссылки: `owner/repo`, `owner/repo.py`.
# Без этого шага «откуда идёт цитирование» остаётся пустым при живом ответе.
REPO_SLUG_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9][\w.-]{1,38}/[A-Za-z0-9][\w.-]{1,38})(?![\w/-])")
SLUG_STOPWORDS = ("и/или", "т.е", "т.д", "т.п", "как/или")


def norm(text: str) -> str:
    return text.lower().replace("ё", "е")


# Хосты-платформы: их вхождение в ответ ничего не говорит о бренде
GENERIC_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org", "medium.com", "habr.com", "vc.ru",
    "youtube.com", "t.me", "telegram.me", "x.com", "twitter.com", "linkedin.com",
}

# «Данных нет / связь не подтверждена» — отдельный результат прогона: «нас не
# знают» и «нас знают, но не подтверждают» — разные задачи. Дословных шаблонов
# мало: формулировка живая («публично подтверждённой связи между … и … нет»),
# поэтому ищем ДВА сигнала в одном предложении — предмет и отрицание.
UNKNOWN_SUBJECTS = ("связ", "подтвержд", "данн", "информац", "найден", "известн", "упоминан")
UNKNOWN_NEGATIONS = ("нет", "не ", "ничего не", "отсутств", "не удалось", "не могу")
SENTENCE_RE = re.compile(r"[.!?\n]+")


def brand_forms(entry: dict) -> list[str]:
    """Все написания бренда: имя + явные алиасы + хост и путь сайта.

    Из сайта берём полный хост и последний значимый сегмент пути, но не имя
    платформы: «github» в ответе — это про хостинг, а не про бренд.
    """
    forms = [entry.get("name", "")]
    forms += [a for a in (entry.get("aliases") or []) if a]
    for site in entry.get("sites") or []:
        cleaned = re.sub(r"^https?://", "", site).rstrip("/")
        host = cleaned.split("/")[0].lower()
        if host.startswith("www."):
            host = host[4:]
        if host not in GENERIC_HOSTS:
            forms.append(host)
            forms.append(host.split(".")[0])
        for seg in cleaned.split("/")[1:]:
            if seg and len(seg) > 2 and seg.lower() not in ("index.html",):
                forms.append(seg)
    out: list[str] = []
    for f in forms:
        f = norm(f.strip())
        if f and len(f) > 1 and f not in out:
            out.append(f)
    return out


def find_mentions(text: str, forms: list[str]) -> list[tuple[int, int, str]]:
    """Позиции упоминаний бренда: (начало, конец, найденная форма).

    Ищем по границе слова: без неё «вектор» ловится внутри «векторный», а
    отчёт получает упоминания, которых в ответе модели нет.
    """
    hits: list[tuple[int, int, str]] = []
    hay = norm(text)
    for form in forms:
        pattern = r"(?<![а-яa-z0-9])" + re.escape(form) + r"(?![а-яa-z0-9])"
        for m in re.finditer(pattern, hay):
            hits.append((m.start(), m.end(), form))
    # одна и та же позиция, найденная двумя формами (имя и домен), — это одно упоминание
    dedup: list[tuple[int, int, str]] = []
    for hit in sorted(hits):
        if dedup and hit[0] < dedup[-1][1]:
            continue
        dedup.append(hit)
    return dedup


def mention_position(text: str, offset: int) -> int:
    """Порядковый номер упоминания в ответе (1 = первое имя в тексте).

    Это не «место в топе», а позиция в потоке ответа: для «первая рекомендация
    или в конце списка» этого достаточно и не требует разметки структуры.
    """
    return len([m for m in LIST_ITEM_RE.finditer(text) if m.start() <= offset]) + 1


def sentiment_around(text: str, start: int, end: int, window: int = 220) -> str:
    """Тональность контекста вокруг упоминания: positive / negative / neutral.

    Смотрим окно вокруг, а не весь ответ: ответ целиком почти всегда содержит
    и плюсы, и минусы разных брендов.
    """
    fragment = norm(text[max(0, start - window): end + window])
    pos = sum(1 for m in POSITIVE_MARKERS if m in fragment)
    neg = sum(1 for m in NEGATIVE_MARKERS if m in fragment)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def cited_domains(text: str) -> list[str]:
    """Домены, на которые опирается ответ: ссылки + markdown-ссылки.

    Это и есть ответ на вопрос «откуда идёт цитирование» — сюда потом
    заказываются/сеются статьи.
    """
    hosts: list[str] = []
    # Оба вида собираем ВМЕСТЕ: раньше наличие одной markdown-ссылки отключало
    # поиск обычных URL, и часть источников терялась. Плюс MD_LINK_RE отдаёт
    # ссылку целиком — схему нужно снять, иначе «домен» выходит как «https:».
    for url in MD_LINK_RE.findall(text) + URL_RE.findall(text):
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        if host.startswith("www."):
            host = host[4:]
        if host and host not in hosts:
            hosts.append(host)
    return hosts


def source_slugs(text: str) -> list[str]:
    """Названные моделью источники без ссылок: `owner/repo`, `owner/repo.json`.

    Модель часто перечисляет проекты слагом без URL — для вопроса «откуда идёт
    цитирование» это тот же ответ, что и домен, поэтому собираем оба вида.
    """
    out: list[str] = []
    for slug in REPO_SLUG_RE.findall(text):
        # Хвостовая пунктуация липнет к слагу («Marketing/Cutco.») — снимаем её,
        # иначе в отчёте появляются источники, которых модель не называла.
        slug = slug.rstrip(".,;:!?»)\"'")
        low = slug.lower()
        if low in SLUG_STOPWORDS:
            continue
        if "/" not in slug or slug.startswith(("http", "www")):
            continue
        # Верхний регистр в обоих сегментах и длина 1 — обычно «И/Или» и т.п.
        if len(slug) < 4 or slug.count("/") > 2:
            continue
        if slug not in out:
            out.append(slug)
    return out


def detect_unknown_claim(text: str) -> bool:
    """Есть ли в ответе утверждение «данных о бренде нет / связь не подтверждена».

    Проверяем по предложениям: нужен предмет (связь, подтверждение, данные,
    информация, упоминание) И отрицание в том же предложении. Так «связи между
    проектом X и компанией Y нет» ловится, а «есть данные о компании X» — нет.
    """
    for sentence in SENTENCE_RE.split(text):
        low = norm(sentence)
        if not low.strip():
            continue
        if any(subj in low for subj in UNKNOWN_SUBJECTS) and any(
            neg in low for neg in UNKNOWN_NEGATIONS
        ):
            return True
    return False


def analyze_answer(text: str, brand: dict, competitors: list[dict]) -> dict:
    forms = brand_forms(brand)
    hits = find_mentions(text, forms)
    # Имя бренда может совпасть с чужим (проверено: «Vector Marketing» у модели —
    # это американская MLM-компания, а не наш репозиторий). Если совпало только
    # общее имя, а ни один различающий алиас/домен не встретился, помечаем
    # прогон как требующий ручной проверки, а не считаем упоминанием.
    distinctive = [norm(a) for a in (brand.get("aliases") or [])]
    distinctive += [norm(s.split("//")[-1].split("/")[0]) for s in (brand.get("sites") or [])]
    distinguishing_found = any(
        find_mentions(text, [d]) for d in distinctive if d and len(d) > 2
    )
    # Ответ может упоминать бренд ровно для того, чтобы сказать «связи нет».
    # Для GEO это отдельный результат, и в отчёте он должен быть виден.
    claims_unknown = detect_unknown_claim(text)
    comp_report = {}
    for comp in competitors:
        comp_hits = find_mentions(text, brand_forms(comp))
        comp_report[comp.get("name", "")] = {
            "mentioned": bool(comp_hits),
            "count": len(comp_hits),
            "firstPosition": mention_position(text, comp_hits[0][0]) if comp_hits else None,
        }
    return {
        "brand": {
            "mentioned": bool(hits),
            "count": len(hits),
            "firstPosition": mention_position(text, hits[0][0]) if hits else None,
            "sentiment": sentiment_around(text, *hits[0][:2]) if hits else None,
            # True — имя найдено, но различающих признаков нет: вероятен омоним.
            "ambiguousEntity": bool(hits) and bool(distinctive) and not distinguishing_found,
            "distinguishingMatch": distinguishing_found,
            # True — модель прямо говорит, что данных о бренде нет / связь не
            # подтверждена: это задача на публикации, а не на «улучшение тональности».
            "claimsUnknown": claims_unknown,
        },
        "competitors": comp_report,
        "citedDomains": cited_domains(text),
        "sourceSlugs": source_slugs(text),
        "answerChars": len(text),
    }


def normalize_base_url(raw: str) -> str:
    """Базовый URL до `/chat/completions`.

    Провайдеры объявляют версию по-разному: у одного база оканчивается на `/v1`,
    у другого на `/v4` — дописывать `/v1` всем подряд значит получить 404 на
    ровном месте (проверено на z.ai: `/v4/v1/chat/completions`).
    """
    base = raw.strip().rstrip("/")
    if not re.search(r"/v\d+[a-z]*$", base):
        base += "/v1"
    return base


def call_model(cfg: dict, prompt: str, timeout: int = 120) -> tuple[str, str]:
    """Запрос к OpenAI-совместимому эндпоинту. Возвращает (текст, ошибка)."""
    key_env = cfg.get("api_key_env")
    key = os.getenv(key_env, "").strip() if key_env else ""
    if key_env and not key:
        return "", f"нет переменной окружения {key_env}"
    base = normalize_base_url(cfg["base_url"])
    body = {
        "model": cfg["model"],
        "messages": [
            # temperature 0 — прогон должен быть воспроизводимым: сравнивать
            # «до/после» по публикациям можно только при стабильном сэмплинге.
            {"role": "system", "content": cfg.get("system") or
             "Отвечай по существу на русском языке, перечисляя конкретные решения и названия."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
        method="POST",
    )
    last_err = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="ignore")
            # 429 и 5xx — временные: повторяем с паузой; 4xx — нет смысла
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                last_err = f"HTTP {exc.code}: {raw[:200]}"
                time.sleep(2 * (attempt + 1))
                continue
            return "", f"HTTP {exc.code}: {raw[:200]}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"сеть: {exc}"
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            return "", last_err
    else:
        return "", last_err
    choices = data.get("choices") or []
    if not choices:
        return "", f"пустой ответ провайдера: {json.dumps(data, ensure_ascii=False)[:200]}"
    return (choices[0].get("message") or {}).get("content", ""), ""


def summarize(runs: list[dict], brand_name: str) -> dict:
    """Сводка по моделям: доля упоминаний, средняя позиция, тональность, домены."""
    by_model: dict[str, dict] = {}
    domain_counter: dict[str, int] = {}
    for run in runs:
        slot = by_model.setdefault(run["model"], {
            "prompts": 0, "mentioned": 0, "ambiguous": 0, "positions": [],
            "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
            "competitorsMentioned": 0, "sourceSlugs": {}, "domains": {},
        })
        slot["prompts"] += 1
        b = run["analysis"]["brand"]
        if b.get("claimsUnknown"):
            slot["claimsUnknown"] = slot.get("claimsUnknown", 0) + 1
        if b["mentioned"]:
            slot["mentioned"] += 1
            if b.get("ambiguousEntity"):
                slot["ambiguous"] += 1
            if b["firstPosition"]:
                slot["positions"].append(b["firstPosition"])
            slot["sentiment"][b["sentiment"] or "neutral"] += 1
        for slug in run["analysis"].get("sourceSlugs", []):
            slot["sourceSlugs"][slug] = slot["sourceSlugs"].get(slug, 0) + 1
        slot["competitorsMentioned"] += sum(
            1 for c in run["analysis"]["competitors"].values() if c["mentioned"]
        )
        for host in run["analysis"]["citedDomains"]:
            domain_counter[host] = domain_counter.get(host, 0) + 1
            slot["domains"][host] = slot["domains"].get(host, 0) + 1

    for name, slot in by_model.items():
        n = max(1, slot["prompts"])
        slot["mentionRate"] = round(slot["mentioned"] / n, 3)
        slot["avgFirstPosition"] = (
            round(sum(slot["positions"]) / len(slot["positions"]), 2) if slot["positions"] else None
        )
        # Домены — по конкретной модели: у разных движков разные источники, и
        # общий счётчик на всех делал колонку бессмысленной.
        slot["topCitedDomains"] = [
            h for h, _ in sorted(slot["domains"].items(), key=lambda x: (-x[1], x[0]))[:8]
        ]
        slot.pop("domains")
        slot.pop("positions")
    return {
        "brand": brand_name,
        "models": by_model,
        "topCitedDomains": [h for h, _ in sorted(domain_counter.items(), key=lambda x: (-x[1], x[0]))[:15]],
    }


def load_json(path: str, what: str):
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"нет файла {what}: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"{what}: битый JSON — {exc}") from None


def main() -> int:
    ap = argparse.ArgumentParser(description="GEO-прогон: упоминания бренда в ответах генеративных движков")
    ap.add_argument("--config", required=True, help="JSON: brand, competitors, prompts, models, опц. repeat")
    ap.add_argument("--out", help="файл результата (по умолчанию geo-<brand>-<дата>.json)")
    ap.add_argument("--out-dir", default=".", help="каталог для результата")
    ap.add_argument("--only-models", help="имена моделей через запятую (для точечного перепрогона)")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--dry-run", action="store_true", help="показать план вызовов без запросов")
    args = ap.parse_args()

    cfg = load_json(args.config, "конфиг")
    brand = cfg.get("brand") or {}
    if not brand.get("name"):
        raise SystemExit("в конфиге нужен brand.name")
    prompts = cfg.get("prompts") or []
    if not prompts:
        raise SystemExit("в конфиге нужен непустой prompts")
    models = cfg.get("models") or []
    if not models:
        raise SystemExit("в конфиге нужен непустой models (base_url + model)")
    if args.only_models:
        wanted = {m.strip() for m in args.only_models.split(",") if m.strip()}
        models = [m for m in models if m.get("name") in wanted]
        if not models:
            raise SystemExit(f"нет моделей из списка: {', '.join(sorted(wanted))}")
    repeat = int(cfg.get("repeat") or 1)
    competitors = cfg.get("competitors") or []

    plan = len(models) * len(prompts) * repeat
    print(f"бренд: {brand['name']} | моделей: {len(models)} | промптов: {len(prompts)} "
          f"| повторов: {repeat} → вызовов: {plan}", file=sys.stderr)
    if args.dry_run:
        for m in models:
            for p in prompts:
                print(f"  {m['name']:16s} ← {p}")
        return 0

    runs: list[dict] = []
    for m in models:
        for prompt in prompts:
            for attempt in range(repeat):
                text, err = call_model(m, prompt, args.timeout)
                if err:
                    print(f"  ошибка {m['name']}: {err}", file=sys.stderr)
                    runs.append({
                        "model": m["name"], "prompt": prompt, "attempt": attempt + 1,
                        "error": err, "answer": "", "analysis": None,
                    })
                    continue
                runs.append({
                    "model": m["name"], "prompt": prompt, "attempt": attempt + 1,
                    "error": "", "answer": text,
                    "analysis": analyze_answer(text, brand, competitors),
                })
                b = runs[-1]["analysis"]["brand"]
                flag = "✓" if b["mentioned"] else "—"
                print(f"  {flag} {m['name']:16s} {prompt[:60]}", file=sys.stderr)
                time.sleep(float(cfg.get("delay") or 0.2))

    ok_runs = [r for r in runs if r.get("analysis")]
    result = {
        "probedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brand": brand,
        "competitors": competitors,
        "models": [{"name": m["name"], "model": m.get("model"), "base_url": m.get("base_url")} for m in models],
        "repeat": repeat,
        "callsMade": len(runs),
        "callsFailed": len(runs) - len(ok_runs),
        "summary": summarize(ok_runs, brand["name"]) if ok_runs else {},
        "runs": runs,
    }
    out = Path(args.out) if args.out else (
        Path(args.out_dir) / f"geo-{re.sub(r'[^a-z0-9]+', '-', norm(brand['name'])).strip('-')}-"
        f"{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    s = result["summary"]
    print(f"\nотчёт: {out}")
    if s:
        print(f"{'модель':<18} {'промптов':>8} {'упомянут':>9} {'доля':>7} {'ср. позиция':>12} {'омоним':>7}")
        for name, slot in sorted(s["models"].items()):
            print(f"{name:<18} {slot['prompts']:>8} {slot['mentioned']:>9} "
                  f"{slot['mentionRate']:>7.0%} {str(slot['avgFirstPosition'] or '—'):>12} "
                  f"{slot['ambiguous']:>7}")
        ambiguous = sum(slot.get("ambiguous", 0) for slot in s["models"].values())
        if ambiguous:
            print(f"\nвнимание: {ambiguous} упоминаний похожи на одноимённую чужую сущность — "
                  f"проверьте ответы вручную (поле ambiguousEntity)")
        unknown = sum(slot.get("claimsUnknown", 0) for slot in s["models"].values())
        if unknown:
            print(f"модель прямо говорит «данных нет / связь не подтверждена»: "
                  f"{unknown} ответов — это задача на публикации и упоминания, "
                  f"а не на тон ответов")
        print()
        for name, slot in sorted(s["models"].items()):
            if slot.get("topCitedDomains"):
                print(f"  {name}: опирается на {', '.join(slot['topCitedDomains'][:5])}")
        slugs: dict[str, int] = {}
        for slot in s["models"].items():
            for slug, n in slot[1].get("sourceSlugs", {}).items():
                slugs[slug] = slugs.get(slug, 0) + n
        if slugs:
            top = sorted(slugs.items(), key=lambda x: (-x[1], x[0]))[:10]
            print("названные модели источники (без ссылок): "
                  + ", ".join(f"{k}×{v}" for k, v in top))
        if s.get("topCitedDomains"):
            print("\nисточники, на которые опирались модели (частота): "
                  + ", ".join(s["topCitedDomains"][:10]))
    if result["callsFailed"]:
        print(f"\nнеудачных вызовов: {result['callsFailed']} — сводка неполная, "
              f"перезапустите с --only-models для упавших моделей")
    return 0


if __name__ == "__main__":
    sys.exit(main())
