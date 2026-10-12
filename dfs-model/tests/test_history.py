"""History refits (dfs.history): Vegas lines from the schedule, starter absences, season weights, weighted fits."""
import os
import tempfile
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import backtest, history

CFG = dict(teams=dict(nflverse_to_fd={'LA': 'LAR'}))


def stat_rows():
    """Team AAA, 5 games. WR One (8 targets a game) misses week 5; WR Two goes from 5 targets to 11, the TE stays at 4."""
    rows = []
    for w in range(1, 6):
        if w < 5:
            rows.append(dict(k='one', position='WR', week=w, team='AAA', targets=8, carries=0))
        rows.append(dict(k='two', position='WR', week=w, team='AAA', targets=5 if w < 5 else 11, carries=0))
        rows.append(dict(k='te', position='TE', week=w, team='AAA', targets=4, carries=0))
        rows.append(dict(k='rb', position='RB', week=w, team='AAA', targets=1, carries=15))
    return pd.DataFrame(rows).assign(season=2025)


class HistoryTest(unittest.TestCase):
    def test_season_weights(self):
        self.assertEqual(history.season_weights([2023, 2024, 2025], 0.5), {2023: 0.25, 2024: 0.5, 2025: 1.0})

    def test_lines_from_schedule(self):
        cache = tempfile.mkdtemp()
        pd.DataFrame([dict(game_type='REG', week=1, home_team='LA', away_team='SEA', home_score=30, away_score=10,
                           spread_line=3.0, total_line=47.0),
                      dict(game_type='POST', week=19, home_team='LA', away_team='SEA', home_score=1, away_score=2,
                           spread_line=1.0, total_line=40.0)]).to_csv(os.path.join(cache, 'schedule_2025.csv'), index=False)
        g = history.load_lines(cache, 2025, CFG).set_index('team')
        self.assertEqual(sorted(g.index), ['LAR', 'SEA'])                                 # regular season, FanDuel codes
        self.assertEqual((g.implied['LAR'], g.opp_implied['LAR'], g.margin['LAR']), (25.0, 22.0, 3.0))   # home favoured by 3
        self.assertEqual((g.implied['SEA'], g.margin['SEA'], g.allowed['SEA']), (22.0, -3.0, 30))

    def test_first_missed_game_of_a_starter(self):
        ev = history.absences(stat_rows())
        self.assertEqual(list(ev.k), ['one'])                        # the others never miss; the RB is not out
        e = ev.iloc[0]
        self.assertEqual((e.week, e.base, e.others_base, e.others), (5, 8.0, 10.0, 16.0))
        self.assertEqual((e.gain, e.gain_same, e.gain_other), (6.0, 6.0, 0.0))
        share, _ = history.share(ev, {2025: 1.0})
        self.assertAlmostEqual(share, 0.75)

    def test_a_player_who_moved_teams_is_not_an_absence(self):
        st = pd.concat([stat_rows(), pd.DataFrame([dict(k='one', position='WR', week=5, team='BBB', targets=7, carries=0,
                                                        season=2025)])])
        self.assertEqual(len(history.absences(st)), 0)

    def test_weights_reach_the_fits(self):
        rng = np.random.default_rng(0)
        rows = pd.DataFrame(dict(Pos='WR', Proj=rng.uniform(4, 28, 2000)))
        rows['FPTS'] = rows.Proj - 0.3 * np.maximum(rows.Proj - 16, 0)
        rows.loc[:999, 'FPTS'] = rows.Proj[:1000]                    # the first half shows no over-projection at all
        w = np.r_[np.zeros(1000), np.ones(1000)]
        self.assertAlmostEqual(backtest.fit_calibration(rows, 16.0, 8.0, w)['top_slope'], 0.3, places=6)
        self.assertLess(backtest.fit_calibration(rows, 16.0, 8.0)['top_slope'], 0.2)
        self.assertEqual(history.fit_knees(rows, w, [12, 16, 20], [8])['top_knee'], 16)
        sims = np.tile(np.arange(100.0), (4, 1))                     # 90th percentile 89.1
        actual = np.array([95.0, 95.0, 50.0, 50.0])
        self.assertEqual(backtest.p90_coverage(sims, actual), 0.5)
        self.assertEqual(backtest.p90_coverage(sims, actual, weights=np.array([1, 0, 1, 2])), 0.25)


if __name__ == '__main__':
    unittest.main()
