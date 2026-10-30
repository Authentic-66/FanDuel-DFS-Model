# CLAUDE.md — dfs-model

## What this is
Doug's FanDuel NFL DFS model for the **Sunday main-slate "Pooch Punt"** GPP ($0.05 entry, up to 150 entries, ~600k-entry field,
guaranteed overlay). Goal: maximize chance of top finishes, not average score. Built in a claude.ai chat Sept 30–Oct 4 2026
(Phase 1); this repo is where Phase 2 happens. Doug also runs a Benter-style horse racing model (separate repo, Authentic-66)
and thinks in those terms: fundamentals model + market/public overlay, calibration, backtesting.

## Contest scoring (FanDuel, verified from contest rules screenshot)
- Pass yd 0.04, pass TD 4, INT -1; rush/rec yd 0.1; rush/rec/return TD 6; reception 0.5 (half PPR); fumble lost -2; 2-pt 2.
- **Bonuses: +3 for 100+ rush yds, +3 for 100+ rec yds, +3 for 300+ pass yds.**
- DST: sack 1, INT 2, fumble rec 2, return TD 6, safety 2, blocked kick 2; points-allowed tiers (0:+10, 1-6:+7, 7-13:+4,
  14-20:+1, 21-27:0, 28-34:-1, 35+:-4). Points allowed counts only offensive TDs/2-pt/XP/FG allowed by the defense.
- Roster: QB, RB, RB, WR, WR, WR, TE, FLEX (RB/WR/TE), DEF. Cap $60,000. Max 4 players from one NFL team.
- **Upload CSV header must be exactly `QB,RB,RB,WR,WR,WR,TE,FLEX,DEF`** with FanDuel player Ids. pandas mangles duplicate
  headers (RB.1, WR.1) when re-reading a CSV — write with the csv module or fix the header (this broke an upload in week 4).

## Config (all rules and tunables live here, not in code)
- `config/defaults.toml` — rules that hold week to week: `[scoring]`, `[roster]`, `[teams]`, `[model.*]` (sim count/seed,
  league priors, noise, correlation, DST, injury handling, `[model.prior_blend]`), `[optimizer]` (Doug's standing rules:
  exposure cap, objective weight, overlap, starters depth, yellow/green formulas, default stack shape).
- `[ownership]` (model settings) and `[optimizer.leverage]` (off by default: `own_weight` points per 1% owned,
  `max_lineup_own`, `stack_exponent`) also live in defaults.toml; turn leverage on per week in week.toml.
- `config/<week>/week.toml` — deep-merged over defaults (any default can be overridden for one week): `[status]` OUT/Q
  (+ `[status.starting_qb]` TEAM = "Name": Doug's starting-QB call, overrides the last-game-attempts default),
  `[overrides]` Doug's reads, `[prefs]` red/red_teams/yellow/green/player_cap/starters_only (+ `[prefs.green_floor]`
  per-player green floor instead of 12; `[prefs] green_mode` = "floor" (default: forced minimum) or "boost" (nothing
  forced; green players' objective value and green QBs' stack weights x (1 + `green_boost`, 0.15); `green_qb_weight`
  sets the QB stack-weight multiplier separately); `[optimizer] stack_allocation` = "random" (default) or
  "proportional" (stack counts fixed from the weights by largest remainder, tightest teams built first, a team that
  can no longer be stacked hands its lineups to the rest by weight); `optimize.py
  --subdir <name>` writes a run to `weeks/<week>/<name>/` for side-by-side comparisons; `[optimizer] reserve_required = true` holds a stack rule's required player
  back for a green QB's forced stacks, off by default, on in week 5 for Burrow/Chase Brown), `[stacks.weights]` QB-team
  draw weights, `[stacks.rules.<TEAM>]` per-team stack shape (e.g. BUF: `receivers = 1`, `require = ["James Cook III"]`).
  `[stacks] extra_receivers` = named RBs that count as stack receivers for their own QB (off unless listed; week 7:
  McCaffrey, so SF stacks as Purdy + Kittle + CMC); used by the optimizer, proportional allocation and pool mode.
  `[contest]` field_size (for grading); `[contest.guru]` = FanDuel Guru (paid) suggestions pre-lock: per slot (QB, RB1,
  RB2, WR1-3, TE, FLEX, DEF) the 3 players Guru offered + Doug's pick, plus fill_order and adapts. All ~27 suggestions
  are the signal (Guru shows them to every paying user), not just the picks. Doug may send screenshots: transcribe them.
  Parsed/validated by `ownership.guru_table`.
  `[shadow]` = Doug's colour review saved as a record only (never applied; week 5 ran model-only), to score his
  reads against the model after the games.
  New week: copy last week's `week.toml` and edit.
  `[pool]` QB/RB/WR/TE/DST lists (+ `ranked`; `ranked_top = {QB = 10, ...}` = only the first N per list are ranked and
  boosted, the rest are unranked members with no boost; new Oct 29) = Doug's player pool for pool mode (docs/pool_mode.md); settings
  (`max_filler`, `rank_boost`, `raise_cap_to`) in defaults.toml `[pool]`.
  Pool fillers use `[optimizer] exposure_cap` (a model cap change rebuilds the pool too).
  `[grading] extra_sets` = extra lineup folders under `weeks/<week>/` graded beside pool and model in `pool/grade.csv`
  (week 7: `model_cap45`, the shadow control).
  Salary-floor relief is `exposure_cap + floor_cap_overflow`: +2 from week 8 (Doug, Oct 26); week 7 used +3 (pinned in its
  week.toml), so at cap 27 players reached 30.

## Pipeline (`src/` scripts are thin CLIs over the `src/dfs/` package; all take `--week`, default `$DFS_WEEK`)
- `dfs/config.py` — `Week` paths (data/, weeks/, config/, stats cache by season) and config loading.
- `dfs/scoring.py` — contest scoring from config; `stats_points` turns nflverse rows into FanDuel points (matches FanDuel
  FPPG exactly; tested) so any historical week can be graded.
- `dfs/data.py` — slate (status applied, or FanDuel Q/D tags until [status] is filled; missing FPPG -> 0), Vegas lines -> implied totals, nflverse stats (FanDuel team
  codes, all positions kept: Travis Hunter is listed as CB). `before_week` stops future weeks leaking into re-runs.
- `dfs/usage.py` — per-player totals keyed by name (name collisions like DJ Turner WR/CB resolved by player_id, offensive
  volume wins), prior-season blend, 80% redistribution of newly-OUT players' targets/carries, starting QB = most attempts
  in each team's latest game.
- `dfs/sim.py` + `dfs/project.py` (`model.py`) — implied totals -> usage x volume elasticity -> 10k correlated sims (team
  factor + shared game factor), Q players zeroed in 25% of sims, DST from opponent total + own FanDuel avg. Deterministic
  for a given seed (game order sorted; the old code depended on Python's hash seed).
- `dfs/overrides.py` (`override.py`) — rescale a player's sims to Doug's mean; errors on unknown names; idempotent.
- `dfs/optimize.py` (`optimize.py`) — sequential MILP (PuLP/CBC), one lineup per sim draw; objective 0.6*mean + 0.4*draw
  (`[optimizer] mean_weight`; 0.4 / 0.6 through week 5).
  `--subdir <name>` writes to `weeks/<week>/<name>/`; `--cap N` overrides `exposure_cap` for that run only (Oct 22).
  Upload written with the csv module (exact duplicate header).
- `dfs/ownership.py` — projected field ownership (`Own_proj`, % of lineups): ridge on logit(%Drafted), refit every run
  from all earlier weeks' results (training rows cached in `weeks/<w>/ownership_train.csv`), shifted per position so
  QB/DST sum to 100%. Added in model.py, override.py (post-override) and optimize.py; also exposure.csv
  (`Own_proj_%`, `Exp_minus_Own`, plus 0-lineup players projected >= 5%) and stacks.csv. `fit_ownership.py` = CV report.
- `dfs/analyze.py` (`analyze_results.py`) — post-slate grading, including Doug's reads: red, yellow and green graded
  separately, applied (`[prefs]`) and shadow (`[shadow]`), per player and as lineups (optimizer re-run as entered, then
  once per colour and source with only that group removed/added; `reads_players.csv`, `reads_lineups.csv`;
  `--no-read-lineups` skips the re-runs). Weeks 4-5 pin `mean_weight = 0.4` so "as entered" still reproduces. `dfs/backtest.py` (`backtest.py`) — Phase 2 tuning;
  `backtest_leverage.py` — leverage settings on an archived slate.
- `dfs/pool.py` (`optimize.py --pool`) — Doug's pool mode: 150 lineups from `[pool]` only, at most 1 filler per lineup
  (role-guard test, never the QB), pool players' cap raised 25 -> 40 when 25 is infeasible; writes `weeks/<week>/pool/`
  (model files untouched); `analyze_results.py` grades it vs the model and the entries (`pool/grade.csv`).
- `fetch_stats.py` — nflverse stats for the week's season and the prior one.
- `diff_players.py <old> <new>` — two FanDuel player lists for the same slate: players added / removed, injury-tag and
  salary changes (week-8 checklist: re-download Friday and Sunday morning and diff against the previous file).
- Tests: `python -m unittest discover -s tests` (stdlib unittest; scoring, usage/blend, ownership, week-4 regression checks).

## Doug's standing rules (current; confirm each week)
- **Starters only**: QB1 (week's starter), RB1, top-3 WR, TE1 per team by projection. Green-listed players always eligible.
- **Exposure cap 25 lineups** for every player and DST (Doug's choice to limit bust risk; raise to 40 only if infeasible).
  Week 7: 27 (Doug, Oct 22: his reds / yellows left too few stackable teams; 25 stalled at 147, 26 at 149 once Kyren /
  Jones became stack receivers). Raise only with Doug's OK, smallest cap that builds 150.
- Stack per lineup: QB + >=2 of his WR/TE + >=1 bring-back from opponent. No DST facing your own offensive players.
- Pull questionable players rather than rely on late swap (he enters via CSV and won't hand-edit 150 lineups):
  `[optimizer] exclude_questionable = true` (default; week 4 sets false, it predates the rule). Before Friday's report
  (`[status]` lists both empty) FanDuel's own tags apply: O/IR out, Q/D = Q (excluded). Once `[status]` has entries,
  FanDuel's Q/D tags are ignored. Excluded Q/OUT players don't hold starter depth: RB1/top-3 WR/TE1 are ranked among
  eligible players, so backups move up (green exempt).
- If he has a free entry, upload 149 (drop lowest projected) and use the free entry separately.
- From week 7: role guard on (WR/TE only), WR implied-total correction on, $59K salary floor with cap relief for
  capped players only: +3 in week 7, **+2 from week 8** (Doug, Oct 26). Test (weeks 4-7, avg / top-10% / top-1% / best,
  +3 vs +2 vs +1): **week 4 114.6 / 16 / 3 / 191.8 -> 113.1 / 12 / 1 / 164.0 -> 112.4 / 11 / 1 / 164.0** (the cost: the
  191.8 lineup and two top-1% lineups lost); week 5 level; week 6 103.9 / 103.8 / 103.2; week 7 at cap 27 100.9 /
  101.6 / stalls at 147. +2 builds 150 every week.
- **Questionable routing ON from week 8** (Doug, Oct 26): `[model.injury] questionable_routing = true`,
  `questionable_inactive_prob = 0.45` (weeks 4-7 pinned off / 0.25). Q players are still held out of lineups.
- Weekly review loop: he color-codes `exposure.csv` in Excel — **red = exclude, yellow = less (cap at ~half current),
  green = more (min = max(2x current, 12))**. Two shades of green both mean "more". Lists live in `config/<week>/week.toml`
  `[prefs]`.
- Weeks 6-7: red/yellow reads applied, green shadow-only, based on weeks 4-5 (+3.0, +2.5 per lineup).
  **From week 8 (Doug, Oct 26): red applied (`[prefs] red`); yellow AND green shadow-only (`[shadow.yellow]`,
  `[shadow.green]`; `[prefs.yellow]` / `[prefs.green]` stay empty).** Weeks 4-7 as lineups, points per lineup: red
  +1.4 / +1.4 / -1.6 (weeks 5-7; week 4 +3.0 with yellow), yellow +0.6 / -0.5 / -4.8, green +1.3 / -1.7 / none /
  +0.3 (week-7 shadow, boost mode). docs/week8_prep.md section 5.
- When he wants more of a player the model projects low, prefer a projection override (ask his read) over forced exposure;
  forcing low-projected players cost ~5 points of average lineup projection in week 4.

## Week 4 (2026-w04) result — see docs/week4_review.md
149 model lineups + 1 FanDuel "Guru" lineup. Model avg 111.3 vs field 107.3; best 178.7 (rank 1,054 / 596,809, top 0.18%);
4 lineups in top 1%; winner 217.0. Guru lineup 93.0 (rank ~427k). Net +$2.35.
Calibration: rank-order fine (r = 0.68) but **overconfident at the top** (proj 20+: 23.4 projected vs 17.1 actual) — 3-week
hot starts inflate. DST projections ~uninformative (r = 0.24). Jaguars "contrarian" stack was actually chalk
(P. Washington 30% owned) and was our worst stack — we had no ownership model.

## Week 5 (2026-w05) result — see docs/week5_review.md
Entered model-only (Doug's colours recorded under `[shadow]`, not applied). 149 model + 1 Guru in the Pooch Punt (571,483
entries), 6 entries in the $0.25 Hail Mary. Model avg 108.5 vs field 131.2; best 184.9 (rank 10,705); 0 in top 1%;
winner 247.6. Guru lineup 171.9 (top 6%), better than 147 of 149 model lineups. RB was 19 of the 22-point gap: chalk RBs
(Gibbs, Warren, A. Jones) hit, the 25 cap held us to 17% on each, and 45% of lineups had a TE in the flex (field 16%).
20+ tier still +4.9 (23.7 vs 18.8); DST r = 0.11; ownership fine overall (MAE 1.4) but missed the mid-priced chalk again
(M. Wilson 11% vs 51%). Players with a teammate out got ~no gained volume (B. Allen, Warren). Non-starting QBs carry
starter projections. Re-optimizing with Doug's reads: red+yellow +2.5/lineup, green -1.7, all three -1.0.
Net -$4.74 (Pooch Punt $3.11 won on $7.45; Hail Mary $1.10 on $1.50).
Results: `src/convert_results.py <export> --user gst1999 [--tag 025]` turns a FanDuel All Entries export (kept
untracked in `data/<week>/raw/`) into `results_*.csv`.

## Week 6 prep (Oct 12) — see docs/week6_prep.md
Four default changes, each with an off switch in defaults.toml: `[model.injury] absent_mode = "present_share"` (an OUT
player who already missed games is still handed out, for the share of each teammate's usage sample he played in),
`[model.qb] zero_backups` (non-starting QBs project 0; warns when a team has no starter flagged), `[model.calibration]`
(lose 28% of each point above 16, RBs also 12% above 8; refit with `src/fit_calibration.py`), `[model.dst.flatten]` (DST
mean from opponent implied total and salary only). All in `project.adjust`. Week 4/5 skill RMSE 7.99 -> 7.61 and
8.65 -> 7.94. Cap test (model-only, new code): week 5 avg 113.2 / 116.6 / 120.0 at 25 / 32 / 40, week 4 105.1 / 103.9 /
103.1: split, default stays 25 pending Doug's decision. TE-in-flex (45%) comes from the 22-RB pool, TEs counting as
stack receivers and the single-draw objective, not from the cap or inflated TE projections; unchanged.
Week 6 is model-only again with `[shadow]` recording Doug's reads (`config/2026-w06/week.toml`, to be filled).
Second pass (section 7): calibration `mode = "shift"` (mean only; uncalibrated 16+ ceilings were right at 10.9% beat-p90,
13.0% after); log(actual ownership) adds ~1.3 pts per log unit beyond the entered projection (0.84 on week-6 code);
second RB per team and no-cap runs earned nothing, draw weight 40% was +1.0 / +1.8 (not adopted).
`[[status.trade]]` (player, from, to, new_target_share, first_week_factor): old team = first-time OUT in full, new team =
his share of targets taken pro rata; missing share stops the run. Untraded team mismatches only print a warning.
`[optimizer.starters_min_proj]` exists (off).
Third pass (section 8), Doug's week-6 defaults: cap 25, draw weight 40% (`mean_weight = 0.6`), no second RB, mean-only
calibration, plus `[model.spread] RB = 1.376` (RB draws widened around an unchanged mean; RBs beat their p90 14.7% ->
9.8% on 2025 wks 4-18 leave-one-week-out; refit with `src/fit_spread.py`; week 5 -0.6, week 4 +0.6). TE (13.7%) and QB
(11.9%) are also short and not widened. Week-4 gap measured: model-only 104.9 -> Doug's stack teams/BUF rule/Q allowed
107.5 -> overrides 107.8 -> red+yellow 110.8 -> green 112.1 (reads +4.6; entered 111.3). Harrison trade set at
`new_target_share = 0.15`, `first_week_factor = 0.7`, copied under `[shadow.trade]`.
Fourth pass (section 9), from the history refit, all adopted under Doug's rule (no week worse by > 1 point of average):
`top_slope = 0.36`; `[model.injury] routing = "position"` + `[model.injury.position_share]` (OUT/traded player's volume
split by his position first: WR tgt 77% same / 16% other, RB car 94/1, RB tgt 70/0, TE tgt 46/4; `usage.routes`);
`[model.spread]` tapered `{low, top}` per position between `[model.spread_taper]` from 12 to 20 (QB 1.50/1.00, RB 1.43/1.04,
WR 1.23/1.00, TE 1.22 flat; `src/fit_taper.py`). **Caveat flagged to Doug:** top-1% lineups went 1 and 4 (weeks 5, 4) to
0 and 0 with all three on (routing cost week 4's, taper week 5's), and the taper alone fails the rule on week 4 (-1.2).
Fifth pass (sections 9.1 and 10). **Rule from Doug (Oct 12): every lineup test reports average, top-10% count, top-1%
count and best score, and no change is adopted automatically; Doug and Claude decide.** Routing and tapered spread are on
by default but Doug has not yet confirmed them. The lost top finishes were reshuffles (week 4: same exposure to the big
scorers, but lineups holding 3+ of them fell 17 -> 6; week 5: one lineup lost Gibbs). Inside a position the split is NOT
pro rata: with a WR out, the top remaining WR gets ~20% of the gain (pro rata 57%), depth players 60% (14%); candidate fix,
not changed. `[model.opponent]` (dfs/opponent.py, `fit_opponent.py`): defence-vs-position tilt beyond the defence's overall
level, built and OFF: RMSE 7.251 -> 7.247 on 2021-2025, adjustments ~0.2 pts typical, 2.2 max. By-product, untested: WR/TE
projections over-react to the implied total (coefficient about -0.33).
Sixth pass (section 11) and **week-6 model freeze, tag `week6-model-freeze`**: after it only week-6 inputs change
(statuses, reads, lines, Guru, trade). Doug kept routing by position and the tapered spread; opponent adjustment off;
WR/TE implied-total sensitivity is a week-7 item. Depth-rank split inside a position built and OFF
(`[model.injury] within_position = "depth_rank"`, `depth_rank_positions`, `*_rank` shares in `position_share`;
`usage.rank_weights`; `src/fit_depth.py`): WR out 20/20/60 to largest/second/third-and-lower, RB carries 58/33/10.
History (2021-2025 absence games, players moved 1+): RMSE 6.90 pro rata -> 6.72 depth, all from lowering the
established teammate; depth players are over-raised (5.1 projected, 3.6 actual; Derius Davis reached 7-8 week-5
lineups and scored 0) and lead backs are under-projected (Allen, Warren go back down). Recommendation given to Doug:
WR only, via week.toml. Same test: routing by position is NOT more accurate than the old 80% rule for moved players
(6.74 vs 6.59; better with an RB out, worse with a WR or TE out).
Doug's call after section 11: week 6 runs the depth split for WRs only, set in `config/2026-w06/week.toml` (a config input;
defaults.toml stays pro rata). `exposure.csv` has a `Routing_bump` column (proj.csv `RoutingBump`): points each player's
projection gained from injury / trade redistribution, so depth players lifted into lineups can be spotted and red-listed.
It is report-only: added after the freeze tag, draws verified identical before and after.

## Week 6 preliminary run (Tue Oct 13) — inputs only, model frozen
Slate: 10 games, 20 teams (byes CIN, DET, MIA, MIN; off-slate SEA@DEN Thu, HOU@JAC London, DAL@GB SNF, WAS@SF MNF).
Houston is off the slate, so Harrison is not in the player list: only the Arizona side of the trade applies, and the
trade entry got `position = "WR"` so his targets route by position. `data/2026-w06/lines.csv` and `[stacks.weights]`
are PRELIMINARY (nflverse schedule spread_line / total_line); `[status]` mirrors FanDuel's Oct 13 tags (O -> out,
Q/D -> questionable; listed so the O players' volume is redistributed). All three are replaced before the final run.
Preliminary optimizer run in `weeks/2026-w06/prelim/` (no upload file kept); Doug's review sheet is
`data/2026-w06/review_sheet.xlsx` (untracked: *.xlsx is ignored).
Doug, Oct 13: IR players with real 2026 volume (3+ blended targets + carries a game, 16 of them) are listed out as
well, so their volume is handed out under present_share (Kamara +3.1 for Etienne, Hubbard +2.4, NE WRs ~+2).
Harrison off the slate was checked: `data.trades` returns him with share 0 and the configured position, and
`usage.trade_volume` hands 93% of his 4.19 blended ARI targets to his old teammates (WRs 3.23 by depth rank, TEs
0.48, RBs 0.19; ARI total 46.3 -> 46.0 a game). No code change was needed (freeze intact); test added in
tests/test_routing.py. The Houston side and `[shadow.trade]` stay in week.toml, inactive until Houston is on a slate.
`analyze_results.py` does not read `[shadow.trade]`: that read is scored by hand.
Open for the final run: starting-QB calls for BAL (Huntley flagged, Lamar Q projects 0), CHI (Bagent flagged,
Williams Q, Keenum split week 5) and ATL (Penix Q, so ATL cannot be stacked).

**Pick up Friday Oct 16 (state at end of Oct 13: head 4052ead on origin/main, working tree clean):**
1. `[status]` in `config/2026-w06/week.toml`: replace the FanDuel-tag lists with Friday's report (week-5 convention:
   Out and Doubtful -> out, Questionable -> questionable). Keep the 16 IR players listed out (Doug's call) unless he
   says otherwise; re-download `fd_players.csv` if FanDuel has updated it (salaries / tags).
2. `[status.starting_qb]`: Doug's calls for BAL (Lamar or Huntley), CHI (Williams, Bagent or Keenum), ATL (Penix),
   and confirm TB (Jalon Daniels, Mayfield out).
3. Saturday: replace `data/2026-w06/lines.csv` (currently nflverse schedule lines, marked PRELIMINARY) with current
   lines and redo `[stacks.weights]` with the same formula.
4. Doug's colours from `data/2026-w06/review_sheet.xlsx` (Color column): red and yellow -> `[prefs]` (applied),
   green -> `[shadow.green]` (record only). Candidates flagged to him: Kaden Wetjen (PIT, 5.2 all from routing),
   Reggie Virgil (ARI, 7.3 off one game). Guru screens -> `[contest.guru]` if he uses it.
5. Final run goes to `weeks/2026-w06/` (not `prelim/`), with the 149-lineup entry files if he has a free entry.
   The review-sheet builder was a scratch script (not in the repo): pool = `optimize.eligible_pool`, columns Player,
   Team, Opp, Pos, Salary, Proj, Value_per_1k, Implied_total, Routing_bump, Own_proj_%, Lineups, Color, sorted by
   position then projection, second tab `held_out_Q`.
6. Before the first slate Houston is on: ask Doug whether Harrison's `first_week_factor = 0.7` still applies (he
   will have played one Houston game), and score `[shadow.trade]` by hand (analyze_results.py does not read it).

## Week 6 final run (Sun Oct 18) — done 11:35 with Doug's reads (10 red, 9 yellow, no green); entered as below
Inputs done (uncommitted): Sunday `fd_players.csv` (Tuesday's kept as `fd_players_tue.csv`; salaries unchanged, 42 tag
changes), `lines.csv` from nflverse updated 08:15 CT Sunday (no longer PRELIMINARY: BAL -4.5 -> -3, PHI -1.5 -> +3,
CHI/ATL total 49.5 -> 52.5; PIT@TB flat, Mayfield was already out Tuesday), `[stacks.weights]` rebuilt, Doug's
Sunday `[status]` and `[status.starting_qb]` (BAL Huntley, CHI Williams, ATL Penix, TB Daniels, PHI McKee, CLE Watson).
QBs out (Lamar, Hurts, Mayfield) are left to FanDuel's tags, not listed: listing a QB out hands 80% of his carries to
his skill players. Brenen Thompson (LAC, FanDuel Q, not on Doug's list) excluded by Claude. Tanner McKee projects 0
(no passing sample, overrides cannot scale zero sims), so PHI cannot be stacked (2 lineups reallocated).
Review run in `weeks/2026-w06/review/` (upload.csv deleted on purpose); sheet `data/2026-w06/exposure_review.xlsx`
(149 = lowest-projected lineup dropped, Color column empty; builder script was scratch). Free entry confirmed by Doug.
**Next:** Doug's reds -> `[prefs] red`, yellows -> `[prefs.yellow]` with his sheet's Lineups numbers (record red under
`[shadow.red_lineups]`), greens -> `[shadow.green]`; then `model.py` is not needed again (status unchanged), run
`optimize.py --week 2026-w06` (main folder) and write the 149 files (`entered_upload_149.csv`, `entered_readable_149.csv`,
`entered_exposure.csv`). Lock noon CT; Doug wants lineups by 11:00.

## Week 6 (2026-w06) result — see docs/week6_review.md
149 model lineups (Doug changed 3 by hand to spend leftover salary, +60.9 pts) + 1 free entry (Doug's own lineup) in
the Pooch Punt (571,917 entries; no other contest). Model avg 104.5 vs field 110.7; best 158.4 (Maye stack, rank 3,975,
top 0.70%); 1 in top 1%, 8 in top 10%; winner 189.96. Won $5.96 on $7.45, net -$1.49; running total since week 4 -$3.88.
Reads as lineups: red +1.4/lineup, yellow -0.5 (Penix fade wrong; ATL best stack). RB again the gap (Walker). 20+ tier
+7.8 (n 5; third week of +5-8); WR r -0.02; DST r 0.11; ownership MAE 1.3, mid-priced chalk missed again (Likely 10% vs
38%). Q exclusion cost nothing (1 rostered slot behind an excluded Q). 14 lineups left $3,000+ (all late in the build,
22 players at the 25 cap): salary-floor test in the review section 8. Harrison (London): 4 of 32 targets (12.5%) vs
read 0.15 / applied 0.105, but on 12 snaps of ~59 (Doug, from a game page): keep a factor below 1 in week 7.

## Week 7 prep (Oct 18) — see docs/week7_prep.md
Adopted on Doug's instruction, both ON in defaults.toml:
- **Name matching fix** `[model] skip_defense_names = true` (`data.no_offense` in `load_stats`): defensive / specialist
  stat rows with no attempts, carries or targets are dropped before name matching (Michael Carter II, PHI CB, had
  matched Michael Carter, TEN RB). Two-way players with touches (Travis Hunter) kept. Weeks 4-6: only Carter (3.5 / 2.6
  -> 0) and Marcus Jones (0.8 -> 0) really change, never in a lineup; everything else moves <= 0.4 from the shared
  random stream (proven). `tests/test_names.py`. FanDuel has no gsis id, so matching stays name-based.
- **Salary floor** `[optimizer] min_salary = 59000`, `floor_cap_overflow = 3`. **Doug approved cap relief to 28 for
  salary-floor lineups only (week 7).** Relief only for players at the standing 25 cap (not yellow / player_cap), only
  when a lineup cannot otherwise reach the floor; else the lineup is built without it. Weeks 4-6 pin `min_salary = 0`.
  Week 6 with the repo version: 104.2 / 6 / 1 / 158.4 (scratch version that also relieved yellow caps: 10 / 2).
Recommended, not adopted (Doug and Claude decide): WR/TE implied-total term (WR b -0.34, TE -0.27, mean-only; slope
refit 0.357 = current, keep); history 20+ gap +0.17 -> -0.04, live weeks 4-6 +3.1 -> +2.8. Live level bias +1.5 vs
history +0.3 is mostly players scoring 0 (9.7% live vs 3.5%: history rows only hold players who played). Ownership:
Guru / cheap-new-role flags / sharpness do not fix the chalk miss (15%+ MAE 12.2 -> 12.1 at best); record full Guru
lists weekly. Fallback players with no stats (Phil Mafah, FPPG 9.9 from one game, projected ~10.6, scored 0 x3) are a
risk if their starter sits. Projection draws share one random stream: per-player seeds would cut test noise.
`config/2026-w07/week.toml` is a template: HOU is on the main slate (hosts NYG), Harrison trade active with Doug's read
`new_target_share = 0.15`, `first_week_factor = 0.5` (12 of ~59 snaps in London), copied to `[shadow.trade]`.
Doug's decisions (second pass, Oct 18): floor kept as built (no relief for yellow caps); slope stays 0.36; ownership
flags dropped (he records full Guru lists when he uses it). Built in the second pass (docs/week7_prep.md sections 6-7):
- `[model.implied_sensitivity]` (OFF, `project.implied_shift`): WR mean x (1 - 0.34 x (implied/22.5 - 1)) after the
  calibration; TE = 0. Lineup test (floor on): avg +4.2 / +0.9 / -1.3 on weeks 4/5/6, top-10% 11->22 in week 4.
  Doug turned it ON for week 7 (Oct 18); weeks 4-6 pin it off.
- **Role guard ON** `[model.role_guard]` (`project.role_guard`): skill players with no current-season stats project 0
  unless in `[overrides]` (warning lists them); WR/TE under 3 targets + carries a game in 2026 games (pre-routing) project
  0. RBs stay out of the floor (Doug, Oct 18; inherited RB jobs get real work: Bam Knight 17 touches). Weeks 4-6: 43 entered slots removed, scored 1.0 (proj 5.9); lineups +0.1 / +0.8 / -0.1;
  blocked Thornton (KC, 28.6, never rostered). Weeks 4-6 pin it off. proj gains RoleVol, NoData, RoleGuard.
- **`[names.aliases]` ON** (nflverse -> FanDuel name): Josh/Joshua Palmer, Marquise/Hollywood Brown, Matthew/Matt
  Hibner, Nicholas/Nick Singleton, Mitchell/Mitch Tinsley, Andrew/Drew Ogletree. The guard's no-data warning is the
  place new aliases show up: check it every run.

## Week 7 run checklist (ALL DONE: step 6 graded Oct 26, docs/week7_review.md; see "Week 7 (2026-w07) result")
Steps 1-2 and the preliminary parts of 3-6 are DONE (section "Week 7 preliminary run"). Remaining:
1. DONE Oct 22 for colours (`data/2026-w07/review_sheet_reviewed.xlsx`). Pool lists loaded (ranked). **Doug, Oct 22:** pool cap 45 for week 7
   (shadow test; `[pool] raise_cap_to = 45`), model cap 26, then 27 after the extra receivers (stays
   marked PRELIMINARY until the final run).
2. DONE Oct 23 (see "Week 7 Friday run"): statuses, `[status] active`, TB = Mayfield, Harrison starter override,
   Mumpfield red and Godwin yellow cleared, Kyren forced min 15, Jones left at 14.1, no Estime / SF reads. Sunday (DONE Oct 25: Lamar OUT, left Q so
   BAL kept as built with Huntley; Nacua Q, kept excluded): **Lamar** (Doug decides; if he plays, Huntley's 6 lineups are dead: move Lamar out of questionable,
   set `[status.starting_qb] BAL`), **Nacua** (if ruled OUT, move him from questionable to out and rerun model.py).
   Was: Friday's report (check Nacua, hurt in practice Oct 22; Adams already out) -> `[status]` (replace the preliminary FanDuel-tag lists; Out/Doubtful -> out, Questionable ->
   questionable, IR players with 3+ targets + carries a game out, QBs out left to FanDuel tags) and
   `[status.starting_qb]` (BAL: Lamar Q, Huntley flagged; TB: Mayfield Q). Re-download `fd_players.csv` if FanDuel
   updated it. Then Doug's Estime (CLE RB, no 2026 data) and SF override reads, if any.
3. DONE Oct 25. Saturday / Sunday: replace `data/2026-w07/lines.csv` (PRELIMINARY nflverse lines) and rebuild `[stacks.weights]`
   = round(2 x (implied - 16)), min 1. Keep `[stacks] extra_receivers = ["Christian McCaffrey", "Kyren Williams",
   "Aaron Jones Sr."]` (Doug's reads). Mumpfield is no longer red (Doug, Oct 23): LAR stacks use Kyren / Higbee / Mumpfield.
4. DONE Oct 25. `model.py`, read the role-guard warning (new names = no 2026 snaps or a missing alias) and team-mismatch warnings.
5. DONE Oct 25 (PRELIMINARY comments on `exposure_cap` still in week.toml; cap 27 is final). Final `optimize.py --week 2026-w07` (main folder; check the floor line), the control
   `optimize.py --week 2026-w07 --subdir model_cap45 --cap 45` and `optimize.py --week 2026-w07 --pool`
   (shadow, `weeks/2026-w07/pool/`; pool players auto-raise to 45, Doug's week-7 setting). Model cap is 27: if any set
   stalls after Friday's statuses, stop and ask Doug (don't raise caps on your own). Drop the PRELIMINARY marks on
   `exposure_cap`. **Doug has a free entry (confirmed Oct 23): write the 149 files for the model set.** Final model run goes to the
   main folder (Friday's preliminary model set is in `prelim/`). Enter the model's lineups only;
   keep upload.csv in all three folders (grading reads them).
6. After the slate: `convert_results.py`, `[contest] field_size`, `analyze_results.py` (`pool/grade.csv` grades model
   cap 27 (entered), model_cap45 (control) and pool cap 45: avg, top-10%, top-1%, best), `docs/week7_review.md`
   (week-6 format + the three sets, Harrison's trade read and the extra-receiver reads McCaffrey / Kyren / Jones by
   hand; 106 reds incl. TEN / MIA DSTs and the cap-0 yellows), ask Doug for winnings (running total -$3.88 after week 6).
Review sheet recipe (builder is a scratch script, not in the repo): rows = every active player with an empty
`RoleGuard`, sorted by position then Proj; columns Player, Team, Opp, Pos, Salary, Proj, Value_per_1k, Implied_total,
Routing_bump, Role_vol, Own_proj_%, Lineups (from the prelim/review exposure.csv), Status, In_model_pool (Y or the
reason: red, questionable, not the starting QB, depth, projects < 4), Color (reds pre-filled), Pool, Rank; tabs
held_out_Q and notes. Check: Lineups sums to 1,350.
Reading it back (Oct 22 lesson): count Pool = Y per position after stripping blanks (cleared Excel cells come back as
" "), compare to the sizes, and before loading list every mismatch (count, unmarked ranks, marked-but-unranked) for
Doug; he prefers to fix the sheet himself so the file matches what was used. Keep the sheet's notes and his run
template on the same Pool marker (the sheet said Y, his template said P).

## Doug's pool mode (Oct 19) — see docs/pool_mode.md
Built on Doug's spec, inside the model. **Deviation he must decide:** his sizes (QB 10, RB 10, WR 10, TE 8, DST 5)
can't fill 150 lineups at cap 25 (375 fillers needed, 150 allowed) and stalled at 138/138/145 at cap 40 on weeks 4-6
(stand-in pools); WR 14 at cap 40 built 150 valid lineups every week (also cap 45 or 2 fillers on week 4). Pool mode
raises pool players to 40 under the standing rule and stops with advice beyond that. Normal model proven unchanged
(week 6 identical, 150/150). **Doug's decisions (Oct 19):** pool sizes QB 10, RB 10, WR 14, TE 8, DST 5 at cap 40;
rank_boost 0.05 stays (ranking optional); auto-raise to 40 fine, beyond that stop and ask; Q pool players held out
unless he clears them Sunday (same as the model). **Week 7 is shadow:** build both sets, enter the model's, grade both.

## Week 7 preliminary run (Mon Oct 19) — inputs only
Slate confirmed: 10 games / 20 teams exactly as in week.toml (byes BUF, JAX, LAC, WAS; off-slate NE@CHI, PIT@NO,
KC@SEA, DAL@PHI). Stats cache now includes week 6. `lines.csv` = nflverse schedule lines downloaded Oct 19 23:23 UTC
(**PRELIMINARY**); `[stacks.weights]` rebuilt from them (DET 24 ... NYG 1). `[status]` = FanDuel's Oct 19 tags (O -> out,
Q/D -> questionable, Q QBs Lamar / Mayfield listed) + 14 IR players with 3+ targets + carries a game in 2026 (Achane
15.3, Jordan Mason 15.0, ...). Preliminary run in `weeks/2026-w07/prelim/` (upload.csv deleted): 150 lineups, all
>= $59,000, no cap relief, mean proj 118.3. Review sheet `data/2026-w07/review_sheet.xlsx` (untracked): every player
passing the role guard (201), columns incl. Role_vol, Status, In_model_pool, Color, Pool, Rank; tabs held_out_Q, notes.
Fixed: `ownership` feature `gained_vol` floored at 0 (Harrison's -1.34 made log1p NaN and every WR projected 0% owned;
training rows never negative, so weeks 4-6 fits unchanged). Found:
- Harrison (HOU): 4 of 32 targets in week 6; projects 4.3 at 0.15 x 0.5; RoleVol 3.4 (just over the floor). ARI side
  hands out his volume although ARI's weeks 5-6 already lacked him (backlog). **Doug, Oct 19: factor 0.7** (10.5% of
  HOU targets; also under [shadow.trade]). proj.csv, prelim and the review sheet (rebuilt Oct 19 evening) use 0.7.
- SF got 0 stacks: Kittle was the only usable SF receiver (Cooks, Watkins, Cowing, X. Smith under the role floor; Deebo
  O, Evans Q; Jennings is MIN, not SF). **Doug, Oct 19: `[stacks] extra_receivers = ["Christian McCaffrey"]`** (also
  under [shadow]). Prelim re-run (with Harrison 0.7): SF 13 stacks = its weight share 13.1, all Purdy + CMC + Kittle;
  mean proj 118.3 -> 118.4; Harrison 4.3 -> 6.0. Week 6 re-built with the new code: identical (150/150 vs entered).
- Kaytron Allen WAS -> MIA (real move) and Jared Wayne HOU -> MIA: **both red** (Doug, Oct 19; also under
  [shadow.red_lineups] with 0 lineups). No trade entry for Allen (Doug wants him in no lineup; WAS on bye, MIA
  teammates unaffected). Both projected under 4, so the eligible pool and the prelim lineups are unchanged.
- Estime and SF override reads: Doug decides after Friday's report.
- Role-guard no-data list (all real, no missing aliases): Josh Johnson (CIN QB), Audric Estime (CLE RB 8.4), Phil Mafah
  (NYG RB 9.6), Jaret Patterson (CLE RB), Michael Bandy, Shedrick Jackson, Devin Culp. CLE RB room thin (Judkins Q,
  Sanders IR): Estime may start.
Next: Doug's sheet (Color -> [prefs] / [shadow]; Pool / Rank -> [pool]), Friday status, Saturday / Sunday lines,
then final model run, `optimize.py` (main folder) and `optimize.py --pool` (shadow), 149 files if free entry.

## Week 7 review applied (Thu Oct 22) — inputs only
Doug's sheet `data/2026-w07/review_sheet_reviewed.xlsx` (untracked; `review_sheet.xlsx` left as built). All 201 names
match proj.csv. Colours: 106 red -> `[prefs] red` (+ `[shadow.red_lineups]`; 28 of them were in 161 prelim slots, incl.
TEN DST 25, MIA DST 24, Ja'Kobi Lane 10, Bartholomew 9, Skattebo 8, Tate 8), 36 yellow -> `[prefs.yellow]` with the
sheet's Lineups (8 of them had 0-1 lineups, so cap round(0.5 x) = 0: Winston, Dulcich, CIN / GB / ATL DST, and depth
RBs Harvey, B. Robinson, Tracy), 59 green -> `[shadow.green]`. Red QBs Lamar and Mayfield stay out even if cleared Friday.
Stats cache refreshed (the Oct 19 download predated SF@WAS MNF): only SF usage changed (McCaffrey 18.2 -> 19.0, Kittle
13.8 -> 14.4, Purdy 21.2 -> 21.0); everyone else <= 0.1 (random-stream noise). MNF: Purdy 100% of snaps, Kittle 89%,
CMC 85% (30.7 pts); none of the three on SF's week-7 practice report (nflverse injuries_2026.csv): no injury.
**Model set:** stalls at 147 at cap 25 (reads leave too few stackable teams: MIN 0 with Bartholomew red and
Addison / Hockenson Q, BAL capped by Huntley yellow 6, ARI / TEN / MIA QBs red, NYG Winston cap 0). Cap 26 is the
smallest that builds 150 (floor relief +3 -> up to 29); relief held at 28 fails at caps 26-28. **Doug, Oct 22: cap 26 used in week 7 because
his reds / yellows limited the stackable teams** (`[optimizer] exposure_cap = 26`, marked PRELIMINARY until the final run). Prelim in `weeks/2026-w07/prelim/` (upload
deleted): 150, mean proj 119.9 (Monday 118.4), salary all $59,000-60,000, 13 stack teams (HOU 28, CIN 19, DET 17, GB 17,
SF 16, LAR 14, ...), 84 players used. Bijan 25 -> 2, Jefferson 14 -> 1, Murray 9 -> 0.
**Pool:** in week.toml `[pool]` (ranked) since Oct 22 evening: Doug re-marked the sheet (Irving added, TE 6-8 added)
and confirmed in chat WR ranks 1-14, DST ranks 1-5 (the sheet still marks 20 WR / 13 DST). CLI run at cap 40 stalls
at 145. **Doug: cap 45 for week 7.** Pool set in `weeks/2026-w07/pool/` (upload deleted): 150, mean proj 122.5
(model 119.9), p90 ceiling 158.1 (154.9), 9 stack teams (HOU 25, SF 24, GB 22, DET 21, CIN 19, CAR 18, LV 13, LAR 6,
TB 2; MIN 0: Jefferson is Murray's only pool receiver), 148 lineups use a filler (Coker 18, Tucker 16, Gesicki 15),
72 players (model 84), 22 lineups identical to the model's. Pool heavier on Harrison, A. Jones, Hubbard, McMillan,
LaPorta, Likely, Egbuka, CLE DST (45 each, model 27-29); lighter on Jeanty, Flowers, DEN DST, Higbee, Dobbins. First marks (superseded) gave QB 17, RB 0, WR 26, TE 12, DST 0; his ranks run QB 1-17, RB 1-19,
WR 1-18, TE 1-17, DST 1-14 (no 13). Provisional reading (scratch only): top N by rank = QB 10, RB 10, WR 14, TE 8,
DST 5, all usable. It stalls at 145 at cap 40; builds 150 at cap 45 (mean proj 122.5, 148 lineups use a filler, 9
stack teams). WR 18 or 2 fillers stall earlier (118 / 133): the capacity check then passes at the standing cap, so pool
mode never raises pool players to 40 (gap: raise is triggered by the arithmetic check only, not by a stall).
**Shadow control set (Doug, Oct 22):** the normal model at cap 45 (same reds, yellows, floor; relief to 48), not
entered: `optimize.py --week 2026-w07 --subdir model_cap45 --cap 45` (`--cap` = this run only, new Oct 22; without it
the prelim reproduces byte-identical). `[grading] extra_sets = ["model_cap45"]` in week.toml: `analyze.pool_report`
grades it beside pool and model in `pool/grade.csv` (`tests/test_grading_sets.py`). Monday grades all three: model
cap 27 (entered), model cap 45 (control), pool cap 45.
Davante Adams (LAR): FanDuel O (hamstring), not IR; in `[status] out`, volume routed (Nacua +1.6, Higbee +1.5,
Mumpfield +1.9). **Nacua: Doug says hurt in practice Oct 22 -> check Friday's report.** Not on nflverse's LAR report
yet. If out (scratch what-if): Kyren 17.7 -> 18.2, Higbee 10.3 -> 11.2, Corum 9.1 -> 9.5, Mumpfield 6.1 -> 8.1 (red),
Stafford 20.8 -> 20.7; the rest of his targets go to WRs the role guard zeroes (Atwell, Whittington, Bachman), so LAR
would have no usable WR (Mumpfield red) and Stafford stacks = Higbee + an extra-receiver RB.
**Extra receivers (Doug, Oct 22):** Kyren Williams (LAR) and Aaron Jones Sr. (MIN) added to `[stacks] extra_receivers`
(also under `[shadow]`). Control and pool rebuilt: LAR 18 -> 17 / 6 -> 19 stacks, MIN 0 -> 10 / 0 -> 14 (all Murray +
Jones + Jefferson); control mean proj 123.2 -> 122.5, pool 122.5 -> 121.9. **Model at cap 26 now stalls at 149**
(reshuffle; no team left for the last lineup); cap 27 builds 150 (scratch preview: mean 119.7, LAR 18, MIN 9).
**Doug: cap 27** (`exposure_cap = 27`, still PRELIMINARY until the final run; relief to 30). Prelim rebuilt = the preview
(150, mean 119.7, HOU 29, LAR 18, CIN 17, DET 16, SF 14, GB 13, MIN 9, ...). Pool rebuilt (fillers now cap 27): 150,
mean 121.9, LAR 17, MIN 14. Control unchanged (own --cap 45).
Practice notes (Wed report, not applied): Irving, Hubbard, Egbuka, Schultz, K. Allen, Montgomery, Waller DNP.

## Week 7 Friday run (Fri Oct 23) — preliminary lines; all three sets built (see 'Doug's decisions' at the end)
Doug's Friday statuses in `[status]` (Out/Doubtful out; uncertain Q = questionable, no redistribution; IR-volume list
kept; 11 off-slate names not listed). New `[status] active` (data.load_slate; `tests/test_status.py`): clears
FanDuel's O/IR tag for players back from IR (Tank Dell, Jordan Mason, Beaux Collins; Dell and Collins have no 2026
data, so the role guard projects them 0). `[status.starting_qb] TB = "Baker Mayfield"` (active per Doug; default
would have started Jalon Daniels; Mayfield is red, so TB is not stacked). Mumpfield's red cleared (Doug); Kyren
Williams = Doug's forced read: `[prefs.green]` 0 + `[prefs.green_floor]` 15 (min 15; floor is max(2 x listed, floor)),
out of `[shadow.green]`, graded as green (applied). Pool WR: Godwin at Egbuka's rank 7, Mumpfield added at 15.
Projections: Nacua 20.8 -> 17.0 (Q), Bijan +4.0 (B. Robinson out), Allgeier +4.3 / Knight +3.3 (Love out), Marks +3.1
(Montgomery out), Godwin +1.9 (Egbuka out), A. Jones 16.2 -> 14.1 (Mason back, 9.5). Control (cap 45) and pool built:
150 each. **Model at cap 27 stalls at 137**: Harrison 6.1 -> 5.8 (Montgomery's routing + stream noise) fell under
Jaylin Noel 6.0 (red), and red players hold depth slots, so HOU's top-3 WR = Collins + two reds; HOU stacks 29 -> ~20.
Scratch: caps 28 / 29 / 30 stall at 142 / 145 / 148, cap 31 builds 150 (Harrison 0); cap 27 builds 150 if Harrison is
a starter (override 6.1, or red players not holding depth: same lineups, Harrison the only new player, 29). Kyren's
floor is not the cause (stalls without it) and never binds (30+ lineups). Godwin still yellow cap 1 (1 lineup in pool).
`weeks/2026-w07/prelim/` held Thursday's set until Doug decided.
**Doug's decisions (Oct 23, later):** new `[prefs.starter_override]` TEAM = [names] (`optimize.starters`; test in
`tests/test_status.py`): named players count as starters on top of the normal depth, red players keep their slots,
red / Q / min_proj still apply; week 7: `HOU = ["Marvin Harrison Jr."]`. Godwin's yellow cleared. Model cap stays 27.
Aaron Jones: Doug left him at 14.1 (no read). Doug has a free entry in week 7: write the 149 files on the final run. Built (no uploads),
all lineups checked against the rules: model `prelim/` 150, mean 119.8, HOU 30 / CIN 19 / SF 16 / DET 16 / LAR 14 /
MIN 9, Harrison 24, Godwin 28, Kyren 30, Mumpfield 23; control 150, mean 122.3, LAR 19, MIN 11, Kyren 45; pool 150,
mean 121.9, LAR 18 (Mumpfield + Kyren 15), MIN 15, Kyren / Mumpfield / Godwin 45. Every MIN stack = Murray + Jones + Jefferson.

## Week 7 final run (Sun Oct 25, done 11:31) — entered: entered_upload_149.csv (free entry confirmed)
Doug: Lamar OUT, BAL kept as built (Lamar left in `[status] questionable`, so no redistribution; Huntley starts by
default, 6 lineups). Nacua Q, expected to play: kept excluded, no redistribution. nflverse lines refreshed (all 10
games moved; CIN@BAL now CIN -3, 46.5: BAL 27.0 -> 21.8, weight 22 -> 12; DET 29.5, weight 27); `lines.csv` marked
FINAL, `[stacks.weights]` rebuilt (round half up). Model cap 27: 150, mean 120.4; 149 file drops lineup 145 (103.7),
checked: header, 149 unique, salary 59,000-60,000, no red / OUT / Q / FanDuel O-IR players. Max exposure 30 = cap 27
+ salary-floor relief 3. Control (cap 45) 150, mean 122.8; pool (cap 45) 150, mean 122.2. Next: checklist step 6.

## Week 7 (2026-w07) result — see docs/week7_review.md
149 model lineups (cap 27, as built) + 1 free entry (Doug's own) in the Pooch Punt (550,210 entries). Model avg 101.1
vs field 103.3; best 151.4 (Burrow stack, rank 9,356); 0 in top 1%, 11 in top 10%; winner 228.78; cash line ~102 (76
of 150 cashed). Won $8.18 on $7.45 (Pooch Punt +$0.73) plus two $0.25 Hail Mary entries ($0 won): net +$0.23,
running total since week 4 -$3.65 (Doug confirmed both, Oct 26).
Four sets (exact ranks): model 101.1 / 11 / 0 / 151.4; control cap 45 98.0 / 8 / 1 / 157.8; pool cap 45 96.1 / 4 / 0 /
148.9; free entry 110.1. Pool vs control -1.9, cap 45 vs 27 -2.9 (better best). Projected vs actual lineup r -0.23.
Reads as lineups (scratch re-runs; analyze_results.py crashed on the shadow-green floor run, 185 forced QB lineups):
red -1.6, yellow -4.8 (QB yellows Nix / Smith / Watson / Penix all 20+; Pollard 38.0 capped at 4), Kyren min -0.8 (never
bound), shadow greens (boost mode) +0.3, McCaffrey receiver -0.3, Mumpfield -0.8 / -0.6 (pool), Godwin -1.3 / -2.5 (pool).
Harrison: 4 of 28 targets (14.3%) on 13 snaps (21%); two HOU games 13.3%. RB -10.8 vs field; TE in flex 78%.
**Josh Jacobs missing**: `fd_players.csv` was the Oct 19 file, never refreshed; Strong (12 lineups) scored 0. Q held
out without redistribution: Hall / Spears sat, B. Allen 19.4 and Pollard 38.0. Floor: no $3k+ lineups, but 21 players
above cap 27 (12 at 30). Role guard: 179 of 216 zeroed players scored 0, no real miss. WR correction neutral. 20+ tier
+4.7; beat-p90 9.8%; DST r -0.09; ownership MAE 1.5, chalk missed again (Golden 12% vs 40%, Coker 10% vs 36%).
Week-8 list in the review, section 6.

## Week 8 prep (Oct 26) — see docs/week8_prep.md
Doug's eight items. Done and ON: floor relief +1 (`floor_cap_overflow = 1`; week 7 pinned at 3); traded player's
old team by present share (`[model.injury] trade_old_team = "present_share"`, ARI double count, weeks 6-7 pinned
"full"); reads mode (red applied, yellow + green shadow); Harrison 0.15 / 0.9 in `config/2026-w08/week.toml`;
`assign_forced` scales forced green QBs to fit (week-7 crash) and `reads_lineups` survives a failed run;
`src/diff_players.py`. Built and OFF: `[optimizer] flex_te_max_share` (TE-in-FLEX cap). Built and ON (Doug, Oct 26):
`[model.injury] questionable_routing` at `questionable_inactive_prob = 0.45` (a Q player's volume to teammates in the
draws he sits; Doug's Q lists sat 12 of 26, history Q + DNP 45%, all Q 24%). Tapered TE spread
tested (config only), not adopted. Lineup tests weeks 4-7 (`weeks/2026-w07/backtest_week8_prep.csv`): TE taper
-0.7 / +0.5 / -0.2 / +0.2, FLEX mix unchanged; TE cap 35% -1.1 / 0.0 / -0.4 / week 7 infeasible at cap 27 (builds at 29);
Q routing -0.1 / 0 / -0.2 / -0.2 with top-10% +3 / 0 / +1 / 0, top-1% +1 in week 4 (recommended at 0.45); relief +1
-2.2 / 0.0 / -0.7 and **week 7 at cap 27 stalls at 147** (builds with +2, cap 28, or yellows shadow at cap 25).
Week 7's 78% TE-in-FLEX was mostly the RB / WR yellows: with yellows off it is 56%.
**Week 8 schedule:** byes HOU, NO, NYG, SF; CAR@GB Thursday; likely main slate 11 games / 22 teams (BAL@BUF,
TEN@CIN, ARI@DAL, MIN@DET, IND@JAX, LV@NYJ, CLE@PIT, ATL@TB, LAC@LAR, KC@DEN, NE@MIA). Harrison (HOU) and Jacobs (GB)
are not on it. **Doug's decisions (Oct 26):** pool kept for weeks 8-9 (shadow), then reviewed; Q routing ON at 0.45;
no extra receivers carried over (he adds them per week); cap relief +2 (not +1). Harrison 0.15 / 0.9 and Jacobs' read
wait for week 9. **Week 9: McCaffrey left week 7 injured (SF bye in week 8): check his status before the week-9 run.**

## Week 8 preliminary run (Tue Oct 27) — inputs only; checklist steps 1-2 DONE
Slate confirmed: 11 games / 22 teams as planned (552 players, `fd_players.csv` downloaded Oct 27 18:50; keep it as the
base for Friday's diff). Stats cache through week 7 (all 28 teams incl. MNF). `lines.csv` = nflverse lines Oct 27 23:56
UTC (**PRELIMINARY**); `[stacks.weights]` DAL 29, BUF 26, CIN 25, JAC 24 ... TEN / CLE 4. `[status]` = FanDuel tags
(Kattus O; 25 Q incl. QBs Lamar and Carson Beck) + 13 IR players with 3+ targets + carries a game (Achane 15.3, Adams
8.2, ...). Prelim in `weeks/2026-w08/prelim/` (upload deleted): 150 at cap 25, no cap relief, mean proj 118.7, all
rules checked, FLEX RB 73 / WR 37 / TE 40, 22 stack teams (DAL 14 ... CLE 2). Review sheet `data/2026-w08/review_sheet.xlsx`
(220 rows, Lineups sum 1,350; builder is a scratch script). Largest routing bump: Ollie Gordon II +4.3 (Achane out).
Role-guard no-data list: Buechele, Gabriel, Browning, Josh Johnson (backup QBs), Estime, Hodgins, Shedrick Jackson,
Patterson: no missing aliases.
**Doug's decisions (Oct 27):** TB = Mayfield (`[status.starting_qb]`; 14.9, all 8 TB stacks). **Cameo rule fixed**
(`[model.qb] cameo_rule = "backup_only"`, `data.cameo`, `tests/test_cameo.py`): a QB row under `min_attempts` is
dropped only when a teammate QB threw more in that game (Mayfield was TB's only QB in week 7, 11 attempts, so the old
rule made Daniels the starter). Weeks 4-7: no 2026 row and no starter changes; 2025 prior rows change for ~7 QBs
(Lamar, Darnold, Love, Mariota, Dart, McCarthy, Huntley), so weeks 4-7 pin `cameo_rule = "any"` to re-run as entered.
**Ties (Doug, Oct 27, later): a tie for the team's most attempts (under 15) is a cameo for both QBs** (2025 wk 16
Lamar / Huntley 10 each; without it Huntley fell 18.0 -> 16.0). Week 8 vs the old rule: only Mayfield / Daniels
change (rest within 0.2, stream noise). Prelim and sheet rebuilt: 150, mean 118.6, FLEX RB 74 / WR 37 / TE 39. Allen / Wayne: Doug marks them on the sheet if he wants them out. BAL / Lamar: after Friday.

## Week 8 review applied (Thu Oct 29) — inputs only; pool loaded (all 97 P, Doug)
Doug's sheet `data/2026-w08/review_sheet_reviewed.xlsx` (untracked; `review_sheet.xlsx` left as built). All 220 names
match proj.csv. Colours typed as "red": **118 red, 0 yellow, 0 green** -> `[prefs] red` (applied) + `[shadow.red_lineups]`
(40 of them held 256 prelim slots: Mason 25, Warren 20, B. Allen 13, O. Cooper 12, DET DST 11, Johnston 11, ...; red QBs
Geno Smith, Penix, Rodgers, Nix, Willis, Ward and more; Allen / Wayne red). **Pool:** 97 rows marked P, but only 47 ranked
and the ranked ones are exactly the target sizes (QB 10, RB 10, WR 14, TE 8, DST 5; ranks 1-N, no gaps); the other 50 P
rows have no rank. Asked Doug which is the pool; with the ranked 47 only, Mayfield / Mahomes / D. Jones have 0 own
WR/TE in the pool, Allen / Lawrence 1, Goff 1 usable (St. Brown Q, ranked WR 4, held out). Not loaded until he answers.
Rebuilt with the reds (no model.py rerun: statuses unchanged): **model `prelim/` 150 at cap 25** (6 lineups used floor
relief, max 27), mean 119.2 (Oct 27: 118.6), 15 stack teams (DAL 21, BUF 20, CIN 18, JAC 15, LAR 11, BAL 10, NE 10, ...);
NYJ / PIT / ATL / DEN / MIA / TEN QBs red and LAC with no usable receiver, so 29 stack lineups reallocated. FLEX TE 84 /
RB 47 / WR 19 (was TE 39 / RB 74: 60 RBs red). **Control `model_cap45/` 150**, mean 120.5, same stack counts, 109
lineups identical to the model's, max exposure 40 (Nacua). Upload files deleted (Doug: no uploads yet).
**Doug, Oct 29 (later): pool = all 97 P players**; the 47 ranked get the rank boost, the 50 unranked are members with no
boost (new `[pool] ranked_top`, `tests/test_pool.py`; pool.py only, model and control untouched). Sizes QB 17, RB 19,
WR 31, TE 18, DST 12; held out Q: Lamar, St. Brown, Rice, Egbuka, DJ Moore, McConkey. Short of two pool receivers:
Daniel Jones (Downs only: 3 stacks, with a filler TE) and Herbert (none: LAC dropped, 0 lineups). **Pool `pool/` 150 at
cap 25** (no raise; 4 lineups floor relief to 27), mean 118.9, 15 stack teams (DAL 18, BUF 16, CIN 15, JAC 14, LAR 12,
NE 12, BAL 11, DET 11, ...), 10 lineups use a filler (Engram 6, Mallory 4), 838 slots ranked / 502 unranked players,
20 lineups identical to the model's. Unused: Herbert, Mason Taylor. Upload deleted. Rank 10 boost = 1.00 (linear to
the last ranked, as in week 7).

## Week 8 run checklist (2026-w08)
**State Oct 29: step 3 DONE incl. the pool (see "Week 8 review applied"). Next = Friday:
rename the Oct 27 file to
`fd_players_oct27.csv`, save the new download as `fd_players.csv`, diff, report, then `[status]` from Friday's report
(BAL / Lamar call; TB stays Mayfield unless Doug says otherwise). Free entry: ask Doug before the final run.**
1. FanDuel player list: download when the slate opens (`data/2026-w08/fd_players.csv`); **re-download Friday and
   Sunday morning**, keep the earlier file, run `python src/diff_players.py <earlier> <new>` and report added /
   removed players and new tags to Doug before re-running `model.py`. Confirm the slate against week.toml's list.
2. Preliminary run (week-7 recipe): stats cache refresh (`fetch_stats.py`, week 7 in), PRELIMINARY nflverse lines ->
   `data/2026-w08/lines.csv` and `[stacks.weights]` = round(2 x (implied - 16)), min 1; `[status]` from FanDuel tags +
   IR players with 3+ targets + carries a game; `model.py`, read the role-guard and team-mismatch warnings; prelim
   optimizer run in `weeks/2026-w08/prelim/`; review sheet (recipe in the week-7 checklist). Check the FLEX mix.
3. Doug's sheet: red -> `[prefs] red` (+ `[shadow.red_lineups]`), **yellow -> `[shadow.yellow]`**, green ->
   `[shadow.green]`, Pool / Rank -> `[pool]` (pool kept weeks 8-9). Extra receivers only if Doug names them.
4. Friday statuses, Sunday lines (FINAL), final `optimize.py --week 2026-w08`, control `--subdir model_cap45 --cap 45`,
   `optimize.py --week 2026-w08 --pool`; 149 files if Doug has a free entry. Cap 25 (standing); if a set stalls, stop and ask Doug.
5. After the slate: `convert_results.py`, `[contest] field_size`, `analyze_results.py`, `docs/week8_review.md`,
   ask Doug for winnings (running total -$3.65 after week 7).

## Week-8 backlog
- **Per-position redistribution mode**: RB out = routing by position; WR out = depth split; TE out = old 80% rule or none.
  Basis: the section 11.2 accuracy table (players moved 1+: RB out 6.65 routing vs 6.70 old; WR out 6.53 depth vs 6.77 pro
  rata; TE out 4.71 none / 4.75 old vs 5.15 routing).
- **Cap the boost to depth players**: the depth split projects the players it raises at 5.1 and they scored 3.6
  (partly covered now by the WR/TE role guard).
- **Per-player random streams** in the projection sims, so a change to one player stops reshuffling everyone else's
  draws (docs/week7_prep.md 1.1): cleaner lineup tests.
- **Zero-score risk**: 9.7% of live slate players score 0 vs 3.5% in the history rows (week7_prep 3); a play-probability
  term for players without a stat row in their team's recent games.
- **Ownership**: chalk under-predicted ~10 pts; needs a pre-lock signal the field sees (full Guru lists weekly, or a
  public ownership projection). Guru / cheap-new-role flags were tested and dropped.
- **Harrison trade**: Arizona side fixed Oct 26 (present share); remove the trade entry after ~3 Houston games.
- 149-lineup script (still an inline snippet each week).
- Pool mode: raise pool players to `raise_cap_to` on a stall too, not only when the capacity arithmetic fails (week 7).
- From the week-7 review (section 6): DONE Oct 26 (docs/week8_prep.md): player-file refresh check, Harrison factor,
  ARI side via present_share, Q routing (on), yellows to shadow, TE-in-FLEX test (cap off), relief +2, control and pool
  kept, `assign_forced` fix.
- **Week 9:** McCaffrey's status (left week 7 injured; SF bye in week 8); Jacobs' read (two games of data by then);
  Harrison 0.15 / 0.9 applies (HOU back on the slate, if it is); pool review after week 9.

## History refits (Oct 12) — see docs/phase2_history.md
`fetch_stats.py --seasons 2020-2025 --history` puts player stats, team stats and schedules with Vegas lines in
`data/cache` (untracked); `fit_history.py` refits DST, injury share, spread and calibration on 2021-2025, leave-one-season-out,
recent seasons weighted 0.75 per year back. **No defaults changed; Doug and Claude decide before week 7.** Findings: DST
-0.35 on opponent implied total holds (own DST average predicts nothing); injury volume goes to the missing player's own
position (WR 93% total / 77% to WRs, RB carries 95%, RB targets 70%, TE 49%) while the model spreads 80% pro rata across
positions; RB spread 1.376 holds (1.36), QB/WR/TE want 1.15/1.17/1.22 but a flat factor over-widens 16+ players;
calibration slope above 16 fits 0.36 with Vegas totals (0.28 then), RB slope 0.12 holds, moving the knees gains nothing.
The slope, the routing and a tapered spread were then adopted for week 6 (week6_prep.md section 9).

## Phase 2 roadmap (in priority order)
1. **Prior-season blend** — DONE Oct 5 (docs/phase2_prior_blend.md): usage 2 pseudo-games, efficiency 4 games of 2025.
   Week-4 RMSE 8.30 -> 8.08, 20+ tier gap +7.1 -> +4.2; also better on 2025 wks 4-18 (with 2024 prior). Residual
   structural bias (~+0.7 overall, ~+2 at 20+) remains — candidate: heavier TD-rate shrinkage, tuned with the same backtest.
2. **Ownership model** — DONE Oct 5 (docs/phase2_ownership.md). Week-4 CV MAE 3.2 pts (null 4.2), log-r 0.73. Misses
   mid-priced chalk (P. Washington 4.6% vs 30%, A. Jones 6% vs 40%) and QB ownership; would NOT have flagged the JAC
   stack. The FanDuel Guru lineup held 6 players owned 17-40% — candidate feature once 3+ weeks are recorded.
   Leverage OFF by default; week-4 backtest is noise-dominated (0.2 harmless, 1.0 costs ~10 pts of projection).
3. **Vegas-weighted stacks**: stack-team weights from implied totals instead of hand-set `[stacks.weights]` in week.toml.
4. Pass/rush defensive split adjustment (opponent yds allowed vs league avg, heavily shrunk). Doug supplied week-4 tables.
5. Better DST model; better starter detection (depth charts) instead of projection rank.
6. Backtest harness: re-run each archived week and score lineups vs actuals.

## Tech debt (honest)
Refactored Oct 5 into `src/dfs/` with config-driven rules. Verified: with the same hash seed the new projection code
reproduces the old model.py sims exactly (all 537 players x 10k draws), and the optimizer's pool, caps, green forcing and
stack-team draws match the old optimize.py exactly. Full optimizer run on 2026-w04 (Oct 5, blend off for comparability):
150 lineups, zero rule violations, 102 of 104 players shared with the archived run, exposure corr 0.97, stack counts
within a few lineups (exact match isn't possible: sims.npy wasn't archived). Known interaction (also in the old code): the
BUF rule requires Cook, so Cook's 25 cap is shared with non-BUF lineups and Josh Allen's green target of 25 lands at 21. Known gaps: starter detection misses teams whose last starter is
inactive (TB in week 4 had no starting QB flagged); the "raise exposure cap to 40 if infeasible" rule is manual
(`[optimizer] exposure_cap` in week.toml). Team codes: FanDuel JAC/LAR vs nflverse JAX/LA (`[teams]` in defaults.toml).
Vegas lines are entered by hand; three week-4 lines were estimates.
