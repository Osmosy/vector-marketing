# Дека «Vector Marketing» — тема 01-obsidian-neon (неон-синий на тёмно-синем)
# 14 слайдов: титул, что это, проблема, решение, три слоя, агенты, PM-скиллы,
# гипотезный цикл, контур качества, инструменты РФ, деливераблы, roadmap, финал.
import os
OUT_FMT = os.path.expanduser('~/projects/vector-legal-decks15/vector-marketing-{theme}.pptx')

DATA = dict(
    kicker='AI-МАРКЕТИНГОВОЕ АГЕНТСТВО · OSMOSY VECTOR',
    title='Vector Marketing',
    subtitle='19 профильных агентов под управлением Osmosy (CMO-оркестратор) — '
             'стратегия, привлечение, упаковка, удержание, операции',
    chips=[('19', 'агентов'), ('170+', 'навыков'), ('29', 'PM-методик')],
    github='github.com/Osmosy/vector-marketing',
    footer_tag='Osmosy · Hermes Agent · 2026',
    intro_lead='Маркетинговое агентство на базе Hermes Agent: клиент ставит бизнес-задачу, '
               'CMO-оркестратор декомпозирует её и делегирует профильным агентам.',
    intro_cards=[
        ('19 агентов', ['Стратегия: market-research,', 'analytics. Привлечение: performance,', 'Директ, SEO, VK, Авито, МП', 'Упаковка: лендинги, контент, SMM']),
        ('Company Brain', ['7 файлов общего контекста:', 'голос бренда, anti-slop,', 'ICP, офферы, барьеры,', 'данные о компании']),
        ('Human approval', ['Публикация, бюджет, outreach —', 'только после подтверждения', 'человеком. Агент не тратит', 'деньги сам']),
    ],

    # 02 · Проблема
    prob_cards=[
        ('Дорого и медленно', ['Агентство full-service:', 'ретейнер + медиабаинг +', 'дизайн. Месяц на запуск', 'кампании, большой бюджет']),
        ('Фриланс-зоопарк', ['SEO-шник, таргетолог и', 'дизайнер не разговаривают.', 'Никто не видит воронку', 'целиком — каждый свой кусок']),
        ('Данные не работают', ['Wordstat, Метрика, MPSTATS', 'не собираются в единую', 'картину. Решения — по интуиции', 'и «как в прошлый раз»']),
    ],
    prob_panel='Что должно быть по-другому',
    prob_lines=[
        'Одна система видит всю воронку: от спроса в Wordstat до ROMI в отчёте — без потерь на стыках между исполнителями.',
        '!Скорость: исследования и медиапланы собираются за часы, а не недели; дешёвые smoke-тесты идут до больших бюджетов.',
        'Каждое внешнее действие — под контролем человека: агент предлагает, человек утверждает.',
    ],

    # 03 · Решение
    sol_cards=[
        ('CMO-оркестратор', ['Osmosy принимает задачу,', 'декомпозирует, делегирует', 'параллельно, проверяет', 'противоречия между агентами']),
        ('Профильные агенты', ['19 агентов, у каждого:', 'свой профиль Hermes,', 'skills, MCP-инструменты,', 'правила и guardrails']),
        ('Полный цикл', ['Стратегия → привлечение →', 'упаковка → удержание →', 'операции. От исследования', 'рынка до отчёта по ROMI']),
    ],
    sol_panel='Главный принцип',
    sol_lines=[
        '!Контекст ценнее ботов: Company Brain — общая база знаний, без неё агенты дают генерик. Заполняется под бизнес клиента.',
        'Агенты не работают вслепую: handoff-протокол передаёт выводы между агентами, противоречия разрешает оркестратор.',
        'Контур качества: draft → check → retry. Anti-slop правила на каждый драфт, human sign-off на внешние действия.',
    ],

    # 04 · Три слоя
    layers_items=[
        ('Context — что модель видит', 'company-brain/: brand-voice, anti-slop-rules, ICP, офферы, данные о бизнесе. Без контекста — генерик-выпуск; с контекстом — агент говорит голосом бренда клиента'),
        ('Harness — что позволяет действовать', 'agents/*.md (19 ролей) + Hermes profile + 170+ skills + MCP-инструменты: Яндекс Метрика/Директ API, MPSTATS, ДaData, Wordstat, карты'),
        ('Loop — как обеспечивается качество', 'draft → check → retry: anti-slop чеклист, взаимная проверка агентов, handoff-протокол, cron-ритм. Red-team стратегии обязателен перед выдачей клиенту'),
    ],

    # 05 · Агенты
    ag_items=[
        ('СТРАТЕГИЯ', 'market-research (рынок, спрос, ICP, CJM, конкуренты, интервью) · analytics (метрики, воронки, A/B, NSM, дашборды)'),
        ('ПРИВЛЕЧЕНИЕ', 'performance (медиапланы, pre-mortem, GTM) · yandex-direct · seo (GEO/AEO) · vk-ads · avito · marketplaces (Ozon/WB)'),
        ('УПАКОВКА', 'landing-cro (лендинги, CRO, 152-ФЗ) · content (контент-планы, нейминг) · smm-telegram · creative · presentation'),
        ('УДЕРЖАНИЕ + ОПЕРАЦИИ', 'crm-retention (RFM + когорты) · reputation (отзывы, карты) · sales · support · ops (NDA, стейкхолдеры)'),
    ],

    # 06 · PM-скиллы
    skills_cards=[
        ('Исследования', ['TAM/SAM/SOM: Wordstat,', 'MPSTATS, ДaData, Росстат', 'ICP и CJM как деливераблы', 'Конкуренты: библиотека', 'Директа, отзывы, МП']),
        ('Гипотезы', ['Карта допущений: 8 категорий', 'Матрица Impact × Risk', 'Smoke-тесты: TG-пост,', 'лендинг+Директ, карточка', 'WB/Ozon без рекламы']),
        ('Метрики', ['North Star + дерево метрик', 'A/B: мощность, SRM,', 'guardrails, ship/extend/stop', 'Когорты и RFM: retention', 'кривые из CSV']),
    ],
    skills_panel='29 методик PM Skills Marketplace + адаптация РФ',
    skills_lines=[
        'Источник: github.com/phuryn/pm-skills (MIT, The Product Compass). Взято 29 из 68 — остальные дубли или SDLC-домен.',
        '!Каждый скилл адаптирован под РФ: источники данных (Wordstat вместо Google Trends), юнит-экономика маркетплейсов, 152-ФЗ в политиках, Роспатент в нейминге, право РФ в NDA.',
    ],

    # 07 · Гипотезный цикл
    hypo_rows=[
        ('1 · Допущения', 'identify-assumptions: рисковые допущения продукта/кампании по 8 категориям', 'market-research'),
        ('2 · Приоритизация', 'prioritize-assumptions: матрица Impact × Risk — что тестировать первым', 'market-research'),
        ('3 · Smoke-тест', 'Wordstat → TG-пост в нише → лендинг + Директ → карточка МП без рекламы (3-5 дней)', 'market-research → performance'),
        ('4 · Разбор', 'ab-test-analysis: мощность, значимость, guardrails → ship / extend / stop / revert', 'analytics'),
        ('5 · Масштаб', 'Медиаплан + pre-mortem рисков перед стартом; growth-loops снижают зависимость от paid', 'performance'),
    ],
    hypo_panel='Правило бюджета',
    hypo_lines=[
        '!Никакого полного медиаплана до smoke-сигнала: сначала дешёвый тест на сотнях рублей, потом решение о тысячах.',
    ],

    # 07b · Контур качества
    qual_items=[
        ('Loop: draft → check → retry', 'Anti-slop чеклист на каждый драфт; агент не публикует сам — проверяет и переписывает'),
        ('Red-team стратегий', 'orchestrator обязан прогнать стратегию через strategy-red-team: стилман → атака несущих допущений → failure modes'),
        ('Pre-mortem кампании', 'performance: Tigers (реальные риски) / Paper Tigers (раздутые) / Elephants (неозвученные) до старта медиаплана'),
        ('Human approval', 'Все внешние действия: публикация, рассылки, бюджет, доступы — только через подтверждение человеком'),
    ],

    # 08 · Инструменты РФ
    tools_cards=[
        ('Спрос и рынок', ['Яндекс Wordstat: объём,', 'сезонность, минус-слова', 'MPSTATS/Moneyplace: выручка', 'категорий WB/Ozon', 'ДaData: компании, ОКВЭД']),
        ('Реклама и аналитика', ['Яндекс Метрика + Директ API', 'VK Ads пиксель и аудитории', 'A/B: статистический разбор', 'Когорты: retention-кривые']),
        ('Право и комплаенс', ['152-ФЗ: согласие, локализация,', 'реестр РКН, утечки 24/72ч', 'NDA: режим КТ по ФЗ-98', 'Роспатент/МКТУ в нейминге']),
    ],
    tools_panel='Российские источники вместо западных дефолтов',
    tools_lines=[
        'Wordstat вместо Google Trends, MPSTATS вместо SEMrush, ДaData вместо Crunchbase, Яндекс Карты вместо Google Maps.',
        '!Каждый методический скилл проверен на применимость в РФ: западные практики (Van Westendorp, ABM, PLG) заменены или ограничены там, где не работают.',
    ],

    # 09 · Деливераблы
    deliv_rows=[
        ('Стратегия', 'Объём рынка в деньгах, ICP, CJM, позиционирование, офферы, гипотезы — red-team пройден', 'от часов до дней'),
        ('GTM-план', 'Канальная матрица РФ, метрики запуска (ДРР, CPL), pre-mortem рисков, бюджет по этапам', 'дни'),
        ('Проверка гипотез', 'Smoke-тест: лендинг + Директ / TG-интеграция / карточка МП — с вердиктом go/no-go', '3-5 дней'),
        ('Лендинг + упаковка', 'HTML-лендинг с 152-ФЗ, A/B-гипотезы, нейминг с проверкой Роспатента, контент-план', 'дни'),
        ('Retention-контур', 'RFM-сегментация + когортные кривые, цепочки welcome/reactivation, чёрный ящик метрик', 'непрерывно'),
    ],

    # 10 · Roadmap
    roadmap_items=[
        ('Сейчас', ['29 PM-скиллов в 4 группах, 19 агентов, 170+ навыков', 'Живая архитектурная диаграмма (Archify) + визуальная верификация']),
        ('Следующий шаг', ['Прогон агентства на реальном клиенте: полный цикл от брифа до отчёта ROMI', 'Company Brain под конкретный бизнес — контекст решает качество']),
        ('Экосистема Vector', ['Связка с vector-prediction (прогноз спроса) и vector-work (роли)', 'Единый слой Company Brain для всех продуктов Osmosy']),
    ],
    fact_big='19 агентов · 29 методик', fact_small='полный цикл маркетинга: от исследования рынка до отчёта по ROMI — с human approval на каждом внешнем действии',
    final_msg='Контекст — валюта. Агенты — исполнители. Человек — решение.',
    final_sub='github.com/Osmosy/vector-marketing',
)

from engine import kicker, title_block, footer, bg_fill, card, chip, wide_panel, \
    add_text, add_rect, add_bullets
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

ASSETS = '/tmp/vl_assets'

def _rgb(h): return RGBColor.from_string(h)


def _table(slide, th, x, y, col_ws, head, rows, row_h=0.46, head_h=0.42,
           hl_col=None, size=11):
    xs = [x]
    for w in col_ws[:-1]:
        xs.append(xs[-1] + w)
    total_w = sum(col_ws)
    add_rect(slide, x, y, total_w, head_h, fill=th['surface'], line=th['card_line'],
             line_w=1.0, radius=th['radius'])
    for j, htxt in enumerate(head):
        add_text(slide, xs[j] + 0.14, y + 0.10, col_ws[j] - 0.2, 0.3, htxt, size=size,
                 bold=True, font=th['f_mono'], color=th['kicker_accent'])
    yy = y + head_h + 0.06
    for i, row in enumerate(rows):
        add_rect(slide, x, yy, total_w, row_h, fill=th['card'], line=th['card_line'],
                 line_w=0.75, radius=th['radius'])
        for j, cell in enumerate(row):
            emph = (j == hl_col)
            add_text(slide, xs[j] + 0.14, yy + 0.11, col_ws[j] - 0.2, 0.3, str(cell),
                     size=size, bold=emph, font=th['f_body'] if j == 0 else th['f_mono'],
                     color=th['accent'] if emph else th['text'])
        yy += row_h + 0.06
    return yy


def sl_title(slide, th, D):
    if th.get('art'):
        from engine import full_art, half_art
        if th['art'][0] == 'full':
            full_art(slide, th, th['art'][1], overlay_pct=26)
        else:
            half_art(slide, th, th['art'][1])
    ta = th['title_align']
    if ta == 'center' and not (th.get('art') and th['art'][0] == 'half'):
        add_rect(slide, (13.333-5.6)/2, 1.52, 5.6, 0.42, fill=th['surface'],
                 line=th['card_line'], radius=0.21, alpha=70)
        add_text(slide, (13.333-5.6)/2, 1.60, 5.6, 0.3, D['kicker'], size=10,
                 bold=True, font=th['f_mono'], color=th['text'],
                 align=PP_ALIGN.CENTER, spacing=140)
        add_text(slide, 1.67, 2.02, 10.0, 1.2, D['title'], size=60, bold=True,
                 font=th['f_title'], color=th['accent'], align=PP_ALIGN.CENTER)
        add_text(slide, 2.17, 3.28, 9.0, 0.7, D['subtitle'], size=15.5,
                 font=th['f_body'], color=th['text'], align=PP_ALIGN.CENTER)
        for i, (big, small) in enumerate(D['chips']):
            chip(slide, th, 3.47 + i*2.25, 4.12, 1.95, big, small)
        add_rect(slide, 4.87, 5.62, 3.6, 0.52, fill=th['accent'], radius=0.26)
        add_text(slide, 4.87, 5.74, 3.6, 0.3, D['github'], size=11.5, bold=True,
                 font=th['f_mono'], color='FFFFFF', align=PP_ALIGN.CENTER)
        add_text(slide, 4.17, 6.90, 5.0, 0.26, D['footer_tag'], size=9.5,
                 font=th['f_mono'], color=th['muted'], align=PP_ALIGN.CENTER)
    else:
        add_rect(slide, 0.62, 1.30, 0.05, 2.2, fill=th['accent'])
        add_text(slide, 0.92, 1.30, 6.5, 0.3, D['kicker'], size=10.5, bold=True,
                 font=th['f_mono'], color=th['kicker_accent'], spacing=160)
        add_text(slide, 0.88, 1.66, 6.2, 1.15, D['title'], size=54, bold=True,
                 font=th['f_title'], color=th['accent'])
        add_text(slide, 0.92, 2.86, 5.9, 0.7, D['subtitle'], size=15,
                 font=th['f_body'], color=th['text'])
        for i, (big, small) in enumerate(D['chips']):
            x = 0.92 + i*1.95
            add_text(slide, x, 3.85, 1.8, 0.5, big, size=26, bold=True,
                     font=th['f_title'], color=th['accent'])
            add_text(slide, x, 4.36, 1.8, 0.3, small, size=9.5, font=th['f_mono'],
                     color=th['muted'], spacing=100)
        add_text(slide, 0.92, 5.15, 6.0, 0.3, D['github'], size=12.5, bold=True,
                 font=th['f_mono'], color=th['accent'])
        add_text(slide, 0.92, 6.0, 6.0, 0.26, D['footer_tag'], size=9.5,
                 font=th['f_mono'], color=th['muted'])
    slide.shapes.add_picture(f'{ASSETS}/vector_ray_t.png',
                             Inches(12.20), Inches(0.30), width=Inches(0.9))


def sl_intro(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '01 · Введение')
    title_block(slide, th, 'Агентство без офиса: 19 агентов, один CMO')
    add_text(slide, 0.62, 1.75, 12.1, 0.5, D['intro_lead'], size=13,
             font=th['f_body'], color=th['muted'])
    cw, gap, m = 3.95, 0.25, 0.62
    for i, (head, lines) in enumerate(D['intro_cards']):
        card(slide, th, m + i*(cw+gap), 2.55, cw, 3.4, head, lines)
    footer(slide, th, 2)


def sl_problem(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '02 · Зачем')
    title_block(slide, th, 'Как обычно устроен маркетинг')
    cw, gap, m = 3.95, 0.25, 0.62
    for i, (head, lines) in enumerate(D['prob_cards']):
        card(slide, th, m + i*(cw+gap), 2.15, cw, 3.1, head, lines)
    wide_panel(slide, th, 0.62, 5.55, 12.1, 1.85, D['prob_panel'], D['prob_lines'])
    footer(slide, th, 3)


def sl_solution(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '03 · Решение')
    title_block(slide, th, 'Оркестратор + профильные агенты')
    cw, gap, m = 3.95, 0.25, 0.62
    for i, (head, lines) in enumerate(D['sol_cards']):
        card(slide, th, m + i*(cw+gap), 2.15, cw, 3.1, head, lines)
    wide_panel(slide, th, 0.62, 5.55, 12.1, 1.85, D['sol_panel'], D['sol_lines'])
    footer(slide, th, 4)


def sl_layers(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '04 · Архитектура')
    title_block(slide, th, 'Три слоя: Context → Harness → Loop')
    y = 2.15
    hs = [1.5, 1.5, 1.5]
    for i, (head, line) in enumerate(D['layers_items']):
        wide_panel(slide, th, 0.62, y, 12.1, hs[i], head, [line])
        y += hs[i] + 0.18
    footer(slide, th, 5)


def sl_agents(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '05 · Состав')
    title_block(slide, th, '19 агентов — 5 блоков')
    y = 2.05
    hs = [1.0, 1.35, 1.35, 1.15]
    for i, (head, line) in enumerate(D['ag_items']):
        wide_panel(slide, th, 0.62, y, 12.1, hs[i], head, [line])
        y += hs[i] + 0.14
    footer(slide, th, 5)


def sl_skills(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '06 · Методики')
    title_block(slide, th, '29 PM-скиллов: метод, а не промпт')
    cw, gap, m = 3.95, 0.25, 0.62
    for i, (head, lines) in enumerate(D['skills_cards']):
        card(slide, th, m + i*(cw+gap), 2.15, cw, 3.1, head, lines)
    wide_panel(slide, th, 0.62, 5.55, 12.1, 1.85, D['skills_panel'], D['skills_lines'])
    footer(slide, th, 6)


def sl_hypo(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '07 · Гипотезный цикл')
    title_block(slide, th, 'Проверка спроса до бюджета')
    _table(slide, th, 0.62, 2.05, [2.6, 6.6, 2.9],
           ('Шаг', 'Что происходит', 'Кто'), D['hypo_rows'], row_h=0.62, hl_col=0)
    wide_panel(slide, th, 0.62, 6.05, 12.1, 1.15, D['hypo_panel'], D['hypo_lines'])
    footer(slide, th, 7)


def sl_quality(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '08 · Контур качества')
    title_block(slide, th, 'Draft → check → retry')
    y = 2.05
    hs = [1.0, 1.35, 1.35, 0.95]
    for i, (head, line) in enumerate(D['qual_items']):
        wide_panel(slide, th, 0.62, y, 12.1, hs[i], head, [line])
        y += hs[i] + 0.14
    footer(slide, th, 8)


def sl_tools(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '09 · Инструменты РФ')
    title_block(slide, th, 'Российские источники, не западные шаблоны')
    cw, gap, m = 3.95, 0.25, 0.62
    for i, (head, lines) in enumerate(D['tools_cards']):
        card(slide, th, m + i*(cw+gap), 2.15, cw, 3.1, head, lines)
    wide_panel(slide, th, 0.62, 5.55, 12.1, 1.85, D['tools_panel'], D['tools_lines'])
    footer(slide, th, 9)


def sl_deliv(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '10 · Деливераблы')
    title_block(slide, th, 'Что получает клиент')
    _table(slide, th, 0.62, 2.05, [2.9, 6.3, 2.9],
           ('Продукт', 'Состав', 'Срок'), D['deliv_rows'], row_h=0.72, hl_col=0)
    footer(slide, th, 9)


def sl_roadmap(slide, th, D):
    bg_fill(slide, th)
    kicker(slide, th, '11 · Развитие')
    title_block(slide, th, 'Roadmap')
    ys = [1.95, 3.15, 4.75]
    hts = [1.0, 1.4, 1.1]
    for (h, lines), y, hh in zip(D['roadmap_items'], ys, hts):
        wide_panel(slide, th, 0.62, y, 12.1, hh, h, lines)
    footer(slide, th, 12)


def sl_final(slide, th, D):
    bg_fill(slide, th)
    add_text(slide, 1.67, 2.0, 10.0, 1.0, D['fact_big'], size=48, bold=True,
             font=th['f_title'], color=th['accent'], align=PP_ALIGN.CENTER)
    add_text(slide, 1.17, 3.15, 11.0, 0.5, D['fact_small'], size=14,
             font=th['f_body'], color=th['text'], align=PP_ALIGN.CENTER)
    add_text(slide, 2.67, 4.35, 8.0, 0.6, D['final_msg'], size=22, bold=True,
             font=th['f_title'], color=th['text'], align=PP_ALIGN.CENTER)
    add_rect(slide, 5.17, 5.25, 3.0, 0.035, fill=th['accent'])
    add_text(slide, 2.67, 5.65, 8.0, 0.3, D['final_sub'], size=12.5,
             font=th['f_mono'], color=th['accent'], align=PP_ALIGN.CENTER)
    add_text(slide, 2.17, 6.85, 9.0, 0.24,
             'Context → Harness → Loop · Human approval на внешние действия · адаптация всех методик под рынок РФ',
             size=9.5, font=th['f_body'], color=th['muted'], align=PP_ALIGN.CENTER)
    slide.shapes.add_picture(f'{ASSETS}/vector_ray_t.png',
                             Inches(12.20), Inches(0.30), width=Inches(0.9))


SLIDES = [sl_title, sl_intro, sl_problem, sl_solution, sl_layers, sl_agents,
          sl_skills, sl_hypo, sl_quality, sl_tools, sl_deliv, sl_roadmap, sl_final]