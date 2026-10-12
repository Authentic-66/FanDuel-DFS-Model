"""Proportional stack allocation and green floor/boost modes (optimize)."""
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import optimize

OPT = dict(n_lineups=150, exposure_cap=25, yellow_factor=0.5, green_multiplier=2, green_floor=12,
           questionable_cap_pct=0.12)
DF = pd.DataFrame(dict(Name=['A', 'B', 'C'], Inj=['', '', '']))


def prefs(**kw):
    return dict(dict(yellow={}, green={'A': 1, 'B': 10}, player_cap={}), **kw)


class AllocationTest(unittest.TestCase):
    def test_counts_sum_and_follow_weights(self):
        counts = optimize.allocate_stacks({'X': 26, 'Y': 0, 'Z': 3, 'W': 1}, 150)
        self.assertEqual(sum(counts.values()), 150)
        self.assertEqual(counts, {'X': 130, 'Y': 0, 'Z': 15, 'W': 5})

    def test_largest_remainder_ties_go_to_first_listed(self):
        self.assertEqual(optimize.allocate_stacks({'X': 1, 'Y': 1, 'Z': 1}, 10), {'X': 4, 'Y': 3, 'Z': 3})

    def test_zero_weights_rejected(self):
        with self.assertRaises(ValueError):
            optimize.allocate_stacks({'X': 0}, 10)


class GreenModeTest(unittest.TestCase):
    def test_floor_mode_forces_minimums(self):
        _, need = optimize.exposure_limits(DF, prefs(), OPT)
        self.assertEqual(need, {0: 12, 1: 20})

    def test_per_player_floor(self):
        _, need = optimize.exposure_limits(DF, prefs(green_floor={'A': 5}), OPT)
        self.assertEqual(need, {0: 5, 1: 20})

    def test_boost_mode_forces_nothing(self):
        p = prefs(green_mode='boost', green_boost=0.3)
        self.assertEqual(optimize.exposure_limits(DF, p, OPT)[1], {})
        self.assertAlmostEqual(optimize.green_boost(p), 1.3)
        self.assertEqual(optimize.green_boost(prefs()), 1.0)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            optimize.green_boost(prefs(green_mode='more'))


if __name__ == '__main__':
    unittest.main()
