"""Week-9 changes (Doug, Nov 2; docs/week9_tests.md): position-scaled injury bump ([model.injury] bump_scale) and the
one-sided WR implied-total correction ([model.implied_sensitivity] one_sided)."""
import os
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import config, project, usage
from test_routing import ROUTING, setup


class BumpScaleTest(unittest.TestCase):
    def test_volume_scaled_by_the_out_players_position(self):
        agg, out, active, k = setup('Out WR')
        full_t, full_c = usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING)
        xt, xc = usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING, scale={'WR': 0.45, 'RB': 0.8})
        for key, v in full_t.items():
            self.assertAlmostEqual(xt[key], 0.45 * v)        # a WR is out: everything he hands out x 0.45
        for key, v in full_c.items():
            self.assertAlmostEqual(xc[key], 0.45 * v)

    def test_missing_position_and_none_mean_unscaled(self):
        agg, out, active, k = setup('Back One')
        base = usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING)
        self.assertEqual(usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING, scale=None), base)
        self.assertEqual(usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING, scale={'WR': 0.45}), base)

    def test_trades_are_not_scaled(self):
        # trade_volume has no scale argument: the old team's share is unchanged by bump_scale
        agg, out, active, k = setup('Out WR')
        moved = pd.DataFrame([dict(Key=k('Out WR'), Name='Out WR', Pos='WR', From='AAA', To='BBB', share=0.0, factor=1.0)])
        xt, _ = usage.trade_volume(agg, moved, active, 0.8, ROUTING)
        self.assertAlmostEqual(xt[k('Wide One')], 6.0)


class OneSidedTest(unittest.TestCase):
    def test_only_teams_above_the_league_total_move(self):
        mean = np.array([10.0, 10.0, 10.0])
        pos = np.array(['WR', 'WR', 'WR'])
        implied = np.array([18.0, 22.5, 27.0])
        two = project.implied_shift(mean, pos, implied, {'WR': -0.34}, 22.5)
        one = project.implied_shift(mean, pos, implied, {'WR': -0.57, 'one_sided': True}, 22.5)
        self.assertGreater(two[0], 0)                          # two-sided raises a low-total WR
        self.assertEqual(one[0], 0.0)                          # one-sided leaves him alone
        self.assertEqual(one[1], 0.0)
        self.assertAlmostEqual(one[2], -0.57 * 10 * (27 / 22.5 - 1))

    def test_defaults_and_pins(self):
        new = config.load_config(config.current_week('2026-w08'))['model']
        self.assertEqual(new['implied_sensitivity']['one_sided'], False)   # week 8 pinned as entered
        self.assertEqual(new['implied_sensitivity']['WR'], -0.34)
        self.assertEqual(new['injury']['bump_scale'], {'RB': 1.0, 'WR': 1.0, 'TE': 1.0})
        d = config._read_toml(os.path.join(config.current_week('2026-w08').root, 'config', 'defaults.toml'))['model']
        self.assertEqual((d['implied_sensitivity']['one_sided'], d['implied_sensitivity']['WR']), (True, -0.57))
        self.assertEqual(d['injury']['bump_scale'], {'RB': 0.8, 'WR': 0.45, 'TE': 0.3})
        for w in ('2026-w04', '2026-w05', '2026-w06', '2026-w07'):
            m = config.load_config(config.current_week(w))['model']
            self.assertEqual(m['injury']['bump_scale'], {'RB': 1.0, 'WR': 1.0, 'TE': 1.0}, w)


if __name__ == '__main__':
    unittest.main()
