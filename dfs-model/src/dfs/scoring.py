"""FanDuel contest scoring, driven by the [scoring] config section. Works on scalars or numpy arrays."""
import numpy as np


def skill_points(sc, pass_yds=0, pass_td=0, ints=0, rush_yds=0, rush_td=0, rec=0, rec_yds=0, rec_td=0,
                 return_td=0, fumbles_lost=0, two_pt=0):
    pts = (sc['pass_yd'] * pass_yds + sc['pass_td'] * pass_td + sc['interception'] * ints
           + sc['rush_yd'] * rush_yds + sc['rush_td'] * rush_td
           + sc['reception'] * rec + sc['rec_yd'] * rec_yds + sc['rec_td'] * rec_td
           + sc['return_td'] * return_td + sc['fumble_lost'] * fumbles_lost + sc['two_pt'] * two_pt)
    return pts + sc['bonus'] * ((np.asarray(pass_yds) >= sc['bonus_pass_yds']).astype(int)
                                + (np.asarray(rush_yds) >= sc['bonus_rush_yds'])
                                + (np.asarray(rec_yds) >= sc['bonus_rec_yds']))


def points_allowed_tier(dst, pa):
    pa = np.asarray(pa)
    return np.select([pa < b for b in dst['pa_bounds']], dst['pa_points'], dst['pa_else'])


def dst_points(dst, points_allowed, sacks=0, ints=0, fumble_recoveries=0, return_td=0, safeties=0, blocked_kicks=0):
    return (points_allowed_tier(dst, points_allowed) + dst['sack'] * sacks + dst['interception'] * ints
            + dst['fumble_recovery'] * fumble_recoveries + dst['return_td'] * return_td
            + dst['safety'] * safeties + dst['blocked_kick'] * blocked_kicks)


def stats_points(sc, st):
    """Actual FanDuel points for each row of an nflverse stats_player_week frame (skill players)."""
    g = lambda c: st[c].fillna(0) if c in st else 0
    return skill_points(
        sc, pass_yds=g('passing_yards'), pass_td=g('passing_tds'), ints=g('passing_interceptions'),
        rush_yds=g('rushing_yards'), rush_td=g('rushing_tds'), rec=g('receptions'), rec_yds=g('receiving_yards'),
        rec_td=g('receiving_tds'), return_td=g('special_teams_tds'),
        fumbles_lost=g('fumbles_lost_total'),   # includes sack and special-teams fumbles
        two_pt=g('passing_2pt_conversions') + g('rushing_2pt_conversions') + g('receiving_2pt_conversions'))
