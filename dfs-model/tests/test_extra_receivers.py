"""[stacks] extra_receivers (Doug, week 7): a named RB counts as a stack receiver for his own QB, off unless listed."""
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import optimize, pool

ROSTER = dict(salary_cap=60000, slots=['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF'],
              flex=['RB', 'WR', 'TE'], max_per_team=4)
OPT = dict(max_overlap=6, leverage=dict(enabled=False), min_salary=0, exposure_cap=25,
           stack=dict(receivers=2, bring_back=1))


def slate():
    """SFX has a QB, one TE and a star RB but no usable WR (week 7's SF); three other teams are full."""
    rows = [dict(Name='QBX', Pos='QB', Team='SFX', Opp='ATX'), dict(Name='Kittle', Pos='TE', Team='SFX', Opp='ATX'),
            dict(Name='CMC', Pos='RB', Team='SFX', Opp='ATX'), dict(Name='Other RB', Pos='RB', Team='SFX', Opp='ATX'),
            dict(Name='SFX D', Pos='D', Team='SFX', Opp='ATX')]
    for t, o in [('ATX', 'SFX'), ('CCC', 'DDD'), ('DDD', 'CCC')]:
        for pos, k in [('QB', 1), ('RB', 3), ('WR', 4), ('TE', 2), ('D', 1)]:
            rows += [dict(Name=f'{t}{pos}{j}', Pos=pos, Team=t, Opp=o) for j in range(k)]
    return pd.DataFrame(rows).assign(Salary=5000)


def solve(df, stacks):
    rule = optimize.stack_rule('SFX', dict(stacks, rules={}), OPT)
    cap, use = {i: 25 for i in df.index}, {i: 0 for i in df.index}
    return optimize.solve_lineup(df, np.ones(len(df)), 'SFX', rule, cap, use, [], [], ROSTER, OPT)


class ExtraReceiverTest(unittest.TestCase):
    def test_off_unless_listed(self):
        df = slate()
        self.assertEqual(optimize.receivers(df, {}).sum(), int(df.Pos.isin(['WR', 'TE']).sum()))
        self.assertIsNone(solve(df, {}))   # one SFX receiver (Kittle): no stack possible

    def test_named_rb_completes_the_stack(self):
        df = slate()
        lp = solve(df, {'extra_receivers': ['CMC']})
        names = set(df.Name[lp])
        self.assertTrue({'QBX', 'Kittle', 'CMC'} <= names)
        self.assertNotIn('Other RB', set(df.Name[optimize.receivers(df, {'extra_receivers': ['CMC']})]))

    def test_only_rbs_can_be_named(self):
        with self.assertRaises(ValueError):
            optimize.receivers(slate(), {'extra_receivers': ['QBX']})

    def test_rb_counts_for_his_own_qb_only(self):
        df = slate()
        rec = optimize.receivers(df, {'extra_receivers': ['CMC']})
        self.assertEqual(set(df.Team[rec & (df.Pos == 'RB')]), {'SFX'})

    def test_proportional_allocation_gives_the_team_its_weight(self):
        """With the RB listed, SFX keeps its weight-based share instead of handing it to the other teams."""
        df = slate().assign(row=lambda d: range(len(d)), Proj=10.0, Inj='', StartingQB=lambda d: d.Pos == 'QB')
        sims = np.full((len(df), 50), 10.0) + np.random.default_rng(0).normal(0, 1, (len(df), 50))
        cfg = dict(roster=ROSTER, prefs=dict(yellow={}, green={}, player_cap={}),
                   stacks=dict(weights={'SFX': 2, 'CCC': 1, 'DDD': 1}, rules={}, extra_receivers=['CMC']),
                   optimizer=dict(OPT, n_lineups=8, seed=1, mean_weight=0.6, yellow_factor=0.5, green_multiplier=2,
                                  green_floor=12, questionable_cap_pct=0.12, relax_force_after=3, drop_force_after=12,
                                  stack_allocation='proportional', max_overlap=7))
        lineups, _ = optimize.build_lineups(df, sims, cfg)
        qb_teams = [df.Team[[i for i in lp if df.Pos[i] == 'QB'][0]] for lp in lineups]
        self.assertEqual(qb_teams.count('SFX'), 4)

    def test_pool_mode_counts_the_rb(self):
        df = slate().assign(InPool=True)
        weights = {'SFX': 5, 'ATX': 1, 'CCC': 1, 'DDD': 1}
        cfg = dict(optimizer=OPT, stacks=dict(weights=weights, rules={}, extra_receivers=['CMC']))
        self.assertEqual(pool.stack_weights(df, cfg, 0).get('SFX'), 5)
        cfg = dict(optimizer=OPT, stacks=dict(weights=weights, rules={}))
        self.assertNotIn('SFX', pool.stack_weights(df, cfg, 0))   # without the RB: dropped


if __name__ == '__main__':
    unittest.main()
