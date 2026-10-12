"""[[status.trade]]: data.trades validation and usage.trade_volume."""
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import data, usage
from test_usage import rows


def slate():
    fd = pd.DataFrame(dict(Nickname=['Star WR', 'Old Mate', 'New One', 'New Two', 'New Back'],
                           Position=['WR', 'WR', 'WR', 'WR', 'RB'], Team=['OLD', 'OLD', 'NEW', 'NEW', 'NEW'], Inj=''))
    fd['Full'] = fd.Nickname
    fd['Key'] = fd.Nickname.map(data.norm_name)
    return fd


def stats():
    recs = []
    for name, team, tgt, car in [('Star WR', 'OLD', 10, 0), ('Old Mate', 'OLD', 5, 0), ('New One', 'NEW', 12, 0),
                                 ('New Two', 'NEW', 6, 0), ('New Back', 'NEW', 2, 15)]:
        recs += [dict(k=data.norm_name(name), player_id=name, week=w, team=team, targets=tgt, carries=car) for w in (1, 2)]
    return usage.aggregate(rows(*recs))


def trade(**changes):
    return {'player': 'Star WR', 'from': 'OLD', 'to': 'NEW', 'new_target_share': 0.2, **changes}


class TradeTest(unittest.TestCase):
    def test_missing_share_stops(self):
        no_share = {k: v for k, v in trade().items() if k != 'new_target_share'}
        with self.assertRaisesRegex(ValueError, 'set new_target_share'):
            data.trades(slate(), {'trade': [no_share]})
        with self.assertRaisesRegex(ValueError, 'missing to'):
            data.trades(slate(), {'trade': [trade(to='')]})
        with self.assertRaisesRegex(ValueError, 'FanDuel lists him on OLD'):
            data.trades(slate(), {'trade': [trade(**{'from': 'ELS'})]})
        off_slate = data.trades(slate(), {'trade': [{'player': 'Gone Guy Jr.', 'from': 'OLD', 'to': 'BYE'}]})
        self.assertEqual((off_slate.Key[0], off_slate.share[0]), ('goneguy', 0.0))   # no share needed off the slate
        self.assertEqual(len(data.trades(slate(), {})), 0)

    def test_volume_moves_on_both_teams(self):
        fd, agg = slate(), stats()
        moved = data.trades(fd, {'trade': [trade(first_week_factor=0.5)]})
        self.assertEqual((moved.share[0], moved.factor[0]), (0.2, 0.5))
        fd.loc[fd.Key == moved.Key[0], 'Team'] = 'NEW'          # what load_slate does
        xt, xc = usage.trade_volume(agg, moved, fd, 0.8)
        k = data.norm_name
        self.assertAlmostEqual(xt[k('Old Mate')], 0.8 * 10)      # old team: handed out in full
        # new team: 20 targets a game between the three; he takes 0.2 * 0.5 of them, pro rata
        self.assertAlmostEqual(xt[k('New One')], -1.2)
        self.assertAlmostEqual(xt[k('New Two')], -0.6)
        self.assertAlmostEqual(xt[k('New Back')], -0.2)
        self.assertAlmostEqual(xt[k('Star WR')], 2.0 - 10)       # from 10 a game to 2
        self.assertEqual(xc, {})
        self.assertEqual(usage.team_mismatches(agg, fd, moved), [])
        self.assertEqual(usage.team_mismatches(agg, fd, moved.iloc[:0]), [('Star WR', 'NEW', 'OLD')])

    def test_traded_player_who_is_out_only_leaves_his_old_team(self):
        fd, agg = slate(), stats()
        status = {'out': ['Star WR'], 'questionable': [], 'trade': [trade()]}
        moved = data.trades(fd, status)
        fd.loc[fd.Key == moved.Key[0], ['Team', 'Inj']] = ['NEW', 'O']
        self.assertEqual(len(data.newly_out(fd, status)), 0)
        xt, _ = usage.trade_volume(agg, moved, data.active(fd), 0.8)
        self.assertEqual(xt, {data.norm_name('Old Mate'): 8.0})


if __name__ == '__main__':
    unittest.main()
