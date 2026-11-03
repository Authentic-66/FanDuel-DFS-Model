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

## 6. RB / flex fix: diagnosis, RB sim calibration, candidate rules (Doug, Nov 2; nothing changed)

### 6.1 Diagnosis: what the FLEX TE is (the uploaded 150, weeks 5-8)

| Week | FLEX TE / RB / WR | Extra TE standalone | Extra TE is the bring-back | Both TEs needed for the stack | RB stack pieces | RB bring-back pieces |
|---|---|---|---|---|---|---|
| 5 | 68 / 35 / 47 | 48 | 20 | 0 | 16 | 59 |
| 6 | 47 / 69 / 34 | 34 | 13 | 0 | 17 | 55 |
| 7 | 117 / 21 / 12 | 77 | 40 | 0 | 43 | 40 |
| 8 | 95 / 32 / 23 | 70 | 25 | 0 | 22 | 59 |

(In a TE-flex lineup, "extra TE" = the less structural of the two: standalone before bring-back before stack piece.)
The stack rule (QB + 2 WR/TE + 1 opponent) counts an RB as a stack piece only if named in `[stacks] extra_receivers`
(the RB stack pieces above are those named RBs or RBs that happen to be on the QB's team). **The bring-back already
allows an RB**, and RBs were 37-39% of bring-back pieces. **No lineup needed two TEs for its stack.** 70% of extra TEs
(229 of 327) are standalone: the optimizer chose them on projection per salary over an RB. So the stack rule is not the
cause.

### 6.2 RB upside in the sims, 2021-2025 (weeks 4-18, with the week-9 calibration, WR correction and spread)

| Position | n | Beat sim p90 | Beat sim p95 | 95% noise band (p95) |
|---|---|---|---|---|
| RB | 3,365 | 10.1% | 5.4% | 4.3-5.7% |
| WR | 5,063 | 10.3% | 4.9% | 4.4-5.6% |
| TE | 1,698 | 9.8% | 4.9% | 4.0-6.0% |
| QB | 2,088 | 8.8% | 3.5% | |

By projection band RBs are slightly narrow below 12 (p95 7.3% at 0-8, 6.5% at 8-12; few of those make lineups) and too
wide at 12-16 (p95 2.7%), where our lineup RBs sit. By season, RB p95 ran 3.5-6.2%. **The sims do not understate RB upside
overall**, so (b) "widen RB variance" fails the history test and was not fitted or run; (c) likewise.

### 6.3 Lineup test, weeks 5-8 (points a lineup vs as entered; baseline reproduced all 150 each week)

Baseline: 108.33 / 103.97 / 100.90 / 106.26; top 10% 32; top 1% 1; money as-if $20.75 (week-7 tiers, ranks above
~9,900 counted at $0.25); RB gap (our RB points a lineup minus the field's) -19.4 / -5.5 / -10.3 / -12.6 (mean -11.9).

| Variant | Builds 150? | Wk 5 | Wk 6 | Wk 7 | Wk 8 | Mean | Top 10% | Top 1% | Money | RB gap mean | FLEX TE by week | Best by week |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (a1) any RB counts as a stack piece | all | +2.42 | -1.10 | -0.17 | -0.23 | +0.23 | 33 | 0 | $20.22 | -10.7 | 54 / 41 / 113 / 82 | 174.5 / 142.7 / 150.3 / 192.3 |
| (a2) bring-back must include an RB | wk 7 stops at 125 | +0.52 | -2.07 | fail | +1.06 | -0.16 (3 wks) | 30 vs 21 | 3 vs 1 | $13.87 vs $13.05 | | 53 / 33 / - / 74 | 181.9 / 156.6 / - / 200.4 |
| (d) TE flex only if top-3 by projection | wk 7 stops at 139 | +0.01 | +0.19 | fail | +0.90 | +0.37 (3 wks) | 18 vs 21 | 1 vs 1 | $14.03 vs $13.05 | | 40 / 37 / - / 62 | 180.8 / 158.4 / - / 190.4 |
| (d) top-5 by projection | wk 7 stops at 149 | -0.17 | -0.15 | fail | -0.53 | -0.28 (3 wks) | 19 vs 21 | 1 vs 1 | $13.05 vs $13.05 | | 53 / 43 / - / 80 | 180.8 / 158.4 / - / 190.4 |
| (d) top-8 by projection | all | +0.11 | -0.29 | +0.19 | -0.38 | -0.09 | 35 | 1 | $20.71 | -12.0 | 64 / 45 / 112 / 94 | 184.9 / 158.4 / 155.7 / 190.4 |
| (d) top-5 by salary | wk 7 stops at 149 | -0.24 | +0.08 | fail | +0.96 | +0.27 (3 wks) | 19 vs 21 | 1 vs 1 | $13.55 vs $13.05 | | 52 / 40 / - / 80 | 180.8 / 158.4 / - / 190.4 |
| (a1) + top-3 by projection | wk 7 stops at 140 | +2.83 | -1.03 | fail | +0.36 | +0.72 (3 wks) | 20 vs 21 | 0 vs 1 | $13.80 vs $13.05 | | 38 / 31 / - / 54 | 174.5 / 142.7 / - / 192.3 |
| (a1) + top-8 by projection | all | +2.59 | -1.07 | +0.06 | -0.14 | +0.36 | 32 | 0 | $20.10 | -10.5 | 50 / 40 / 106 / 82 | 174.5 / 142.7 / 150.3 / 192.3 |
| (a1) + top-5 by salary | all | +2.50 | -0.97 | +1.32 | +0.11 | **+0.74** | 30 | 0 | $21.01 | -10.1 | 45 / 32 / 96 / 69 | 174.5 / 142.7 / 150.5 / 192.3 |

"3 wks" rows compare with the baseline's weeks 5, 6 and 8 only. (a1) is the only (a) rule that builds every week, so it
is the one combined with (d). (a1) also makes top-5 by salary buildable in week 7 (more teams can be stacked).

### 6.4 Recommendation: no change for week 9

- **Cause:** not the stack rule (no lineup needs two TEs; RB bring-backs are already allowed and used) and not RB sim
  width (RBs beat p90/p95 at 10.1% / 5.4%, the same as WRs and TEs). The FLEX TE is a value pick: cheap TEs project
  well per dollar, and the projection error found in test 1 (TEs 12+ over-projected) is small next to that.
- **No candidate passes your rule 4.** Lineup rules cannot be tested in history (no FanDuel salaries before 2026), so
  the bar is "does not hurt weeks 5-8". Every rule hurts at least one week, fails to build week 7, or both. The best
  average, (a1) + top-5 TEs by salary (+0.74, money +$0.26, all weeks build), gets almost all of it from week 5 (+2.5),
  costs about a point in week 6 and loses the only top-1% lineup (week 6's 158.4; (a1) causes that in every
  combination). Top-8 by projection builds every week but barely binds (flex TE 64 / 45 / 112 / 94 against 68 / 47 /
  117 / 95) and is neutral (-0.09).
- If you want something on trial, (a1) + top-5 by salary is the one to watch, as a shadow build alongside the real
  one for weeks 9-10 rather than a live change.
- **The bigger RB lever is still the RB reds** (section 5: removing them was +2.2 in week 7 and +1.0 in week 8).

## 7. Flex TEs vs the RBs passed over, and TE calibration by tier (Doug, Nov 2)

### 7.1 Weeks 5-8: the FLEX TE vs the best RB the optimizer passed over

For each of the 327 uploaded TE-flex lineups: the extra TE (as in 6.1) against the highest-projected eligible-pool RB
that fit the slot (salary within the TE's salary plus unused cap, not already in the lineup, max 4 per team, not facing
the lineup's DST; exposure caps ignored, so a capped RB still counts as passed over). No RB fit in 67 lineups (53 in
week 8, mostly reds).

| | Lineups | TE proj | TE actual | RB found | RB proj | RB actual | TE minus RB (actual) | RB outscored TE |
|---|---|---|---|---|---|---|---|---|
| Week 5 | 68 | 12.4 | 12.2 | 60 | 21.1 | 18.5 | -5.7 | 60% |
| Week 6 | 47 | 13.6 | 10.0 | 46 | 16.1 | 12.8 | -2.6 | 54% |
| Week 7 | 117 | 10.8 | 7.2 | 112 | 12.3 | 2.9 | +4.4 | 18% |
| Week 8 | 95 | 11.3 | 10.2 | 42 | 15.3 | 13.1 | +2.1 | 38% |
| **All** | 327 | 11.7 | 9.5 | 260 | 15.5 | 9.9 | **+0.4** | 37% |
| TE projected under 8 | 59 | 7.1 | 6.5 | 37 | 12.5 | 3.3 | +3.4 | 19% |
| TE 8-10 | 50 | 9.2 | 8.3 | 18 | 17.5 | 13.3 | -4.9 | 61% |
| TE 10-12 | 100 | 10.9 | 4.8 | 87 | 13.0 | 6.2 | -0.9 | 38% |
| TE 12+ | 118 | 15.6 | 15.5 | 118 | 17.9 | 14.2 | +1.3 | 39% |

The flex TEs fell 2.2 short of projection, but the RBs passed over fell 5.6 short, so swapping the TE for the
best-projected RB would have lost 0.4 points per lineup overall. Week 7 dominates: Pierre Strong Jr. was the passed-over RB in 62
lineups and scored 0. The weak spot is the 10-12 tier (4.8 on 10.9), and it is a few players: Likely (23 lineups, 2.2)
and Higbee (18, 2.4) in week 7. The 12+ TEs (Bowers, McBride) scored to projection.

All TEs in the weeks 5-8 projections by tier (proj minus actual): under 8 +0.6 (n 147), 8-10 +1.2 (20), 10-12 +5.3 (12,
standard error 1.6), 12+ +0.9 (13). Too few to fit on.

### 7.2 2021-2025: TE calibration by projection tier (week-9 settings)

| Tier | n | Proj | Actual | Bias (proj - actual) | Std error | Seasons over-projected | Beat p90 / p95 |
|---|---|---|---|---|---|---|---|
| Under 8 | 941 | 6.13 | 6.24 | -0.11 | 0.18 | 2 of 5 | 11% / 6% |
| 8-10 | 394 | 8.90 | 8.37 | +0.54 | 0.30 | 5 of 5 (0.08 to 1.29) | 9% / 4% |
| 10-12 | 196 | 10.87 | 11.07 | -0.20 | 0.55 | 2 of 5 | 11% / 6% |
| 12+ | 167 | 14.43 | 11.84 | +2.58 | 0.61 | 5 of 5 (3.1 / 3.2 / 3.8 / 1.1 / 0.7) | 6% / 2% |

Corrections fitted leave-one-season-out (TE loses s of each projected point above a knee):

| Correction | s (folds) | RMSE (6.222 now) | Bias (+0.30 now) | Under 8 | 8-10 | 10-12 | 12+ |
|---|---|---|---|---|---|---|---|
| knee 8 | 0.36 (0.32-0.39) | 6.166 | -0.12 | -0.11 | +0.21 | -1.24 | +0.35 |
| knee 9 | 0.45 (0.40-0.48) | 6.162 | -0.06 | -0.11 | +0.45 | -1.05 | +0.21 |
| knee 10 (test 1) | 0.58 (0.52-0.61) | 6.158 | -0.01 | -0.11 | +0.54 | -0.71 | +0.10 |
| flat -0.8 for 8+ | 0.64-0.98 | 6.203 | -0.06 | -0.11 | -0.28 | -1.01 | +1.79 |

**Low and mid-tier TEs are not meaningfully over-projected in history:** under 8 -0.1, 10-12 -0.2; 8-10 is +0.5 (about
two standard errors). Every correction that fixes 8-10 pushes 10-12 to -1.0 or worse. The over-projection is the 12+
tier, and it has shrunk (+0.7 to +1.1 in 2024-25). The knee-10 slope that fixes it is the test-1 candidate (-0.6 a lineup in weeks 5-8).
**No mid/low-tier fix proposed.**

### 7.3 Flex shadow build, weeks 9-10 (Doug, Nov 2)

`optimize.py --week 2026-w09 --flex-shadow` builds 150 with every RB counted as a stack piece and a TE in the FLEX only if
he is a top-5 TE by salary (`[optimizer] rb_stack_pieces`, `flex_te_top_salary`, both off by default) into
`weeks/2026-w09/flex_shadow/`. Not entered. Add `[grading] extra_sets = ["flex_shadow"]` (plus any control set) to the
week's week.toml so Monday's grading reports it beside the entered set. Checked: with the switches off, weeks 5-8
rebuild the uploaded 150 exactly. With them on, weeks 5-8 give 110.83 / 103.00 / 102.22 / 106.37, matching the section 6 test.

## 8. Ownership as a market signal (Doug, Nov 2; nothing changed)

Benter's idea: the public's odds hold information the model lacks, so blend the two. Here the "odds" are ownership.
Rows: weeks 5-8, every slate player with a result and an as-entered projection of 4+ (660 player-weeks; 42 games).
Residual = actual FanDuel points minus our as-entered projection. Standard errors are clustered by game (players in
one game move together), so the effective sample is about 42, not 660. Scratch scripts: own_signal.py, own_lineups.py.

**8.1 Do popular players beat our projection? Yes.** Controlling for position, log salary, week and our projection,
residual on log(actual ownership): **+1.42 per log unit (se 0.31, p < 0.001), about +1.0 point per doubling of
ownership.** Positive every week (+1.69 / +1.55 / +1.37 / +1.11; p 0.01 / 0.001 / 0.04 / 0.25). Without the
projection control it is +0.38 (p 0.11): highly owned players are also our high projections, which run hot, so the
two pull against each other. Players who scored 0 left out: +1.15 (p 0.001); ownership in % instead of log: +0.20 per
point (p 0.005). By position: QB +3.5 (p < 0.001), RB +2.1 (p 0.005), DST +1.6 (p 0.13), WR +0.7 (p 0.12), TE +0.1.
So the field knows something we don't, mostly about QBs and RBs.

**8.2 (a) Can we predict that ownership before lock? Not the part that matters.** Projected-ownership ridge on
logit(%Drafted), leave-one-week-out on weeks 5-8 (rows projected 2+):

| model | MAE (pts) | log-r | players 15%+ owned: actual vs predicted |
|---|---:|---:|---|
| as entered (trained on earlier weeks) | 2.66 | 0.869 | 25.2 vs 14.9 |
| current features, LOWO | 2.63 | 0.861 | 25.2 vs 16.5 |
| + injury/role news (routing bump, Q tag), position-specific salary / projection / value slopes | 2.60 | 0.871 | 25.2 vs 17.7 |

The new inputs help a little (the chalk shortfall 10.3 -> 7.5 points) but the error on chalk stays about 13 points.
The decisive test: residual on log(**projected** ownership, out of week) = **-0.39 (se 1.15, p 0.74): nothing.**
With both in, the "surprise" (actual minus projected, log) carries it all: +1.74 (p < 0.001), projected -1.42 (p 0.23).
A model built from our own inputs (salary, our projection, Vegas, news we already have) can only re-weight those
inputs; the field's edge is information outside them (late news, other people's projections, Guru).

**8.3 (b) Blended projection, nested leave-one-week-out** (the held-out week is never used to fit, and each training
week's projected ownership is itself out of week). A = recalibration only (residual on position, our projection, log
salary); B = A + log(projected ownership) = the blend; C = A + log(actual ownership) = the ceiling, NOT available
before lock.

| held out, Proj 4+ | RMSE | bias (proj - actual) | r |
|---|---:|---:|---:|
| ours as entered | 7.408 | +1.09 | 0.493 |
| A recalibration only | 7.239 | +0.02 | 0.501 |
| **B blend (projected ownership)** | **7.281** | -0.06 | 0.493 |
| C ceiling (actual ownership) | 7.077 | +0.01 | 0.533 |

B is worse than A (squared error +0.60 a player, t -2.6 over 42 games); its ownership coefficient flips sign by
held-out week (+1.22, -1.66, -0.08, -0.36). Lineups (as-entered rebuild with each player's projection and draws moved
by the held-out delta; players under 4 untouched; base = the entered 150 in every week):

| | avg wk 5 / 6 / 7 / 8 | mean | top 10% | top 1% | best wk 5 / 6 / 7 / 8 | money as-if |
|---|---|---:|---:|---:|---|---:|
| as entered | 108.33 / 103.97 / 100.90 / 106.26 | 104.87 | 32 | 1 | 184.9 / 158.4 / 151.4 / 190.4 | $20.75 |
| A recalibration | 108.11 / 103.05 / 100.94 / 107.43 | 104.88 | 34 | 0 | 168.0 / 151.4 / 152.4 / 190.4 | $19.11 |
| **B blend** | 106.61 / 100.34 / 100.96 / 107.23 | **103.79** | 34 | 0 | 160.7 / 145.3 / 152.4 / 190.4 | $18.28 |
| C ceiling | 112.31 / 104.21 / 102.37 / 113.08 | 107.99 | 38 | 4 | 184.6 / 153.2 / 164.1 / 219.9 | $24.52 |

**Verdict: no blend.** The signal is real and worth about +3 points a lineup and 3 extra top-1% finishes over four
weeks *if* we had the field's ownership before lock (C), but a projected-ownership model from our inputs adds nothing
and the blend costs 1.1 points a lineup. On significance: 8.1 is solid (p < 0.001, same sign every week); 8.3's B-vs-A
loss is t -2.6 on four held-out weeks; C is an upper bound, not a result. The route to the signal is an **outside
pre-lock ownership projection** (a public ownership projection, or the full Guru lists each week) as the "public
odds" input: that is what would let a Benter-style blend work. By-product: A (salary-aware recalibration) removes the
+1.1 bias at no lineup cost (avg 104.88 vs 104.87, top 1% 1 -> 0); the week-9 model already lowers WR and bumped
projections (sections 2-3), so A is not proposed as is.

## 9. Cheap DSTs: under-projected, or luck? (Doug, Nov 2; nothing changed)

**Live, weeks 5-8 (84 DST-weeks), as-entered projection vs actual by salary** (scratch: dst_cal.py):

| salary | n | opp implied | own % | proj | actual | actual - proj (se) | pts / $1k |
|---|---:|---:|---:|---:|---:|---|---:|
| < $3.8k | 33 | 25.0 | 5.8 | 4.85 | 5.94 | **+1.09 (1.10)** | 1.78 |
| $3.8-4.2k | 20 | 22.8 | 3.3 | 5.92 | 5.90 | -0.02 (1.43) | 1.48 |
| $4.3-4.7k | 20 | 20.8 | 3.9 | 7.06 | 6.85 | -0.21 (1.22) | 1.52 |
| $4.8k+ | 11 | 17.6 | 5.9 | 8.15 | 8.09 | -0.06 (1.75) | 1.65 |

Cheap DSTs beat their projection by +1.1, within one standard error; by week -0.5 / +3.4 / +2.4 / -0.7 (adding week 4:
+0.6, se 0.9). Salary adds nothing beyond the opponent's implied total (-0.66 per $1k, se 1.47; the model uses
+0.35); the opponent term fits -0.42 (se 0.24; model -0.35).

**History 2021-2025 (2,238 team-games, weeks 4-18; no FanDuel salaries, so by projection = the live opponent term
around a level from the other seasons):** the lowest quintile (weakest matchups, the cheap end) projected 4.54 and
scored 4.26 (-0.28, se 0.23); the top quintile +0.30. Low-projected DSTs are, if anything, slightly over-projected,
and they have less upside (15+ points in 4.5% of games vs 16.1% for the top quintile). The opponent slope refits to
-0.40 to -0.47 by season (live -0.35): the formula is a touch flat, which also points away from "cheap DSTs are
under-projected".

**Verdict: the field got lucky with cheap DSTs in weeks 6-7; they are not under-projected.** We had few of them in
weeks 7-8 because of the reds, not the model: 3 of 8 cheap DSTs were red in week 7 (incl. TEN, 34% owned), 7 of 8 in
week 8 (incl. DET, 21%). In weeks 5-6, with no DST reds, the model used a cheap DST in 36% / 32% of lineups (field
44-48%). The reds were right on DST points (red DSTs 2.5 vs 5.6 for the rest in week 7, 6.0 vs 7.7 in week 8). The
winners' cheap DSTs mattered for the salary they freed for RBs (learn_from_winners.md), which is the RB/flex question
again. Possible small cleanup, not proposed: the +0.35 per $1k salary term has no support live and no history to
test it on.

## 10. Cap for week 9: swap roles (cap 45 entered, cap 25 control)? (Doug, Nov 2)

Nothing technical blocks it: `--cap` works for the model, `--pool` and `--flex-shadow` runs. The week-9 setup would be
`[optimizer] exposure_cap = 45` in `config/2026-w09/week.toml` (defaults.toml stays 25; salary-floor relief goes to
47), control `optimize.py --week 2026-w09 --subdir model_cap25 --cap 25`, and `[grading] extra_sets =
["model_cap25", "flex_shadow"]`. Week 4 cannot be rebuilt (its draws were never archived), so weeks 5-8 only
(scratch: cap_compare.py; weeks 5-6 cap-45 sets are the scratch builds from learn_from_winners.md):

| cap 45 minus cap 25 | wk 5 | wk 6 | wk 7 | wk 8 | mean |
|---|---:|---:|---:|---:|---:|
| average | +5.5 | +1.9 | -2.9 | +1.2 | **+1.4** |
| top-10% lineups | +2 | +2 | -3 | +3 | +1.0 a week |
| top-1% lineups | 0 | -1 | +1 | 0 | 0 |
| best lineup | -4.0 | -6.0 | +6.4 | +0.3 | -0.8 |
| money as-if (week-7 tiers) | +$1.01 | +$0.54 | -$1.23 | +$0.39 | +$0.18 a week |
| bottom 10% (p10) | -0.8 | +2.0 | -4.8 | -0.3 | -1.0 |

What argues against it (none decisive):
1. **Thin evidence.** The +1.4 is mostly week 5 (+5.5); without it +0.1. Top-1% finishes are level and the best
   lineup was worse in two of four weeks. The week-6 prep cap test (older model, model-only) had week 4 the other
   way: 105.1 at cap 25 vs 103.1 at 40.
2. **It doesn't fix what the study found.** Cap 45 adds more to the chalk that missed than to the chalk that hit
   (learn_from_winners.md section 4), and leaves the RB, TE-flex and DST gaps unchanged.
3. **More concentration, the risk 25 was set for.** 7-16 players in 30+ lineups (at cap 25 only floor relief goes
   past 25), max 40-48; the bottom 10% of lineups was 1.0 lower; one dud costs more (Flowers 0.0 in week 8: 31 lineups
   vs 27). Overlap between lineups +0.2 players. Duplication with the field stays negligible at both caps (0-6 of
   150 lineups identical to another entry).
4. **Knock-on for the shadows.** The pool (players and fillers) and the flex shadow read `exposure_cap`: at 45 they
   are built at 45 unless run with `--cap 25`. Suggest building both at the entered cap, so each still answers "better
   than what we entered?"; the pool review after week 9 then compares a cap-45 pool (as in week 7).

In favour: both caps keep being measured, so the swap costs no information; cap 45 never stalled (25 needed 27 in
week 7); money +$0.18 a week. **My read: fine to swap for weeks 9-10 as a measured trial, not as a finding.** A
middle cap (e.g. 35) is untested.
