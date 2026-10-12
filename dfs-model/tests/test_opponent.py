"""Opponent adjustment (dfs.opponent): points allowed by position, the tilt beyond a defence's overall level, factors."""
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import config, opponent

SC = config.load_config(config.current_week('2026-w05'))['scoring']
O = dict(shrink_games=0.0, prior_games=0.0, cap=0.15, beta=dict(QB=1.0, TE=0.5))


def games(te_vs_soft=2.0, all_vs_bad=1.0):
    """Four defences, two weeks. Each offence scores the same every game except: tight ends against SOFT score
    te_vs_soft times as much, and everyone against BAD scores all_vs_bad times as much."""
    rows = []
    for week in (1, 2):
        for d in ['SOFT', 'BAD', 'AVG', 'AVG2']:
            for pos, yds in [('QB', 200), ('RB', 60), ('WR', 70), ('TE', 40)]:
                mult = (te_vs_soft if (d, pos) == ('SOFT', 'TE') else 1.0) * (all_vs_bad if d == 'BAD' else 1.0)
                rows.append(dict(week=week, opp=d, position=pos, passing_yards=yds * mult if pos == 'QB' else 0,
                                 rushing_yards=yds * mult if pos == 'RB' else 0, receiving_yards=yds * mult if pos in ('WR', 'TE') else 0))
    return pd.DataFrame(rows)


class OpponentTest(unittest.TestCase):
    def test_tilt_is_the_position_ratio_over_the_overall_ratio(self):
        a = opponent.allowed(games(), SC)
        self.assertEqual(a.loc[(1, 'SOFT'), 'TE'], 8.0)           # 80 receiving yards (yardage kept under the bonuses)
        t = opponent.tilt(a, None, O)
        self.assertGreater(t.at['SOFT', 'TE'], 1.3)
        self.assertLess(t.at['SOFT', 'QB'], 1.0)                 # same points as everyone, but SOFT's overall level is up
        self.assertAlmostEqual(t.at['SOFT', 'TE'] * t.at['SOFT', 'ALL'], opponent.ratios(a).at['SOFT', 'TE'])

    def test_a_defence_that_is_bad_at_everything_has_no_tilt(self):
        t = opponent.tilt(opponent.allowed(games(te_vs_soft=1.0, all_vs_bad=1.3), SC), None, O)
        self.assertGreater(t.at['BAD', 'ALL'], 1.15)             # the Vegas total already prices this
        np.testing.assert_allclose(t.loc['BAD', opponent.POS].astype(float), 1.0, atol=0.03)

    def test_shrinkage_and_prior_season(self):
        a = opponent.allowed(games(), SC)
        raw = opponent.tilt(a, None, O).at['SOFT', 'TE']
        shrunk = opponent.tilt(a, None, dict(O, shrink_games=2.0)).at['SOFT', 'TE']      # 2 games + 2 at league average
        self.assertTrue(1.0 < shrunk < raw)
        flat_prior = opponent.allowed(games(te_vs_soft=1.0), SC)
        blended = opponent.tilt(a, flat_prior, dict(O, prior_games=2.0)).at['SOFT', 'TE']
        self.assertTrue(1.0 < blended < raw)
        early = opponent.tilt(a.iloc[:0], a, dict(O, prior_games=2.0))                   # week 1: prior season only
        self.assertAlmostEqual(early.at['SOFT', 'TE'], raw)

    def test_factors_use_beta_and_the_cap(self):
        t = pd.DataFrame(dict(QB=[1.05, 1.5], RB=[1.2, 1.2], WR=1.0, TE=[0.9, 0.5], ALL=1.0), index=['AAA', 'BBB'])
        f = opponent.factors(np.array(['QB', 'TE', 'RB', 'D', 'QB', 'TE', 'WR']),
                             np.array(['AAA', 'AAA', 'AAA', 'AAA', 'BBB', 'BBB', 'ZZZ']), t, O)
        np.testing.assert_allclose(f, [1.05, 0.95, 1.0, 1.0, 1.15, 0.85, 1.0])   # RB has no beta; D and unknown defence: 1


if __name__ == '__main__':
    unittest.main()
