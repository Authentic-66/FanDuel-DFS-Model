"""Flex shadow switches (Doug, Nov 2; docs/week9_tests.md section 6): [optimizer] flex_te_top_salary and
rb_stack_pieces. Both off by default; the weeks 9-10 shadow build turns them on (optimize.py --flex-shadow)."""
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import optimize
from test_extra_receivers import OPT, ROSTER, slate


def solve(df, team='CCC', obj=None):
    rule = optimize.stack_rule(team, {'rules': {}}, OPT)
    cap, use = {i: 25 for i in df.index}, {i: 0 for i in df.index}
    obj = np.ones(len(df)) if obj is None else obj
    return optimize.solve_lineup(df, obj, team, rule, cap, use, [], [], ROSTER, OPT)


class FlexTeTopSalaryTest(unittest.TestCase):
    def test_second_te_only_from_the_top_n(self):
        df = slate()
        obj = np.where(df.Pos == 'TE', 100.0, 1.0)            # the optimizer wants as many TEs as possible
        self.assertEqual(int((df.Pos[solve(df, obj=obj)] == 'TE').sum()), 2)
        df['FlexTE'] = df.Name.isin(['CCCTE0', 'DDDTE0'])     # a pair must include one of these (he is the FLEX TE)
        tes = set(df.Name[[i for i in solve(df, obj=obj) if df.Pos[i] == 'TE']])
        self.assertTrue(len(tes) == 1 or tes & {'CCCTE0', 'DDDTE0'}, tes)
        df['FlexTE'] = False                                  # nobody qualifies: one TE only
        self.assertEqual(int((df.Pos[solve(df, obj=obj)] == 'TE').sum()), 1)

    def test_eligible_pool_marks_the_slate_top_n_by_salary_reds_included(self):
        proj = pd.DataFrame(dict(Name=['T1', 'T2', 'T3', 'Q'], Pos=['TE', 'TE', 'TE', 'QB'], Team=['A', 'B', 'C', 'A'],
                                 Salary=[7000, 6000, 5000, 8000], Proj=10.0, Inj='', StartingQB=[False, False, False, True]))
        proj['Id'] = proj.Name
        opt = dict(exclude_questionable=True, min_proj=0, starters={'TE': 1}, starters_min_proj={})
        prefs = dict(green={}, red=['T1'], red_teams=[], starters_only=False)
        self.assertNotIn('FlexTE', optimize.eligible_pool(proj, prefs, opt))            # off by default
        df = optimize.eligible_pool(proj, prefs, dict(opt, flex_te_top_salary=2))
        self.assertEqual(dict(zip(df.Name, df.FlexTE)), {'T2': True, 'T3': False, 'Q': False})   # T1 red, still ranked


class RbStackPiecesTest(unittest.TestCase):
    def test_every_rb_becomes_a_stack_piece(self):
        """SFX has one receiver (Kittle): unstackable unless an RB counts."""
        df = slate().assign(row=lambda d: range(len(d)), Proj=10.0, Inj='', StartingQB=lambda d: d.Pos == 'QB')
        sims = np.full((len(df), 50), 10.0) + np.random.default_rng(0).normal(0, 1, (len(df), 50))
        cfg = dict(roster=ROSTER, prefs=dict(yellow={}, green={}, player_cap={}),
                   stacks=dict(weights={'SFX': 2, 'CCC': 1, 'DDD': 1}, rules={}),
                   optimizer=dict(OPT, n_lineups=8, seed=1, mean_weight=0.6, yellow_factor=0.5, green_multiplier=2,
                                  green_floor=12, questionable_cap_pct=0.12, relax_force_after=3, drop_force_after=12,
                                  stack_allocation='proportional', max_overlap=7))
        qbs = lambda lu: [df.Team[[i for i in lp if df.Pos[i] == 'QB'][0]] for lp in lu]
        self.assertEqual(qbs(optimize.build_lineups(df, sims, cfg)[0]).count('SFX'), 0)
        cfg['optimizer']['rb_stack_pieces'] = True
        self.assertEqual(qbs(optimize.build_lineups(df, sims, cfg)[0]).count('SFX'), 4)
        self.assertNotIn('extra_receivers', cfg['stacks'])    # the config itself is not changed


if __name__ == '__main__':
    unittest.main()
