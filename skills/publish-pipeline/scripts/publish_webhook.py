#!/usr/bin/env python3
"""Отправка одобренного payload в webhook — или показ запроса без отправки.

Границы зашиты в код: без --confirmed скрипт не отправляет ничего и возвращает код 3.
Ключи берутся только из окружения (MARKETING_WEBHOOK_URL, MARKETING_WEBHOOK_TOKEN) и не
попадают ни в вывод, ни в payload.

Коды выхода:
  0 — отправлено (или dry-run выполнен)
  1 — ошибка сети или ответа
  2 — плохой вход (нет JSON, нет адреса)
  3 — отказ запускать (нет подтверждения человека)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Отправить payload в webhook после подтверждения.")
    parser.add_argument("--url", help="адрес webhook; по умолчанию MARKETING_WEBHOOK_URL")
    parser.add_argument("--payload-file", help="путь к JSON; по умолчанию читается stdin")
    parser.add_argument("--header", action="append", default=[], metavar="NAME: VALUE",
                        help="дополнительный заголовок, можно повторять")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--dry-run", action="store_true", help="показать запрос, не отправляя")
    parser.add_argument("--confirmed", action="store_true",
                        help="отправлять; ставится только после явного «да» на показанный payload")
    return parser.parse_args()


def load_payload(path: str | None) -> dict:
    try:
        raw = open(path, "r", encoding="utf-8").read() if path else sys.stdin.read()
    except OSError as exc:
        print(f"не прочитал payload: {exc}", file=sys.stderr)
        sys.exit(2)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"payload не JSON: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(payload, dict):
        print("payload должен быть объектом JSON", file=sys.stderr)
        sys.exit(2)
    return payload


def main() -> int:
    args = parse_args()
    url = args.url or os.environ.get("MARKETING_WEBHOOK_URL", "")
    payload = load_payload(args.payload_file)

    missing = [key for key in ("id", "platform", "title", "body", "source_ref", "approved_by")
               if not str(payload.get(key) or "").strip()]
    if missing:
        print(f"в payload нет обязательных полей: {', '.join(missing)}", file=sys.stderr)
        return 2
    if not url:
        print("нет адреса: --url или MARKETING_WEBHOOK_URL", file=sys.stderr)
        return 2

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    token = os.environ.get("MARKETING_WEBHOOK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for raw in args.header:
        name, _, value = raw.partition(":")
        if name.strip():
            headers[name.strip()] = value.strip()

    if args.dry_run:
        print(f"POST {url}")
        for name, value in sorted(headers.items()):
            shown = "Bearer <redacted>" if name.lower() == "authorization" else value
            print(f"{name}: {shown}")
        print()
        print(body.decode("utf-8"))
        return 0

    if not args.confirmed:
        print("отказ: нет подтверждения человека. Сначала покажите этот запрос и получите «да»,\n"
              "затем запустите с --confirmed (проверить текст можно через --dry-run).",
              file=sys.stderr)
        return 3

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            answer = response.read(2000).decode("utf-8", "replace")
            print(f"отправлено: HTTP {response.status}")
            if answer.strip():
                print(answer.strip())
            return 0
    except urllib.error.HTTPError as exc:
        print(f"отказ сервиса: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"сеть недоступна: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
