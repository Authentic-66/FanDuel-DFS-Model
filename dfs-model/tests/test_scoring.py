import unittest
import warnings

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import config, scoring


class ScoringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.week = config.current_week('2026-w04')
        cls.cfg = config.load_config(cls.week)
        cls.sc = cls.cfg['scoring']

    def test_bonuses(self):
        self.assertAlmostEqual(scoring.skill_points(self.sc, pass_yds=300), 15.0)    # 12 + 3
        self.assertAlmostEqual(scoring.skill_points(self.sc, pass_yds=299), 11.96)
        self.assertAlmostEqual(scoring.skill_points(self.sc, rec=8, rec_yds=100, rec_td=1), 4 + 10 + 3 + 6)
        self.assertAlmostEqual(scoring.skill_points(self.sc, rush_yds=100, rec_yds=100), 26.0)

    def test_dst_tiers(self):
        dst = self.sc['dst']
        pa = np.array([0, 1, 6, 7, 13, 14, 20, 21, 27, 28, 34, 35, 50])
        np.testing.assert_array_equal(scoring.points_allowed_tier(dst, pa), [10, 7, 7, 4, 4, 1, 1, 0, 0, -1, -1, -4, -4])
        self.assertEqual(scoring.dst_points(dst, 10, sacks=3, ints=1, fumble_recoveries=1, return_td=1), 4 + 3 + 2 + 2 + 6)

    def test_matches_fanduel_fppg(self):
        """Config scoring reproduces FanDuel's own FPPG from nflverse stats (players with 3 games played)."""
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            st = pd.read_csv(self.week.stats(), low_memory=False)
            st['fd'] = scoring.stats_points(self.sc, st)
        m = st[st.week < 4].groupby('player_display_name').agg(fd=('fd', 'mean'), g=('week', 'nunique'))
        fd = pd.read_csv(self.week.fd_players)
        x = fd[(fd.Position != 'D') & (fd.Played == 3)].merge(m[m.g == 3], left_on='Nickname', right_index=True)
        self.assertGreater(len(x), 150)
        np.testing.assert_allclose(x.FPPG, x.fd, atol=0.01)


if __name__ == '__main__':
    unittest.main()
