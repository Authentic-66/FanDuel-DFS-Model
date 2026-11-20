# Top-1% lineup features, weeks 5-10 (Nov 20)

Analysis of which **pre-lock** lineup features raise the chance of a top-1% finish in the Pooch Punt, using every
field lineup in the weeks 5-10 All Entries exports (3.29M complete lineups), not just the top finishers. Doug's
decisions from it are at the end (two freeze exceptions, applied from week 11; two items queued for after week 12).

Scripts were scratch (session scratchpad `feat/`: build.py, lift.py, role_players.py, history_rb2.py), not in the
repo. Their method is described here so the numbers can be rebuilt.

## Method
- Rows = every complete field lineup per week; top 1% = rank <= 1% of `[contest] field_size`.
- **Lift** = top-1% rate of lineups with the feature / rate of lineups without it, per week; the pooled lift is the
  geometric mean of the six weekly lifts (each week counts the same). **Weeks up** = weeks with lift > 1 (of 6).
- **Joint** = a weighted logistic regression of top-1% on all the features at once with week fixed effects (all
  top-1% lineups + a 10% sample of the rest, weighted back), also fit per week; "joint weeks up" = weeks whose
  odds multiplier is above 1. Its z-statistics are NOT trustworthy: top-1% lineups cluster (one max-entrant lineup
  entered 150 times, a few players per week), so consistency across weeks is the test used, not significance.
- A distinct-lineup version (duplicates within a week dropped) gave similar lifts.
- Ownership = FanDuel's actual %Drafted (not known before lock; our Own_proj tracks the low-owned counts closely
  enough, see the decisions section).
- High-variance player = within position, players projected 5+, residual of log(sim sd) on log(projection) in the top
  quarter (from our sims.npy, so it is our model's notion of variance).
- Role-change player = same-position teammate of a team's #1 (RB by carries, WR / TE by targets per game this season;
  RB 8+, WR 5+, TE 3.5+) who missed the week after playing in one of the team's last two games, and whose volume share
  rose 15+ points or snap share 20+ points vs his last 3 games (post hoc: uses the actual game). Next-in-line = the
  teammate with the most prior volume (a pre-lock definition).

## Results (ranked by consistency)

| Feature | Field % | Top-1% lift | Weeks up | Joint, weeks up | Ours (entered, wks 5-10) |
|---|---|---|---|---|---|
| **RB in FLEX (= 3 RBs: identical)** | 66% | **2.35** | 5 | 6 | 35% |
| TE in FLEX | 14% | 0.47 | 1 | | 46% |
| WR in FLEX | 19% | 0.45 | 0 | | 18% |
| **QB + own RB** | 20% | **0.56** | **0** | 0 | 16% |
| **Naked QB** | 17% | **0.33** | 1 | 1 | 0% |
| **Salary left $600-1,000** | 5.6% | 0.77 | 1 | | 15% |
| **Salary left $1,100-2,000** | 1.7% | 0.55 | **0** | (per $1k: 2) | 5% |
| Salary left $2,100+ | 0.7% | 0.20 | 0 | | 5% |
| Salary left $0 / $100-500 | 44% / 48% | 0.97 / 1.14 | 2 / 4 | | 27% / 49% |
| 3+ players under 5% owned | 27% | 0.35 | 2 | (per player: 2) | **59%** |
| 1 player under 5% owned | 28% | 1.26 | 5 | | 13% |
| Chalk core (3+ at 20%+) + 1-2 under 5% | 34% | 1.29 | 4 | | 18% |
| 2+ high-variance players | 52% | 1.59 | 5 | 4 | 54% |
| RB + own-team DST | 19% | 1.29 | 4 | 4 | 9% |
| Bring-back | 45% | 1.51 | 5 | 3 (about 1.0) | 100% |
| 3+ / 4+ / 5+ players from one game | 65 / 26 / 5% | 1.66 / 1.60 / 1.22 | 4 / 3 / 3 | 3 (4+) | 99 / 99 / 14% |
| 0 / 1 / 2 / 3+ players 30%+ owned | 32 / 27 / 23 / 18% | no consistent sign (week 8 had none) | | | |
| Role-change player | 34% | 1.62 | 3 | 2 | 24% |
| Next-in-line player | 38% | 1.71 | 3 | | 36% |

Notes:
- **QB + own RB holds at a fixed stack size:** adding the QB's own RB lowered the top-1% rate in 6 of 6 weeks among
  QB + 2 lineups (lifts 0.57 / 0.82 / 0.62 / 0.07 / 0.18 / 0.40), and in 5 of 6 among QB + 1 and QB + 3+.
- Game stacks of 4+ won only in weeks 8 and 10 (one QB decided the slate); bring-back adds nothing once the QB + 2
  stack is counted; 30%+ chalk counts follow whether the chalk hit that week.
- Role-change / next-in-line lift is week 10 alone (Emmett Johnson: lift 67 that week) and week 5 (Braelon Allen).

## #5 Role-change players in detail (76 on the slate, weeks 5-10)
- Field ownership median 0.7%; the top 1% held them above their field ownership in only 20% of cases.
- Projected 4+ (47): projected 8.3, scored 7.2 (-1.0 vs our projection), 34% beat it. RBs (21): 9.1 / 8.5, median -2.5.
  "Share jumped" players projected 4+ (32, defined with hindsight): 8.0 / 7.8.
- Hits: Emmett Johnson +17.2 (50% owned, in 98.5% of top-1% lineups), Braelon Allen +15.0 (week 5, before the
  present-share fix), Tyrone Tracy +13.2, Ollie Gordon +8.4. Misses: Singletary -10.8 (29% owned), Allgeier -7.4 /
  -4.9 / -9.7 / -8.7, Adonai Mitchell -8.8, Godwin -8.5.
- Reading: coin flips we already project about right on average; not a feature to build toward.

## History 2021-2025: the team's #1 misses his first game of the season
Events from `history.absences` (first missed game, week 4+, played the 3 games before); the missing player must be his
team's #1 at the position; next man = the same-position teammate with the most volume in the games the #1 played.
Model = `usage.redistribute_out` with the live week-11 rules (routing by position, RB pro rata inside the position,
WR depth rank 20 / 20 / 60, bump_scale RB 0.8 / WR 0.45); points = the fit_depth.py sim recipe, calibrated.

**RB1 out (96 events):** RB1 14.4 carries a game; next man 4.7 -> 12.8.
- Share of RB1's carries the next man gained: actual **0.57** (median 0.58; quartiles 0.34 / 0.88), model **0.51**.
- Points: actual 12.1; model 11.9; no bump 6.4; with his true volume 13.0. RMSE 7.91 model, 10.04 no bump.
- True backups (next man under 35% of RB1's work, 50 events): 0.56 vs 0.47, points bias -0.7. Committee 0.60 vs 0.54
  (+0.4); co-lead 0.51 vs 0.59 (0.0).
- By season, actual / model / points bias: 2021 0.53 / 0.50 / -0.9; 2022 0.47 / 0.49 / +1.5; 2023 0.64 / 0.52 / +1.0;
  2024 0.56 / 0.54 / -0.4; **2025 0.65 / 0.48 / -2.0** (18 events: watch).
- Reading: right on average; the problem is the spread (whether the job goes to him), not the mean.

**WR1 out (87 events):** WR1 8.4 targets a game; next man 4.7 -> 6.5.
- Share of WR1's targets gained: actual **0.21** (median 0.17), model **0.07** (1.8 vs 0.6 targets a game).
- Points: actual 10.2, model 9.0 (-1.2), no bump 8.0, true volume 10.6. Model low in 4 of 5 seasons (2023 +0.4).
- True backups (16): 0.44 vs 0.07; committee (45) 0.18 vs 0.07, bias -1.8; co-lead (26) 0.11 vs 0.07.
- Cause: the depth-rank split gives the largest remaining WR 20% of the same-position bump, and bump_scale WR 0.45
  shrinks it again (bump_scale was fit on all moved players, where depth players were over-raised). Candidate fix
  after the freeze: exempt the rank-1 WR from bump_scale, or refit both together.

## What is real and fixable
1. **RB in FLEX:** real (5 / 6, joint 6 / 6). The weeks 11-12 entry (flex shadow) already leans this way.
2. **QB + own RB:** real and negative (0 / 6). The flex shadow counted every RB as a stack piece, so it held the QB's
   own RB in 87 of 150 week-11 lineups and 14 of the 20 entered. Fixed (decision 1).
3. **$600+ salary left:** real and negative. Our $59,000 floor allowed up to $1,000 left (15-25% of our lineups).
   Fixed (decision 2).
4. **3+ players under 5% owned:** probably real (lift 0.35; per extra player 0.87 jointly), but depends on ownership;
   our Own_proj counts track the actual ones (weeks 9-10 share of lineups with 3+: 61% vs 54%, 58% vs 70%).
   Queued (decision 4).
Not worth building: role-change chasing, 30%+ chalk counts, bigger game stacks, more bring-backs, RB + own DST.

## Decisions (Doug, Nov 20)
1. **Freeze exception, from week 11:** no lineup may hold the stacked QB with an RB from his own team, in the builds
   that count every RB as a stack piece (flex shadow = the entry build, median-70 v1). `[optimizer] no_qb_own_rb =
   "rb_pieces"` (defaults.toml; "off" | "rb_pieces" | "all"; weeks 4-10 pin "off"). RB-in-FLEX and the other flex
   rules unchanged. Evidence: QB + own RB lift 0.56, 0 of 6 weeks up. Named `[stacks] extra_receivers` RBs in the
   normal model are not affected (week 11 has none). weekly.py's rule check reports any QB + own RB in those sets.
2. **Freeze exception, from week 11:** `[optimizer] min_salary` 59,000 -> **59,500** for all sets (weeks 7-10 pin
   59,000). Evidence: $600-1,000 left lift 0.77 (1 / 6 up), $1,100-2,000 0.55 (0 / 6).
3. Week-11 Friday stage rerun (Nov 20, same lines and stats cache as Nov 19, so only the two rules differ; proj.csv
   unchanged):

   | | QB + own RB | $600+ left | FLEX RB | projection range (avg) |
   |---|---|---|---|---|
   | entry 20, Nov 19 | 14 | 2 | 20 | 121.7-127.3 (123.6) |
   | entry 20, Nov 20 | **0** | **0** | 15 | 120.5-126.5 (122.9) |
   | flex shadow 150, before / after | 87 / 0 | 27 / 0 | 94 / 77 | |
   | median-70 v1 150, before / after | 98 / 0 | 1 / 0 | 150 / 149 | |
   | model 150, before / after | 30 / 29 (rule not applied) | 33 / 0 | 76 / 75 | |

   Side effect: with the QB's own RB gone, NYJ, TB and ARI could no longer be stacked in the flex shadow (9 lineups
   reallocated), and FLEX RB in the 20 fell 20 -> 15 (part of the RB-in-FLEX came from the QB's own RB). All nine
   sets 150, 0 rule problems; 3 flex-shadow lineups used floor cap relief (to 27).
4. **Queued for after week 12:** (a) at most 2 players projected under 5% owned per lineup (lineup test: average,
   top-10%, top-1%, best, money); (b) WR1-out bump fix (history test as above, then lineup test).
5. **Queued for after week 12 (Doug, Nov 20): player floor, judged on CASH RATE** (about half the field cashes), not
   top 1%. (a) Weeks 5-12 field lineups: cash rate when the lowest-projected non-DST player is below vs at/above
   5 / 6 / 7 / 8 pts, and with 0 vs 1+ non-DST players whose sim 20th percentile is under 3. (b) Flex shadow 150 rebuilt
   with a per-player floor at the best threshold: cash rate, money, top 1% (plus top 10%, average, best) vs the current
   flex-shadow build. Analysis + lineup test only.
