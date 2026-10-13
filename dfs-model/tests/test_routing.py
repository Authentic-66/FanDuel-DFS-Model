"""Injury volume routed by position ([model.injury.position_share]) and the tapered spread ([model.spread] {low, top})."""
import unittest

import _setup  # noqa: F401
import numpy as np
import pandas as pd

from dfs import data, history, project, usage
from test_usage import rows

ROUTING = {'WR': {'tgt_same': 0.8, 'tgt_other': 0.2}, 'RB': {'car_same': 0.9, 'car_other': 0.0, 'tgt_same': 0.5}}
PLAYERS = [('Out WR', 'WR', 10, 2), ('Wide One', 'WR', 6, 0), ('Wide Two', 'WR', 2, 0), ('Tight', 'TE', 4, 0),
           ('Back One', 'RB', 2, 10), ('Back Two', 'RB', 0, 5)]


def setup(out_name):
    fd = pd.DataFrame(dict(Nickname=[p[0] for p in PLAYERS], Position=[p[1] for p in PLAYERS], Team='AAA', Inj=''))
    fd['Full'], fd['Key'] = fd.Nickname, fd.Nickname.map(data.norm_name)
    agg = usage.aggregate(rows(*[dict(k=data.norm_name(n), player_id=n, week=w, team='AAA', position=p, targets=t, carries=c)
                                 for n, p, t, c in PLAYERS for w in (1, 2)]))
    return agg, fd[fd.Nickname == out_name], fd[fd.Nickname != out_name], data.norm_name


class RoutingTest(unittest.TestCase):
    def test_wr_targets_go_mostly_to_wrs(self):
        agg, out, active, k = setup('Out WR')
        xt, xc = usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING)
        self.assertAlmostEqual(xt[k('Wide One')], 0.8 * 10 * 6 / 8)        # 80% of his 10 targets, split 6 : 2
        self.assertAlmostEqual(xt[k('Wide Two')], 0.8 * 10 * 2 / 8)
        self.assertAlmostEqual(xt[k('Tight')], 0.2 * 10 * 4 / 6)           # 20% to the other positions, split 4 : 2
        self.assertAlmostEqual(xt[k('Back One')], 0.2 * 10 * 2 / 6)
        # no rule for a WR's carries: the pro-rata rule, 80% of his 2 carries split 10 : 5 between the backs
        self.assertAlmostEqual(xc[k('Back One')], 0.8 * 2 * 10 / 15)
        old, _ = usage.redistribute_out(agg, out, active, 0.8)             # without routing: everyone pro rata
        self.assertAlmostEqual(old[k('Tight')], 0.8 * 10 * 4 / 14)

    def test_rb_volume_stays_with_the_backs_and_an_empty_group_gets_nothing(self):
        agg, out, active, k = setup('Back One')
        xt, xc = usage.redistribute_out(agg, out, active, 0.8, routing=ROUTING)
        self.assertEqual({key: round(v, 6) for key, v in xc.items() if v}, {k('Back Two'): 9.0})   # 90% of 10 carries
        self.assertEqual(sum(xt.values()), 0)      # the only other back has no targets: that half is not handed out

    def test_trade_routes_the_old_team_the_same_way(self):
        agg, out, active, k = setup('Out WR')
        moved = pd.DataFrame([dict(Key=k('Out WR'), Name='Out WR', Pos='WR', From='AAA', To='BBB', share=0.0, factor=1.0)])
        xt, _ = usage.trade_volume(agg, moved, active, 0.8, ROUTING)
        self.assertAlmostEqual(xt[k('Wide One')], 6.0)
        self.assertAlmostEqual(xt[k('Tight')], 0.2 * 10 * 4 / 6)

    def test_a_traded_player_off_the_slate_still_leaves_his_old_team_volume(self):
        # week 6 2026: Harrison (ARI -> HOU) is not in the FanDuel list because Houston is not on the main slate
        agg, _, active, k = setup('Out WR')
        ranked = dict(ROUTING, WR=dict(ROUTING['WR'], tgt_rank=[0.25, 0.75, 0.0]))
        entry = {'player': 'Out WR', 'position': 'WR', 'from': 'AAA', 'to': 'BBB', 'new_target_share': 0.15,
                 'first_week_factor': 0.7}
        moved = data.trades(active, {'trade': [entry]})
        self.assertEqual((moved.Key[0], moved.Pos[0], moved.share[0]), (k('Out WR'), 'WR', 0.0))   # new-team read inactive
        xt, _ = usage.trade_volume(agg, moved, active, 0.8, ranked)
        self.assertAlmostEqual(xt[k('Wide One')], 0.8 * 10 * 0.25)         # old team: by position, WRs by depth rank
        self.assertAlmostEqual(xt[k('Wide Two')], 0.8 * 10 * 0.75)
        self.assertAlmostEqual(xt[k('Tight')], 0.2 * 10 * 4 / 6)
        self.assertAlmostEqual(sum(xt.values()), 10.0)                     # all of it handed out, nobody loses targets
        self.assertNotIn(k('Out WR'), xt)                                  # and no new-team share for him
        self.assertTrue(all(v >= 0 for v in xt.values()))
        # without `position` it still runs, on the 80% pro-rata rule (he cannot be looked up on the slate)
        moved = data.trades(active, {'trade': [{key: v for key, v in entry.items() if key != 'position'}]})
        xt, _ = usage.trade_volume(agg, moved, active, 0.8, ranked)
        self.assertAlmostEqual(xt[k('Tight')], 0.8 * 10 * 4 / 14)
        self.assertAlmostEqual(sum(xt.values()), 8.0)

    def test_depth_rank_split_inside_the_position(self):
        np.testing.assert_allclose(usage.rank_weights([2, 6, 0, 1], [0.2, 0.3, 0.5]), [0.3, 0.2, 0.25, 0.25])
        np.testing.assert_allclose(usage.rank_weights([2, 6], [0.2, 0.3, 0.5]), [0.6, 0.4])     # unused share rescaled
        np.testing.assert_allclose(usage.rank_weights([4], [0.2, 0.3, 0.5]), [1.0])
        agg, out, active, k = setup('Out WR')
        ranked = dict(ROUTING, WR=dict(ROUTING['WR'], tgt_rank=[0.25, 0.75, 0.0]))
        xt, _ = usage.redistribute_out(agg, out, active, 0.8, routing=ranked)
        self.assertAlmostEqual(xt[k('Wide One')], 0.8 * 10 * 0.25)         # the larger role gets the smaller share
        self.assertAlmostEqual(xt[k('Wide Two')], 0.8 * 10 * 0.75)
        self.assertAlmostEqual(xt[k('Tight')], 0.2 * 10 * 4 / 6)           # the other positions: still pro rata
        moved = pd.DataFrame([dict(Key=k('Out WR'), Name='Out WR', Pos='WR', From='AAA', To='BBB', share=0.0, factor=1.0)])
        self.assertAlmostEqual(usage.trade_volume(agg, moved, active, 0.8, ranked)[0][k('Wide Two')], 6.0)   # trades too

    def test_a_back_with_no_carries_is_reached_by_the_depth_split(self):
        agg, out, active, k = setup('Back One')
        ranked = dict(ROUTING, RB=dict(ROUTING['RB'], tgt_rank=[0.6, 0.3, 0.1]))
        xt, _ = usage.redistribute_out(agg, out, active, 0.8, routing=ranked)
        self.assertAlmostEqual(xt[k('Back Two')], 0.5 * 2)                 # pro rata he got nothing (no targets of his own)


class TaperTest(unittest.TestCase):
    TAPER = {'from': 12.0, 'to': 20.0}

    def test_factor_falls_from_low_to_top(self):
        got = project.spread_factor(np.array([5.0, 12.0, 16.0, 20.0, 30.0]), {'low': 1.4, 'top': 1.0}, self.TAPER)
        np.testing.assert_allclose(got, [1.4, 1.4, 1.2, 1.0, 1.0])
        np.testing.assert_allclose(project.spread_factor(np.array([5.0, 30.0]), 1.3), [1.3, 1.3])

    def test_adjust_widens_each_player_by_his_own_factor(self):
        proj = pd.DataFrame(dict(Name=['Low', 'High'], Pos='RB', Team='AAA', Opp='BBB', Salary=6000, StartingQB=False))
        sims = np.array([[8.0, 10.0, 12.0], [18.0, 20.0, 22.0]])
        m = dict(qb={}, calibration=dict(enabled=False), dst={}, spread=dict(RB={'low': 2.0, 'top': 1.0}), spread_taper=self.TAPER)
        np.testing.assert_allclose(project.adjust(proj, sims, None, m), [[6, 10, 14], [18, 20, 22]])

    def test_fit_taper_widens_only_the_tier_that_needs_it(self):
        rng = np.random.default_rng(3)
        mean = np.r_[np.full(1500, 9.0), np.full(600, 22.0)]
        sims = mean[:, None] + rng.normal(0, 3, (2100, 300))
        actual = mean + np.r_[rng.normal(0, 4.5, 1500), rng.normal(0, 3, 600)]     # only the low tier is too narrow
        spec = history.fit_taper(sims, mean, actual, np.ones(2100), self.TAPER)
        self.assertAlmostEqual(spec['low'], 1.5, delta=0.15)
        self.assertLess(spec['top'], 1.1)
        few = history.fit_taper(sims[:1550], mean[:1550], actual[:1550], np.ones(1550), self.TAPER)   # 50 at 16+
        self.assertEqual(few['low'], few['top'])                                     # too few to taper: one flat factor


if __name__ == '__main__':
    unittest.main()
