# Week 5 review (Oct 11, 2026)

Two contests, both graded from FanDuel's "All Entries" exports (converted with `src/convert_results.py`):

| | Pooch Punt ($0.05) | Hail Mary ($0.25) |
|---|---|---|
| Export name | 35k Pooch Punt | 45k Hail Mary |
| Entries | 571,483 | 207,707 |
| Winner | 247.58 | 247.58 (same lineup) |
| Field average / median | 131.2 / 132.3 | 135.0 / 137.3 |
| Top-1% cutoff | 190.44 | 191.88 |
| Mine | 149 model + 1 Guru | 1 Guru + 5 model |

**Bottom line: a bad week.** The model lineups averaged 108.5 against a field average of 131.2, and none reached the
top 1%. Week 4 was the reverse (111.3 against 107.3). The model lineups scored about the same both weeks; the field
scored 24 points more this week because four cheap, heavily owned running backs carried it, and our 25-lineup cap
held us well below the field on every one of them.

Not in the exports: prize money. **Cash count and net $ are open** until Doug supplies the winnings for each
contest. Entry fees were $7.45 (149 paid + 1 free) and $1.50 (6 entries).

## 1. Model lineups vs the field (Pooch Punt)

| | Week 5 | Week 4 |
|---|---|---|
| Model average | 108.5 | 111.3 |
| Field average | 131.2 | 107.3 |
| Difference | -22.7 | +4.0 |
| Best lineup | 184.86 | 178.72 |
| Best rank | 10,705 (top 1.9%) | 1,054 (top 0.18%) |
| Lineups in top 1% | 0 | 4 |
| Lineups above field median | 29 of 149 | n/a |
| Winning score | 247.58 | 216.98 |
| Net $ | open (fees $7.45) | +$2.35 |

Other model-lineup counts: 3 in the top 10%, 8 in the top 20%, 15 in the top 30%. The median model lineup ranked
at the 81st percentile from the top (worse than four fifths of the field). Projected lineup average was 123.2;
projected and actual lineup scores correlated 0.43.

Where the 22 points went, by roster position (field = ownership-weighted average lineup):

| Position | Field pts | Our pts | Field slots | Our slots |
|---|---|---|---|---|
| QB | 23.2 | 20.0 | 1.0 | 1.0 |
| RB | 50.4 | 31.2 | 2.63 | 2.23 |
| WR | 33.8 | 33.8 | 3.17 | 3.32 |
| TE | 16.0 | 16.8 | 1.15 | 1.45 |
| DST | 7.2 | 6.7 | 1.0 | 1.0 |

Running back is 19 of the 22 points. The field put a third RB in the flex in 64% of lineups; we did in 23%, and
used a second tight end in 45% (week 4: 48%). Field RB slots averaged 19.2 points each, ours 14.0. Two players
explain 13 points of the gap on their own: Jahmyr Gibbs (38.2 pts, field 39%, us 17%) and Jaylen Warren (36.8,
field 30%, us 17%). Both were in 80-90% of the top 1,000 lineups.

Our lineups also left money unspent: average salary $58,730, and 57 of 149 lineups used under $59,000.

## 2. Calibration

Skill players: r = 0.70 (week 4: 0.68), average over-projection +0.8, RMSE 5.2.

| Projected | n | Projected avg | Actual avg | Gap | Week 4 gap |
|---|---|---|---|---|---|
| 0-8 | 318 | 1.8 | 1.5 | +0.3 | |
| 8-14 | 65 | 10.3 | 8.1 | +2.2 | +1.8 |
| 14-20 | 31 | 16.9 | 15.3 | +1.6 | +2.8 |
| 20+ | 9 | 23.7 | 18.8 | +4.9 | +6.3 |

The top-tier bias is still there. Week 4 (before the prior-season blend) was 23.4 projected against 17.1; week 5
with the blend is 23.7 against 18.8. One player is a third of it: Tyler Shough, projected 20.2, scored 1.8 (I have
not checked why). Without him the tier is 24.2 against 20.9, still +3.3. The nine: Gibbs 38.2, Goff 28.9, Burrow
24.6, Smith-Njigba 23.3, Purdy 17.2, Swift 15.3, St. Brown 9.9, Taylor 9.7, Shough 1.8.

Two things inside those numbers:

- **Backup quarterbacks get starter projections.** Case Keenum 19.5, Drew Lock 16.3, Athan Kaliakmanis 15.7, Carson
  Wentz 13.9, Josh Johnson 10.4. None is eligible for lineups, but they scored 0-2 and distort the tiers. Without
  them the 14-20 tier is exact (16.8 against 16.8); the 20+ gap is unchanged.
- **Running backs are the over-projected position.** Projected 8+: RB 13.4 against 9.7, WR 11.8 against 9.5, QB 16.9
  against 14.9, TE 10.9 against 10.9.

The players the field piled onto were ones whose role had grown, and the model gave them almost no extra volume:
Braelon Allen (Breece Hall out) projected 6.1 with zero gained volume, scored 21.1; Warren (Dowdle out) projected
16.0, scored 36.8; Michael Wilson (Harrison out) gained 0.95. The one large redistribution the model did make,
D'Andre Swift (+9.7, projected 25.6), scored 15.3.

## 3. Stacks

| Stack | Lineups | Avg | Best | QB | QB proj | QB actual |
|---|---|---|---|---|---|---|
| NE | 9 | 148.1 | 180.8 | Maye | 19.1 | 42.5 |
| NYG | 5 | 142.2 | 166.7 | Winston | 11.4 | 28.7 |
| ARI | 9 | 129.4 | 145.4 | Brissett | 19.3 | 25.8 |
| DET | 14 | 127.5 | 151.6 | Goff | 25.1 | 28.9 |
| WAS | 9 | 127.3 | 184.9 | Daniels | 17.5 | 35.3 |
| GB | 5 | 125.6 | 139.5 | Love | 17.8 | 28.3 |
| LV | 6 | 113.4 | 142.1 | Cousins | 17.4 | 13.7 |
| PIT | 8 | 105.3 | 145.5 | Rodgers | 17.2 | 22.0 |
| HOU | 8 | 103.9 | 127.3 | Stroud | 18.4 | 20.9 |
| IND | 6 | 103.0 | 142.6 | D. Jones | 15.2 | 11.1 |
| SEA | 10 | 100.2 | 129.8 | Darnold | 19.7 | 10.3 |
| CIN | 10 | 100.1 | 122.9 | Burrow | 21.8 | 24.6 |
| MIN | 6 | 98.0 | 122.5 | K. Murray | 15.4 | 18.3 |
| DEN | 8 | 95.2 | 113.6 | Nix | 16.9 | 7.9 |
| CHI | 9 | 92.0 | 127.9 | Bagent | 16.6 | 3.2 |
| NYJ | 6 | 90.1 | 117.7 | G. Smith | 14.5 | 10.0 |
| SF | 7 | 90.0 | 128.4 | Purdy | 21.9 | 17.2 |
| CLE | 4 | 89.0 | 101.2 | Watson | 17.1 | 12.2 |
| MIA | 1 | 87.0 | 87.0 | Willis | 11.8 | 20.9 |
| NO | 4 | 75.7 | 100.3 | Shough | 20.2 | 1.8 |
| LAC | 4 | 68.6 | 86.1 | Herbert | 15.2 | 11.2 |
| TEN | 1 | 58.5 | 58.5 | Ward | 11.6 | 6.0 |

Stack count against average score: r = +0.54, so the implied-total weights put more lineups on the better stacks
(implied total against stack average: r = 0.58). Only NE and NYG beat the field average. Of the three 10+ stacks,
DET was fine and SEA and CIN were both near 100. The top 1,000 lineups were built on Love (32%), Maye (26%), Goff
(13%), Brissett (10%), Daniels (8%) and Winston (7%); we had 5, 9, 14, 9, 9 and 5 lineups on them.

QB projections had little rank-order value this week (r = 0.32 among QBs projected 8+).

## 4. DST

r = 0.11 between projected and actual (week 4: 0.24). The three highest projected scored 11 (MIN), 9 (CIN) and 1
(PIT); the best four of the week (SF 18, GB 18, NYJ 16, HOU 15) were projected 4.9, 4.4, 6.5 and 7.3. Our lineups
averaged 6.7 DST points, the field 7.2, and the plain average of all 22 defenses was 7.2. Two weeks running the
DST projection has been no better than picking at random.

## 5. Ownership model

Across 445 players: mean error 1.4 points against 2.9 for guessing the average, r = 0.75 (log r = 0.89). It ranks
the field well overall and misses the chalk badly, the same pattern as week 4:

| Player | Salary | Projected own | Actual own | Our exposure | Proj pts | Actual pts |
|---|---|---|---|---|---|---|
| Michael Wilson | 6,400 | 11% | 51% | 17% | 15.7 | 5.3 |
| D'Andre Swift | 6,500 | 60% | 44% | 17% | 25.6 | 15.3 |
| Jahmyr Gibbs | 10,000 | 36% | 39% | 17% | 29.7 | 38.2 |
| Trey McBride | 7,200 | 15% | 36% | 17% | 18.8 | 17.1 |
| Aaron Jones Sr. | 6,200 | 7% | 31% | 14% | 14.1 | 20.2 |
| Jacoby Brissett | 6,800 | 4% | 30% | 6% | 19.3 | 25.8 |
| Jaylen Warren | 6,700 | 8% | 30% | 17% | 16.0 | 36.8 |
| Amon-Ra St. Brown | 9,000 | 21% | 29% | 17% | 22.1 | 9.9 |
| Nico Collins | 7,800 | 11% | 28% | 17% | 16.4 | 8.1 |
| Commanders DST | 3,300 | 4% | 25% | 7% | 5.7 | 6.0 |
| Jaxon Smith-Njigba | 9,300 | 39% | 19% | 17% | 24.7 | 23.3 |
| Jonathan Taylor | 8,600 | 18% | 18% | 17% | 22.3 | 9.7 |
| Jared Goff | 8,100 | 11% | 18% | 9% | 25.1 | 28.9 |
| Chase Brown | 8,000 | 6% | 16% | 17% | 16.4 | 5.5 |

Eight of these 14 were projected at under half their real ownership, all priced $6,200-$8,000 (plus a $3,300 DST).
Braelon Allen was the same miss one step down (projected 1%, actual 14%).

We were under the field on 13 of the 14, mostly because 17% (25 of 149) is the ceiling the exposure cap allows.
That cut both ways: the chalk as a group scored 17.9 against a projected 19.4, and being light on Wilson, Swift,
St. Brown and Collins helped. It cost far more on Gibbs, Warren, Jones and Brissett.

**Guru as an ownership signal.** The 21 players Guru suggested averaged 14.5% owned against 7.8% projected; the
nine Doug picked averaged 22.5% against 10.8%. Guru had suggested Wilson, Gibbs, Jones, Warren, St. Brown, Goff and
Allen. The ownership model does not yet use Guru at all.

Backup QBs also leak ownership: Keenum, Lock, Kaliakmanis, Wentz and Johnson were given 13.6% of QB ownership
between them (actual 0.2%), which is taken from real starters because QB ownership is scaled to sum to 100%.

## 6. Doug's shadow reads

Scored two ways. Per player:

- **Red (18 names):** projected 5.5 on average, scored 3.2. Sixteen of 18 scored below projection. The exception
  that mattered is Braelon Allen: 21.1 points at 14% owned, in 29% of the top 1,000 lineups (Germie Bernard, 11.4,
  is the other). The final run had already dropped Allen to zero lineups, so that read cost nothing. The entered
  lineups still held 53 red slots, and those averaged 2.2 points against 6.3 projected.
- **Yellow (2):** both right. Doubs 2.1 (projected 10.8), Metcalf 3.8 (projected 13.0); we had them in 16 and 24
  lineups.
- **Green (11):** projected 13.4 on average, scored 9.8; three of 11 beat projection (Aaron Jones 20.2, Burrow
  24.6, Emanuel Wilson 12.2). Misses: Shough 1.8, Hockenson 1.2, Loveland 2.9, Darnold 10.3, Cousins 13.7. Jones
  was a hit but at 31% owned, not a low-owned edge like the week-4 greens.

As lineups. I re-ran the optimizer in a scratch copy with the final statuses and the same simulations (the
unmodified run reproduces the entered lineups exactly), then applied the reads as `[prefs]`:

| Run (150 lineups) | Avg | Best | Above field median | Top 10% | Top 1% |
|---|---|---|---|---|---|
| As entered (no reads) | 108.3 | 184.9 | 29 | 3 | 0 |
| Red + yellow only | 110.8 | 180.8 | 36 | 3 | 0 |
| Green only | 106.6 | 170.9 | 32 | 3 | 0 |
| Red + yellow + green | 107.3 | 180.8 | 25 | 4 | 0 |
| No reads, exposure cap 40 | 112.8 | 180.8 | 38 | 5 | 0 |

**Would applying them have helped? No, not in any way that mattered.** The fades were worth about +2.5 points per
lineup, the greens cost about 1.7, and all three together came out 1 point worse than the model alone. No version
put a lineup in the top 1% or came near the 23-point gap. The archived Oct 10 comparison runs (floor 105.4, boost
111.0, hybrid 108.6) say the same; they used earlier injury statuses, so the table above is the cleaner test.

Over two weeks the reads are mixed: the week-4 greens hit at low ownership (Kyren Williams, Nacua, Emanuel Wilson,
Hockenson), the week-5 greens did not, and the week-5 fades were good.

## 7. The Guru lineup

Goff, Gibbs, Warren, Aaron Jones (flex), Doubs, Golden, Michael Wilson, Kraft, Vikings DST: **171.92, rank 35,308
(top 6.2%)**. It beat 147 of the 149 model lineups. Week 4's Guru lineup scored 93.0 (rank about 427,000).

It was a chalk lineup that hit: its players averaged 22.5% owned, it held three of the four chalk RBs with a third
RB in the flex, and Gibbs, Warren, Jones, Golden and Goff scored 144 between them. Wilson (5.3) and Doubs (2.1)
missed. The model projected it at 141.6, well under its own best lineups (160), mainly because it had Warren at
16.0 and Jones at 14.1.

## 8. The $0.25 Hail Mary

Six entries, not four. Field 207,707, median 137.3.

| Entry | Lineup | Projected | Points | Rank | Percentile |
|---|---|---|---|---|---|
| 1/6 | Guru lineup | 141.6 | 171.92 | 15,051 | top 7.2% |
| 2/6 | Model #1 (Goff) | 160.1 | 151.04 | 56,625 | top 27% |
| 6/6 | Model #6 (Goff) | 154.7 | 146.12 | 72,568 | top 35% |
| 5/6 | Model #26 (Brissett) | 155.6 | 130.26 | 123,452 | 59th |
| 3/6, 4/6 | Not in the final set (same lineup twice) | 156.9 | 127.42 | 131,340 | 63rd |

The model's final top four by projection were #1, #3, #26 and #6. Lineup #3 was not entered. Entries 3/6 and 4/6
are one identical lineup (Goff, Swift, Aaron Jones, Smith-Njigba, St. Brown, Wilson, LaPorta, Hockenson,
Commanders DST) that is not in the final 150 or in any archived run, so it probably came from an earlier upload.
Two model lineups beat the field median and three did not; the Guru lineup was the best of the six. Net $ is
open (fees $1.50).

## 9. Changes for week 6

1. **Decide the 25-lineup cap on evidence.** It bound on 19 players, left $1,270 a lineup unspent and pushed 45% of
   flex spots to a second tight end. The cap-40 re-run projected 6.9 points higher per lineup and scored 4.5 higher.
   That is one slate, so before changing Doug's standing rule, re-run weeks 4 and 5 at 25, 32 and 40 and compare
   top-end finishes, not only averages.
2. **Fix role-change volume.** Allen, Warren and Wilson all had a teammate ruled out and gained almost nothing in
   the projection. Find out why the redistribution skipped them (the `skip_already_absent` path is the first place
   to look) and backtest the fix on weeks 4 and 5.
3. **Add Guru and value-chalk to the ownership model.** Two weeks of the same miss: $6,000-$7,800 players with a
   new role, owned 30-50% and projected under 12%. Guru-suggested players averaged 1.9x the model's number. Once
   ownership finds the chalk, how much of it to hold becomes a choice instead of an accident of the cap.
4. **Shrink the top tier and running backs.** 20+ has run +6.3 and +4.9 in consecutive weeks, and RBs projected 8+
   came in 3.7 under. This is the TD-rate shrinkage already on the roadmap; there are now two slates to tune on
   alongside the 2025 season backtest.
5. **Stop projecting backups and paying for DST projections.** Zero out non-starting QBs (fixes the calibration
   tiers and returns 14% of QB ownership to starters). Treat DST as a near-flat projection until roadmap item 5
   gives a better model; r = 0.24 and 0.11 does not justify spending up.

Stack weights from implied totals worked as intended and need no change.

## Files

- `data/2026-w05/results_*.csv`: Pooch Punt, week-4 formats. `results_025_*.csv`: Hail Mary.
- `data/2026-w05/raw/`: the FanDuel exports, untracked.
- `weeks/2026-w05/`: the final run as entered; `final_week.toml` is its config.
