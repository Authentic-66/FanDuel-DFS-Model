# Max-entrants' NFL lineups vs ours (Doug, Nov 6 2026; analysis only, NFL only, nothing changed)

Why: in `docs/top_finishers.md`, users who enter the max (150) returned 1.43 per $1 in the Pooch Punt (weeks 5-8)
vs the field's 1.26 and ours 0.73. What do their lineups look like next to ours?

**Data.** Weeks 5-8 Pooch Punt full exports (field ~550-570k full lineups a week; max-entrants ~265-276k lineups
from ~1,800 users a week; their top-1% lineups 2,700-4,100 a week). Ours: Doug as entered (149 model + the free
entry) and four builds re-scored on each week's ACTUAL ownership: **model** (`weeks/<week>/upload.csv`), **no-draw**,
**median-70** and **cap 45**, rebuilt from the archived inputs into the session scratchpad (`optimize.py --subdir
<scratch>`; nothing in `weeks/` written). Checks: the rebuilt model matched the archived upload 150 of 150 in weeks
5, 6, 7 and 8; the rebuilt cap 45 matched the archived week 7-8 controls 150 of 150. **No-draw can't build week 7**
(stalls at lineup 150 at cap 27: no stack team left; same as the Nov 3 cash-build study), so no-draw averages weeks
5, 6 and 8.

**Metrics** (same definitions as `learn_from_winners.py`): salary by position, average and total ownership (FanDuel
%Drafted), chalk = players over 20% owned, RBs, FLEX position, stack shape (QB teammates, QB + 2, bring-back,
naked QB), and portfolio shape for a 150-lineup set: distinct lineups (repeats), top player exposure, players used,
average overlap with the nearest other lineup (players shared, of 9). **Similarity** = mean |gap| to the
max-entrants over the lineup metrics, each gap in units of the field's per-lineup SD (portfolio: SD across
max-entrant users); lower = more like them. Script: `python src/max_entrants.py --builds <scratch folder>`.

## Findings

**Which of our builds looks most like theirs: median-70, every week, on every measure.** Weeks 5-8 average gap
(lineups / vs their top-1% lineups / portfolio): **median-70 0.52 / 0.59 / 0.44**, no-draw 0.73 / 0.84 / 0.86,
cap 45 0.76 / 0.82 / 0.90, model 0.83 / 0.89 / 1.01, Doug as entered 0.81 / 0.88 / 1.01 (= the model). In every
week median-70 is the closest and the model (and Doug's entry, which is the model) the furthest or tied (week 8:
no-draw = model on lineups); no-draw and cap 45 swap places in between. Looking like them is not proof it pays: the cash-build
study had median-70 +21.5 / +6.9 / **-15.4** / +7.3 a lineup vs the model in weeks 5-8.

Weeks 5-8, max-entrants vs our model (median-70 in brackets):

| | Max-entrants | Their top-1% | Our model | (median-70) |
|---|---|---|---|---|
| Average player ownership | 17.7% | 17.4% | 11.1% | (15.6%) |
| Chalk players (>20% owned) per lineup | 3.5 | 3.3 | 1.5 | (2.8) |
| RBs per lineup | 2.7 | 2.8 | 2.3 | (2.5) |
| RB in the FLEX | 72% | 84% | 26% | (46%) |
| TE in the FLEX | 14% | 7% | 55% | (46%) |
| TE salary | $6,800 | $6,420 | $8,950 | ($8,420) |
| DST salary | $3,750 | $3,735 | $4,300 | ($4,015) |
| RB salary | $20,150 | $20,760 | $16,810 | ($18,350) |
| QB + 2 teammates | 43% | 50% | 100% (rule) | (100%) |
| Bring-back | 55% | 60% | 100% (rule) | (100%) |
| Naked QB | 11% | 11% | 0% (rule) | (0%) |
| Distinct lineups per 150 | 106 | | 150 | (150) |
| Top player exposure | 66% | | 18% | (70%) |
| Players used across 150 | 68 | | 105 | (91) |
| Overlap with nearest lineup (of 9) | 6.3 | | 5.2 | (6.9) |

1. **Ownership and chalk: they play the chalk, we fade it.** Max-entrants average 17.7% owned and 3.5 chalk players
   a lineup (slightly above the field's 16.8% / 3.2); our model 11.1% and 1.5. Median-70 closes most of it (15.6% / 2.8).
2. **RB in the FLEX is the biggest structural gap.** 72% of their lineups (84% of their top-1%) put an RB in the
   FLEX; ours 26% (TE 55%). Their RB salary is $3,300 higher, TE $2,150 lower, DST $550 lower. Same as the
   learn-from-winners finding, now also true of the max-entrants as a group.
3. **Stack shape: our rule, not theirs.** Only 43% of their lineups are QB + 2 and 55% have a bring-back (top-1%:
   50% / 60%); 11% are naked QBs. Every one of ours is QB + 2 + bring-back (Doug's standing rule), so no build can
   move on this. Their top-1% leans slightly towards our shape.
4. **Portfolio: concentrated, with repeats.** A max-entrant's 150 holds 106 distinct lineups (30% are repeats),
   uses 68 players, puts one player in 66% of lineups and shares 6.3 of 9 players with its nearest lineup. Our model:
   150 distinct, 105 players, top exposure 18% (cap 25), overlap 5.2. Median-70 (cap 105, overlap 7) is the only
   build near them (70%, 91 players, 6.9); cap 45 (30%) and no-draw sit in between on some measures.
5. **Salary:** they spend $59,800 (field level); our model $59,340, $465 less (weeks 5-6 had no salary floor);
   median-70 spends $59,890.

**Takeaway (Doug decides; nothing changed):** the entered week-9 set (75 median-70 + 74 model, Doug, Nov 3) already
moves half the entry towards the max-entrants' shape. The gaps no current build closes are RB-in-FLEX (best 46% vs
72%), the stack rule (100% QB + 2 + bring-back vs 43-55%) and lineup repeats. Each would be its own test with
average / top-10% / top-1% / best per week before any change.

**Caveats:** this compares shape, not skill; max-entrants are a mix (the top-1% lineups are the better guide);
duplicated lineups count once per entry; builds are re-scored on actual ownership, which they couldn't see.

## Tables (script output)

## 2026-w05

Lineups: field 568,465, max-entrants 275,794, max top-1% 3,650, field top-1% 5,734, Doug entered 150, model 150, nodraw 150, median70 150, cap45 150; max-entrant users with 150: 1,834

|  | field | max-entrants | max top-1% | field top-1% | Doug | model | nodraw | median70 | cap45 |
|---|---|---|---|---|---|---|---|---|---|
| salary QB | 7382.6 | 7311.6 | 7392.0 | 7429.5 | 7430.7 | 7420.7 | 7420.7 | 7420.7 | 7420.7 |
| salary RB | 18995.5 | 19701.6 | 21297.3 | 20969.8 | 16125.3 | 16062.0 | 17250.0 | 19122.7 | 16571.3 |
| salary WR | 22274.7 | 21814.9 | 20712.9 | 20865.5 | 22461.3 | 22487.3 | 22328.7 | 20794.0 | 22667.3 |
| salary TE | 7246.6 | 7200.7 | 6657.7 | 6714.8 | 8568.0 | 8598.7 | 8152.0 | 8899.3 | 8762.7 |
| salary DST | 3881.1 | 3731.4 | 3785.6 | 3850.6 | 4152.7 | 4150.0 | 4242.0 | 3638.0 | 4076.0 |
| salary total | 59780.5 | 59760.2 | 59845.5 | 59830.2 | 58738.0 | 58718.7 | 59393.3 | 59874.7 | 59498.0 |
| avg player own % | 18.6 | 19.9 | 20.5 | 20.1 | 10.7 | 10.6 | 10.8 | 17.4 | 12.6 |
| total own % | 167.7 | 179.5 | 184.6 | 180.7 | 96.4 | 95.3 | 97.5 | 157.0 | 113.4 |
| chalk (>20% owned) | 3.4 | 3.8 | 3.9 | 3.8 | 1.5 | 1.4 | 1.5 | 3.0 | 1.9 |
| RBs | 2.6 | 2.7 | 2.9 | 2.9 | 2.2 | 2.2 | 2.4 | 2.4 | 2.2 |
| FLEX RB % | 64.3 | 73.4 | 89.3 | 85.4 | 24.0 | 23.3 | 41.3 | 42.0 | 20.0 |
| FLEX WR % | 19.6 | 13.1 | 2.8 | 5.0 | 31.3 | 31.3 | 24.0 | 14.0 | 32.7 |
| FLEX TE % | 16.1 | 13.4 | 7.9 | 9.6 | 44.7 | 45.3 | 34.7 | 44.0 | 47.3 |
| QB stack pieces | 1.3 | 1.5 | 1.4 | 1.4 | 2.1 | 2.1 | 2.2 | 2.2 | 2.1 |
| QB + 2 or more % | 42.3 | 49.5 | 45.7 | 43.7 | 99.3 | 100.0 | 100.0 | 100.0 | 100.0 |
| bring-back % | 55.3 | 63.3 | 63.3 | 58.7 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| naked QB % | 13.0 | 7.0 | 9.5 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| distinct lineups per 150 |  | 105.6 |  |  | 150.0 | 150.0 | 150.0 | 150.0 | 150.0 |
| top player exposure % |  | 69.5 |  |  | 17.3 | 16.7 | 16.7 | 70.0 | 30.0 |
| players used |  | 70.2 |  |  | 133.0 | 133.0 | 117.0 | 111.0 | 137.0 |
| overlap with nearest lineup |  | 6.3 |  |  | 4.9 | 4.9 | 6.0 | 6.9 | 4.9 |

## 2026-w06

Lineups: field 569,900, max-entrants 275,097, max top-1% 2,732, field top-1% 5,704, Doug entered 150, model 150, nodraw 150, median70 150, cap45 150; max-entrant users with 150: 1,831

|  | field | max-entrants | max top-1% | field top-1% | Doug | model | nodraw | median70 | cap45 |
|---|---|---|---|---|---|---|---|---|---|
| salary QB | 7767.4 | 7730.2 | 7485.9 | 7507.3 | 7771.3 | 7764.7 | 7764.7 | 7760.0 | 7748.0 |
| salary RB | 19793.8 | 20300.9 | 22260.6 | 21799.2 | 18358.7 | 18274.7 | 19380.7 | 18815.3 | 17471.3 |
| salary WR | 21694.4 | 21426.5 | 20240.6 | 20588.8 | 21198.0 | 21155.3 | 20480.7 | 22436.7 | 21401.3 |
| salary TE | 6666.0 | 6563.1 | 5902.3 | 6040.3 | 7824.0 | 7822.7 | 7724.7 | 7072.7 | 9048.0 |
| salary DST | 3886.7 | 3786.0 | 3950.7 | 3905.8 | 4066.7 | 4059.3 | 4095.3 | 3748.0 | 3949.3 |
| salary total | 59808.3 | 59806.7 | 59840.1 | 59841.3 | 59218.7 | 59076.7 | 59446.0 | 59832.7 | 59618.0 |
| avg player own % | 16.6 | 17.3 | 18.7 | 18.5 | 12.2 | 12.1 | 12.5 | 17.2 | 13.5 |
| total own % | 149.5 | 155.8 | 168.2 | 166.7 | 109.8 | 108.6 | 112.4 | 154.6 | 121.6 |
| chalk (>20% owned) | 3.3 | 3.6 | 3.7 | 3.7 | 1.9 | 1.9 | 2.0 | 3.7 | 2.3 |
| RBs | 2.7 | 2.7 | 2.9 | 2.8 | 2.5 | 2.5 | 2.6 | 2.7 | 2.4 |
| FLEX RB % | 67.2 | 74.9 | 87.4 | 80.8 | 46.7 | 46.0 | 62.0 | 66.7 | 38.0 |
| FLEX WR % | 18.0 | 12.1 | 8.1 | 12.4 | 22.0 | 22.7 | 8.7 | 13.3 | 16.7 |
| FLEX TE % | 14.8 | 13.0 | 4.5 | 6.8 | 31.3 | 31.3 | 29.3 | 20.0 | 45.3 |
| QB stack pieces | 1.2 | 1.3 | 1.1 | 1.1 | 2.1 | 2.1 | 2.3 | 2.2 | 2.1 |
| QB + 2 or more % | 33.9 | 37.3 | 30.6 | 32.7 | 98.7 | 100.0 | 100.0 | 100.0 | 100.0 |
| bring-back % | 38.9 | 48.3 | 54.8 | 42.9 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| naked QB % | 18.3 | 14.0 | 26.7 | 25.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| distinct lineups per 150 |  | 105.4 |  |  | 150.0 | 150.0 | 150.0 | 150.0 | 150.0 |
| top player exposure % |  | 64.6 |  |  | 18.7 | 16.7 | 16.7 | 70.0 | 30.0 |
| players used |  | 64.9 |  |  | 107.0 | 107.0 | 98.0 | 91.0 | 105.0 |
| overlap with nearest lineup |  | 6.2 |  |  | 5.2 | 5.2 | 6.0 | 6.9 | 5.3 |

## 2026-w07

Lineups: field 547,771, max-entrants 265,450, max top-1% 4,111, field top-1% 5,492, Doug entered 150, model 150, median70 150, cap45 150; max-entrant users with 150: 1,765

|  | field | max-entrants | max top-1% | field top-1% | Doug | model | median70 | cap45 |
|---|---|---|---|---|---|---|---|---|
| salary QB | 7614.4 | 7613.8 | 7768.1 | 7753.8 | 7681.3 | 7686.7 | 7728.7 | 7726.0 |
| salary RB | 19630.9 | 20355.8 | 19777.5 | 19584.5 | 16205.3 | 16188.0 | 17177.3 | 16336.0 |
| salary WR | 21675.5 | 21171.3 | 21981.2 | 22147.0 | 21047.3 | 21070.0 | 20798.7 | 21253.3 |
| salary TE | 7041.8 | 7004.0 | 6868.9 | 6865.6 | 10210.0 | 10197.3 | 9626.7 | 9861.3 |
| salary DST | 3848.1 | 3667.3 | 3436.8 | 3488.2 | 4648.7 | 4652.0 | 4580.0 | 4620.0 |
| salary total | 59810.7 | 59812.2 | 59832.5 | 59839.0 | 59792.7 | 59794.0 | 59911.3 | 59796.7 |
| avg player own % | 18.3 | 19.2 | 14.1 | 13.8 | 12.1 | 12.0 | 14.9 | 13.5 |
| total own % | 164.4 | 173.2 | 126.5 | 124.6 | 109.2 | 108.3 | 133.9 | 121.7 |
| chalk (>20% owned) | 3.5 | 3.8 | 2.3 | 2.2 | 1.5 | 1.5 | 2.0 | 1.9 |
| RBs | 2.6 | 2.7 | 2.7 | 2.7 | 2.1 | 2.1 | 2.3 | 2.2 |
| FLEX RB % | 58.2 | 65.2 | 74.6 | 72.9 | 14.0 | 14.0 | 27.3 | 15.3 |
| FLEX WR % | 21.3 | 15.6 | 11.9 | 13.7 | 8.0 | 8.0 | 2.0 | 10.7 |
| FLEX TE % | 20.5 | 19.2 | 13.5 | 13.4 | 78.0 | 78.0 | 70.7 | 74.0 |
| QB stack pieces | 1.3 | 1.4 | 1.4 | 1.4 | 2.0 | 2.0 | 2.1 | 2.0 |
| QB + 2 or more % | 40.9 | 46.9 | 45.0 | 42.4 | 99.3 | 100.0 | 100.0 | 100.0 |
| bring-back % | 52.6 | 61.1 | 52.9 | 50.7 | 100.0 | 100.0 | 100.0 | 100.0 |
| naked QB % | 13.3 | 8.2 | 6.9 | 10.2 | 0.7 | 0.0 | 0.0 | 0.0 |
| distinct lineups per 150 |  | 105.9 |  |  | 150.0 | 150.0 | 150.0 | 150.0 |
| top player exposure % |  | 66.9 |  |  | 20.7 | 20.0 | 70.0 | 32.0 |
| players used |  | 65.3 |  |  | 84.0 | 83.0 | 76.0 | 83.0 |
| overlap with nearest lineup |  | 6.3 |  |  | 5.6 | 5.6 | 6.9 | 5.5 |

## 2026-w08

Lineups: field 563,810, max-entrants 274,800, max top-1% 3,714, field top-1% 5,659, Doug entered 150, model 150, nodraw 150, median70 150, cap45 150; max-entrant users with 150: 1,830

|  | field | max-entrants | max top-1% | field top-1% | Doug | model | nodraw | median70 | cap45 |
|---|---|---|---|---|---|---|---|---|---|
| salary QB | 7938.6 | 7949.0 | 8293.6 | 8301.4 | 7850.7 | 7846.7 | 7919.3 | 7846.7 | 7846.7 |
| salary RB | 19606.7 | 20252.9 | 19702.3 | 19512.5 | 16712.7 | 16698.7 | 17410.7 | 18286.0 | 16722.0 |
| salary WR | 21908.0 | 21391.7 | 21829.3 | 21832.2 | 21691.3 | 21708.7 | 20764.7 | 21642.7 | 21450.7 |
| salary TE | 6412.6 | 6426.6 | 6260.2 | 6282.1 | 9183.3 | 9182.7 | 9582.0 | 8069.3 | 9450.0 |
| salary DST | 3968.0 | 3817.4 | 3765.8 | 3916.9 | 4336.0 | 4330.7 | 4278.7 | 4095.3 | 4295.3 |
| salary total | 59833.9 | 59837.6 | 59851.2 | 59845.1 | 59774.0 | 59767.3 | 59955.3 | 59940.0 | 59764.7 |
| avg player own % | 13.7 | 14.4 | 16.3 | 15.7 | 9.9 | 9.8 | 10.1 | 12.8 | 10.4 |
| total own % | 123.0 | 129.2 | 146.4 | 141.4 | 88.8 | 88.4 | 91.0 | 114.9 | 93.2 |
| chalk (>20% owned) | 2.5 | 2.8 | 3.2 | 2.9 | 1.3 | 1.3 | 1.3 | 2.3 | 1.5 |
| RBs | 2.7 | 2.7 | 2.8 | 2.8 | 2.2 | 2.2 | 2.3 | 2.5 | 2.2 |
| FLEX RB % | 67.2 | 73.8 | 83.2 | 81.2 | 21.3 | 21.3 | 29.3 | 46.0 | 23.3 |
| FLEX WR % | 21.8 | 16.2 | 13.2 | 13.6 | 15.3 | 15.3 | 2.7 | 6.7 | 10.7 |
| FLEX TE % | 11.0 | 10.0 | 3.5 | 5.2 | 63.3 | 63.3 | 68.0 | 47.3 | 66.0 |
| QB stack pieces | 1.2 | 1.3 | 1.8 | 1.8 | 2.1 | 2.1 | 2.2 | 2.2 | 2.1 |
| QB + 2 or more % | 33.7 | 38.8 | 79.3 | 73.3 | 99.3 | 100.0 | 100.0 | 100.0 | 100.0 |
| bring-back % | 40.8 | 48.7 | 67.8 | 62.5 | 99.3 | 100.0 | 100.0 | 100.0 | 100.0 |
| naked QB % | 19.9 | 16.2 | 1.4 | 1.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| distinct lineups per 150 |  | 105.8 |  |  | 150.0 | 150.0 | 150.0 | 150.0 | 150.0 |
| top player exposure % |  | 63.6 |  |  | 18.0 | 18.0 | 18.0 | 70.0 | 26.7 |
| players used |  | 70.2 |  |  | 99.0 | 97.0 | 89.0 | 85.0 | 97.0 |
| overlap with nearest lineup |  | 6.2 |  |  | 5.1 | 5.1 | 5.9 | 6.9 | 5.0 |

## Similarity: mean gap in SD units (lower = more like max-entrants), per week

**2026-w05**

|  | vs max-entrants (lineups) | vs max top-1% (lineups) | vs max-entrants (portfolio) |
|---|---|---|---|
| Doug entered | 0.87 | 1.01 | 1.26 |
| model | 0.88 | 1.02 | 1.27 |
| nodraw | 0.70 | 0.85 | 1.01 |
| median70 | 0.47 | 0.56 | 0.50 |
| cap45 | 0.74 | 0.89 | 1.16 |

**2026-w06**

|  | vs max-entrants (lineups) | vs max top-1% (lineups) | vs max-entrants (portfolio) |
|---|---|---|---|
| Doug entered | 0.70 | 0.89 | 1.02 |
| model | 0.73 | 0.92 | 1.04 |
| nodraw | 0.62 | 0.77 | 0.87 |
| median70 | 0.34 | 0.56 | 0.50 |
| cap45 | 0.67 | 0.87 | 0.90 |

**2026-w07**

|  | vs max-entrants (lineups) | vs max top-1% (lineups) | vs max-entrants (portfolio) |
|---|---|---|---|
| Doug entered | 0.81 | 0.74 | 0.84 |
| model | 0.82 | 0.74 | 0.84 |
| median70 | 0.71 | 0.64 | 0.35 |
| cap45 | 0.76 | 0.67 | 0.74 |

**2026-w08**

|  | vs max-entrants (lineups) | vs max top-1% (lineups) | vs max-entrants (portfolio) |
|---|---|---|---|
| Doug entered | 0.88 | 0.89 | 0.89 |
| model | 0.88 | 0.89 | 0.88 |
| nodraw | 0.88 | 0.89 | 0.71 |
| median70 | 0.59 | 0.59 | 0.42 |
| cap45 | 0.86 | 0.87 | 0.81 |

**Weeks 5-8 average**

|  | vs max-entrants (lineups) | vs max top-1% (lineups) | vs max-entrants (portfolio) |
|---|---|---|---|
| Doug entered | 0.81 | 0.88 | 1.01 |
| model | 0.83 | 0.89 | 1.01 |
| nodraw | 0.73 | 0.84 | 0.86 |
| median70 | 0.52 | 0.59 | 0.44 |
| cap45 | 0.76 | 0.82 | 0.90 |

## Weeks 5-8 average of every metric

|  | field | max-entrants | max top-1% | field top-1% | Doug | model | nodraw | median70 | cap45 |
|---|---|---|---|---|---|---|---|---|---|
| salary QB | 7675.8 | 7651.2 | 7734.9 | 7748.0 | 7683.5 | 7679.7 | 7701.6 | 7689.0 | 7685.3 |
| salary RB | 19506.7 | 20152.8 | 20759.4 | 20466.5 | 16850.5 | 16805.8 | 18013.8 | 18350.3 | 16775.2 |
| salary WR | 21888.2 | 21451.1 | 21191.0 | 21358.4 | 21599.5 | 21605.3 | 21191.3 | 21418.0 | 21693.2 |
| salary TE | 6841.7 | 6798.6 | 6422.3 | 6475.7 | 8946.3 | 8950.3 | 8486.2 | 8417.0 | 9280.5 |
| salary DST | 3896.0 | 3750.5 | 3734.7 | 3790.4 | 4301.0 | 4298.0 | 4205.3 | 4015.3 | 4235.2 |
| salary total | 59808.4 | 59804.2 | 59842.3 | 59838.9 | 59380.8 | 59339.2 | 59598.2 | 59889.7 | 59669.3 |
| avg player own % | 16.8 | 17.7 | 17.4 | 17.0 | 11.2 | 11.1 | 11.1 | 15.6 | 12.5 |
| total own % | 151.2 | 159.4 | 156.4 | 153.4 | 101.1 | 100.2 | 100.3 | 140.1 | 112.5 |
| chalk (>20% owned) | 3.2 | 3.5 | 3.3 | 3.1 | 1.6 | 1.5 | 1.6 | 2.8 | 1.9 |
| RBs | 2.6 | 2.7 | 2.8 | 2.8 | 2.3 | 2.3 | 2.4 | 2.5 | 2.2 |
| FLEX RB % | 64.2 | 71.8 | 83.6 | 80.1 | 26.5 | 26.2 | 44.2 | 45.5 | 24.2 |
| FLEX WR % | 20.2 | 14.3 | 9.0 | 11.2 | 19.2 | 19.3 | 11.8 | 9.0 | 17.7 |
| FLEX TE % | 15.6 | 13.9 | 7.3 | 8.8 | 54.3 | 54.5 | 44.0 | 45.5 | 58.2 |
| QB stack pieces | 1.3 | 1.4 | 1.4 | 1.4 | 2.1 | 2.1 | 2.2 | 2.2 | 2.1 |
| QB + 2 or more % | 37.7 | 43.1 | 50.2 | 48.0 | 99.2 | 100.0 | 100.0 | 100.0 | 100.0 |
| bring-back % | 46.9 | 55.3 | 59.7 | 53.7 | 99.8 | 100.0 | 100.0 | 100.0 | 100.0 |
| naked QB % | 16.1 | 11.3 | 11.1 | 12.4 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| distinct lineups per 150 |  | 105.7 |  |  | 150.0 | 150.0 | 150.0 | 150.0 | 150.0 |
| top player exposure % |  | 66.1 |  |  | 18.7 | 17.8 | 17.1 | 70.0 | 29.7 |
| players used |  | 67.6 |  |  | 105.8 | 105.0 | 101.3 | 90.8 | 105.5 |
| overlap with nearest lineup |  | 6.3 |  |  | 5.2 | 5.2 | 6.0 | 6.9 | 5.2 |
