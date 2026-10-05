import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import data, usage


def rows(*recs):
    base = dict(season_type='REG', position='WR', team='KC', attempts=0, completions=0, passing_yards=0, passing_tds=0,
                passing_interceptions=0, carries=0, rushing_yards=0, rushing_tds=0, targets=0, receptions=0,
                receiving_yards=0, receiving_tds=0)
    return pd.DataFrame([{**base, **r} for r in recs])


class UsageTest(unittest.TestCase):
    def test_name_key(self):
        self.assertEqual(data.norm_name('Kenneth Walker III'), data.norm_name('Kenneth Walker'))
        self.assertEqual(data.norm_name("Ja'Marr Chase"), 'jamarrchase')

    def test_name_collision_keeps_offensive_player(self):
        st = rows(dict(k='djturner', player_id='wr', week=1, targets=6),
                  dict(k='djturner', player_id='cb', week=1, position='CB'),
                  dict(k='djturner', player_id='cb', week=2, position='CB'))
        agg = usage.aggregate(st)
        self.assertEqual(agg.at['djturner', 'g'], 1)
        self.assertEqual(agg.at['djturner', 'tgt'], 6)

    def test_two_way_player_keeps_all_games(self):
        st = rows(dict(k='th', player_id='a', week=1, targets=3, position='CB'),
                  dict(k='th', player_id='a', week=2, position='CB'))
        self.assertEqual(usage.aggregate(st).at['th', 'g'], 2)

    def test_blend_math(self):
        cur = usage.aggregate(rows(*[dict(k='p', player_id='a', week=w, targets=10, receptions=8, receiving_yards=100)
                                     for w in (1, 2)]))
        prior = usage.aggregate(rows(*[dict(k='p', player_id='a', week=w, targets=5, receptions=3, receiving_yards=30)
                                       for w in range(1, 5)]))
        pb = dict(usage_games=2, efficiency_games=4, team_change_weight=1.0, min_prior_games=4)
        b = usage.blend_prior(cur, prior, pb)
        self.assertAlmostEqual(usage.per_game(b, 'p', 'tgt'), (20 + 2 * 5) / 4)       # 2 pseudo-games at 5 tgt/g
        self.assertAlmostEqual(b.at['p', 'rey'] / b.at['p', 'tgt'], (200 + 4 * 30) / (20 + 4 * 5))
        self.assertEqual(usage.per_game(cur, 'p', 'tgt'), 10)                          # input untouched

    def test_blend_skips_short_prior_and_scales_team_change(self):
        cur = usage.aggregate(rows(dict(k='p', player_id='a', week=1, targets=10)))
        short = usage.aggregate(rows(dict(k='p', player_id='a', week=1, targets=0)))
        pb = dict(usage_games=2, efficiency_games=4, team_change_weight=0.5, min_prior_games=4)
        self.assertEqual(usage.per_game(usage.blend_prior(cur, short, pb), 'p', 'tgt'), 10)
        moved = usage.aggregate(rows(*[dict(k='p', player_id='a', week=w, targets=2, team='NYJ') for w in range(1, 5)]))
        self.assertAlmostEqual(usage.per_game(usage.blend_prior(cur, moved, pb), 'p', 'tgt'), (10 + 1 * 2) / 2)

    def test_starting_qb_uses_each_teams_latest_game(self):
        st = rows(dict(k='a', player_id='a', week=3, position='QB', team='BUF', attempts=30),
                  dict(k='b', player_id='b', week=2, position='QB', team='MIA', attempts=35),   # MIA bye in week 3
                  dict(k='c', player_id='c', week=1, position='QB', team='MIA', attempts=40))
        self.assertEqual(usage.starting_qbs(st), {'a', 'b'})


if __name__ == '__main__':
    unittest.main()
