---
name: open-seo
description: OpenSEO — open source SEO tool (Semrush/Ahrefs alternative). MCP server, Docker, pay-as-you-go via DataForSEO API. Keyword research, rank tracking, competitor insights, backlinks, site audits, AI visibility. Use when user asks about SEO optimization, site ranking, or competitor analysis.
---

# OpenSEO

**Repo:** https://github.com/every-app/open-seo
**License:** MIT, TypeScript · **Stars:** 4 000+ на момент подключения (авг 2026)
**Site:** https://openseo.so

> Звёзды и релизы не фиксируем в тексте: они меняются каждую неделю. Сверяйте актуальное
> через `gh repo view every-app/open-seo` или MCP-инструмент, а не из этого файла.

## Overview

Open source alternative to Semrush and Ahrefs. Pay-as-you-go — bring your own
DataForSEO API key, pay only for what you use. No subscriptions.

Built-in MCP server — connect to Claude Code, Codex, Hermes, OpenClaw.
Pre-built agent skills included.

## Готовые агентские скиллы апстрима

Репозиторий несёт собственный набор скиллов в `.agents/skills/` — их можно ставить себе
по URL, не вендоря в этот репозиторий:

```bash
hermes skills install \
  "https://raw.githubusercontent.com/every-app/open-seo/HEAD/.agents/skills/<имя>/SKILL.md" \
  --name <имя> --yes
```

Полезные для нашего `seo`-агента: `keyword-research`, `keyword-clustering`, `seo-audit`,
`technical-seo`, `local-seo`, `competitive-landscape`, `link-prospecting`, `content-brief`,
`deslop` (чистка AI-паттернов в тексте — пересекается с `company-brain/anti-slop-rules.md`).
Остальные в наборе — внутренние для разработки самого OpenSEO (release-notes, greptile,
merge-ready) и агентству не нужны.

## Features

- Keyword research
- Rank tracking
- Competitor Insights
- Backlinks
- Site Audits
- AI Visibility (tracking in AI-powered search results)

## Deployment

Docker (recommended):
```bash
docker compose up -d
```

Requires DataForSEO API key (free tier available).

## MCP Integration

OpenSEO exposes MCP tools for agent-driven SEO:
- keyword research
- rank tracking
- competitor analysis
- backlink analysis
- site audit

Add to Hermes via MCP config (SSE or stdio, depends on deployment).

## For vector-marketing

Use OpenSEO for:
- SEO audit of vector ecosystem sites
- Competitor keyword analysis
- AI visibility tracking (how Vector appears in AI search)
- Backlink monitoring
