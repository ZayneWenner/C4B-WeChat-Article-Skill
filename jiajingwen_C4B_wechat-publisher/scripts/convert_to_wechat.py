#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Publisher (CUSTOMIZED) — Markdown / Word → 微信公众号兼容 HTML

在 starter kit 基础上新增的能力：
  1. 多主题系统（default / accent / warm / minimal / forest）
  2. Callout 高亮框（:::info / :::tip / :::warning / :::knowledge / :::note）
  3. 自动目录（从 h2 标题生成「一、二、三…」结构预览）
  4. 文章元数据（frontmatter：title / author / date / abstract）
  5. 页脚版权声明（可自定义）
  6. 中文排版优化（中英文 / 数字间距自动加空格）
  7. 本地图片 base64 内嵌（--embed-images，生成自包含 HTML）

用法：
  python convert_to_wechat.py input.md output.html
  python convert_to_wechat.py input.md output.html --theme accent --toc
  python convert_to_wechat.py input.md output.html --embed-images --no-typo

然后在浏览器打开 output.html → Ctrl+A → Ctrl+C → 粘贴到公众号编辑器。
"""

import sys
import os
import re
import base64
import argparse
from pathlib import Path

# --- 依赖自动安装（首次运行） ---
def install_dependencies():
    missing = []
    try:
        import markdown  # noqa
    except ImportError:
        missing.append("markdown")
    try:
        from bs4 import BeautifulSoup  # noqa
    except ImportError:
        missing.append("beautifulsoup4")
    try:
        from docx import Document  # noqa
    except ImportError:
        missing.append("python-docx")
    try:
        import lxml  # noqa
    except ImportError:
        missing.append("lxml")
    if missing:
        print(f"安装缺失依赖: {', '.join(missing)} ...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        except subprocess.CalledProcessError:
            # 某些环境需要 --break-system-packages
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", *missing, "--break-system-packages", "-q"]
            )
        print("完成！\n")

install_dependencies()

import markdown
from bs4 import BeautifulSoup, NavigableString
from docx import Document


# ============================================================
# 微信公众号约束
# ============================================================
ALLOWED_TAGS = {
    'p', 'h2', 'h3', 'ul', 'ol', 'li', 'span', 'img', 'a',
    'table', 'tr', 'th', 'td', 'br',
}
FORBIDDEN_TAGS = {'script', 'style', 'iframe', 'h1', 'div'}
ALLOWED_CSS = {
    'color', 'background-color', 'font-size', 'font-weight',
    'line-height', 'text-align', 'font-style', 'margin',
    'padding', 'border', 'border-left', 'border-top', 'border-radius',
    'border-collapse', 'text-decoration', 'white-space', 'word-wrap',
    'max-width', 'width', 'vertical-align',
}


# ============================================================
# 主题系统
# ============================================================
# 每个主题是一套 inline CSS 值与 accent 主色，可自由扩展。
THEMES = {
    'default': {
        'accent': '#0366d6',
        'h2': 'font-size: 22px; font-weight: bold; line-height: 1.6; color: #333; margin: 20px 0 10px 0;',
        'h3': 'font-size: 18px; font-weight: bold; line-height: 1.6; color: #333; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;',
        'code_inline': 'background-color: #f5f5f5; color: #d73a49; font-size: 14px; padding: 2px 4px; border-radius: 3px;',
        'code_block': 'background-color: #f6f8fa; color: #24292e; font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; white-space: pre-wrap; word-wrap: break-word; border-radius: 4px;',
        'blockquote': 'background-color: #f9f9f9; color: #666; padding: 10px 15px; margin: 10px 0; border-left: 4px solid #ddd; border-radius: 3px;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px;',
        'th': 'background-color: #f6f8fa; color: #24292e; font-weight: bold; padding: 8px; text-align: left; border: 1px solid #ddd;',
        'td': 'padding: 8px; border: 1px solid #ddd; color: #333;',
        'a': 'color: #0366d6; text-decoration: underline;',
        'title': 'font-size: 24px; font-weight: bold; line-height: 1.4; color: #333; margin: 12px 0 6px 0;',
        'subtitle': 'font-size: 13px; color: #999; margin: 4px 0 16px 0;',
    },
    'accent': {
        'accent': '#1a73e8',
        'h2': 'font-size: 22px; font-weight: bold; line-height: 1.6; color: #1a73e8; margin: 20px 0 10px 0; border-left: 4px solid #1a73e8; padding-left: 10px;',
        'h3': 'font-size: 18px; font-weight: bold; line-height: 1.6; color: #1a73e8; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;',
        'code_inline': 'background-color: #eef3fb; color: #1a73e8; font-size: 14px; padding: 2px 4px; border-radius: 3px;',
        'code_block': 'background-color: #f0f7ff; color: #1a3a6b; font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; white-space: pre-wrap; word-wrap: break-word; border-left: 3px solid #1a73e8; border-radius: 4px;',
        'blockquote': 'background-color: #f0f7ff; color: #444; padding: 10px 15px; margin: 10px 0; border-left: 4px solid #1a73e8; border-radius: 3px;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px;',
        'th': 'background-color: #e8f0fe; color: #1a3a6b; font-weight: bold; padding: 8px; text-align: left; border: 1px solid #c5d9f5;',
        'td': 'padding: 8px; border: 1px solid #c5d9f5; color: #333;',
        'a': 'color: #1a73e8; text-decoration: underline;',
        'title': 'font-size: 24px; font-weight: bold; line-height: 1.4; color: #1a73e8; margin: 12px 0 6px 0;',
        'subtitle': 'font-size: 13px; color: #999; margin: 4px 0 16px 0;',
    },
    'warm': {
        'accent': '#e65100',
        'h2': 'font-size: 22px; font-weight: bold; line-height: 1.6; color: #e65100; margin: 20px 0 10px 0;',
        'h3': 'font-size: 18px; font-weight: bold; line-height: 1.6; color: #bf360c; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;',
        'code_inline': 'background-color: #fff3e0; color: #e65100; font-size: 14px; padding: 2px 4px; border-radius: 3px;',
        'code_block': 'background-color: #fff8e1; color: #5d4037; font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; white-space: pre-wrap; word-wrap: break-word; border-left: 3px solid #ff9800; border-radius: 4px;',
        'blockquote': 'background-color: #fff8e1; color: #444; padding: 10px 15px; margin: 10px 0; border-left: 4px solid #ff9800; border-radius: 3px;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px;',
        'th': 'background-color: #ffe0b2; color: #5d4037; font-weight: bold; padding: 8px; text-align: left; border: 1px solid #ffcc80;',
        'td': 'padding: 8px; border: 1px solid #ffcc80; color: #333;',
        'a': 'color: #e65100; text-decoration: underline;',
        'title': 'font-size: 24px; font-weight: bold; line-height: 1.4; color: #e65100; margin: 12px 0 6px 0;',
        'subtitle': 'font-size: 13px; color: #999; margin: 4px 0 16px 0;',
    },
    'minimal': {
        'accent': '#555555',
        'h2': 'font-size: 21px; font-weight: bold; line-height: 1.6; color: #222; margin: 20px 0 10px 0;',
        'h3': 'font-size: 17px; font-weight: bold; line-height: 1.6; color: #222; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.8; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.8; color: #333; margin: 5px 0;',
        'code_inline': 'background-color: #f2f2f2; color: #333; font-size: 14px; padding: 2px 4px; border-radius: 3px;',
        'code_block': 'background-color: #fafafa; color: #333; font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #eee; border-radius: 4px;',
        'blockquote': 'background-color: #fafafa; color: #666; padding: 10px 15px; margin: 10px 0; border-left: 4px solid #999; border-radius: 3px;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px;',
        'th': 'background-color: #f5f5f5; color: #222; font-weight: bold; padding: 8px; text-align: left; border: 1px solid #ddd;',
        'td': 'padding: 8px; border: 1px solid #ddd; color: #333;',
        'a': 'color: #555; text-decoration: underline;',
        'title': 'font-size: 23px; font-weight: bold; line-height: 1.4; color: #222; margin: 12px 0 6px 0;',
        'subtitle': 'font-size: 13px; color: #aaa; margin: 4px 0 16px 0;',
    },
    'forest': {
        'accent': '#2e7d32',
        'h2': 'font-size: 22px; font-weight: bold; line-height: 1.6; color: #2e7d32; margin: 20px 0 10px 0;',
        'h3': 'font-size: 18px; font-weight: bold; line-height: 1.6; color: #1b5e20; margin: 15px 0 8px 0;',
        'p': 'font-size: 16px; line-height: 1.75; color: #333; margin: 10px 0;',
        'li': 'font-size: 16px; line-height: 1.75; color: #333; margin: 5px 0;',
        'code_inline': 'background-color: #e8f5e9; color: #2e7d32; font-size: 14px; padding: 2px 4px; border-radius: 3px;',
        'code_block': 'background-color: #f1f8f2; color: #1b5e20; font-size: 14px; line-height: 1.6; padding: 16px; margin: 10px 0; white-space: pre-wrap; word-wrap: break-word; border-left: 3px solid #2e7d32; border-radius: 4px;',
        'blockquote': 'background-color: #e8f5e9; color: #444; padding: 10px 15px; margin: 10px 0; border-left: 4px solid #2e7d32; border-radius: 3px;',
        'table': 'border-collapse: collapse; margin: 10px 0; font-size: 14px;',
        'th': 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold; padding: 8px; text-align: left; border: 1px solid #a5d6a7;',
        'td': 'padding: 8px; border: 1px solid #a5d6a7; color: #333;',
        'a': 'color: #2e7d32; text-decoration: underline;',
        'title': 'font-size: 24px; font-weight: bold; line-height: 1.4; color: #2e7d32; margin: 12px 0 6px 0;',
        'subtitle': 'font-size: 13px; color: #999; margin: 4px 0 16px 0;',
    },
}

# Callout 类型定义（颜色独立于主题，保证辨识度）
CALLOUT_TYPES = {
    'info':      {'icon': 'ℹ️', 'label': '说明', 'bg': '#eef6ff', 'border': '#1a73e8'},
    'tip':       {'icon': '💡', 'label': '贴士', 'bg': '#eafaf0', 'border': '#1aad5a'},
    'warning':   {'icon': '⚠️', 'label': '注意', 'bg': '#fff4e5', 'border': '#ff9800'},
    'knowledge': {'icon': '📘', 'label': '知识点', 'bg': '#f3ecff', 'border': '#7b4dff'},
    'note':      {'icon': '📌', 'label': '笔记', 'bg': '#f5f5f5', 'border': '#999999'},
}

MD_EXT = ['extra', 'fenced_code', 'nl2br', 'sane_lists']


# ============================================================
# 输入读取
# ============================================================
def parse_frontmatter(text):
    """解析 YAML 风格 frontmatter。返回 (meta_dict, 剩余正文)。"""
    meta = {}
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return meta, text
    block = m.group(1)
    rest = text[m.end():]
    lines = block.split('\n')
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        mm = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
        if not mm:
            idx += 1
            continue
        key = mm.group(1).lower()
        val = mm.group(2).strip()
        if val in ('>', '|', '>-', '|+', '>+', '|-'):
            idx += 1
            buf = []
            while idx < len(lines) and (lines[idx].startswith('  ') or lines[idx].startswith('\t')):
                buf.append(lines[idx].strip())
                idx += 1
            meta[key] = ' '.join(buf)
        else:
            meta[key] = val.strip().strip('"').strip("'")
            idx += 1
    return meta, rest


def extract_callouts(md_text):
    """把 :::type ... ::: 块提取为占位符，返回 (新md, [callout_html,...])。"""
    callouts = []

    def repl(match):
        ctype = match.group(1).lower()
        inner = match.group(2)
        html = render_callout(ctype, inner)
        callouts.append(html)
        return "\n@@CALLOUT_%d@@\n" % (len(callouts) - 1)

    pattern = re.compile(r'^:::\s*(\w+)\s*\n(.*?)\n:::\s*$', re.MULTILINE | re.DOTALL)
    new_md = pattern.sub(repl, md_text)
    return new_md, callouts


def render_callout(ctype, inner):
    spec = CALLOUT_TYPES.get(ctype, CALLOUT_TYPES['note'])
    inner_html = markdown.markdown(inner.strip(), extensions=MD_EXT)
    isoup = BeautifulSoup(inner_html, 'lxml')
    children = [c for c in isoup.children
               if not (isinstance(c, str) and not c.strip())]
    if len(children) == 1 and getattr(children[0], 'name', None) == 'p':
        body = ''.join(str(c) for c in children[0].children)
    else:
        parts = []
        for c in children:
            name = getattr(c, 'name', None)
            if name in ('ul', 'ol'):
                for li in c.find_all('li', recursive=False):
                    parts.append('• ' + li.get_text() + '<br>')
            elif name == 'p':
                parts.append(c.get_text() + '<br>')
            else:
                parts.append(c.get_text() + '<br>')
        body = ''.join(parts).rstrip('<br>')
    label = ('<span style="font-weight:bold;color:%s;">%s %s</span><br>'
             % (spec['border'], spec['icon'], spec['label']))
    style = ('background-color:%s;border-left:4px solid %s;padding:12px 15px;'
             'margin:15px 0;border-radius:4px;font-size:15px;line-height:1.7;color:#333;'
             % (spec['bg'], spec['border']))
    return '<p style="%s">%s%s</p>' % (style, label, body)


def read_markdown(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    meta, body = parse_frontmatter(text)
    body, callouts = extract_callouts(body)
    html = markdown.markdown(body, extensions=MD_EXT)
    return html, meta, callouts


def read_docx(filepath):
    doc = Document(filepath)
    parts = []
    meta = {}
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style_name = para.style.name if para.style else ''
        if style_name.startswith('Heading'):
            level = style_name.replace('Heading ', '')
            tag = 'h2' if level in ('1', '2') else 'h3'
            parts.append('<%s>%s</%s>' % (tag, text, tag))
        else:
            p_html = '<p>'
            for run in para.runs:
                t = run.text
                if not t:
                    continue
                if run.bold and run.italic:
                    p_html += '<span style="font-weight:bold;font-style:italic;">%s</span>' % t
                elif run.bold:
                    p_html += '<span style="font-weight:bold;">%s</span>' % t
                elif run.italic:
                    p_html += '<span style="font-style:italic;">%s</span>' % t
                else:
                    p_html += t
            p_html += '</p>'
            parts.append(p_html)
    return '\n'.join(parts), meta, []


# ============================================================
# 清洗 / 样式
# ============================================================
def sanitize(html):
    soup = BeautifulSoup(html, 'lxml')
    for tag_name in ('script', 'style', 'iframe'):
        for el in soup.find_all(tag_name):
            el.decompose()
    for h1 in soup.find_all('h1'):
        h1.name = 'h2'
    for div in soup.find_all('div'):
        div.name = 'p'
    for pre in soup.find_all('pre'):
        code = pre.find('code')
        code_text = code.get_text() if code else pre.get_text()
        p = soup.new_tag('p')
        p.string = code_text
        pre.replace_with(p)
    for code in soup.find_all('code'):
        if code.parent and code.parent.name == 'pre':
            continue
        span = soup.new_tag('span')
        span.string = code.get_text()
        code.replace_with(span)
    for bq in soup.find_all('blockquote'):
        p = soup.new_tag('p')
        p.string = bq.get_text()
        bq.replace_with(p)
    for tag in soup.find_all(['strong', 'b']):
        span = soup.new_tag('span')
        span.string = tag.get_text()
        span['style'] = 'font-weight: bold;'
        tag.replace_with(span)
    for tag in soup.find_all(['em', 'i']):
        span = soup.new_tag('span')
        span.string = tag.get_text()
        span['style'] = 'font-style: italic;'
        tag.replace_with(span)
    return soup


def apply_styles(soup, theme):
    style_map = {
        'h2': theme['h2'], 'h3': theme['h3'], 'p': theme['p'], 'li': theme['li'],
        'table': theme['table'], 'th': theme['th'], 'td': theme['td'], 'a': theme['a'],
    }
    code_style = theme['code_inline']
    code_block_style = theme['code_block']
    bq_style = theme['blockquote']
    for tag_name, style in style_map.items():
        for el in soup.find_all(tag_name):
            if el.has_attr('style'):
                continue
            # 代码块（pre→p）含换行，留待 restyle 阶段单独上样式
            if tag_name == 'p' and '\n' in el.get_text():
                continue
            el['style'] = style
    return soup


def restyle_code_and_quote(soup, theme):
    """为代码块与行内 code 补齐主题样式（sanitize 阶段已把它们转成 p / span）。"""
    for p in soup.find_all('p'):
        if '\n' in p.get_text() and not p.has_attr('style'):
            p['style'] = theme['code_block']
    for span in soup.find_all('span'):
        if not span.has_attr('style'):
            span['style'] = theme['code_inline']
    return soup


def clean_attributes(soup):
    for tag in soup.find_all(True):
        for attr in ('class', 'id'):
            if attr in tag.attrs:
                del tag.attrs[attr]
        if tag.name not in ALLOWED_TAGS and tag.name not in ('html', 'head', 'body', '[document]'):
            tag.unwrap()
    return soup


def replace_callouts(soup, callouts):
    for p in soup.find_all('p'):
        txt = p.get_text()
        m = re.search(r'@@CALLOUT_(\d+)@@', txt)
        if m:
            idx = int(m.group(1))
            cal = BeautifulSoup(callouts[idx], 'lxml').find('p')
            if cal:
                p.replace_with(cal)
    return soup


# ============================================================
# 元数据头 / 目录 / 页脚
# ============================================================
def build_header(meta, theme, cli):
    parts = []
    title = meta.get('title') or cli.get('title')
    author = meta.get('author') or cli.get('author') or ''
    date = meta.get('date') or cli.get('date') or ''
    abstract = meta.get('abstract')
    if title:
        parts.append('<p style="%s">%s</p>' % (theme['title'], title))
    if author or date:
        sub = ' · '.join(filter(None, [author, date]))
        parts.append('<p style="%s">%s</p>' % (theme['subtitle'], sub))
    if abstract:
        ab_style = ('background-color:#f7f7f7;border-left:4px solid %s;padding:12px 15px;'
                    'margin:12px 0 18px 0;border-radius:4px;font-size:14px;line-height:1.7;color:#555;'
                    % theme['accent'])
        parts.append('<p style="%s"><span style="font-weight:bold;color:%s;">📝 摘要</span><br>%s</p>'
                     % (ab_style, theme['accent'], abstract))
    return parts


def build_toc(article_html, theme):
    tsoup = BeautifulSoup(article_html, 'lxml')
    h2s = tsoup.find_all('h2')
    h2s = [h for h in h2s if '@@CALLOUT' not in h.get_text()]
    if not h2s:
        return []
    nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    parts = ['<p style="font-size:15px;font-weight:bold;color:%s;margin:10px 0 6px 0;">📑 本文目录</p>'
             % theme['accent']]
    for i, h in enumerate(h2s):
        n = nums[i] if i < len(nums) else str(i + 1)
        t = h.get_text().strip()
        parts.append('<p style="font-size:14px;color:#555;margin:4px 0;line-height:1.6;">%s、%s</p>'
                     % (n, t))
    return parts


def build_footer(meta, theme, cli):
    custom = meta.get('footer') or cli.get('footer')
    if custom is not None and custom == '':
        return []
    if custom:
        text = custom
    else:
        author = meta.get('author') or cli.get('author') or '作者'
        text = '© %s %s ｜ 本文由 wechat-publisher 技能生成' % (
            meta.get('date') or cli.get('date') or '2026', author)
    style = ('font-size:12px;color:#999;border-top:1px solid #eee;padding-top:10px;'
             'margin-top:24px;text-align:center;')
    return ['<p style="%s">%s</p>' % (style, text)]


# ============================================================
# 中文排版优化
# ============================================================
def typography_text(text):
    # 中英文 / 中文数字之间加一个半角空格（中文排版惯例）
    text = re.sub(r'([一-鿿])([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z0-9])([一-鿿])', r'\1 \2', text)
    return text


def apply_typography(soup):
    nodes = []
    for node in soup.find_all(string=True):
        parent = node.parent
        if parent is None:
            continue
        if parent.name in ('code', 'script', 'style'):
            continue
        # 代码块（pre→p，带 pre-wrap/换行）不做中英文加空格，避免破坏命令
        if parent.name == 'p' and 'pre-wrap' in parent.get('style', ''):
            continue
        new = typography_text(str(node))
        if new != str(node):
            nodes.append((node, new))
    for node, new in nodes:
        node.replace_with(NavigableString(new))
    return soup


# ============================================================
# 图片 base64 内嵌
# ============================================================
def embed_images(soup, base_dir):
    mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif'}
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith(('http://', 'https://', 'data:')):
            continue
        p = src if os.path.isabs(src) else os.path.join(base_dir, src)
        if os.path.exists(p):
            ext = os.path.splitext(p)[1].lower().lstrip('.')
            mime = mime_map.get(ext)
            if mime:
                data = base64.b64encode(open(p, 'rb').read()).decode('ascii')
                img['src'] = 'data:%s;base64,%s' % (mime, data)
    return soup


# ============================================================
# 主流程
# ============================================================
def normalize_line_heights(soup):
    """把倍数行高（line-height: 1.75）统一改写为显式 px（line-height: 28px）。

    为什么必须做这一步：公众号编辑器的「内容结构检测」在比对行高与字号时按
    数值字面量比较，`line-height: 1.75` 会被读成 1.75 < 16px，从而误报
    「行高小于字体大小，可能导致文字重叠」；写成 px 后两项同为像素值，
    检测器不再误判。同时保留 ≥1.75 倍的字号比例，保证多行文字不会真的重叠。
    """
    def nearest_font_size(tag, default=16.0):
        node = tag.parent
        while node is not None:
            m = re.search(r'font-size\s*:\s*([\d.]+)px', node.get('style') or '')
            if m:
                return float(m.group(1))
            node = node.parent
        return default

    def fix_style(style_str, inherited_fs):
        m_fs = re.search(r'font-size\s*:\s*([\d.]+)px', style_str)
        fs = float(m_fs.group(1)) if m_fs else inherited_fs

        def repl(m):
            if m.group(2):  # 已经是 px，原样保留，避免二次改写
                return m.group(0)
            ratio = float(m.group(1))
            return 'line-height: %dpx' % round(fs * max(ratio, 1.75))

        return re.sub(r'line-height\s*:\s*([\d.]+)(px)?\s*(?=;|$)', repl, style_str)

    for tag in soup.find_all(True):
        style = tag.get('style')
        if not style or 'line-height' not in style:
            continue
        new_style = fix_style(style, nearest_font_size(tag))
        if new_style != style:
            tag['style'] = new_style
    return soup


def convert(input_path, output_path, args):
    path = Path(input_path)
    if not path.exists():
        print("❌ 文件不存在: %s" % input_path)
        return False

    ext = path.suffix.lower()
    print("📖 读取 %s (%s) ..." % (path.name, ext))
    if ext == '.md':
        html, meta, callouts = read_markdown(input_path)
    elif ext == '.docx':
        html, meta, callouts = read_docx(input_path)
    elif ext in ('.html', '.htm'):
        with open(input_path, 'r', encoding='utf-8') as f:
            html = f.read()
        meta, callouts = {}, []
    else:
        print("❌ 不支持的格式: %s（支持 .md / .docx / .html）" % ext)
        return False

    theme_name = (meta.get('theme') or args.theme or 'default').lower()
    if theme_name not in THEMES:
        print("⚠️ 未知主题 '%s'，回退到 default" % theme_name)
        theme_name = 'default'
    theme = THEMES[theme_name]

    print("🧹 清洗 HTML（适配公众号规则）...")
    soup = sanitize(html)
    soup = replace_callouts(soup, callouts)
    soup = apply_styles(soup, theme)
    soup = restyle_code_and_quote(soup, theme)
    soup = clean_attributes(soup)

    body = soup.find('body')
    article_nodes = [c for c in (body or soup).children if str(c).strip()]
    article_html = ''.join(str(c) for c in article_nodes)

    cli = {'title': args.title, 'author': args.author, 'date': args.date, 'footer': args.footer}

    print("🎨 应用主题 '%s' ..." % theme_name)
    header = build_header(meta, theme, cli)

    toc_enabled = args.toc
    if 'toc' in meta:
        toc_enabled = str(meta.get('toc')).lower() not in ('false', 'no', '0')
    toc = build_toc(article_html, theme) if toc_enabled else []

    footer = build_footer(meta, theme, cli)

    final_parts = header + toc + article_nodes + footer
    final_html = ''.join(str(p) for p in final_parts)

    fsoup = BeautifulSoup(final_html, 'lxml')
    if args.typo:
        print("🔤 优化中文排版...")
        fsoup = apply_typography(fsoup)
    fsoup = normalize_line_heights(fsoup)

    if args.embed_images:
        print("🖼️ 内嵌本地图片...")
        fsoup = embed_images(fsoup, str(path.parent))

    content = '\n'.join(str(c) for c in fsoup.children if str(c).strip())

    if args.no_shell:
        output_html = content
    else:
        output_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WeChat Article Preview</title>
</head>
<body style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;">
%s
</body>
</html>""" % content

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)

    size_kb = os.path.getsize(output_path) / 1024
    print("\n✅ 完成！%s (%.1f KB)，主题=%s" % (output_path, size_kb, theme_name))
    print("\n📋 下一步：")
    print("   1. 浏览器打开 %s 预览" % output_path)
    print("   2. Ctrl+A → Ctrl+C 全选复制")
    print("   3. 进入 mp.weixin.qq.com 新建图文")
    print("   4. Ctrl+V 粘贴到正文")
    print("   5. 如需图片，通过公众号素材库上传（本工具已处理本地图内嵌）")
    print("   6. 手机预览 → 发布！")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Markdown/Word → 微信公众号 HTML 转换器（增强版）')
    parser.add_argument('input', help='输入文件 (.md / .docx / .html)')
    parser.add_argument('output', help='输出 HTML 文件')
    parser.add_argument('--theme', default='default',
                        choices=list(THEMES.keys()),
                        help='主题：%s（默认 default）' % ' / '.join(THEMES.keys()))
    parser.add_argument('--toc', dest='toc', action='store_true', default=True,
                        help='生成自动目录（默认开）')
    parser.add_argument('--no-toc', dest='toc', action='store_false', help='不生成目录')
    parser.add_argument('--typo', dest='typo', action='store_true', default=True,
                        help='中文排版优化（默认开）')
    parser.add_argument('--no-typo', dest='typo', action='store_false', help='关闭中文排版优化')
    parser.add_argument('--embed-images', action='store_true', help='将本地图片内嵌为 base64')
    parser.add_argument('--no-shell', action='store_true', help='只输出正文 HTML（不含预览外壳）')
    parser.add_argument('--title', default=None, help='文章标题（覆盖 frontmatter）')
    parser.add_argument('--author', default=None, help='作者名')
    parser.add_argument('--date', default=None, help='日期')
    parser.add_argument('--footer', default=None, help='自定义页脚（传空字符串可去掉页脚）')
    args = parser.parse_args()

    success = convert(args.input, args.output, args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
