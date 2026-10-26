import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageFont
from handright import Template
import handright._core as handright_core

from app import apply_right_align


def _draft_lines(text, template, seed=1):
    positioned_chars = []
    original_flow_layout = handright_core._flow_layout

    def record_flow_layout(draw, x, y, char, template, rand):
        positioned_chars.append((round(y), char))
        return original_flow_layout(draw, x, y, char, template, rand)

    with patch.object(handright_core, "_flow_layout", record_flow_layout):
        list(handright_core._draft(text, (template,), seed=seed))

    chars_by_line = defaultdict(list)
    for y, char in positioned_chars:
        chars_by_line[y].append(char)
    return ["".join(chars) for chars in chars_by_line.values()]


class TypographyTest(unittest.TestCase):
    def test_closing_punctuation_does_not_start_a_line(self):
        font_path = Path(__file__).parents[1] / "font_assets" / "李国夫手写体.ttf"
        template = Template(
            background=Image.new("RGB", (60, 120), "white"),
            font=ImageFont.truetype(str(font_path), 24),
            line_spacing=30,
            word_spacing=0,
            line_spacing_sigma=0,
            font_size_sigma=0,
            word_spacing_sigma=0,
            perturb_x_sigma=0,
            perturb_y_sigma=0,
            perturb_theta_sigma=0,
            ink_depth_sigma=0,
        )
        for punctuation in "，。！？；：、）》】’”":
            with self.subTest(punctuation=punctuation):
                self.assertEqual(
                    _draft_lines(f"丁。{punctuation}后文", template),
                    [f"丁。{punctuation}", "后文"],
                )

    def test_right_aligned_letter_ending_stays_on_three_lines(self):
        font_path = Path(__file__).parents[1] / "font_assets" / "云烟体.ttf"
        template = Template(
            background=Image.new("RGB", (2481, 500), "white"),
            font=ImageFont.truetype(str(font_path), 70),
            line_spacing=100,
            left_margin=150,
            top_margin=20,
            right_margin=146,
            bottom_margin=20,
            word_spacing=2,
            line_spacing_sigma=1,
            font_size_sigma=1,
            word_spacing_sigma=2,
            perturb_x_sigma=1,
            perturb_y_sigma=1,
            perturb_theta_sigma=0.05,
            ink_depth_sigma=30,
        )
        ending = "\n".join(
            [
                ">>>爱你的儿子",
                ">>>佳佳",
                ">>>2026 年 7 月 26 日",
            ]
        )

        aligned = apply_right_align(ending, template)
        lines = _draft_lines(aligned, template, seed=5)

        self.assertEqual(
            [line.lstrip("　") for line in lines],
            ["爱你的儿子", "佳佳", "2026 年 7 月 26 日"],
        )
