"""Render a safe, useful subset of Mermaid flowcharts as inline SVG."""

from __future__ import annotations

import html
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


HEADER_PATTERN = re.compile(r"^(?:flowchart|graph)\s+(TD|TB|BT|LR|RL)\s*$", re.I)
NODE_ID_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)")


@dataclass
class FlowNode:
    node_id: str
    label: str
    shape: str = "rounded"


@dataclass
class FlowEdge:
    source: str
    target: str
    label: str = ""


@dataclass
class Flowchart:
    direction: str
    nodes: Dict[str, FlowNode] = field(default_factory=dict)
    edges: List[FlowEdge] = field(default_factory=list)


def _clean_label(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def _parse_node_token(text: str) -> Tuple[Optional[FlowNode], str]:
    text = text.lstrip()
    match = NODE_ID_PATTERN.match(text)
    if not match:
        return None, text

    node_id = match.group(1)
    rest = text[match.end() :].lstrip()
    label = node_id
    shape = "rounded"

    delimiters = (
        ("([", "])", "pill"),
        ("[", "]", "rounded"),
        ("{", "}", "decision"),
        ("(", ")", "pill"),
    )
    for opening, closing, candidate_shape in delimiters:
        if not rest.startswith(opening):
            continue
        end = rest.find(closing, len(opening))
        if end == -1:
            return None, text
        label = _clean_label(rest[len(opening) : end]) or node_id
        shape = candidate_shape
        rest = rest[end + len(closing) :].lstrip()
        break

    return FlowNode(node_id=node_id, label=label, shape=shape), rest


def _add_node(chart: Flowchart, node: FlowNode) -> None:
    existing = chart.nodes.get(node.node_id)
    if existing and node.label == node.node_id and node.shape == "rounded":
        return
    chart.nodes[node.node_id] = node


def _parse_statement(chart: Flowchart, statement: str) -> None:
    source, rest = _parse_node_token(statement)
    if not source:
        return

    if not rest:
        _add_node(chart, source)
        return

    edge_label = ""
    edge_match = re.match(r"^(?:-->|==>|---)\s*(?:\|([^|]+)\|\s*)?", rest)
    if edge_match:
        edge_label = _clean_label(edge_match.group(1) or "")
        rest = rest[edge_match.end() :]
    else:
        labelled_match = re.match(r"^--\s*(.+?)\s*-->\s*", rest)
        if not labelled_match:
            _add_node(chart, source)
            return
        edge_label = _clean_label(labelled_match.group(1))
        rest = rest[labelled_match.end() :]

    target, trailing = _parse_node_token(rest)
    if not target or trailing.strip():
        return

    _add_node(chart, source)
    _add_node(chart, target)
    chart.edges.append(FlowEdge(source.node_id, target.node_id, edge_label))


def parse_mermaid_flowchart(source: str) -> Optional[Flowchart]:
    """Parse simple Mermaid nodes and directed edges into a graph model."""
    lines = [line.strip() for line in source.splitlines()]
    lines = [line for line in lines if line and not line.startswith("%%")]
    if not lines:
        return None

    header = HEADER_PATTERN.match(lines[0])
    if not header:
        return None

    direction = header.group(1).upper().replace("TB", "TD")
    chart = Flowchart(direction=direction)
    for line in lines[1:]:
        if line.lower().startswith(("subgraph", "end", "classdef", "class ", "style ")):
            continue
        for statement in line.split(";"):
            if statement.strip():
                _parse_statement(chart, statement.strip())

    if len(chart.nodes) < 2 or not chart.edges:
        return None
    return chart


def _node_ranks(chart: Flowchart) -> Dict[str, int]:
    outgoing: Dict[str, List[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in chart.nodes}
    for edge in chart.edges:
        outgoing[edge.source].append(edge.target)
        indegree[edge.target] = indegree.get(edge.target, 0) + 1

    queue = deque(node_id for node_id in chart.nodes if indegree.get(node_id, 0) == 0)
    ranks = {node_id: 0 for node_id in chart.nodes}
    visited = set()
    while queue:
        node_id = queue.popleft()
        visited.add(node_id)
        for target in outgoing[node_id]:
            ranks[target] = max(ranks[target], ranks[node_id] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    fallback_rank = max(ranks.values(), default=0)
    for node_id in chart.nodes:
        if node_id not in visited:
            fallback_rank += 1
            ranks[node_id] = fallback_rank
    return ranks


def _wrap_label(label: str, limit: int = 13) -> List[str]:
    if len(label) <= limit:
        return [label]

    words = label.split()
    if len(words) > 1:
        lines: List[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > limit:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines[:3]

    return [label[index : index + limit] for index in range(0, len(label), limit)][:3]


def _layout(chart: Flowchart):
    ranks = _node_ranks(chart)
    levels: Dict[int, List[str]] = defaultdict(list)
    for node_id in chart.nodes:
        levels[ranks[node_id]].append(node_id)

    ordered_levels = [levels[index] for index in sorted(levels)]
    node_width = 186
    node_height = 76
    positions = {}

    if chart.direction in {"TD", "BT"}:
        gap_x, gap_y, padding = 42, 78, 48
        max_count = max(len(level) for level in ordered_levels)
        width = max(720, padding * 2 + max_count * node_width + (max_count - 1) * gap_x)
        height = padding * 2 + len(ordered_levels) * node_height + (len(ordered_levels) - 1) * gap_y
        visual_levels = list(reversed(ordered_levels)) if chart.direction == "BT" else ordered_levels
        for level_index, level in enumerate(visual_levels):
            total_width = len(level) * node_width + (len(level) - 1) * gap_x
            start_x = (width - total_width) / 2
            y = padding + level_index * (node_height + gap_y)
            for item_index, node_id in enumerate(level):
                positions[node_id] = (start_x + item_index * (node_width + gap_x), y, node_width, node_height)
    else:
        gap_x, gap_y, padding = 88, 36, 48
        max_count = max(len(level) for level in ordered_levels)
        width = padding * 2 + len(ordered_levels) * node_width + (len(ordered_levels) - 1) * gap_x
        height = max(360, padding * 2 + max_count * node_height + (max_count - 1) * gap_y)
        visual_levels = list(reversed(ordered_levels)) if chart.direction == "RL" else ordered_levels
        for level_index, level in enumerate(visual_levels):
            total_height = len(level) * node_height + (len(level) - 1) * gap_y
            start_y = (height - total_height) / 2
            x = padding + level_index * (node_width + gap_x)
            for item_index, node_id in enumerate(level):
                positions[node_id] = (x, start_y + item_index * (node_height + gap_y), node_width, node_height)

    return width, height, positions


def _edge_svg(edge: FlowEdge, positions, direction: str) -> str:
    sx, sy, sw, sh = positions[edge.source]
    tx, ty, tw, th = positions[edge.target]

    if direction == "TD":
        start, end = (sx + sw / 2, sy + sh), (tx + tw / 2, ty)
        middle = (start[1] + end[1]) / 2
        path = f"M {start[0]:.1f} {start[1]:.1f} C {start[0]:.1f} {middle:.1f}, {end[0]:.1f} {middle:.1f}, {end[0]:.1f} {end[1]:.1f}"
    elif direction == "BT":
        start, end = (sx + sw / 2, sy), (tx + tw / 2, ty + th)
        middle = (start[1] + end[1]) / 2
        path = f"M {start[0]:.1f} {start[1]:.1f} C {start[0]:.1f} {middle:.1f}, {end[0]:.1f} {middle:.1f}, {end[0]:.1f} {end[1]:.1f}"
    elif direction == "LR":
        start, end = (sx + sw, sy + sh / 2), (tx, ty + th / 2)
        middle = (start[0] + end[0]) / 2
        path = f"M {start[0]:.1f} {start[1]:.1f} C {middle:.1f} {start[1]:.1f}, {middle:.1f} {end[1]:.1f}, {end[0]:.1f} {end[1]:.1f}"
    else:
        start, end = (sx, sy + sh / 2), (tx + tw, ty + th / 2)
        middle = (start[0] + end[0]) / 2
        path = f"M {start[0]:.1f} {start[1]:.1f} C {middle:.1f} {start[1]:.1f}, {middle:.1f} {end[1]:.1f}, {end[0]:.1f} {end[1]:.1f}"

    output = [f'<path d="{path}" fill="none" stroke="#718087" stroke-width="2.4" marker-end="url(#flow-arrow)"/>']
    if edge.label:
        label_x = (start[0] + end[0]) / 2
        label_y = (start[1] + end[1]) / 2 - 7
        output.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            'font-size="12" font-weight="700" fill="#5b6870" stroke="#f6fbfc" '
            f'stroke-width="5" paint-order="stroke">{html.escape(edge.label)}</text>'
        )
    return "".join(output)


def _node_svg(node: FlowNode, position, index: int) -> str:
    x, y, width, height = position
    palettes = (
        ("#e3f5f8", "#43b5cf"),
        ("#fae9f0", "#e980a7"),
        ("#fff0e9", "#e99578"),
        ("#e8f5f1", "#61baa9"),
    )
    fill, stroke = palettes[index % len(palettes)]
    center_x, center_y = x + width / 2, y + height / 2

    if node.shape == "decision":
        points = f"{center_x:.1f},{y:.1f} {x + width:.1f},{center_y:.1f} {center_x:.1f},{y + height:.1f} {x:.1f},{center_y:.1f}"
        shape = f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
    else:
        radius = height / 2 if node.shape == "pill" else 12
        shape = f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" rx="{radius:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'

    lines = _wrap_label(node.label, 11 if node.shape == "decision" else 14)
    line_height = 19
    first_y = center_y - ((len(lines) - 1) * line_height) / 2 + 5
    tspans = "".join(
        f'<tspan x="{center_x:.1f}" y="{first_y + line_index * line_height:.1f}">{html.escape(line)}</tspan>'
        for line_index, line in enumerate(lines)
    )
    text = f'<text text-anchor="middle" font-size="15" font-weight="750" fill="#303840">{tspans}</text>'
    return f'<g class="flow-node">{shape}{text}</g>'


def render_mermaid_flowchart(source: str) -> Optional[str]:
    """Return a self-contained HTML/SVG flowchart, or None for unsupported input."""
    chart = parse_mermaid_flowchart(source)
    if not chart:
        return None

    ranks = _node_ranks(chart)
    level_count = max(ranks.values(), default=0) + 1
    if chart.direction in {"LR", "RL"} and level_count > 4:
        chart.direction = "TD" if chart.direction == "LR" else "BT"

    width, height, positions = _layout(chart)
    edge_markup = "".join(_edge_svg(edge, positions, chart.direction) for edge in chart.edges)
    node_markup = "".join(
        _node_svg(node, positions[node.node_id], index)
        for index, node in enumerate(chart.nodes.values())
    )
    svg = f"""<svg viewBox="0 0 {width} {height}" role="img" aria-label="研究流程图" xmlns="http://www.w3.org/2000/svg">
      <defs><marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#718087"/></marker></defs>
      {edge_markup}{node_markup}
    </svg>"""
    return f"""<section class="flowchart-card">
      <div class="flowchart-heading"><span>FLOW</span><strong>研究流程</strong></div>
      <div class="flowchart-canvas">{svg}</div>
    </section>"""
