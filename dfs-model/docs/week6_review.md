# Week 6 review (Oct 18, 2026)

One contest, graded from FanDuel's "All Entries" export (`data/2026-w06/raw/135326-281053769.csv`, converted with
`src/convert_results.py --user gst1999`). Doug entered no other contest this week.

| | Pooch Punt ($0.05) |
|---|---|
| Entries | 571,917 |
| Winner | 189.96 |
| Field average / median | 110.7 / 110.9 |
| Top-10% / top-1% cutoff | 136.26 / 156.52 |
| Mine | 149 model lineups (3 changed by hand) + 1 free entry (Doug's own lineup) |

**Bottom line: below the field again, but one lineup made the top 1%.** The 149 model lineups averaged 104.5
against a field average of 110.7 (-6.2). The best, a Drake Maye stack, scored 158.4 and ranked 3,975 (top 0.70%).
A low-scoring slate: the winner had 190, against 248 in week 5 and 217 in week 4.

**Money: net -$1.49.** Won $5.96 on $7.45 of fees (149 paid + 1 free; Doug's total, the export carries no prize
data). Running total since week 4: **-$3.88** (week 4 +$2.35, week 5 -$4.74, week 6 -$1.49).

## 1. Model lineups vs the field

| | Week 6 | Week 5 | Week 4 |
|---|---|---|---|
| Model average | 104.5 | 108.5 | 111.3 |
| Field average | 110.7 | 131.2 | 107.3 |
| Difference | -6.2 | -22.7 | +4.0 |
| Best lineup | 158.40 | 184.86 | 178.72 |
| Best rank | 3,975 (top 0.70%) | 10,705 (top 1.9%) | 1,054 (top 0.18%) |
| Lineups in top 1% | 1 | 0 | 4 |
| Lineups in top 10% | 8 | 3 | n/a |
| Lineups above field median | 58 of 149 | 29 of 149 | n/a |
| Winning score | 189.96 | 247.58 | 216.98 |
| Winnings / net $ | $5.96 / -$1.49 | $3.11 / -$4.34 (PP) | +$2.35 net |
| Running total since week 4 | -$3.88 | -$2.39 | +$2.35 |

Other counts: 2 in the top 5%, 13 in the top 20%. The model's lineups as built (before Doug's three hand changes)
averaged 104.1 with the same 8 / 1 top-10% / top-1% counts. Projected lineup average was 122.7; projected and
actual lineup scores correlated **0.00** (week 5: 0.43). The free entry (Doug's own Stafford / Walker / Nacua
lineup, not from any model run) scored 117.5, rank 201,233 (top 35%), better than 104 of the 149 model lineups.
The model's 150th lineup, dropped for the free entry, would have scored 84.4.

Where the 6 points went, by roster position (field = ownership-weighted average lineup):

| Position | Field pts | Our pts | Field slots | Our slots |
|---|---|---|---|---|
| QB | 17.7 | 18.2 | 1.00 | 1.00 |
| RB | 37.8 | 32.7 | 2.66 | 2.47 |
| WR | 34.0 | 34.4 | 3.17 | 3.22 |
| TE | 13.2 | 11.6 | 1.14 | 1.31 |
| DST | 7.5 | 7.6 | 1.00 | 1.00 |

Running back again: 5 of the 6 points. Our flex was RB 70, TE 47, WR 33 (TE in flex 31%, down from 45%). Kenneth
Walker (29.9 pts, 31% owned, us 18%) is most of it; Bijan Robinson (6.3 pts, us 17%) and Kyren Williams (8.2, us
17%) took the rest.

## 2. Doug's reads (red and yellow applied, no greens)

Graded by `src/analyze_results.py` (`weeks/2026-w06/reads_players.csv`, `reads_lineups.csv`).

**Per player.**

| Colour | Players | Projected | Scored | Below projection | Field own | Our lineup slots |
|---|---|---|---|---|---|---|
| Red | 10 (all WR) | 7.3 | 7.0 | 6 of 10 | 3.0% | 0 (46 in the review run) |
| Yellow | 9 (6 QB, Kamara, D. Smith, Metcalf) | 14.5 | 13.6 | 5 of 9 | 1.5% | 31 |

Red, player by player (projected / scored; lineups in the review run): Vele 10.0 / 5.7 (8), Tate 9.0 / 16.0 (8),
Robinson 9.0 / 3.7 (8), **Germie Bernard 8.1 / 20.2 (3)**, Virgil 7.3 / 0.0 (6), Bourne 7.2 / 7.2 (5), Concepcion
6.7 / 5.9 (1), Hurst 5.5 / 5.5 (1), Mumpfield 5.3 / 2.5 (2), Fields 5.2 / 2.9 (4). Bernard was the miss that
mattered: 12% owned and in the winning lineup and the second-place one. Tate was the other hit.

Yellow (projected / scored; cap = half the review-run number): Huntley 17.8 / 13.4, Brissett 17.1 / 7.9, Watson
16.1 / 9.5, **Penix 15.5 / 23.1**, Daniels 14.7 / 12.7, Herbert 13.9 / 9.8, Kamara 12.7 / 13.9, D. Smith 11.6 /
17.0, Metcalf 11.5 / 14.8. The QB fades were right on five of six; Penix was wrong, and the ATL stack (capped at
6 lineups) was our best stack at 125.6 a lineup. The three skill-player yellows all beat projection.

**As lineups.** The optimizer re-run as entered reproduces the uploaded 150 exactly (104.0, best 158.4), then once
with each colour taken out:

| Run (150 lineups) | Avg | Top 10% | Top 1% | Best | Best rank |
|---|---|---|---|---|---|
| As entered (red + yellow) | 104.0 | 8 | 1 | 158.4 | 5,089* |
| Red removed | 102.6 | 6 | 0 | 140.3 | 41,280 |
| Yellow removed | 104.5 | 8 | 0 | 152.5 | 12,794 |

\* estimated from field quantiles; the entered lineup's real rank was 3,975.

Red was worth **+1.4 per lineup**, yellow **-0.5**. Over three weeks red + yellow have been worth +3.0, +2.5 and
about +0.9 (week 6 is the sum of the two separate runs; they were not removed together). The single top-1% lineup appears only in the as-entered run, so it is a reshuffle,
not something either colour bought on its own.

## 3. Doug's manual swaps

146 of the 150 entries match `weeks/2026-w06/entered_upload_149.csv` exactly. Three were changed by hand, and the
150th is the free entry. All three changes were the last three lineups built, and all three spent leftover salary:

| Entry | Out | In | Salary before / after | Proj before / after | Points before / after | Rank before / after |
|---|---|---|---|---|---|---|
| 149 | Dameon Pierce (13.0) | Kenneth Walker III (29.9) | $55,900 / $59,500 | 109.4 / 117.7 | 91.2 / 108.1 | ~478,000 / 315,183 |
| 148 | Buccaneers DST (7.0), Michael Wilson (5.2), Cedric Tillman (0.0) | Puka Nacua (11.0), Jonathan Taylor (20.1), Chiefs DST (15.0) | $51,400 / $59,900 | 100.6 / 127.4 | 67.7 / 101.6 | ~563,000 / 385,054 |
| 147 | Mark Andrews (0.9) | Puka Nacua (11.0) | $56,100 / $59,900 | 105.7 / 121.9 | 68.0 / 78.1 | ~562,000 / 542,535 |

**+60.9 points over the three, +20.3 a lineup**; projection +17.1 a lineup. None reached the top 10%, so no prize
effect is likely, but every swap was right. "Before" ranks are interpolated from our own entries' real ranks.

## 4. Salary left on the table

As built, the 149 lineups left $893 a lineup unspent (after the swaps, $781). Fourteen left $3,000 or more:

| Unspent | Lineups | Avg points | Avg projection | Above field median |
|---|---|---|---|---|
| under $500 | 87 | 106.1 | 127.1 | 39 |
| $500-1,500 | 36 | 103.3 | 118.5 | 14 |
| $1,500-3,000 | 12 | 101.6 | 115.2 | 2 |
| **$3,000+** | **14** | **95.7** | **107.7** | **2** |

The $3,000+ lineups (as built; line number, unspent, points, cheap players with their points):

| Line | Unspent | Pts | Cheap players ($5,300 or less) |
|---|---|---|---|
| 148 | $8,600 | 67.7 | Juwan Johnson 0.0, Cedric Tillman 0.0 (swapped by Doug) |
| 141 | $7,000 | 83.6 | Juwan Johnson 0.0 |
| 134 | $6,000 | 102.2 | Tyler Allgeier 5.3, Tyler Higbee 2.2 |
| 108 | $5,300 | 105.5 | Darren Waller 0.0, Jalen Nailor 1.4 |
| 144 | $4,900 | 102.8 | Kyle Pitts 20.5, Dameon Pierce 13.0 |
| 107 | $4,700 | 109.9 | Jalen Nailor 1.4, Pat Freiermuth 2.1 |
| 145 | $4,300 | 78.4 | Dameon Pierce 13.0, Tyler Higbee 2.2 |
| 149 | $4,100 | 91.2 | Dameon Pierce 13.0, Juwan Johnson 0.0 (swapped by Doug) |
| 109 | $4,000 | 106.6 | Jalen Nailor 1.4 |
| 147 | $3,900 | 68.0 | Quentin Johnston 6.2, Mark Andrews 0.9 (swapped by Doug) |
| 106 | $3,300 | 107.8 | Tyler Higbee 2.2, Cody White 0.0 |
| 42 | $3,300 | 118.6 | none |
| 47 | $3,200 | 112.2 | Hunter Henry 12.8 |
| 123 | $3,100 | 85.9 | Dameon Pierce 13.0, Pat Freiermuth 2.1 |

**Tillman and Pierce.** Cedric Tillman (NO WR3, $4,200, projected 4.8, 0.1% owned) was in 8 lineups as built and
scored 0.0; seven of them spent almost all the cap (he was a punt to fit studs), and the eighth was line 148. Dameon
Pierce (PHI RB1 with Barkley and Bigsby out, $5,300, projected 10.7 with +6.2 from routing) scored 13.0, above
projection; he is in four of the $3,000+ lineups because he was cheap and eligible late, not because he failed.

**Did leftover salary cost us? Yes, but it is a symptom.** The $3,000+ lineups scored 10 points under the
full-spend ones and projected 19 under. Twelve of the 14 are among the last 45 lineups built (106-149): by then 22
players had hit the 25-lineup cap, the optimizer was choosing from what was left, and nothing it could still afford
projected better than the cheap options. A salary floor forces it to spend that money on the best remaining players.
Section 8 tests one.

## 5. Depth check (the Q-exclusion issue)

Excluded Q players do not hold starter depth, so the next man up becomes a "starter" (RB1 / top-3 WR / TE1 by
projection). Six players were promoted that way; with the Q player counted at his un-discounted projection, these
six would not have been starters:

| Team | Promoted | Proj | Pts | Our lineups | Behind (excluded Q, pts) |
|---|---|---|---|---|---|
| NE | Efton Chism III (WR) | 5.0 | 0.0 | **1** | A.J. Brown (4.2) |
| BAL | Chris Moore (WR) | 3.4 | 0.0 | 0 | Ja'Kobi Lane (6.0) |
| BUF | Skyler Bell (WR) | 3.1 | 0.0 | 0 | DJ Moore (0.0) |
| CLE | Jaret Patterson (RB) | 3.5 | 0.0 | 0 | Quinshon Judkins (0.0) |
| IND | Mo Alie-Cox (TE) | 2.7 | 6.6 | 0 | Tyler Warren (0.0) |
| LAC | Marquez Valdes-Scantling (WR) | 3.0 | 0.0 | 0 | Brenen Thompson (0.0) |

**One rostered slot out of 1,350** was a player behind an excluded starter (Chism, 0.0). The `min_proj = 4` filter
kept the other five out. Of the 11 excluded Q players, Judkins, Warren, DJ Moore and Thompson scored 0 (did not
play or barely); A.J. Brown 4.2, Palmer 4.2, Lane 6.0; Omar Cooper Jr. scored 22.3 but was projected 1.7 and would
not have been used. Pulling Q players cost nothing measurable this week.

Players promoted by an OUT teammate (real absences, not Q) did well: the eight with 2+ points of routing bump that
we rostered (Allen, Pierce, Allgeier, Wetjen, Swift, Hubbard, Kamara, Worthy; 134 slots) projected 14.6 per slot
and scored 14.0, closer than the slate as a whole. The week-6 volume fix is doing its job. Wetjen (5.1, all from
routing, 0.0) and Allgeier (12.7, 5.3) were the misses.

## 6. Calibration, stacks, DST, ownership

### Calibration

Skill players projected above 0: r = 0.70 (0.73 including zeros), average over-projection +1.4, RMSE 5.0.

| Projected | n | Projected avg | Actual avg | Gap | Week 5 gap | Week 4 gap |
|---|---|---|---|---|---|---|
| 0-8 | 184 | 3.1 | 2.3 | +0.8 | +0.3 | |
| 8-14 | 51 | 10.4 | 8.5 | +2.0 | +2.2 | +1.8 |
| 14-20 | 31 | 16.9 | 14.4 | +2.6 | +1.6 | +2.8 |
| 20+ | 5 | 22.5 | 14.7 | +7.8 | +4.9 | +6.3 |

The 20+ five: Allen 24.6 / 18.3, Nacua 23.7 / 11.0, Stafford 23.3 / 16.9, Swift 20.8 / 21.0, Bijan 20.1 / 6.3. A
low-scoring slate lowers every tier, and only 2.3% of players projected 8+ beat their 90th percentile (expected
10%), so part of this is the slate. But the top tier has now been over-projected by 5-8 points three weeks running,
with the calibration shrink on.

By position, projected 8+: QB 17.3 / 15.7 (r 0.45), RB 13.6 / 9.9 (r 0.57), **WR 11.7 / 11.0 (r -0.02)**, TE 11.1
/ 5.7 (r 0.54). WR had no rank-order value this week; RB and TE are over-projected again.

### Stacks

| Stack | Lineups | Avg | Best | QB | QB proj | QB pts | QB field own | Weight |
|---|---|---|---|---|---|---|---|---|
| ATL | 6 | 125.6 | 142.7 | Penix (yellow) | 15.5 | 23.1 | 2.9% | 19 |
| NE | 13 | 119.0 | 158.4 | Maye | 19.9 | 23.8 | 6.3% | 19 |
| BUF | 23 | 114.7 | 149.1 | Allen | 24.6 | 18.3 | 15.1% | 27 |
| NYG | 8 | 109.2 | 136.6 | Winston | 15.2 | 8.5 | 5.7% | 13 |
| NO | 10 | 108.8 | 126.6 | Shough | 18.3 | 27.0 | 4.0% | 16 |
| LV | 9 | 108.4 | 117.8 | Cousins | 17.4 | 22.5 | 9.8% | 16 |
| CHI | 18 | 104.4 | 139.8 | Williams | 19.4 | 19.5 | 5.6% | 22 |
| TB | 1 | 103.1 | 103.1 | Daniels (yellow) | 14.7 | 12.7 | 0.5% | 4 |
| IND | 14 | 101.7 | 119.6 | D. Jones | 16.6 | 15.8 | 2.6% | 19 |
| CAR | 6 | 100.6 | 123.5 | Young | 17.8 | 19.8 | 7.0% | 10 |
| LAR | 19 | 97.4 | 117.5 | Stafford | 23.3 | 16.9 | 26.6% | 32 |
| CLE | 1 | 96.2 | 96.2 | Watson (yellow) | 16.1 | 9.5 | 0.8% | 4 |
| NYJ | 2 | 93.3 | 98.5 | G. Smith | 13.4 | 13.0 | 0.4% | 4 |
| KC | 12 | 84.5 | 120.3 | Mahomes | 19.3 | 11.5 | 4.4% | 17 |
| PIT | 5 | 83.4 | 101.7 | Rodgers | 16.2 | 17.0 | 1.6% | 9 |
| BAL | 3 | 81.2 | 94.4 | Huntley (yellow) | 17.8 | 13.4 | 1.3% | 10 |

Stack count against average: r = +0.31 (week 5: +0.54). The heaviest stack, LAR (weight 32, 19 lineups; 8 more
could not be built because Nacua and Adams hit the cap), was below average: Stafford was the most-owned QB at 27%
and Nacua scored 11. The top 1,000 lineups were built on Cousins (29%), Shough (24%), Allen (11%), Young (9%) and
Maye (7%); we had 9, 10, 23, 6 and 13 lineups on them. QB projections r = 0.45 among QBs projected 8+.

### DST

r = 0.11 (weeks 4-5: 0.24, 0.11). Our lineups averaged 7.6 DST points, the field 7.5, all 20 defenses 6.8. Best:
Titans 21 (projected 4.7, 3 lineups), Chiefs 15 (8.2, the top projection, 19 lineups), Saints 13. The flat DST
projection did no harm; three weeks of r near 0.1-0.2 says it still has no real signal.

### Ownership vs exposure

Ownership model across skill players: mean error 1.3 points against 3.2 for guessing the average, r = 0.85 (week
5: 1.4, r 0.75). Same miss as weeks 4 and 5: mid-priced chalk.

| Player | Salary | Projected own | Actual own | Our exposure | Proj pts | Pts |
|---|---|---|---|---|---|---|
| Puka Nacua | 9,000 | 33% | 42% | 19% | 23.7 | 11.0 |
| Isaiah Likely | 5,500 | 10% | 38% | 17% | 13.8 | 20.9 |
| Drake London | 7,600 | 11% | 32% | 17% | 14.9 | 10.2 |
| Kenneth Walker III | 8,900 | 20% | 31% | 18% | 19.0 | 29.9 |
| Bijan Robinson | 9,300 | 18% | 29% | 17% | 20.1 | 6.3 |
| D'Andre Swift | 6,600 | 34% | 27% | 17% | 20.8 | 21.0 |
| Matthew Stafford | 7,800 | 12% | 27% | 13% | 23.3 | 16.9 |
| Chuba Hubbard | 6,800 | 22% | 23% | 17% | 17.2 | 21.6 |
| Rhamondre Stevenson | 6,300 | 4% | 22% | 8% | 12.9 | 3.6 |
| Davante Adams | 7,200 | 20% | 21% | 17% | 18.5 | 5.4 |
| Luther Burden III | 5,800 | 5% | 21% | 17% | 11.1 | 13.5 |
| Buccaneers DST | 3,200 | 5% | 21% | 15% | 6.5 | 7.0 |
| Jalen Coker | 6,000 | 7% | 19% | 9% | 11.3 | 12.7 |
| Jonathan Taylor | 8,700 | 13% | 19% | 17% | 18.8 | 20.1 |

This week the chalk busted: the 19 players owned 15%+ scored 13.1 against 16.3 projected, so the 25-lineup cap
helped. Walker was the exception that cost us. The big scorers we missed were cheap and low-owned: Tre Tucker
24.2 (7% owned, us 13%), Kyle Pitts 20.5 (1%, us 5%), Germie Bernard 20.2 (12%, red, us 0), Omar Cooper 22.3 (Q,
excluded), Titans DST 21.

## 7. Marvin Harrison Jr. in London (HOU @ JAC)

| | Read | Applied (week-1 factor 0.7) | Actual |
|---|---|---|---|
| Target share | 0.15 | 0.105 | **0.125 (4 of 32)** |
| Receptions / yards / TD | | | 3 / 34 / 0 (4.9 FanDuel pts) |
| Air-yards share | | | 18.7% |
| Snaps | | | **12 of about 59 plays (~20%)** |
| Targets per snap | | | 0.33 |

Targets, catches and yards from nflverse week-6 player stats (fetched Oct 18 evening). Snaps are Doug's figure from
a game page found online (nflverse has only Thursday's game so far); its targets / catches / yards match nflverse
exactly. Houston's play count is 34 pass attempts + 25 carries + 0 sacks. In Arizona he played 65-79% of snaps
(weeks 1-4).

He was fourth among Houston targets, behind Schultz (6) and Collins (5) and level with Noel (4). On target share
the read looks right: 12.5% sits between the applied 10.5% and Doug's settled 15%. **But it came on about a fifth
of the snaps**: Houston threw to him on a third of the plays he was on the field for, a rate that will not hold
when his snaps grow. He was a part-time player in his first game in the offence, which is what
`first_week_factor` is meant for; the target share overstated his role.

Suggest week 7 (if Houston is on the main slate): keep `new_target_share = 0.15` as the settled number and keep a
factor below 1 until his snaps rise; 0.7-0.8 (10.5-12%) is defensible. Check his week-7 snap share before raising
it. `[shadow.trade]` is scored here by hand (analyze_results.py does not read it).

## 8. Week-7 fixes

### 8.1 Salary floor (first)

Tested in a scratch copy of the optimizer (nothing in the repo changed): each week's archived projections,
simulations and final config, with a salary floor added. If a lineup cannot meet the floor it falls back to no
floor. The "+3 overflow" variant first lets players already at the 25 cap go up to 28, **only for a lineup that
cannot otherwise meet the floor**. That is what Doug did by hand: his three swaps took Nacua to 28 lineups, Walker
to 27 and Taylor to 26. The no-floor runs reproduce the entered lineups exactly on both weeks.

| Week | Run | Avg | Top 10% | Top 1% | Best | Avg salary | $3k+ unspent | Couldn't meet floor | Used overflow |
|---|---|---|---|---|---|---|---|---|---|
| 6 | No floor (as entered) | 104.0 | 8 | 1 | 158.4 | $59,077 | 15 | | |
| 6 | Floor $59,000 | 104.5 | 7 | 1 | 158.4 | $59,399 | 5 | 15 | |
| 6 | Floor $59,500 | 104.4 | 4 | 1 | 158.4 | $59,435 | 8 | 18 | |
| 6 | **Floor $59,000 + 3 overflow** | **104.5** | **10** | **2** | **165.1** (rank 1,320) | $59,639 | 0 | 5 | 14 |
| 6 | Floor $59,500 + 3 overflow | 104.0 | 7 | 2 | 165.1 | $59,792 | 0 | 5 | 16 |
| 5 | No floor (as entered) | 108.3 | 3 | 0 | 184.9 | $58,719 | 22 | | |
| 5 | Floor $59,000 | 109.7 | 3 | 0 | 184.9 | $59,415 | 3 | 3 | |
| 5 | Floor $59,500 | 109.9 | 3 | 0 | 180.8 | $59,544 | 5 | 5 | |
| 5 | **Floor $59,000 + 3 overflow** | **110.6** | **3** | **0** | **184.9** | $59,566 | 0 | 0 | 3 |
| 5 | Floor $59,500 + 3 overflow | 111.4 | 3 | 0 | 180.8 | $59,755 | 0 | 0 | 5 |

What it shows:

- **A floor on its own does not reach the problem lineups.** With the 25 cap in force, 15 of week 6's lineups had
  no $59,000 option at all, so they fell back to the old lineup. The money is left because the cap has used up the
  players worth buying.
- **Floor $59,000 + 3 overflow was the only run no worse than as-entered on any of the four numbers in either
  week**: week 6 +0.6 a lineup, top-10% 8 → 10, top-1% 1 → 2, best 158.4 → 165.1; week 5 +2.3 a lineup, the others
  the same. No lineup left $3,000. Overflow was needed for 14 lineups in week 6 and 3 in week 5, and no player went
  above 28.
- $59,500 pushes harder for little more: a better average in week 5 and a worse top end in both weeks.

Two slates are noise (week6_prep 9.1), so this is a proposal, not an adoption. It is a mechanical fix with a clear
cause, and it does what Doug did by hand on lines 147-149 (+20 a lineup). **Proposal:** add `[optimizer]
min_salary` and `floor_cap_overflow` to `optimize.py` (off in defaults.toml), and set `min_salary = 59000`,
`floor_cap_overflow = 3` in week 7's week.toml if Doug agrees. The overflow bends his 25-lineup rule to 28 for a
handful of late lineups, so that part is his call; without it the floor does little.

### 8.2 The rest

In priority order. Each one goes in switched off until Doug and I decide.

2. **Top-tier over-projection.** 20+ has run +6.3, +4.9 and +7.8 over three live weeks, with the calibration shrink
   on since week 6 (about 23 players in total). Refit the slope above 16 (now 0.36) with weeks 4-6 added to the
   2021-2025 history, and test on history first (`fit_calibration.py` / `fit_history.py`) before any lineup test.
   RB (13.6 against 9.9) and TE (11.1 against 5.7, projected 8+) are the over-projected positions again.
3. **WR/TE sensitivity to the implied total** (week-7 backlog). WR projections had no rank-order value this week
   (r -0.02 at 8+). Run the out-of-sample test already planned.
4. **Ownership: mid-priced chalk, third week running.** Likely (10% against 38%), London (11% against 32%), Stafford,
   Stevenson, Burden, Coker. Add a value / role-change feature, and Guru when Doug uses it. The chalk busted this
   week, but knowing it is chalk is what turns the 25 cap from an accident into a choice.
5. **Stack weights and QB ownership.** LAR had the largest weight (32) and the most-owned QB (27%) and averaged
   97.4. The leverage `stack_exponent` exists and is off; a small value (0.2-0.3) is worth a lineup test on weeks
   4-6 together.
6. **Reads.** Keep red and yellow applied (red +1.4 this week; reds have been right three weeks running). Yellow on
   QBs was right five times out of six, but a fade on a QB whose team has a 25+ implied total (Penix, ATL 25.5)
   cost the best stack: worth a second look before capping.
7. **Harrison.** If Houston is on the week-7 main slate: `new_target_share = 0.15`, keep a factor below 1
   (section 7), and check his snaps first.
8. **Existing backlog, unchanged:** per-position redistribution mode and a cap on depth-player boosts. This week
   the routed players were close to their projections (14.6 projected, 14.0 scored), so neither is urgent.
9. **No change: Q exclusion.** One rostered slot in 1,350 was behind an excluded Q player.
10. **Housekeeping:** a small script for the 149-lineup files (still an inline snippet every week), and a reminder
    to note winnings in the run instructions.

## Files

- `data/2026-w06/results_*.csv`: Pooch Punt, from the export in `data/2026-w06/raw/` (untracked).
- `weeks/2026-w06/`: the final run (`upload.csv` 150, `entered_*_149.csv` as uploaded), `review/` the pre-reads run,
  `reads_players.csv` and `reads_lineups.csv` from `analyze_results.py`.
- `config/2026-w06/week.toml`: final config as entered, plus `[contest] field_size`.
