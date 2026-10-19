"""[model.role_guard]: no current-season stats -> 0 (unless overridden); role floor on the configured positions."""
import contextlib
import io
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import project


def frame():
    return pd.DataFrame(dict(
        Name=['Phil Mafah', 'Kaden Wetjen', 'Braelon Allen', 'Bam Knight', 'Real WR', 'Override Guy', 'Bills DST'],
        Team=['NYG', 'PIT', 'NYJ', 'ARI', 'KC', 'NO', 'BUF'],
        Pos=['RB', 'WR', 'RB', 'RB', 'WR', 'WR', 'D'],
        NoData=[True, False, False, False, False, True, False],
        RoleVol=[0.0, 0.0, 5.5, 1.5, 7.0, 0.0, np.nan]))


class RoleGuardTest(unittest.TestCase):
    def run_guard(self, rg, overrides=None):
        p, sims = frame(), np.full((7, 100), 6.0)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            why = project.role_guard(p, sims, rg, overrides or {})
        return dict(zip(p.Name, why)), dict(zip(p.Name, sims.mean(axis=1))), out.getvalue()

    def test_off(self):
        why, mean, _ = self.run_guard({'enabled': False})
        self.assertTrue(all(v == '' for v in why.values()))
        self.assertTrue(all(v == 6.0 for v in mean.values()))

    def test_no_data_and_role_floor(self):
        why, mean, out = self.run_guard({'enabled': True, 'min_volume': 3.0, 'positions': ['WR', 'TE']},
                                        overrides={'Override Guy': 9.0})
        self.assertEqual(why['Phil Mafah'], 'no 2026 data')      # projected from FanDuel FPPG alone
        self.assertEqual(mean['Phil Mafah'], 0)
        self.assertIn('Phil Mafah', out)                          # the warning lists him
        self.assertEqual(why['Kaden Wetjen'], 'role < 3')        # routed volume only
        self.assertEqual(mean['Kaden Wetjen'], 0)
        self.assertEqual(mean['Braelon Allen'], 6.0)             # a backup with real volume qualifies
        self.assertEqual(mean['Bam Knight'], 6.0)                # RB not in the floor positions
        self.assertEqual(mean['Real WR'], 6.0)
        self.assertEqual(mean['Override Guy'], 6.0)              # Doug's read exempts him; overrides.apply rescales
        self.assertEqual(mean['Bills DST'], 6.0)

    def test_rb_in_floor(self):
        why, mean, _ = self.run_guard({'enabled': True, 'min_volume': 3.0, 'positions': ['RB', 'WR', 'TE']})
        self.assertEqual(why['Bam Knight'], 'role < 3')
        self.assertEqual(mean['Braelon Allen'], 6.0)

    def test_role_volume_is_pre_routing_current_season(self):
        st = pd.DataFrame([dict(k='ba', player_id='a', week=w, team='NYJ', attempts=0, completions=0, passing_yards=0,
                                passing_tds=0, passing_interceptions=0, carries=c, rushing_yards=0, rushing_tds=0,
                                targets=t, receptions=0, receiving_yards=0, receiving_tds=0)
                           for w, c, t in [(1, 4, 1), (2, 6, 0)]])
        self.assertAlmostEqual(project.role_volume(st)['ba'], 5.5)


if __name__ == '__main__':
    unittest.main()
