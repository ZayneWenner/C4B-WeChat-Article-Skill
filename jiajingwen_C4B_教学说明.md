# 教学说明：jiajingwen_C4B_wechat-publisher 技能

本文档说明如何安装、使用这个「公众号文章生成技能」，以及怎么把你自己的文章变成可发布的公众号 HTML。

## 一、安装

### 1. 安装 Python 依赖

```bash
pip install markdown beautifulsoup4 python-docx lxml
```

> 技能脚本首次运行会自动检测并安装缺失依赖（必要时回退到 `--break-system-packages`）。

### 2. 放置技能目录

把 `jiajingwen_C4B_wechat-publisher/` 整个目录放到任意位置即可（例如你的项目目录）。
也可以放进 WorkBuddy 的用户技能目录 `~/.workbuddy/skills/` 让它全局可用——但这不是必须的，直接跑脚本即可。

## 二、最基础的用法

把你的文章写成 Markdown（`.md`），然后：

```bash
python jiajingwen_C4B_wechat-publisher/scripts/convert_to_wechat.py \
     你的文章.md 输出.html
```

打开 `输出.html` → `Ctrl+A` 全选 → `Ctrl+C` 复制 → 进入公众号编辑器（`mp.weixin.qq.com`）新建图文 → `Ctrl+V` 粘贴 → 手机预览 → 发布。

## 三、参数说明

| 参数 | 作用 |
|------|------|
| `--theme <name>` | 主题：`default` / `accent` / `warm` / `minimal` / `forest`（默认 `default`） |
| `--no-toc` | 不生成自动目录 |
| `--no-typo` | 关闭中英文/数字自动加空格 |
| `--embed-images` | 把本地图片内嵌成 base64，生成自包含 HTML |
| `--no-shell` | 只输出正文 HTML（不含预览外壳），适合二次处理 |
| `--title / --author / --date / --footer` | 命令行覆盖文章元数据 |

示例：

```bash
# 暖色主题 + 内嵌图片 + 关闭目录
python convert_to_wechat.py 文章.md 输出.html --theme warm --embed-images --no-toc
```

## 四、在 Markdown 里使用高级功能

### 1. 文章元数据（写在文件最顶部）

```yaml
---
title: 文章标题
author: 你的名字
date: 2026-10-07
abstract: 一句话摘要，会渲染成带边框的摘要框。
theme: accent
toc: true
footer: 自定义页脚（留空字符串可去掉）
---
```

### 2. Callout 高亮框

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
```

支持 `tip` / `warning` / `knowledge` / `info` / `note` 五种。

### 3. 自动目录

只要文章里有 `##` 二级标题，开启 `toc: true`（默认开）就会在摘要下方自动生成「一、二、三」结构预览。

### 4. 表格、代码块

照常写 Markdown 表格和 ``` 代码块即可，脚本会自动套用主题样式并适配公众号规则。

## 五、发布到公众号（关键一步）

1. 浏览器打开生成的 `输出.html`
2. `Ctrl+A` → `Ctrl+C`
3. 进入 `mp.weixin.qq.com` → 新建图文 → 正文 `Ctrl+V`
4. 若文章含图片且未用 `--embed-images`，需通过公众号素材库上传图片后替换
5. 手机预览 → 确认排版 → 发布

## 六、常见问题

- **粘贴后样式丢失？** 多半用了禁用标签/属性。本技能已自动处理，确保你是从本脚本输出粘贴。
- **目录点了不跳转？** 公众号会剥离 `id`，所以目录是结构预览而非跳转链接，这是设计使然。
- **SVG 图片消失？** 公众号保存即丢 SVG，请用 PNG/JPG/GIF，或用 `--embed-images` 内嵌。
- **想换配色？** 改 `scripts/convert_to_wechat.py` 里 `THEMES` 字典，照葫芦画瓢加一套即可。
