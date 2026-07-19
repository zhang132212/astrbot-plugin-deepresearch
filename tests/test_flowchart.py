import html
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "output_format" / "flowchart.py"
SPEC = importlib.util.spec_from_file_location("deepresearch_flowchart", MODULE_PATH)
flowchart = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = flowchart
SPEC.loader.exec_module(flowchart)


class FlowchartTests(unittest.TestCase):
    def test_parses_nodes_edges_shapes_and_labels(self):
        chart = flowchart.parse_mermaid_flowchart(
            """flowchart TD
            A[接收问题] --> B{需要搜索?}
            B -->|是| C([多源检索])
            B -->|否| D[直接总结]
            C --> E[生成报告]
            D --> E
            """
        )

        self.assertIsNotNone(chart)
        self.assertEqual(chart.direction, "TD")
        self.assertEqual(chart.nodes["B"].shape, "decision")
        self.assertEqual(chart.nodes["C"].shape, "pill")
        self.assertEqual(chart.edges[1].label, "是")

    def test_renders_safe_inline_svg(self):
        source = """flowchart LR
        A[输入<script>] --> B[输出]
        """
        rendered = flowchart.render_mermaid_flowchart(source)

        self.assertIn("<svg", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn(html.escape("输入<script>"), rendered)

    def test_rejects_unsupported_or_empty_graphs(self):
        self.assertIsNone(flowchart.render_mermaid_flowchart("sequenceDiagram\nA->>B: Hi"))
        self.assertIsNone(flowchart.render_mermaid_flowchart("flowchart TD\nA[只有一个节点]"))

    def test_long_horizontal_graph_uses_readable_vertical_layout(self):
        rendered = flowchart.render_mermaid_flowchart(
            "flowchart LR\nA --> B\nB --> C\nC --> D\nD --> E\nE --> F"
        )
        viewbox = rendered.split('viewBox="', 1)[1].split('"', 1)[0]
        _, _, width, height = [float(value) for value in viewbox.split()]
        self.assertGreater(height, width)


if __name__ == "__main__":
    unittest.main()
