#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple IR drawing
"""
from .module import Module
from .node import Node, SUBNODE_NAMES
from .ast_.function import Function
import svgwrite
import math
import random

HEADER_FONT_SIZE = 12
PORT_FONT_SIZE = 8

NODE_STROKE_COLOR = "black"
NODE_FILL_COLOR = "#aaaaaa"
O_PORT_FILL_COLOR = "#aa9999"
I_PORT_FILL_COLOR = "#9999aa"
PORT_STROKE_COLOR = "grey"
ARROW_COLOR = "#222222"

PORT_HEIGHT = 20
PORT_TOP_MARGIN = 15 + HEADER_FONT_SIZE * 1.5  # offset to make node's label visible
PORT_MARGIN = 2

TEXT_HEIGHT = 15

HEIGHT_DIFFERENCE = (PORT_MARGIN + PORT_HEIGHT) * 2 + PORT_TOP_MARGIN

MINIMAL_NODE_WIDTH = 140
MINIMAL_NODE_HEIGHT = 5

SIDE_MARGIN = 20

WIDTH_DIFFERENCE = 0

FUNCTION_GAP = 10


def size_estimate(self: Node) -> (int, int):
    """size estimate for Node class"""
    if self.is_complex:  # contains various nodes
        level = []
        for o_p in self.out_ports:
            in_node = o_p.input_node
            if not in_node in level and self != in_node:
                level.append(in_node)
        self.levels = [level]
        while level:
            level = []
            for node in self.levels[-1]:
                if hasattr(node, "in_ports"):
                    for o_p in node.in_ports:
                        in_node = o_p.input_node
                        if in_node:
                            if not in_node in level and self != in_node:
                                level.append(in_node)
            if level:
                self.levels.append(level)

        self.sizes = [[node.size_estimate() for node in level] for level in self.levels]

        side_x = (
            max(
                [
                    sum([size[0] for size in level]) + SIDE_MARGIN * (len(level))
                    for level in self.sizes
                ]
            )
            + SIDE_MARGIN
        )
        side_y = sum(
            [max([size[1] for size in level]) if level else 0 for level in self.sizes]
        ) + SIDE_MARGIN * (len(self.sizes) + 1)
    elif self.is_multi:  # if, let, loop
        # put them in a row for now
        clusters = self.get_clusters()
        sizes = [cl.size_estimate() for cl in clusters]
        side_x = sum(size[0] + SIDE_MARGIN for size in sizes) + SIDE_MARGIN
        side_y = max(size[1] for size in sizes) + SIDE_MARGIN * 2
    else:  # basic
        side_x = MINIMAL_NODE_WIDTH
        side_y = MINIMAL_NODE_HEIGHT
    return side_x, side_y + HEIGHT_DIFFERENCE


Node.size_estimate = size_estimate


def draw_ports(dwg, ports, color, width, hor_offset, origin_height):
    port_width = int((width - PORT_MARGIN * 2) / len(ports))
    for n, port in enumerate(ports):
        x = hor_offset + n * port_width + PORT_MARGIN
        y = origin_height
        dwg.add(
            svgwrite.shapes.Rect(
                insert=(x, y),
                size=(port_width, PORT_HEIGHT),
                fill=color,
                stroke=PORT_STROKE_COLOR,
            )
        )
        port.coords = (x + port_width / 2, y + PORT_HEIGHT / 2)
        if port.label:
            dwg.add(
                svgwrite.text.Text(
                    port.label,
                    insert=(x, y),
                    dy=[TEXT_HEIGHT],
                    style=f"font-size:{PORT_FONT_SIZE}px;",
                )
            )


def get_internal_area(insert, size):
    """returns insert and size of node's internal area,
    where it's internal nodes are drawn"""
    insert = (
        insert[0],
        insert[1] + PORT_MARGIN + PORT_TOP_MARGIN + PORT_HEIGHT,
    )
    size = (size[0], size[1] - HEIGHT_DIFFERENCE)
    return insert, size


def draw_simple_internal_nodes(self, dwg, area_insert, area_size):
    v_offset = 0
    left = area_insert[0] + SIDE_MARGIN  # X of parent node internal area
    bottom = area_insert[1] + area_size[1]  # Y of parent node internal area

    for Y, level in enumerate(self.levels):
        level_height = max([size[1] for size in self.sizes[Y]]) if self.sizes[Y] else MINIMAL_NODE_HEIGHT
        level_width = sum([size[0] for size in self.sizes[Y]])
        h_offset = 0  # area_size[0] / 2 - level_width / 2
        v_offset += level_height + SIDE_MARGIN
        for X, node in enumerate(level):
            size = self.sizes[Y][X]
            node.draw_node(dwg, (left + h_offset, bottom - v_offset), size)
            h_offset += size[0] + SIDE_MARGIN


def draw_multi_internal_nodes(self, dwg, area_insert, area_size):
    h_offset = SIDE_MARGIN
    for cl in self.get_clusters():
        cl_size = cl.size_estimate()
        x = area_insert[0] + h_offset
        y = area_insert[1] + SIDE_MARGIN
        cl.draw_node(dwg, (x, y), cl_size)
        h_offset += cl_size[0] + SIDE_MARGIN


COLOR_VARIATION = 8
FADE_COLOR = 15


def rand_channel():
    return (
        100
        - COLOR_VARIATION
        - FADE_COLOR
        + random.randrange(-COLOR_VARIATION, COLOR_VARIATION)
    )


def rand_color():
    return svgwrite.rgb(rand_channel(), rand_channel(), rand_channel(), "%")


ATTRIBUTES = ["value", "callee", "operator"]


def attributes(node):
    attr_strs = [
        f"{attr}: {node.__dict__[attr]}" for attr in ATTRIBUTES if hasattr(node, attr)
    ]
    return "; ".join(attr_strs)


def draw_node(self, dwg: svgwrite.drawing, insert, size):
    """generic method for all types of nodes"""
    if not hasattr(self, "is_drawn"):
        self.is_drawn = True
    else:
        return
    dwg.add(
        svgwrite.shapes.Rect(
            insert=insert, size=size, stroke=NODE_STROKE_COLOR, fill=rand_color()
        )
    )
    label = self.function_name if hasattr(self, "function_name") else self.name
    label += f" ({self.id})"
    dwg.add(
        svgwrite.text.Text(
            label, insert=insert, dy=[15], style=f"font-size:{HEADER_FONT_SIZE}px;"
        )
    )
    dwg.add(
        svgwrite.text.Text(
            attributes(self),
            insert=insert,
            dy=[HEADER_FONT_SIZE + 15],
            style=f"font-size:{HEADER_FONT_SIZE}px;",
        )
    )

    if self.out_ports:
        draw_ports(
            dwg,
            self.out_ports,
            O_PORT_FILL_COLOR,
            size[0],
            insert[0],
            origin_height=insert[1] + size[1] - PORT_HEIGHT - PORT_MARGIN,
        )
    if hasattr(self, "in_ports") and self.in_ports:
        draw_ports(
            dwg,
            self.in_ports,
            I_PORT_FILL_COLOR,
            size[0],
            insert[0],
            origin_height=insert[1] + PORT_MARGIN + PORT_TOP_MARGIN,
        )

    area_insert, area_size = get_internal_area(insert, size)
    """
    dwg.add(
        svgwrite.shapes.Rect(
            insert=area_insert, size=area_size, stroke=NODE_STROKE_COLOR, fill="red"
        )
    )
    """
    if hasattr(self, "nodes"):
        draw_simple_internal_nodes(self, dwg, area_insert, area_size)
    elif self.is_multi:  # if, let, or loop
        draw_multi_internal_nodes(self, dwg, area_insert, area_size)


Node.draw_node = draw_node


def draw_edges(module, dwg, marker):
    for edge in module.edges:
        x1, y1 = edge.from_.coords
        x2, y2 = edge.to.coords

        if not edge.from_.node == edge.to.node:
            if not edge.from_.in_port and not edge.to.in_port:
                y1 += PORT_HEIGHT / 2
                y2 -= PORT_HEIGHT / 2
            else:
                y1 += PORT_HEIGHT / 2
                y2 -= PORT_HEIGHT / 2

        line = dwg.add(
            svgwrite.shapes.Line(
                start=(x1, y1), end=(x2, y2), stroke=ARROW_COLOR, fill="none"
            )
        )

        line.set_markers((None, False, marker))


def draw_module(module_to_draw):
    sizes = []

    for name, node in module_to_draw.functions.items():
        sizes.append(node.size_estimate())

    image_width = max([size[0] for size in sizes])
    image_height = sum([size[1] + FUNCTION_GAP for size in sizes]) - FUNCTION_GAP

    dwg = svgwrite.Drawing("IR", size=(image_width, image_height))
    marker = dwg.marker(
        insert=(0, 0), size=(15, 15), orient="auto", viewBox="-5 -5 10 10"
    )

    marker.add(dwg.polygon([(5, 0), (0, 2), (0, -2)], fill=ARROW_COLOR))

    dwg.defs.add(marker)

    v_offset = 0
    for index, (name, node) in enumerate(module_to_draw.functions.items()):
        node.draw_node(dwg, insert=(0, v_offset), size=sizes[index])
        v_offset += sizes[index][1] + FUNCTION_GAP

    draw_edges(module_to_draw, dwg, marker)

    print(dwg.tostring())


def draw_graph(ir_data):
    module_to_draw = Module()
    module_to_draw.load_from_json_data(ir_data)
    draw_module(module_to_draw)
