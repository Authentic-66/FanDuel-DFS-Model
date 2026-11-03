# Learn from winners — weeks 5-8 (Nov 2)

Doug's request: compare the field's top 1%, top 10%, the whole field and our entered lineups each week on how the
lineups were built; list the us-vs-top-10% differences that show up in all four weeks separately from the one- or
two-week ones; how often our lineups finished below the field median; and whether the exposure cap (25) keeps us
under the popular players who hit (model set vs the cap-45 control). **Nothing changed in the model.** It is now a
weekly review step (section 6).

Data: the full FanDuel All Entries export for each week (`data/<week>/raw/`, untracked; ~550-570k lineups; week 5 =
the Pooch Punt file). Top 1% / 10% = rank within 1% / 10% of `[contest] field_size`. "Ours" = our 150 entries in the
contest (149 model + Doug's free entry). Ownership = FanDuel's %Drafted. A stack piece is any non-DST teammate of the
QB; bring-back = at least one non-DST from the QB's opponent; game stack = teammate + bring-back, one-team = teammates
only, naked = no teammate. Script: `src/learn_from_winners.py` (tables per week in `weeks/<week>/winners.csv` and
`winners_top_owned.csv`).

## 1. Four weeks at a glance (means of the four weekly values)

| | top 1% | top 10% | field | **ours** |
|---|---:|---:|---:|---:|
| Salary QB | 7,749 | 7,703 | 7,676 | 7,684 |
| Salary RB (all RBs) | 20,469 | 20,216 | 19,507 | **16,851** |
| Salary WR | 21,355 | 21,483 | 21,888 | 21,600 |
| Salary TE (all TEs) | 6,475 | 6,638 | 6,842 | **8,946** |
| Salary DST | 3,792 | 3,798 | 3,896 | **4,301** |
| Salary total | 59,839 | 59,838 | 59,808 | 59,381 |
| RBs per lineup | 2.8 | 2.7 | 2.6 | **2.3** |
| FLEX RB / WR / TE % | 80 / 11 / 9 | 75 / 14 / 11 | 64 / 20 / 16 | **27 / 19 / 54** |
| Avg player ownership % | 17.0 | 17.6 | 16.8 | **11.2** |
| Players over 20% owned | 3.1 | 3.3 | 3.2 | **1.6** |
| QB + 0 / 1 / 2 / 3+ teammates % | 12 / 40 / 43 / 5 | 16 / 45 / 35 / 5 | 16 / 46 / 33 / 5 | 0 / 1 / 89 / 10 |
| Bring-back % | 54 | 49 | 47 | 100 |
| Game / one-team / naked stack % | 48 / 39 / 12 | 43 / 41 / 16 | 41 / 43 / 16 | 100 / 0 / 0 |
| QB <7.5k / 7.5-8.4k / 8.5-9.2k / 9.3k+ % | 33 / 63 / 1 / 3 | 34 / 59 / 2 / 5 | 35 / 53 / 5 / 7 | 36 / 51 / 6 / 6 |
| DST <3.8k / 3.8-4.2k / 4.3-4.7k / 4.8k+ % | 56 / 15 / 18 / 11 | 55 / 15 / 18 / 12 | 48 / 16 / 20 / 16 | **19 / 20 / 34 / 28** |
| Points QB / RB / WR / TE / DST | 29 / 67 / 58 / 17 / 12 | 26 / 60 / 49 / 15 / 9 | 20 / 43 / 34 / 13 / 7 | 19 / **31** / 35 / 14 / 7 |
| Points total | 183.2 | 160.0 | 116.4 | 105.3 |

The 10 most-owned players each week, with every group's exposure, are in `weeks/<week>/winners_top_owned.csv`.

## 2. Us minus the top 10%

A difference counts in a week if it is at least $150 of salary, 4 points of share, 0.5 points of ownership, 0.1 a
lineup, or 1 fantasy point. The "field minus top 10%" column shows whether **the winners** differ from everyone (a
winner trait) or whether **we** are the odd one out.

**In all four weeks, same direction:**

| | wk 5 | wk 6 | wk 7 | wk 8 | mean | field minus top 10% |
|---|---:|---:|---:|---:|---:|---:|
| Salary RB | -4,465 | -2,602 | -3,412 | -2,983 | **-3,366** | -709 |
| Salary TE | +1,619 | +1,431 | +3,326 | +2,857 | **+2,308** | +204 |
| Salary DST | +371 | +248 | +987 | +408 | **+503** | +98 |
| RBs per lineup | -0.6 | -0.3 | -0.5 | -0.5 | **-0.5** | -0.1 |
| FLEX RB % | -57 | -28 | -54 | -53 | **-48** | -10 |
| FLEX TE % | +34 | +20 | +63 | +55 | **+43** | +4 |
| Avg player ownership | -10.6 | -6.1 | -3.7 | -5.2 | **-6.4** | -0.8 |
| Players over 20% owned | -2.7 | -1.8 | -1.2 | -1.5 | **-1.8** | -0.2 |
| DST under $3.8k % | -21 | -17 | -64 | -44 | **-36** | -7 |
| DST $4.8k+ % | +10 | +9 | +34 | +10 | **+16** | +4 |
| QB + 2 % | +49 | +58 | +61 | +49 | +54 | -2 |
| QB + 1 % / naked % | -46 / -11 | -43 / -23 | -46 / -13 | -42 / -16 | -44 / -16 | +1 / +1 |
| Bring-back % (= game stack) | +35 | +64 | +47 | +56 | +50 | -3 |
| Points RB | -43 | -22 | -24 | -25 | -29 | -17 |
| Points WR | -11 | -9 | -11 | -27 | -14 | -15 |
| Points DST | -2 | -2 | -5 | -1 | -3 | -2 |

**In three weeks:** QB + 3 teammates more often (+6 pts), QB $8.5-9.2k more often (+5; the top 10% almost never use
that tier), DST $4.3-4.7k more often (+16), QB points -7.

**Only one or two weeks, or mixed direction:** QB salary (we spent $345 less in week 8, otherwise level), WR salary
(+$1,294 in week 5, -$964 in week 7), total salary (we left $1,095 / $624 more unspent in weeks 5-6, before the salary
floor; level since), FLEX WR, cheap QB (week 8 only: +22 pts), TE points.

What the all-weeks list says, split three ways:

1. **Winner traits we lack** (the top 10% differ from the field the same way, every week): more RBs, more RB salary,
   RB in the FLEX, cheap DSTs. We are on the far side of the field on each, not just short of the winners: FLEX RB
   ours 27%, field 64%, top 10% 75%, top 1% 80%. The RB shortfall shows up as -29 RB points a lineup.
2. **Ownership:** we play far less chalk than anyone (11.2% average player vs 16.8% field, 1.6 players over 20% vs
   3.2). The top 10% are only slightly chalkier than the field (+0.8), and in week 7 less chalky, so chalk itself
   is not a winner trait; but our gap is six to eight times the winners' edge over the field.
3. **Our stack rule, not a winner trait:** QB + 2 with a bring-back on every lineup. The top 10% look like the field
   here (QB + 1 is the most common build; bring-back about half the time). The top 1% lean our way (QB + 2 43% vs 35%
   in the top 10%; game stack 48% vs 43%), and in week 8, the one-QB Burrow slate, the top 1% were 64% QB + 2 and 62%
   game stacks. So the stack shape costs nothing visible at the top-1% end, where the money is.

## 3. Below the field median

| | field median | our average | ours minus median | our lineups below the median |
|---|---:|---:|---:|---:|
| Week 5 | 132.3 | 108.9 | **-23.4** | 80% |
| Week 6 | 110.9 | 104.6 | -6.3 | 61% |
| Week 7 | 101.2 | 101.1 | -0.0 | 48% |
| Week 8 | 118.7 | 106.5 | -12.2 | 72% |
| Four weeks | | | **-10.5** | **65%** |

Our average lineup finished below the field median in three of the four weeks (week 7 level). The gaps are biggest
in the weeks the chalk RBs hit (week 5: Gibbs, Warren; week 8: Burrow/Higgins, B. Allen, Gibbs).

## 4. Is the 25 cap keeping us off the popular players who hit?

"Hit" = the top 10% held the player at 1.2 times the field's rate or more. Mean exposure %, the field's 10 most-owned
players. Model = the entered build (cap 25; **cap 27 in week 7**). Control = the same model at cap 45: weeks 7-8 the
archived `model_cap45/` sets; **weeks 5-6 built afterwards in the scratchpad** from the archived inputs (the model
rebuilt at its own cap matched the entered 150 exactly both weeks).

| | hits | the hits: field / top 10% / model / cap 45 | the rest: field / top 10% / model / cap 45 |
|---|---:|---|---|
| Week 5 | 4 (Gibbs, Warren, Brissett, WAS DST) | 30.8 / 52.9 / 11.7 / 15.7 | 36.4 / 33.6 / 16.2 / 21.3 |
| Week 6 | 4 (Likely, Walker, Swift, Hubbard) | 29.8 / 54.5 / 16.7 / 21.7 | 28.6 / 18.5 / 14.6 / 18.6 |
| Week 7 | 1 (B. Allen) | 21.4 / 27.6 / 3.3 / 2.0 | 34.0 / 25.5 / 14.2 / 18.0 |
| Week 8 | 3 (Higgins, B. Allen, Gibbs) | 25.0 / 49.2 / 11.3 / 12.4 | 24.5 / 18.4 / 13.6 / 16.7 |
| Cap 45 adds | | **+4.0 / +5.0 / -1.3 / +1.1, mean +2.2** | **+5.1 / +4.0 / +3.8 / +3.1, mean +4.0** |

- **The cap binds:** 28 of the 40 most-owned players sat at or just above the cap in the model set (16.7% = 25
  lineups; 18-20% in week 7).
- **But raising it does not find the hits.** At cap 45 the model adds more exposure to the popular players who
  missed (+4.0) than to the ones who hit (+2.2), and it still holds the hits at 2-22% while the top 10% held them at
  ~50%. The hits the model was lowest on were held down by other things: Braelon Allen red in week 8 (25.3 pts) and Q
  (held out) in week 7, Warren 17-18% even at cap 45 (projection), Walker 11% at cap 45, Brissett and WAS DST 6-9%.
- **Ownership:** cap 45 lifts our average player ownership by 0.6-2.0 points (model 11.1 -> 12.5 over four weeks),
  about a fifth of the 6.4-point gap to the top 10%. It changes **none** of the RB count, FLEX TE share or cheap-DST
  share (RBs 2.26 vs 2.24, FLEX TE 54% vs 58%).
- **Lineups, model vs cap 45** (avg / top-10% / top-1% / best): week 5 108.3 / 3 / 0 / 184.9 vs 113.9 / 5 / 0 / 180.8;
  week 6 104.0 / 8 / 1 / 158.4 vs 105.9 / 10 / 0 / 152.4; week 7 100.9 / 11 / 0 / 151.4 vs 98.0 / 8 / 1 / 157.8;
  week 8 106.3 / 10 / 0 / 190.4 vs 107.4 / 13 / 0 / 190.7. Four weeks: average +1.4 for cap 45 (3 weeks of 4),
  top 10% 32 vs 36, top 1% 1 vs 1, best better in 2 of 4.

**Answer:** the cap is part of why we are light on chalk, but it is not why we miss the chalk that hits. Cap 45 has
been a little better on average (+1.4 a lineup over four weeks, no gain in top-1% finishes) because it adds chalk
across the board, not because it picks the right chalk. The bigger, consistent gap is the build: half an RB fewer per
lineup, TE in the FLEX, and an expensive DST, and the cap does not touch any of those.

## 5. What this points to (for Doug; nothing adopted)

- **RB in the FLEX and cheap DSTs** are the only winner traits that show up in all four weeks, and they are the same
  RB/flex gap as docs/week9_tests.md sections 1, 5-7. The flex shadow build (RB stack pieces + top-5-salary TE flex)
  runs in weeks 9-10. Section 7 there found the flex TEs out-scored the RBs the optimizer passed over (+0.4), so the
  model's choice was right among the RBs it rated; the RBs that won were mostly ones it rated lower or couldn't use
  (reds, Q, the cap). A cheap-DST test would need history (DST r was 0.11-0.40 live).
- **Cap:** the case for 45 is a small average gain, not a fix for missing the hits; the decision stays Doug's
  (standing rule: ask before any cap raise).
- **Stack rule:** no evidence against it at the top-1% end.
- Caveat: four weeks, and the top-10% traits are partly outcomes (RB-heavy lineups won because RBs hit). A difference
  that holds all four weeks is the signal to test on 2021-2025 history; it is not proof by itself.

## 6. Weekly review step (from week 9)

After `convert_results.py`:

    python src/learn_from_winners.py --week 2026-w09
    python src/learn_from_winners.py --compare 2026-w05,2026-w06,2026-w07,2026-w08,2026-w09

The first reads the raw export (pass `--export` if `data/<week>/raw/` holds more than one csv) and writes
`weeks/<week>/winners.csv` and `winners_top_owned.csv`; the model set and every `[grading] extra_sets` set (control,
pool, flex_shadow) get a column in the most-owned exposure table. The second lists the differences that hold every
week, in all but one, or only in some ("all but one week" = three of four now). Report both in the
week's review.
