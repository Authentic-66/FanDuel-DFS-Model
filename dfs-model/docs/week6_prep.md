# Week 6 prep (Oct 12, 2026)

Work done after the week-5 review, in the order Doug asked for it.

**What changes in week 6 if nothing is switched off.** Four defaults in `config/defaults.toml` now alter projections:

| Change | Setting | To turn off |
|---|---|---|
| Out players who already missed games still hand volume to teammates | `[model.injury] absent_mode = "present_share"` | `absent_mode = "skip"` |
| Non-starting QBs project 0 | `[model.qb] zero_backups = true` | `false` |
| Shrink above 16 points, and RBs above 8 | `[model.calibration] enabled = true` | `false` |
| DST from opponent total and salary only | `[model.dst.flatten] enabled = true` | `false` |

The exposure cap is unchanged at 25. Section 5 has the numbers for Doug's decision.

## 1. Merge

`week5-model-only` is merged into `main` and pushed (merge commit d35317a); it merged cleanly. `config/2026-w05/week.toml`
is now the final config as entered (a copy of `weeks/2026-w05/final_week.toml`), so re-running week 5 reproduces the
entered lineups. Tests: 36 passed after the merge, 41 pass now with the new ones.

## 2. Volume bug

**Doug's diagnosis was right for Allen and Warren, and Michael Wilson was not a bug.**

- **Braelon Allen.** Breece Hall missed week 4, so `skip_already_absent` treated Hall's carries as already sitting
  in Allen's numbers and handed out nothing. They were not: Allen's usage is a season average, three games behind
  Hall (10, 5, 4 carries) and one without him (14), blended with two pseudo-games of his 2025 backup role (4.5 a
  game). That comes to 7 carries a game.
- **Jaylen Warren.** Same thing. Rico Dowdle missed weeks 3 and 4, so he was skipped, while Warren's average still
  included the two games he shared with Dowdle (10 and 11 carries, against 17 and 17 without him).
- **Michael Wilson.** Marvin Harrison had played all four games, so he was handed out normally. He simply had
  little to give: 13 targets in four games. Wilson's 51% ownership came from his own 17 and 13 targets in weeks 3
  and 4 at $6,400, not from Harrison's absence. His projection (15.7) is unchanged; he scored 5.3.

**Fix.** A player listed out is now handed out in proportion to the share of each teammate's usage sample in
which he was still playing: the current-season games they shared, plus the teammate's prior-season pseudo-games.
A player ruled out for the first time is handed out in full, as before. One who has missed games is handed out
for the rest, and the amount fades each week he stays out. For Hall that share was 5 of Allen's 6 sample games; for
Dowdle, 4 of Warren's 6.

Week 5, before and after (volume fix only, then with every change in this document):

| Player | Gained volume before | After | Projection before | Volume fix only | All changes | Actual |
|---|---|---|---|---|---|---|
| Braelon Allen | 0.00 | 8.17 | 6.1 | 11.6 | 11.2 | 21.1 |
| Jaylen Warren | 0.57 | 5.71 | 16.0 | 20.3 | 17.6 | 36.8 |
| Michael Wilson | 0.95 | 0.95 | 15.7 | 15.7 | 15.7 | 5.3 |

Other week-5 players it moved by a point or more: Garrett Wilson 12.6 to 15.1 (scored 22.9), Mason Taylor 5.2 to
6.6 (3.9), Kenyon Sadiq 6.7 to 8.0 (-0.7), Cam Skattebo 13.0 to 14.2 (6.1), Brock Bowers 16.2 to 17.3 (22.0).

The fix is not a clear accuracy gain on two slates: week-5 RMSE improves (8.65 to 8.50) and week 4 gets slightly
worse (7.99 to 8.05), mostly because it raises Garrett Wilson from 14.8 to 18.2 in a week he scored 4.2. I kept it
because the old rule was wrong in principle and its misses land on exactly the cheap role-change players the
field piles onto.

Not changed: the 80% share itself. Allen took about 45% of Hall's carries in week 4, so 80% may be high; that
needs more than two cases.

## 3. Flex usage

Flex position mix (share of lineups; field from the sum of %Drafted by position):

| | RB flex | WR flex | TE flex |
|---|---|---|---|
| Week 4, our 149 | 28% | 24% | 48% |
| Week 4, field | 56% | 22% | 19% |
| Week 4, top 1,000 lineups | 72% | 16% | 12% |
| Week 5, our 149 | 23% | 32% | 45% |
| Week 5, field | 63% | 18% | 15% |
| Week 5, top 1,000 lineups | 88% | 4% | 8% |

**Why.** I re-ran the week-5 optimizer on the entered projections, changing one thing at a time:

| Run | RB flex | WR flex | TE flex | Avg projection | Avg salary |
|---|---|---|---|---|---|
| As entered | 23% | 31% | 45% | 123.0 | $58,719 |
| Two RBs per team in the pool | 33% | 33% | 35% | 122.8 | $58,439 |
| Objective = projection only (no sim draw) | 41% | 24% | 35% | 126.0 | $59,393 |
| No stack rule | 34% | 28% | 38% | 125.1 | $59,091 |
| Exposure cap 40 | 21% | 33% | 47% | 129.9 | $59,401 |
| No exposure cap | 33% | 25% | 41% | 138.5 | $59,519 |

No single cause; three things each account for about ten points of the 45%:

- **The RB pool is 22 players.** Starters-only keeps one RB per team. The top seven were all at the 25 cap, and
  the next tier (projected 10-14 at $5,700-$7,100) is no better than a $5,200 tight end projected 10.
- **The stack rule counts tight ends.** A stack needs two of the QB's WR/TE and a bring-back. In two-TE lineups,
  0.78 of the tight ends came from the stack team and 0.41 from the bring-back side.
- **The objective is 60% one simulated draw.** Tight ends and receivers have wider simulated spreads than RBs
  (standard deviation 58% of the mean against 47%), so they win single draws more often. With projection only,
  TE flex drops to 35% and RB flex rises to 41%.

Neither of Doug's two suspects is the main driver:

- **The cap.** Raising it to 40 did not lower TE flex (47%), because McBride, Bowers and LaPorta were capped
  too and got used more.
- **Inflated TE projections.** Tight ends projected 8+ averaged 10.9 and scored 10.9 in week 5, and across 2025
  they run +0.6 high in the 8-12 range, the same as RBs and WRs.

Was it the leak in week 5? Not by itself. Our flex tight ends averaged 10.3 points, our flex RBs 9.6 and our flex
WRs 5.4. The gap to the field was which RBs we held, not the flex slot. Across the whole field, though, RB-flex
lineups averaged 135.7 against 126.4 for TE-flex.

I changed nothing here. Options, if Doug wants the mix closer to the field: allow a second RB per team when he
projects 8+, or lower the weight on the single draw.

## 4. Calibration

### Skill players

Fit on 2025 weeks 4-18 (2,378 player-weeks, projections from earlier weeks plus the 2024 prior) and 2026 weeks 4
and 5 (the real pipeline against FanDuel results). Every number below is leave-one-week-out: each week is graded
with slopes fit on the other 16.

**One departure from the request.** A shrink that starts at 20 cannot fix the 20+ tier. The 2025 data put the
over-projection at +1.4 for 20-22 and +4.4 for 22+, so a hinge at 20 fits a slope above 1, which would flatten
everything over 20 to the same number. The shrink therefore starts at 16:

- every skill player loses 28% of each projected point above 16 (leave-one-week-out range 20-32%);
- RBs also lose 12% of each point above 8 (range 9-14%).

So 20 becomes 18.9, 24 becomes 21.8, and an RB at 14 becomes 13.3. Simulations are rescaled, so ceilings shrink in
proportion. The knees are `top_knee` and `rb_knee` in `[model.calibration]`.

| Rows | Tier | n | Projected | Calibrated | Actual | RMSE before | RMSE after |
|---|---|---|---|---|---|---|---|
| 2025 wk 4-18 | all | 2,378 | 11.7 | 11.4 | 10.9 | 7.32 | 7.30 |
| 2025 wk 4-18 | 20+ | 163 | 21.4 | 19.4 | 19.2 | 9.93 | 9.67 |
| 2025 wk 4-18 | RB 8+ | 523 | 13.6 | 12.7 | 12.5 | 8.52 | 8.45 |
| 2026 wk 4 | all | 124 | 11.9 | 11.5 | 10.5 | 7.85 | 7.70 |
| 2026 wk 4 | 20+ | 13 | 22.8 | 20.8 | 18.6 | 8.41 | 7.47 |
| 2026 wk 4 | RB 8+ | 27 | 13.8 | 12.8 | 12.3 | 8.60 | 8.44 |
| 2026 wk 5 | all | 119 | 12.1 | 11.7 | 10.4 | 8.11 | 8.10 |
| 2026 wk 5 | 20+ | 10 | 23.4 | 20.4 | 20.6 | 10.68 | 10.87 |
| 2026 wk 5 | RB 8+ | 28 | 13.6 | 12.6 | 9.9 | 8.54 | 8.52 |

It removes the tier bias (2025 20+: +2.2 to +0.2) and barely moves RMSE, because the error in any one week is
mostly noise. Week 5's 20+ tier gets slightly worse on RMSE because Gibbs (38.2) is pulled from 29.7 to 23.0.
That is the cost of the shrink: the top play of the slate now projects seven points lower.

The 2025 rows only include players who played, and use league-average team totals, so they understate the bias on
a real slate; weeks 4 and 5 still show +1.0 and +1.3 overall after calibration.

Seen in the data and not acted on: QB projections are too spread out (actual moves 0.64 points per projected
point), and a per-position linear shrink scores slightly better than the two hinges (week 5 RMSE 7.93 against
8.10). It is a bigger change than was asked for.

### Non-starting QBs

They now project 0 (`[model.qb] zero_backups`). A team with no starter flagged prints a warning naming it, to be
fixed with `[status.starting_qb]`; week 4 prints one for TB. Case Keenum goes from 19.5 to 0.

### DST

Across the 46 DST games in weeks 4 and 5, actual points correlated -0.40 with the opponent's implied total and
+0.31 with salary, and -0.06 with FanDuel's season average, which is what the old projection leaned on (r = 0.85
between the two). The DST mean is now the slate's simulated average, minus 0.35 per point of opponent implied total
above the slate average, plus 0.35 per $1,000 of salary above it. The spread between the best and worst DST
narrows from 6-8 points to about 5.

These two coefficients were chosen looking at the same 46 games (roughly half the least-squares values), so the
DST improvement below is in-sample.

### RMSE on the two slates, one change at a time

Skill players with a FanDuel average of 5+ (backup QBs included), and all DSTs. Calibration slopes are the
leave-one-week-out ones.

| Week | Step | Skill RMSE | Skill bias | Skill r | DST RMSE | DST r |
|---|---|---|---|---|---|---|
| 4 | Before | 7.99 | +1.60 | 0.45 | 3.21 | 0.25 |
| 4 | + volume fix | 8.05 | +1.66 | 0.44 | 3.23 | 0.24 |
| 4 | + backup QBs zero | 7.76 | +1.34 | 0.48 | 3.23 | 0.24 |
| 4 | + calibration | 7.61 | +0.97 | 0.48 | 3.23 | 0.24 |
| 4 | + DST flatten | 7.61 | +0.97 | 0.48 | 2.82 | 0.46 |
| 5 | Before | 8.65 | +2.07 | 0.51 | 6.14 | 0.12 |
| 5 | + volume fix | 8.50 | +2.24 | 0.54 | 6.12 | 0.13 |
| 5 | + backup QBs zero | 7.95 | +1.63 | 0.60 | 6.12 | 0.13 |
| 5 | + calibration | 7.94 | +1.22 | 0.60 | 6.12 | 0.13 |
| 5 | + DST flatten | 7.94 | +1.22 | 0.60 | 5.73 | 0.42 |

Zeroing backup QBs is the largest single gain. Overall: skill RMSE 7.99 to 7.61 in week 4 and 8.65 to 7.94 in week 5.

## 5. Exposure cap: 25, 32, 40

Both weeks run model-only on the new code, with week 5's final-run settings: starters only, questionable players
excluded, proportional stack counts from the implied-total weights, QB + 2 receivers + 1 bring-back for every team,
no overrides, no red/yellow/green, nothing forced. Each week keeps its own injury statuses. The cap (players and
DSTs alike) is the only thing that differs between runs. Calibration slopes are the leave-one-week-out ones, so
neither week is graded with slopes that saw it. 150 lineups per run.

| Week | Cap | Avg score | Field avg | Best score | Best rank | Top 1% | Top 10% | Above field median | Avg projection |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 25 | 113.2 | 131.2 | 191.3 | 5,291 | 1 | 7 | 37 | 118.5 |
| 5 | 32 | 116.6 | 131.2 | 191.3 | 5,291 | 1 | 7 | 47 | 121.1 |
| 5 | 40 | 120.0 | 131.2 | 202.7 | 1,182 | 2 | 8 | 52 | 123.0 |
| 4 | 25 | 105.1 | 107.3 | 169.2 | about 4,400 | 3 | 20 | 67 | 117.7 |
| 4 | 32 | 103.9 | 107.3 | 169.2 | about 4,400 | 2 | 16 | 65 | 118.9 |
| 4 | 40 | 103.1 | 107.3 | 169.2 | about 4,400 | 2 | 16 | 63 | 119.9 |

Week-5 ranks are exact, from the full export. Week-4 ranks below the top 2,000 are interpolated from the field
quantiles, so "about 4,400" is rough; the top-1% counts are exact in both weeks.

**The new code at cap 25 beats what was entered in week 5:** 113.2 against 108.3, with one lineup in the top 1%
(191.3, rank 5,291) where the entered set had none. Week 4 has no like-for-like baseline: the entered week-4 set
(111.3) used Doug's overrides and colour reads, which this test leaves out.

**The cap test is a split decision.** Raising the cap helped in week 5 (+6.8 points at 40, best rank 1,182) and
hurt in week 4 (-2.0, one fewer top-1% lineup). A higher cap concentrates lineups on the highest projections. In
week 5 those hit (Gibbs 38.2, Warren 36.8); in week 4 the players who gained most missed (Smith-Njigba 10.1,
Henry 14.9). Two slates pointing opposite ways are not evidence for changing the default.

Our exposure on players the field owned 15% or more:

| Week | Cap | Chalk players | Field avg own | Our avg exposure | Players where we are under the field |
|---|---|---|---|---|---|
| 5 | 25 | 14 | 29.5% | 14.5% | 13 |
| 5 | 32 | 14 | 29.5% | 17.1% | 12 |
| 5 | 40 | 14 | 29.5% | 19.1% | 12 |
| 4 | 25 | 16 | 23.3% | 12.8% | 16 |
| 4 | 32 | 16 | 23.3% | 12.9% | 16 |
| 4 | 40 | 16 | 23.3% | 13.4% | 15 |

Week 5 by player (our exposure at each cap):

| Player | Projection | Actual | Field | Cap 25 | Cap 32 | Cap 40 |
|---|---|---|---|---|---|---|
| Michael Wilson | 15.7 | 5.3 | 50.7% | 16.7% | 21.3% | 26.7% |
| D'Andre Swift | 20.7 | 15.3 | 44.1% | 16.7% | 21.3% | 26.7% |
| Jahmyr Gibbs | 23.0 | 38.2 | 39.2% | 16.7% | 21.3% | 26.7% |
| Trey McBride | 17.9 | 17.1 | 36.2% | 16.7% | 21.3% | 24.7% |
| Aaron Jones Sr. | 13.4 | 20.2 | 30.8% | 12.7% | 11.3% | 8.7% |
| Jacoby Brissett | 18.3 | 25.8 | 29.6% | 6.0% | 6.0% | 6.0% |
| Jaylen Warren | 17.6 | 36.8 | 29.6% | 16.7% | 21.3% | 26.7% |
| Amon-Ra St. Brown | 20.2 | 9.9 | 28.8% | 16.7% | 21.3% | 26.7% |
| Nico Collins | 16.3 | 8.1 | 27.8% | 16.7% | 19.3% | 14.7% |
| Commanders DST | 6.4 | 6.0 | 24.7% | 8.7% | 10.0% | 11.3% |
| Jaxon Smith-Njigba | 22.0 | 23.3 | 18.8% | 16.7% | 21.3% | 26.7% |
| Jonathan Taylor | 18.7 | 9.7 | 18.4% | 16.7% | 21.3% | 22.7% |
| Jared Goff | 22.3 | 28.9 | 18.1% | 9.3% | 9.3% | 9.3% |
| Chase Brown | 15.4 | 5.5 | 15.5% | 16.7% | 12.7% | 10.0% |

Week 4 by player:

| Player | Projection | Actual | Field | Cap 25 | Cap 32 | Cap 40 |
|---|---|---|---|---|---|---|
| Aaron Jones Sr. | 12.4 | 14.8 | 39.9% | 8.0% | 6.0% | 6.0% |
| Jeremiyah Love | 13.5 | 6.0 | 33.2% | 12.0% | 9.3% | 9.3% |
| Parker Washington | 12.8 | 1.5 | 30.2% | 13.3% | 11.3% | 11.3% |
| Kenneth Walker III | 18.2 | 33.4 | 24.5% | 16.7% | 19.3% | 17.3% |
| Derrick Henry | 20.8 | 14.9 | 24.2% | 16.7% | 21.3% | 22.0% |
| Jaxon Smith-Njigba | 24.9 | 10.1 | 23.8% | 16.7% | 21.3% | 26.7% |
| Jordan Addison | 10.5 | 7.1 | 22.7% | 6.7% | 6.7% | 7.3% |
| Travis Kelce | 11.4 | 2.5 | 21.5% | 10.0% | 9.3% | 10.0% |
| Bears DST | 7.1 | 7.0 | 20.5% | 9.3% | 10.7% | 10.7% |
| Michael Wilson | 13.0 | 13.0 | 20.4% | 10.7% | 10.0% | 10.0% |
| Tee Higgins | 14.1 | 24.2 | 20.0% | 14.0% | 12.0% | 13.3% |
| Brock Bowers | 16.1 | 17.6 | 19.4% | 16.7% | 18.0% | 19.3% |
| Braelon Allen | 11.2 | 7.7 | 19.0% | 9.3% | 8.7% | 9.3% |
| Christian McCaffrey | 18.1 | 14.5 | 18.4% | 16.7% | 15.3% | 15.3% |
| Vikings DST | 8.8 | 8.0 | 17.6% | 11.3% | 10.0% | 9.3% |
| Nico Collins | 15.8 | 30.3 | 17.4% | 16.7% | 16.7% | 16.7% |

What the tables show:

- **The cap is not what keeps us under the field on chalk.** Even at 40 we are under on 12 of 14 (week 5) and 15
  of 16 (week 4). The cap only binds on the players the model already projects highest. The mid-priced chalk the
  model projects at 12-14 (Aaron Jones both weeks, Love, Washington, Addison) stays at 6-13% at any cap, and
  tends to go down as the cap rises because the top projections take more lineups.
- **QB exposure does not move with the cap.** It is set by the stack counts (Goff 9.3%, Brissett 6.0% at every cap).
- **TE flex is unchanged by the cap** (44-48% in every run), as section 3 found.
- **DSTs never reach the cap.** The most-used DST is in 15-18 lineups in every run, now that DST projections
  are nearly flat.
- At cap 25 the cap binds on 18 players in week 5 and 13 in week 4; at 40, on 6 and 1.

TB has no starting QB flagged in week 4, so it gets no stacks there; MIA and TEN (weight 1) round to zero stacks.

**The default stays at 25.** Results are in `weeks/2026-w05/backtest_caps.csv` and `backtest_caps_chalk.csv`.

## 6. Shadow record

`config/2026-w06/week.toml` is set up the same way as week 5: model-only, with Doug's red/yellow/green recorded
under `[shadow]` and not applied. `[status]`, `[stacks.weights]` and `[contest.guru]` are empty until the week-6
inputs arrive.

## Files

- `src/dfs/usage.py`, `src/dfs/project.py`, `config/defaults.toml`: the four changes.
- `src/fit_calibration.py`: refits the calibration slopes; `weeks/2026-w05/calibration_cv.csv`, `calibration_fit.csv`.
- `weeks/2026-w05/backtest_week6_prep.csv`: the step-by-step RMSE table. `backtest_caps.csv`: section 5.
