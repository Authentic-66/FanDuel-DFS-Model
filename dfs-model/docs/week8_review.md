# Week 8 review (Nov 2, 2026)

Graded from FanDuel's "All Entries" export (`data/2026-w08/raw/135859-281259493.csv`, converted with
`src/convert_results.py --user gst1999`), `analyze_results.py` and scratch scripts (exact ranks against all 566,416
entries; read re-runs in process, nothing in `weeks/` rewritten). Week-8 usage from nflverse player stats and snap
counts, downloaded Nov 2 (PHI@WAS Sunday night and CHI@SEA Monday night are off the slate). No week-8 entry history
file yet, so prizes per entry are not checked (see Money).

| | Pooch Punt ($0.05) |
|---|---|
| Entries | 566,416 |
| Winner | 258.38 (Burrow, Chase, Higgins, M. Wilson, Tuten, Braelon Allen, Pollard, Gesicki, Jaguars DST) |
| Field average / median | 120.2 / 118.7 |
| Top-10% / top-1% cutoff | 159.60 / 196.48 |
| Cash line | about 120 points (estimated; 39 of our 149 cashed) |
| Mine | 149 model lineups (`entered_upload_149.csv`, entered unchanged: all 149 matched) + 1 free entry (Doug's own) |

**Bottom line: a one-quarterback slate, and we were at the field's weight on that quarterback, not above it.** Joe
Burrow scored 45.5 and was in **983 of the top 1,000 lineups**. Our 15 CIN stacks averaged 167.8 and held all 10 of our
top-10% lineups (best 190.4, rank 8,591, top 1.5%). The other 134 lineups averaged 100.1, and the set averaged 106.4
against the field's 120.2 (-13.8). Burrow was 13.2% owned; we had him in 10.1% of lineups (his stack weight share).
Nothing reached the top 1%.

**Money: week 8 net -$2.88.** Won **$4.57** (Doug) on $7.45 of fees (149 paid + 1 free). Running total since week 4:
**-$6.53** (week 4 +$2.35, week 5 -$4.74, week 6 -$1.49, week 7 +$0.23, week 8 -$2.88). Check: the week-7 payout
tiers applied to our week-8 ranks give $4.52, so $4.57 is consistent (the tiers moved a little with the bigger field).
If there were other entries this week (week 7 had two Hail Mary entries), the net changes.

## 1. Model lineups vs the field

| | Week 8 | Week 7 | Week 6 | Week 5 | Week 4 |
|---|---|---|---|---|---|
| Model average | 106.4 | 101.1 | 104.5 | 108.5 | 111.3 |
| Field average | 120.2 | 103.3 | 110.7 | 131.2 | 107.3 |
| Difference | **-13.8** | -2.2 | -6.2 | -22.7 | +4.0 |
| Best lineup | 190.38 | 151.38 | 158.40 | 184.86 | 178.72 |
| Best rank | 8,591 (top 1.5%) | 9,356 (1.7%) | 3,975 (0.70%) | 10,705 (1.9%) | 1,054 (0.18%) |
| Lineups in top 1% | 0 | 0 | 1 | 0 | 4 |
| Lineups in top 10% | 10 | 11 | 8 | 3 | n/a |
| Lineups above field median | 42 of 149 | 77 | 58 | 29 | n/a |
| Winning score | 258.38 | 228.78 | 189.96 | 247.58 | 216.98 |
| Winnings / net $ | $4.57 / -$2.88 | $8.18 / +$0.23 | $5.96 / -$1.49 | $3.11 / -$4.34 | +$2.35 net |
| Running total since week 4 | **-$6.53** | -$3.65 | -$3.88 | -$2.39 | +$2.35 |

Other counts: 6 in the top 5%. Projected lineup average 120.1 (the field scored exactly that). **Projected and actual
lineup scores correlated +0.28** (week 7 -0.23). The free entry (Prescott / Henry / Stevenson / Lamb / Higgins /
Cooper) scored 111.7, rank 334,401, better than 88 of the 149. The 150th model lineup, dropped for the free entry,
would have scored 80.4.

Where the 13.8 points went, by roster position (field = ownership-weighted average lineup):

| Position | Field pts | Our pts | Field slots | Our slots |
|---|---|---|---|---|
| QB | 20.7 | 18.5 | 1.00 | 1.00 |
| RB | 43.3 | 30.7 | 2.66 | 2.21 |
| WR | 36.6 | 34.9 | 3.20 | 3.15 |
| TE | 11.0 | 14.1 | 1.10 | 1.64 |
| DST | 8.2 | 8.3 | 1.00 | 1.00 |

**Running back again: -12.6 points, the fourth week in a row** (week 7 -10.8). Flex was TE in 95 of 149 lineups (64%),
RB 32, WR 22; control and pool the same (66%). The field's RB points came from Tuten 31.9 (19% owned, us 7%),
Braelon Allen 25.3 (25%, red), Pollard 30.2 (10%, us 14%) and Gibbs 26.8 (22%, us 17%); our most-used RBs were
Jonathan Taylor 4.7 (13%), Hampton 3.7 (11%), Javonte Williams 6.2 (17%) and Stevenson 10.5 (17%).

## 2. All four sets

Same projections, sims, reds, salary floor and stack weights in the three built sets. Exact ranks against all 566,416
entries. "Money as-if" = the week-7 payout tiers ($0.10 to about rank 272k, $0.12 to 65k, $0.15 to 21k, $0.25 to 10k)
applied to each set's ranks; payouts above the $0.25 tier are unknown, so a lineup ranked above about 9,900 is counted
at $0.25 (a floor).

| Set | Lineups | Avg | Proj avg | Top 10% | Top 1% | Best | Best rank | Cashed | Money as-if | Same lineups as model |
|---|---|---|---|---|---|---|---|---|---|---|
| **Model cap 25 (entered 149)** | 149 | **106.4** | 120.1 | **10** | 0 | 190.4 | 8,591 | 39 | $4.52 (actual $4.57) | |
| Model, all 150 | 150 | 106.3 | 120.0 | 10 | 0 | 190.4 | 8,591 | 39 | $4.52 | 150 |
| Control: model cap 45 | 150 | 107.4 | 121.1 | 13 | 0 | 190.7 | 8,435 | 41 | $4.91 | 103 |
| Doug's pool (cap 25) | 150 | **108.0** | 120.1 | **17** | **1** | **197.1** | **5,264** | 44 | $5.32+ | 11 |
| Doug's free entry | 1 | 111.7 | 113.4 | 0 | 0 | 111.7 | 334,401 | 0 | $0 | |
| Field | 566,416 | 120.2 (median 118.7) | | | | 258.4 | | | | |

(`weeks/2026-w08/pool/grade.csv` has the same averages and counts; its best ranks are estimated from the top 2,000 and
the field quantiles.)

**The pool was the best set this week, the first time.** Pool vs model (both cap 25): +1.5 a lineup, 17 top-10% against
10, one top-1% lineup (Burrow, Chase, Higgins, Tuten, Bowers, Wan'Dale Robinson, Hampton, Strange, Patriots DST:
197.1). Nearly all of it is the CIN stacks: pool 16 at 176.0 (all 16 in the top 10%), model 15 at 167.8 (10). The pool
also had LV 8 at 133.3 (Bowers 24.7 at 15% vs our 11%) and no Geno Smith (5% of model lineups).
**Cap 45 vs cap 25 (control vs model): +1.2**, 13 top-10% against 10, same best. Two weeks now: pool vs control -1.9,
+0.6; cap 45 vs cap 27/25 -2.9, +1.2. Both flip sign week to week: noise so far. Pool review is due after week 9.

### Stacks (entered 149)

| Stack | Lineups | Avg | Best | Top 10% | QB | QB proj | QB pts | QB own | Weight |
|---|---|---|---|---|---|---|---|---|---|
| CIN | 15 | **167.8** | 190.4 | 10 | Burrow | 22.0 | **45.5** | 13.2% | 27 |
| NE | 8 | 123.4 | 147.9 | 0 | Maye | 20.0 | 22.5 | 7.2% | 17 |
| MIN | 5 | 120.5 | 151.3 | 0 | Murray | 15.6 | 20.9 | 3.2% | 12 |
| LV | 6 | 116.2 | 132.3 | 0 | Cousins | 17.6 | 28.2 | 3.6% | 13 |
| BUF | 15 | 114.9 | 145.5 | 0 | J. Allen | 24.0 | 27.6 | 11.9% | 26 |
| NYJ | 8 | 109.7 | 151.4 | 0 | Geno Smith (cleared) | 16.0 | 19.0 | 3.6% | 16 |
| IND | 2 | 106.6 | 111.0 | 0 | D. Jones | 13.5 | 8.5 | 0.2% | 5 |
| ARI | 8 | 106.4 | 125.8 | 0 | Brissett | 18.0 | 4.5 | 10.1% | 16 |
| LAR | 10 | 103.0 | 132.7 | 0 | Stafford | 20.6 | 9.3 | 2.8% | 20 |
| DAL | 18 | 102.7 | 128.8 | 0 | Prescott | 21.3 | 19.8 | 18.2% | 30 |
| KC | 5 | 96.7 | 113.5 | 0 | Mahomes | 17.2 | 28.4 | 1.0% | 11 |
| JAC | 13 | 95.0 | 109.6 | 0 | Lawrence | 20.1 | 19.4 | 10.4% | 25 |
| DET | 9 | 93.1 | 118.4 | 0 | Goff | 20.6 | 10.0 | 2.2% | 18 |
| PIT | 5 | 87.8 | 113.4 | 0 | Rodgers (cleared) | 16.4 | 5.9 | 0.7% | 10 |
| CLE | 1 | 81.7 | 81.7 | 0 | Watson | 15.0 | 14.2 | 0.4% | 3 |
| ATL | 4 | 75.6 | 90.3 | 0 | Penix (cleared) | 15.2 | 2.1 | 1.2% | 9 |
| BAL | 10 | 67.3 | 84.2 | 0 | Lamar | 18.7 | **0.0** | 5.6% | 20 |
| TB | 7 | 65.4 | 97.7 | 0 | Mayfield | 14.6 | 1.4 | 1.3% | 14 |

Top 1,000 field lineups by QB: Burrow 98.3%, Josh Allen 0.9%, Ward 0.3%. CIN's weight (27) was the second-highest
after DAL (30), and proportional allocation gave it exactly its share (15 of 149). DEN, LAC, MIA and TEN could not be
stacked (red receivers / QBs) and their 9 lineups went elsewhere.

**BAL and TB were the two worst stacks, both for reasons outside the projection.** Lamar threw one pass and left (1
snap); Huntley played 10 snaps, then third-stringer Joe Fagnano threw 21 passes for 91 yards. Flowers (27 lineups,
cap 25 + relief) caught 0 of 5. Tampa threw **3 passes** all game (Mayfield 60 snaps, 0 yards), after 11 in week 7:
Godwin (12 lineups) and Otton (8) scored 0.

## 3. Doug's reads: 113 red (5 cleared Sunday)

### All reds as a group

105 reds had a result row (the rest were out or off the list). **Projected 4.93, scored 4.96**: as a group the reds
scored exactly what the model expected, 63 of 105 below projection, 1.5% owned on average.

Against non-reds at the same position and salary band ($1,000 bands), counting only players projected 4+ (real
roles; below that both groups are mostly zeros): **reds 7.0 projected, 7.8 scored (+0.8); non-reds 8.4 projected, 9.3
scored (+0.9)**. The reds did no worse than comparable players; the read did not find busts as a group. By position
(all with a result row): QB 4.8 -> 9.0, RB 4.2 -> 4.1, WR 6.1 -> 5.4, TE 5.6 -> 6.3, DST 4.9 -> 6.0.

What matters for lineups is the reds the model wanted: the 40 that held prelim lineups (256 slots) projected 9.3 and
scored 8.5, prelim-weighted. Slightly right.

| Red the model wanted | Pos | Proj | Pts | Field own | Prelim lineups |
|---|---|---|---|---|---|
| Jordan Mason | RB MIN | 9.6 | 2.0 | 1.5% | 25 (right) |
| Jaylen Warren | RB PIT | 15.1 | **23.8** | 8.2% | 20 (wrong) |
| Braelon Allen | RB NYJ | 15.6 | **25.3** | 25.0% | 13 (wrong; Hall out, 21 carries, 147 yds) |
| Omar Cooper Jr. | WR NYJ | 9.5 | 0.0 | 15.2% | 12 (right; 78% of snaps, no catch) |
| Quentin Johnston | WR LAC | 7.7 | 5.7 | 0.4% | 11 (right) |
| Detroit Lions DST | DST | 6.2 | 6.0 | 20.9% | 11 (neutral) |
| Ryan Flournoy | WR DAL | 8.6 | 11.6 | 5.6% | 10 (wrong) |
| Germie Bernard | WR PIT | 9.3 | 5.5 | 14.9% | 9 (right) |
| Courtland Sutton | WR DEN | 8.0 | 7.3 | 0.9% | 9 (right) |
| Ja'Kobi Lane | WR BAL | 5.7 | 1.8 | 4.6% | 9 (right) |

Red hits the model would not have used much anyway: Cam Ward 29.3, Adonai Mitchell 26.7 (9 targets, 142 yds), Emmett
Johnson 25.8 (5 catches, 128 yds), Jonah Coleman 18.4.

**As lineups** (optimizer re-run as entered reproduces all 150 lineups exactly; then once per change):

| Run (150 lineups) | Avg | Top 10% | Top 1% | Best | Best rank | Same lineups as entered | Read worth (pts / lineup) |
|---|---|---|---|---|---|---|---|
| As entered | 106.3 | 10 | 0 | 190.4 | 8,591 | 150 | |
| No reds at all | 105.9 | 8 | 0 | 187.4 | 10,569 | 1 | **red +0.3** |
| The 5 cleared kept red | **108.8** | 12 | 0 | 190.4 | 8,591 | 71 | **clearing them -2.6** |
| Ward + Willis not red | 106.3 | 10 | 0 | 190.4 | 8,591 | 150 | **0.0** |

Red as lineups, weeks 5-8: +1.4 / +1.4 / -1.6 / **+0.3**. Small help this week.

### The 5 cleared Sunday: clearing them cost about 2.6 a lineup

| Cleared | Proj | Pts | Field own | Our lineups | Their lineups' avg |
|---|---|---|---|---|---|
| Aaron Rodgers (QB PIT) | 16.4 | 5.9 | 0.7% | 5 | 87.8 |
| Geno Smith (QB NYJ) | 16.0 | 19.0 | 3.6% | 8 | 109.7 |
| Michael Penix Jr. (QB ATL) | 15.2 | 2.1 | 1.2% | 4 | 75.6 |
| Bo Nix (QB DEN) | 14.8 | 19.3 | 0.5% | 0 (DEN could not be stacked) | |
| Keenan Allen (WR IND) | 9.4 | 10.2 | 1.3% | 9 | 105.6 |

**Doug's original reds were right on Rodgers and Penix** (their 9 stacks averaged 82.9), wrong on Geno Smith and Nix,
neutral on Keenan Allen. Re-run with all 5 still red: +2.6 a lineup, 12 top-10% against 10, same best. Most of the gain
is the PIT and ATL lineups going to other teams; 79 of 150 lineups change, so part of it is reshuffle.

### Ward and Willis (still red): no effect

The model would not have used either: TEN's stack weight was 1 (implied 16.0) and MIA's 3, Ward projected 10.2 and
Willis 13.6. With both un-red the optimizer builds the identical 150 lineups. Ward's 29.3 (40 attempts, 304 yds, 0.2%
owned; 0.3% of the top 1,000) was a miss for the model, not the read. Willis 15.6 on 13.6: as expected.

## 4. Late decisions (Sunday status calls)

**Q players cleared after inactives (1pm games, FanDuel tag cleared on the 10:37 list):**

| Player | Proj | Pts | Field own | Our lineups | Their avg |
|---|---|---|---|---|---|
| George Pickens (WR DAL) | 14.5 | 5.8 | 4.0% | 21 | 104.4 |
| Michael Wilson (WR ARI) | 12.3 | **25.8** | 18.8% | 27 | 112.1 |
| Dalton Kincaid (TE BUF) | 9.7 | **16.6** | 3.6% | 14 | 111.5 |
| Jakobi Meyers (WR JAC) | 8.9 | 3.4 | 0.9% | 10 | 89.8 |
| DJ Moore (WR BUF) | 8.6 | 14.6 | 6.7% | 7 | 99.1 |
| Tyler Allgeier (RB ARI) | 7.9 | **36.6** | 0.2% | 0 (ARI RB2; Love red) | |
| Jeremiyah Love (RB ARI, red) | 11.2 | 2.3 | 4.4% | 0 | |
| Ray Davis, LeQuint Allen, Ridley, Ian Thomas | 0-2.5 | 0-3.0 | 0% | 0 | |

All played. Across our lineups the five we used scored about +1.8 points a lineup above their projections (Wilson
and Kincaid made up for Pickens and Meyers). Taking them off the Q list was right; holding them out would have cost
Wilson's 27 lineups.

**4pm games, taken as active on FanDuel's cleared tag before inactives:** McConkey 10.6 (proj 7.3, 2 lineups), Kelce
9.2 (9.9, 8 lineups), Dulcich 6.3 (5.8, 2), Tre' Harris 4.6 (6.1, 0), Malik Washington 12.5 (red), Wayne 0 and Kacmarek
0 (0 lineups). **All active, none a zero in our lineups**; the 12 lineups holding one averaged 95.6 (mostly KC / LAC
stacks, which were poor for other reasons). The call was right.

**Kept Q (held out):** Gainwell 17.0 (red anyway), Waddle 13.4 (red anyway), Zaccheaus 0.9, Schoonmaker, Ogletree,
Geers, Parkinson, Whittington 0, DJ Rogers no result. Holding them out cost nothing.
**Moved to out:** all 10 scored 0 (Hall, Harvey, Henderson, A.J. Brown, Spears, Tate, Turpin, Gould, B. Thompson,
Skowronek). Jack Bech, taken off out, scored 0 (0.05% owned, not in our lineups).

**Lamar as BAL starter:** projected 18.7, scored **0.0** (1 snap, then out; Huntley -2.0 on 10 snaps, Fagnano 21
attempts). Our 10 BAL stacks averaged 67.3, the worst stack. The call was right on what was known (he was active and
started); the injury was not foreseeable. Without `[status.starting_qb] BAL` the model would have started Huntley,
who scored -2.0, so the alternative was no better.

## 5. Biggest misses and hits by exposure

Points per lineup against the field = (our exposure - field ownership) x (player's points - field's average at his
position). Negative = cost us. Sum over all players: -10.9 of the -13.8 (the rest is slot mix: more TE, fewer RB).

**Cost us most:**

| Player | Proj | Pts | Field own | Us | Pts / lineup |
|---|---|---|---|---|---|
| Tee Higgins (WR CIN) | 15.0 | 35.5 | 28.2% | 17.4% | **-2.6** |
| Braelon Allen (RB NYJ, red) | 15.6 | 25.3 | 25.0% | 0% | **-2.3** |
| Bhayshul Tuten (RB JAC) | 12.7 | 31.9 | 19.1% | 7.4% | **-1.8** |
| Jonathan Taylor (RB IND) | 16.7 | 4.7 | 1.7% | 12.8% | -1.3 |
| Omarion Hampton (RB LAC) | 10.6 | 3.7 | 0.9% | 10.7% | -1.2 |
| Jake Ferguson (TE DAL; hurt, 4 snaps) | 7.9 | 0.0 | 1.2% | 12.1% | -1.1 |
| Ja'Marr Chase (WR CIN) | 14.8 | 28.6 | 13.6% | 7.4% | -1.1 |
| DK Metcalf (WR PIT) | 11.6 | 0.9 | 3.8% | 12.8% | -1.0 |
| Jets DST | 6.1 | 0.0 | 2.9% | 14.1% | -0.9 |
| Joe Burrow (QB CIN) | 22.0 | 45.5 | 13.2% | 10.1% | -0.8 |

**Helped most:**

| Player | Proj | Pts | Field own | Us | Pts / lineup |
|---|---|---|---|---|---|
| Omar Cooper Jr. (WR NYJ, red) | 9.5 | 0.0 | 15.2% | 0% | +1.7 |
| Zay Flowers (WR BAL) | 16.2 | 0.0 | 29.9% | 18.1% | +1.4 |
| Javonte Williams (RB DAL) | 17.8 | 6.2 | 28.1% | 17.4% | +1.1 |
| Buccaneers DST | 6.8 | 18.0 | 6.8% | 16.8% | +1.0 |
| Germie Bernard (WR PIT, red) | 9.3 | 5.5 | 14.9% | 0% | +0.9 |
| Brock Bowers (TE LV) | 16.1 | 24.7 | 5.1% | 10.7% | +0.8 |
| Jacoby Brissett (QB ARI) | 18.0 | 4.5 | 10.1% | 5.4% | +0.8 |
| Hunter Henry (TE NE) | 9.4 | 4.5 | 21.2% | 9.4% | +0.6 |
| Tony Pollard (RB TEN) | 12.7 | 30.2 | 9.7% | 14.1% | +0.6 |

Reds in these tables net out: Braelon Allen -2.3 and Warren -0.6 against Cooper +1.7, Bernard +0.9 and Lions DST +0.5.
The week turned on CIN: Higgins, Chase and Burrow together cost 4.5 a lineup because we were under the field on all
three. The chalk (15%+ owned) scored 14.6 on 15.5 projected, close this week (week 7 11.0 on 15.0).

**Zero-scorers:** 75 of 149 lineups held a non-DST player who scored 0 (week 7: 14). Flowers 27 lineups (BAL QB
injuries), Tre Tucker 25 (1 target on 54% of snaps), Ferguson 18 (hurt after 4 snaps), Godwin 12 and Otton 8 (TB threw
3 passes), Lamar 10, Engram 5, TeSlaa 2. Mostly game events, not role errors: Tucker is the only one the role data
could have flagged, and he had 12 targets in week 7.

**Ownership model:** mean error 1.2 points against 2.8 for guessing the average, r = 0.80 (week 7 1.5, r 0.74).
Under-predicted again: Henry 3.8% vs 21%, Lions DST 4.6% vs 21%, Tuten 5% vs 19%, M. Wilson 6.7% vs 19%, Higgins 13% vs
28%, Flowers 16% vs 30%.

## 6. Calibration (flags only, no changes this week)

Skill players projected above 0 with a result row: n 180, r = 0.55 (0.70 with the zeros), bias +0.7, RMSE 7.6.

| Projected | n | Projected avg | Actual avg | Gap | Week 7 | Week 6 | Week 5 |
|---|---|---|---|---|---|---|---|
| 0-8 | 89 | 4.6 | 4.5 | +0.1 | +0.3 | +0.8 | +0.3 |
| 8-14 | 48 | 10.4 | 9.6 | +0.8 | +0.9 | +2.0 | +2.2 |
| 14-20 | 33 | 16.3 | 13.7 | **+2.5** | +1.0 | +2.6 | +1.6 |
| 20+ | 10 | 21.1 | 20.8 | **+0.3** | +4.7 | +7.8 | +4.9 |

The 20+ tier was right for the first time (Burrow 45.5 and Allen 27.6 offset Goff 10.0, Stafford 9.3, Bijan 7.6).
7.7% of players projected 8+ beat their 90th percentile (10% expected; week 7 9.8%).

By position (projected 8+): QB 17.3 / 16.4 (r 0.26), RB 14.5 / 12.9 (r 0.22), WR 11.5 / 9.7 (r 0.31), TE 11.1 / 10.4
(r 0.56). DST r 0.40 (6.0 projected, 6.9 scored), the best DST week yet.

Flags (each one slate; nothing changes until Doug and I decide, and any change gets a history test first):

1. **WR over-projection, second week.** WRs projected 8+: 11.5 vs 9.7 (week 7 12.1 vs 9.9). The WR implied-total
   correction helped this week (bias +1.19 corrected vs +1.38 without, RMSE 7.17 vs 7.23), but the top band is still
   high two weeks running: team total 24+ WRs 10.6 projected, 9.0 scored (week 7 9.8 vs 8.6). Points at a stronger WR
   correction or a WR-level shrink; worth a history test, not a change.

   | Team implied total | WRs | Corrected (used) | Uncorrected | Actual |
   |---|---|---|---|---|
   | under 21 | 24 | 7.1 | 6.7 | 6.2 |
   | 21-24 | 16 | 8.4 | 8.5 | 7.4 |
   | 24+ | 22 | 10.6 | 11.5 | 9.0 |

2. **Routing bumps ran high.** The 26 players raised 1+ point by injury routing projected 10.1 and scored 8.3 (average
   bump 2.0). Biggest: Braelon Allen +5.4 (scored 25.3, right), Stevenson +4.1 (10.5), DeMario Douglas +3.2 (15.1),
   Ollie Gordon +3.1 (6.9), Dobbins +3.0 (1.3), Bijan +2.9 (7.6), Higbee +2.0 (1.9). Fits the backlog item "cap the boost
   to depth players". Q routing (bump 0.5+): 4 players, 9.9 projected, 8.3 scored.
3. **RB vs field, fourth week (-12.6) and TE flex 64%.** Same cause as before: RB1-only plus 60 red RBs leaves few
   RBs, and TEs count as stack receivers. The flex-TE cap is built and off. Worth looking at together with the
   per-position redistribution item.
4. **Spread: nothing to flag.** By the team's line, actual minus projected: favoured by 7+ +0.8, by 3-7 -1.7, pick'em
   +0.3, underdog by 3-7 -1.8, by 7+ -0.1. No direction (both sides of 3-7 over-projected, the extremes fine).
5. **14-20 tier +2.5** (week 7 +1.0, week 6 +2.6): the middle-high tier is still the most over-projected after the
   calibration slope. Driven this week by QBs (Goff, Stafford) and RBs (J. Taylor, Javonte Williams).
6. **Passing-volume collapses**: TB 3 attempts (11 in week 7), BAL QB injuries. Not a model rule; noted for week 9
   (TB's pass rate two weeks running).

## 7. Week-9 carry-overs

1. **Harrison**: share 0.15, factor 0.9 (Doug, Oct 26) in week 9 if HOU is on the main slate (HOU was on bye in week
   8). Remove the trade entry after ~3 Houston games.
2. **Josh Jacobs (GB)**: two games now. Week 7: 11 carries, 7 targets. Week 8 (Thursday): 21 carries, 6 targets (39
   rush yds, 6 catches for 13). He is GB's lead back; Doug's read before the week-9 run if GB is on the main slate.
3. **McCaffrey (SF)**: left week 7 injured, SF on bye in week 8. Check his status before the week-9 run.
4. **New**: Lamar (left after 1 snap; BAL starter call for week 9), Jake Ferguson (4 snaps), ARI QB (Minshew played
   42% of snaps after Brissett), TB's passing volume (3 and 11 attempts).
5. Pool review after week 9 (two weeks: pool vs control -1.9, +0.6; pool vs model -4.8 (week 7, cap 45), +1.5).
6. Existing backlog, unchanged: per-position redistribution, depth-player boost cap, per-player random streams,
   zero-score risk, ownership signal, 149-lineup script, pool auto-raise on a stall.
