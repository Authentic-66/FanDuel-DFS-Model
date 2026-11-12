# Week 9 review (Nov 9, 2026)

Graded from FanDuel's "All Entries" export (`data/2026-w09/raw/136184-281370292.csv`, converted with
`src/convert_results.py --user gst1999`), `analyze_results.py`, `learn_from_winners.py`, `max_entrants.py` and scratch
scripts (exact ranks and exact money against all 524,339 entries with the Pooch Punt prize table
`data/2026-w09/prizes_pooch-punt.csv`; every re-run in process, nothing in `weeks/` rewritten).

| | Pooch Punt ($0.05) |
|---|---|
| Entries | 524,339 |
| Winner | 215.58 (Love, K. Walker III, Javonte Williams, C. Watson, Golden, DeMario Douglas, Fannin, Jonah Coleman, Rams DST) |
| Field average / median | 113.5 / 113.0 |
| Top-10% / top-1% cutoff | 142.4 / 169.7 |
| Cash line | 112.6 (rank 265,100, the last paid place) |
| Mine | 149 lineups (100 median-70 + 49 model, `entered_upload_149.csv`) + 1 free entry (Doug's own) |

**Bottom line: the median-70 half sank the week.** The 49 model lineups averaged 109.4 and nearly broke even
(-$0.01); the 100 median-70 lineups averaged 100.7 and lost $2.41. Median-70 put ~70% exposure on three players who
busted together: Allgeier (5.6), Smith-Njigba (8.6) and Singletary (4.9). The full model, no-draw, cap-45 and pool
sets all cashed 39-43% (the entry 27.5%); median-70 was the worst set of the week. Best lineup 183.3 (GB stack, rank
1,201, top 0.23%).

## 1. Entries check

All 149 lineups in `entered_upload_149.csv` (the first build, before the Pickens rebuild) are in the export exactly
(compared as sets of 9 player Ids). The 150th entry is Doug's hand-built free entry. Nothing else.

## Money

The export's Won column: **149 lineups $5.03, free entry $0.10, total $5.13** (Doug wrote $5.12: one cent apart;
**Doug confirmed $5.13 from the export, Nov 12**). 41 of the 149 cashed. **Week 9 net (149 paid, $7.45): -$2.42. Running total since
week 4: -$8.95** (week 4 +$2.35, week 5 -$4.74, week 6 -$1.49, week 7 +$0.23, week 8 -$2.88, week 9 -$2.42).
The free entry goes in `docs/my_own_lineups.md` only (+$0.10).

## 2. Every set side by side (exact money as if entered; cash line 112.6)

Near 5 / near 10 = lineups that missed the cash line by under 5 / 10 points. Table saved in
`weeks/2026-w09/grade_all_sets.csv`.

| Set | Lineups | Avg | Cash rate | Won | Net | Near 5 / 10 | Top 10% | Top 1% | Best (rank) |
|---|---|---|---|---|---|---|---|---|---|
| **Entered 149** | 149 | 103.6 | 27.5% | $5.03 | -$2.42 | 17 / 39 | 7 | 1 | 183.3 (1,208) |
| - median-70 half | 100 | 100.7 | 23.0% | $2.59 | -$2.41 | 9 / 25 | 2 | 0 | 166.6 (8,699) |
| - model half | 49 | 109.4 | 36.7% | $2.44 | -$0.01 | 8 / 14 | 5 | 1 | 183.3 (1,208) |
| Median-70 150 | 150 | 101.1 | 24.0% | $3.96 | -$3.54 | 15 / 36 | 4 | 0 | 166.6 (8,699) |
| Model 150 (cap 25) | 150 | 108.7 | 38.7% | $7.40 | -$0.10 | 16 / 30 | 10 | 3 | 183.3 (1,208) |
| No-draw 150 | 150 | 109.6 | 43.3% | $7.57 | **+$0.07** | 7 / 24 | **14** | 2 | 174.2 (4,147) |
| Cap-45 150 | 150 | 109.3 | 41.3% | $6.64 | -$0.86 | 13 / 27 | 9 | 0 | 161.3 (14,546) |
| Pool 150 | 150 | **110.3** | 42.0% | $7.28 | -$0.22 | 11 / 32 | 8 | 2 | 181.2 (1,493) |
| Flex shadow 150 | 150 | 107.7 | 35.3% | $5.91 | -$1.59 | 16 / 30 | 11 | 0 | 166.4 (8,921) |
| Pickens-out 149 (not entered) | 149 | 101.7 | 25.5% | $4.43 | -$3.02 | 19 / 33 | 8 | 1 | 175.2 (3,896) |

Ranks in the last column are estimated from the top-2,000 file and field quantiles (1,208 vs the real 1,201); money
uses exact ranks against every entry. The Pickens-out rebuild shares 61 of 149 lineups with the entered set and would
have won $0.60 less: keeping the first upload was right. Its six sets: model 106.3, median-70 101.1, no-draw 109.0,
cap 45 106.1, pool 108.9, flex shadow 106.3.

Why median-70 lost: its 70% cap put Allgeier (71 of 100), Smith-Njigba (70) and Singletary (70) in most lineups.
They scored 5.6, 8.6 and 4.9 (projected 15.3, 21.1, 15.7). Both RBs were projections lifted by injured teammates
(routing bump +7.5 and +9.5), so they were not elite, but at 53% / 52% / 52% of the 149 none reached the 70% flag.
The model half spread its exposure (top player 12 of 49: Jacobs, who scored 0.5).

**Cap 45 vs 25:** 109.3 vs 108.7 avg, money -$0.76, top-1% 0 vs 3. **Flex shadow vs model:** -1.0 avg, -$1.49,
top-1% 0 vs 3. **Pool:** best average of the week (110.3), $7.28, 2 top-1%; in week 8 it was also the best set.

## Free entry (Doug's own, not in the totals)

128.7 (Goff 6.3, Gibbs 13.4, Allgeier 5.6, DeMario Douglas 15.7, Golden 30.4, Lamb 31.5, Likely 13.8, Kaelon Black 7.0,
Saints DST 5.0), rank 124,634 (top 24%), won $0.10. Beat 134 of the 149. Logged in `docs/my_own_lineups.md`.

## 3. Reds split by Doug's reasons

Lineups re-run in process as entered (both builds, recombined 100 + 49 exactly like `combine_entry`), with only one
group made eligible. "As entered" reproduces the entered 149 exactly. Saved in `weeks/2026-w09/red_split.csv`.

| Group | Players (proj / actual) | Proj | Actual | Diff |
|---|---|---|---|---|
| Role / news | Emanuel Wilson 10.1 / 0.0 | 10.1 | 0.0 | -10.1 |
| Matchup | Gordon 15.2 / 6.9, Jeanty 14.0 / 4.5, B. Allen 10.3 / 4.4, Hampton 9.6 / 6.0 | 12.3 | 5.5 | -6.8 |

All five scored under projection. The two QB reds (Darnold out, Brissett not starting) were status calls.

| Run (entered 149) | Avg | Cashed | Won | Top 1% | Best |
|---|---|---|---|---|---|
| As entered (all reds) | 103.6 | 41 | $5.03 | 1 | 183.3 |
| Role red removed (E. Wilson eligible) | 103.6 | 41 | $5.03 | 1 | 183.3 |
| Matchup reds removed (4 RBs eligible) | 102.5 | 35 | $4.39 | 1 | 178.4 |
| Both removed | 102.5 | 35 | $4.39 | 1 | 178.4 |

- **Role red: no effect.** Wilson would not have been picked anyway: Doug's SEA starter override made Charbonnet the
  RB1, and starters-only leaves Wilson out. He scored 0.
- **Matchup reds: +1.1 a lineup, +$0.64.** Without them Gordon would have been in 50 of the 149 (6.9 points), Jeanty 8
  and Hampton 3. In the model build alone they kept 2 extra top-1% lineups (3 vs 1).

## 4. Promotion kill-rule check (report only; decided after week 10)

Players promoted by the role guard with Proj 4+ (final proj.csv):

| Player | Team | Why promoted | Proj | Actual | Our lineups |
|---|---|---|---|---|---|
| Eli Raridon (TE) | NE | inherits, last 2 games, snaps 92% | 5.9 | 6.7 | 9 |
| Kyle Williams (WR) | NE | snaps 83% | 5.0 | 0.0 | 1 |
| Noah Gray (TE) | KC | snaps 54% | 4.1 | 1.6 | 0 |

**Week 9: 5.0 projected, 2.8 scored, -2.2 a player (n 3).** The kill rule (1.5+ under, weeks 9-10 combined) fires
unless week 10's promoted players come in over projection. All 12 promoted players: 3.7 projected, 2.1 scored.
Role-drop flags: Emanuel Wilson 0.0 (flag right), Lambert-Smith 5.5 (proj 3.3), Cody White 0.

## 5. Sunday status calls and notes

- **St. Brown taken active on news** (FanDuel still Q, 17 lineups): played, 12.6 (proj 16.2). Right call.
- **Pickens kept Q**: inactive. Right. Skattebo, H. Henry, D. Watson, J. Wright out on news: none played. Right.
- **Nabers active** (knee DNP, no tag): 6.8 on proj 14.6, 10 lineups.
- **QBs projected 0:** Shedeur Sanders 22.7 (Doug's call: no read, CLE 0 stacks), Joe Milton III 13.2 (PHI 0
  stacks). Both about 2% owned; neither in the winning builds.
- **Jonah Coleman (DEN RB) in 0 lineups:** 24.8% owned, 16.8 points, in 42% of the top 1%. Starters-only made
  J.K. Dobbins DEN's RB1 by 0.2 projected points (11.1 vs 10.9); Dobbins scored 2.7.
- **Josh Jacobs 0.5** in 38 lineups (Kaleb Johnson 12.8): GB's lead back left early.
- **Harrison** 3.0 (1 lineup). Third HOU game: remove the trade entry for week 10 (standing plan).
- Projection tiers: 8-14 projected 10.5 scored 7.8; 20+ 21.3 scored 15.6 (n 6); 14-20 fine (16.6 / 16.0). r 0.71,
  DST r 0.51. The week's big misses were RBs lifted by injured teammates (Allgeier, Singletary).
- No greens this week (Doug's choice), so no green-RB comparison.

## 6. Learn from winners and max-entrants (week 9, and weeks 5-9)

`weeks/2026-w09/winners.csv`, `winners_top_owned.csv`. Ours = all 150 incl. the free entry.

- **The FLEX gap closed this week:** FLEX RB 70.7% (top 10% 67.7%, field 68.1%), the first week it is level (weeks
  5-8 ours 27-46%). It came from the median-70 half (FLEX RB 85%). But our RBs scored 26.4 a lineup vs the top 10%'s
  48.7: right shape, wrong players.
- Still different every week (5 of 5): QB + 2 (ours 88% vs top 10% 34%), bring-back (99% vs 37%), no naked or
  one-team stacks, RB points (-27.6 a week on average), WR points (-15.5). Four of five: DST salary higher, QB points lower.
- Below the field median: 73% of our lineups (avg -9.2); weeks 5-9: 80 / 61 / 48 / 72 / 73%.
- Field's 10 most-owned: the 3 that hit (Golden, Coleman, K. Walker III) we held at 6% (top 10% 50%); the 7 that
  missed we held at 33% (top 10% 22%). Median-70 alone: hits 4%, misses 42%. Chalkier this week, on the wrong chalk.

**Max-entrants, week 9** (`max_entrants.py`, week-9 export added to its list): 1,751 users entered 150; they were 50%
of entries and 61% of the top 1%; cash 53.8% vs 44.2% for single entries; return 1.37 (field 1.34, single entries
1.02); us 0.68. Similarity to max-entrants (lower = closer): median-70 0.37, Doug entered 0.44, cap 45 0.66, no-draw
0.70, model 0.75, the same order as weeks 5-8. Their portfolio: 105 distinct lineups per 150, top player 65%, 70 players
used; ours 150 / 53% / 118. Their FLEX RB 76% (median-70 85%, model 39%). QB + 2: theirs 37%, their top 1% 52%, ours 99%.

## 7. Week-10 build tests: median-70 variants, weeks 5-9

Rebuilt in process (nothing in `weeks/` rewritten). The week-9 plain build is byte-identical to the archived
`median70/upload.csv`, and "plain 100 + model 49" in week 9 reproduces the entered result exactly. One change at a
time: (1) **v1 flex** = the flex-shadow rule (TE in the FLEX only if top-5 TE salary, RBs count as stack pieces);
(2) **v2 stack** = QB + 1 allowed, bring-back optional; (3) **v3 repeats** = plain's 150 ranked by its own objective,
top 105 kept and the top 45 entered twice (30% repeats, 105 distinct). Every variant built 150 every week (no stalls,
week 7 included). Money as if entered, with the week-9 prize table (it reproduces Doug's weeks 5/7/8 winnings).
"Model" = each week's archived model set. Full table: `weeks/2026-w09/week10_build_tests.csv`.

**Weeks 5-9 totals (150 lineups a week, $37.50 in fees):**

| Set | Avg | Cash rate | Won | Net | Top 10% | Top 1% | Best | Near 5 / 10 |
|---|---|---|---|---|---|---|---|---|
| Model (as built each week) | 105.6 | 33.9% | $28.91 | -$8.59 | **42** | 4 | 190.4 | 55 / 124 |
| Median-70 plain | 108.2 | 32.5% | $26.54 | -$10.96 | 35 | 3 | 198.0 | 65 / 146 |
| v1 flex | 109.1 | 35.1% | $28.73 | -$8.77 | 38 | 2 | 192.6 | 73 / 137 |
| v2 stack | 110.3 | **39.6%** | **$30.79** | **-$6.71** | 26 | 1 | 197.8 | 69 / 130 |
| v3 repeats | 109.4 | 32.4% | $26.65 | -$10.85 | 34 | 5 | 198.0 | 69 / 161 |
| Plain 100 + model 49 (week 9's entry) | 107.2 | 32.1% | $26.72 | -$10.53 | 36 | 4 | 198.0 | 66 / 154 |
| v1 100 + model 49 | 107.5 | 34.3% | $28.36 | -$8.89 | 38 | 3 | 192.6 | 64 / 130 |
| v2 100 + model 49 | 108.4 | 37.4% | $29.74 | -$7.51 | 29 | 2 | 183.3 | 56 / 123 |
| v3 100 + model 49 | 107.9 | 32.8% | $27.11 | -$10.14 | 33 | 4 | 198.0 | 62 / 152 |
| Model 100 + plain 49 | 106.5 | 32.6% | $27.73 | -$9.52 | 40 | 5 | 198.0 | 54 / 122 |
| Model 100 + v1 49 | 106.8 | 34.4% | $28.87 | -$8.38 | 36 | 4 | 190.4 | 52 / 114 |
| Model 100 + v2 49 | 107.0 | 34.5% | $28.37 | -$8.88 | 34 | 3 | 190.4 | 49 / 118 |
| Model 100 + v3 49 | 106.7 | 33.4% | $28.06 | -$9.19 | 36 | 6 | 198.0 | 51 / 123 |

**Net by week ($):**

| Set | Wk 5 | Wk 6 | Wk 7 | Wk 8 | Wk 9 |
|---|---|---|---|---|---|
| Model | -4.51 | -1.63 | **+0.58** | -2.93 | **-0.10** |
| Median-70 plain | -1.17 | +0.29 | -5.02 | -1.52 | -3.54 |
| v1 flex | -1.34 | +0.98 | -4.78 | -1.70 | -1.93 |
| v2 stack | **+0.39** | **+1.61** | -6.40 | -0.19 | -2.12 |
| v3 repeats | -0.96 | +0.73 | -6.68 | +0.72 | -4.66 |

What it says:
- **Every median-70 build swings with the week** (week 5 avg 130 vs model 108; week 7 85 vs 101). Concentration:
  it wins when its 3-4 core players hit and loses big when they don't (weeks 7 and 9).
- **v2 (relaxed stack rule) is the best cash build**: better money than plain in 4 of 5 weeks, cash 39.6%. But it
  has the fewest top-10% (26) and top-1% (1) lineups: it trades ceiling for floor.
- **v1 (flex rule)** beats plain on money in 3 of 5 weeks (+$2.19 total), with fewer top-1% (2 vs 3).
- **v3 (repeats)** is the most top-heavy: week 8's 4 top-1% are 2 lineups entered twice; weeks 7 and 9 its worst.
- **The model alone still has the most top-10% lineups (42) and is level on money with the best variants once noise
  is allowed for:** every money gap in the table is under $4.30 over five weeks, while a single week swings $5-7.
  Five slates cannot separate these builds on money.

## 8. Recommendation for week 10 (Doug decides)

1. **Entered set: model-led again: 100 model + 49 median-70 with the flex rule (v1), or the model 149 alone.**
   Both sit at the top of the five-week money table (-$8.38 / -$8.59), keep the model's top-finish count (4 top-1%),
   and avoid week 9's risk of three players in 70% of the median-70 lineups. Week 9's split (100 median-70 + 49 model)
   was -$10.53 over the five weeks and the worst set this week. If the goal shifts to cash rate rather than top
   finishes, v2 (relaxed stacks) is the build to try, as the 49.
2. Possible test (not run): in median-70, cap players lifted by injured teammates (RoutingBump 1+) at 50% instead of
   70%. Allgeier and Singletary would have been capped.
3. Keep building every variant as a shadow in week 10 (plain, v1, v2, v3) so week 10 adds a sixth week.
4. Week-10 checks: DEN RB starter (Coleman vs Dobbins, 0.2 apart; the field and the winners played Coleman); remove
   the Harrison trade entry; promotion kill rule after week 10 (week 9 -2.2, n 3); confirm $5.12 vs $5.13.
