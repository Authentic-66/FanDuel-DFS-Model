# Role guard: recent-role switches (Doug, Nov 3 2026)

Doug's spec: build the three switches proposed on Nov 3 (CLAUDE.md "Role guard and injury-driven role changes"), off by
default; history-test on 2023-25 (bias and error for the players each switch changes) and rebuild weeks 5-8 (four
numbers + money as-if); per switch, players changed per week and a yes / no. **Adopt only if it improves calibration
in history and doesn't hurt weeks 5-8.** Nothing is on until Doug says so.

## 1. What was built (all OFF in defaults.toml `[model.role_guard]`)

| Switch | Setting | What it does |
|---|---|---|
| 1 promotion | `promotion = true` (`promotion_games = 2`, `promotion_snap_share = 0.5`) | A WR / TE the guard would zero for under 3 targets + carries a game is kept if (a) his own volume + what he inherits from teammates ruled OUT this week (`GainedVol`) is 3+, or (b) he averaged 3+ over the team's last 2 games, or (c) he played 50%+ of the snaps in the team's last game. |
| 2 snap projection | `snap_projection = true` (`snap_min_share = 0.5`) | A no-data player (active, no stat row this season) with 50%+ snaps last game keeps his fallback projection x (last-game snap share / prior-season share, max 1). |
| 3 role drop | `role_drop_action = "flag"` (default) or `"scale"` (`role_drop_max = 0.10`, `role_drop_min_avg = 0.30`) | Flag: players active last game with under 10% of snaps after averaging 30%+, not tagged Q / O, are printed as a WARNING and get a `RoleDrop` note in proj.csv (and the review sheet). `"scale"` also multiplies their draws by (mean snap share over the team's last 2 games) / (earlier average), max 1. |

Code: `src/dfs/snaps.py` (snap features), `project.guard_rescue`, `project.role_drop`, `project.role_guard`
(rescues applied), `pool.passes_role_guard` (a rescued player is a valid filler only when a switch is on);
`fetch_stats.py` now also downloads `snap_counts_<season>.csv`; history test `src/fit_role_guard.py`; unit tests
`tests/test_role_guard_switches.py`. New proj.csv columns (reporting): LastSnap, ActiveLast, AvgSnap, Recent2Snap,
RecentVol, PriorSnap, GuardRescue, RoleDrop.

**Switches off = no change:** weeks 7, 8 and 9 rebuild with projections and draws identical to the archived files;
weeks 5-6 (guard pinned off) give identical draws before and after the change (they already differed from their
archive before it). Week 9's proj.csv was rewritten with the new columns: Proj and Own_proj identical.

## 2. History, 2023-25 (`python src/fit_role_guard.py --week 2026-w09`)

Weeks 4-18 of each season. Population = every RB / WR / TE with a snap-count row in the game (active), projected as
model.py does with the week-9 settings (usage from earlier weeks + prior-season blend, Vegas totals, routing of players
with 3+ targets + carries a game who were absent, FanDuel-FPPG fallback = prior-season points a game, calibration, WR
correction). The guard is then applied four ways on the same draws, so only the switch differs. 1,000 draws a player.
Bias = projection minus actual FanDuel points.

| Switch | Changed a week | n | Actual | As live: proj / bias / RMSE | With switch: proj / bias / RMSE |
|---|---|---|---|---|---|
| 1 promotion, all | 26.1 (15-44) | 1,175 | 3.29 | 0.00 / -3.29 / 5.29 | 3.29 / **-0.00** / **3.99** |
| 2023 / 2024 / 2025 | 26.3 / 24.7 / 27.3 | 395 / 371 / 409 | 3.25 / 3.48 / 3.15 | bias -3.25 / -3.48 / -3.15 | bias +0.05 / -0.10 / +0.04; RMSE 5.21 -> 3.98, 5.62 -> 4.17, 5.04 -> 3.83 |
| promoted and projected 4+ (lineup-relevant) | | 304 | 4.64 | 0.00 / -4.64 / 6.72 | 4.65 / +0.01 / 4.85 |
| by test: inherits / last 2 games / snaps / snaps only | | 140 / 471 / 924 / 622 | 5.14 / 3.80 / 3.35 / 2.77 | | bias -0.71 / -0.22 / -0.14 / +0.15 |
| by position: TE / WR | | 570 / 605 | 2.96 / 3.60 | | bias +0.06 / -0.06 |
| 2 snap projection | 0.04 | 2 | 1.75 | 0.00 | 1.50 (fires twice in three seasons) |
| 3 role drop, scale | 1.0 | 44 | 2.73 | 6.22 / +3.49 / 5.68 | 1.96 / **-0.77** / **3.98** |
| 2023 / 2024 / 2025 | | 14 / 15 / 15 | 3.10 / 3.41 / 1.72 | bias +2.60 / +2.70 / +5.09 | bias -1.66 / -0.98 / +0.27; RMSE 5.05 -> 4.53, 5.76 -> 4.41, 6.13 -> 2.79 |
| 3 role drop, flag (as live) | 2.4 | 110 | 1.89 | 2.58 / +0.68 | (flag only) |

The guard still does its job on the rest: of 6,377 guarded player-weeks, the 1,175 that promotion keeps scored 3.29 a
game (8.8% scored 10+); the 4,134 it still zeroes for role scored 1.29 (1.9% scored 10+); no-data players 0.71.

Caveats: (1) the history population knows who was active (snap rows); the live run doesn't until inactives, but it
already projects every untagged player as active, so this matches the Sunday final run. (2) History has no injury
tags, so switch 3's history set includes players hurt early in their last game (St. Brown 2025 wk 14: 6% snaps, then
12.2 points; scaled to 9.1). Live, the flag skips Q / O-tagged players, but a player hurt early who is NOT tagged the
next week still fires (Skattebo and Hockenson, week 7 2026: see section 3). (3) Switch 3's sample is small (44)
though the direction holds in all three seasons.

## 3. Weeks 5-8 lineup rebuilds

In-process, as entered (week.toml pins) except the guard is ON in weeks 5-6 for every run (pinned off there), so the
baseline is the guard as live with the switches off. Each variant turns one switch on; same draws for every
unchanged player. Ranks from the field files; money as-if = week-7 Pooch Punt tiers by field share ($0.25 top 1.75%,
$0.15 3.7%, $0.12 11.7%, $0.10 48.2%; ranks above the $0.25 tier counted at $0.25).

| Run | Avg wk 5 / 6 / 7 / 8 | Mean vs base | Top 10% | Top 1% | Best wk 5 / 6 / 7 / 8 | Money as-if | Lineups same as base |
|---|---|---|---|---|---|---|---|
| Base (guard as live) | 111.88 / 103.32 / 100.90 / 106.26 | | 35 (8/6/11/10) | 0 | 179.0 / 149.1 / 151.4 / 190.4 | $19.42 | |
| 1 promotion | 111.95 / 102.02 / 100.31 / 106.91 | **-0.29** (+0.08 / -1.30 / -0.59 / +0.64) | 34 (7/4/11/12) | **1** (wk 8) | 179.0 / 149.1 / 155.8 / 197.8 | **$20.17** (+0.80 / +0.08 / -0.51 / +0.38) | 33 / 44 / 16 / 36 |
| 2 snap projection | identical | 0 | 35 | 0 | identical | $19.42 | 150 each week (0 players changed) |
| 3 role drop scale | identical | 0 | 35 | 0 | identical | $19.42 | 150 each week (3 players changed, none in lineups) |

Players changed a week: promotion 15 / 23 / 24 / 26; role drop scale 0 / 1 / 2 / 0; snap projection 0.

**Live check of the changed players (2026 weeks 5-8):**
- Promotion, 88 player-weeks: projected 0 (guard) -> 3.58 (switch), scored 2.67. **The 31 it lifts to 4+ (the ones
  that can enter lineups): projected 5.09, scored 3.01** (history: 4.65 vs 4.64). Hits: Kyle Williams wk 8 12.3 / 10.8,
  Tez Johnson wk 7 6.6 / 11.7, Parkinson 5.3 / 11.6 and 6.1 / 7.3; misses: Jennings 6.5 / 0, Wetjen 5.1 / 0, Ertz 4.5 /
  0, Tez Johnson wk 8 7.0 / 0, Ridley 5.7 / 1.5.
- Role drop scale, 3: Mumpfield wk 6 5.3 -> 1.8 (scored 2.5, right); **Skattebo wk 7 10.9 -> 6.2 (scored 21.6) and
  Hockenson wk 7 7.8 -> 4.4 (scored 11.5), both wrong**: each had left his previous game hurt (8% / 3% snaps) and
  wasn't tagged the next week.

## 4. Week 9 now (prelim, in-process)

- Switch 1: 11 players change; 2 enter the optimizer pool (Eli Raridon NE TE 0 -> 5.4, Kyle Williams NE WR 0 -> 5.0);
  others stay under 4 (Noah Gray 4.0 is at the line, Davis Allen 3.9, Troy Franklin 3.8, Brandin Cooks 3.4, Elijah
  Higgins 3.4, Spann-Ford 3.2). Kirk is switch 2's case and stays 0 (30% snaps in his one SF game).
- Switch 2: 0 players.
- Switch 3 flag: Emanuel Wilson (SEA RB, 11.4: 40% -> 0%), Lambert-Smith (LAC WR, 3.3), Cody White (LV WR, 3.7). With
  "scale": Wilson 11.0 -> 6.8, out of the pool (SEA RB1 by projection becomes Charbonnet).

## 5. Decision (Doug, Nov 3)

**Promotion ON from week 9** (weeks 4-8 pinned off; weeks 7-8 checked identical). **Snap projection NO. Role drop:
flag only, no scaling.** Kill rule: each weekly review reports the players promotion lifted to 4+ (projected vs
actual); if they under-score by 1.5+ points on average over weeks 9-10 combined, promotion goes off and Doug is told.

## 6. Recommendation as made (before the decision)

| Switch | History calibration | Weeks 5-8 | Recommendation |
|---|---|---|---|
| 1 promotion | **Better** every season (bias -3.29 -> 0.00, RMSE 5.29 -> 3.99; 4+ group calibrated) | Mixed: average -0.29 a lineup (2 weeks down, 2 up), top-10% 34 vs 35, top-1% 1 vs 0, best up 2 weeks, money +$0.75; live 4+ promoted players over-projected (5.09 vs 3.01, n 31) | **Yes, narrowly**: passes both prongs of the rule (history better; weeks 5-8 not clearly hurt: the average loss is within the 1-2 point reshuffle noise of a 26-player change, and money / top-1% / best go the other way). Watch the promoted players' scores weekly; if the live over-projection holds for 2-3 weeks, turn it off. |
| 2 snap projection | Fires twice in three seasons | No change any week | **No**: it does nothing (active players with no stat row almost never play 50%+ of snaps). Leave the code off. |
| 3 role drop scale | Better every season (bias +3.49 -> -0.77, RMSE 5.68 -> 3.98; n 44) | Lineups identical; but 2 of 3 live cases wrong by 10-15 points (Skattebo, Hockenson: hurt the game before, untagged) | **No** for the scaling: the sample is small and the live misses are the in-game-injury case the rule can't tell apart. **Keep the flag** (warning + RoleDrop column, already live): Doug reds or reads the flagged player. |

To turn promotion on for Friday: `config/defaults.toml` `[model.role_guard] promotion = true` (and pin
`promotion = false` in weeks 4-8 week.toml so they re-run as entered), then re-run model.py and the sets.
