# Week 6 prep (Oct 12, 2026)

Work done after the week-5 review, in the order Doug asked for it.

**What changes in week 6 if nothing is switched off.** Four defaults in `config/defaults.toml` now alter projections,
one widens the RB simulations and one changes the optimizer (from section 8), and three more came from the
history refit (the last three rows, section 9):

| Change | Setting | To turn off |
|---|---|---|
| Out players who already missed games still hand volume to teammates | `[model.injury] absent_mode = "present_share"` | `absent_mode = "skip"` |
| Non-starting QBs project 0 | `[model.qb] zero_backups = true` | `false` |
| Shrink above 16 points, and RBs above 8 (mean only, spread kept: see 7.2) | `[model.calibration] enabled = true` | `false` |
| DST from opponent total and salary only | `[model.dst.flatten] enabled = true` | `false` |
| RB simulations 1.376 times as wide, projection unchanged (8.1) | `[model.spread] RB = 1.376` | `RB = 1.0` |
| Objective is 60% projection, 40% one simulated draw (was 40 / 60) | `[optimizer] mean_weight = 0.6` | `0.4` |
| Calibration slope above 16 raised (9.1) | `[model.calibration] top_slope = 0.36` | `0.28` |
| An out or traded player's volume goes mainly to his own position (9.2) | `[model.injury] routing = "position"` | `"pro_rata"` |
| Spread tapered for QB, RB, WR, TE; replaces the flat RB 1.376 (9.3) | `[model.spread]` `{ low, top }` | `[model.spread]` with only `RB = 1.376` |

The exposure cap is unchanged at 25 (Doug's decision after section 5).

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

So 20 becomes 18.9, 24 becomes 21.8, and an RB at 14 becomes 13.3. The knees are `top_knee` and `rb_knee` in
`[model.calibration]`. As first committed the simulations were rescaled in proportion; after the ceiling check in
7.2 the default lowers the mean and leaves the spread alone.

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
inputs arrive. It also carries the Harrison trade entry (7.6), which stops the run until his target share is set.

## 7. Follow-up tests (Oct 12, second pass)

Decisions carried in: the cap stays at 25 and the shrink starts at 16. One default changed in this pass (the
calibration now lowers the mean and leaves the simulated spread alone, 7.2), and one feature was added
(`[[status.trade]]`, 7.6).

### 7.1 Chalk test

**Players owned 15%+ against our final (entered) projection:**

| | Players | Projected | Actual | Beat projection | New-code projection |
|---|---|---|---|---|---|
| Week 4 | 16 | 17.3 | 13.3 | 4 of 16 | 14.3 |
| Week 5 | 14 | 19.4 | 17.9 | 6 of 14 | 17.7 |
| Both | 30 | 18.3 | 15.4 | 10 of 30 | 15.9 |

The chalk fell short of the entered projections by 2.9 points, but so did everyone else we projected for 10+:
chalk scored 84% of its projection and the other 128 such players scored 81%. Chalk is not over-projected more
than the rest. With the week-6 code the chalk projects 15.9 against 15.4 actual.

**Does ownership predict points beyond our projection? Yes, and it is stable across the two weeks.** Regression
of actual points on our projection and log(actual ownership), skill players projected 2+:

| Projection used | Rows | n | Coefficient on log(ownership) | Std. error | Coefficient on projection | R-squared without / with ownership |
|---|---|---|---|---|---|---|
| Entered | Week 4 | 239 | 1.36 | 0.32 | 0.39 | 0.32 / 0.37 |
| Entered | Week 5 | 220 | 1.25 | 0.33 | 0.53 | 0.35 / 0.40 |
| Entered | Pooled | 459 | 1.32 | 0.23 | 0.45 | 0.33 / 0.38 |
| Week-6 code | Week 4 | 248 | 1.07 | 0.32 | 0.58 | 0.37 / 0.40 |
| Week-6 code | Week 5 | 215 | 0.48 | 0.39 | 0.90 | 0.42 / 0.42 |
| Week-6 code | Pooled | 463 | 0.84 | 0.25 | 0.71 | 0.39 / 0.41 |

- On the entered projections the coefficient is 1.32: at the same projection, a player owned twice as much scored
  about 0.9 points more. Weeks 4 and 5 give 1.36 and 1.25, well inside one standard error of each other.
- The week-6 fixes take away about a third of it (0.84 pooled), and week 5 alone is no longer distinguishable from
  zero (0.48, standard error 0.39). Zeroing backup QBs and the volume fix capture part of what the field knew.
- Restricted to players projected 8+ (entered), it is 1.55 pooled but 0.97 and 2.01 by week, so noisier.

Two cautions. This uses actual ownership, known only after lock; the pre-lock version of this test needs the
ownership model, which still misses the chalk. And ownership and projection are correlated 0.8, so part of the
coefficient is ownership standing in for a noisy projection (the projection's own coefficient is well under 1).

### 7.2 Ceiling check

Share of players whose actual score beat the simulated 90th percentile (target 10%). "Scaled" is the calibration
as committed this morning (every draw shrunk in proportion); "mean only" lowers each draw by the same amount.
Slopes are leave-one-week-out.

| Rows | Tier | n | Uncalibrated | Scaled | Mean only |
|---|---|---|---|---|---|
| 2025 wk 4-18 | Projected 16+ | 514 | 10.9% | 13.8% | 13.0% |
| 2025 wk 4-18 | Projected 20+ | 163 | 6.1% | 12.3% | 11.0% |
| 2026 wk 4-5 | Projected 16+ | 62 | 14.5% | 16.1% | 14.5% |
| 2026 wk 4-5 | Projected 20+ | 23 | 8.7% | 13.0% | 8.7% |
| All | Projected 16+ | 576 | 11.3% | 14.1% | 13.2% |
| All | Projected 20+ | 186 | 6.5% | 12.4% | 10.8% |
| All | Everyone graded | 2,621 | 12.2% | 12.9% | 12.7% |

By position at 16+ (all rows): QB 10.9% / 12.5% / 11.6%, RB 13.4% / 20.1% / 18.9%, WR 9.3% / 9.3% / 9.3%.

**The uncalibrated ceilings at 16+ were about right (10.9% in 2025), so by Doug's rule the calibration now shrinks
only the mean** (`[model.calibration] mode = "shift"`; `"scale"` restores the first version). Mean-only is the
better of the two on every row.

It is not a clean fix, though. Lowering a mean without widening the spread still lowers the ceiling by the same
number of points, so coverage at 16+ goes from 10.9% to 13.0%: the calibrated ceilings are a little low. They are
worst for RBs (18.9% beat their ceiling). The model's RB means run high while its RB ceilings were already too
low, and one adjustment cannot fix both. Inside the tier, 20+ ceilings were too high before (6.1%) and are right
after (11.0%); 16-20 were already low at 13%.

Projections do not change between the two modes, so section 4's RMSE tables stand. The cap-25 baseline was re-run
on the mean-only version (7.3): week 5 is unchanged at 113.2 and week 4 moves from 105.1 to 104.9.

### 7.3 Second RB, draw weight, no cap

Model-only, same settings as the cap test in section 5, cap 25 except the no-cap run. The no-cap run keeps the
overlap rule (at most 6 shared players) and is a diagnostic, not a candidate default.

| Week | Run | Avg score | Best rank | Top 1% | Top 10% | RB / WR / TE flex | Our avg exposure on 15%+ players | Field |
|---|---|---|---|---|---|---|---|---|
| 5 | Cap 25 baseline | 113.2 | 5,291 | 1 | 8 | 24 / 33 / 43% | 14.6% | 29.5% |
| 5 | Second RB if 8+ | 112.1 | 5,291 | 1 | 5 | 30 / 34 / 36% | 14.3% | 29.5% |
| 5 | Draw weight 40% | 114.2 | 5,291 | 1 | 9 | 29 / 34 / 37% | 14.7% | 29.5% |
| 5 | No cap | 121.1 | 5,291 | 2 | 13 | 29 / 28 / 43% | 20.6% | 29.5% |
| 4 | Cap 25 baseline | 104.9 | about 4,400 | 3 | 20 | 13 / 41 / 46% | 12.8% | 23.3% |
| 4 | Second RB if 8+ | 103.8 | about 4,400 | 2 | 25 | 19 / 39 / 42% | 12.7% | 23.3% |
| 4 | Draw weight 40% | 106.7 | about 4,400 | 3 | 22 | 18 / 33 / 49% | 13.9% | 23.3% |
| 4 | No cap | 102.4 | about 4,400 | 2 | 17 | 13 / 39 / 48% | 14.0% | 23.3% |

Field averages were 131.2 (week 5) and 107.3 (week 4). The best lineup is the same one in every run of a week
(191.3 and 169.2); week-4 ranks are interpolated, as in section 5.

- **Second RB when he projects 8+.** Adds 7 RBs to the pool in week 5 and 6 in week 4. It moves flex toward RBs
  (TE flex down 4-7 points) and costs about a point of average score in both weeks. No case for it.
- **Draw weight 40%.** Better in both weeks (+1.0 and +1.8), with no loss at the top. It is the only change here
  that helped twice, but the gain is small against lineup-to-lineup noise, and TE flex went down in week 5 and up
  in week 4. Worth a wider test before changing the default (`[optimizer] mean_weight = 0.6`).
- **No cap.** Same split as the cap test: +7.9 in week 5, -2.5 in week 4. Chalk exposure only rises to 20.6% and
  14.0%, still well under the field, so the cap is not what holds it down.

Ten most-used players with no cap (lineups out of 150, actual points):

| Week 5 | Lineups | Exposure | Actual | | Week 4 | Lineups | Exposure | Actual |
|---|---|---|---|---|---|---|---|---|
| D'Andre Swift | 81 | 54% | 15.3 | | Jaxon Smith-Njigba | 55 | 37% | 10.1 |
| Jaxon Smith-Njigba | 42 | 28% | 23.3 | | James Cook III | 38 | 25% | 15.3 |
| Jahmyr Gibbs | 39 | 26% | 38.2 | | Derrick Henry | 33 | 22% | 14.9 |
| Trey McBride | 39 | 26% | 17.1 | | Garrett Wilson | 33 | 22% | 4.2 |
| Jaylen Warren | 38 | 25% | 36.8 | | Brock Bowers | 28 | 19% | 17.6 |
| Michael Wilson | 37 | 25% | 5.3 | | D'Andre Swift | 27 | 18% | 6.4 |
| Amon-Ra St. Brown | 36 | 24% | 9.9 | | Davante Adams | 26 | 17% | 5.2 |
| Jonathan Taylor | 31 | 21% | 9.7 | | Trey McBride | 25 | 17% | 6.6 |
| Tee Higgins | 30 | 20% | 3.2 | | Nico Collins | 25 | 17% | 30.3 |
| Brock Bowers | 28 | 19% | 22.0 | | Kenneth Walker III | 24 | 16% | 33.4 |

With no cap the model would have put Swift in 54% of week-5 lineups, on the strength of the Monangai volume it
handed him; he scored 15.3. The only other player above 30% in either week is Smith-Njigba in week 4 (37%). The
overlap rule and the spread of stacks already do most of the diversifying.

Exposure on 15%+ players, by player, is in `weeks/2026-w05/backtest_runs_chalk.csv`.

### 7.4 Week 4: entered 111.3 against 105.1 model-only

The week-4 lineups Doug entered averaged 111.3. The new code run model-only averages 105.1 (104.9 with the
mean-only calibration). That is not a like-for-like measure of the code, because the two runs differ in all of
these:

| | Entered week 4 | New code, model-only |
|---|---|---|
| Projection overrides | 6 (Nacua, McCaffrey, Montgomery, E. Wilson, Addison, Hockenson) | none |
| Red | 50 players, plus all of TEN and MIA | none |
| Yellow / green | 18 capped at half, 11 forced to a minimum | none |
| Questionable players | allowed (capped at 12% each) | excluded |
| Stack teams | 10 hand-picked (JAC 25, BUF 25, KC 20, CIN 18, DAL/HOU/SF 15, LV/LAR 12, SEA 10), random draws | 21 teams by implied total, fixed counts |
| Stack rules | BUF: Allen + 1 receiver + Cook | QB + 2 receivers + 1 bring-back everywhere |
| Projection code | Phase 1: no prior blend, none of the week-6 changes | prior blend + week-6 changes |
| Lineups | 149 | 150 |

So the 6-point difference mixes Doug's reads, the stack choices and three rounds of projection changes. The reads
look like the larger part: a re-run this morning with the full week-4 config on the pre-week-6 code (prior blend
on) averaged 115.7 with 7 top-1% lineups. That run includes Doug's week-4 greens, which hit at low ownership
(Kyren Williams, Nacua, Emanuel Wilson, Hockenson). I did not finish the matching run with the week-4 config on
the week-6 code (it is slow with forced players), so the split between reads and code is not measured.
(Done since: see 8.2. The reads were worth +4.6.)

For contrast, in week 5 the comparison is clean (both model-only, same settings): 108.3 entered, 113.2 on the
new code.

### 7.5 What these tests say together

- The model's problem on chalk is projection, not the cap or the flex: ownership carries information the entered
  projections lacked (7.1), and no optimizer setting moves our chalk exposure much (7.3).
- Doug's week-4 reads were worth more than any change tested here.
- Nothing in 7.3 earns a default change yet. The draw weight is the one to test on more slates.

### 7.6 Trades (`[[status.trade]]`)

**How the code handled a traded player before this change** (and still does when there is no trade entry). A
player whose FanDuel team differs from his team in the stats:

- projects with his old-team per-game volume, scaled to the new team's implied total;
- takes nothing from his new teammates, so the new team's targets add up to more than a full game;
- hands nothing to his old teammates, because he is not listed out;
- if he is listed out, his old-team volume is partly handed to his **new** teammates, which is wrong, and his old
  teammates still get nothing.

A run now prints a warning for any such player with real volume who has no trade entry.

**What week 6 would do with Harrison as-is, and with the entry.** Week-6 inputs are not in, so this is a
simulated trade on week-5 data: Harrison moved to HOU and active. `new_target_share = 0.15` is a placeholder to
show the mechanics, not a recommendation. Shares are of each team's pre-trade targets per game.

HOU (41.3 targets a game before the trade):

| Player | Before trade | As-is | With entry (0.15) | With entry, first-week factor 0.6 |
|---|---|---|---|---|
| Marvin Harrison Jr. | - | 10.1% | 15.0% | 9.0% |
| Nico Collins | 20.6% | 20.6% | 17.5% | 18.7% |
| Dalton Schultz | 15.9% | 15.9% | 13.5% | 14.5% |
| Xavier Hutchinson | 13.4% | 13.4% | 11.4% | 12.2% |
| Jared Wayne | 9.7% | 9.7% | 8.2% | 8.8% |
| Kayshon Boutte | 7.9% | 7.9% | 6.7% | 7.2% |
| Jaylin Noel | 6.5% | 6.5% | 5.5% | 5.9% |
| Other 7 (RBs, TEs) | 26.0% | 26.0% | 22.2% | 23.7% |
| **Team total** | **100%** | **110.1%** | **100%** | **100%** |

As-is, HOU is projected for 10% more targets than it throws. With the entry the total stays at 100% and every
teammate gives up the same proportion.

ARI (38.9 targets a game before the trade, Harrison 10.8% of them):

| Player | Before trade | As-is | With entry |
|---|---|---|---|
| Marvin Harrison Jr. | 10.8% | - | - |
| Trey McBride | 28.2% | 28.2% | 31.0% |
| Michael Wilson | 25.2% | 25.2% | 27.6% |
| Kendrick Bourne | 11.1% | 11.1% | 12.2% |
| Jeremiyah Love | 8.4% | 8.4% | 9.2% |
| Others | 16.3% | 16.3% | 17.8% |
| **Team total** | **100%** | **89.2%** | **97.8%** |

As-is, Harrison's 10.8% vanishes from ARI. With the entry, 80% of it (the standing redistribution share) goes to
his old teammates pro rata: Wilson goes from 25.2% to 27.6% (9.8 to 10.75 targets a game), and the rest of the
gap to 100% is the 20% the rule does not hand out.

In projected points (week-5 slate): Harrison 6.3 as-is and 9.5 with the entry (5.6 with the 0.6 factor); Collins
16.3 as-is and 13.9 with it; Wilson 14.2 as-is and 15.7 with it; McBride 16.7 and 18.0.

**The entry:**

```toml
[[status.trade]]
player = "Marvin Harrison Jr."
from = "ARI"
to = "HOU"
new_target_share = 0.15      # required: his share of the new team's targets
first_week_factor = 0.6      # optional, default 1.0
```

- Old team: treated as a player ruled out for the first time, in full, even if he had already missed games there.
- New team: he gets `new_target_share` x `first_week_factor` of the team's targets per game, taken from teammates
  in proportion to their own. His catch rate and yards per target stay his own; carries are not moved.
- **An empty `new_target_share` stops the run. Confirmed:** `[[status.trade]] Marvin Harrison Jr. (ARI -> HOU): set
  new_target_share, his share of the HOU targets (e.g. 0.15). The model will not guess the role of a traded player.`
- If he is listed out, only the old-team half applies. If he is not on the slate at all, the old-team half still
  applies and no share is needed.
- FanDuel still listing him on his old team is handled: he is moved to the new one.

`config/2026-w06/week.toml` has the Harrison entry with `new_target_share` commented out, so the first week-6
run will stop until Doug sets it. The entry should come out once his HOU games carry his role, and stays Doug's
call until then: left in, it keeps handing his ARI volume out in full.

Tests: `tests/test_trade.py` (3 tests). 46 tests pass in total.

### Files added in this pass

- `weeks/2026-w05/calibration_ceiling.csv` (7.2), `backtest_runs.csv` and `backtest_runs_chalk.csv` (7.3).
- `[optimizer.starters_min_proj]` (off by default) is the switch used for the second-RB run.

## 8. Week-6 defaults (Oct 12, third pass)

Doug's decisions after section 7: cap stays 25, **draw weight 40%** adopted (`[optimizer] mean_weight = 0.6`,
was 0.4), no second-RB rule, calibration stays mean-only. This pass adds the RB spread, measures the week-4 gap,
and sets the Harrison trade.

### 8.1 Wider RB spread

**Adopted as a default: `[model.spread] RB = 1.376`.** Neither week got worse by more than a point (week 5 is
0.6 lower, week 4 is 0.6 higher).

What it does. After the calibration, every RB draw is moved to 1.376 times its distance from the player's mean.
Draws pushed below zero are set to zero and the row is rescaled, so the mean, and therefore the projection, does
not change. Only the ceiling and floor move: the average RB 90th percentile goes from 19.4 to 22.3.

How it was fit. On 2025 weeks 4-18, with the calibration applied as in the model (mean only, leave-one-week-out
slopes), the factor is the smallest one at which 10% of RBs beat their 90th percentile. It was fit on all graded
RBs, not only those projected 16+, because RBs were short at every level. Leave-one-week-out, the factor ranges
from 1.31 to 1.42; 1.376 is the fit on all 15 weeks. `src/fit_spread.py` refits it.

Share beating the simulated 90th percentile (target 10%), 2025 weeks 4-18, each week graded with a factor fit on
the other 14:

| Position | Tier | n | Before | After |
|---|---|---|---|---|
| RB | All | 651 | 14.7% | 9.8% |
| RB | Under 8 | 128 | 14.1% | 9.4% |
| RB | 8-16 | 375 | 13.6% | 9.6% |
| RB | 16+ | 148 | 18.2% | 10.8% |
| QB | All | 411 | 11.9% | 11.9% |
| WR | All | 945 | 10.9% | 10.9% |
| TE | All | 371 | 13.7% | 13.7% |

(The 18.9% in 7.2 was RBs at 16+ over 2025 and 2026 together; on 2025 alone it is 18.2%.)

Check on the two 2026 slates with the real pipeline, which were not used in the fit: RBs beating their 90th
percentile go from 10 of 62 (16%) to 6 of 62 (10%). The other positions are untouched: QB 6 of 43, WR 11 of 98,
TE 6 of 40.

Only RBs were widened, as asked. TEs are also short (13.7%; the same fit gives 1.24) and QBs slightly (11.9%;
1.12). WRs are about right (1.07). Widening TEs would probably push the TE-flex share back up, and it is not
tested.

Weeks 4 and 5, model-only, cap 25, draw weight 40%, with and without the wider RB spread:

| Week | Run | Avg score | Median | Best rank | Top 1% | Top 10% | RB / WR / TE flex |
|---|---|---|---|---|---|---|---|
| 5 | Draw weight 40% | 114.2 | 110.5 | 5,291 | 1 | 9 | 29 / 34 / 37% |
| 5 | + RB spread 1.376 | 113.6 | 113.3 | 5,291 | 1 | 6 | 35 / 28 / 37% |
| 4 | Draw weight 40% | 106.7 | 104.5 | about 4,400 | 3 | 22 | 18 / 33 / 49% |
| 4 | + RB spread 1.376 | 107.4 | 105.6 | 1,820 | 4 | 24 | 31 / 31 / 38% |

The field's flex mix was 63 / 18 / 15% in week 5 and 56 / 22 / 19% in week 4.

- **Average score:** -0.6 in week 5, +0.6 in week 4. Both are inside the noise of one slate.
- **Flex:** RB-flex rises in both weeks (29 to 35%, 18 to 31%). In week 4 it comes out of TE-flex (49 to 38%); in
  week 5 it comes out of WR-flex and TE-flex stays at 37%.
- **Top 1%:** unchanged in week 5, 3 to 4 in week 4, where the best lineup also improves (169.2 to 173.6).
- Exposure on players the field owned 15%+ barely moves (14.7 to 15.0% in week 5, 13.9 to 14.0% in week 4): the
  RBs at the 25 cap are the same players either way.

The case for adopting it is the coverage table, which rests on 651 RB games. The two slates only show that it
does no harm.

### 8.2 Week 4: how much of 111.3 against 104.9 came from Doug's reads

The run was not slow on the week-6 code (about a minute per step), so it is finished. Week 4, the code as of
section 7 (mean-only calibration, draw weight 60%, cap 25, no RB spread, so it lines up with the 104.9 baseline
and with what was entered), adding Doug's week-4 config one piece at a time:

| Step | Avg score | Change | Top 1% | Top 10% | Best rank |
|---|---|---|---|---|---|
| Model-only (21 stack teams by implied total, questionable out) | 104.9 | | 3 | 20 | about 4,400 |
| Doug's 10 stack teams and weights, BUF rule, questionable allowed | 107.5 | +2.6 | 1 | 16 | about 5,700 |
| + 6 projection overrides | 107.8 | +0.3 | 3 | 15 | 1,459 |
| + red and yellow | 110.8 | +3.0 | 3 | 13 | about 4,400 |
| + green (the full week-4 config) | 112.1 | +1.3 | 2 | 17 | about 3,900 |
| Entered on Oct 4 (Phase-1 code, 149 lineups) | 111.3 | | 4 | | 1,054 |

- **Doug's reads were worth +4.6 of the 7.2 points** (overrides +0.3, red and yellow +3.0, green +1.3). His stack
  teams, the Buffalo rule and allowing questionable players were worth the other +2.6.
- **Red and yellow did most of it**, as in week 5 (+2.5 there). Green was positive here (+1.3) and negative in
  week 5 (-1.7).
- **Average score and top finishes do not move together.** The reads lifted the average by 4.6 but the top-1%
  count went from 3 to 2.
- **The code itself is about level on this slate:** 112.1 with the full config now against 111.3 entered. But the
  same config on the pre-week-6 code scored 115.7 with 7 top-1% lineups (7.4), so the week-6 projection changes
  cost 3.6 points on week 4 when Doug's reads are applied. Model-only on week 5 the same changes were worth
  about +5 (108.3 to 113.2). This is one slate, and the yellow and green numbers were set against the old
  projections.

Results: `weeks/2026-w05/backtest_w4_reads.csv`.

### 8.3 Harrison

`config/2026-w06/week.toml` now has `new_target_share = 0.15` and `first_week_factor = 0.7` in his
`[[status.trade]]` entry, so the week-6 run no longer stops on it. The same numbers are recorded under
`[shadow.trade]` as Doug's trade read. Unlike the colours, this read is applied; the shadow copy is there so it
can be scored against his actual share afterwards.

This week he gets 0.15 x 0.7 = 10.5% of Houston's targets. On the simulated week-5 slate that is Harrison 10.5%,
Collins 20.6% to 18.4%, Schultz 15.9% to 14.2%, Hutchinson 13.4% to 12.0%, team total 100%. His own number is
close to the 10.1% he carried over from Arizona before the fix; the difference is that his new teammates now pay
for it. Arizona is as in 7.6 (Wilson 25.2% to 27.6%).

### 8.4 Defaults for week 6

| Setting | Value | Changed in this pass |
|---|---|---|
| Exposure cap | 25 | no |
| Draw weight | 40% (`[optimizer] mean_weight = 0.6`) | yes, was 60% |
| Second RB per team | off | no |
| Calibration | mean only, knee 16 | no |
| RB spread | `[model.spread] RB = 1.376` | yes, new |

To turn the RB spread off, set `RB = 1.0`. Tests: two added in `tests/test_adjust.py`; 48 pass in total.

Still needed for the first week-6 run: `[status]`, `[stacks.weights]` from the week-6 lines, and Guru if used.

### Files added in this pass

- `src/fit_spread.py`; `weeks/2026-w05/spread_cv.csv` and `spread_fit.csv` (coverage and factors by position).
- `weeks/2026-w05/backtest_spread.csv` and `backtest_spread_p90.csv` (8.1), `backtest_w4_reads.csv` (8.2).

## 9. Three changes from the history refit, for week 6 (Oct 12, fourth pass)

From `docs/phase2_history.md`: the calibration slope above 16, injury volume routed by position, and tapered
spread factors for all four positions. Each was added in the order Doug gave and tested on weeks 4 and 5.

**All three are adopted as defaults: none made either week's average score worse by more than a point. But the
top finishes got worse, and Doug should see that before week 6 locks.** Top-1% lineups went from 1 and 4 (weeks 5
and 4) to 0 and 0 with all three on. The fall came with the routing in week 4 (3 to 0) and with the tapered spread
in week 5 (1 to 0). Section 9.4 has the table and 9.5 has the switches to turn either off.

### 9.1 Calibration slope above 16: 0.28 to 0.36

`[model.calibration] top_slope = 0.36`. A projection loses 36% of each point above 16 instead of 28%: 20 becomes
18.6 (was 18.9), 24 becomes 21.1 (was 21.8). Nothing under 16 changes. The RB slope stays at 0.12.

### 9.2 Injury volume routed by position

`[model.injury] routing = "position"`, with the shares in `[model.injury.position_share]`:

| Player out | Volume | To teammates at his position | To the other positions | Total | Rule through week 5 |
|---|---|---|---|---|---|
| WR | Targets | 77% | 16% | 93% | 80% to everyone pro rata |
| RB | Carries | 94% | 1% | 95% | same |
| RB | Targets | 70% | 0% | 70% | same |
| TE | Targets | 46% | 4% | 50% | same |

Inside each group the volume is still split in proportion to each player's own volume. If the group has no volume
at all (no other TE with targets, say), that part is not handed out. A WR's or TE's carries, which are a handful a
season, keep the old 80% rule. The fading for players who have already missed games (section 2) still applies on
top. The old team of a traded player is routed the same way.

Projections before and after, week 5 (both with the 0.36 slope; "gained" is targets plus carries a game):

| Player | Gained before | Gained after | Projection before | After | Actual |
|---|---|---|---|---|---|
| Braelon Allen | 8.2 | 11.3 | 11.2 | 13.7 | 21.1 |
| Jaylen Warren | 5.7 | 7.7 | 17.4 | 18.6 | 36.8 |
| Tre' Harris | 2.1 | 5.7 | 8.9 | 14.3 | 2.6 |
| Emanuel Wilson | 3.2 | 5.1 | 10.5 | 12.5 | 12.2 |
| Justin Jefferson | 1.3 | 2.5 | 12.6 | 14.6 | 15.8 |
| Marquez Valdes-Scantling | 1.0 | 2.7 | 3.6 | 5.6 | 3.2 |
| D'Andre Swift | 9.7 | 12.6 | 20.2 | 21.8 | 15.3 |
| Tre Tucker | 0.4 | 1.4 | 9.4 | 10.9 | 5.5 |
| Romeo Doubs | 0.9 | 1.6 | 10.8 | 12.3 | 2.1 |
| Terry McLaurin | 1.2 | 2.1 | 12.7 | 14.1 | 10.2 |
| Michael Wilson | 1.0 | 2.1 | 15.7 | 17.0 | 5.3 |
| Antonio Williams | 0.8 | 1.4 | 8.3 | 9.3 | 4.6 |
| Kenyon Sadiq | 1.0 | 0.2 | 8.0 | 7.0 | -0.7 |
| Pat Freiermuth | 0.9 | 0.3 | 9.0 | 8.0 | 19.0 |
| Mason Taylor | 1.1 | 0.3 | 6.6 | 5.6 | 3.9 |
| Oronde Gadsden II | 1.9 | 0.6 | 8.6 | 6.7 | 0.0 |

Week 4 moved ten players by a point or more: Braelon Allen 11.2 to 14.2 (scored 7.7), George Holani 5.9 to 7.8
(2.5), Jordan Addison 10.5 to 12.2 (7.1), Dontayvion Wicks 10.5 to 12.2 (3.3), Isaiah Davis 3.7 to 5.0 (0.0),
Jauan Jennings 7.5 to 8.7 (1.3), Emanuel Wilson 9.0 to 10.1 (25.5), and down a point each Saquon Barkley
(1.5), Kenyon Sadiq (0.0) and T.J. Hockenson (21.4).

- **It does what was intended for Allen and Warren:** both move toward what they scored, Allen by 2.5 and Warren
  by 1.2. They are still well short (13.7 against 21.1, 18.6 against 36.8).
- **It did not make the projections more accurate on these two slates.** For the players it moved by a point or
  more, the average miss went from 6.6 to 6.9 in week 5 and from 7.5 to 8.4 in week 4. Over all players projected
  5+, RMSE is unchanged (7.63 to 7.66 and 7.05 to 7.05). Receivers who were raised mostly missed (Tre' Harris,
  Doubs, Tucker, Michael Wilson, Wicks, Addison).
- The case for it is the history (the first missed game of 124 WRs, 105 RBs and 59 TEs), not these 26
  players.

Harrison trade, simulated on the week-5 slate with his week-6 entry (15% share, first-week factor 0.7):

| Player | Gained, pro rata | Gained, by position | Projection, pro rata | By position |
|---|---|---|---|---|
| Michael Wilson (WR) | 0.95 | 2.13 | 15.7 | 17.0 |
| Trey McBride (TE) | 1.06 | 0.37 | 17.9 | 17.1 |
| Kendrick Bourne (WR) | 0.42 | 0.94 | 7.2 | 8.0 |
| Jeremiyah Love (RB) | 0.31 | 0.11 | 13.1 | 12.8 |

Harrison's Arizona targets now go mostly to the other Cardinals receivers: Wilson is up 1.3 and McBride down 0.8.
Houston is unchanged by the routing (Collins 14.7, Harrison 6.5), because the new team's side of a trade was not
touched. This table was run with 4,000 simulations, so projections carry about 0.1 of noise.

### 9.3 Tapered spread for all four positions

`[model.spread]` now takes `{ low, top }` for a position. `low` applies to players projected up to 12; the factor
then falls in a straight line to `top` at 20 and above (`[model.spread_taper] from = 12, to = 20`). The projection
itself is never changed, only how wide the draws around it are.

Fit on 2021-2025 with Vegas totals and the 0.36 calibration (`src/fit_taper.py`): `low` so that 10% of the
players projected under 16 beat their simulated 90th percentile, `top` so that the same holds from 16 up, never
below 1.

| Position | Low (up to 12) | Top (20 and up) | Low, leaving one season out | Flat factor before |
|---|---|---|---|---|
| QB | 1.50 | 1.00 | 1.44 to 1.56 | 1.0 |
| RB | 1.43 | 1.04 | 1.41 to 1.46 | 1.376 |
| WR | 1.23 | 1.00 | 1.17 to 1.27 | 1.0 |
| TE | 1.22 | 1.22 | 1.20 to 1.22 | 1.0 |

TEs get one flat factor: only about 45 TE games in five seasons were projected 16+, too few to fit a taper.

Share beating the simulated 90th percentile (target 10%). "Before" is the section-8 setting (RB 1.376, others
unwidened). "Tapered" grades each season with factors fit on the other four. Tiers are by calibrated projection.

| Position | Tier | n | Before | Tapered |
|---|---|---|---|---|
| QB | All | 2,067 | 13.8% | 8.8% |
| QB | 8-16 | 701 | 19.8% | 9.7% |
| QB | 16+ | 1,365 | 10.7% | 8.3% |
| QB | 20+ | 408 | 7.2% | 7.2% |
| RB | All | 3,365 | 9.9% | 10.1% |
| RB | Under 8 | 828 | 11.4% | 10.5% |
| RB | 8-16 | 2,132 | 10.0% | 9.8% |
| RB | 16+ | 405 | 6.7% | 11.0% |
| WR | All | 5,063 | 12.3% | 9.7% |
| WR | Under 8 | 1,757 | 14.4% | 11.8% |
| WR | 8-16 | 2,771 | 11.8% | 8.8% |
| WR | 16+ | 535 | 7.9% | 7.7% |
| TE | All | 1,698 | 13.2% | 9.9% |
| TE | Under 8 | 939 | 14.7% | 11.2% |
| TE | 8-16 | 715 | 11.5% | 8.4% |

- **RBs at 16+ go from 6.7% to 11.0%:** the flat 1.376 was making the top RBs' ceilings too high, and the taper
  fixes that.
- **Every position is within about 1 point of 10% overall.** By tier the range is 7.2% to 11.8%.
- **QBs and WRs at 16+ stay under 10%** (8.3% and 7.7%). Their ceilings were already slightly high before any
  widening, and the factor is not allowed below 1.
- The QB factor of 1.50 applies to few players in practice: backup QBs project 0, and most starters project 16+.

### 9.4 Lineup test

Weeks 4 and 5, model-only, cap 25, draw weight 40%, adding the changes one at a time. The baseline is the
default as of section 8.

| Week | Run | Avg score | Change | Top 1% | Top 10% | Best score | RB / WR / TE flex |
|---|---|---|---|---|---|---|---|
| 5 | Baseline | 113.6 | | 1 | 6 | 191.3 | 35 / 28 / 37% |
| 5 | + slope 0.36 | 113.5 | -0.1 | 1 | 5 | 191.3 | 37 / 27 / 36% |
| 5 | + routing by position | 113.4 | -0.2 | 1 | 6 | 199.0 | 41 / 37 / 21% |
| 5 | + tapered spread | 112.9 | -0.5 | 0 | 6 | 180.9 | 33 / 43 / 25% |
| 4 | Baseline | 107.4 | | 4 | 24 | 173.6 | 31 / 31 / 38% |
| 4 | + slope 0.36 | 107.1 | -0.3 | 3 | 22 | 173.6 | 29 / 31 / 39% |
| 4 | + routing by position | 108.1 | +1.1 | 0 | 7 | 153.4 | 33 / 31 / 36% |
| 4 | + tapered spread | 107.8 | -0.4 | 0 | 12 | 160.4 | 25 / 36 / 39% |

"Change" is against the row above. The field's flex mix was 63 / 18 / 15% in week 5 and 56 / 22 / 19% in week 4.

By Doug's rule (adopt unless either week is worse by more than a point), all three pass. The largest single drop
is 0.5.

What the rule does not capture:

- **Top finishes fell.** With all three on, neither week has a top-1% lineup, against 1 and 4 at the baseline.
  Week 4's top-10% count went from 22 to 7 when the routing was added, while its average went up by a point. The
  best lineup in week 4 fell from 173.6 to 153.4.
- **The tapered spread fails the rule if it is added without the routing.** On top of the slope alone it scores
  114.4 in week 5 (+0.9) and 105.9 in week 4 (-1.2), with top-1% counts unchanged at 1 and 3. In the order asked,
  on top of the routing, it passes.
- **TE-flex dropped in week 5** (36% to 21% with the routing) and barely moved in week 4. WR-flex rose to 43% in
  week 5. RB-flex ends lower than the baseline in both weeks (33% and 25%).
- These are 150 lineups on two slates. Top-1% counts between 0 and 4 can move on one or two lineups, and no run
  here differs from another by more than about 2 points of average score.

### 9.5 Defaults after this pass, and how to undo each

| Change | Setting now | To go back |
|---|---|---|
| Calibration slope above 16 | `[model.calibration] top_slope = 0.36` | `0.28` |
| Injury routing | `[model.injury] routing = "position"` | `routing = "pro_rata"` |
| Spread | `[model.spread]` QB 1.50/1.00, RB 1.43/1.04, WR 1.23/1.00, TE 1.22 | `[model.spread]` with only `RB = 1.376` |

Any of these can be set for week 6 alone in `config/2026-w06/week.toml`. The run that kept the most top finishes
while still using the history fit was the slope alone (1 and 3 top-1% lineups).

Tests: `tests/test_routing.py` (6 tests); 62 pass in total.

### Files added in this pass

- `src/fit_taper.py`; `weeks/history/taper.csv` and `taper_fits.csv` (9.3).
- `weeks/2026-w05/backtest_section9.csv` (9.4; runs `base`, `s1`, `s12`, `s123`, and `s13` = slope plus taper
  without routing).

## Files

- `src/dfs/usage.py`, `src/dfs/project.py`, `config/defaults.toml`: the four changes.
- `src/fit_calibration.py`: refits the calibration slopes; `weeks/2026-w05/calibration_cv.csv`, `calibration_fit.csv`.
- `weeks/2026-w05/backtest_week6_prep.csv`: the step-by-step RMSE table. `backtest_caps.csv`: section 5.
