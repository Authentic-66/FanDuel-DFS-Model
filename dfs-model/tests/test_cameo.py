"""QB cameo rule ([model.qb] cameo_rule, Doug Oct 27): a QB game row under min_attempts is dropped only when a
teammate QB threw more passes in that game. A sole QB with few attempts is still the starter (TB, 2026 week 7:
Mayfield 11 attempts, Daniels 0). "any" = the old rule (every QB row under min_attempts dropped)."""
import os
import tempfile
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import data, usage

COLS = dict(season=2026, season_type='REG', attempts=0, completions=0, passing_yards=0, passing_tds=0,
            passing_interceptions=0, carries=0, rushing_yards=0, rushing_tds=0, targets=0, receptions=0,
            receiving_yards=0, receiving_tds=0)


def load(rule, *recs):
    cfg = {'model': {'season_types': ['REG'], 'qb': {'min_attempts': 15, 'cameo_rule': rule}},
           'teams': {'nflverse_to_fd': {}}}
    df = pd.DataFrame([{**COLS, **r} for r in recs])
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    df.to_csv(path, index=False)
    try:
        return data.load_stats(path, cfg)
    finally:
        os.remove(path)


def qb(name, week, att, team='TB', carries=0):
    return dict(player_id=name, player_display_name=name, position='QB', team=team, week=week, attempts=att,
                carries=carries)


# TB 2026: Daniels started weeks 4-6, Mayfield came back in week 7 (11 attempts, left early; Daniels 0 attempts)
TB = [qb('Jalon Daniels', 4, 27), qb('Jalon Daniels', 5, 25), qb('Jalon Daniels', 6, 43),
      qb('Baker Mayfield', 7, 11, carries=1), qb('Jalon Daniels', 7, 0, carries=2)]


class CameoRuleTest(unittest.TestCase):
    def test_sole_qb_with_low_attempts_is_the_starter(self):
        st = load('backup_only', *TB)
        self.assertEqual(usage.starting_qbs(st), {data.norm_name('Baker Mayfield')})
        kept = set(zip(st.player_display_name, st.week))
        self.assertIn(('Baker Mayfield', 7), kept)
        self.assertNotIn(('Jalon Daniels', 7), kept)      # 0 attempts while Mayfield threw 11: a cameo

    def test_old_rule_dropped_him(self):
        st = load('any', *TB)
        self.assertEqual(usage.starting_qbs(st), {data.norm_name('Jalon Daniels')})

    def test_backup_cameo_still_dropped(self):
        st = load('backup_only', qb('Starter', 7, 35), qb('Backup', 7, 4))
        self.assertEqual(list(st.player_display_name), ['Starter'])

    def test_other_teams_and_weeks_do_not_count(self):
        # a low-attempt QB is not a cameo because a QB on another team, or in another week, threw more
        st = load('backup_only', qb('Sole', 7, 10, team='BAL'), qb('Other', 7, 40, team='BUF'),
                  qb('Sole', 6, 30, team='BAL'))
        self.assertEqual(sorted(zip(st.player_display_name, st.week)), [('Other', 7), ('Sole', 6), ('Sole', 7)])

    def test_tie_is_a_cameo_for_both(self):
        # Doug, Oct 27: a tie for the most attempts is a cameo for both (2025 BAL wk 16 Lamar / Huntley 10 each)
        st = load('backup_only', qb('A', 16, 10, team='BAL'), qb('B', 16, 10, team='BAL'), qb('A', 15, 30, team='BAL'))
        self.assertEqual(list(zip(st.player_display_name, st.week)), [('A', 15)])

    def test_tie_above_min_attempts_kept(self):
        st = load('backup_only', qb('A', 16, 20, team='BAL'), qb('B', 16, 20, team='BAL'))
        self.assertEqual(len(st), 2)

    def test_tie_does_not_count_non_qbs(self):
        # a receiver's trick-play pass is not a QB tie
        st = load('backup_only', qb('Sole', 7, 1, team='BAL'),
                  dict(player_id='wr', player_display_name='Wideout', position='WR', team='BAL', week=7, attempts=1))
        self.assertIn('Sole', set(st.player_display_name))

    def test_bad_rule(self):
        with self.assertRaises(ValueError):
            load('sometimes', *TB)


if __name__ == '__main__':
    unittest.main()
