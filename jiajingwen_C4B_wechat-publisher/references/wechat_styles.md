# WeChat Publisher — Style & Theme Reference

Inline CSS values used by the converter. WeChat accepts only inline styles,
so every element gets its own `style="..."`.

## Typography Baseline (mobile)

- Body text: **≥16px** (smaller is unreadable on phones)
- Line height: **1.75** is the sweet spot for Chinese text
- Color: avoid pure black; **#333** is softer
- Max width: articles render ~375px wide on most phones
- Images: always `max-width: 100%` to prevent overflow

## Built-in Themes

Select with `--theme <name>`. Each theme defines heading color, accent,
blockquote, table, code, link, and title styles. Defined in
`scripts/convert_to_wechat.py` under the `THEMES` dict.

| Theme | Accent | Vibe |
|-------|--------|------|
| `default` | `#0366d6` blue | neutral, safe |
| `accent` | `#1a73e8` blue | modern, tech |
| `warm` | `#e65100` orange | warm, lively |
| `minimal` | `#555` gray | clean, editorial |
| `forest` | `#2e7d32` green | calm, natural |

## How to Add Your Own Theme

Append a key to `THEMES` in `scripts/convert_to_wechat.py`. Copy an existing
entry and change the values. Required keys:

```
'accent'   : main color (title, links, TOC marker)
'h2' 'h3'  : heading styles
'p' 'li'   : body & list styles
'code_inline' 'code_block' : code styles
'blockquote' : quote box
'table' 'th' 'td' : table styles
'a'        : link style
'title'    : in-body title (from frontmatter)
'subtitle' : author·date line
```

## Callout Colors (independent of theme)

| Type | Icon | Label | Border |
|------|------|-------|--------|
| info | ℹ️ | 说明 | `#1a73e8` |
| tip | 💡 | 贴士 | `#1aad5a` |
| warning | ⚠️ | 注意 | `#ff9800` |
| knowledge | 📘 | 知识点 | `#7b4dff` |
| note | 📌 | 笔记 | `#999999` |

To recolor a callout type, edit `CALLOUT_TYPES` in the script.

## Customization Ideas

- **Brand color:** set `accent` + `h2` color to your brand hex.
- **Rounded cards:** add `border-radius` to blockquote/callout styles.
- **Quote style:** change `blockquote` border-left color + background tint.
