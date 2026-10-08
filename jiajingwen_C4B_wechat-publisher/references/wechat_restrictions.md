# WeChat Official Account HTML Restrictions

Complete reference of what WeChat's editor allows and forbids. The converter
(`scripts/convert_to_wechat.py`) enforces these automatically — you normally
never need to think about them, but here they are for reference and debugging.

## Allowed HTML Tags

```
p, h2, h3, ul, ol, li, span, img, a, table, tr, th, td, br
```

## Forbidden Tags (auto-handled)

| Tag | Why | Converter does |
|-----|-----|----------------|
| `<h1>` | reserved for article title | → `<h2>` |
| `<div>` | unreliable rendering | → `<p>` |
| `<script>` | security, always stripped | removed |
| `<style>` | CSS must be inline | removed |
| `<iframe>` | external embeds forbidden | removed |
| `<video>` / `<audio>` | must use WeChat's own embed | removed / convert to link |

## Forbidden Attributes

| Attribute | Why | Converter does |
|-----------|-----|----------------|
| `class` | no CSS classes | removed |
| `id` | no element IDs | removed |
| `onclick` etc. | no JS events | removed |

## CSS Rules

- **Inline only.** Every element carries its own `style="..."`.
- **Allowed properties:** `color, background-color, font-size, font-weight,
  font-style, line-height, text-align, margin, padding, border, border-left,
  border-top, border-radius, border-collapse, text-decoration, white-space,
  word-wrap, max-width, width, vertical-align`.
- **Forbidden:** `position, float, flex, grid, animation, transition,
  @media, @font-face`.

## Images

| Method | Works? | Notes |
|--------|--------|-------|
| `<img src="https://...">` | ⚠️ | may be re-hosted; better upload to media library |
| `<img src="data:image/png;base64,...">` | ✅ | WeChat re-uploads on paste |
| SVG data URI / inline `<svg>` | ❌ | disappears on save |

Best practice: PNG/JPG/GIF as base64 for self-contained output; photos via
WeChat media library. The `--embed-images` flag handles the base64 step.

## Article Limits

| Limit | Value |
|-------|-------|
| Max length | ~20,000 Chinese characters |
| Max images | 100 / article |
| Max image size | 10 MB (GIF 2 MB) |
| Formats | PNG, JPG, GIF |

## Common Pitfalls

1. Lost formatting after save → forbidden tag or CSS used
2. Images disappearing → SVG or broken external URL
3. Spacing off → WeChat collapses margins differently than browsers
4. Code broken → must be `<p>` + inline style, not `<pre><code>`
5. Wide tables overflow → no horizontal scroll; split them
