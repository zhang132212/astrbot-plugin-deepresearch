"""Generate a standalone browser preview for the report theme."""

import ast
import argparse
import html
import importlib.util
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
FORMATTERS_PATH = PROJECT_DIR / "output_format" / "formatters.py"
FLOWCHART_PATH = PROJECT_DIR / "output_format" / "flowchart.py"
HERO_PATTERNS_PATH = PROJECT_DIR / "output_format" / "hero_patterns.py"

FLOWCHART_SPEC = importlib.util.spec_from_file_location("preview_flowchart", FLOWCHART_PATH)
flowchart = importlib.util.module_from_spec(FLOWCHART_SPEC)
sys.modules[FLOWCHART_SPEC.name] = flowchart
FLOWCHART_SPEC.loader.exec_module(flowchart)

HERO_PATTERNS_SPEC = importlib.util.spec_from_file_location("preview_hero_patterns", HERO_PATTERNS_PATH)
hero_patterns = importlib.util.module_from_spec(HERO_PATTERNS_SPEC)
sys.modules[HERO_PATTERNS_SPEC.name] = hero_patterns
HERO_PATTERNS_SPEC.loader.exec_module(hero_patterns)


def _read_string_constant(name: str) -> str:
    tree = ast.parse(FORMATTERS_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError(f"Could not find string constant: {name}")


SAMPLE_ARTICLE = """
<h2><span class="section-number">01</span>技术演进与核心能力</h2>
<p>现代智能体通常由 <strong>语言模型、工具系统、记忆与执行循环</strong> 构成。模型负责理解目标与规划，外部工具负责获取实时信息或执行具体操作。</p>
<ul>
  <li>任务规划从单轮指令发展为多步骤工作流。</li>
  <li>工具调用让模型能够连接搜索、代码、数据库与业务系统。</li>
  <li>记忆机制帮助系统在较长任务中保持上下文一致。</li>
</ul>
<blockquote><p>真正决定智能体价值的不是回复是否流畅，而是任务能否可靠完成并被验证。</p></blockquote>

<!-- FLOWCHART -->

<h2><span class="section-number">02</span>典型应用场景</h2>
<table>
  <thead><tr><th>场景</th><th>主要价值</th><th>落地难点</th></tr></thead>
  <tbody>
    <tr><td>研究分析</td><td>汇总多来源信息</td><td>来源质量与引用核验</td></tr>
    <tr><td>软件开发</td><td>修改文件并运行测试</td><td>权限与变更边界</td></tr>
    <tr><td>客服运营</td><td>分类问题并调用业务系统</td><td>隐私与交接机制</td></tr>
  </tbody>
</table>
<p>智能体更适合作为可审查的执行者，而不是完全脱离监督的自动决策者。<a class="source-link" href="https://example.org/agents">来源</a></p>

<h2><span class="section-number">03</span>风险与治理</h2>
<ol>
  <li><strong>事实错误：</strong>重要结论必须关联可访问的原始来源。</li>
  <li><strong>权限扩张：</strong>工具权限应遵循最小授权原则。</li>
  <li><strong>成本失控：</strong>限制搜索次数、并发量与模型调用次数。</li>
  <li><strong>过程不可见：</strong>保留关键步骤、失败原因和最终依据。</li>
</ol>
<pre><code>result = await agent.run(task)
assert result.sources
assert result.verified</code></pre>

<h2><span class="section-number">04</span>实施建议与结论</h2>
<p>建议先选择边界清晰、结果容易验证的任务进行试点，再逐步扩展工具权限与自动化程度。每个工作流都应设置超时、重试、人工确认和回滚机制。</p>
<p>智能体的竞争重点将从“模型能说什么”转向“系统能稳定完成什么”。具备可靠工具链、质量评估和权限治理的产品，更容易形成持续价值。</p>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero-index", type=int, default=0)
    args = parser.parse_args()

    template = _read_string_constant("REPORT_TEMPLATE")
    title = "人工智能智能体的发展趋势与实际应用"
    flowchart_html = flowchart.render_mermaid_flowchart(
        """flowchart LR
        A([接收研究问题]) --> B[拆解与扩展查询]
        B --> C[多引擎检索]
        C --> D{来源可用?}
        D -->|是| E[抓取并总结]
        D -->|否| F[回退至模型知识]
        E --> G([聚合生成报告])
        F --> G
        """
    )
    summary = """<section class="summary"><span class="summary-label">研究导读</span><p>智能体正在从单一问答工具转向能够规划、调用工具并持续执行任务的协作系统。本报告梳理其技术基础、应用价值与落地风险。</p></section>"""
    output = template.format(
        page_title=html.escape(title),
        report_title=html.escape(title),
        report_date=datetime.now().strftime("%Y.%m.%d"),
        source_count=2,
        reading_minutes=4,
        summary_block=summary,
        article_body=SAMPLE_ARTICLE.replace("<!-- FLOWCHART -->", flowchart_html or ""),
        hero_visual=hero_patterns.BUILTIN_HEROES[
            args.hero_index % len(hero_patterns.BUILTIN_HEROES)
        ],
    )

    output_dir = PROJECT_DIR / "preview"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"report_theme_preview_{args.hero_index % len(hero_patterns.BUILTIN_HEROES)}.html"
    output_path.write_text(output, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
