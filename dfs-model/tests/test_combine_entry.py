"""Week-9 entered split (Doug, Nov 3): evenly spaced picks and the upload checks."""
import os
import sys
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import combine_entry as C  # noqa: E402

HEADER = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF']


def slate():
    rows = [('q', 'QB', 9000), ('r1', 'RB', 7000), ('r2', 'RB', 6000), ('w1', 'WR', 7000), ('w2', 'WR', 6000),
            ('w3', 'WR', 5000), ('t', 'TE', 5000), ('f', 'RB', 5000), ('d', 'D', 4000), ('x', 'WR', 9000)]
    return pd.DataFrame({'Id': [r[0] for r in rows], 'Position': [r[1] for r in rows], 'Salary': [r[2] for r in rows],
                         'Nickname': [r[0].upper() for r in rows], 'Injury Indicator': [None] * len(rows)})


CFG = {'prefs': {'red': ['X']}, 'roster': {'salary_cap': 60000}, 'status': {'out': [], 'questionable': []}}
OK = ['q', 'r1', 'r2', 'w1', 'w2', 'w3', 't', 'f', 'd']


class CombineTest(unittest.TestCase):
    def test_spaced(self):
        self.assertEqual(C.spaced(75, 150), list(range(0, 150, 2)))
        self.assertEqual(len(C.spaced(74, 147)), 74)
        with self.assertRaises(SystemExit):
            C.spaced(80, 75)

    def test_checks(self):
        self.assertEqual(C.check([OK], HEADER, slate(), CFG), [])
        bad = C.check([OK, OK, ['q', 'r1', 'r2', 'w1', 'w2', 'x', 't', 'f', 'd'], ['r1', 'q'] + OK[2:]],
                      HEADER, slate(), CFG)
        text = ' '.join(bad)
        self.assertIn('duplicate', text)
        self.assertIn('red player', text)
        self.assertIn('in the QB slot', text)
        df = slate()
        df.loc[df.Id == 'f', 'Injury Indicator'] = 'O'
        self.assertIn('Out / IR', ' '.join(C.check([OK], HEADER, df, CFG)))


if __name__ == '__main__':
    unittest.main()
