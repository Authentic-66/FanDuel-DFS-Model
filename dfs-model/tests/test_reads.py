"""Doug's reads graded by colour and source (analyze.read_groups / read_variants / reads_players)."""
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import analyze

CFG = dict(optimizer=dict(min_proj=4),
           prefs=dict(starters_only=True, red=['Bad WR'], red_teams=['ZZZ'], yellow={'So So': 20}, green={}, green_floor={}),
           shadow=dict(reviewed='', red=[], yellow={'Other': 10}, green={'Like Him': 6}, green_floor={'Like Him': 5},
                       trade={'Moved': {}}))


class ReadsTest(unittest.TestCase):
    def test_groups_split_colour_and_source(self):
        got = [(c, s) for c, s, _ in analyze.read_groups(CFG)]
        self.assertEqual(got, [('red', 'applied'), ('yellow', 'applied'), ('yellow', 'shadow'), ('green', 'shadow')])

    def test_each_variant_changes_one_group(self):
        v = {(c, s): p for c, s, _, p in analyze.read_variants(CFG)}
        no_red = v['red', 'applied']
        self.assertEqual((no_red['red'], no_red['red_teams'], no_red['yellow']), ([], [], {'So So': 20}))
        self.assertEqual(v['yellow', 'applied']['yellow'], {})
        self.assertEqual(v['yellow', 'shadow']['yellow'], {'So So': 20, 'Other': 10})
        green = v['green', 'shadow']
        self.assertEqual((green['green'], green['green_floor'], green['red']), ({'Like Him': 6}, {'Like Him': 5}, ['Bad WR']))
        self.assertEqual(CFG['prefs']['green'], {})                       # the entered config is untouched

    def test_players_table(self):
        proj = pd.DataFrame(dict(Id=list('abcdef'), Name=['Bad WR', 'So So', 'Other', 'Like Him', 'Z Back', 'Z Scrub'],
                                 Pos=['WR', 'WR', 'TE', 'RB', 'RB', 'WR'], Team=['AAA', 'AAA', 'BBB', 'BBB', 'ZZZ', 'ZZZ'],
                                 Proj=[8.0, 12.0, 9.0, 14.0, 10.0, 2.0]))
        actuals = pd.DataFrame(dict(Id=list('abcde'), FPTS=[3.0, 15.0, 4.0, 20.0, 6.0], own_pct=[1.0, 9.0, 3.0, 12.0, 5.0]))
        me = pd.DataFrame(dict(ids=[['b', 'd'], ['b']]))
        t = analyze.reads_players(CFG, proj, actuals, me)
        self.assertEqual(list(t.Name[t.colour == 'red']), ['Bad WR', 'Z Back'])       # the scrub is under min_proj
        s = analyze.reads_summary(t).set_index(['colour', 'source'])
        self.assertEqual((s.actual['red', 'applied'], s.below_proj['red', 'applied']), (4.5, 2))
        self.assertEqual((s.my_lineup_slots['yellow', 'applied'], s.below_proj['green', 'shadow']), (2, 0))


if __name__ == '__main__':
    unittest.main()
