"""Render a Minecraft comparator report preview with the plugin's report theme."""

import ast
import html
import importlib.util
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
FORMATTERS_PATH = PROJECT_DIR / "output_format" / "formatters.py"
FLOWCHART_PATH = PROJECT_DIR / "output_format" / "flowchart.py"
HERO_PATTERNS_PATH = PROJECT_DIR / "output_format" / "hero_patterns.py"


def _read_string_constant(name: str) -> str:
    tree = ast.parse(FORMATTERS_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError(f"Could not find string constant: {name}")


def _load_flowchart_module():
    spec = importlib.util.spec_from_file_location("comparator_flowchart", FLOWCHART_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_hero_patterns_module():
    spec = importlib.util.spec_from_file_location("comparator_hero_patterns", HERO_PATTERNS_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    template = _read_string_constant("REPORT_TEMPLATE")
    flowchart = _load_flowchart_module()
    hero_patterns = _load_hero_patterns_module()

    flowchart_html = flowchart.render_mermaid_flowchart(
        """flowchart TD
        A([后方输入信号 R]) --> B[读取侧向最强信号 S]
        B --> C{减法模式?}
        C -->|否| D{R 是否大于等于 S?}
        D -->|是| E([输出 R])
        D -->|否| F([输出 0])
        C -->|是| G([输出 max(R - S, 0)])
        """
    )

    article = f"""
<h2><span class="section-number">01</span>它到底在比较什么</h2>
<p>红石比较器会读取<strong>后方输入</strong>的信号强度，并同时读取左右两侧中较强的一路信号。红石信号强度范围都是 <strong>0 到 15</strong>；比较器不会把两侧信号继续向前传递，它们只参与判断。</p>
<table>
  <thead><tr><th>输入位置</th><th>作用</th><th>参与方式</th></tr></thead>
  <tbody>
    <tr><td>后方</td><td>主输入 R</td><td>决定可输出的基础强度</td></tr>
    <tr><td>左右两侧</td><td>侧向输入 S</td><td>取两侧中较高的强度作为阈值</td></tr>
    <tr><td>前方</td><td>输出</td><td>输出比较或相减后的最终强度</td></tr>
  </tbody>
</table>

<h2><span class="section-number">02</span>比较模式与减法模式</h2>
<p>默认的<strong>比较模式</strong>适合做信号门：只有当后方输入不小于侧向最强信号时，才原样输出后方强度。右键切换后，前方小红石火把点亮，进入<strong>减法模式</strong>。</p>
<ul>
  <li><strong>比较模式：</strong>若 R ≥ S，输出 R；否则输出 0。</li>
  <li><strong>减法模式：</strong>输出 max(R - S, 0)。</li>
  <li><strong>延迟：</strong>两种模式的输出延迟都是 1 个红石刻，也就是 2 个游戏刻。</li>
</ul>
{flowchart_html}

<h2><span class="section-number">03</span>为什么它能读取容器状态</h2>
<p>比较器还能读取许多方块保存的状态，并将其转换为 0 到 15 的红石信号。例如箱子、漏斗、熔炉、投掷器等容器会按填充程度给出信号；讲台、物品展示框、唱片机等特殊方块也能提供各自的状态信号。</p>
<blockquote><p>比较器读取的是“方块状态转换后的强度”，不是直接识别物品名称。因此它非常适合做库存检测、分类机、音乐机和物品展示框密码锁。</p></blockquote>

<h2><span class="section-number">04</span>常见电路用途</h2>
<ol>
  <li><strong>库存检测：</strong>根据容器填充度，触发补货、报警或熔炉阵列。</li>
  <li><strong>信号筛选：</strong>用比较模式拦截低于阈值的红石信号。</li>
  <li><strong>数值运算：</strong>用减法模式扣除侧向强度，制作计数和优先级电路。</li>
  <li><strong>状态读取：</strong>把展示框旋转角度、唱片机状态等转为可用信号。</li>
</ol>

<h2><span class="section-number">05</span>快速记忆</h2>
<p>把比较器理解成一个带两种算法的信号处理器即可：默认模式负责“<strong>够不够</strong>”，减法模式负责“<strong>还剩多少</strong>”。后方提供主数值，侧面提供阈值或扣减量，前方给出最终结果。</p>
<p>机制参考：<a class="source-link" href="https://minecraft.wiki/w/Redstone_Comparator">Minecraft Wiki · Redstone Comparator</a></p>
"""

    summary = """<section class="summary"><span class="summary-label">研究导读</span><p>Minecraft 红石比较器用于读取、比较和扣减 0 到 15 的红石信号。掌握后方主输入与两侧阈值的关系，就能理解它在库存检测、密码锁和数值电路中的作用。</p></section>"""
    title = "Minecraft 红石比较器：功能、模式与工作原理"
    report = template.format(
        page_title=html.escape(title),
        report_title=html.escape(title),
        report_date=datetime.now().strftime("%Y.%m.%d"),
        source_count=1,
        reading_minutes=4,
        summary_block=summary,
        article_body=article,
        hero_visual=hero_patterns.BUILTIN_HEROES[0],
    )

    output_dir = PROJECT_DIR / "preview"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "minecraft_comparator_report.html"
    output_path.write_text(report, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
