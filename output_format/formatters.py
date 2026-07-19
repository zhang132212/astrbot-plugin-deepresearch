# output_format/formatters.py
"""Concrete report formatters and the shared visual report theme."""

import html
import math
import re
from datetime import datetime
from typing import Optional

import markdown
from astrbot.api import logger
from astrbot.api.star import Star
from bs4 import BeautifulSoup

from .base import BaseOutputFormatter
from .flowchart import render_mermaid_flowchart
from .hero_patterns import render_random_hero


SOURCE_PATTERN = re.compile(r"\[来源:\s*(https?://[^\]\s]+)\]")
REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<style>
  :root {{
    --ink: #33363d;
    --muted: #747780;
    --paper: #fffdfb;
    --canvas: #f4f1ef;
    --cyan: #55bfd9;
    --cyan-soft: #e8f8fb;
    --pink: #ef8eb1;
    --pink-soft: #fcebf2;
    --coral: #ef9b80;
    --mint: #69c8b7;
    --line: #e6e1df;
  }}

  * {{ box-sizing: border-box; }}

  html, body {{ margin: 0; padding: 0; }}

  body {{
    width: 920px;
    color: var(--ink);
    background: var(--canvas);
    font-family: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei",
      "PingFang SC", system-ui, sans-serif;
    font-size: 17px;
    line-height: 1.78;
    letter-spacing: 0;
  }}

  .report {{
    position: relative;
    overflow: hidden;
    min-height: 1200px;
    background: var(--paper);
  }}

  .hero {{
    position: relative;
    min-height: 390px;
    overflow: hidden;
    color: var(--ink);
    background: #eef6f7;
  }}

  .hero::before {{
    content: "";
    position: absolute;
    inset: 0;
    opacity: .35;
    background-image:
      linear-gradient(rgba(59,93,102,.10) 1px, transparent 1px),
      linear-gradient(90deg, rgba(59,93,102,.10) 1px, transparent 1px);
    background-size: 38px 38px;
  }}

  .hero::after {{
    content: "";
    position: absolute;
    left: -5%;
    right: -5%;
    bottom: -80px;
    height: 145px;
    background: var(--paper);
    border-radius: 50% 50% 0 0;
  }}

  .hero-copy {{
    position: relative;
    z-index: 3;
    width: 58%;
    padding: 48px 0 90px 62px;
  }}

  .brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 54px;
    color: #667178;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
  }}

  .brand-mark {{
    display: inline-grid;
    width: 34px;
    height: 34px;
    place-items: center;
    color: #26313a;
    background: var(--cyan);
    border: 3px solid #fff;
    border-radius: 9px;
    font-size: 16px;
  }}

  .eyebrow {{
    margin-bottom: 13px;
    color: #319bb3;
    font-size: 14px;
    font-weight: 800;
  }}

  h1 {{
    max-width: 520px;
    margin: 0;
    color: var(--ink);
    font-size: 43px;
    line-height: 1.24;
    font-weight: 850;
    overflow-wrap: anywhere;
  }}

  .hero-subtitle {{
    margin-top: 18px;
    color: #7a8087;
    font-size: 15px;
  }}

  .hero-art {{
    position: absolute;
    z-index: 2;
    top: 0;
    right: 0;
    width: 43%;
    height: 340px;
    overflow: hidden;
  }}

  .hero-art img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
  }}

  .mascot-stage {{
    position: absolute;
    inset: 20px 22px 0 0;
  }}

  .hero-pattern {{
    position: absolute;
    inset: 20px 22px 0 0;
  }}

  .mascot-panel {{
    position: absolute;
    top: 34px;
    right: 34px;
    width: 285px;
    height: 256px;
    background: #f8f5f4;
    border: 8px solid #dce9eb;
    border-radius: 48% 48% 28% 28%;
    transform: rotate(3deg);
  }}

  .antenna {{
    position: absolute;
    top: -38px;
    left: 126px;
    width: 16px;
    height: 54px;
    background: var(--cyan);
    border: 5px solid #343a46;
    border-radius: 12px;
  }}

  .antenna::after {{
    content: "";
    position: absolute;
    top: -19px;
    left: -9px;
    width: 24px;
    height: 24px;
    background: var(--pink);
    border: 5px solid #343a46;
    border-radius: 50%;
  }}

  .bot-face {{
    position: absolute;
    top: 62px;
    left: 42px;
    width: 185px;
    height: 126px;
    background: #dff6fa;
    border: 7px solid #343a46;
    border-radius: 46px;
  }}

  .bot-face::before,
  .bot-face::after {{
    content: "";
    position: absolute;
    top: 40px;
    width: 25px;
    height: 32px;
    background: #343a46;
    border-radius: 50%;
    box-shadow: inset 7px 5px 0 var(--cyan);
  }}

  .bot-face::before {{ left: 38px; }}
  .bot-face::after {{ right: 38px; box-shadow: inset -7px 5px 0 var(--pink); }}

  .bot-smile {{
    position: absolute;
    left: 111px;
    top: 151px;
    width: 48px;
    height: 23px;
    border-bottom: 6px solid #343a46;
    border-radius: 50%;
  }}

  .bot-ear {{
    position: absolute;
    top: 100px;
    width: 28px;
    height: 54px;
    background: var(--pink);
    border: 6px solid #343a46;
    border-radius: 15px;
  }}

  .bot-ear.left {{ left: 17px; }}
  .bot-ear.right {{ right: 17px; background: var(--cyan); }}

  .spark {{
    position: absolute;
    width: 26px;
    height: 26px;
    border: 7px solid var(--pink);
    transform: rotate(45deg);
  }}

  .spark.one {{ top: 24px; left: 14px; }}
  .spark.two {{ right: 5px; bottom: 45px; width: 18px; height: 18px; border-color: var(--cyan); }}

  .hero-pattern-library {{ transform: rotate(-4deg); }}

  .library-book {{
    position: absolute;
    width: 210px;
    height: 245px;
    border: 7px solid #343a46;
    border-radius: 14px 24px 24px 14px;
  }}

  .library-book-back {{ top: 46px; right: 72px; background: #f6c6d7; transform: rotate(11deg); }}
  .library-book-front {{ top: 36px; right: 102px; padding: 49px 31px; background: #e4f6f9; }}
  .library-book-front::before {{ content: ""; position: absolute; top: 0; bottom: 0; left: 42px; width: 6px; background: #343a46; }}
  .library-book-front span {{ display: block; height: 11px; margin: 16px 0 0 27px; background: #55bfd9; border-radius: 3px; }}
  .library-book-front span:nth-child(2) {{ width: 112px; background: #ef8eb1; }}
  .library-book-front span:nth-child(3) {{ width: 83px; background: #69c8b7; }}
  .library-lens {{ position: absolute; top: 210px; right: 22px; width: 93px; height: 93px; border: 10px solid #343a46; border-radius: 50%; background: rgba(255,255,255,.55); }}
  .library-lens::after {{ content: ""; position: absolute; width: 65px; height: 15px; right: -47px; bottom: -31px; background: #343a46; border-radius: 9px; transform: rotate(48deg); }}
  .library-lens i {{ position: absolute; width: 28px; height: 28px; top: 21px; left: 21px; border: 7px solid var(--pink); border-radius: 50%; }}
  .library-spark {{ position: absolute; width: 21px; height: 21px; border: 6px solid var(--cyan); transform: rotate(45deg); }}
  .library-spark-one {{ top: 18px; left: 42px; }}
  .library-spark-two {{ right: 16px; top: 52px; border-color: var(--pink); }}

  .hero-pattern-signal {{ transform: rotate(5deg); }}
  .signal-frame {{ position: absolute; top: 48px; right: 50px; width: 273px; height: 236px; border: 7px solid #343a46; border-radius: 28px; background: #f8fcfc; overflow: hidden; }}
  .signal-line {{ position: absolute; left: 28px; right: 28px; height: 10px; border-radius: 5px; background: #55bfd9; }}
  .line-one {{ top: 53px; right: 86px; }}
  .line-two {{ top: 105px; left: 73px; background: #ef8eb1; }}
  .line-three {{ top: 157px; right: 54px; background: #69c8b7; }}
  .signal-core {{ position: absolute; top: 94px; right: 133px; width: 94px; height: 94px; background: #fff0e9; border: 7px solid #343a46; border-radius: 50%; }}
  .signal-core span {{ position: absolute; inset: 22px; background: var(--coral); border-radius: 50%; }}
  .signal-card {{ position: absolute; width: 68px; height: 48px; border: 6px solid #343a46; border-radius: 11px; background: #e4f6f9; }}
  .card-one {{ top: 14px; right: 15px; transform: rotate(19deg); }}
  .card-two {{ bottom: 2px; left: 12px; background: #f6c6d7; transform: rotate(-17deg); }}

  .hero-pattern-notes {{ transform: rotate(4deg); }}
  .note-sheet {{ position: absolute; top: 35px; right: 77px; width: 237px; height: 270px; padding: 55px 33px; background: #fffaf7; border: 7px solid #343a46; border-radius: 19px; box-shadow: 22px 18px 0 #f7c8d8; }}
  .note-tab {{ position: absolute; top: -25px; left: 55px; width: 105px; height: 34px; background: #55bfd9; border: 7px solid #343a46; border-radius: 10px 10px 0 0; }}
  .note-sheet i {{ display: block; height: 12px; margin: 18px 0; background: #d8e8eb; border-radius: 5px; }}
  .note-sheet i:nth-of-type(2) {{ width: 78%; background: #f6c6d7; }}
  .note-sheet i:nth-of-type(3) {{ width: 91%; background: #d7f0ea; }}
  .note-pencil {{ position: absolute; right: 18px; bottom: 34px; width: 156px; height: 25px; background: var(--coral); border: 6px solid #343a46; border-radius: 9px; transform: rotate(-43deg); }}
  .note-pencil::before {{ content: ""; position: absolute; left: -30px; top: -6px; border-top: 13px solid transparent; border-bottom: 13px solid transparent; border-right: 30px solid #343a46; }}
  .note-check {{ position: absolute; width: 32px; height: 18px; border-left: 7px solid #69c8b7; border-bottom: 7px solid #69c8b7; transform: rotate(-45deg); }}
  .check-one {{ top: 72px; left: 14px; }}
  .check-two {{ top: 163px; left: 25px; border-color: #ef8eb1; }}

  .content {{
    position: relative;
    z-index: 4;
    padding: 0 62px 54px;
  }}

  .stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: -24px 0 32px;
  }}

  .stat {{
    min-height: 82px;
    padding: 15px 18px;
    background: #fff;
    border: 1px solid var(--line);
    border-top: 4px solid var(--cyan);
    border-radius: 8px;
  }}

  .stat:nth-child(2) {{ border-top-color: var(--pink); }}
  .stat:nth-child(3) {{ border-top-color: var(--coral); }}

  .stat-label {{
    display: block;
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
  }}

  .stat-value {{
    display: block;
    margin-top: 3px;
    color: var(--ink);
    font-size: 18px;
    font-weight: 800;
  }}

  .summary {{
    position: relative;
    margin: 0 0 38px;
    padding: 26px 30px 26px 35px;
    background: var(--cyan-soft);
    border-left: 7px solid var(--cyan);
    border-radius: 0 8px 8px 0;
  }}

  .summary::after {{
    content: "RESEARCH NOTE";
    position: absolute;
    top: 14px;
    right: 20px;
    color: rgba(51,54,61,.12);
    font-size: 12px;
    font-weight: 900;
  }}

  .summary-label {{
    display: block;
    margin-bottom: 8px;
    color: #248aa3;
    font-size: 14px;
    font-weight: 850;
  }}

  .summary p {{ margin: 0; font-size: 18px; line-height: 1.75; }}

  .article {{ counter-reset: section; }}

  .article h2 {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 46px 0 18px;
    color: var(--ink);
    font-size: 27px;
    line-height: 1.35;
    font-weight: 850;
    overflow-wrap: anywhere;
  }}

  .section-number {{
    flex: 0 0 auto;
    display: inline-grid;
    width: 46px;
    height: 38px;
    place-items: center;
    color: #fff;
    background: var(--pink);
    border-radius: 7px;
    font-size: 15px;
    font-weight: 900;
  }}

  .article h2:nth-of-type(even) .section-number {{ background: var(--cyan); }}

  .article h3 {{
    margin: 30px 0 12px;
    padding-left: 14px;
    color: #4c515a;
    border-left: 4px solid var(--mint);
    font-size: 20px;
    line-height: 1.45;
  }}

  .article p {{ margin: 0 0 18px; }}

  .article strong {{ color: #2e879b; font-weight: 850; }}

  .article ul,
  .article ol {{
    margin: 14px 0 24px;
    padding: 18px 24px 18px 46px;
    background: #faf8f7;
    border: 1px solid var(--line);
    border-radius: 8px;
  }}

  .article li {{ margin: 8px 0; padding-left: 4px; }}
  .article li::marker {{ color: var(--pink); font-weight: 800; }}

  .article blockquote {{
    margin: 24px 0;
    padding: 20px 24px;
    color: #4f5860;
    background: var(--pink-soft);
    border-left: 6px solid var(--pink);
    border-radius: 0 8px 8px 0;
  }}

  .article blockquote p:last-child {{ margin-bottom: 0; }}

  .article table {{
    width: 100%;
    margin: 22px 0 30px;
    border-collapse: collapse;
    overflow: hidden;
    color: #343a42;
    background: #edf3f5;
    border: 2px solid #ccd9dd;
    border-radius: 8px;
    font-size: 15px;
  }}

  .article th {{ color: #fff; background: #454d58; }}
  .article th, .article td {{
    padding: 13px 15px;
    border-right: 1px solid #d4dfe2;
    border-bottom: 1px solid #ccd9dd;
    text-align: left;
  }}
  .article th:last-child, .article td:last-child {{ border-right: 0; }}
  .article tbody tr:nth-child(odd) td {{ background: #edf5f7; }}
  .article tbody tr:nth-child(even) td {{ background: #f8edf2; }}
  .article tbody tr:last-child td {{ border-bottom: 0; }}

  .article pre {{
    margin: 22px 0;
    padding: 20px;
    overflow: hidden;
    color: #eaf7f9;
    background: #303640;
    border-left: 6px solid var(--cyan);
    border-radius: 7px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }}

  .article code {{
    padding: 2px 6px;
    color: #b94f77;
    background: var(--pink-soft);
    border-radius: 4px;
    font-family: Consolas, "SFMono-Regular", monospace;
    font-size: .9em;
  }}

  .article pre code {{ padding: 0; color: inherit; background: transparent; }}

  .flowchart-card {{
    margin: 28px 0 34px;
    overflow: hidden;
    background: #f5fafb;
    border: 2px solid #cbdde1;
    border-radius: 8px;
  }}

  .flowchart-heading {{
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 14px 18px;
    color: #3b454c;
    background: #e4f2f5;
    border-bottom: 1px solid #cbdde1;
  }}

  .flowchart-heading span {{
    display: inline-grid;
    min-width: 47px;
    height: 25px;
    place-items: center;
    color: #fff;
    background: var(--cyan);
    border-radius: 5px;
    font-size: 11px;
    font-weight: 900;
  }}

  .flowchart-heading strong {{ color: #354047; font-size: 15px; }}

  .flowchart-canvas {{
    padding: 18px;
    background: #f8fcfc;
  }}

  .flowchart-canvas svg {{
    display: block;
    width: 100%;
    height: auto;
    overflow: visible;
  }}

  .source-link {{
    display: inline-block;
    max-width: 100%;
    margin: 0 3px;
    padding: 1px 8px;
    color: #167e96;
    background: var(--cyan-soft);
    border: 1px solid #bfeaf2;
    border-radius: 5px;
    font-size: 13px;
    font-weight: 750;
    text-decoration: none;
    vertical-align: baseline;
    overflow-wrap: anywhere;
  }}

  .footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    margin-top: 54px;
    padding-top: 22px;
    color: var(--muted);
    border-top: 1px dashed #cfc9c6;
    font-size: 13px;
  }}

  .footer-brand {{ color: var(--ink); font-weight: 850; }}

  @media (max-width: 700px) {{
    body {{ width: 100vw; font-size: 16px; }}
    .hero {{ min-height: 460px; }}
    .hero-copy {{ width: 100%; padding: 34px 34px 170px; }}
    .brand {{ margin-bottom: 30px; }}
    h1 {{ font-size: 34px; }}
    .hero-art {{ top: auto; bottom: 35px; width: 48%; height: 190px; }}
    .mascot-stage {{ transform: scale(.62); transform-origin: right bottom; }}
    .content {{ padding: 0 28px 40px; }}
    .stats {{ grid-template-columns: 1fr; }}
    .article h2 {{ font-size: 23px; }}
  }}
</style>
</head>
<body>
<main class="report">
  <header class="hero">
    <div class="hero-copy">
      <div class="brand"><span class="brand-mark">A</span>AstrBot Deep Research</div>
      <div class="eyebrow">深度研究简报 · DEEP RESEARCH BRIEF</div>
      <h1>{report_title}</h1>
      <div class="hero-subtitle">从多源信息中提炼事实、观点与趋势</div>
    </div>
    <div class="hero-art">{hero_visual}</div>
  </header>

  <div class="content">
    <section class="stats">
      <div class="stat"><span class="stat-label">生成日期</span><span class="stat-value">{report_date}</span></div>
      <div class="stat"><span class="stat-label">外部来源</span><span class="stat-value">{source_count} 个</span></div>
      <div class="stat"><span class="stat-label">预计阅读</span><span class="stat-value">约 {reading_minutes} 分钟</span></div>
    </section>

    {summary_block}

    <article class="article">{article_body}</article>

    <footer class="footer">
      <span class="footer-brand">AstrBot Deep Research</span>
      <span>AI 生成内容 · 请结合原始来源核验</span>
    </footer>
  </div>
</main>
</body>
</html>"""


def build_report_html(markdown_content: str) -> str:
    """Turn report Markdown into a self-contained, image-friendly HTML document."""
    normalized = SOURCE_PATTERN.sub(lambda match: f"[来源]({match.group(1)})", markdown_content)
    html_body = markdown.markdown(
        normalized,
        extensions=["extra", "codehilite", "tables", "toc", "sane_lists"],
    )
    soup = BeautifulSoup(html_body, "lxml")
    root = soup.body or soup

    for code_block in list(root.find_all("code")):
        classes = set(code_block.get("class", []))
        if not classes.intersection({"language-mermaid", "mermaid"}):
            continue
        rendered_flowchart = render_mermaid_flowchart(code_block.get_text("\n"))
        if not rendered_flowchart:
            continue
        fragment = BeautifulSoup(rendered_flowchart, "html.parser").find("section")
        if fragment:
            container = code_block.parent if code_block.parent.name == "pre" else code_block
            container.replace_with(fragment)

    title_tag = root.find("h1")
    report_title = title_tag.get_text(" ", strip=True) if title_tag else "深度研究报告"
    if title_tag:
        title_tag.decompose()

    for index, heading in enumerate(root.find_all("h2"), start=1):
        badge = soup.new_tag("span")
        badge["class"] = "section-number"
        badge.string = f"{index:02d}"
        heading.insert(0, badge)

    source_urls = set()
    for link in root.find_all("a", href=True):
        href = link.get("href", "")
        if href.startswith(("http://", "https://")):
            source_urls.add(href)
            link["class"] = list(link.get("class", [])) + ["source-link"]
            link["target"] = "_blank"
            link["rel"] = "noopener noreferrer"

    first_paragraph = root.find("p")
    summary_block = ""
    if first_paragraph:
        summary_block = (
            '<section class="summary"><span class="summary-label">研究导读</span>'
            + str(first_paragraph)
            + "</section>"
        )
        first_paragraph.decompose()

    plain_text = root.get_text("", strip=True)
    reading_minutes = max(1, math.ceil(len(plain_text) / 420))
    safe_title = html.escape(report_title)

    return REPORT_TEMPLATE.format(
        page_title=safe_title,
        report_title=safe_title,
        report_date=datetime.now().strftime("%Y.%m.%d"),
        source_count=len(source_urls),
        reading_minutes=reading_minutes,
        summary_block=summary_block,
        article_body=root.decode_contents(),
        hero_visual=render_random_hero(),
    )


class ImageFormatter(BaseOutputFormatter):
    """Render a themed Markdown report to an image URL."""

    @property
    def format_name(self) -> str:
        return "image"

    @property
    def description(self) -> str:
        return "将Markdown报告渲染为图片"

    @property
    def file_extension(self) -> str:
        return ".png"

    async def format_report(
        self, markdown_content: str, star_instance: Star = None
    ) -> Optional[str]:
        if not self.validate_content(markdown_content):
            logger.warning("[ImageFormatter] Markdown内容为空")
            return None
        if not star_instance:
            logger.error("[ImageFormatter] 需要Star实例来调用html_render")
            return None

        try:
            image_url = await star_instance.html_render(
                build_report_html(markdown_content), {}, return_url=True
            )
            if image_url:
                logger.info("[ImageFormatter] 图片报告渲染成功")
                return image_url
            logger.warning("[ImageFormatter] 图片渲染失败，未返回URL")
            return None
        except Exception as exc:
            logger.error(f"[ImageFormatter] 渲染图片时发生错误: {exc}", exc_info=True)
            return None


class MarkdownFormatter(BaseOutputFormatter):
    """Return the original Markdown report."""

    @property
    def format_name(self) -> str:
        return "markdown"

    @property
    def description(self) -> str:
        return "原始Markdown格式文本"

    @property
    def file_extension(self) -> str:
        return ".md"

    async def format_report(
        self, markdown_content: str, star_instance: Star = None
    ) -> Optional[str]:
        if not self.validate_content(markdown_content):
            logger.warning("[MarkdownFormatter] Markdown内容为空")
            return None
        logger.info("[MarkdownFormatter] 返回原始Markdown文本")
        return markdown_content


class HTMLFormatter(BaseOutputFormatter):
    """Turn Markdown into a complete themed HTML report."""

    @property
    def format_name(self) -> str:
        return "html"

    @property
    def description(self) -> str:
        return "HTML格式报告"

    @property
    def file_extension(self) -> str:
        return ".html"

    async def format_report(
        self, markdown_content: str, star_instance: Star = None
    ) -> Optional[str]:
        if not self.validate_content(markdown_content):
            logger.warning("[HTMLFormatter] Markdown内容为空")
            return None
        try:
            result = build_report_html(markdown_content)
            logger.info("[HTMLFormatter] HTML报告生成成功")
            return result
        except Exception as exc:
            logger.error(f"[HTMLFormatter] 转换HTML时发生错误: {exc}", exc_info=True)
            return None
