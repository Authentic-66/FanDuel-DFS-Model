"""Nov 16 operational changes: FanDuel 'NA' (official inactive) read as out, and config/<week>/auto.toml merged under
week.toml (status lists joined, [status] active removes names, week.toml wins on other keys)."""
import os
import tempfile
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import config, data


def slate(tags):
    path = os.path.join(tempfile.mkdtemp(), 'fd_players.csv')
    pd.DataFrame([dict(Id=f'1-{k}', Position='WR', **{'First Name': n, 'Last Name': 'X', 'Nickname': n + ' X'},
                       FPPG=10.0, Salary=6000, Team='AAA', **{'Injury Indicator': t})
                  for k, (n, t) in enumerate(tags)]).to_csv(path, index=False)
    return path


class NaInactiveTest(unittest.TestCase):
    def test_na_is_out_by_default(self):
        fd = data.load_slate(slate([('A', 'NA'), ('B', ''), ('C', 'Q')]), {'out': ['Z'], 'questionable': []})
        self.assertEqual(list(fd.Inj), ['O', '', ''])

    def test_pin_keeps_old_reading(self):
        fd = data.load_slate(slate([('A', 'NA'), ('B', '')]), {'out': ['Z'], 'questionable': [], 'na_inactive': False})
        self.assertEqual(list(fd.Inj), ['', ''])


class AutoTomlTest(unittest.TestCase):
    def test_merge(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, 'config', '2026-w11'))
        with open(os.path.join(root, 'config', 'defaults.toml'), 'w') as f:
            f.write('[optimizer]\nexposure_cap = 25\n')
        with open(os.path.join(root, 'config', '2026-w11', 'auto.toml'), 'w') as f:
            f.write('[status]\nout = ["A", "B"]\nquestionable = ["C", "D"]\n[stacks.weights]\nSF = 20\nBUF = 18\n')
        with open(os.path.join(root, 'config', '2026-w11', 'week.toml'), 'w') as f:
            f.write('[status]\nout = ["D", "E"]\nquestionable = []\nactive = ["B"]\n[stacks.weights]\nSF = 0\n')
        cfg = config.load_config(config.Week('2026-w11', root))
        self.assertEqual(cfg['status']['out'], ['A', 'D', 'E'])        # joined, B cleared by active
        self.assertEqual(cfg['status']['questionable'], ['C'])        # D: week.toml out beats auto Q
        self.assertEqual(cfg['stacks']['weights'], {'SF': 0, 'BUF': 18})   # week.toml wins per team

    def test_no_auto_file_unchanged(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, 'config', '2026-w11'))
        with open(os.path.join(root, 'config', 'defaults.toml'), 'w') as f:
            f.write('[optimizer]\nexposure_cap = 25\n')
        with open(os.path.join(root, 'config', '2026-w11', 'week.toml'), 'w') as f:
            f.write('[status]\nout = ["D"]\nquestionable = []\n')
        cfg = config.load_config(config.Week('2026-w11', root))
        self.assertEqual(cfg['status']['out'], ['D'])


if __name__ == '__main__':
    unittest.main()
