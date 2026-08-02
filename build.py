"""
Edge's Web - 文章管理器
用法: python build.py

扫描 articles/ 和 wiki/ 目录下的 .md 文件，自动：
1. 将 .md 转换为带完整模板的 .html 页面
2. 生成 articles.json 文章清单
3. 首页 index.html 通过 JS 读取 articles.json 展示文章列表

只需要把写好的 .md 文件丢进 articles/ 或 wiki/ 目录，然后运行 python build.py 即可。
"""

import json
import os
import re
import sys
import io
from datetime import date
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

# ============================================================
# 配置
# ============================================================

BASE_DIR = Path(__file__).parent
ARTICLES_DIR = BASE_DIR / "articles"
WIKI_DIR = BASE_DIR / "wiki"
SITE_TITLE = "Edge's Web"
SITE_URL = "/"

# ============================================================
# 模板
# ============================================================

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <script>!function(){{var t=localStorage.getItem('wiki-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}}()</script>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <!-- 液态玻璃背景 -->
    <div class="glass-bg"></div>

    <header class="header">
        <div class="header-inner">
            <a href="/" class="site-title">{site_title}</a>
            <nav class="nav">
                <ul class="nav-list">
                    <li><a href="https://wiki.xingqiwu.net.cn/">Wike</a></li>
                    <li><a href="../about.html">关于我</a></li>
                </ul>
            </nav>
            <div class="nav-right">
                <a class="nav-right-link" href="https://ucnift0madf0.feishu.cn/wiki/WPelwNGQ8ifj2kkCDjIcHKywnMf?from=from_copylink">讲座信息</a>
                <button class="nav-theme-toggle" id="nav-theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>
            </div>
        </div>
    </header>

    <main class="container">
        <article class="wiki article-page">
            <header class="article-header">
                <h1>{title}</h1>
                <div class="article-meta">
                    <time datetime="{date}">{date}</time>
                    {category_html}
                </div>
            </header>
            {toc}
            <div class="article-body">
                {content}
            </div>
        </article>
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <p><a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons License: BY-NC 4.0</a></p>
            <p>&copy; {year} {site_title}</p>
        </div>
    </footer>

    <script src="../script.js"></script>
</body>
</html>
"""

# 关于页模板（路径相对于根目录）
ABOUT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <script>!function(){{var t=localStorage.getItem('wiki-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}}()</script>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- 液态玻璃背景 -->
    <div class="glass-bg"></div>

    <header class="header">
        <div class="header-inner">
            <a href="/" class="site-title">{site_title}</a>
            <nav class="nav">
                <ul class="nav-list">
                    <li><a href="https://wiki.xingqiwu.net.cn/">Wike</a></li>
                    <li><a href="about.html">关于我</a></li>
                </ul>
            </nav>
            <div class="nav-right">
                <a class="nav-right-link" href="https://ucnift0madf0.feishu.cn/wiki/WPelwNGQ8ifj2kkCDjIcHKywnMf?from=from_copylink">讲座信息</a>
                <button class="nav-theme-toggle" id="nav-theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>
            </div>
        </div>
    </header>

    <main class="container">
        <article class="wiki article-page">
            {toc}
            <div class="article-body">
                {content}
            </div>
        </article>
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <p><a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons License: BY-NC 4.0</a></p>
            <p>&copy; {year} {site_title}</p>
        </div>
    </footer>

    <!-- 暗色/亮色 切换按钮 -->
    <button class="theme-toggle" id="theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>

    <script src="script.js"></script>
</body>
</html>
"""

# Wiki 页面模板（路径相对于根目录，与 articles 同级）
WIKI_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <script>!function(){{var t=localStorage.getItem('wiki-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}}()</script>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <!-- 液态玻璃背景 -->
    <div class="glass-bg"></div>

    <header class="header">
        <div class="header-inner">
            <a href="/" class="site-title">{site_title}</a>
            <nav class="nav">
                <ul class="nav-list">
                    <li><a href="https://wiki.xingqiwu.net.cn/">Wike</a></li>
                    <li><a href="../about.html">关于我</a></li>
                </ul>
            </nav>
            <div class="nav-right">
                <a class="nav-right-link" href="https://ucnift0madf0.feishu.cn/wiki/WPelwNGQ8ifj2kkCDjIcHKywnMf?from=from_copylink">讲座信息</a>
                <button class="nav-theme-toggle" id="nav-theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>
            </div>
        </div>
    </header>

    <main class="container">
        <article class="wiki article-page">
            <header class="article-header">
                <h1>{title}</h1>
            </header>
            {toc}
            <div class="article-body">
                {content}
            </div>
        </article>
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <p><a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons License: BY-NC 4.0</a></p>
            <p>&copy; {year} {site_title}</p>
        </div>
    </footer>

    <script src="../script.js"></script>
</body>
</html>
"""

CATEGORY_COLORS = {
    "编程基础": "box-green",
    "操作系统": "box-blue",
    "计算机网络": "box-violet",
    "开发工具": "box-gray",
    "数据库": "box-green",
    "其他": "box-gray",
}


def get_category_box(category):
    """返回分类标签的 HTML"""
    if not category:
        return ""
    cls = CATEGORY_COLORS.get(category, "box-gray")
    return f'<span class="box {cls}">{category}</span>'


# ============================================================
# Markdown 转换
# ============================================================

# 优先使用 python-markdown 库，否则使用内置简单转换器
try:
    import markdown as md_lib

    HAS_MARKDOWN_LIB = True
except ImportError:
    HAS_MARKDOWN_LIB = False


def convert_markdown(text: str) -> str:
    """将 markdown 文本转换为 HTML"""
    if HAS_MARKDOWN_LIB:
        # 使用 Markdown 实例以支持 toc 扩展配置
        md = md_lib.Markdown(
            extensions=[
                "fenced_code",
                "tables",
                "codehilite",
                "toc",
            ]
        )
        return md.convert(text)
    else:
        return simple_markdown_to_html(text)


def generate_toc_html(text: str) -> str:
    """从 markdown 文本生成目录 HTML（悬浮侧边栏样式）"""
    if not HAS_MARKDOWN_LIB:
        return ""

    # 使用带 toc marker 的转换器生成目录
    md = md_lib.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "codehilite",
            "toc",
        ]
    )
    # 先在内容前插入 [TOC] 标记，转换后提取目录 div
    text_with_toc = "[TOC]\n\n" + text
    full_html = md.convert(text_with_toc)

    # 提取 <div class="toc">...</div>
    toc_match = re.search(r'<div class="toc">\s*.*?</div>\s*', full_html, re.DOTALL)
    if toc_match:
        toc_html = toc_match.group(0)
        # 把目录标题 span 去掉
        toc_html = re.sub(r'<span class="toc-(title|header)">.*?</span>', '', toc_html)

        # 构建悬浮侧边栏结构
        result = '''<!-- 目录切换按钮 -->
<button class="toc-toggle-btn" id="toc-toggle-btn" title="目录" aria-label="打开目录">目录</button>

<!-- 目录侧边栏 -->
<aside class="toc-sidebar" id="toc-sidebar">
    <div class="toc-sidebar-header">
        <span class="toc-sidebar-title">目录</span>
        <button class="toc-close-btn" id="toc-close-btn" title="关闭目录" aria-label="关闭目录">✕</button>
    </div>
    <nav class="toc">
''' + toc_html + '''
    </nav>
</aside>'''
        return result
    return ""


def simple_markdown_to_html(text: str) -> str:
    """
    内置的简易 markdown → HTML 转换器
    支持：标题、代码块、行内代码、链接、图片、列表、粗体、斜体、表格、引用、段落
    """
    lines = text.split("\n")
    out = []
    in_code_block = False
    code_lang = ""
    code_content = []
    in_table = False
    table_rows = []
    in_list = None  # "ul" or "ol"
    list_tag = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                # 结束代码块
                lang_attr = f' class="language-{code_lang}"' if code_lang else ""
                code_html = (
                    f"<pre><code{lang_attr}>"
                    + "\n".join(code_content)
                    + "</code></pre>"
                )
                out.append(code_html)
                in_code_block = False
                code_content = []
                code_lang = ""
            else:
                # 开始代码块
                in_code_block = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # 表格
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(line)
            i += 1
            continue
        elif in_table:
            # 结束表格
            out.append(build_table(table_rows))
            in_table = False
            table_rows = []
            # 不要 i+=1，继续处理当前行
            continue

        # 空行
        if line.strip() == "":
            if in_list:
                out.append(f"</{list_tag}>")
                in_list = None
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline_parse(m.group(2))}</h{level}>")
            i += 1
            continue

        # 无序列表
        m = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if m:
            if in_list != "ul":
                if in_list:
                    out.append(f"</{list_tag}>")
                out.append("<ul>")
                in_list = "ul"
                list_tag = "ul"
            out.append(f"<li>{inline_parse(m.group(2))}</li>")
            i += 1
            continue

        # 有序列表
        m = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m:
            if in_list != "ol":
                if in_list:
                    out.append(f"</{list_tag}>")
                out.append("<ol>")
                in_list = "ol"
                list_tag = "ol"
            out.append(f"<li>{inline_parse(m.group(2))}</li>")
            i += 1
            continue

        # 引用
        if line.strip().startswith("> "):
            out.append(f"<blockquote><p>{inline_parse(line.strip()[2:])}</p></blockquote>")
            i += 1
            continue

        # 水平线
        if line.strip() in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue

        # 普通段落
        out.append(f"<p>{inline_parse(line)}</p>")
        i += 1

    # 收尾
    if in_code_block:
        lang_attr = f' class="language-{code_lang}"' if code_lang else ""
        out.append(
            f"<pre><code{lang_attr}>"
            + "\n".join(code_content)
            + "</code></pre>"
        )
    if in_table:
        out.append(build_table(table_rows))
    if in_list:
        out.append(f"</{list_tag}>")

    return "\n".join(out)


def build_table(rows):
    """构建 HTML 表格"""
    if len(rows) < 2:
        return ""
    html = "<table>\n"
    # 表头
    html += "<thead>\n<tr>\n"
    for cell in parse_table_row(rows[0]):
        html += f"<th>{inline_parse(cell.strip())}</th>\n"
    html += "</tr>\n</thead>\n"
    # 跳过对齐行 (|---|---|)
    body_start = 2 if re.match(r"^[\|\s\-:]+$", rows[1]) else 1
    html += "<tbody>\n"
    for row in rows[body_start:]:
        html += "<tr>\n"
        for cell in parse_table_row(row):
            html += f"<td>{inline_parse(cell.strip())}</td>\n"
        html += "</tr>\n"
    html += "</tbody>\n</table>"
    return html


def parse_table_row(line):
    """解析表格行"""
    cells = line.strip().split("|")
    # 去掉首尾空元素
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def inline_parse(text: str) -> str:
    """行内元素解析：粗体、斜体、行内代码、链接、图片"""
    # 图片 ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)
    # 链接 [text](url)
    text = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # 行内代码 `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 粗体+斜体 ***text***
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # 粗体 **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 斜体 *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


# ============================================================
# 文章解析
# ============================================================


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    解析 YAML frontmatter
    返回 (元数据字典, 剩余正文)
    """
    meta = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip()
            content = parts[2]

    return meta, content


def extract_title_from_body(text: str) -> str:
    """从正文提取第一个 # 标题作为文章标题"""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ""


def build_about():
    """构建关于页：about.md → about.html"""
    about_md = BASE_DIR / "about.md"
    if not about_md.exists():
        print("[提示] about.md 不存在，跳过")
        return

    print(f"[处理] about.md ...", end=" ")
    text = about_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    # 标题优先级: frontmatter title > 正文第一个 # heading > 默认值
    title = meta.get("title", "")
    if not title:
        title = extract_title_from_body(body)
    if not title:
        title = "关于我"

    # 去掉正文中的第一个 # 标题行
    body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

    body_html = convert_markdown(body)
    toc_html = generate_toc_html(body)

    full_html = ABOUT_TEMPLATE.format(
        title=title,
        site_title=SITE_TITLE,
        toc=toc_html,
        content=body_html,
        year=date.today().year,
    )

    about_html = BASE_DIR / "about.html"
    about_html.write_text(full_html, encoding="utf-8")
    print("✓")


def build_wiki():
    """构建 wiki 页面：wiki/*.md → wiki/*.html，并返回元数据列表"""
    wiki_meta_list = []

    if not WIKI_DIR.exists():
        print("[提示] wiki/ 目录不存在，跳过")
        return wiki_meta_list

    md_files = sorted(
        WIKI_DIR.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not md_files:
        print("[提示] wiki/ 目录下没有 .md 文件，跳过")
        return wiki_meta_list

    converted = 0
    for md_path in md_files:
        print(f"[Wiki] {md_path.name} ...", end=" ")

        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        # 标题优先级: frontmatter title > 正文第一个 # heading > 文件名
        title = meta.get("title", "")
        if not title:
            title = extract_title_from_body(body)
        if not title:
            title = md_path.stem

        # 日期
        wiki_date = meta.get("date", "")
        if not wiki_date:
            mtime = date.fromtimestamp(md_path.stat().st_mtime)
            wiki_date = mtime.isoformat()

        # 简介
        description = meta.get("description", "")

        # 排序顺序（数字越小越靠前，默认为999）
        order = meta.get("order", "999")
        try:
            order = int(order)
        except (ValueError, TypeError):
            order = 999

        # 去掉正文中的第一个 # 标题行
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

        # 转换 markdown → HTML
        body_html = convert_markdown(body)
        toc_html = generate_toc_html(body)

        # 填充模板
        full_html = WIKI_TEMPLATE.format(
            title=title,
            site_title=SITE_TITLE,
            toc=toc_html,
            content=body_html,
            year=date.today().year,
        )

        # 生成 HTML 文件到 wiki/ 目录
        html_name = md_path.stem + ".html"
        html_path = WIKI_DIR / html_name
        html_path.write_text(full_html, encoding="utf-8")
        converted += 1
        print("✓")

        wiki_meta_list.append(
            {
                "id": md_path.stem,
                "title": title,
                "date": wiki_date,
                "description": description,
                "order": order,
                "md_file": md_path.name,
                "html_file": html_name,
            }
        )

    print(f"[Wiki] 转换了 {converted} 个页面")

    # 按照 order 排序（数字越小越靠前）
    wiki_meta_list.sort(key=lambda x: (x.get("order", 999), x.get("date", "")))

    return wiki_meta_list


def build_articles():
    """主构建函数"""
    if not ARTICLES_DIR.exists():
        print(f"[错误] articles/ 目录不存在: {ARTICLES_DIR}")
        sys.exit(1)

    md_files = sorted(
        ARTICLES_DIR.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not md_files:
        print("[提示] articles/ 目录下没有 .md 文件，创建一个示例...")
        create_sample_article()
        md_files = list(ARTICLES_DIR.glob("*.md"))

    articles_meta = []
    converted = 0

    for md_path in md_files:
        print(f"[处理] {md_path.name} ...", end=" ")

        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        # 标题优先级: frontmatter title > 正文第一个 # heading > 文件名
        title = meta.get("title", "")
        if not title:
            title = extract_title_from_body(body)
        if not title:
            title = md_path.stem

        # 去掉正文中的第一个 # 标题行（会作为页面标题显示）
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

        # 日期
        article_date = meta.get("date", "")
        if not article_date:
            mtime = date.fromtimestamp(md_path.stat().st_mtime)
            article_date = mtime.isoformat()

        # 分类（支持 category 或 categories 字段）
        category = meta.get("category", "")
        if not category:
            categories = meta.get("categories", "")
            if isinstance(categories, list) and categories:
                category = categories[0]
            elif isinstance(categories, str):
                category = categories

        # 是否在首页显示（featured: 1 表示显示）
        featured = meta.get("featured", "")

        # 摘要（取正文前200字，去掉markdown标记）
        summary = re.sub(r"[#*`\[\]\(\)\|]", "", body[:200]).strip()
        summary = re.sub(r"\s+", " ", summary)

        # 生成 HTML 文件名
        html_name = md_path.stem + ".html"
        html_path = ARTICLES_DIR / html_name

        # 转换 markdown → HTML
        body_html = convert_markdown(body)
        toc_html = generate_toc_html(body)

        # 生成分类标签
        category_html = get_category_box(category)

        # 填充模板
        full_html = PAGE_TEMPLATE.format(
            title=title,
            site_title=SITE_TITLE,
            date=article_date,
            category_html=category_html,
            toc=toc_html,
            content=body_html,
            year=date.today().year,
        )

        html_path.write_text(full_html, encoding="utf-8")
        converted += 1
        print("✓")

        articles_meta.append(
            {
                "id": md_path.stem,
                "title": title,
                "date": article_date,
                "category": category,
                "featured": featured,
                "summary": summary,
                "md_file": md_path.name,
                "html_file": html_name,
            }
        )

    # 生成 articles.json
    manifest_path = BASE_DIR / "articles.json"
    manifest_path.write_text(
        json.dumps(articles_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[完成] 转换了 {converted} 篇文章")
    print(f"[清单] articles.json 已更新 ({len(articles_meta)} 条)")

    # 直接注入文章列表到 index.html（避免 file:// 下 fetch 跨域问题）
    inject_article_list(articles_meta)
    print(f"[首页] index.html 文章列表已更新")


def inject_article_list(articles_meta: list):
    """把文章列表 HTML 直接注入 index.html 和 articles.html，替换 <!-- ARTICLE_LIST_START --> ... <!-- ARTICLE_LIST_END --> 之间的内容"""
    # 筛选首页展示的文章：featured=1 的文章优先，不足3篇时用最新的补足
    featured_articles = [a for a in articles_meta if a.get("featured") == "1"]
    remaining_needed = 3 - len(featured_articles)

    if remaining_needed > 0:
        # 从非 featured 文章中取最新的来补足
        non_featured = [a for a in articles_meta if a.get("featured") != "1"]
        featured_articles.extend(non_featured[:remaining_needed])

    # 最多显示3篇
    display_articles = featured_articles[:3]

    # 构建文章列表 HTML
    if not display_articles:
        article_html = '<ul id="article-list" class="article-list">\n<li class="empty">还没有文章。在 articles/ 目录下创建 .md 文件，然后运行 <code>python build.py</code></li>\n</ul>'
    else:
        items = []
        for a in display_articles:
            cat_html = get_category_box(a["category"])
            items.append(
                f'<li class="article-item">'
                f'<a href="articles/{a["html_file"]}">{a["title"]}</a>'
                f'{cat_html}'
                f' <time class="article-date" datetime="{a["date"]}">{a["date"]}</time>'
                f'</li>'
            )
        article_html = '<ul id="article-list" class="article-list">\n' + "\n".join(items) + '\n</ul>'

    # 注入到 index.html
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        html = index_path.read_text(encoding="utf-8")
        pattern = r"<!-- ARTICLE_LIST_START -->.*?<!-- ARTICLE_LIST_END -->"
        replacement = f"<!-- ARTICLE_LIST_START -->\n{article_html}\n<!-- ARTICLE_LIST_END -->"
        html = re.sub(pattern, replacement, html, count=0, flags=re.DOTALL)
        index_path.write_text(html, encoding="utf-8")

    # 注入到 articles.html（显示所有文章）
    articles_html_path = BASE_DIR / "articles.html"
    if articles_html_path.exists():
        html = articles_html_path.read_text(encoding="utf-8")
        # 构建完整文章列表
        if not articles_meta:
            full_article_html = '<ul id="article-list" class="article-list">\n<li class="empty">还没有文章。</li>\n</ul>'
        else:
            items = []
            for a in articles_meta:
                cat_html = get_category_box(a["category"])
                items.append(
                    f'<li class="article-item">'
                    f'<a href="articles/{a["html_file"]}">{a["title"]}</a>'
                    f'{cat_html}'
                    f' <time class="article-date" datetime="{a["date"]}">{a["date"]}</time>'
                    f'</li>'
                )
            full_article_html = '<ul id="article-list" class="article-list">\n' + "\n".join(items) + '\n</ul>'
        pattern = r"<!-- ARTICLE_LIST_START -->.*?<!-- ARTICLE_LIST_END -->"
        replacement = f"<!-- ARTICLE_LIST_START -->\n{full_article_html}\n<!-- ARTICLE_LIST_END -->"
        html = re.sub(pattern, replacement, html, count=0, flags=re.DOTALL)
        articles_html_path.write_text(html, encoding="utf-8")


def inject_wiki_list(wiki_meta_list: list):
    """把 wiki 列表 HTML 直接注入 index.html，替换 <!-- WIKI_LIST_START --> ... <!-- WIKI_LIST_END --> 之间的内容"""
    index_path = BASE_DIR / "index.html"

    if not index_path.exists():
        print(f"[警告] index.html 不存在，跳过 wiki 注入")
        return

    html = index_path.read_text(encoding="utf-8")

    if not wiki_meta_list:
        wiki_html = '<div class="wiki-list">\n<p class="empty">还没有 Wiki 页面。在 wiki/ 目录下创建 .md 文件，然后运行 <code>python build.py</code></p>\n</div>'
    else:
        # 只显示2个 wiki
        display_wikis = wiki_meta_list[:2]
        items = []
        for w in display_wikis:
            description = w.get("description", "")
            desc_html = f'<p class="wiki-item-desc">{description}</p>' if description else ''
            items.append(
                f'<div class="wiki-item">'
                f'<a href="wiki/{w["html_file"]}" class="wiki-item-title">{w["title"]}</a>'
                f'{desc_html}'
                f'</div>'
            )
        wiki_html = '<div class="wiki-list">\n' + "\n".join(items) + '\n</div>'

    pattern = r"<!-- WIKI_LIST_START -->.*?<!-- WIKI_LIST_END -->"
    replacement = f"<!-- WIKI_LIST_START -->\n{wiki_html}\n<!-- WIKI_LIST_END -->"
    html = re.sub(pattern, replacement, html, count=0, flags=re.DOTALL)
    index_path.write_text(html, encoding="utf-8")


def create_sample_article():
    """创建示例文章"""
    sample = """---
title: Hello World - 第一篇文章
date: 2024-01-15
category: 编程基础
---

## 关于这篇文章

这是我的第一篇 Wiki 文章。

## 代码示例

```c
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
```

## 要点

- 保持好奇心
- **实践**比理论更重要
- 善用工具，比如 `gdb` 和 `git`

> 程序 = 数据结构 + 算法
"""
    sample_path = ARTICLES_DIR / "hello-world.md"
    sample_path.write_text(sample, encoding="utf-8")
    print(f"[创建] 示例文章: {sample_path.name}")


if __name__ == "__main__":
    build_about()
    wiki_meta = build_wiki()
    build_articles()

    # 将 wiki 列表注入 index.html
    inject_wiki_list(wiki_meta)

    # 将 wiki 元数据追加到 articles.json
    manifest_path = BASE_DIR / "articles.json"
    if manifest_path.exists() and wiki_meta:
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # 在 JSON 中添加 wikis 字段
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump({"articles": data, "wikis": wiki_meta}, f, ensure_ascii=False, indent=2)
            else:
                # 已有 articles/wikis 结构
                data["wikis"] = wiki_meta
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 更新 articles.json 失败: {e}")

    if wiki_meta:
        print(f"[首页] index.html Wiki 列表已更新")
