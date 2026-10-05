"""Week-4 regression checks on the real inputs (no files written)."""
import os
import tempfile
import unittest
import warnings

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import backtest, config, optimize, overrides, project


class Week4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('ignore')
        cls.week = config.current_week('2026-w04')
        cls.cfg = config.load_config(cls.week, model={'n_sims': 2000})
        cls.proj, cls.sims = project.build(cls.week, cls.cfg)

    def test_shapes_and_order(self):
        self.assertEqual(len(self.proj), self.sims.shape[0])
        self.assertEqual(self.sims.shape[1], 2000)
        self.assertTrue(self.proj.Proj.is_monotonic_decreasing)
        np.testing.assert_allclose(self.proj.Proj, self.sims.mean(1), atol=0.051)
        self.assertFalse(self.proj.Proj.isna().any())

    def test_status_applied(self):
        names = self.proj.set_index('Name')
        self.assertNotIn('Justin Jefferson', names.index)                 # OUT -> removed
        self.assertEqual(names.Inj['Ray Davis'], 'Q')
        starters = self.proj[self.proj.StartingQB]
        self.assertEqual(starters.Team.value_counts().max(), 1)
        self.assertGreaterEqual(len(starters), 23)    # TB's week-3 starter is not on the week-4 active list

    def test_deterministic(self):
        _, s2 = project.build(self.week, self.cfg)
        np.testing.assert_array_equal(self.sims, s2)

    def test_overrides(self):
        p, s = overrides.apply(self.proj, self.sims, self.cfg['overrides'])
        got = p.set_index('Name').Proj
        for name, mean in self.cfg['overrides'].items():
            self.assertAlmostEqual(got[name], mean, places=1)
        p2, _ = overrides.apply(p, s, self.cfg['overrides'])
        pd.testing.assert_frame_equal(p, p2)
        with self.assertRaises(KeyError):
            overrides.apply(self.proj, self.sims, {'Nobody Real': 10})

    def test_optimizer_pool_and_limits(self):
        o, prefs = self.cfg['optimizer'], self.cfg['prefs']
        df = optimize.eligible_pool(self.proj, prefs, o)
        self.assertFalse(df.Name.isin(prefs['red']).any())
        self.assertFalse(df.Team.isin(prefs['red_teams']).any())
        self.assertTrue(df[df.Pos == 'QB'].StartingQB.all())
        self.assertLessEqual(df[(df.Pos == 'RB') & ~df.Name.isin(prefs['green'])].groupby('Team').size().max(), 1)
        cap, need = optimize.exposure_limits(df, prefs, o)
        for i, n in df.Name.items():
            if n in prefs['yellow']:
                self.assertEqual(cap[i], round(prefs['yellow'][n] / 2))
        self.assertTrue(all(v <= o['exposure_cap'] for v in need.values()))
        self.assertEqual(need[df.index[df.Name == 'Josh Allen'][0]], 25)   # min(25, max(2*17, 12))
        rule = optimize.stack_rule('BUF', self.cfg['stacks'], o)
        self.assertEqual((rule['receivers'], rule['require']), (1, ['James Cook III']))

    def test_upload_header_survives_round_trip(self):
        path = os.path.join(tempfile.mkdtemp(), 'upload.csv')
        optimize.write_upload(path, [['1-1'] * 9], self.cfg['roster']['slots'])
        header, _ = optimize.read_upload(path)
        self.assertEqual(','.join(header), 'QB,RB,RB,WR,WR,WR,TE,FLEX,DEF')

    def test_blend_reduces_week4_error(self):
        """The tuned prior blend must beat no blend on the week-4 slate (docs/phase2_prior_blend.md)."""
        res, _ = backtest.slate_backtest(self.week, config.load_config(self.week),
                                         [dict(usage_games=0, efficiency_games=0), {}])
        self.assertLess(res.rmse[1], res.rmse[0])
        self.assertLess(res['gap_20+'][1], res['gap_20+'][0])


if __name__ == '__main__':
    unittest.main()
