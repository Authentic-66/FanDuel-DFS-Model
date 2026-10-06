"""FanDuel injury tags vs config [status] (data.load_slate) and the exclude_questionable rule (optimize.eligible_pool)."""
import os
import tempfile
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import data, optimize

ROWS = [('1-1', 'A', 'WR', 'Q'), ('1-2', 'B', 'WR', 'D'), ('1-3', 'C', 'WR', 'O'), ('1-4', 'D', 'WR', 'IR'),
        ('1-5', 'E', 'WR', '')]


def slate():
    path = os.path.join(tempfile.mkdtemp(), 'fd_players.csv')
    pd.DataFrame([dict(Id=i, Position=p, **{'First Name': n, 'Last Name': 'X', 'Nickname': n + ' X'}, FPPG=10.0,
                       Salary=6000, Team='AAA', **{'Injury Indicator': t or None}) for i, n, p, t in ROWS]).to_csv(path, index=False)
    return path


class StatusTest(unittest.TestCase):
    def test_fd_tags_until_status_filled(self):
        fd = data.load_slate(slate(), {'out': [], 'questionable': []}).set_index('Nickname')
        self.assertEqual(list(fd.Inj), ['Q', 'Q', 'O', 'IR', ''])
        self.assertEqual(list(data.active(fd.reset_index()).Nickname), ['A X', 'B X', 'E X'])

    def test_status_replaces_fd_q_d_tags(self):
        fd = data.load_slate(slate(), {'out': ['A X'], 'questionable': []}).set_index('Nickname')
        self.assertEqual(list(fd.Inj), ['O', '', 'O', 'IR', ''])

    def test_exclude_questionable(self):
        proj = pd.DataFrame(dict(Id=['1', '2', '3'], Name=['q', 'g', 'h'], Pos='WR', Team='AAA', Inj=['Q', 'Q', ''],
                                 Proj=10.0, StartingQB=False))
        prefs = dict(starters_only=False, red=[], red_teams=[], green={'g': 5})
        opt = dict(min_proj=4, exclude_questionable=True)
        self.assertEqual(list(optimize.eligible_pool(proj, prefs, opt).Name), ['g', 'h'])   # green exempt
        opt['exclude_questionable'] = False
        self.assertEqual(len(optimize.eligible_pool(proj, prefs, opt)), 3)


if __name__ == '__main__':
    unittest.main()
