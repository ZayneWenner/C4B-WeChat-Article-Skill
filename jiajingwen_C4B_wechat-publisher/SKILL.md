---
name: wechat-publisher
description: |
  Convert Markdown or Word documents into WeChat Official Account (微信公众号)
  compatible HTML that can be copy-pasted directly into the WeChat editor.
  Applies inline CSS styling, enforces WeChat's HTML restrictions, and adds
  publishing-grade features: multiple themes, callout boxes, auto table of
  contents, article metadata (frontmatter), configurable footer, Chinese
  typography optimization, and local-image base64 embedding.
  Use whenever the user says "转公众号", "公众号排版", "微信公众号格式",
  "convert to WeChat", "generate WeChat HTML", "公众号文章", or provides a
  .md / .docx file and asks to format it for WeChat publishing. Also trigger
  when the user wants to publish an article to WeChat Official Account and
  needs copy-paste-ready, mobile-friendly HTML.
agent_created: true
---

# WeChat Publisher — Markdown/Word → 公众号 HTML（增强版）

## Purpose

Convert a Markdown (.md) or Word (.docx) document into copy-paste-ready HTML
for WeChat Official Account publishing. Treat it as a "print driver" for
WeChat: supply content, receive formatted HTML that survives WeChat's strict
editor rules — including inline CSS, forbidden-tag sanitization, and
publishing-grade layout features.

This is a customized version of the `c4b-wechat-publisher-starter` kit. It
keeps the starter's reliable core (read → sanitize → style → output) and adds
seven capabilities on top. See `拿来说明` / `README` in the challenge
submission for the full "what was taken / changed / why" record.

## Quick Start

```bash
python scripts/convert_to_wechat.py input.md output.html
python scripts/convert_to_wechat.py input.md output.html --theme accent
python scripts/convert_to_wechat.py input.md output.html --embed-images
```

Then: open `output.html` in a browser → Ctrl+A → Ctrl+C → paste into the
WeChat editor (mp.weixin.qq.com).

## Supported Input Formats

| Format | Handling |
|--------|----------|
| Markdown (.md) | `markdown` library (tables, fenced code, footnotes) + frontmatter + callout syntax |
| Word (.docx) | `python-docx` — headings, paragraphs, bold/italic preserved |
| HTML (.html) | sanitized in place (strips forbidden tags/attributes) |

## Bundled Resources

- `scripts/convert_to_wechat.py` — the converter (all logic lives here)
- `references/wechat_restrictions.md` — the full list of WeChat HTML rules this tool enforces
- `references/wechat_styles.md` — theme palettes and how to add your own
- `examples/sample_article.md` + `examples/sample_output.html` — a worked example using every feature

## Core Workflow

### Step 1 — Read source

Detect format. For Markdown, parse YAML-style frontmatter (title / author /
date / abstract / theme / toc / footer) and extract `:::callout` blocks before
conversion. For Word, map Heading styles to `<h2>`/`<h3>`.

### Step 2 — Sanitize for WeChat

Enforce the rules automatically:

| Forbidden | Action |
|-----------|--------|
| `<h1>` | → `<h2>` |
| `<div>` | → `<p>` |
| `<script>` `<style>` `<iframe>` | removed |
| `class=` `id=` | removed |
| `<pre><code>` | → styled `<p>` (code block, `pre-wrap`) |
| `<blockquote>` | → styled `<p>` with left border |
| `<strong>`/`<em>` | → styled `<span>` |

### Step 3 — Apply theme + features

Apply the selected theme's inline CSS to every element, then assemble the
document in this order: **metadata header → auto TOC → body → footer**.

### Step 4 — Output

Wrap in a 600px preview shell (or `--no-shell` for bare body HTML). Output
UTF-8 HTML ready to paste.

## Feature Reference

### Themes (`--theme`)

Choose a palette with `--theme <name>`. Default `default`. Available:
`default`, `accent` (blue), `warm` (orange), `minimal` (grayscale),
`forest` (green). Each defines heading color, accent, blockquote, table,
code, link, and title styles. To add a theme, append a key to `THEMES` in
`scripts/convert_to_wechat.py`.

### Callout boxes (`:::type`)

Use fenced blocks in Markdown. Supported types and their look:

```
:::tip
一句话经验或操作提示。
:::

:::warning
需要避开的坑。
:::

:::knowledge
补充的知识点。
:::

:::info
普通说明。
:::

:::note
笔记 / 小结。
:::
```

Each renders as a single styled `<p>` (left border + tinted background +
icon label), which is WeChat-safe (no `<div>`).

### Auto table of contents (`--toc` / `--no-toc`)

When enabled, headings (`<h2>`) are collected and rendered as a "本文目录"
list with Chinese ordinals (一、二、三…). Disable with `--no-toc`. Note:
clickable in-page anchors are unreliable in WeChat (it strips `id`), so the
TOC is a structural preview, not jump-links — by design.

### Article metadata (frontmatter)

Top of the `.md` file:

```yaml
---
title: 文章标题
author: 你的名字
date: 2026-10-07
abstract: 一句话摘要，会渲染成带边框的摘要框。
theme: accent
toc: true
footer: 自定义页脚文字（留空字符串可去掉页脚）
---
```

These drive the auto-generated header (title + author·date + 摘要框) and
footer. CLI flags `--title/--author/--date/--footer` override frontmatter.

### Chinese typography (`--typo` / `--no-typo`)

By default, a half-width space is inserted between CJK characters and adjacent
Latin letters / digits (e.g. `完成C4B` → `完成 C4B`). Skipped inside code
blocks and inline code to avoid breaking commands. Disable with `--no-typo`.

### Image embedding (`--embed-images`)

Local images referenced in Markdown are read and inlined as PNG/JPG/GIF
base64 data URIs, producing a self-contained HTML. External (`http(s):`) and
already-base64 images are left untouched (external ones still need upload to
WeChat's media library on paste). SVG is intentionally not embedded — WeChat
drops it on save.

## Dependencies

```bash
pip install markdown beautifulsoup4 python-docx lxml
```

The script auto-installs these on first run if missing.

## Edge Cases

| Situation | Handling |
|-----------|----------|
| Empty file | reports error, no empty HTML |
| Non-UTF-8 | opens UTF-8 first; extend if needed |
| Missing deps | auto-install (falls back to `--break-system-packages`) |
| Unknown `--theme` | warns and falls back to `default` |
| External image URL | kept as-is, warns to upload to WeChat CDN |
| Long article | works; WeChat caps ~20,000 Chinese chars |
| Wide table | no horizontal scroll; split wide tables manually |
