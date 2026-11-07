# Who finishes at the top? NFL (Doug, Nov 6 2026; analysis only, no model change)

NFL only: never pooled with the NBA (Doug, Nov 6). The NBA version is in the NBA repo.

Full All Entries exports for weeks 5-8: the Pooch Punt every week plus the week-5 Hail Mary (5 contests, 2.47
million entries, 166,442 distinct users). FanDuel's entry name "user (k/N)" gives each user's entry count N.
Cash = finishing inside the paid ranks of the week-9 $35K Pooch Punt table (`data/2026-w09/prizes_pooch-punt.csv`),
which reproduces Doug's reported winnings to the cent for weeks 5, 7 and 8 (week 6 $5.97 vs $5.96, a split tie).
The Hail Mary has no prize table: sections 1-3 only. Aggregated; repeat winners are anonymous ids from this run.
Script: `python src/top_finishers.py`. Lineup comparison with our builds: `docs/max_entrants.md`.

## Findings (NFL)

1. **The top 20 is spread out; the top-1% clusters are copies of one lineup.** The top 20 held 16-20 different users
   every contest (one user at most 5). In 3 of 5 contests one user had all 150 entries in the top 1%, every time the
   same lineup 150 times.
2. **Max-entry users (150) win more than their share.** 1.7% of users, 49.1% of entries, 63.2% of top-1% entries.
   Top-1% rate per entry 1.3% vs 0.6% (one entry) and 0.7% (2-20). Over-represented in 4 of 5 contests (week 6 even).
3. **Repeat winners are max-entrants.** 751 users made the top 1% in 3+ of the 5 contests: 638 max-entrants (of
   1,636 who played 3+ at 150), 1 one-entry user (of 78,494). 85 made it in all 5; the top 9 at 3.6-6.1% of their
   entries (field 1%; picked for top finishes, so the rate overstates their edge).
4. **Max-entrants cash at a higher rate, not just more often:** Pooch Punt cash 51.8% vs 41.4% (one entry), field
   47.3%; return per $1 of fees 1.43 vs 1.05, field 1.26. Their return beat the field's every week (4 of 4).
5. **Overlay every week:** the Pooch Punt paid 1.23-1.30x its fees (the $35K guarantee didn't fill), so the average
   entry made money; a return under ~1.26 is below the average player.
6. **Us (Doug as entered):** 600 Pooch Punt entries (4 x 150 incl. the free entries), cash 33.2%, return **0.73**,
   one top-1% entry in 606 (incl. Hail Mary). We play the max like the 1.43 group but return about half of it.

**Caveats:** who wins, not why (max-entrants are likely full-time players with their own tools); duplicated lineups
make the top-1% shares lumpy; ties use FanDuel's shared rank; the prize table is week 9's (checked above).

## Tables (script output)

## 1. Concentration at the top (users among the top entries; most entries one user had there, with that user's total entries in the contest)

| Contest | Entries | Users | Max_entries | Top 20: users | Top 20: most by 1 user | Top 100: users | Top 100: most by 1 user | Top 1%: users | Top 1%: most by 1 user |
|---|---|---|---|---|---|---|---|---|---|
| wk5 Pooch Punt | 571,483 | 116,653 | 150 | 19 of 21 | 3 (30 entered, 1 distinct) | 82 of 100 | 4 (150 entered, 3 distinct) | 2140 of 5734 | 150 (150 entered, 1 distinct) |
| wk5 Hail Mary | 207,707 | 20,699 | 150 | 19 of 20 | 2 (150 entered, 2 distinct) | 88 of 100 | 3 (150 entered, 3 distinct) | 822 of 2082 | 41 (150 entered, 41 distinct) |
| wk6 Pooch Punt | 571,917 | 115,659 | 150 | 16 of 21 | 5 (150 entered, 1 distinct) | 74 of 110 | 20 (40 entered, 1 distinct) | 2517 of 5730 | 150 (150 entered, 1 distinct) |
| wk7 Pooch Punt | 550,210 | 114,590 | 150 | 19 of 21 | 2 (150 entered, 2 distinct) | 88 of 100 | 3 (150 entered, 3 distinct) | 1805 of 5522 | 23 (150 entered, 23 distinct) |
| wk8 Pooch Punt | 566,416 | 116,072 | 150 | 20 of 20 | 1 (15 entered, 1 distinct) | 97 of 100 | 2 (150 entered, 2 distinct) | 2055 of 5730 | 150 (150 entered, 1 distinct) |

## 2. Share of top-1% entries vs share of field entries, by the user's entries in the contest

| Contest | 1 | 2-20 | 21-149 | 150 (max) |
|---|---|---|---|---|
| wk5 Pooch Punt | 9.7% vs 16.1% | 11.6% vs 16.5% | 15.1% vs 18.9% | 63.7% vs 48.5% |
| wk5 Hail Mary | 2.9% vs 4.5% | 14.2% vs 22.1% | 15.7% vs 17.2% | 67.1% vs 56.2% |
| wk6 Pooch Punt | 15.4% vs 15.8% | 17.0% vs 16.9% | 19.8% vs 19.2% | 47.8% vs 48.1% |
| wk7 Pooch Punt | 5.3% vs 16.4% | 7.1% vs 17.0% | 12.7% vs 18.3% | 74.9% vs 48.4% |
| wk8 Pooch Punt | 8.5% vs 16.2% | 11.4% vs 16.5% | 14.7% vs 18.6% | 65.4% vs 48.7% |

All NFL contests:

| Entries_per_user | Field_entries | Top1_entries | Lift | Top1_rate_per_entry | Field_users | Users_with_a_top1 |
|---|---|---|---|---|---|---|
| 1 | 15.2% | 9.2% | 0.61 | 0.6% | 77.3% | 24.4% |
| 2-20 | 17.2% | 12.0% | 0.70 | 0.7% | 19.1% | 21.1% |
| 21-149 | 18.6% | 15.6% | 0.84 | 0.8% | 1.9% | 13.6% |
| 150 (max) | 49.1% | 63.2% | 1.29 | 1.3% | 1.7% | 40.9% |

Duplicate lineups: distinct lineups per entry within a user (1.00 = no repeats), pooled:

| Entries_per_user | Distinct_per_entry |
|---|---|
| 1 | 0.99 |
| 2-20 | 0.72 |
| 21-149 | 0.52 |
| 150 (max) | 0.71 |

## 3. Repeat winners: users in the top 1% of 3+ of the 5 contests

751 users (of 166,442 distinct users; 102,161 entered 3+ contests).

| Top-1% contests | Users |
|---|---|
| 3 | 405 |
| 4 | 261 |
| 5 | 85 |

Top 25 (and Doug):

| User | Contests entered | Top-1% contests | Top-1% entries | Total entries | Median entries per contest | Sports | Top-1% rate per entry |
|---|---|---|---|---|---|---|---|
| user_001 | 5 | 5 | 46 | 750 | 150 | NFL | 6.1% |
| user_002 | 5 | 5 | 44 | 750 | 150 | NFL | 5.9% |
| user_003 | 5 | 5 | 37 | 750 | 150 | NFL | 4.9% |
| user_004 | 5 | 5 | 34 | 750 | 150 | NFL | 4.5% |
| user_005 | 5 | 5 | 32 | 750 | 150 | NFL | 4.3% |
| user_006 | 5 | 5 | 31 | 750 | 150 | NFL | 4.1% |
| user_007 | 5 | 5 | 31 | 750 | 150 | NFL | 4.1% |
| user_008 | 5 | 5 | 28 | 750 | 150 | NFL | 3.7% |
| user_009 | 5 | 5 | 27 | 750 | 150 | NFL | 3.6% |
| user_010 | 5 | 5 | 26 | 750 | 150 | NFL | 3.5% |
| user_011 | 5 | 5 | 25 | 750 | 150 | NFL | 3.3% |
| user_012 | 5 | 5 | 25 | 750 | 150 | NFL | 3.3% |
| user_013 | 5 | 5 | 25 | 750 | 150 | NFL | 3.3% |
| user_014 | 5 | 5 | 24 | 750 | 150 | NFL | 3.2% |
| user_015 | 5 | 5 | 23 | 750 | 150 | NFL | 3.1% |
| user_016 | 5 | 5 | 23 | 750 | 150 | NFL | 3.1% |
| user_017 | 5 | 5 | 23 | 750 | 150 | NFL | 3.1% |
| user_018 | 5 | 5 | 22 | 650 | 150 | NFL | 3.4% |
| user_019 | 5 | 5 | 22 | 750 | 150 | NFL | 2.9% |
| user_020 | 5 | 5 | 22 | 750 | 150 | NFL | 2.9% |
| user_021 | 5 | 5 | 21 | 750 | 150 | NFL | 2.8% |
| user_022 | 5 | 5 | 20 | 750 | 150 | NFL | 2.7% |
| user_023 | 5 | 5 | 20 | 750 | 150 | NFL | 2.7% |
| user_024 | 5 | 5 | 19 | 750 | 150 | NFL | 2.5% |
| user_025 | 5 | 5 | 19 | 750 | 150 | NFL | 2.5% |

Entered 3+ contests, by median entries per contest (top-1% rate per entry; field 1%):

| Entries_per_contest | Users | With_3plus_top1 | Rate |
|---|---|---|---|
| 1 | 78494 | 1 | 0.6% |
| 2-20 | 20162 | 16 | 0.7% |
| 21-149 | 1869 | 96 | 1.0% |
| 150 (max) | 1636 | 638 | 1.3% |

Doug: 5 contests, 1 with a top-1% entry, 1 top-1% entries of 606 (0.2%).

## 4. Cash rate / return (won / fees) by entries per user (contests with a prize table)

| Contest | Field_cash | Field_return | 1 | 2-20 | 21-149 | 150 (max) | Doug |
|---|---|---|---|---|---|---|---|
| wk5 Pooch Punt | 46.4% | 1.23 | 34.4% / 0.81 | 34.3% / 0.81 | 42.4% / 1.33 | 56.1% / 1.47 | 19.3% / 0.41 |
| wk6 Pooch Punt | 47.6% | 1.30 | 45.9% / 1.43 | 46.2% / 1.11 | 47.1% / 1.12 | 49.0% / 1.40 | 37.3% / 0.80 |
| wk7 Pooch Punt | 48.2% | 1.27 | 42.7% / 0.93 | 43.4% / 0.96 | 47.1% / 1.10 | 52.2% / 1.57 | 50.7% / 1.09 |
| wk8 Pooch Punt | 46.9% | 1.24 | 42.8% / 1.02 | 43.1% / 1.38 | 45.3% / 1.16 | 50.1% / 1.30 | 25.3% / 0.61 |

All NFL contests: field cash 47.3%, return 1.26; Doug 600 entries, cash 33.2%, return 0.73

| Entries_per_user | Entries | Share_of_entries | Cash_rate | Share_of_cashes | Return | Share_of_prize_money |
|---|---|---|---|---|---|---|
| 1 | 364,653 | 16.1% | 41.4% | 14.1% | 1.05 | 13.4% |
| 2-20 | 377,508 | 16.7% | 41.8% | 14.8% | 1.07 | 14.1% |
| 21-149 | 423,765 | 18.8% | 45.4% | 18.0% | 1.18 | 17.5% |
| 150 (max) | 1,094,100 | 48.4% | 51.8% | 53.1% | 1.43 | 54.9% |
