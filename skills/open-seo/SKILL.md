---
name: open-seo
description: OpenSEO — open source SEO tool (Semrush/Ahrefs alternative). MCP server, Docker, pay-as-you-go via DataForSEO API. Keyword research, rank tracking, competitor insights, backlinks, site audits, AI visibility. Use when user asks about SEO optimization, site ranking, or competitor analysis.
---

# OpenSEO

**Repo:** https://github.com/every-app/open-seo
**Stars:** 3642, MIT, TypeScript
**Site:** https://openseo.so

## Overview

Open source alternative to Semrush and Ahrefs. Pay-as-you-go — bring your own
DataForSEO API key, pay only for what you use. No subscriptions.

Built-in MCP server — connect to Claude Code, Codex, Hermes, OpenClaw.
Pre-built agent skills included.

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
