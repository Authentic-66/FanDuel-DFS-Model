"""Week-8 prep (docs/week8_prep.md): traded player's old team by present share, questionable routing, TE-in-FLEX limit,
green-QB overflow in assign_forced, FanDuel player-list diff."""
import os
import random
import sys
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import data, optimize, project, usage
from test_usage import rows

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
import diff_players  # noqa: E402

ROUTING = {'WR': {'tgt_same': 0.8, 'tgt_other': 0.2}}


def team(gone_after_week1):
    """AAA: 'Moved WR' (10 targets a game) played week 1 only if gone_after_week1; teammates played weeks 1-2."""
    players = [('Moved WR', 'WR', 10), ('Wide One', 'WR', 6), ('Tight', 'TE', 4)]
    recs = [dict(k=data.norm_name(n), player_id=n, week=w, team='AAA', position=p, targets=t)
            for n, p, t in players for w in (1, 2) if not (n == 'Moved WR' and w == 2 and gone_after_week1)]
    st = rows(*recs)
    fd = pd.DataFrame(dict(Nickname=[p[0] for p in players], Position=[p[1] for p in players], Team='AAA', Inj=''))
    fd['Full'], fd['Key'] = fd.Nickname, fd.Nickname.map(data.norm_name)
    return usage.aggregate(st), st, fd[fd.Nickname != 'Moved WR']


class TradeOldTeamTest(unittest.TestCase):
    def moved(self):
        return pd.DataFrame([dict(Key=data.norm_name('Moved WR'), Name='Moved WR', Pos='WR', From='AAA', To='BBB',
                                  share=0.0, factor=1.0)])

    def test_full_hands_everything_out_present_share_halves_it_after_one_game_without_him(self):
        agg, st, active = team(gone_after_week1=True)
        k = data.norm_name
        full, _ = usage.trade_volume(agg, self.moved(), active, 0.8, ROUTING)
        fade, _ = usage.trade_volume(agg, self.moved(), active, 0.8, ROUTING, st, 'present_share')
        self.assertAlmostEqual(full[k('Wide One')], 0.8 * 10)
        self.assertAlmostEqual(fade[k('Wide One')], 0.8 * 10 / 2)     # he was there for 1 of Wide One's 2 games
        self.assertAlmostEqual(fade[k('Tight')], full[k('Tight')] / 2)

    def test_present_share_is_full_when_he_never_missed_a_game(self):
        agg, st, active = team(gone_after_week1=False)
        full, _ = usage.trade_volume(agg, self.moved(), active, 0.8, ROUTING)
        fade, _ = usage.trade_volume(agg, self.moved(), active, 0.8, ROUTING, st, 'present_share')
        self.assertEqual({a: round(b, 9) for a, b in full.items()}, {a: round(b, 9) for a, b in fade.items()})

    def test_unknown_mode_rejected(self):
        agg, st, active = team(True)
        with self.assertRaises(ValueError):
            usage.trade_volume(agg, self.moved(), active, 0.8, ROUTING, st, 'half')


class QuestionableRoutingTest(unittest.TestCase):
    def setUp(self):
        agg, st, fd = team(gone_after_week1=False)
        self.agg, self.st = agg, st
        fd = pd.concat([fd, pd.DataFrame(dict(Nickname=['Moved WR'], Position=['WR'], Team=['AAA'], Inj=['Q'],
                                              Full=['Moved WR'], Key=[data.norm_name('Moved WR')]))], ignore_index=True)
        self.fd = fd
        self.inj = dict(questionable_routing=True, questionable_inactive_prob=0.45, redistribute_share=0.8,
                        absent_mode='present_share')

    def test_off_returns_nothing(self):
        self.assertEqual(project.questionable_routes(self.fd, self.agg, self.st, dict(self.inj, questionable_routing=False),
                                                     ROUTING, 42, 1000), ({}, {}))

    def test_sit_share_and_gains_match_an_out_player(self):
        sits, gain = project.questionable_routes(self.fd, self.agg, self.st, self.inj, ROUTING, 42, 20000)
        q = data.norm_name('Moved WR')
        self.assertEqual(list(sits), [q])
        self.assertAlmostEqual(sits[q].mean(), 0.45, delta=0.01)
        out_t, _ = usage.redistribute_out(self.agg, self.fd[self.fd.Key == q], self.fd, 0.8, self.st, 'present_share',
                                          ROUTING)
        self.assertEqual(gain[q][0], out_t)
        self.assertAlmostEqual(gain[q][0][data.norm_name('Wide One')], 8.0)
        again, _ = project.questionable_routes(self.fd, self.agg, self.st, self.inj, ROUTING, 42, 20000)
        np.testing.assert_array_equal(again[q], sits[q])           # fixed by the seed


def lineup_df():
    """Team AAA (QB, 2 WR, TE) vs BBB (3 RB, WR, TE, WR); DST CCC. The best FLEX is BBB's TE."""
    p = [('QB A', 'QB', 'AAA', 'BBB', 10), ('WR A1', 'WR', 'AAA', 'BBB', 9), ('WR A2', 'WR', 'AAA', 'BBB', 8),
         ('TE A', 'TE', 'AAA', 'BBB', 7), ('RB B1', 'RB', 'BBB', 'AAA', 9), ('RB B2', 'RB', 'BBB', 'AAA', 8),
         ('WR B1', 'WR', 'BBB', 'AAA', 7), ('TE B', 'TE', 'BBB', 'AAA', 6), ('RB B3', 'RB', 'BBB', 'AAA', 2),
         ('WR B2', 'WR', 'BBB', 'AAA', 1), ('DST C', 'D', 'CCC', 'DDD', 5)]
    df = pd.DataFrame(p, columns=['Name', 'Pos', 'Team', 'Opp', 'obj'])
    return df.assign(Salary=5000)


ROSTER = dict(salary_cap=60000, max_per_team=4, slots=['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF'],
              flex=['RB', 'WR', 'TE'])
OPT = dict(max_overlap=9, leverage=dict(enabled=False, max_lineup_own=0), min_salary=0, exposure_cap=25)
RULE = dict(receivers=2, bring_back=1, require=[], extra=set())


class FlexTeTest(unittest.TestCase):
    def solve(self, te_flex):
        df = lineup_df()
        cap, use = {i: 25 for i in df.index}, {i: 0 for i in df.index}
        lp = optimize.solve_lineup(df, df.obj.values, 'AAA', RULE, cap, use, [], [], ROSTER, OPT, te_flex=te_flex)
        return sorted(df.Pos[lp])

    def test_te_in_flex_only_when_allowed(self):
        self.assertEqual(self.solve(True).count('TE'), 2)
        self.assertEqual(self.solve(False).count('TE'), 1)


class ForcedQbOverflowTest(unittest.TestCase):
    def test_qb_needs_scaled_to_the_lineup_count(self):
        df = pd.DataFrame(dict(Name=['Q1', 'Q2', 'Q3', 'W'], Pos=['QB', 'QB', 'QB', 'WR']))
        force = optimize.assign_forced(df, {0: 100, 1: 60, 2: 25, 3: 12}, 150, random.Random(1))
        qb_slots = [[s for s, f in force.items() if q in f] for q in (0, 1, 2)]
        self.assertEqual(sum(map(len, qb_slots)), 150)                         # every lineup, once
        self.assertEqual(len(set().union(*map(set, qb_slots))), 150)           # disjoint
        self.assertEqual([len(s) for s in qb_slots], [81, 49, 20])             # 185 -> 150 in proportion
        self.assertEqual(sum(3 in f for f in force.values()), 12)              # non-QBs untouched

    def test_no_change_when_they_fit(self):
        df = pd.DataFrame(dict(Name=['Q1', 'Q2'], Pos=['QB', 'QB']))
        force = optimize.assign_forced(df, {0: 30, 1: 20}, 150, random.Random(1))
        self.assertEqual([sum(q in f for f in force.values()) for q in (0, 1)], [30, 20])


class DiffPlayersTest(unittest.TestCase):
    def test_added_removed_tags_salary(self):
        base = dict(Nickname=['A', 'B', 'C'], Team='AAA', Position='WR', FPPG=1.0)
        old = pd.DataFrame(dict(base, Id=['1', '2', '3'], Salary=[5000, 6000, 7000], **{'Injury Indicator': ['', 'Q', '']}))
        new = pd.DataFrame(dict(base, Nickname=['A', 'B', 'D'], Id=['1', '2', '4'], Salary=[5100, 6000, 4000],
                                **{'Injury Indicator': ['', 'O', '']}))
        prep = lambda d: d.assign(**{'Injury Indicator': d['Injury Indicator'].fillna(''),
                                     'Player': d.Nickname + ' (AAA WR)'}).set_index('Id')
        d = diff_players.diff(prep(old), prep(new))
        self.assertEqual(list(d['added'].Player), ['D (AAA WR)'])
        self.assertEqual(list(d['removed'].Player), ['C (AAA WR)'])
        self.assertEqual(d['tags'][['was', 'now']].values.tolist(), [['Q', 'O']])
        self.assertEqual(d['salary'][['was', 'now']].values.tolist(), [[5000, 5100]])


if __name__ == '__main__':
    unittest.main()
