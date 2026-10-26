# Week 7 review (Oct 26, 2026)

Graded from FanDuel's "All Entries" export (`data/2026-w07/raw/135562-281154846.csv`, converted with
`src/convert_results.py --user gst1999`) and Doug's entry history (`data/2026-w07/fanduel entry history 20261026.xlsx`,
which carries the prizes). Week-7 usage and snaps are from nflverse, downloaded Oct 26 (DAL@PHI is Monday night and
off the slate).

| | Pooch Punt ($0.05) |
|---|---|
| Entries | 550,210 |
| Winner | 228.78 (Burrow, Chase, Higgins, Flowers, Pollard, B. Allen, Concepcion, McBride, Buccaneers DST) |
| Field average / median | 103.3 / 101.2 |
| Top-10% / top-1% cutoff | 129.76 / 156.88 |
| Cash line | about 102 points (76 of our 150 entries cashed) |
| Mine | 149 model lineups (model cap 27, as built, no hand changes) + 1 free entry (Doug's own lineup) |

**Bottom line: just below the field, no top-1% lineup, small profit.** The 149 model lineups averaged 101.1 against
a field average of 103.3 (-2.2). The best, a Burrow stack, scored 151.4 and ranked 9,356 (top 1.7%). Eleven were in
the top 10%. The yellows took about 5 points a lineup off us and the reds about 1.6 (section 3). This was the first
week Doug's reads were wrong on balance.

**Money: Pooch Punt net +$0.73.** Won **$8.18** on $7.45 of fees (149 paid + 1 free). The entry history adds up to
$8.18, not the $8.08 in the run note: 63 x $0.10, 9 x $0.12, 2 x $0.15, 2 x $0.25. Running total since week 4:
**-$3.15** (week 4 +$2.35, week 5 -$4.74, week 6 -$1.49, week 7 +$0.73).
**To confirm:** the entry history also has **two $0.25 Hail Mary entries** (110.12 and 76.92, $0 won; one scored the free
entry's 110.12, so it is probably the same lineup). If they count, week 7 is +$0.23 after $0.50 more in fees, and the running total is -$3.65.

## 1. Model lineups vs the field

| | Week 7 | Week 6 | Week 5 | Week 4 |
|---|---|---|---|---|
| Model average | 101.1 | 104.5 | 108.5 | 111.3 |
| Field average | 103.3 | 110.7 | 131.2 | 107.3 |
| Difference | -2.2 | -6.2 | -22.7 | +4.0 |
| Best lineup | 151.38 | 158.40 | 184.86 | 178.72 |
| Best rank | 9,356 (top 1.7%) | 3,975 (top 0.70%) | 10,705 (top 1.9%) | 1,054 (top 0.18%) |
| Lineups in top 1% | 0 | 1 | 0 | 4 |
| Lineups in top 10% | 11 | 8 | 3 | n/a |
| Lineups above field median | 77 of 149 | 58 of 149 | 29 of 149 | n/a |
| Winning score | 228.78 | 189.96 | 247.58 | 216.98 |
| Winnings / net $ | $8.18 / +$0.73 | $5.96 / -$1.49 | $3.11 / -$4.34 (PP) | +$2.35 net |
| Running total since week 4 | -$3.15 | -$3.88 | -$2.39 | +$2.35 |

Other counts: 4 in the top 5%. Projected lineup average 120.5. **Projected and actual lineup scores correlated
-0.23**: the lineups the model liked most did worst (week 6: 0.00, week 5: 0.43). The free entry (Doug's
Stroud / Gibbs / Kyren / Higgins lineup) scored 110.1, rank 187,031 (top 34%), better than 99 of the 149 model
lineups. The 150th model lineup, dropped for the free entry, would have scored 77.1.

Where the 2.2 points went, by roster position (field = ownership-weighted average lineup):

| Position | Field pts | Our pts | Field slots | Our slots |
|---|---|---|---|---|
| QB | 17.4 | 18.7 | 1.00 | 1.00 |
| RB | 40.9 | 30.1 | 2.57 | 2.14 |
| WR | 29.7 | 34.8 | 3.20 | 3.08 |
| TE | 9.5 | 13.3 | 1.20 | 1.78 |
| DST | 5.4 | 4.2 | 1.00 | 1.00 |

Running back again, and by more than ever: **-10.8 points**, made up at WR and TE. **Our flex was TE in 116 of 149
lineups (78%)**, RB 21, WR 12 (week 6: TE 31%; week 5: 45%). The control set (74%) and the pool (82%) were the
same, so the cause is the shared player pool, not the cap. With only each team's RB1 eligible and several of them red,
yellow or held out, and TEs counting as stack receivers, the flex goes to a TE. The field's RB points came from Tony
Pollard (38.0, yellow, 4 lineups), Braelon Allen (19.4, 21% owned, 5 lineups) and Bucky Irving (26.5). Gibbs
(17.8, 47% owned) and Bijan (14.7) were fine but not the difference.

## 2. All four sets

Every set is scored on actual points and ranked against the real field (all 550,210 entries; the best ranks are exact,
not estimated). Same projections, sims, reds, yellows, salary floor and stack weights in the three built sets.

| Set | Lineups | Avg | Proj avg | Top 10% | Top 1% | Best | Best rank | Players used | Same lineups as model |
|---|---|---|---|---|---|---|---|---|---|
| **Model cap 27 (entered)** | 149 | **101.1** | 120.5 | **11** | 0 | 151.4 | 9,356 | 83 | |
| Model cap 27, all 150 | 150 | 100.9 | 120.4 | 11 | 0 | 151.4 | 9,356 | 83 | 150 |
| Control: model cap 45 | 150 | 98.0 | 122.8 | 8 | **1** | **157.8** | **5,000** | 83 | 35 |
| Doug's pool cap 45 | 150 | 96.1 | 122.2 | 4 | 0 | 148.9 | 11,721 | 74 | 2 |
| Doug's free entry | 1 | 110.1 | 125.2 | 0 | 0 | 110.1 | 187,031 | 9 | |

(`weeks/2026-w07/pool/grade.csv` has the same averages and counts; its best ranks are estimated from the top 2,000 and
the field quantiles, so they differ from the exact ranks here.)

**The pool's effect, apart from the cap (pool vs control, both cap 45): -1.9 a lineup**, top-10% 4 against 8, top-1%
0 against 1, best 148.9 against 157.8. Every number is worse. The pool had 9 stack teams to the model's 14: Doug's pool QBs left out BAL, ATL, NYJ, DEN and IND
(all yellow QBs; Penix, Smith and Nix scored 20+), and it was heavier on players who busted: Godwin, Mumpfield and
Aaron Jones at 45 lineups and Kyren at 44, against 27-30 in the model.

**The cap's effect (control cap 45 vs model cap 27, same pool and reads): -2.9 a lineup**, top-10% 8 against 11, but
top-1% 1 against 0 and best 157.8 against 151.4. Mixed: a lower average and a better top lineup. The cap-45 top-1%
lineup was a Burrow stack (Burrow, Chase, Higgins, Flowers, with Tony Pollard's 38 from a yellow-capped slot): CIN was the best stack in both
sets (control 12 lineups at 126.6, model 17 at 121.4). The higher cap bought 2.4 points of projection that went the
wrong way this week.

**Recommendation:** no case this week for cap 45 or for pool mode. Keep the model set as the entry. One slate is
noise (week6_prep 9.1), and week 7 also had a negative projection-to-result correlation, which punishes any setting
that leans harder on projections. Whether the control and pool sets keep running in week 8 is Doug's call; they cost
two optimizer runs and nothing else.

## 3. Doug's reads

Per player from `weeks/2026-w07/reads_players.csv`. As lineups, the optimizer re-run as entered reproduces the
uploaded 150 exactly (150 of 150 lineups identical), then once per read with only that read changed. Scored on actual
points and ranked against the real field:

| Run (150 lineups) | Avg | Top 10% | Top 1% | Best | Best rank | Same lineups as entered | Read worth (pts / lineup) |
|---|---|---|---|---|---|---|---|
| As entered | 100.9 | 11 | 0 | 151.4 | 9,356 | 150 | |
| Red removed | 102.5 | 17 | 0 | 151.2 | 9,514 | 1 | **-1.6** |
| Yellow removed | 105.7 | 23 | 2 | 162.6 | 3,040 | 10 | **-4.8** |
| Kyren minimum removed | 101.7 | 8 | 2 | 162.0 | 3,217 | 52 | -0.8 |
| Shadow greens added (boost mode) | 101.2 | 14 | 3 | 168.8 | 1,562 | 15 | +0.3 |
| McCaffrey not a stack receiver | 101.2 | 17 | 1 | 157.0 | 5,425 | 18 | -0.3 |
| Mumpfield red | 101.7 | 10 | 1 | 162.0 | 3,217 | 39 | -0.8 |
| Godwin yellow (cap 1, as before Doug cleared it) | 102.2 | 15 | 1 | 179.1 | 471 | 63 | -1.3 |

"Read worth" = as entered minus without the read (applied reads), or with it minus as entered (shadow). The
repo's `analyze_results.py` stopped at the shadow-green run: adding all 57 greens under the floor rule asks for 185
forced QB lineups out of 150 (nine green QBs at 12-28 each), and `optimize.assign_forced` fails with "pop from empty
list". The run above uses `green_mode = "boost"` (nothing forced; green players' value x 1.15) instead. The other
read runs were done in a scratch script (same code, nothing in `weeks/` rewritten). Every run that changes lineups
reshuffles most of the 150, so differences of a point or two and top-1% counts of 0-3 are mostly noise
(week6_prep 9.1).

### Red (applied): -1.6 a lineup

105 reds, 102 on the slate (47 RB, 33 WR, 9 QB, 7 TE, 6 DST). The 100 with a result row: projected 4.9, scored 4.4,
64 below projection, 1.1% owned on average. As a group the reds were right; most were depth players the model would
not have used. **What cost us were the few that hit:**

| Red | Pos | Proj | Pts | Field own | Prelim lineups |
|---|---|---|---|---|---|
| Malik Willis | QB MIA | 12.7 | 26.0 | 0.7% | 1 |
| Omar Cooper Jr. | WR NYJ | 7.2 | 23.0 | 4.1% | 6 |
| Quinshon Judkins | RB CLE | 13.2 | 22.9 | 2.9% | 0 (was Q) |
| Mason Taylor | TE NYJ | 5.3 | 22.7 | 0.1% | 0 |
| KC Concepcion Jr. | WR CLE | 7.2 | 22.2 | 1.8% | 5 (in the winning lineup) |
| Cam Skattebo | RB NYG | 10.9 | 21.6 | 1.5% | 8 |
| Caleb Douglas | WR MIA | 7.3 | 20.0 | 0.5% | 0 (was Q) |
| Blake Corum | RB LAR | 9.1 | 16.6 | 2.2% | 0 |

The red DSTs were right: Titans 5.0 (34% owned, the field's top DST; 25 prelim lineups), Dolphins 4.0 (24 prelim).
Red has now been +1.4 (week 6) and -1.6 (week 7) on its own; weeks 4-5 were graded together with yellow.

### Yellow (applied): -4.8 a lineup

34 players: projected 8.9, scored 9.8, only 19 of 34 below projection. The yellow caps were wrong this week, mostly
on QBs and Pollard:

| Yellow | Cap | Our lineups | Proj | Pts |
|---|---|---|---|---|
| Bo Nix (QB DEN) | 4 | 3 | 15.3 | **26.2** |
| Geno Smith (QB NYJ) | 3 | 1 | 14.5 | **24.5** |
| Deshaun Watson (QB CLE) | 2 | 0 | 15.6 | **22.2** |
| Michael Penix Jr. (QB ATL) | 4 | 4 | 15.7 | **20.4** |
| Tyler Huntley (QB BAL) | 6 | 6 | 17.0 | 16.1 |
| Daniel Jones (QB IND) | 1 | 1 | 14.0 | 4.6 |
| Jameis Winston (QB NYG) | 0 | 0 | 12.3 | 6.4 |
| Tony Pollard (RB TEN) | 4 | 4 | 9.3 | **38.0** (slate's top scorer) |
| Ollie Gordon II (RB MIA) | 8 | 8 | 11.0 | 19.8 |
| Pierre Strong Jr. (RB GB) | 12 | 12 | 11.3 | **0.0** (see section 4) |
| Jameson Williams (WR DET) | 7 | 7 | 11.0 | 23.6 |
| Buccaneers DST | 1 | 1 | 5.4 | **27.0** |
| Panthers DST | 6 | 6 | 6.7 | -4.0 |

QB fades: right on 3 of 7 this week (Jones, Winston, and Huntley just under projection), wrong on 4 (Nix, Smith,
Watson, Penix); Daniels did not start. Over two weeks they are 8 right and 5 wrong, and every wrong one was a cheap QB on a team the field ignored (1-3% owned). The skill-player
yellows were mixed (Boston, K. Allen, Downs, W. Robinson, Otton right; Pollard, J. Williams, Gordon wrong).

### Green: Kyren's forced minimum (applied) and the shadow greens

**Kyren Williams (forced min 15):** projected 17.8, scored 17.1, 20.5% owned. He was in 30 of 149 lineups, which the
model would have chosen anyway: the minimum never bound. Taking it out changed 98 lineups by reshuffle: -0.8 a lineup
for the read, 11 top-10% against 8, but 0 top-1% against 2. Call it neutral; he did his job.

**Shadow greens (57, record only):** projected 13.7, scored 11.9, 36 of 57 below projection. The busts were the
chalk: LaPorta 2.3 (13.7% owned), Nico Collins 1.6, Coker 1.4 (36%), Aaron Jones 3.1, McMillan 6.0, Likely 2.2 (20%),
Watson 8.2 (28%), Golden 6.9 (40%). The hits were CIN and the cheap WRs: Higgins 26.8, Flowers 26.7, Irving 26.5, Tucker
21.8, Burrow 28.9, McBride 25.1. Added in boost mode they were worth +0.3 a lineup with 3 top-1% lineups (best 168.8,
rank 1,562), mostly reshuffle. The floor version cannot be built (185 QB lineups forced).

### The SF stack with McCaffrey as a stack receiver

All 16 SF lineups were Purdy + McCaffrey + Kittle: average **90.6**, best 123.5, none in the top 10%. McCaffrey did his
part (19.0 on 18.7 projected; 7 targets, 61 yards); Purdy (14.0 on 20.7) and Kittle (10.8 on 14.1) didn't. Without the
read SF has no stack (Kittle was its only usable receiver), so its lineups go to other teams. Re-run that way: 101.2 a lineup, 17 top-10% against 11, 1 top-1%: the read was
worth **-0.3**, within the noise. The receiver idea worked; the SF game didn't.

### Mumpfield as the LAR stack receiver

Mumpfield scored **2.0** (projected 6.1): 2 targets on 43% of snaps. Nacua, held out as questionable, played and scored
17.8 on 10 targets. LAR stacks still did well (16 lineups, 109.8, sixth-best stack) on Stafford 18.5 and Kyren 17.1. The
11 LAR stacks with Mumpfield averaged 108.9, the 5 without him 111.9. Overall he was in 28 model lineups (104.7, above
the set average because they were mostly LAR stacks). Re-run with Mumpfield red again: model 101.7 a lineup (read worth **-0.8**), 10 top-10%, 1
top-1%; pool without him (the pool re-run reproduces the built pool exactly) 96.8 (read worth **-0.6**), 5 top-10%.
Small and against the read in both sets; the real cost was Nacua being held out.

### Godwin replacing Egbuka

Godwin scored **4.7** (projected 8.8, of which 1.9 from Egbuka being out), 11.3% owned. He had 5 targets on 73% of
snaps, but Tampa threw only 11 passes (Mayfield 7 of 11 for 64 yards; Irving 24 carries; Bucs DST 27). His 27 model
lineups averaged 96.0, the other 122 averaged 102.2; in the pool he was at 45 lineups (92.2). Re-run with his yellow (cap 1) restored: model 102.2 a lineup (read
worth **-1.3**), 15 top-10%, best 179.1 (a reshuffle). Pool with Egbuka's slot left empty: 98.7 (read worth
**-2.5**), 6 top-10%. Wrong in both sets; the pool felt it more because he was at 45.

### Harrison's trade read (share 0.15 x factor 0.7 = 10.5% of Houston targets)

| | Read / applied | Week 6 (@JAC) | **Week 7 (vs NYG)** | Two HOU games |
|---|---|---|---|---|
| Target share | 0.15 x 0.7 = 0.105 | 0.125 (4 of 32) | **0.143 (4 of 28)** | 0.133 (8 of 60) |
| Snaps | | 12 (19%) | **13 (21%)** | 25 (~20%) |
| Rec / yds / TD | | 3 / 34 / 0 | 1 / 6 / 1 | |
| Air-yards share | | 18.7% | 35.7% | |
| FanDuel pts | | 4.9 | **7.1** (projected 5.7) | |

Targets, snaps and air yards from nflverse week-7 player stats and snap counts. **The share read was right and the
factor slightly low:** 14.3% of targets against 10.5% applied, and two games average 13.3%. **But his snaps did not
grow** (19%, then 21%; Collins 67%, Hutchinson 56%, Noel and Boutte 31%): he gets a target on about a third of his
snaps, a rate that only holds while he is a part-time deep option. He was in 20 of the 149 lineups (95.9 average; 17 of
them HOU stacks). Houston stacks were our biggest and among our worst (29 lineups, 93.1): Stroud 16.5,
Collins 1.6, Schultz 7.0.

## 4. New this week: salary floor, role guard, WR implied-total correction

### Salary floor ($59,000, relief to cap + 3)

It did what it was meant to. **No lineup left $3,000 or more** (week 6: 14). Salaries ran $59,000-60,000, average
$59,793; 51 lineups spent exactly $60,000 and 2 left $1,000. The cost: **19 lineups used cap relief, and 21 players
ended above the 27 cap** (12 of them at 30: Hubbard, Golden, McCaffrey, LaPorta, Watson, McMillan, A. Jones, Browns
DST, Kyren, Higbee, Coker, Tucker). In the week-6 test only 14 lineups needed relief and no one passed 28. With so many
reads, relief is part of most late lineups, so cap 27 behaved like cap 30 for the most-used players, and most of them
busted. Every attempt the floor could not meet even with relief (21) was a stack team that could no longer be built,
which the allocation then moved to another team; no lineup was built below the floor.

### Role guard (WR/TE under 3 targets + carries a game, or no 2026 data, project 0)

247 players were zeroed (144 with no 2026 data, 103 under the role floor). Of the 216 with a result row, **179 scored 0
and they averaged 0.7 points.** Two reached 10: Davis Allen (LAR TE, 16.0, 0.06% owned) and Tez Johnson (TB WR, 11.7,
0.8%). Nobody the guard removed was a real miss. Players just above the floor scored as you would expect from part-timers
(Harrison 7.1, Mumpfield 2.0, Noel 0.7).

### Zero-scorers in our lineups

14 of the 149 lineups had a non-DST player score 0. None of them were players the guard should have caught:

| Player | Lineups | Proj | Why 0 |
|---|---|---|---|
| **Pierre Strong Jr.** (GB RB, yellow) | 12 | 11.3 | **Josh Jacobs came back and was not in our player file.** Jacobs: 11 carries + 7 targets on 52% of snaps, 17.6 pts, 3.5% owned. Strong: 8 snaps, no touches. RBs are outside the role floor, and Strong had real volume (13 a game). |
| Cade Otton (TB TE, yellow) | 2 | 6.6 | 89% of snaps; Tampa threw 11 passes, 1 target. Game script, not role. |

DSTs: Cardinals 0 (4 lineups), 49ers -1 (5), Panthers -4 (6).

**Jacobs, and the stale player file.** `data/2026-w07/fd_players.csv` is the Oct 19 download and was never
refreshed. The checklist said "re-download if FanDuel updated it", and nobody checked. FanDuel added at least Jacobs
($6,800), Christian Kirk (3.3% owned, 0 pts), Dylan Sampson and Jonah Coleman after Oct 19. With Jacobs missing, Strong
was GB's RB1 at 11.3 and filled the 12-lineup yellow cap. Fix for week 8: re-download the player list on Friday and on
Sunday morning and compare it with the previous one (new names, status changes) before the final run.

### WR implied-total correction (WR mean x (1 - 0.34 x (implied / 22.5 - 1)))

Neutral this week. Over 59 WRs projected above 0 the corrected projections had bias +1.51 and RMSE 6.70; without the
correction, +1.55 and 6.70; r 0.539 both. By team total it helped at the top and hurt at the bottom:

| Team implied total | WRs | Corrected (used) | Uncorrected | Actual |
|---|---|---|---|---|
| under 21 | 23 | 7.3 | 6.8 | 5.4 |
| 21-24 | 18 | 8.9 | 9.0 | 7.6 |
| 24+ | 18 | 9.8 | 10.4 | 8.6 |

One slate; keep it on as Doug set it.

### Questionable players held out without redistribution

Of the 8 held out as questionable, 3 played (Nacua 17.8, Waddle 6.8, Mike Washington Jr.) and 5 sat. Two of the five
that sat handed their work to backups the model had at their normal projection: **Breece Hall out, Braelon Allen 17
carries + 7 targets, 19.4 pts (projected 8.7, 21% owned, 5 lineups); Tyjae Spears out, Tony Pollard 38.0 (projected
9.3, yellow).** The field priced in both absences. Holding the Q player out was fine; not passing on any of his
volume was not. See the week-8 list.

## 5. Calibration, stacks, DST, ownership

### Calibration

Skill players projected above 0 (with a result row): n 165, r = 0.61 (0.74 with the zeros), bias +0.7, RMSE 6.7.

| Projected | n | Projected avg | Actual avg | Gap | Week 6 | Week 5 | Week 4 |
|---|---|---|---|---|---|---|---|
| 0-8 | 83 | 4.5 | 4.2 | +0.3 | +0.8 | +0.3 | |
| 8-14 | 43 | 10.7 | 9.8 | +0.9 | +2.0 | +2.2 | +1.8 |
| 14-20 | 34 | 16.2 | 15.2 | +1.0 | +2.6 | +1.6 | +2.8 |
| 20+ | 5 | 21.9 | 17.2 | +4.7 | +7.8 | +4.9 | +6.3 |

The best-calibrated week yet in the middle tiers. **9.8% of players projected 8+ beat their 90th percentile (10%
expected)**, the first week the ceilings were right. The 20+ five were Gibbs 23.3 / 17.8, Bijan 22.6 / 14.7, Goff
22.1 / 21.0, Purdy 20.7 / 14.0, Stafford 20.7 / 18.5: over again, a fourth week, smaller this time. By position
(projected 8+): QB 16.7 / 16.7 (r 0.27), RB 13.3 / 12.9 (r 0.12), WR 12.1 / 9.9 (r 0.53), TE 12.6 / 9.1 (r 0.43). The
means are close; the rank order inside RB and QB was weak, and that is what the lineup scores followed.

### Stacks (entered 149)

| Stack | Lineups | Avg | Best | Top 10% | QB | QB proj | QB pts | QB field own | Weight |
|---|---|---|---|---|---|---|---|---|---|
| CIN | 17 | 121.4 | 151.4 | 5 | Burrow | 19.8 | 28.9 | 4.7% | 18 |
| ATL | 4 | 117.1 | 131.5 | 1 | Penix (yellow) | 15.7 | 20.4 | 1.8% | 16 |
| BAL | 6 | 114.8 | 131.4 | 1 | Huntley (yellow) | 17.0 | 16.1 | 1.1% | 12 |
| LV | 11 | 111.6 | 127.5 | 0 | Cousins | 17.3 | 20.4 | 3.2% | 13 |
| LAR | 16 | 109.8 | 138.6 | 1 | Stafford | 20.7 | 18.5 | 5.1% | 20 |
| GB | 14 | 108.9 | 143.3 | 2 | Love | 19.3 | 18.0 | 31.7% | 20 |
| DET | 18 | 100.0 | 126.8 | 0 | Goff | 22.1 | 21.0 | 9.6% | 27 |
| HOU | 29 | 93.1 | 132.2 | 1 | Stroud | 19.2 | 16.5 | 12.0% | 21 |
| SF | 16 | 90.6 | 123.5 | 0 | Purdy | 20.7 | 14.0 | 7.1% | 21 |
| NYJ | 1 | 88.0 | 88.0 | 0 | G. Smith (yellow) | 14.5 | 24.5 | 1.8% | 11 |
| DEN | 3 | 84.3 | 86.5 | 0 | Nix (yellow) | 15.3 | 26.2 | 2.9% | 15 |
| MIN | 9 | 78.8 | 96.7 | 0 | Murray | 16.6 | 13.9 | 3.6% | 16 |
| IND | 1 | 75.9 | 75.9 | 0 | D. Jones (yellow) | 14.0 | 4.6 | 0.2% | 3 |
| CAR | 4 | 63.3 | 76.9 | 0 | Young | 18.8 | 7.4 | 8.1% | 16 |

Stack count against average: r = +0.33. The top 1,000 field lineups were built on Burrow (39%), Goff (18%), Love (10%),
Nix (6%), Stafford, Cousins, Watson (4% each) and Huntley (3%). CIN was right and we had 17 (its weight share). The
**Lamar-out line move** (BAL 27.0 -> 21.8, weight 22 -> 12) cost little: the 6 Huntley lineups averaged 114.8. HOU was
our heaviest stack because Harrison's starter override and the extra receivers made it the easiest to build, not
because of its weight (21, the same as SF). MIN (Murray + Aaron Jones + Jefferson, 9 lineups) was poor: Jordan Mason
took the backfield (64% of snaps to Jones's 25%) in his first game back.

### DST

r = -0.09 (weeks 4-6: 0.24, 0.11, 0.11). Our lineups averaged 4.2 DST points, the field 5.4. The Buccaneers scored 27
(projected 5.4, yellow cap 1, 1 lineup, 3.6% owned) and were in the winning lineup. Our Browns (30 lineups) scored 5.
Four weeks of DST r at 0.24 or lower: the flat projection is still as good as anything else we have.

### Ownership vs exposure

Ownership model across skill players: mean error 1.5 points against 3.1 for guessing the average, r = 0.74 (week 6: 1.3,
r 0.85). The same miss for the fourth week, mid-priced chalk:

| Player | Salary | Projected own | Actual own | Our exposure | Proj pts | Pts |
|---|---|---|---|---|---|---|
| Jahmyr Gibbs | 9,800 | 38% | 47% | 18% | 23.3 | 17.8 |
| Matthew Golden | 6,700 | 12% | 40% | 20% | 13.5 | 6.9 |
| Jalen Coker | 6,200 | 10% | 36% | 20% | 12.8 | 1.4 |
| George Kittle | 6,500 | 10% | 34% | 20% | 14.1 | 10.8 |
| Titans DST (red) | 3,200 | 5% | 34% | 0% | 6.8 | 5.0 |
| Jordan Love | 7,600 | 8% | 32% | 9% | 19.3 | 18.0 |
| Woody Marks | 6,200 | 6% | 28% | 1% | 12.4 | 8.6 |
| Christian Watson | 7,400 | 20% | 28% | 20% | 16.5 | 8.2 |
| Christian McCaffrey | 8,700 | 17% | 25% | 20% | 18.7 | 19.0 |
| Braelon Allen | 6,300 | 2% | 21% | 3% | 8.7 | 19.4 |
| Kyren Williams | 7,900 | 16% | 20% | 20% | 17.8 | 17.1 |
| Isaiah Likely | 5,500 | 5% | 20% | 20% | 11.0 | 2.2 |
| Chuba Hubbard | 7,100 | 15% | 18% | 20% | 16.1 | 8.0 |
| Tetairoa McMillan | 7,100 | 15% | 17% | 20% | 15.7 | 6.0 |
| Bijan Robinson | 9,400 | 42% | 16% | 19% | 22.6 | 14.7 |
| Tucker Kraft | 5,500 | 5% | 16% | 19% | 11.3 | 12.8 |

The chalk busted again: the 16 players owned 15%+ scored 11.0 against 15.0 projected, and we held 18-20% of most of
them (cap 27 plus relief = 30 of 149). The big scorers we were light on were cheap and low-owned: Pollard 38.0 (10%,
us 3%), Burrow 28.9 (5%, us 11%), Nix 26.2 (3%, us 2%), Willis 26.0 (red), McBride 25.1 (4%, us 8%), Geno Smith 24.5 (2%,
us 1%), J. Williams 23.6 (11%, us 5%), Cooper 23.0 (red), Mason Taylor 22.7 (red). Higgins (26.8), Flowers (26.7) and
Irving (26.5) we had at 14-19%.

## 6. Week-8 list

In priority order. Nothing changes until Doug and I decide.

1. **Player file refresh (process).** Re-download `fd_players.csv` on Friday and Sunday morning and compare it with the
   previous one: new players, salary and tag changes. Jacobs was missing all week (section 4). Cheap to add as a
   check that prints the differences.
2. **Josh Jacobs (GB).** Back from the exempt list with one game: 11 carries, 7 targets, 52% of snaps, 17.6 pts. Lloyd
   36%, Strong 12%. With one 2026 game, his usage blends one game with the 2025 prior; he likely needs a read
   (`[overrides]`), and Strong should drop out as GB's RB1 by himself once Jacobs is in the file.
3. **Harrison's share and factor (two HOU games).** Observed: 13.3% of targets over two games (12.5%, 14.3%) on ~20% of
   snaps. Options for Doug: keep `new_target_share = 0.15` with `first_week_factor` 0.9 (13.5%, matching what he has
   done), or factor 1.0 (15%) if he expects more snaps. His snaps did not grow from week 6 to 7, so I would use 0.9.
   Check his snaps on the week-8 practice / depth chart before raising further. After a third HOU game the HOU side can
   come from his own Houston usage and the trade entry can go.
4. **Arizona double count.** The trade's ARI side hands out his full blended ARI volume (about 2.2 targets a game to
   WR/TE; projections McBride +0.6, Wilson +0.9, Bourne +0.9, Virgil +0.6), but ARI's games since the trade already lack him:
   ARI threw 46, 34 and 44 targets in weeks 5-7 without him, against 37 a game with him (weeks 1-4). Weeks 5-6 were a
   quarter of week 7's usage sample (with the 2025 prior), so about a quarter of the bump was counted twice; with week 7
   added it is a third. Fix: hand out his ARI volume with `present_share` (as for
   injured players: only for the share of each teammate's sample he played in), or end the ARI side now that ARI has
   three games without him. Small (under a point across four players this week), but it grows every week it stays.
5. **Questionable players: pass on some volume.** Hall and Spears sat; their backups scored 19.4 and 38.0 on
   projections of 8.7 and 9.3, and the field had them at 21% and 10%. Proposal: for an uncertain Q held out of our
   lineups, still route his volume in the share of sims where he is zeroed (the 25% the sims already use), so the
   backup's ceiling shows. Built off, tested on weeks 5-7.
6. **Reads.** First week red and yellow were both negative (red -1.6, yellow -4.8). Two weeks of QB yellows: 8 right,
   5 wrong, and the wrong ones were all cheap QBs the field ignored. Yellow on a QB costs more than yellow elsewhere,
   because it removes whole stacks. Worth a talk before week 8's colours: perhaps yellow QBs only below a team total of
   about 21.
7. **TE in the flex (78%).** RB was -10.8 points this week. Week-6 prep found the TE flex comes from the RB1-only pool
   and TEs counting as stack receivers; a second RB per team earned nothing then. Re-test with weeks 4-7 (second RB
   eligible as flex only, or a flex-TE limit), reporting the four numbers.
8. **Cap relief.** 21 players passed the 27 cap (12 at 30). Options: relief +1 or +2 instead of +3, or relief only
   for players not already at cap + 1. Doug's call; the week-6 test gave relief its edge with only 14 lineups using it.
9. **Cap 45 control and pool sets.** Section 2: pool -1.9 against the control, control -2.9 against the model, one
   top-1% lineup for the control. Continue as shadow sets or stop: Doug decides.
10. **Shadow greens and `assign_forced`.** The grading crash: adding all shadow greens under the floor rule asks for
    more QB lineups than exist. Small fix: cap the forced QB lineups at the number of lineups, or grade shadow greens
    in boost mode, so `analyze_results.py` finishes.
11. **Existing backlog, unchanged:** per-position redistribution mode, depth-player boost cap, per-player random
    streams, zero-score risk, ownership signal, 149-lineup script, pool auto-raise on a stall.

## Files

- `data/2026-w07/results_*.csv` (untracked): from the export in `data/2026-w07/raw/`.
- `weeks/2026-w07/`: the final run (`upload.csv` 150, `entered_*_149.csv` as uploaded), `model_cap45/` (control),
  `pool/` (pool set, with `grade.csv` from `analyze_results.py`), `reads_players.csv`, and `reads_lineups.csv`: the section-3 re-runs (model and pool) from a scratch
  script with exact field ranks, since `analyze_results.py` stopped at the shadow-green re-run.
- `config/2026-w07/week.toml`: final config as entered, plus `[contest] field_size = 550210`.
