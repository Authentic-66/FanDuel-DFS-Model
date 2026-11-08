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
held_out_Q and notes. Check: Lineups sums to 1,350. **From week 9 also:** `RB_trend` (RBs: team's last 3 games, snap % /
carry share / target share, UP / DOWN; from `data/cache/snap_counts_<season>.csv`) and `RoleDrop` (proj.csv column
from model.py: the switch-3 flag, e.g. "snaps 40% -> 0% last game"; docs/role_guard_tests.md).
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

## Week 8 Friday run (Fri Oct 30) — statuses applied; preview sets built (not committed)
`fd_players.csv` = Friday's download (Oct 27 file kept as `fd_players_oct27.csv`). Diff: 0 salary changes, 0 added,
Demercado removed; tags cleared: Lamar, St. Brown, Rice, DJ Moore, Beck, A. Jones, Warren, J. Wright, Nwangwu; Egbuka /
B. Robinson Q -> O, Briscoe O; 22 new Q (Pickens, A.J. Brown, M. Wilson, Meyers, Tate, Allgeier, Kincaid, Kelce, ...).
FanDuel has no D tags. Rotowire report `data/2026-w08/injuries_rotowire_2026-10-30.docx` (Friday practice notes / coach
quotes) agrees with FanDuel except **DJ Moore**: Rotowire Q (shoulder), FanDuel untagged -> kept Q. `[status]` = FanDuel
O/Q + DJ Moore + the IR-volume list. **`[status.starting_qb] BAL = "Lamar Jackson"`** (default would start Huntley, BAL's
week-7 QB, and Lamar would project 0; week-7 checklist rule). Projections: Lamar 18.6, Huntley 0, St. Brown 17.9, Rice
13.2, A. Jones 12.4, Warren 9.8; new Q players ~-45% (routing), Stevenson +2.1, Bijan +1.6, Irving +1.5.
Preview sets (untracked, uploads deleted): model `friday/` 150 at cap 25 (10 lineups relief to 27), mean 120.3 (prelim
119.2); control `friday_cap45/` 150, mean 121.7; pool `pool/friday/` 150 at cap 25, mean 120.5. All 150 lineups differ
from the prelim in each set. ARI no longer stacked (M. Wilson Q). `prelim/`, `model_cap45/`, `pool/` untouched (Oct 29);
`proj.csv` / `sims.npy` are Friday's.

## Week 8 final run (Sun Nov 1, done ~10:55 CT) — entry file: weeks/2026-w08/entered_upload_149.csv (free entry)
`fd_players.csv` = Sunday 10:37 CT download (Friday's kept as `fd_players_fri.csv`). Diff vs Friday: 0 added / removed /
salary changes, 27 tag changes. Doug's sheet re-read: **5 reds cleared (Rodgers, Geno Smith, Penix, Nix, Keenan Allen),
none added -> 113 red**; pool unchanged (97). Sunday status rule: inactive / FanDuel O-NA-IR -> `out` (Breece Hall NA,
RJ Harvey IR, Henderson, A.J. Brown, Spears, Tate, Turpin, Gould, B. Thompson O; Skowronek still Q on FanDuel but
reported inactive); FanDuel-cleared Q players -> active (1pm: Love, Allgeier, Ray Davis, LeQuint Allen, Pickens,
M. Wilson, Meyers, Ridley, DJ Moore, Kincaid, Ian Thomas; **4pm games, inactives not out before the upload: McConkey,
Tre' Harris, M. Washington, Wayne, Kelce, Dulcich, Kacmarek taken as active on FanDuel's cleared tag**, 12 of 149 lineups
hold one, Kelce 8). Still Q on FanDuel, kept Q: Gainwell, Zaccheaus, Schoonmaker, Ogletree, Geers, DJ Rogers, Waddle,
Whittington, Parkinson. Jack Bech off `out` (IR tag cleared, reported playing). Lamar active (not on BAL's inactive
list): BAL starter stays Lamar (18.7, 10 stacks). Lines FINAL (nflverse 16:42 UTC: CIN -13.5, NE total 41.5, TB/ATL
43.5 ...); `[stacks.weights]` rebuilt (DAL 30, CIN 27, BUF 26, JAC 25 ... TEN 1). Projections: Pickens 8.0 -> 14.5,
M. Wilson 7.0 -> 12.3, Kelce 5.4 -> 9.9, Kincaid, Meyers, DJ Moore ~+4 (Q discount gone).
Sets (all rules checked: slots, $59-60K, no red/out/Q/FanDuel-tagged, no duplicates, stack + bring-back, DST): model
150 at cap 25 (4 lineups relief to 27), mean 120.0; **149 file drops lineup 126 (104.1), mean 120.1**; 18 stack teams
(DAL 18, CIN 15, BUF 15, JAC 13, LAR 10, BAL 10, ...); FLEX TE 95 / RB 32 / WR 22. Control `model_cap45/` 150, mean
121.1; pool `pool/` 150 at cap 25 (27 fillers), mean 120.1. First kickoff 12:00 CT (1:00 ET; DST ended Nov 1).

## Week 8 (2026-w08) result — see docs/week8_review.md
149 model lineups (cap 25, entered unchanged: all 149 matched `entered_upload_149.csv`) + 1 free entry (Doug's own,
111.7) in the Pooch Punt (566,416 entries). Model avg 106.4 vs field 120.2 (-13.8); best 190.4 (Burrow stack, rank
8,591); 0 top-1%, 10 top-10% (all CIN stacks); winner 258.38; cash line ~120 (39 of 149 cashed). **One-QB slate: Burrow
45.5, in 98.3% of the top 1,000; we had 15 CIN stacks (weight share, 10.1% vs 13.2% owned), avg 167.8; the other 134
averaged 100.1.** Won $4.57 on $7.45: **net -$2.88, running total -$6.53** (Doug, Nov 2: no other entries; the week-7
payout tiers give $4.52 on our ranks). Four sets (exact ranks): model 106.4 / 10 / 0 / 190.4; control cap 45 107.4 / 13 / 0 /
190.7; **pool 108.0 / 17 / 1 / 197.1 (rank 5,264), best set for the first time** (16 CIN stacks at 176.0); money
as-if (week-7 tiers) $4.52 / $4.91 / $5.32+. Two weeks: pool vs control -1.9, +0.6; cap 45 vs model -2.9, +1.2.
Reads as lineups (re-run as entered = 150/150): red +0.3; **clearing the 5 Sunday cost -2.6** (Rodgers 5.9, Penix 2.1
right as reds; Geno 19.0, Nix 19.3 wrong); Ward / Willis red no effect (identical lineups; Ward 29.3 at proj 10.2).
Reds as a group 4.93 projected / 4.96 scored; vs non-reds at same position / salary (proj 4+) +0.8 vs +0.9: no
signal. Big red misses Braelon Allen 25.3 (25% owned), Warren 23.8; hits Mason 2.0, Cooper 0 (15% owned).
Sunday calls right: 1pm cleared Q +1.8 a lineup over projection (M. Wilson 25.8 in 27, Pickens 5.8 in 21); 4pm cleared
all active; kept-Q and outs cost nothing. **Lamar 1 snap, 0.0** (Huntley 10 snaps, Fagnano 21 att.): BAL 10 stacks 67.3.
TB threw 3 passes (11 in week 7): Godwin / Otton 0. 75 of 149 lineups held a non-DST zero (Flowers 27, Tucker 25,
Ferguson 18 hurt, Godwin 12). RB -12.6 vs field (4th week), FLEX TE 64%. Calibration: 20+ tier +0.3 (first good week),
14-20 +2.5, beat-p90 7.7%, DST r 0.40, ownership MAE 1.2. Flags only: WR over-projection 2nd week (proj 8+ 11.5 vs
9.7; 24+ totals still +1.6 after the correction), routing bumps 10.1 -> 8.3, spread no pattern. Week-9 list: review
section 7.

## Week 8 run checklist (2026-w08)
**State Nov 2: ALL DONE (step 5 graded, docs/week8_review.md; see "Week 8 (2026-w08) result"). Next = week-9 prep.**
Earlier: **State Nov 1: FINAL RUN DONE (see "Week 8 final run"); next = step 5 after the slate.** Earlier: **State Oct 30: Friday DONE (see "Week 8 Friday run"). Next = Sunday: re-download `fd_players.csv` (keep Friday's as
`fd_players_fri.csv`) and diff; FINAL lines + `[stacks.weights]`; after inactives (~10:30 CT) apply the Sunday status rule
below, `model.py`, then the three final sets. **Doug has a free entry in week 8 (confirmed Oct 30): write the 149 files for the model set
(`entered_upload_149.csv` etc., drop the lowest-projected lineup).**
**Sunday status rule (Doug, Oct 30): after inactives, every player on `[status] questionable` who is ACTIVE comes off the
Q list before the final run (standard treatment, no hand adjustments); inactive ones move to `out`. Doug makes the calls
on the Friday non-practisers (A.J. Brown, Henderson, Spears, Tate, ...). Re-check BAL = Lamar.**
1. FanDuel player list: download when the slate opens (`data/2026-w08/fd_players.csv`); **re-download Friday and
   Sunday morning**, keep the earlier file, run `python src/diff_players.py <earlier> <new>` and report added /
   removed players and new tags to Doug before re-running `model.py`. Confirm the slate against week.toml's list.
2. Preliminary run (week-7 recipe): stats cache refresh (`fetch_stats.py`, week 7 in), PRELIMINARY nflverse lines ->
   `data/2026-w08/lines.csv` and `[stacks.weights]` = round(2 x (implied - 16)), min 1; `[status]` from FanDuel tags +
   IR players with 3+ targets + carries a game; `model.py`, read the role-guard and team-mismatch warnings; prelim
   optimizer run in `weeks/2026-w08/prelim/`; review sheet (recipe in the week-7 checklist). Check the FLEX mix.
3. Doug's sheet: red -> `[prefs] red` (+ `[shadow.red_lineups]`), **yellow -> `[shadow.yellow]`**, green ->
   `[shadow.green]`, Pool / Rank -> `[pool]` (pool kept weeks 8-9). Extra receivers only if Doug names them.
4. Friday statuses (DONE Oct 30), Sunday lines (FINAL), **Sunday inactives: active Q players off the Q list, inactive
   -> out, rerun `model.py`**, final `optimize.py --week 2026-w08`, control `--subdir model_cap45 --cap 45`,
   `optimize.py --week 2026-w08 --pool`; 149 files if Doug has a free entry. Cap 25 (standing); if a set stalls, stop and ask Doug.
5. After the slate: `convert_results.py`, `[contest] field_size`, `analyze_results.py`, `docs/week8_review.md`,
   ask Doug for winnings (running total -$3.65 after week 7). Check his entries match `entered_upload_149.csv`. In
   the review, grade the Sunday status calls: 4pm-game Q players taken as active on FanDuel's cleared tag (McConkey,
   Tre' Harris, Kelce, Dulcich, M. Washington, Wayne, Kacmarek; 12 lineups) and early-game players kept Q though
   possibly active (Gainwell, Zaccheaus, Schoonmaker, Ogletree, Geers, DJ Rogers). Lesson to weigh: the 10:37 CT
   list came 7 minutes after the 1pm inactives, so some early-game tags hadn't updated yet.

## Week 9 preliminary run (Tue Nov 3) — inputs only; checklist steps 0-2 DONE
Slate: 11 games / 22 teams, matches nflverse (568 players, `fd_players.csv` downloaded Nov 3 07:59; keep it as the base
for Friday's diff): DEN@CAR, DAL@IND, NYJ@KC, DET@MIA, CLE@NO, NYG@PHI, LAR@WAS, HOU@LAC, LV@SF, GB@NE, ARI@SEA. Off:
JAX@BAL (Thu), CIN@ATL (London), TB@CHI (SNF), BUF@MIN (MNF); byes PIT, TEN. **BAL (Lamar) and TB are not on the
slate**: no starting-QB call, no TB volume question this week. `config/2026-w09/week.toml` = week 8's with the pins
DELETED; **confirmed live** (in-process, nothing written): one-sided WR -0.57 moves 45 players (JSN -1.3, St. Brown /
Lamb -1.2, Nacua -0.9), bump_scale RB .8 / WR .45 / TE .3 moves 93 (Chism -1.4, Higbee / R. White -1.2). Stats through
week 8 (28 teams incl. MNF); `data/cache/snap_counts_2026.csv` fetched (nflverse snap_counts release, untracked).
Lines PRELIMINARY (nflverse Nov 3 14:02 UTC): SF 30, DAL / DET 26, KC / SEA 24, LAR 21, NE 18 ... ARI 1. `[status]` =
FanDuel tags (Bourne O, McNichols D -> out; 30 Q) + 26 IR players with 3+ targets + carries a game.
Carry-overs: Harrison 0.15 / 0.9 runs (HOU on the slate; HOU WR2, 7.0; no starter override needed; 3rd HOU game ->
remove the entry after week 9); Jacobs projects as GB's lead back without a read (16.2; 58% -> 81% of carries, 52 -> 71%
snaps); **McCaffrey Q (hamstring)** after the bye, held out (12.7 if cleared; 52% snaps week 7); **Stafford Q (arm), LAR's
starter: 0 LAR stacks** (weight 21 reallocated); Ferguson Q (ankle; 4 snaps week 8, DAL TE1 = next eligible); ARI QB:
week 8 Brissett 23 att / 47 snaps, Minshew 23 att / 34 snaps (tie, both 23); default starts Brissett (14.8), ARI weight 1.
Model warnings: FanDuel team differs from stats for Demercado (HOU, was DAL), Wayne (MIA, was HOU), Kaytron Allen (MIA,
was WAS); role guard 0: Mafah (NYG, no 2026 data), Kirk (SF), Browning, Gabriel, Estime and others.
Prelim sets (uploads deleted, all rules checked: slots, $59-60K, no out / Q / tagged, no duplicates, stack + bring-back,
DST): model `prelim/` 150 at cap 25 (relief to 26), mean 115.9, FLEX TE 57 / RB 52 / WR 41; control `model_cap45/` 150,
mean 117.4 (max JSN 43); flex shadow `flex_shadow/` 150, mean 117.1, FLEX RB 83 / TE 44 / WR 23 (every two-TE lineup has a
top-5-salary TE). Stacks (all three): SF 15, DAL / KC / DET 13, SEA 12, NE 10, NO / IND / DEN 8, HOU 7, ... ARI 1, LAR 0.
**SF stacks all use Jordan Watkins (4.8)**: Evans / Deebo Q, Kirk / Cooks role-guarded. Review sheet
`data/2026-w09/review_sheet.xlsx` (226 rows, Lineups 1,350) with a new **RB_trend** column (last 3 team games: snap %,
carry share, target share, UP / DOWN) for Doug's RB greens. RB notes: SEA's Emanuel Wilson (RB1 by projection, 11.0)
had 0% snaps in week 8 (Charbonnet 37%, Price 48%); Jeanty 6% of LV carries week 8.
**Rebuilt Nov 3 afternoon with promotion ON (6340035):** 11 promoted (Raridon 5.4 and K. Williams 5.0 enter the pool;
Gray 4.0, Allen 3.9, Franklin 3.8, Cooks 3.4, ...). Model `prelim/` mean 115.7, FLEX TE 60 / RB 56 / WR 34, 62 of 150
lineups unchanged, Raridon 6 / K. Williams 3, Chism 10 -> 1; control mean 117.2 (JSN 41); flex shadow mean 116.8. Stack
counts unchanged. Rules checked, uploads deleted. Review sheet rebuilt (237 rows, Lineups 1,350) with **RoleDrop**
(E. Wilson, Lambert-Smith; Cody White is still guarded so not listed) and **Promoted** columns.

## Week 9 review applied (Thu Nov 5) — sheet loaded, pool built
Doug's sheet `data/2026-w09/review_sheet_reviewed.xlsx` (typed colours, no fills; his notes in Rank / an unnamed column).
**7 red, 0 yellow, 0 green, 0 DST red:** QB Darnold ("Darnold is out"), Brissett (typed "red0": "No longer starter");
RB Jeanty, Ollie Gordon II, Braelon Allen, Hampton (run-defence notes), Emanuel Wilson ("third on the depth chart").
Notes applied as statuses: `[status] out` + Darnold, `[status.starting_qb]` SEA = Drew Lock, ARI = Gardner Minshew II
(Minshew 13.0, Lock 9.5; SEA receivers unchanged: only lines move them). **Lock is still FanDuel Q (elbow) -> SEA 0
stacks**, as LAR (Stafford Q): Friday decides both. Charbonnet ("now listed as the starter") is SEA RB1 only because he
projects 11.0 vs Wilson 10.9 (reds don't free depth). **Doug, Nov 5: `[prefs.starter_override] SEA = Charbonnet`**
added (prelim rebuilt byte-identical: he was already RB1). Doug confirmed: no greens (intentional), Darnold / Lock /
Minshew status calls kept, all 5 RB reds kept.
**Pool: 94 Y = QB 21, RB 18, WR 27, TE 18, DST 10; no ranks (Doug: membership only) -> `[pool] ranked = false`.**
Held out Q: Stafford, Lock, McCaffrey, Watson, M. Wilson. Short of two pool receivers: Purdy, Cousins, Willis,
Herbert, Minshew (1 each), Geno Smith (0: NYJ dropped). Pool 150 at cap 25, mean 116.3, 136 lineups use a filler
(Watkins 17, M. Washington 12, Flournoy 10, ...; week 8: 10), 4 identical to the model.
Rebuilt after model.py: model `prelim/` 150 (mean 115.5, FLEX TE 75 / WR 43 / RB 32; relief to 27), control 150 (117.2),
flex shadow 150 (116.3); rules checked, uploads deleted. Reds' own effect (statuses-only build vs with reds): stacks
unchanged; Jeanty 25 / Gordon 24 / Allen 14 / Hampton 8 -> 0, to R. White +10, Barkley +8, Judkins +7, Marks +6, Black +5,
Singletary +5; 69 of 150 lineups unchanged. LV / MIA / NYJ / LAC have no model-set RB (red holds the RB1 slot).

## Week 9 Friday run (Fri Nov 6) — statuses applied; preview sets built (not committed)
`fd_players.csv` = Friday's download (Doug saved it as `fd_players_fri.csv`, kept; Nov 3 file kept as
`fd_players_nov03.csv`). Diff: 0 added, 0 salary changes; removed Brissett (ARI QB) and Slovis; 44 tag changes.
**Cleared (no designation on FanDuel or Rotowire): Stafford, Lock, McCaffrey, M. Wilson, Breece Hall, C. Watson,
Theo Johnson, Gould.** New O: Evans, Deebo, **Christian Kirk** (knee, meniscus), DeVonta Smith, Garrett Wilson,
A.J. Brown, Montgomery, Henderson, Shaheed, Wicks, Burks, Dyami Brown, Bam Knight, Donaldson, Turpin, Covey, Whyle,
Yeboah; D: Skattebo, Brenen Thompson; Love Q -> IR. New Q: St. Brown (ribs), Pickens, Deshaun Watson, McKee, Lloyd,
Vaki, J. Wright, Kaytron Allen, Whittington, Charlie Jones. Rotowire (`injuries_rotowire_2026-11-06.txt`, now a tab
text file, not .docx) agrees with every FanDuel tag on the slate except Yeboah (FanDuel O, kept out).
`[status]` = Darnold + FanDuel O / D (21) + IR with 3+ targets + carries a game (29) out; FanDuel Q (16) questionable.
**`[status.starting_qb] CLE = "Shedeur Sanders"`** (Rotowire Nov 6: he starts even if Watson is active). He projects
**0** (no 2026 data, 3 attempts) -> CLE 0 stacks either way (weight 9); needs a Doug [overrides] read to be used.
Projections: Stafford 12.0 -> 20.0, Lock 9.5 -> 16.8, McCaffrey 12.7 -> 19.5, C. Watson 8.8 -> 15.7, Allgeier 10.0 ->
15.7, Singletary 10.7 -> 16.1, Breece Hall 7.0 -> 12.3, M. Wilson 6.7 -> 12.0; St. Brown 16.0 -> 9.4, Pickens 12.7 ->
7.1 (Q discount; held out). SF WRs: Watkins 5.2, Cooks 3.8 (promoted), Cowing 3.1 (promoted).
Practice (nflverse injuries_2026.csv week 9, undated = latest report): **Nabers DNP (knee), no designation anywhere**;
Diggs DNP (rest). Both active.
Lines NOT refreshed (Tuesday's file; Sunday pulls FINAL). nflverse Nov 6 vs Tuesday: **ARI@SEA total 44.5 -> 39.5,
SEA -11.5 -> -8.5 (SEA implied 28.0 -> 24.0, weight 24 -> 16)**; NYJ@KC 46.5 -> 48.5; GB@NE 46.5 -> 44.5; NYG@PHI
40.5 -> 38.5 (NYG -3.5 -> PHI -3); HOU -4.5 -> -6; CLE@NO 43.5 -> 42.5 (NO -3.5); DEN@CAR 44.5; DET@MIA 49.5.
Preview sets (untracked, uploads deleted; all rules checked: slots, $59-60K, no out / Q / red / tagged, no duplicates,
stack + bring-back, DST): model `friday/` 150 at cap 25 (5 relief to 27), mean 120.0, FLEX RB 63 / TE 59 / WR 28;
`friday_cap45/` 122.5; `pool/friday/` 120.3 (131 fillers; NYJ no pool receivers); `friday_flex/` 120.9;
`friday_nodraw/` 122.5; `friday_median70/` 117.9 (FLEX RB 133). Stacks (model): SF 16, DET 14, DAL 13, KC 13, **SEA 11,
LAR 10**, NE 9, ... CLE 0. SF stacks all Purdy + Kittle + Watkins (McCaffrey not an extra receiver). LAR = Stafford +
Nacua + Higbee; SEA = Lock + JSN / Horton / Kupp.
**Dry run 75 median70 + 74 model** (`combine_entry.py --a friday_median70:75 --b friday:74`, files moved to
`friday_entry_dryrun/`, upload deleted): 149, 0 duplicates, all checks passed; top: **Allgeier 45.6%, Singletary 43.0%**,
Gibbs 40.3, Nacua 32.2, JSN 29.5, C. Watson 27.5, Jacobs 27.5, Kittle 24.2, NO DST 18.1, Stevenson 18.1, LaPorta
17.4, Kelce 15.4, Bowers 14.1, Lamb 14.1, Kyren 13.4. **None over 50%** (Kyren / Jacobs down from 44 / 45 on Tuesday).
Non-practisers with exposure in the dry run: Nabers 18 (12.1%), Diggs 11 (7.4%). Doug decides Sunday after inactives.
FDR Friday file (476 rows): 86 names not on FanDuel's list = 41 kickers / D/ST ("Seattle D/ST" vs "Seattle
Seahawks"), ~20 suffix / nickname forms (Deebo Samuel, Gardner Minshew, Zonovan Knight = Bam, Marquise Brown =
Hollywood, Tre Harris, Chigoziem Okonkwo, Andrew Ogletree = Drew, Velus Jones, ... Jr. / II), rest not on the list.
Record only.

## Week 9 final run (Sun Nov 8, done ~10:45 CT) — entry file: weeks/2026-w09/entered_upload_149.csv (free entry separate)
`fd_players.csv` = Sunday 10:30 CT download (`fd_players_sun.csv`, kept; Friday's `fd_players_fri.csv`). Doug saved the
list under the FDR name first and renamed it: **no `fdr_projections_sun.csv` this week** (FDR test: week 9 Friday only).
Diff vs Friday: 0 added / removed / salary; 10 tag changes (Hollins, Pat Bryant, Pierce IR -> Q; Tyson IR -> Q; Remigio
new Q; Demarcus Robinson, Rivers IR cleared; Velus Jones Q cleared; Kirk, Dyami Brown O -> IR).
**Statuses set BEFORE official inactives were posted (news only, ~10:35 CT):** St. Brown ACTIVE (Pelissero: "officially
good to go"; still Q on FanDuel's list, 17 lineups); **Pickens kept Q** (Dallas only "hopeful"; 0 lineups); Skattebo
out (D, no practice); Nabers active (no tag); Hunter Henry, Deshaun Watson, Jaylen Wright out (reported); Velus Jones
active; Robinson / Rivers off `out`; Hollins / Bryant / Pierce / Tyson / Remigio Q. PHI starts Joe Milton III (no 2026
data, projects 0 -> PHI 0 stacks).
Lines FINAL (nflverse games.csv, Sunday): SEA -8.5 / 39.5, NYG -3 / 38.5 at PHI, HOU -5.5, DAL -4.5 ... weights SF 29,
KC 25, DAL / DET 24, LAR 20, NE / SEA 16 ... ARI 1. `model.py` rerun, then all six sets 150 each (model, median70, nodraw,
model_cap45, pool, flex_shadow). combine_entry 100 median-70 + 49 model: 149, 0 duplicates, all checks passed; 25 elite
(St. Brown skipped: FanDuel Q tag -> Olave); top Allgeier 53.0%, JSN 52.3, Singletary 51.7; **none over 70%, no rebuild**.
Combined stacks SF 17, KC 15, DAL 13, DET 13, LAR 10, ... CLE / PHI / ARI 0. First kickoff 12:00 CT.
**Free entry = Doug's HAND-BUILT lineup (Nov 8):** Goff, Gibbs, Allgeier, D. Douglas, Golden, Lamb, Likely, Kaelon Black
(FLEX), Saints DST, logged in `docs/my_own_lineups.md` (new NFL own-lineups tally; never in model grades / totals).
**Monday review: grade it separately** (score, rank, won, from his entry in the results export; settle which Douglas from
the ids: DeMario NE or Caleb MIA), split his winnings between the 149 and the free entry, update the tally.

## Week 9 run checklist (2026-w09) — START HERE when FanDuel releases the week-9 player list
**State Fri Nov 6: Friday DONE (see "Week 9 Friday run"). Next = Sunday: re-download fd_players.csv (diff vs
`fd_players_fri.csv`), save fdr_projections_sun.csv, FINAL lines + weights (SEA moved -4), inactives (Sunday rule;
Doug's calls on Nabers / Diggs), then the six builds + combine_entry (step 5): **100 median-70 + 49 model, flag over 70%** (Doug, Nov 6).**
**EXPOSURE RULE (Doug, Nov 6, built into combine_entry.py):** elite players have NO exposure cap = top 5 at their
position (QB/RB/WR/TE/DST) by FanDuel 2026 FPPG among players with 4+ games played, with no FanDuel injury tag and their
normal role (RoutingBump < 1.0, no RoleDrop, no GuardRescue, QB = starter); **BACKFILL (Doug, Nov 6, later): a
player who fails is skipped and the next eligible moves up, so each position has 5 elite when available.** Any non-elite player over 70% of the 149 (104 lineups): the model is rebuilt without him
into `weeks/2026-w09/model_excl/` (`optimize.py --exclude`, needs --subdir; main model folder untouched and still
graded) and recombined until all non-elite are <= 70%. **Report the elite table and any rebuild to Doug.** Friday
data: 25 elite (St. Brown Q skipped, Olave moves up); Allgeier 54% / Singletary 52% top non-elite, no rebuild needed (forced test at
50% rebuilt without both, 0 of 150 in model_excl, each 70 lineups = their median-70 share).
**Doug, Nov 6: (1) Shedeur gets NO projection: CLE stays at 0 stacks; CLE's other players (Judkins 14 Friday
lineups, Boston, Fannin) stay eligible as normal players. (2) Sunday, after inactives and BEFORE the final run,
confirm and report: Skattebo (D; drives Singletary's 43% exposure), St. Brown (Q), Pickens (Q), Nabers (knee DNP, no
designation).** Apply the Sunday status rule to each, then rebuild.
**State end of Nov 5 (pushed, d7f2ca1): step 4 DONE** (see "Week 9 review applied"): 7 reds, no greens, pool 94 Y
(ranked = false), SEA = Lock (Q), ARI = Minshew II, Charbonnet override; prelim / control / flex shadow / pool rebuilt.
**Friday (Nov 6) order:** Stafford status (LAR 0 stacks while Q), **Lock status (SEA 0 stacks while Q; if Lock is out
too, ask Doug who starts)**, re-download fd_players.csv + diff vs the Nov 3 file, statuses from the injury report,
save fdr_projections_fri.csv, rerun model.py and all sets (check Charbonnet stays eligible).
**State end of Nov 3 (all committed and pushed, head 7698fda):** Nov 3 additions: exact Pooch Punt money grading
(`data/2026-w09/prizes_pooch-punt.csv`), cash shadows `--no-draw` / `--median70`, and the **entered set = 75 median-70
+ 74 model via `src/combine_entry.py`** (step 5). Sunday order: final model build, median70, nodraw, cap 45, flex
shadow, pool, then combine_entry; report combined exposure (top 15, >50% flags) to Doug before upload.
**State Nov 3 evening: steps 0-2 DONE, prelim REBUILT with role-guard promotion ON (see "Week 9 preliminary run" and "Role guard and injury-driven role changes"); review sheet rebuilt with RoleDrop + Promoted columns, unmarked. Friday order: Stafford status FIRST (LAR stacks), ARI QB (Brissett unless Doug says Minshew), SF Kirk / Cooks (guarded unless Doug overrides), statuses + player-list diff, save fdr_projections_fri.csv. Next = Doug's sheet (step 4: colours, Pool / Rank,
RB greens shadow), then the pool build; Friday statuses.** Earlier: **State Nov 2: all week-9 tests done and decided (docs/week9_tests.md s1-10, docs/learn_from_winners.md). Nothing
built for week 9 yet: `config/2026-w09/` and `data/2026-w09/` do not exist.**
0. **New week.toml = copy week 8's, then DELETE the as-entered pins** (they keep weeks 4-8 reproducible and must not
   carry over): `[model.injury] bump_scale = {1.0...}` and `[model.implied_sensitivity] one_sided = false / WR = -0.34`. (From week 10: also delete `[model.role_guard] promotion = false`, the
   week 4-8 pin; week 9 has none.)
   Week 9 runs the new defaults (WR one-sided -0.57, bump_scale RB 0.8 / WR 0.45 / TE 0.3). Keep the WR depth split
   (`within_position = "depth_rank"`, `depth_rank_positions = ["WR"]`) and `stack_allocation = "proportional"` unless
   Doug says otherwise. Empty: `[status]`, `[overrides]`, `[prefs] red`, `[shadow.*]`, `[stacks.weights]`,
   `[stacks] extra_receivers` (Doug adds per week), `[contest]` field_size. Pool: kept for week 9 (Doug, Oct 26), the
   lists come from his week-9 sheet; pool review after week 9. `[grading] extra_sets = ["model_cap45", "flex_shadow", "nodraw", "median70"]`.
   Check the slate (byes / Thursday / SNF / MNF teams) against nflverse schedule_2026.csv.
1. FanDuel player list -> `data/2026-w09/fd_players.csv`; re-download Friday and Sunday, keep the earlier file and run
   `python src/diff_players.py <earlier> <new>`; report added / removed / tag changes before re-running model.py.
2. Prelim (week-8 recipe): `fetch_stats.py` (week 8 in), PRELIMINARY nflverse lines -> `lines.csv`, `[stacks.weights]`
   = round(2 x (implied - 16)), min 1; `[status]` from FanDuel tags + IR players with 3+ targets + carries a game;
   `model.py` (read role-guard / team-mismatch warnings); prelim optimizer run in `weeks/2026-w09/prelim/`; review sheet
   (recipe in the week-7 checklist). Check the FLEX mix.
3. Carry-overs to raise with Doug at the prelim: **McCaffrey** status (left week 7 hurt; SF bye week 8), **Jacobs** read
   (GB lead back: 11 car + 7 tgt, then 21 + 6), **Harrison** trade 0.15 / 0.9 applies if HOU is on the slate (remove the
   entry after ~3 HOU games), **Lamar** (1 snap week 8; BAL starter call via `[status.starting_qb]`), Jake Ferguson
   (4 snaps), ARI QB (Minshew 42% of snaps), TB pass volume (3 and 11 attempts).
4. Doug's sheet: red -> `[prefs] red` (+ `[shadow.red_lineups]`; DST reds as usual), yellow -> `[shadow.yellow]`,
   green -> `[shadow.green]` (**he will green RBs with clear role increases: shadow only**), Pool / Rank -> `[pool]`.
   Read-back rules in the week-7 checklist (counts per position, mismatches listed, Doug fixes the sheet).
4b. **FanDuel Research projections (Doug, Nov 3; weekly, record only):** Doug saves FDR's main-slate projections CSV
   Friday and Sunday morning as `data/2026-w09/fdr_projections_fri.csv` / `fdr_projections_sun.csv`. Check the
   names match `fd_players.csv` (list any that don't) and commit them with the week's files. Not used by the model.
   See "FanDuel Research projections test".
4c. **Doug's prelim notes (Nov 3), for Friday:** (1) **Stafford's Friday status FIRST THING** (LAR's starter; Q = 0
   LAR stacks, weight 21). (2) ARI QB: keep Brissett (default) unless Doug says ARI named Minshew; then
   `[status.starting_qb] ARI = "Gardner Minshew"` (check the FanDuel name). (3) SF: if Evans and Deebo are both out,
   the guard keeps Kirk / Cooks at 0 (unguarded they project 6.4 / 3.8; see "Role guard and injury-driven role
   changes"); no change unless Doug gives an [overrides] read.
5. Friday statuses; Sunday: FINAL lines + weights, inactives (active Q off the Q list, inactive -> out; Doug's Sunday
   rule in the week-8 checklist), rerun `model.py`, then the sets: final `optimize.py --week 2026-w09` (cap 25,
   entered), control `--subdir model_cap45 --cap 45`, `optimize.py --week 2026-w09 --pool`, and the flex shadow
   `optimize.py --week 2026-w09 --flex-shadow` (cap 25, not entered), and the **cash-style shadows (Doug, Nov 3;
   weeks 9-10, not entered)** `optimize.py --week 2026-w09 --no-draw` (projection-only objective, cap 25 -> nodraw/)
   and `--median70` (median objective, cap 105, overlap 7 -> median70/).
   **ENTERED SET CHANGED (Doug, Nov 3 evening): 75 median-70 + 74 current-model lineups; Doug, Nov 6: SUNDAY SPLIT
   100 median-70 + 49 model (his call; combine_entry defaults now 100 / 49), no duplicates, free entry as
   usual** -> `python src/combine_entry.py --week 2026-w09` (after the main and median70 builds) writes
   `entered_upload_149.csv` / `entered_readable_149.csv` / `entered_exposure.csv` / `entered_source.csv` (lineups
   evenly spaced through each build so each half keeps its stack mix; checks slots, cap, player list, out / Q / reds,
   duplicates; prints combined exposure top 15 and flags players over **70%** (Doug, Nov 6: over 50% is acceptable
   at 100 / 49, max-entrants run their top player ~66%): **report both to Doug**). All five full
   150 sets stay in their folders for grading (model = main folder, median70, nodraw, model_cap45, flex_shadow).
   Dry run on the prelim (Nov 3, scratch): 149 built, 0 duplicates, all checks passed, top Jacobs 45% / Kyren 44% /
   NO DST 37% (median70 alone has both RBs at 105 of 150), none over 50%. If a set stalls at cap 25, stop and ask
   Doug (no cap raise without him).
6. After the slate: `convert_results.py <export> --user gst1999`, `[contest] field_size`, `analyze_results.py` (grades
   model / control / pool / flex_shadow / nodraw / median70; with `data/2026-w09/prizes_pooch-punt.csv` (Doug's
   Prizes-tab screenshot, transcribed Nov 3: $35,000, pays ranks 1-265,100) and the All Entries export in raw/, every
   set gets exact cashed / won / net as if entered), `learn_from_winners.py --week 2026-w09` and `--compare
   2026-w05,...,2026-w09`, `docs/week9_review.md`. **Must include: Doug's RB greens vs projection and vs salary-matched
   non-green RBs** (plus the shadow-green lineup re-run), flex shadow vs entered, cap 45 vs 25, pool review, the
   carry-over calls (step 3), **Doug's RB reds split by reason, grouped by his sheet notes (Doug, Nov 5): role/news =
   E. Wilson (3rd on the depth chart); matchup = Jeanty (vs SF run D), Hampton (vs HOU), Ollie Gordon II (vs DET),
   Braelon Allen (vs KC): each group's actual vs projected, and what
   removing each group alone changed (lineup re-run with only that group red vs no reds)**, and winnings (ask; check the entry-history xlsx; running total -$6.53 after week 8).
   **Also the promotion kill-rule check** (Doug, Nov 3): every player in the final proj.csv with `GuardRescue` set and
   Proj 4+, projected vs actual FanDuel points (and the role-drop flags vs actual). Kill rule: if over weeks 9-10
   combined they under-score their projection by 1.5+ points on average, set `promotion = false` in defaults.toml and
   tell Doug (week 10 review decides; week 9 alone is reported, not acted on).

## FanDuel Research projections test (Doug, Nov 3) — collect weeks 9-12, test after week 12; NOTHING LIVE
- **Every week from week 9:** Doug downloads FanDuel Research's main-slate projections CSV Friday and again Sunday
  morning, saved as `data/<week>/fdr_projections_fri.csv` and `fdr_projections_sun.csv`. Archive them with the weekly
  files (commit; `data/<week>/*.csv` is tracked). On the first file, record its columns and match its names to
  `fd_players.csv` (aliases if needed). Projections and lineups never read them.
- **After week 12 (4 weeks, 9-12): does FDR's projection predict actual points beyond ours?** Same regression as the
  ownership test (`docs/week9_tests.md` section 8.1): rows = every slate player with a result and an as-entered
  projection of 4+; residual = actual FanDuel points minus our as-entered (Sunday final) projection; regress it on
  FDR's Sunday projection (also as FDR minus ours), controlling for position, log salary, week and our projection;
  standard errors clustered by game. Report the coefficient, se, p, each week's sign, and by position; repeat with
  the Friday file (does Sunday's news add anything?).
- **Only if it does: test a blend** (as section 8.3): nested leave-one-week-out blend weight (held-out week never
  used to fit), projection accuracy (MAE / bias) and lineups re-built as entered, reporting average, top-10%,
  top-1% and best per week. Doug decides; nothing adopted automatically.

## Role guard and injury-driven role changes (proposal Nov 3; BUILT + TESTED Nov 3; DECIDED Nov 3)
**Doug, Nov 3: promotion ON from week 9** (defaults.toml `promotion = true`; weeks 4-8 week.toml pin `promotion =
false`, checked: weeks 7-8 rebuild identical). **Snap projection NO. Role drop: flag only, no scaling.** **Kill rule:**
each weekly review reports the players promotion lifted to 4+ (projected vs actual); if they under-score by 1.5+ points
on average over weeks 9-10 combined, turn promotion off and tell Doug. New week.toml files must NOT copy the
`promotion = false` pin from weeks 4-8.
**Results: docs/role_guard_tests.md.** Switches in defaults.toml `[model.role_guard]` (promotion, snap_projection,
role_drop_action), code in src/dfs/snaps.py + project.py, history test `src/fit_role_guard.py`. Off = projections and
draws identical (weeks 5-9 checked). Recommendation: **1 promotion YES narrowly** (history bias -3.29 -> 0.00, RMSE
5.29 -> 3.99; weeks 5-8 avg -0.29, top-10% 34 vs 35, top-1% 1 vs 0, money +$0.75; live 4+ promoted 5.09 vs 3.01, n 31:
watch); **2 snap projection NO** (fires twice in 3 seasons); **3 role-drop scale NO, flag kept** (history better, n 44,
but live Skattebo / Hockenson wrong; the flag prints in model.py and fills proj.csv RoleDrop: reporting only, live).
If Doug turns promotion on: pin `promotion = false` in weeks 4-8 week.toml, re-run model.py + sets.
Why the guard misses promotions: it tests `RoleVol` = the player's own 2026 targets + carries per game over ALL his
2026 games, before routing; volume inherited from OUT teammates (`GainedVol`) never counts, and a player active with
no stat row (Kirk: SF week 7, 30% snaps, 0 targets) is "no 2026 data". SF scenario (Evans + Deebo OUT, in-process):
guard on Kirk 0 / Cooks 0; guard off **Kirk 6.4** (FanDuel FPPG fallback = his 2025 HOU role) / **Cooks 3.8** (still
below min_proj 4). Routing adds little (Cooks +0.7, Watkins +0.4) because both have been absent since weeks 6 / 5,
so SF's current usage already reflects it. Week 7, the one game without both: targets Kittle 10, McCaffrey 7, Watkins
6 (76% snaps), Cowing 5, Cooks 3 (68% snaps), Black 3, Kirk 0 (30%). So the model's Watkins-as-WR2 matches the evidence;
Cooks' snaps rose 12 -> 40 -> 52 -> 68% weeks 4-7 without the targets following.
Proposed (each a switch, OFF, history-tested weeks 4-8 + 2023-25 with nflverse snap counts before Doug decides):
1. **Promotion path:** the guard passes a player if RoleVol + GainedVol >= 3 (inherits a starter ruled out this week),
   OR his targets + carries per game over the team's last 2 games >= 3 (role already grown), OR he played 50%+ of
   snaps in the team's last game. Cooks would pass on snaps (68%), projecting 3.8.
2. **Active-but-no-stats players** (snap row, no stat row, like Kirk): project from recent snaps / role, not the
   FanDuel FPPG fallback; stay 0 below 50% snaps.
3. **Reverse case, role drop (Emanuel Wilson: SEA RB1 by projection 11.0, 0% snaps week 8 while Charbonnet 37% and
   Price 48% appeared):** flag, don't zero: a player active last game with under 10% snaps after averaging 30%+, and
   not on the injury list, goes in the prelim warnings and the review sheet (Doug reds or reads him). A
   recency-weighted volume option tested on history alongside.

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
- **Week 9 carry-overs:** McCaffrey's status (left week 7 injured; SF bye in week 8); Jacobs' read (two games: 11 car
  + 7 tgt, then 21 car + 6 tgt: GB's lead back); Harrison 0.15 / 0.9 applies (HOU back on the slate, if it is); pool
  review after week 9. New from the week-8 review: Lamar (left after 1 snap; BAL starter call), Jake Ferguson (4 snaps),
  ARI QB (Minshew 42% of snaps), TB pass volume (3 and 11 attempts). Flags to test on history (no change yet): WR
  over-projection / stronger WR correction at 24+ totals, routing bump size, RB vs field + TE flex.
- **Week-9 tests DONE Nov 2 (docs/week9_tests.md; nothing changed, Doug decides before the week-9 prelim):**
  1 RB/flex NO (RBs calibrated; gap = flex choice; TE slope 0.53 above 10 better in history but -0.6 a lineup, flex TE
  only -9/week; TE-flex cap -0.2, stalls week 7). 2 WR YES, one-sided refit b -0.57 (no raise below 22.5; history bias
  +0.72 -> +0.35, RMSE 7.099 -> 7.073; lineups 0.0); Doug's 24+ term c 0.27 works but smaller. 3 routing YES, bump x k
  by out position RB 0.8 / WR 0.45 / TE 0.3 (history k 0.61-0.73 every season; moved bias +1.23 -> +0.06; live wks 6-8
  kept 20%; lineups -0.4). 4 bad-defence games NO (28 games 2020-25; Vegas totals already +4.4; (a)/(b) no edge,
  underdog side +1.2 = all underdogs; (c) corr 0.43 vs 0.24 p 0.28). Underdogs in general beat FD expectation ~2.5 vs
  favourites (p 0.003), mostly already in the projections. Yes items need code built OFF + week pinning.
  Scratch scripts were in the Nov 2 session scratchpad (w9/), not in the repo.
- **Doug, Nov 2: tests 2 and 3 ADOPTED, ON from week 9 (defaults.toml); tests 1 and 4 no change.** WR correction:
  [model.implied_sensitivity] one_sided = true, WR = -0.57 (project.implied_shift). Injury bump: [model.injury]
  bump_scale = {RB 0.8, WR 0.45, TE 0.3} (usage.redistribute_out; also Q routing; trades NOT scaled). Weeks 4-8 pin
  bump_scale 1.0, weeks 7-8 pin one_sided false / WR -0.34; weeks 4-8 rebuild bit-identical (proj + sims). tests/test_week9.py.
  Week 8 under the new defaults: 202 of 482 players' draws move; the largest drops are high-total WRs (Lamb -1.8,
  Douglas -1.9) and bumped teammates (bump 1+: 2.24 -> 1.32 avg). WATCH ITEM for next season: bad-defence games' FD
  scoring correlation 0.43 vs 0.24 (n=28, p 0.28): recheck with 2026 added.
  RB reds check (docs/week9_tests.md s5): reds NOT the main RB-gap driver (wk5, no reds, gap -19.4); gap mostly fewer
  RBs (2.2 vs 2.6/lineup) + non-red RBs; but RB reds cost +2.2 (wk7) / +1.0 (wk8) a lineup, 10.4 of wk8 12.6 gap.
- **RB/flex (week9_tests s6-7, Nov 2): NO live change (Doug agreed).** Stack rule not the cause (no lineup needs 2 TEs;
  RB bring-backs allowed); RB sims calibrated (p90 10.1% / p95 5.4%); flex TEs beat the passed-over RBs +0.4; history
  TE tiers <8 / 8-10 / 10-12 / 12+ bias -0.1 / +0.5 / -0.2 / +2.6: no mid/low fix.
  **SHADOW BUILD weeks 9-10:** after the real final build run `optimize.py --week 2026-w09 --flex-shadow`
  (-> weeks/<week>/flex_shadow/; RB stack pieces + TE flex top-5 by salary) and put "flex_shadow" in the week's
  `[grading] extra_sets` so Monday grades it. Not entered. Same for week 10.
- **Tests 8-10 (week9_tests s8-10, Nov 2; nothing changed, Doug decides):** 8 ownership signal REAL but NOT usable:
  actual ownership beats our projection +1.42 per log unit (~+1 pt per doubling, p < 0.001, every week; QB +3.5,
  RB +2.1), but projected ownership (LOWO, + news / position slopes, MAE 2.60) carries none of it (-0.39, p 0.74);
  blend lineups 103.8 vs 104.9 as entered (top-1% 1 -> 0); actual-ownership ceiling 108.0 / top-1% 4. Needs an
  outside pre-lock ownership source. 9 cheap DSTs NOT under-projected (live +1.1, se 1.1, only wks 6-7; history weak
  matchups -0.28); our weeks 7-8 shortfall = reds (3 of 8 / 7 of 8 cheap DSTs red; reds right on points). 10 cap swap:
  cap 45 - 25 avg +5.5 / +1.9 / -2.9 / +1.2, top-1% level, best worse 2 of 4, p10 -1.0, money +$0.18/week; nothing
  blocks it; if adopted: week.toml `exposure_cap = 45`, control `--subdir model_cap25 --cap 25`, extra_sets
  ["model_cap25", "flex_shadow"], pool and flex shadow at the entered cap (or `--cap 25`). Week 4 has no sims.npy.
- **Doug's decisions on tests 8-10 (Nov 2):** 8 no blend; ownership signal PARKED unless Doug finds a free pre-lock
  ownership source (then shadow-test it 2 weeks). 9 DST reds stay as is. 10 **no swap: cap 25 entered, cap 45
  control** (`--subdir model_cap45 --cap 45`, `[grading] extra_sets = ["model_cap45", "flex_shadow"]`), keep measuring both.
- **Week 9 reads:** Doug marks greens on RBs with clear role increases (shadow-only, `[shadow.green]`, as usual).
  **Monday's week-9 review must report the RB greens vs projection (actual - proj each and as a group) and vs
  non-green RBs at the same salary** (salary-matched, e.g. within $300 or the same $500 band, same slate; proj 4+),
  plus the usual shadow-green lineup re-run.

## Learn from winners (Nov 2) — see docs/learn_from_winners.md; WEEKLY REVIEW STEP from week 9
Doug: add to every weekly review. After `convert_results.py`: `python src/learn_from_winners.py --week <week>`
(reads the full export in `data/<week>/raw/`, `--export` if there are several csvs; writes `weeks/<week>/winners.csv`
and `winners_top_owned.csv`; model set + every `[grading] extra_sets` set in the most-owned exposure table), then
`--compare 2026-w05,...,<week>` (differences vs the field top 10% in all weeks / all but one / fewer) and report both,
plus below-median share and the cap check (model vs control on the 10 most-owned; hit = top 10% at 1.2x field).
Weeks 5-8 result (nothing changed): every week we had -0.5 RB a lineup, FLEX RB 27% vs top 10% 75% (field 64%), TE
salary +$2,300, DST +$500 (cheap DST 19% vs 55%), avg player ownership 11.2% vs 17.6% (field 16.8%). Winner traits =
RB in FLEX and cheap DST (top 10% beyond the field the same way); QB+2 / bring-back is our rule, not a winner trait
(top 10% = field; top 1% leans our way). Below the median 80 / 61 / 48 / 72% of our lineups (avg -23.4 / -6.3 / 0.0 /
-12.2). Cap: binds (28 of 40 most-owned at the cap), but cap 45 adds more to the chalk that missed (+4.0) than to the
hits (+2.2); lineups +1.4 avg, top-1% 1 vs 1; it changes ownership ~1/5 of the gap and none of the RB / TE / DST gap.
Weeks 5-6 controls were scratch builds at cap 45 (not in weeks/).

## Week-10 build tests (Doug, Nov 6) — AFTER Sunday's slate, not before; analysis only
Variants of median-70 on weeks 5-9 rebuilds (scratch, `optimize.py --median70 --subdir <absolute scratch path>`;
week 9 once graded), **one change at a time** vs plain median-70: (1) more RB in the FLEX (e.g. TE in the FLEX only
for top-5 TEs by salary, the flex-shadow rule); (2) relaxed stack rule (QB + 1 allowed, bring-back optional); (3)
repeats of the top lineups allowed (up to ~30% of 150, like max-entrants' 106 distinct per 150). Report per week:
cash rate, money as-if (Pooch Punt prize table), average, top 1% (plus top 10% and best, the standing rule). Doug
decides the week-10 build from it. Note no-draw / some caps can't build week 7: report any variant that stalls.

## Top finishers and max-entrants (Nov 6) — docs/top_finishers.md, docs/max_entrants.md; analysis only
**NFL and NBA are kept COMPLETELY SEPARATE (Doug, Nov 6): no pooled numbers across sports, ever.** The NBA repo has
its own copy of top_finishers.py (copy, don't link). Aggregated only: never write other users' names (anon user_001).
`python src/top_finishers.py` (weeks 5-8 exports; cash via the week-9 Pooch Punt prize table, which reproduces Doug's
weeks 5/7/8 winnings exactly): max-entry (150) users 49% of entries, 63% of top-1%, cash 51.8% vs 41.4% (one entry),
return 1.43 vs 1.05 (field 1.26, overlay every week); us 0.73; top-1% clusters are one lineup entered 150 times.
`python src/max_entrants.py --builds <scratch>` (model / no-draw / median-70 / cap 45 rebuilt for weeks 5-8 into a
scratch folder with `optimize.py --subdir <absolute scratch path>`; model matched archived uploads 150/150 each
week; no-draw can't build week 7): **median-70 looks most like the max-entrants every week, the model least.** Gaps
no build closes: RB in FLEX (theirs 72%, top-1% 84%; model 26%, median-70 46%), the QB + 2 + bring-back rule (theirs
43-55%), lineup repeats (106 distinct per 150). Nothing changed; each would be its own test (Doug decides).

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
