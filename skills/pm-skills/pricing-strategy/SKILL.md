---
name: pricing-strategy
description: "Analyze and design pricing strategies including pricing models, competitive pricing analysis, willingness-to-pay estimation, and price elasticity. Use when setting prices, evaluating pricing models, preparing for a pricing change, or comparing freemium vs paid approaches."
---

## Pricing Strategy

Design a pricing strategy grounded in value delivery, competitive positioning, and willingness to pay.

### Context

You are developing a pricing strategy for **$ARGUMENTS**.

If the user provides files (competitor pricing, survey data, financial models, or usage data), read them first. Use web search to research competitor pricing if needed.

### Instructions

1. **Understand the value delivered**:
   - What is the core value proposition?
   - What is the customer's alternative (and its cost)?
   - What quantifiable outcomes does the product deliver? (time saved, revenue gained, cost reduced)
   - What is the customer's willingness to pay based on that value?

2. **Evaluate pricing models** — recommend the best fit:

   | Model | Best For | Example |
   |---|---|---|
   | **Flat-rate** | Simple products, predictable costs | Basecamp ($99/mo flat) |
   | **Per-seat** | Collaboration tools, team products | Slack, Figma |
   | **Usage-based** | Infrastructure, API products | AWS, Twilio |
   | **Tiered** | Products with distinct user segments | Most SaaS (Free/Pro/Enterprise) |
   | **Freemium** | Products with viral/network effects | Spotify, Notion |
   | **Freemium + usage** | Platform products | Vercel, OpenAI API |
   | **Value-based** | High-impact enterprise tools | Salesforce, Palantir |

3. **Analyze competitive pricing**:
   - Map competitor pricing tiers and what's included
   - Identify where your product sits (premium, mid-market, budget)
   - Find pricing gaps or opportunities
   - Note any industry pricing conventions

4. **Design the pricing structure**:
   - **Tiers**: Define 2-4 tiers with clear differentiation
   - **Feature gating**: Which features go in which tier? (Use value metrics, not arbitrary limits)
   - **Value metric**: What unit do you charge on? (users, events, storage, API calls)
   - **Anchor pricing**: Set the most popular tier to feel like the obvious choice
   - **Annual discount**: Typically 15-20% off monthly pricing

5. **Estimate price sensitivity**:
   - Van Westendorp Price Sensitivity Meter (if survey data available):
     - Too cheap → quality concerns
     - Cheap → good value
     - Expensive → starting to hesitate
     - Too expensive → won't buy
   - Alternatively, estimate based on competitor pricing and value delivered

6. **Plan pricing experiments**:
   - A/B test pricing pages (different price points, tier names, feature bundles)
   - Founder-led sales conversations to test willingness to pay
   - Landing page tests with different price anchors
   - Cohort analysis of conversion rates by price point

7. **Output a pricing recommendation**:
   ```
   Recommended Model: [Model type]
   Value Metric: [What you charge on]

   | Tier | Price | Target Segment | Key Features | Positioning |
   |---|---|---|---|---|

   Key Assumptions:
   - [Assumption] → [How to test]

   Risks:
   - [Risk] → [Mitigation]
   ```

Think step by step. Save as markdown. Flag any assumptions that need validation before launch.

---

### Источники и особенности для рынка РФ (адаптация Vector Marketing)

- **Конкурентные цены:** MPSTATS/Moneyplace — динамика цен категорий WB/Ozon (история изменения цены конкурента, размер скидок), Авито — частный сегмент
- **Психология цен WB/Ozon:** до-rounding под «психологические пороги» маркетплейсов, учёт комиссии категории и логистики в минимальной цене, спирали демпинга (карточка конкурента может уйти в убыток ради позиции в выдаче)
- **Юнит-экономика:** при расчёте минимальной цены на маркетплейсах вычитать комиссию категории + логистику + эквайринг + рекламный расход (ДРР) — маржа «на карточке» обманчива
- **Оффлайн/услуги:** ценовые якоря через Яндекс.Директ (библиотека объявлений — видны офферы и цены конкурентов)
- **Налоговый фактор:** УСН/патент/НДС — ставка влияет на финальную цену и позиционирование против конкурентов на другой системе налогообложения
- **WTP-исследование:** вместо Van Westendorp (западная практика) — чаще дешёвый A/B цен на карточках или опрос в TG-чате ниши

---

### Attribution

Скилл заимствован из [PM Skills Marketplace](https://github.com/phuryn/pm-skills) (MIT, куратор Павел Хурын, The Product Compass). Адаптация для рынка РФ — Vector Marketing.

### Further Reading

- [Product Pricing Strategies 101](https://www.productcompass.pm/p/product-pricing-strategies-101)
- [The AI Product Pricing Masterclass: OpenAI Product Lead on Why SaaS Pricing Fails in AI (and How to Fix It)](https://www.productcompass.pm/p/ai-product-pricing) (video course)
