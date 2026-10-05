"""Week paths and config loading: config/defaults.toml deep-merged with config/<week>/week.toml."""
import copy
import os
import re
import tomllib
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_WEEK = '2026-w04'


@dataclass(frozen=True)
class Week:
    """All file locations for one slate, keyed by its folder name (e.g. 2026-w04)."""
    name: str
    root: str = ROOT

    @property
    def season(self):
        return int(re.match(r'(\d{4})-w(\d+)$', self.name).group(1))

    @property
    def number(self):
        return int(re.match(r'(\d{4})-w(\d+)$', self.name).group(2))

    @property
    def data(self): return os.path.join(self.root, 'data', self.name)
    @property
    def cache(self): return os.path.join(self.root, 'data', 'cache')
    @property
    def out(self): return os.path.join(self.root, 'weeks', self.name)
    @property
    def config_dir(self): return os.path.join(self.root, 'config', self.name)
    @property
    def fd_players(self): return os.path.join(self.data, 'fd_players.csv')
    @property
    def lines(self): return os.path.join(self.data, 'lines.csv')
    @property
    def results_players(self): return os.path.join(self.data, 'results_players.csv')
    @property
    def results_entries(self): return os.path.join(self.data, 'results_my_entries.csv')
    @property
    def proj(self): return os.path.join(self.out, 'proj.csv')
    @property
    def sims(self): return os.path.join(self.out, 'sims.npy')

    def stats(self, season=None):
        return os.path.join(self.cache, f'stats_player_week_{season or self.season}.csv')

    def output(self, filename):
        os.makedirs(self.out, exist_ok=True)
        return os.path.join(self.out, filename)


def current_week(name=None):
    return Week(name or os.environ.get('DFS_WEEK', DEFAULT_WEEK))


def deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _read_toml(path):
    with open(path, 'rb') as f:
        return tomllib.load(f)


WEEK_DEFAULTS = {
    'status': {'out': [], 'questionable': []},
    'overrides': {},
    'prefs': {'starters_only': True, 'red': [], 'red_teams': [], 'yellow': {}, 'green': {}, 'player_cap': {}},
    'stacks': {'weights': {}, 'rules': {}},
    'contest': {'field_size': 0, 'guru': []},
}


def load_config(week, **overrides):
    """defaults.toml <- week.toml <- keyword overrides (nested dicts, e.g. model={'prior_blend': {...}})."""
    cfg = deep_merge(_read_toml(os.path.join(week.root, 'config', 'defaults.toml')), WEEK_DEFAULTS)
    week_file = os.path.join(week.config_dir, 'week.toml')
    if os.path.exists(week_file):
        cfg = deep_merge(cfg, _read_toml(week_file))
    return deep_merge(cfg, overrides)


def cli(doc, extra_args=None):
    """Parse --week (default: DFS_WEEK env, else DEFAULT_WEEK) for the src/*.py scripts. Returns (week, cfg, args)."""
    import argparse
    ap = argparse.ArgumentParser(description=doc)
    ap.add_argument('--week', help='week folder, e.g. 2026-w05 (default: $DFS_WEEK)')
    for args, kwargs in extra_args or []:
        ap.add_argument(*args, **kwargs)
    a = ap.parse_args()
    week = current_week(a.week)
    return week, load_config(week), a
