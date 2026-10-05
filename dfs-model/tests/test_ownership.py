"""Ownership model and leverage options (Phase 2 #2), on synthetic data plus the week-4 training frame."""
import unittest
import warnings

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import config, optimize, ownership


def synthetic(n=200, seed=0):
    rng = np.random.default_rng(seed)
    pos = rng.choice(['QB', 'RB', 'WR', 'TE', 'D'], n)
    sal = rng.integers(40, 95, n) * 100
    proj = sal / 1000 * 2 + rng.normal(0, 2, n)
    df = pd.DataFrame(dict(Id=[f'1-{i}' for i in range(n)], Name=[f'P{i}' for i in range(n)], Pos=pos, Team='AAA',
                           Salary=sal, Proj=proj, Value_per_1k=proj / sal * 1000, FD_FPPG=proj + rng.normal(0, 2, n),
                           ImpliedTeamTotal=22.0, GameTotal=44.0, GainedVol=0.0))
    z = -4 + 2.0 * (df.Value_per_1k - 2) + rng.normal(0, 0.3, n)
    df['own'] = 1 / (1 + np.exp(-z))
    return df


class OwnershipTest(unittest.TestCase):
    def setUp(self):
        self.oc = config.load_config(config.current_week('2026-w04'))['ownership']

    def test_normalize_hits_position_totals(self):
        df = synthetic()
        z = np.random.default_rng(1).normal(-3, 1, len(df))
        out = ownership.normalize(df, z, {'QB': 1.0, 'RB': 2.5, 'D': 1.0})
        for p, t in [('QB', 1.0), ('RB', 2.5), ('D', 1.0)]:
            self.assertAlmostEqual(out[(df.Pos == p).values].sum(), t, places=6)
        # order within a position is preserved (a constant logit shift)
        m = (df.Pos == 'RB').values
        self.assertTrue((np.argsort(out[m]) == np.argsort(z[m])).all())

    def test_fit_recovers_signal(self):
        df = synthetic(400)
        model = ownership.fit(df, self.oc)
        oof = ownership.cross_validate(df, self.oc)
        self.assertGreater(np.corrcoef(np.log(oof), np.log(df.own))[0, 1], 0.7)
        self.assertEqual(set(model['totals']), set(ownership.POSITIONS))
        self.assertEqual((model['totals']['QB'], model['totals']['D']), (1.0, 1.0))

    def test_stack_table_flags_chalk(self):
        df = pd.DataFrame(dict(Name=['qa', 'wa', 'qb', 'wb'], Pos=['QB', 'WR', 'QB', 'WR'], Team=['A', 'A', 'B', 'B'],
                               StartingQB=[True, False, True, False], Own_proj=[15.0, 30.0, 3.0, 5.0]))
        st = ownership.stack_table(df, {'A': 10, 'B': 10}, chalk_qb_own=10).set_index('Team')
        self.assertEqual(st.Chalk['A'], 'CHALK')
        self.assertEqual(st.Chalk['B'], '')
        self.assertLess(st.Leverage['A'], st.Leverage['B'])
        lw = optimize.leverage_weights(df, {'A': 10, 'B': 10}, {'stack_exponent': 1.0})
        self.assertLess(lw['A'], lw['B'])


class Week4OwnershipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('ignore')
        cls.week = config.current_week('2026-w04')
        cls.cfg = config.load_config(cls.week)
        cls.train = ownership.training_frame(cls.week, cls.cfg)

    def test_frame_and_cv_fit(self):
        self.assertAlmostEqual(self.train.own.sum(), 8.96, places=1)        # ~9 roster slots of ownership
        oof = ownership.cross_validate(self.train, self.cfg['ownership'])
        rep = ownership.fit_report(self.train, oof).set_index('pos')
        self.assertLess(rep.mae['ALL'], rep.mae_null['ALL'])                 # beats position-average guess
        self.assertGreater(rep.r_log['ALL'], 0.6)

    def test_no_prior_results_means_no_column(self):
        proj = self.train.drop(columns='own')
        self.assertNotIn('Own_proj', ownership.attach(self.week, self.cfg, proj, quiet=True))

    def test_next_week_gets_projected_ownership(self):
        """A week-5 run fits on week 4's results; Own_proj sums to ~900% (9 slots) with QB and DST at 100% each."""
        out = ownership.attach(config.current_week('2026-w05'), self.cfg, self.train.drop(columns='own'), quiet=True)
        self.assertAlmostEqual(out.Own_proj.sum(), self.train.own.sum() * 100 + 0.8, delta=1.5)
        for p in ['QB', 'D']:
            self.assertAlmostEqual(out.Own_proj[out.Pos == p].sum(), 100, delta=0.5)


if __name__ == '__main__':
    unittest.main()
