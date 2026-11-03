"""learn_from_winners.features: lineup build features from slot-ordered lineups (weekly review step, Nov 2)."""
import os
import sys
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import learn_from_winners as lfw  # noqa: E402

# id, pos, team, opp, salary, own %, points
ROWS = [('q', 'QB', 'A', 'B', 8000, 10, 20), ('r1', 'RB', 'A', 'B', 7000, 30, 15), ('r2', 'RB', 'C', 'D', 6000, 5, 10),
        ('r3', 'RB', 'B', 'A', 6500, 25, 12), ('w1', 'WR', 'A', 'B', 7500, 22, 18), ('w2', 'WR', 'C', 'D', 6000, 8, 9),
        ('w3', 'WR', 'D', 'C', 5500, 4, 6), ('w4', 'WR', 'B', 'A', 6000, 12, 7), ('t1', 'TE', 'C', 'D', 5000, 6, 5),
        ('t2', 'TE', 'A', 'B', 6000, 15, 8), ('d', 'D', 'C', 'D', 3500, 21, 7)]
P = pd.DataFrame(ROWS, columns=['Id', 'Pos', 'Team', 'Opp', 'Salary', 'own', 'FPTS'])


class FeaturesTest(unittest.TestCase):
    def test_game_stack_with_rb_flex(self):
        lu = ['q', 'r1', 'r2', 'w1', 'w2', 'w3', 't1', 'r3', 'd']        # FLEX RB r3 (opponent) = bring-back
        f = lfw.features(lfw.to_index([lu], P), P).iloc[0]
        self.assertEqual((f.n_RB, f.flex, f.stack_n, f.stack_recv, f.stack_type), (3, 'RB', 2, 1, 'game'))
        self.assertTrue(f.bringback)
        self.assertEqual(f.sal_RB, 19500)
        self.assertEqual(f.n_over20, 4)                                  # r1 30, r3 25, w1 22, d 21
        self.assertAlmostEqual(f.own_avg, np.mean([10, 30, 5, 22, 8, 4, 6, 25, 21]))
        self.assertEqual(f.pts_total, 20 + 15 + 10 + 18 + 9 + 6 + 5 + 12 + 7)

    def test_one_team_and_naked(self):
        lu = ['q', 'r2', 'r2', 'w1', 'w2', 'w3', 't1', 't2', 'd']        # TE flex t2 (teammate), no opponent
        f = lfw.features(lfw.to_index([lu], P), P).iloc[0]
        self.assertEqual((f.flex, f.stack_n, f.stack_type, f.qb_tier), ('TE', 2, 'one-team', 'QB 7.5-8.4k'))
        lu = ['q', 'r2', 'r2', 'w2', 'w2', 'w3', 't1', 'w2', 'd']
        self.assertEqual(lfw.features(lfw.to_index([lu], P), P).iloc[0].stack_type, 'naked')

    def test_unknown_player_dropped(self):
        lu = ['q', 'r1', 'r2', 'w1', 'w2', 'w3', 't1', 'r3', 'zzz']
        self.assertEqual(len(lfw.features(lfw.to_index([lu], P), P)), 0)


if __name__ == '__main__':
    unittest.main()
