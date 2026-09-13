#!/usr/bin/env python3
"""Сборка деки Vector Marketing (тема 01-obsidian-neon).

Запуск:
    bash deck/build.sh                    # собрать + положить pptx и ассеты рядом
    bash deck/build.sh --no-render        # только собрать pptx

Почему скрипт лежит в репозитории, а не в /tmp: предыдущая сборка жила во временном
файле и потерялась, из-за чего арт и эмблему пришлось восстанавливать из готового pptx.
Теперь сборка воспроизводима из этой папки.

Ключевое для этой деки: арт и эмблема ОБЯЗАТЕЛЬНО переопределяются — тема 01 несёт
юридический арт (весы, «ЮРИДИЧЕСКИЙ AI-ДЕПАРТАМЕНТ»), на маркетинговой деке это брак.
"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
DECKS = Path.home() / "projects/vector-legal-decks15"
ASSETS = Path("/tmp/vl_assets")
THEME = "01-obsidian-neon"

# Арт и эмблема этой деки (лежат в deck/ и копируются в рабочий каталог ассетов).
ART = ("full", "hero-marketing.png")
EMBLEM = ("vector_ray_t.png", "38B2F8")   # луч Vector, не весы

# Брендинг подвала и число слайдов. Движок по умолчанию несёт юридический брендинг
# («Vector Legal · Hermes Agent · Osmosy», total=12) — на этой деке это брак: 13 слайдов
# и другое агентство. Длина строки подобрана под ширину подвала (3.1") — более длинный
# вариант переносится на вторую строку, проверено рендером.
FOOTER_BRAND = "Vector Marketing · Osmosy"
SLIDE_TOTAL = 13

# Файлы, которые восстановить неоткуда, если /tmp очистился.
REQUIRED = [ART[1], EMBLEM[0]]


def ensure_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED:
        src, dst = REPO / name, ASSETS / name
        if not src.is_file():
            sys.exit(f"нет {src} — арт деки должен лежать в deck/")
        shutil.copy2(src, dst)
        print(f"  asset ok: {name}")
    # Логотип Vector Ray обязателен на титуле и финале (правило скилла).
    logo = REPO / "vector_ray_t.png"
    if logo.is_file():
        shutil.copy2(logo, ASSETS / "vector_ray_t.png")


def load_engine():
    spec = importlib.util.spec_from_file_location("engine", DECKS / "engine.py")
    eng = importlib.util.module_from_spec(spec)
    sys.modules["engine"] = eng
    spec.loader.exec_module(eng)
    return eng


def main() -> int:
    no_render = "--no-render" in sys.argv
    ensure_assets()
    eng = load_engine()

    deck_path = REPO / "deck-marketing.py"
    spec = importlib.util.spec_from_file_location("deck", deck_path)
    deck = importlib.util.module_from_spec(spec)
    sys.modules["deck"] = deck
    spec.loader.exec_module(deck)

    themes = [t for t in eng.THEMES if t["name"] == THEME]
    if not themes:
        sys.exit(f"тема {THEME} не найдена в engine.py")

    for th in themes:
        th = dict(th)                       # не мутируем каталог тем движка
        th["art"] = ART
        th["emblem"] = EMBLEM
        th["footer_brand"] = FOOTER_BRAND
        th["footer_total"] = SLIDE_TOTAL
        prs = eng.Presentation()
        prs.slide_width, prs.slide_height = eng.SW, eng.SH
        blank = prs.slide_layouts[6]
        for fn in deck.SLIDES:
            fn(prs.slides.add_slide(blank), th, deck.DATA)
        out = Path(deck.OUT_FMT.format(theme=th["name"]))
        prs.save(out)
        print(f"  built: {out}")

        # Кладём рядом с исходником, чтобы дека жила в репозитории.
        local = REPO / out.name
        shutil.copy2(out, local)
        print(f"  copy:  {local}")

    if not no_render:
        render = DECKS / "render" / Path(deck.OUT_FMT).stem
        print(f"  render: {render} (запусти render_all.sh для PNG)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
