"""FanDuel -> nflverse name matching: defensive / specialist players with no offensive volume are skipped
([model] skip_defense_names), so Michael Carter II (PHI CB) no longer matches Michael Carter (TEN RB)."""
import os
import tempfile
import unittest

import _setup  # noqa: F401
import pandas as pd

from dfs import data, usage

COLS = dict(season_type='REG', attempts=0, completions=0, passing_yards=0, passing_tds=0, passing_interceptions=0,
            carries=0, rushing_yards=0, rushing_tds=0, targets=0, receptions=0, receiving_yards=0, receiving_tds=0)


def cfg(skip):
    return {'model': {'season_types': ['REG'], 'qb': {'min_attempts': 5}, 'skip_defense_names': skip},
            'teams': {'nflverse_to_fd': {'JAX': 'JAC'}}}


def stats(*recs):
    """Write nflverse-style weekly rows to a temp csv and load them with data.load_stats (both settings)."""
    df = pd.DataFrame([{**COLS, **r} for r in recs])
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    df.to_csv(path, index=False)
    try:
        return data.load_stats(path, cfg(False)), data.load_stats(path, cfg(True))
    finally:
        os.remove(path)


class NameMatchTest(unittest.TestCase):
    def test_carter_and_carter_ii_share_a_key(self):
        self.assertEqual(data.norm_name('Michael Carter II'), data.norm_name('Michael Carter'))

    def test_carter_ii_cornerback_no_longer_matches(self):
        # 2026: only the PHI cornerback has rows; the TEN running back has not played
        rows = [dict(player_id='cb', player_display_name='Michael Carter II', position='CB', team='PHI', week=w)
                for w in (1, 2, 3, 4)]
        old, new = stats(*rows)
        self.assertEqual(usage.aggregate(old).at['michaelcarter', 'team'], 'PHI')   # the bug
        self.assertNotIn('michaelcarter', usage.aggregate(new).index)              # fixed

    def test_prior_season_running_back_still_wins(self):
        rows = [dict(player_id='rb', player_display_name='Michael Carter', position='RB', team='ARI', week=w,
                     carries=7, targets=3) for w in (1, 2, 3)]
        rows += [dict(player_id='cb', player_display_name='Michael Carter II', position='CB', team='NYJ', week=w)
                 for w in (1, 2, 3, 4, 5)]
        old, new = stats(*rows)
        for st in (old, new):
            agg = usage.aggregate(st)
            self.assertEqual(agg.at['michaelcarter', 'team'], 'ARI')
            self.assertEqual(agg.at['michaelcarter', 'g'], 3)
        self.assertFalse((new.position == 'CB').any())

    def test_two_way_player_kept(self):
        # Travis Hunter is listed CB but has targets: every one of his rows stays, including games without a target
        rows = [dict(player_id='th', player_display_name='Travis Hunter', position='CB', team='JAX', week=1, targets=4),
                dict(player_id='th', player_display_name='Travis Hunter', position='CB', team='JAX', week=2)]
        _, new = stats(*rows)
        self.assertEqual(len(new), 2)
        self.assertEqual(usage.aggregate(new).at['travishunter', 'g'], 2)

    def test_nickname_alias(self):
        # FanDuel "Joshua Palmer" = nflverse "Josh Palmer": [names.aliases] maps the nflverse name to FanDuel's
        df = pd.DataFrame([{**COLS, 'player_id': 'jp', 'player_display_name': 'Josh Palmer', 'position': 'WR',
                            'team': 'BUF', 'week': 1, 'targets': 4}])
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        df.to_csv(path, index=False)
        try:
            plain = data.load_stats(path, cfg(True))
            aliased = data.load_stats(path, {**cfg(True), 'names': {'aliases': {'Josh Palmer': 'Joshua Palmer'}}})
        finally:
            os.remove(path)
        self.assertEqual(plain.k.iloc[0], 'joshpalmer')
        self.assertEqual(aliased.k.iloc[0], data.norm_name('Joshua Palmer'))

    def test_offensive_player_without_volume_kept(self):
        # a fullback or blocking tight end with no touches is still an offensive player
        _, new = stats(dict(player_id='fb', player_display_name='Andrew Beck', position='FB', team='NYJ', week=1))
        self.assertEqual(len(new), 1)


if __name__ == '__main__':
    unittest.main()
