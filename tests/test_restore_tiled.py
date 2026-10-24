import unittest

from omarchy_last_session.restore import tiled
from tests.helpers import saved_window


def seat(name, x, y, width, height):
    return saved_window(name, at=(x, y), size=(width, height)), name


class DwindleGeometry(unittest.TestCase):
    def test_unequal_columns_keep_their_axis_and_proportion(self):
        tree = tiled.infer_tree([seat("left", 10, 10, 300, 780), seat("right", 330, 10, 660, 780)])
        self.assertEqual(tree.axis, "r")
        self.assertAlmostEqual(tree.ratio, 0.64)
        self.assertEqual(tree.first.address, "left")
        self.assertEqual(tree.second.address, "right")

    def test_nested_rows_and_columns_are_recovered_from_unordered_rectangles(self):
        tree = tiled.infer_tree(
            [
                seat("bottom", 420, 410, 570, 380),
                seat("left", 10, 10, 390, 780),
                seat("top", 420, 10, 570, 380),
            ]
        )
        self.assertEqual(tree.axis, "r")
        self.assertEqual(tree.first.address, "left")
        self.assertEqual(tree.second.axis, "d")
        self.assertEqual(tree.second.first.address, "top")
        self.assertEqual(tree.second.second.address, "bottom")

    def test_overlapping_rectangles_are_rejected_without_moving_any_window(self):
        self.assertIsNone(tiled.infer_tree([seat("a", 0, 0, 100, 100), seat("b", 50, 50, 100, 100)]))

    def test_single_window_needs_no_split(self):
        self.assertEqual(tiled.infer_tree([seat("a", 0, 0, 100, 100)]).address, "a")

    def test_reconstruction_keeps_tiles_tiled_and_resizes_after_building_splits(self):
        tree = tiled.infer_tree([seat("a", 10, 10, 300, 780), seat("b", 330, 10, 660, 780)])
        commands = tiled.build_commands(tree)
        self.assertIn("hl.dsp.layout('preselect r')", commands)
        self.assertIn("hl.dsp.layout('splitratio 0.640000 exact')", commands)
        self.assertLess(
            commands.index("action = 'off', window = 'address:b'"), commands.index("window.resize")
        )
        self.assertIn("x = 300, y = 780", commands)
        self.assertIn("x = 660, y = 780", commands)
