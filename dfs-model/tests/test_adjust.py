import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import backtest, project


class AdjustTest(unittest.TestCase):
    def setUp(self):
        self.proj = pd.DataFrame(dict(
            Name=['Starter', 'Backup', 'Back', 'Wideout', 'Cheap D', 'Dear D'], Pos=['QB', 'QB', 'RB', 'WR', 'D', 'D'],
            Team=['AAA', 'AAA', 'AAA', 'BBB', 'AAA', 'BBB'], Opp=['BBB', 'BBB', 'BBB', 'AAA', 'BBB', 'AAA'],
            Salary=[8000, 6000, 9000, 7000, 3000, 5000], StartingQB=[True, False, False, False, False, False],
            Proj=[20.0, 18.0, 26.0, 12.0, 6.0, 8.0]))
        self.sims = np.outer(self.proj.Proj.values, [0.5, 1.0, 1.5])
        self.lines = pd.DataFrame(dict(implied=[26.0, 20.0]), index=['AAA', 'BBB'])
        self.m = dict(qb=dict(zero_backups=True),
                      calibration=dict(enabled=True, top_knee=16.0, top_slope=0.25, rb_knee=8.0, rb_slope=0.1),
                      dst=dict(flatten=dict(enabled=True, opp_implied=-0.5, salary_per_1k=0.5)))

    def test_calibrated_shrinks_the_top_and_running_backs(self):
        cal = self.m['calibration']
        got = project.calibrated(np.array([12.0, 20.0, 26.0, 26.0]), np.array(['WR', 'QB', 'WR', 'RB']), cal)
        np.testing.assert_allclose(got, [12.0, 19.0, 23.5, 23.5 - 1.8])

    def test_adjust(self):
        out = project.adjust(self.proj, self.sims, self.lines, self.m).mean(axis=1)
        self.assertEqual(out[1], 0)                                  # backup QB
        np.testing.assert_allclose(out[[0, 2, 3]], [19.0, 21.7, 12.0])
        # DSTs: slate mean 7 kept; AAA faces BBB (20, 3 under the 23 average) at $1,000 under the average salary
        np.testing.assert_allclose(out[4:], [7 + 1.5 - 0.5, 7 - 1.5 + 0.5])
        np.testing.assert_allclose(self.sims[1], [9, 18, 27])       # input untouched

    def test_everything_off_changes_nothing(self):
        m = dict(qb={}, calibration=dict(enabled=False), dst={})
        np.testing.assert_array_equal(project.adjust(self.proj, self.sims, self.lines, m), self.sims)

    def test_fit_calibration_recovers_slopes_and_caps_them(self):
        rng = np.random.default_rng(0)
        rows = pd.DataFrame(dict(Pos=rng.choice(['RB', 'WR'], 4000), Proj=rng.uniform(4, 28, 4000)))
        true = dict(top_knee=16.0, top_slope=0.3, rb_knee=8.0, rb_slope=0.1)
        rows['FPTS'] = project.calibrated(rows.Proj.values, rows.Pos.values, true) + rng.normal(0, 1, 4000)
        fit = backtest.fit_calibration(rows, 16.0, 8.0)
        self.assertAlmostEqual(fit['top_slope'], 0.3, delta=0.03)
        self.assertAlmostEqual(fit['rb_slope'], 0.1, delta=0.03)
        rows['FPTS'] = np.minimum(rows.Proj, 16)                     # true slope 1: pinned at the cap
        self.assertEqual(backtest.fit_calibration(rows, 16.0, 8.0)['top_slope'], backtest.MAX_SLOPE)


if __name__ == '__main__':
    unittest.main()
