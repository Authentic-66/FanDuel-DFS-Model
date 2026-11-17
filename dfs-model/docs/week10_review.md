# Week 10 review + diagnosis (Nov 16, 2026)

Export `data/2026-w10/raw/136490-281478302.csv` (converted with `convert_results.py --user gst1999`; `[contest]
field_size = 515200`). Exact ranks and money against every entry with `data/2026-w10/prizes_pooch-punt.csv`. All
rebuilds in a scratch copy (each archived model set weeks 5-8 and 10 re-built 150/150 identical first); nothing in
`weeks/` rewritten. Scripts: `weeks/2026-w10/review_scripts/`. The grader reproduces actual winnings exactly (week 10
$3.53, week 9 $5.03, week 7 $8.08).

Field: 515,200 entries, **mean 146.4**, median 146.9, cash line 154.2 (rank 215,100), top 10% 188.9, top 1% 222.9,
winner 265.46 (Purdy / CMC / Hubbard / E. Johnson / P. Washington / Pickens / Deebo / Schultz / Rams).

## 1. Entries and money
All 150 export entries match `edit_entries_149.csv` by entry Id (149 edited model + free entry 3767370153). **Won
$3.53, all of it on the 149** (31 cashed, avg 124.2, best 220.0, rank 6,457). Free entry (Lawrence / Cook / Taylor /
Hubbard / P. Washington / K. Allen / Boston / Warren / JAC): 141.3, rank 290,225, $0. **Week 10 net -$3.92; running
total -$12.87** (weeks 4-10: +2.35, -4.74, -1.49, +0.23, -2.88, -2.42, -3.92).

## 2. Every set (as if entered) — `grade_all_sets.csv`
| Set | Avg | Cash % | Won | Net | Top 10% | Top 1% | Best |
|---|---|---|---|---|---|---|---|
| **Entered 149 (edited)** | 124.2 | 20.8 | 3.53 | -3.92 | 11 | 0 | 220.0 |
| First upload 149 | 119.2 | 12.8 | 2.00 | -5.45 | 3 | 0 | 196.3 |
| Model 150 | 124.2 | 20.7 | 3.53 | -3.97 | 11 | 0 | 220.0 |
| No-draw | 126.3 | 21.3 | 3.35 | -4.15 | 3 | 0 | 204.2 |
| Median-70 (30% injury cap) | 127.4 | 20.7 | 3.42 | -4.08 | 6 | 0 | 219.5 |
| Median-70 plain | 142.5 | 30.0 | 4.90 | -2.60 | 9 | 0 | 219.5 |
| v1 flex | 140.8 | 30.7 | 5.04 | -2.46 | 9 | 0 | 219.5 |
| v2 stack | 136.8 | 25.3 | 3.82 | -3.68 | 0 | 0 | 187.9 |
| v3 repeats | 153.6 | 43.3 | 7.24 | -0.26 | 16 | 0 | 219.5 |
| Cap-45 | 132.5 | 25.3 | 4.66 | -2.84 | 14 | 0 | 222.5 |
| Pool | 125.5 | 19.3 | 3.95 | -3.55 | 10 | 1 | 223.1 |
| Flex shadow | 124.4 | 19.3 | 3.47 | -4.03 | 7 | 0 | 220.7 |

Every set lost. The 30% injury cap cost median-70 15 points a lineup (Emmett Johnson 105 -> capped).
**Sunday calls (149 each, rebuilt one at a time):** Emmett Johnson un-red alone = **+$1.53** (+5.0 a lineup, 11 vs 3
top-10%; he scored 35.1, 50% owned, in 26 of 149). Etienne cap 8 alone = +$0.08 (Etienne 4.9); with E. Johnson
un-red it adds nothing. Together +$1.53: the edit was worth doing.

## 3. Low scores — `low_lineups.csv`, `sub3_rates_w05_w10.csv`
43 of 149 under 100 (2 under 60, low 50.9); 37 of them hold a player under 3 points (62 player-slots). **Nothing
operational:** every entered player took offensive snaps (no inactive missed), and the edit file wrote exactly the
lineups built. Causes: Bowers 2.8 in 16 lineups (19% of snaps, avg 86%: left early); the rest played normal snaps and
had bad games: Vele 2.4 (10), Coker 0.3 (8), Warren 1.4 (6), Kraft 2.4 (5), Shaheed 1.3 (5), Allgeier 1.4 (4),
Tucker 1.4 (4), Worthy 0.0 (2), Boston 2.1 (1); one DST.
Lineups holding a non-DST player under 3 (%): field / top 10% / top 1% / ours: wk5 61 / 33 / 20 / 69; wk6 42 / 15 / 5 /
59; wk7 80 / 52 / 35 / 84; wk8 73 / 42 / 22 / 76; wk9 43 / 29 / 21 / 47; wk10 62 / 48 / 41 / 63. **Ours is above the
field every week (avg 66% vs 60%), but only by 1-17 points;** the top 10% has fewer duds by definition (duds keep you out).
The low scores are not the main problem; the average is (below).

## 4. Projections vs construction — `fdr_accuracy_w09_w10.csv`, `fdr_builds_w09_w10.csv`
FDR = Friday file (no Sunday file either week; it misses Sunday news such as E. Johnson, FDR 4.7). 297 players (active,
both sources, either projects 4+):

| | Ours (Sun) | Ours (Fri) | FDR (Fri) | 50/50 blend | FanDuel FPPG |
|---|---|---|---|---|---|
| MAE | 5.52 | 5.84 | 5.35 | 5.37 | 5.34 |
| Rank corr. | 0.545 | 0.539 | 0.541 | 0.560 | 0.530 |
| Bias | +0.70 | +0.57 | -0.12 | +0.29 | +0.19 |

By position: RB ours MAE 5.78 / bias +1.5 vs FDR 5.21 / +0.2 (rank corr 0.56 vs 0.59); TE ours bias +1.7; WR ours
best (rank corr 0.41 vs 0.35); QB about even. Residual slope on (FDR - ours) 0.40 (QB 0.79, n 38). **All three,
including the season average, are within noise of each other: no edge and no deficit.**
Lineups rebuilt with our optimizer and rules (150 each):

| Build | Wk 9 avg / net | Wk 10 avg / net | Total net | Top 10% | Top 1% |
|---|---|---|---|---|---|
| Ours (model) | 108.7 / -0.10 | 124.2 / -3.97 | **-4.07** | 21 | 3 |
| FDR projections | 107.0 / -0.85 | 122.3 / -5.38 | -6.23 | 13 | 1 |
| 50/50 blend | 108.9 / -0.45 | 126.3 / -3.83 | -4.28 | 13 | 1 |

**Our projections are not the problem.** Construction is: the model 150's average was below the field's average
lineup **every week**: wk5 108.3 vs 130.5, wk6 104.0 vs 110.3, wk7 100.9 vs 102.8, wk8 106.3 vs 119.6, wk9 108.7 vs
113.1, wk10 124.2 vs 146.4 (49-81% of our lineups under the field median). FDR's projections in our builder were
just as far behind (122 vs 146). The rules (cap 25, starters-only, QB + 2 + bring-back, ~90 reds) keep us off the
chalk; when the chalk hits (weeks 5, 10: E. Johnson 50% / 35 pts) we lose 20+ points a lineup.

## 5. Reds and promotion — `red_split.csv`
Doug's sheet notes (each group made eligible alone, 149 rebuilt): **matchup** (Ward 20.1, Dotson 7.8, Ayomanor
10.4; proj 7.4 / actual 12.8): reds cost $0.06 (+1.2 a lineup if eligible). **Role / news** (Wentz; Strong inactive):
no effect. **"No interest"** (12 active; proj 6.2 / actual 3.9; Hutchinson 13.8, Tyson 13.5 hit, K. Coleman 1.6,
Shedeur 0): reds cost $0.52. **No note** (64 active; 3.6 / 2.4; Omar Cooper 0.0 would have been in 15): reds saved
$0.40. All reds together saved $0.35 (+2.0 a lineup). Note: CLE started Deshaun Watson (25.4, 100% snaps); Shedeur
didn't play (both red).
**Promotion kill rule:** week 10 promoted 4+: Dulin 5.6 / 3.5, Mumpfield 5.1 / 9.6, Atwell 5.1 / 3.6, Burks 4.6 / 0.0,
Bartholomew 4.5 / 11.1, Knox 4.1 / 1.2 = 4.83 proj / 4.83 actual. **Weeks 9-10: n 9, 0.74 under a player: under the
1.5 trigger. Promotion stays ON.**

## 6. Twenty lineups — `top20_w05_w10.csv`
Each build's 20 highest-projected lineups (median builds: by median), as if entered ($1.00 a week, week-9 prize table
for weeks 5-8). No-draw can't build week 7; pool from week 7; FDR / blend weeks 9-10 only.

| Build (weeks) | Avg | Cashed | Net | Profit weeks | Top 10% | Top 1% |
|---|---|---|---|---|---|---|
| **Flex shadow (6)** | 120.8 | 50 / 120 | **-$0.28** | 3 | 14 | 0 |
| Cap-45 (6) | 118.8 | 50 | -$0.41 | 2 | 10 | 0 |
| Model (6) | 118.2 | 50 | -$0.54 | 2 | 10 | 0 |
| v2 stack (6) | 118.0 | 52 | -$0.64 | 3 | 6 | 0 |
| v1 flex (6) | 117.4 | 46 | -$1.21 | 3 | 7 | 0 |
| Median-70 (6) | 114.9 | 42 | -$1.59 | 2 | 3 | 0 |
| No-draw (5) | 125.6 | 39 / 100 | -$0.73 | 2 | 8 | 0 |
| Pool (4) | 119.5 | 26 / 80 | -$0.31 | 2 | 13 | 1 |

None made money over six weeks ($6 in fees). The gaps (under $1.40) are smaller than one week's swing (+/-$1). Every
build's top 20 did better per lineup than its full 150 (model -$0.54 vs -$1.67 per 20).
