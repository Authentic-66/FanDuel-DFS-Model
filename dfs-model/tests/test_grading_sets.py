"""[grading] extra_sets: shadow control sets (e.g. week 7's model_cap45) graded beside the pool and the model."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dfs import analyze, config, optimize  # noqa: E402

HEADER = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF']


def ids(start):
    return [f'1-{start + k}' for k in range(9)]


class ExtraSets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.week = config.Week('2026-w07', root=self.tmp.name)
        os.makedirs(self.week.data)
        with open(self.week.results_players, 'w') as f:
            f.write('Player,Roster Position,%Drafted,FPTS,Salary\n')
            for k in range(30):
                f.write(f'P{k} (1-{k}),WR,0.1,{k},5000\n')
        with open(self.week.results_entries, 'w') as f:
            f.write('Rank,EntryId,EntryName,Points,Lineup\n')
            f.write('1,1,me,36,"' + ', '.join(f'X P ({i})' for i in ids(0)) + '"\n')
        for folder, start in [('', 0), ('pool', 10), ('model_cap45', 20)]:
            os.makedirs(os.path.join(self.week.out, folder), exist_ok=True)
            optimize.write_upload(os.path.join(self.week.out, folder, 'upload.csv'), [ids(start)], HEADER)

    def tearDown(self):
        self.tmp.cleanup()

    def test_extra_set_graded(self):
        cfg = {'contest': {'field_size': 0}, 'grading': {'extra_sets': ['model_cap45']}}
        g = analyze.pool_report(self.week, cfg).set_index('set')
        self.assertEqual(list(g.index), ['pool', 'model', 'model_cap45', 'entered'])
        self.assertEqual(g.loc['model_cap45', 'avg'], sum(range(20, 29)))
        self.assertEqual(g.loc['model', 'entered'], 1)
        self.assertEqual(g.loc['model_cap45', 'entered'], 0)

    def test_without_grading_section(self):
        g = analyze.pool_report(self.week, {'contest': {'field_size': 0}})
        self.assertEqual(list(g.set), ['pool', 'model', 'entered'])


if __name__ == '__main__':
    unittest.main()
