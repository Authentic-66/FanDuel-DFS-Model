"""Role-guard recent-role switches (Doug, Nov 3 2026; docs/role_guard_tests.md): promotion, snap_projection,
role-drop flag / scale, the snap features and the pool filler check."""
import contextlib
import io
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import pool, project, snaps

RG = {'enabled': True, 'min_volume': 3.0, 'positions': ['WR', 'TE'], 'report_min_proj': 0.0}


def frame():
    # Cooks: low role, 68% snaps last game; Inheritor: low role but inherits 2.0; Recent: 4 a game lately;
    # Kirk: no data, 60% snaps (prior 0.8); Bench: no data, 30% snaps; Wilson: RB 0% last game after 40%
    return pd.DataFrame(dict(
        Name=['Cooks', 'Inheritor', 'Recent', 'Plain low', 'Kirk', 'Bench', 'Wilson', 'Hurt'],
        Team=['SF'] * 8, Pos=['WR', 'WR', 'TE', 'WR', 'WR', 'WR', 'RB', 'RB'], Inj=[''] * 7 + ['Q'],
        NoData=[False, False, False, False, True, True, False, False],
        RoleVol=[2.0, 1.5, 2.5, 1.0, 0.0, 0.0, 9.0, 9.0], GainedVol=[0.7, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        RecentVol=[2.5, 1.0, 4.0, 0.5, 0.0, 0.0, 4.0, 4.0], LastSnap=[0.68, 0.2, 0.3, 0.1, 0.6, 0.3, 0.0, 0.05],
        ActiveLast=[True] * 8, AvgSnap=[0.4, 0.2, 0.3, 0.1, np.nan, np.nan, 0.4, 0.5],
        Recent2Snap=[0.6, 0.2, 0.3, 0.1, 0.3, 0.15, 0.24, 0.3], PriorSnap=[0.7, 0.5, 0.5, 0.5, 0.8, np.nan, 0.5, 0.5]))


def run(rg):
    p, sims = frame(), np.full((8, 50), 6.0)
    with contextlib.redirect_stdout(io.StringIO()) as out:
        drop = project.role_drop(p, rg, sims)
        why = project.role_guard(p, sims, rg, {})
    return dict(zip(p.Name, why)), dict(zip(p.Name, sims.mean(axis=1))), dict(zip(p.Name, drop)), out.getvalue()


class SwitchTest(unittest.TestCase):
    def test_all_off_is_the_old_guard(self):
        why, mean, drop, out = run(RG)
        for n in ('Cooks', 'Inheritor', 'Recent', 'Plain low'):
            self.assertEqual(mean[n], 0.0)
        self.assertEqual(why['Kirk'], 'no 2026 data')
        self.assertEqual(mean['Wilson'], 6.0)            # flag only: draws untouched
        self.assertIn('snaps 40% -> 0%', drop['Wilson'])
        self.assertIn('Wilson', out)

    def test_promotion(self):
        why, mean, _, _ = run({**RG, 'promotion': True})
        self.assertEqual(mean['Cooks'], 6.0)             # 68% snaps
        self.assertEqual(mean['Inheritor'], 6.0)         # 1.5 + 2.0 inherited
        self.assertEqual(mean['Recent'], 6.0)            # 4 a game over the last 2
        self.assertEqual(mean['Plain low'], 0.0)
        self.assertEqual(why['Cooks'], '')
        self.assertEqual(mean['Kirk'], 0.0)              # no-data players are switch 2's

    def test_snap_projection(self):
        why, mean, _, _ = run({**RG, 'snap_projection': True})
        self.assertAlmostEqual(mean['Kirk'], 6.0 * 0.6 / 0.8)
        self.assertEqual(mean['Bench'], 0.0)             # under 50%
        self.assertEqual(why['Bench'], 'no 2026 data')
        self.assertEqual(mean['Cooks'], 0.0)

    def test_role_drop_scale_and_injured_not_flagged(self):
        _, mean, drop, _ = run({**RG, 'role_drop_action': 'scale'})
        self.assertAlmostEqual(mean['Wilson'], 6.0 * 0.24 / 0.4)
        self.assertEqual(drop['Hurt'], '')               # tagged Q: the injury list covers him
        with self.assertRaises(ValueError):
            run({**RG, 'role_drop_action': 'zero'})

    def test_pool_filler_counts_a_rescue_only_when_on(self):
        p = frame().assign(RoleGuard='', GuardRescue=['promoted: snaps 68%'] + [''] * 7)
        self.assertFalse(pool.passes_role_guard(p, RG).iloc[0])
        self.assertTrue(pool.passes_role_guard(p, {**RG, 'promotion': True}).iloc[0])

    def test_features(self):
        sn = pd.DataFrame(dict(k=['a', 'a', 'a', 'b', 'b'], team=['SF'] * 5, position=['WR'] * 5,
                               week=[5, 6, 7, 5, 6], snap=[0.4, 0.5, 0.68, 0.3, 0.3]))
        st = pd.DataFrame(dict(k=['a', 'a'], team=['SF', 'SF'], week=[6, 7], targets=[2, 3], carries=[0, 0]))
        f = snaps.features(sn, st, None, games=2)
        self.assertAlmostEqual(f.at['a', 'LastSnap'], 0.68)
        self.assertAlmostEqual(f.at['a', 'AvgSnap'], 0.45)
        self.assertAlmostEqual(f.at['a', 'RecentVol'], 2.5)
        self.assertEqual(f.at['b', 'LastSnap'], 0.0)     # no row in the team's last game: inactive
        self.assertFalse(f.at['b', 'ActiveLast'])
        self.assertAlmostEqual(f.at['b', 'Recent2Snap'], 0.15)


if __name__ == '__main__':
    unittest.main()
