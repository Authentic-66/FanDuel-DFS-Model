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
  `[pool]` QB/RB/WR/TE/DST lists (+ `ranked`) = Doug's player pool for pool mode (docs/pool_mode.md); settings
  (`max_filler`, `rank_boost`, `raise_cap_to`) in defaults.toml `[pool]`.

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
- Tests: `python -m unittest discover -s tests` (stdlib unittest; scoring, usage/blend, ownership, week-4 regression checks).

## Doug's standing rules (current; confirm each week)
- **Starters only**: QB1 (week's starter), RB1, top-3 WR, TE1 per team by projection. Green-listed players always eligible.
- **Exposure cap 25 lineups** for every player and DST (Doug's choice to limit bust risk; raise to 40 only if infeasible).
- Stack per lineup: QB + >=2 of his WR/TE + >=1 bring-back from opponent. No DST facing your own offensive players.
- Pull questionable players rather than rely on late swap (he enters via CSV and won't hand-edit 150 lineups):
  `[optimizer] exclude_questionable = true` (default; week 4 sets false, it predates the rule). Before Friday's report
  (`[status]` lists both empty) FanDuel's own tags apply: O/IR out, Q/D = Q (excluded). Once `[status]` has entries,
  FanDuel's Q/D tags are ignored. Excluded Q/OUT players don't hold starter depth: RB1/top-3 WR/TE1 are ranked among
  eligible players, so backups move up (green exempt).
- If he has a free entry, upload 149 (drop lowest projected) and use the free entry separately.
- From week 7: role guard on (WR/TE only), WR implied-total correction on, $59K salary floor with relief to 28 for
  capped players only.
- Weekly review loop: he color-codes `exposure.csv` in Excel — **red = exclude, yellow = less (cap at ~half current),
  green = more (min = max(2x current, 12))**. Two shades of green both mean "more". Lists live in `config/<week>/week.toml`
  `[prefs]`.
- From week 6, red/yellow reads are applied, green is shadow-only, based on weeks 4-5 (+3.0, +2.5 per lineup).
  Red and yellow go under `[prefs]`, green under `[shadow.green]` (`[prefs.green]` stays empty).
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

## Week 7 run checklist (state at end of Oct 19: head 79bef65 on origin/main; preliminary done, see below)
Steps 1-2 and the preliminary parts of 3-6 are DONE (section "Week 7 preliminary run"). Remaining:
1. Doug's review sheet `data/2026-w07/review_sheet.xlsx` (rebuilt Oct 19 evening; untracked): red -> `[prefs] red`
   (+ `[shadow.red_lineups]` with the sheet's Lineups; Kaytron Allen and Jared Wayne already red), yellow ->
   `[prefs.yellow]` with the sheet's Lineups numbers, green -> `[shadow.green]`; Pool = Y / Rank -> `[pool]` lists
   in week.toml (QB 10, RB 10, WR 14, TE 8, DST 5; `ranked = true` only if he ranked them).
2. Friday's report -> `[status]` (replace the preliminary FanDuel-tag lists; Out/Doubtful -> out, Questionable ->
   questionable, IR players with 3+ targets + carries a game out, QBs out left to FanDuel tags) and
   `[status.starting_qb]` (BAL: Lamar Q, Huntley flagged; TB: Mayfield Q). Re-download `fd_players.csv` if FanDuel
   updated it. Then Doug's Estime (CLE RB, no 2026 data) and SF override reads, if any.
3. Saturday / Sunday: replace `data/2026-w07/lines.csv` (PRELIMINARY nflverse lines) and rebuild `[stacks.weights]`
   = round(2 x (implied - 16)), min 1. Keep `[stacks] extra_receivers = ["Christian McCaffrey"]` (Doug's SF read).
4. `model.py`, read the role-guard warning (new names = no 2026 snaps or a missing alias) and team-mismatch warnings.
5. Final `optimize.py --week 2026-w07` (main folder; check the floor line) and `optimize.py --week 2026-w07 --pool`
   (shadow, `weeks/2026-w07/pool/`; cap 40 for pool players is expected; if it stalls, stop and ask Doug). Write the
   149 files for the model set if he has a free entry. Enter the model's lineups only.
6. After the slate: `convert_results.py`, `[contest] field_size`, `analyze_results.py` (grades the pool set too:
   `pool/grade.csv`), `docs/week7_review.md` (week-6 format + pool vs model, Harrison's trade read and the SF
   McCaffrey stack read by hand), ask Doug for winnings (running total -$3.88 after week 6).
Review sheet recipe (builder is a scratch script, not in the repo): rows = every active player with an empty
`RoleGuard`, sorted by position then Proj; columns Player, Team, Opp, Pos, Salary, Proj, Value_per_1k, Implied_total,
Routing_bump, Role_vol, Own_proj_%, Lineups (from the prelim/review exposure.csv), Status, In_model_pool (Y or the
reason: red, questionable, not the starting QB, depth, projects < 4), Color (reds pre-filled), Pool, Rank; tabs
held_out_Q and notes. Check: Lineups sums to 1,350.

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
- **Harrison trade, Arizona side**: full volume handed out although ARI's week-6 game already lacked him (small double
  count); remove the trade entry after ~3 Houston games.
- 149-lineup script (still an inline snippet each week).

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
