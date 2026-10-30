"""Doug's pool mode (dfs/pool.py): pool lists, rank boost, capacity check, filler role-guard test, filler limit."""
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import optimize, pool

PROJ = pd.DataFrame(dict(
    Name=['Q1', 'R1', 'W1', 'W2', 'T1', 'Buffalo Bills'],
    Pos=['QB', 'RB', 'WR', 'WR', 'TE', 'D'],
    Team=['AAA', 'AAA', 'BBB', 'BBB', 'AAA', 'BUF'],
    RoleVol=[0.0, 15.0, 6.0, 1.0, 0.0, np.nan],
    NoData=[False, False, False, False, True, False]))


class ListTest(unittest.TestCase):
    def test_members_ranks_and_dst_by_code(self):
        tab = pool.members(PROJ, {'QB': ['Q1'], 'WR': ['W2', 'W1'], 'DST': ['BUF'], 'ranked': True})
        self.assertEqual(tab.Name.tolist(), ['Q1', 'W2', 'W1', 'Buffalo Bills'])
        self.assertEqual(tab.Rank.tolist(), [1, 1, 2, 1])

    def test_unknown_name_stops(self):
        with self.assertRaises(ValueError):
            pool.members(PROJ, {'WR': ['Nobody']})

    def test_wrong_position_stops(self):
        with self.assertRaises(ValueError):
            pool.members(PROJ, {'RB': ['W1']})

    def test_on_slate_but_out_is_kept_with_note(self):
        tab = pool.members(PROJ, {'WR': ['W1', 'Hurt Guy']}, slate_names={'Hurt Guy'})
        self.assertEqual(tab.Note.tolist(), ['', 'not in projections (out)'])

    def test_settings_alone_do_not_turn_it_on(self):
        self.assertFalse(pool.is_on({'pool': {'max_filler': 1, 'ranked': False}}))
        self.assertTrue(pool.is_on({'pool': {'QB': ['Q1']}}))


class RankTest(unittest.TestCase):
    def test_linear_from_top_to_last(self):
        self.assertAlmostEqual(pool.rank_mult(1, 5, True, 0.05), 1.05)
        self.assertAlmostEqual(pool.rank_mult(3, 5, True, 0.05), 1.025)
        self.assertAlmostEqual(pool.rank_mult(5, 5, True, 0.05), 1.0)

    def test_unranked_is_flat(self):
        self.assertEqual(pool.rank_mult(1, 5, False, 0.05), 1.0)

    def test_ranked_top_splits_ranked_and_unranked(self):
        tab = pool.members(PROJ, {'WR': ['W2', 'W1'], 'QB': ['Q1'], 'ranked': True, 'ranked_top': {'WR': 1}})
        wr = tab[tab.Pos == 'WR']
        self.assertEqual(wr.Ranked.tolist(), [True, False])
        self.assertEqual(wr.Listed.tolist(), [1, 1])
        self.assertTrue(tab[tab.Pos == 'QB'].Ranked.all())   # no ranked_top entry = whole list ranked (old behaviour)
        self.assertEqual(tab[tab.Pos == 'QB'].Listed.tolist(), [1])

    def test_ranked_top_too_big_stops(self):
        with self.assertRaises(ValueError):
            pool.members(PROJ, {'WR': ['W1'], 'ranked': True, 'ranked_top': {'WR': 2}})


class CapacityTest(unittest.TestCase):
    def tab(self, **k):
        return pd.DataFrame(dict(Pos=[p for p, c in k.items() for _ in range(c)], Usable=True))

    def test_doug_sizes_fail_at_25_and_pass_at_33(self):
        t = self.tab(QB=10, RB=10, WR=10, TE=8, D=5)
        ok, needed, short = pool.capacity(t, 25, 150, 1)
        self.assertFalse(ok)
        self.assertEqual((needed, short['WR'], short['RB'], short['D']), (375, 200, 50, 25))   # FLEX short 350 beats the positional 250
        self.assertFalse(pool.capacity(t, 32, 150, 1)[0])
        self.assertTrue(pool.capacity(t, 33, 150, 1)[0])

    def test_qb_never_filled_from_outside(self):
        self.assertFalse(pool.capacity(self.tab(QB=5, RB=20, WR=30, TE=10, D=10), 25, 150, 1)[0])


class RoleGuardTest(unittest.TestCase):
    def test_filler_needs_data_and_volume(self):
        ok = pool.passes_role_guard(PROJ, {'positions': ['WR', 'TE'], 'min_volume': 3.0})
        self.assertEqual(ok.tolist(), [True, True, True, False, False, True])

    def test_missing_columns_stop(self):
        with self.assertRaises(ValueError):
            pool.passes_role_guard(PROJ.drop(columns='RoleVol'), {})


class FillerLimitTest(unittest.TestCase):
    """A small slate where the best lineup is mostly non-pool players: the solver must take at most one."""

    def test_at_most_one_outside(self):
        rows = []
        for t, o in [('AAA', 'BBB'), ('BBB', 'AAA'), ('CCC', 'DDD'), ('DDD', 'CCC')]:
            for pos, k in [('QB', 1), ('RB', 3), ('WR', 4), ('TE', 2), ('D', 1)]:
                rows += [dict(Name=f'{t}{pos}{j}', Pos=pos, Team=t, Opp=o, Salary=5000) for j in range(k)]
        df = pd.DataFrame(rows)
        inside = set(df.index[(df.Team.isin(['AAA', 'BBB'])) | (df.Pos == 'QB')])
        obj = np.where(df.index.isin(list(inside)), 1.0, 10.0)   # outside players look far better
        roster = dict(salary_cap=60000, slots=['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF'],
                      flex=['RB', 'WR', 'TE'], max_per_team=4)
        opt = dict(max_overlap=6, leverage=dict(enabled=False), min_salary=0, exposure_cap=25)
        rule = dict(receivers=2, bring_back=1, require=[])
        cap, use = {i: 25 for i in df.index}, {i: 0 for i in df.index}
        outside = [i for i in df.index if i not in inside]
        lp = optimize.solve_lineup(df, obj, 'AAA', rule, cap, use, [], [], roster, opt, (outside, 1))
        self.assertEqual(len(lp), 9)
        self.assertEqual(sum(i not in inside for i in lp), 1)
        free = optimize.solve_lineup(df, obj, 'AAA', rule, cap, use, [], [], roster, opt)
        self.assertGreater(sum(i not in inside for i in free), 1)   # without the limit it would take more


if __name__ == '__main__':
    unittest.main()
