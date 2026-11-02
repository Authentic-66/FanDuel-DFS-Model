# Week-9 tests (Nov 2, 2026) — past seasons, nothing changed live

Doug's four tests from the week-8 review. **No setting has been changed**; every number below comes from scratch runs
(nothing in `weeks/` or `config/` rewritten). Recommendations are for Doug to decide before the week-9 prelim.

Data and method:
- **History rows:** 2021-2025, weeks 4-18, 12,214 player-weeks: each player projected from earlier weeks plus the prior
  season, scaled by his team's Vegas implied total, then the current calibration and WR correction (`history.season_rows`,
  the same rows the calibration and spread were fit on). Seasons are weighted 0.75 per year back, and anything fitted is
  fit on four seasons and graded on the fifth (leave-one-season-out). The rows only hold players who recorded a stat
  that week, so the zero-scorers seen live are missing (docs/week7_prep.md section 3).
- **Absence games** (test 3): `fit_depth.py` re-run in scratch with today's code: the first game a starter missed,
  2,675 teammates projected with and without the redistributed volume.
- **Lineup test** (test 1 fix, and the other fixes as lineups): past seasons have no FanDuel salaries, so lineups can
  only be built on the archived 2026 weeks 5-8 (week 4 has no saved draws). Each candidate is applied as a shift to the
  archived draws, and the optimizer is re-run with that week's settings. These are four slates, and Oct 12's lesson
  holds: a dozen moved projections reshuffle all 150 lineups. So the lineup numbers are a sanity check, and the history
  tests carry the weight.
- **Test 4:** nflverse team stats (offence passing + rushing EPA per play) and schedule closing lines, 2020-2025.

## Summary

| Test | Finding | Recommendation |
|---|---|---|
| 1. RB / flex | RBs are calibrated fine; the gap is the flex choice (field top lineups RB 75-90%, ours TE 31-78%). TEs are over-projected at 12+, but correcting it moves only ~9 flex slots a week and cost 0.6 a lineup | **No** (no fix found; TE slope kept as an option) |
| 2. WR 24+ correction | Your 24+ term helps a little. The bigger fault: the current correction *raises* WRs on low-total teams. One-sided, refit (b -0.57) is best on every history measure; lineups neutral | **Yes**, the one-sided version |
| 3. Injury bump | Teammates gain about 60% of the projected bump (k 0.61-0.73 in every season); live weeks 6-8 about 20%. Scaling by position fixes the bias | **Yes**, scale by position (lineups slightly negative, within noise) |
| 4. Bad-defence games | 28 games in 6 seasons; Vegas already prices them (closing total +4.4); no edge in (a) or (b); (c) not significant | **No** |

**Lineup test, archived weeks 5-8** (points per lineup vs the as-entered rebuild, which reproduced all 150 entered
lineups each week; top-10% / top-1% counts summed over the four weeks):

| Variant | Wk 5 | Wk 6 | Wk 7 | Wk 8 | Mean | Top 10% (sum) | Top 1% (sum) | Best by week | Flex TE by week |
|---|---|---|---|---|---|---|---|---|---|
| As entered | 108.3 | 104.0 | 100.9 | 106.3 | | 32 | 1 | 184.9 / 158.4 / 151.4 / 190.4 | 68 / 47 / 117 / 95 |
| TE slope 0.53 above 10 | -1.3 | +0.1 | +0.2 | -1.5 | **-0.6** | 34 | 0 | 180.8 / 149.1 / 152.4 / 190.4 | 58 / 39 / 107 / 83 |
| Routing bump x k by position | 0.0 * | -0.8 | -0.7 | 0.0 | -0.4 | 31 | 0 | 184.9 / 154.9 / 151.4 / 190.7 | 68 / 50 / 117 / 96 |
| WR one-sided, b -0.57 | 0.0 | -0.1 | 0.0 | +0.1 | **0.0** | 33 | 1 | 184.9 / 163.6 / 151.4 / 190.4 | 71 / 55 / 116 / 98 |
| WR one-sided + routing x k | 0.0 | -0.5 | -0.4 | -0.2 | -0.3 | 26 | 1 | 184.9 / 163.8 / 151.4 / 190.4 | 71 / 54 / 119 / 96 |
| All three | -0.8 | -0.6 | -0.9 | -0.7 | -0.7 | 28 | 0 | 180.8 / 146.8 / 151.4 / 190.4 | 58 / 49 / 110 / 86 |
| TE in flex capped at 35% (existing switch) | -0.5 | +0.3 | stalls at 144 | -0.3 | -0.2 (3 wks) | 19 (3 wks) | 0 | | 52 / 40 / - / 52 |

\* Week 5 has no saved routing bumps (the column was added in week 6), so that variant equals the baseline there.
Each change reshuffles 40-140 of the 150 lineups; differences under a point a lineup are within the noise measured on Oct 12.

## 1. RB / flex: why a TE in the flex, and why RBs trail the field

**The RB gap is the flex choice, not the RB pool.** For each live week, the field's RB points split by whether that
RB was in our eligible pool:

| Week | Field RB pts from RBs we could use | From RBs we could not (red / not RB1 / Q) | Our flex RB / WR / TE | Top 2,000 field lineups' flex RB / WR / TE |
|---|---|---|---|---|
| 5 | 50.0 | 0.4 | 24% / 31% / 45% | 90% / 3% / 7% |
| 6 | 37.2 | 0.6 | 47% / 22% / 31% | 81% / 13% / 6% |
| 7 | 38.4 | 1.9 (red 1.6) | 14% / 8% / 78% | 75% / 13% / 12% |
| 8 | 32.4 | 10.9 (red 10.4: Braelon Allen, Warren) | 21% / 15% / 63% | 87% / 8% / 5% |

Apart from week 8's reds, nearly every field RB point came from players our optimizer could pick. The best field
lineups put an RB in the flex 75-90% of the time; we put a TE there 31-78%. So the question is why the optimizer
values TEs over RBs for the flex.

**History, by position (current live means, projected minus actual, weighted):**

| Projected | QB | RB | WR | TE |
|---|---|---|---|---|
| 0-8 | | +0.18 | +0.43 | -0.15 |
| 8-12 | -2.23 | +0.04 | +0.55 | +0.29 |
| 12-16 | -0.69 | +0.74 | +1.27 | **+1.68** |
| 16-20 | -0.47 | -0.77 | +1.29 | **+4.15** (n 45) |
| 20+ | -0.17 | +1.34 (n 20) | +3.13 (n 17) | |

- **RBs are the best-calibrated skill position.** Each team's top RB is slightly *under*-projected (RB1 -0.42, beats
  his 90th percentile 11.6%). The second RB is over-projected (RB2 +1.24, beats p90 only 7.1%), which is why a second
  RB per team earned nothing in week 6 and would not now.
- **TEs projected 12+ are over-projected by 1.7-4.2 points**, and their ceilings are too wide at the top (6.9% beat their
  p90 against 10% expected; the TE spread is a flat 1.215). Both push the optimizer toward TEs: the mean through 60% of
  the objective, the ceiling through the 40% draw. Live it is worse: **TEs projected 8-12 in weeks 5-8 scored 6.8 on 9.6
  projected (n 32)**; 12+ scored 14.6 on 15.5 (n 13).
- Flex-range players projected 8-14: RBs reach 20 points 12.1% of the time (model 12.2%), WRs 10.4% (model 12.0%), TEs
  8.3% (model 9.3%). The model's RB upside is right; its TE and WR upside is a little high.

**Candidate fix: a TE calibration slope.** TEs lose part of each projected point above a knee, like the existing top
slope. Fit leave-one-season-out: knee 10, slope 0.47-0.58 (0.53 used); a knee of 12 pins at the 0.6 bound.

| TE projection | Bias | RMSE | r | 8-10 | 10-12 | 12-14 | 14+ |
|---|---|---|---|---|---|---|---|
| Current | +0.22 | 6.177 | 0.336 | +0.48 | -0.05 | +1.25 | +3.56 |
| Slope 0.53 above 10 | -0.03 | 6.135 | 0.342 | +0.48 | -0.50 | +0.28 | +4.07 (n 9) |

Better on every overall number, and it shrinks the TEs that compete for the flex. Narrowing the TE ceiling at the top
had no effect inside the current taper (12 to 20), because the TEs it would touch sit at 12-14. Not pursued.

**Lineup test (table above):** the TE slope changes 4-7 TE projections a week and cuts TE-flex lineups by only 8-12 a
week (week 8: 95 to 83). Points: -1.3, +0.1, +0.2, -1.5 (mean -0.6), top-10% 34 against 32, top-1% 0 against 1. The
existing TE-flex cap (35%) does what it says (week 8: 95 to 52), but it scored -0.2 over three weeks with fewer top-10%
lineups, and week 7 cannot build 150 with it.

**Why the optimizer still picks TEs:** the projection error is real but small next to the structure. FanDuel prices TEs
cheaply. Every lineup must stack its QB with two of his WR/TEs, so the team's TE is often already in. With RB1-only
and many red RBs (60 in week 8), the cheap RBs the field used (Tuten, Braelon Allen, Pollard) were either red or priced
above a $5,000 TE projected 8-10. The field's flex RBs were mostly RB1s we were allowed to use; we were simply lighter
on them because a TE fit the salary.

**Recommendation for test 1: no.** No fix showed up that improves both calibration and lineups. The TE slope is better
calibration in history (bias +0.22 to -0.03, RMSE 6.177 to 6.135, the same in every fold) but costs lineups in two of
four weeks and barely changes the flex mix. The flex cap costs points and can stall. Worth discussing instead: the red
RBs. Week 8's 10.4 field RB points from reds was the single largest piece of that week's RB gap.

## 2. WR implied-total correction: a stronger correction at 24+

The current correction moves every WR by -0.34 x mean x (implied / 22.5 - 1): down on high-total teams, **and up on
low-total teams**. History, projected minus actual by team implied total:

| WR variant (history, LOSO where fit) | Bias | RMSE | r | 14+ gap | <19 | 19-21.5 | 21.5-24 | 24-26.5 | 26.5+ |
|---|---|---|---|---|---|---|---|---|---|
| No correction | +0.82 | 7.126 | 0.419 | +2.16 | +0.38 | +0.06 | +0.88 | +1.29 | +1.64 |
| **Current** (b -0.34, both sides) | +0.72 | 7.099 | 0.419 | +1.48 | **+1.03** | +0.35 | +0.82 | +0.82 | +0.55 |
| Current + extra term above 24 (c 0.27) | +0.61 | 7.098 | 0.415 | +1.22 | +1.03 | +0.35 | +0.82 | +0.68 | +0.03 |
| One-sided, b -0.34 (no raise below 22.5) | +0.53 | 7.079 | 0.420 | +1.31 | +0.38 | +0.06 | +0.80 | +0.82 | +0.55 |
| **One-sided, refit b -0.57** (folds -0.49 to -0.64) | **+0.35** | **7.073** | 0.417 | **+1.00** | +0.38 | +0.06 | +0.74 | +0.53 | -0.14 |

- **Doug's 24+ term works as asked, but it is small:** the extra term (fit 0.15-0.38 by fold, 0.27 overall) lowers the
  24-26.5 gap from +0.82 to +0.68 and the 26.5+ gap from +0.55 to +0.03. It improves the 24+ gap in all five seasons.
  RMSE barely moves (7.0990 to 7.0975), and the rank correlation drops slightly (0.4188 to 0.4153).
- **The bigger fault is the low end.** Raising WRs on teams under 19 makes them worse (+0.38 to +1.03). Making the
  correction one-sided (no raise below the league average) is the best single change. Refitting it on that basis (b
  -0.57) gives the lowest bias and RMSE of every variant and cuts the 14+ gap to +1.00.
- Live: WRs at 24+ were projected 9.8 / 10.2 in weeks 7 / 8 and scored 8.3 / 9.1. The 24+ term would have made them
  9.6 / 9.8, closing only about a fifth of the gap. Live WRs are over at every total, which is the zero-score
  problem as much as the correction.

**Lineup test:** one-sided b -0.57 alone: 0.0, -0.1, 0.0, +0.1 points a lineup; top-10% 33 against 32; top-1% 1 against 1
(week 6's best 163.6, rank 1,707, against 158.4).

**Recommendation for test 2: yes, but the one-sided version rather than an extra 24+ term.** Replace the both-sided
-0.34 with a one-sided correction (WRs on teams above the league-average total move down by 0.57 x mean x (implied /
22.5 - 1); WRs below it are left alone). Effect on calibration (history): WR bias +0.72 to +0.35, RMSE 7.099 to 7.073,
14+ gap +1.48 to +1.00; the under-19 band goes from +1.03 back to +0.38; rank correlation 0.419 to 0.417 (a slight
loss). Lineups neutral. Needs a small code change (a one-sided option in `project.implied_shift`), built switched off,
plus the week-pinning for weeks 7-8. If you prefer your 24+ term: it is the smaller, safer step (c 0.27), and lineups
were not tested separately.

## 3. Injury bump: is the projection boost for teammates too big?

Absence games 2021-2025 (first game a starter missed, teammates who played), live routing (position routing, depth
split for WRs), calibrated:

| Teammates moved 1+ by routing (n 849) | Projected | Actual |
|---|---|---|
| Without the redistributed volume | 5.05 | |
| With it (live routing) | 8.11 (bump +3.06) | **6.89 (gain +1.84)** |

**Teammates gain 60% of the bump.** The least-squares scale k (actual gain = k x bump), fit leave-one-season-out, is
0.61-0.73 in every fold (0.69 overall). By position:

| Group | n | Bump | Actual gain | k |
|---|---|---|---|---|
| RB out | 244 | 4.69 | 3.41 | 0.82 |
| WR out | 443 | 2.19 | 1.11 | 0.47 |
| TE out | 63 | 2.91 | 1.10 | 0.28 |
| Depth players (projected under 8 without the bump) | 649 | 3.11 | 2.06 | 0.70 |
| Established players (8+) | 200 | 2.88 | 1.05 | 0.64 |

Folds for k by out position: RB 0.71-0.87, WR 0.39-0.54, TE 0.10-0.59 (63 rows).

| Projection (teammates moved 1+) | Bias | RMSE | All teammates: bias | RMSE |
|---|---|---|---|---|
| No redistribution | -1.84 | 6.618 | -0.63 | 5.938 |
| Old rule (80% pro rata, through week 5) | -0.05 | 6.190 | +0.41 | 5.853 |
| **Live routing** | **+1.23** | 6.220 | +0.42 | 5.796 |
| Bump x 0.69 (one k) | +0.20 | 6.129 | +0.07 | 5.766 |
| **Bump x k by position (RB 0.82, WR 0.47, TE 0.28)** | **+0.06** | **6.117** | **+0.01** | **5.762** |

**Live 2026:** players with a routing bump of 1+ in weeks 6-8 (n 69) were projected 10.2 and scored 8.3 on a 2.35 bump:
they kept about 20% of it. Week 8's list (Stevenson +4.1 scored 10.5, Dobbins +3.0 scored 1.3, Bijan +2.9 scored 7.6) is
typical. Questionable routing uses the same mechanism (its share of the draws), so it would scale the same way.

**Lineup test:** routing x k alone: 0.0 (week 5 untested), -0.8, -0.7, 0.0; top-10% 31 against 32; top-1% 0 against
1 (week 6's 158.4 lineup lost). With the WR change as well: -0.3 a lineup, top-10% 26 against 32.

**Recommendation for test 3: yes, scale the bump by position: RB out x 0.8, WR out x 0.45, TE out x 0.3.** It is the
clearest history result of the four: the same direction in every season and position group, and on live 2026 the bump
held up even worse (20% kept). Effect on calibration: moved teammates' bias +1.23 to +0.06, RMSE 6.220 to 6.117; all
teammates' bias +0.42 to +0.01. The lineup cost (-0.4, one lost top-1% lineup) is within the reshuffle noise, but it
leans the wrong way, so say so if you would rather wait a week. Needs code: a per-position multiplier on the routed
volume (`usage.redistribute_out`; Q routing uses the same path), built switched off, weeks 4-8 pinned, and a proof that
nothing else moves.

## 4. Bad-defence matchups (Doug's idea)

Ratings: each team's offence EPA per play (passing + rushing EPA over attempts + carries + sacks) and defence EPA per
play allowed, from **that season's games before the week only** (at least 3 games, so weeks 4-18). **Flag: both
defences in the worst third that week, and both offences at or above the median.** A looser version (both defences
in the worse half) is shown for sample size. Expectation for (b): team FanDuel points (QB/RB/WR/TE) = a + b x implied
total, fit leave-one-season-out on all team-games (18.3 + 2.62 x implied overall).

**Sample size per season (flagged / all games, weeks 4-18):**

| Season | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|---|---|---|
| Strict flag | 6 / 208 | 2 / 224 | 10 / 223 | 4 / 224 | 3 / 224 | 3 / 224 | **28 / 1,327** |
| Loose flag | 13 | 7 | 18 | 10 | 17 | 8 | 73 |

About 5 strict games a season, one every three weeks; the main slate would see about two-thirds of them.

**Results (strict flag; loose in brackets):**

| | Flagged | Other games | Difference | p |
|---|---|---|---|---|
| Closing total | 49.3 [48.5] | 44.9 [44.8] | Vegas already adds 4.4 points | |
| (a) Actual total - closing total | -0.1 [+0.9] (95% CI -5.7 to +5.5) | +0.8 | -0.9 [+0.1] | 0.76 [0.95] |
| (b) Team FD points - expected, both teams | -1.2 [+1.2] | 0.0 | -1.3 [+1.3] | 0.69 [0.51] |
| (b) **Lower-implied (underdog) team** | **+1.2** [+3.2] (CI -7.9 to +10.3) | **+1.25** (all other underdogs) | 0.0 [+2.1] | 0.99 [0.47] |
| (b) Higher-implied team | -3.7 [-0.7] | -1.2 (all other favourites) | -2.5 [+0.5] | 0.58 [0.85] |
| (b) Real points - implied, underdog | +0.2 [+0.8] | +0.4 | -0.2 [+0.4] | 0.94 [0.74] |
| (c) SD of actual total | 16.6 [15.3] | 13.8 [13.7] | wider | Levene 0.60 [0.35] |
| (c) SD of total - closing total | 15.2 [14.7] | 13.1 [13.0] | | |
| (c) Corr of the two teams' FD residuals | **0.43** [0.36] (bootstrap 0.10-0.67) | 0.24 | +0.19 [+0.12] | 0.28 [0.30] |
| (c) Both teams beat FD expectation | 21% [29%] | 28% | | |

By season, the strict flag's (a) runs +8.9, -19.0, +1.1, -8.3, 0.0, +1.2: no consistent sign.

**Your underdog question:** in flagged games the underdog beat its FanDuel expectation by +1.2, exactly what every other
underdog did (+1.25). There is a real underdog effect in general: at the same implied total, the lower-implied team
scores about 2.5 more FanDuel points than the higher-implied team (p = 0.003, positive in all six seasons). Trailing
teams pile up yards, and the real-point scores show no difference (+0.36 vs +0.41). It is not special to these games, and
the model's player projections already lean that way: by the team's line, history over-projects favourites' players
slightly more than underdogs', leaving about 0.5 points per team.

**Recommendation: no.** (a) and (b) show no edge: Vegas already prices these games 4.4 points higher, and the actual
totals land on the line. (c) points the right way (wider totals, the two offences more correlated), but with 28 games
neither difference is significant, and "both teams beat expectation" goes the other way. So no stack-weight bump. The
(c) case for more bring-backs isn't proven either: every stack already carries a bring-back, and these games already get
higher stack weights through their totals. Worth re-checking once 2026 adds a season (about 5 more games).

## 5. RB reds vs the RB gap (Doug, Nov 2, before week-9 colours)

RB points per lineup (field = ownership-weighted; ours = the as-entered 150 rebuilt). "Red RBs" = RBs on that week's red
list (week 5: the recorded-only shadow list). The re-run flips only the RB reds and leaves every other colour as entered.

| Week | Reds applied? | RB reds | Field RB pts | of which red RBs | Ours | Gap | Gap from red RBs | Gap from non-red RBs | RBs per lineup field / ours | Re-run without RB reds (wk 5: with) |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | No (shadow) | 2 | 50.4 | 3.1 | 31.1 | -19.4 | -3.1 | -16.3 | 2.63 / 2.23 | +0.1 a lineup, top-10% 3 vs 3 |
| 6 | Yes | 0 | 37.8 | 0.0 | 32.3 | -5.5 | 0.0 | -5.5 | 2.66 / 2.46 | no RB reds: unchanged |
| 7 | Yes | 47 | 40.3 | 1.6 | 30.0 | -10.3 | -1.6 | -8.7 | 2.53 / 2.14 | +2.2 a lineup; top-10% 14 vs 11; top-1% 1 vs 0; best 158.8 vs 151.4 |
| 8 | Yes | 55 | 43.3 | 10.4 | 30.6 | -12.6 | -10.4 | -2.3 | 2.66 / 2.21 | +1.0 a lineup; top-10% 11 vs 10; best 195.8 vs 190.4 |

(a) Weeks with RB reds applied (7-8) averaged a gap of -11.4; weeks without (5-6) -12.4. No difference.
(b) Over the four weeks the gap totals -47.8 points; red RBs account for -15.1 (-12.0 in the weeks they were applied),
non-red RBs -32.8. Week 8 is the exception: there the reds were most of it (Braelon Allen 25.3 at 25% owned, Warren
23.8, Coleman 18.4).

**Plainly: the RB reds are not what drives the gap.** It was largest in week 5, when no reds were applied. Most of it is
that we play fewer RBs (about 2.2 a lineup against the field's 2.6, the TE-flex issue in section 1) and the field's
RBs outscored ours. But the RB reds did cost points: removing them would have added 2.2 a lineup in week 7 and 1.0 in
week 8, and in week 8 the reds were 10.4 of the 12.6-point gap. Being lighter on RB reds looks worth it; it will not
close the gap on its own.
