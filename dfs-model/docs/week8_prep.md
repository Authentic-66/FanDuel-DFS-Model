# Week 8 prep (Oct 26, 2026)

Doug's eight week-8 changes, in his order. Each line says what was done and whether anything still needs his call.

| # | Change | Status |
|---|---|---|
| 1 | Re-download the FanDuel player list Friday and Sunday morning; report changes | **Done.** In the CLAUDE.md checklist; new `src/diff_players.py` |
| 2 | TE in the FLEX: (a) tapered TE spread, (b) a cap on TE-in-FLEX share | Built and tested, **both OFF**. Recommendation: adopt neither yet (section 2) |
| 3 | Questionable players: pass part of their work to the backups | Built and tested, **OFF**. Recommendation: adopt at 45% (section 3); Doug decides |
| 4 | Salary-floor cap relief +3 → +1 | **Done** (default). Weeks 4-6 build 150; **week 7 at cap 27 does not** (147). See section 4 |
| 5 | Reads: red applied; yellow and green shadow-only | **Done.** In CLAUDE.md and the week-8 config, with the week 4-7 numbers |
| 6 | Harrison 0.15 / 0.9; fix the ARI double count; flag Jacobs | **Done.** Note: **Houston has a bye and Green Bay plays Thursday in week 8** |
| 7 | Fix the grading crash | **Done.** Forced green QBs are scaled to fit; one read that cannot build no longer stops the rest |
| 8 | Keep the cap-45 control; pool kept or stopped | Control kept. **Pool: your note still reads "[keep 2 more weeks / stop]". Which one?** |

Archived weeks are unchanged. Weeks 4-7 were rebuilt with the old code and with the new code, and the draws are
identical (max difference 0.0). Weeks 6 and 7 pin the old settings (`trade_old_team = "full"`; week 7 also
`floor_cap_overflow = 3`). The week-7 re-run still reproduces all 150 entered lineups. All 111 unit tests pass.

**How the lineup tests were run.** For each of weeks 4-7: that week's final config, with the week-7 defaults switched
on for weeks 4-6 (salary floor with relief +3, role guard, WR implied-total correction). Projections were rebuilt with
today's code, 150 lineups were built, and they were scored on actual points. Weeks 5-7 use exact field ranks from the
FanDuel export; week 4's ranks are estimated (no raw export). Week 7's base is the entered set (100.90 / 11 / 0 /
151.38). One change at a time, unless the run says otherwise. All rows are in `weeks/2026-w07/backtest_week8_prep.csv`.
Two-slate caveat as usual: any change reshuffles the lineups, so a point or so either way is noise.

## 1. Player-list refresh (checklist)

Week 7 used FanDuel's Oct 19 list all week. Josh Jacobs came back from the exempt list after that, so he was never in
the model, and Pierre Strong (12 lineups) scored 0. From week 8:

- Download `fd_players.csv` when the slate opens. **Download it again Friday and again Sunday morning.** Keep the
  earlier file (e.g. `fd_players_fri.csv`) and run:

      python src/diff_players.py data/2026-w08/fd_players_fri.csv data/2026-w08/fd_players.csv

- It lists players **added** (back from IR or an exempt list, signed, traded in), players **removed**, **injury-tag
  changes** (Q → O etc.) and salary changes, matched on FanDuel Id. `--min-salary 5000` hides the min-priced noise.
  Claude reports the lists to Doug before re-running `model.py`. Example, week 6 Tuesday vs Sunday: 26 tag changes at
  $5,000+ (Lamar Q → O, Olave none → Q, A.J. Brown IR → Q, ...).
- In CLAUDE.md as the first step of the week-8 checklist. Tested in `tests/test_week8.py`.

## 2. TE in the FLEX

Week 7 had a TE in the FLEX in 78% of lineups (117 of 150). Two fixes were tested, both OFF in defaults.toml.

- **(a) Tapered TE spread.** `[model.spread] TE = { low = 1.215, top = 1.0 }`: TEs projected 12+ get narrower draws,
  down to none at 20, like QB and WR. The flat 1.215 was kept in week 6 only because too few TEs project 16+ to fit a
  taper.
- **(b) TE-in-FLEX cap.** New `[optimizer] flex_te_max_share` (0 = off). At most that share of lineups may have a TE
  in the FLEX. The limit is spread through the build: lineup k may add one only while the count stays within
  share × k, so the TE lineups don't all land on whichever stacks are built first. Tested at 35% (Doug's example) and
  20% (about the field rate: 16% in week 5).

| Week | Run | Avg | Top 10% | Top 1% | Best | FLEX RB / WR / TE |
|---|---|---|---|---|---|---|
| 4 | Base | 114.6 | 16 | 3 | 191.8 | 46 / 28 / 76 |
| 4 | (a) TE taper | 113.9 | 16 | 2 | 164.8 | 46 / 31 / 73 |
| 4 | (b) TE flex ≤ 35% | 113.5 | 17 | 1 | 164.0 | 50 / 49 / 51 |
| 4 | (b) TE flex ≤ 20% | 112.9 | 19 | 2 | 184.2 | 52 / 69 / 29 |
| 5 | Base | 113.9 | 7 | 0 | 179.0 | 38 / 76 / 36 |
| 5 | (a) TE taper | 114.3 | 7 | 0 | 179.0 | 37 / 79 / 34 |
| 5 | (b) TE flex ≤ 35% | 113.9 | 7 | 0 | 179.0 | 39 / 78 / 33 |
| 5 | (b) TE flex ≤ 20% | 113.1 | 7 | 0 | 179.0 | 44 / 82 / 24 |
| 6 | Base | 103.9 | 6 | 1 | 158.9 | 69 / 21 / 60 |
| 6 | (a) TE taper | 103.7 | 7 | 1 | 158.9 | 71 / 20 / 59 |
| 6 | (b) TE flex ≤ 35% | 103.4 | 7 | 0 | 149.1 | 76 / 26 / 48 |
| 6 | (b) TE flex ≤ 20% | 103.8 | 8 | 0 | 149.1 | 90 / 30 / 30 |
| 7 | Base (entered) | 100.9 | 11 | 0 | 151.4 | 21 / 12 / 117 |
| 7 | (a) TE taper | 101.1 | 13 | 0 | 151.4 | 22 / 10 / 118 |
| 7 | (b) TE flex ≤ 35% or 20% | **does not build at cap 27** (stalls at 145 / 136) | | | | |
| 7 | (b) TE flex ≤ 35%, cap 29 | 101.4 | 10 | 0 | 147.4 | 51 / 47 / 52 |
| 7 | (b) TE flex ≤ 35%, cap 30 | 101.9 | 15 | 2 | 166.1 | 48 / 50 / 52 |

Against base, average a lineup:
- **(a) Taper:** -0.7, +0.5, -0.2, +0.2. It **barely changes the FLEX mix** (76 → 73, 36 → 34, 60 → 59,
  117 → 118 TE) and loses week 4's 191.8 lineup.
- **(b) 35% cap:** -1.1, 0.0, -0.4, and week 7 does not build. Top-1% 3 → 1 in week 4 and 1 → 0 in week 6.
- **(b) 20% cap:** -1.7, -0.8, -0.1, and week 7 does not build. More top-10% lineups (+3, 0, +2), fewer top-1%.
- All three together (taper + 35% + Q routing): -2.1, +0.2, -0.3, and week 7 does not build.

**Why week 7 was 78%: mostly Doug's yellows, not the TE projections.** The RB / WR yellows (Strong 12, Gordon 8,
Pollard 4, Marks 2, Allgeier 1, Jameson Williams 7, Keenan Allen 6, Boston 6, ...) capped the FLEX alternatives, so
the TE took the slot. Week 7 re-built under the week-8 reads rule (yellows not applied, relief +1, cap 25) has a TE in
the FLEX in **84 of 150 (56%)**. It also scored better: 105.9 / 21 / 1 / 162.2, but
that is the yellow read (section 5), not a TE effect. The same run with the 35% cap: 105.9 / 21 / **4** / 167.1, FLEX
60 / 38 / 52.

**Recommendation: adopt neither yet.**
- The taper doesn't move the mix at all.
- The cap lowered the average in weeks 4 and 6, cost top-1% lineups in both, and makes a tight week infeasible
  (week 7 needs cap 29 with it).
- With yellows shadow-only from week 8, the main cause of the 78% is gone.
- Watch the FLEX mix in week 8's prelim (the exposure sheet will show it). If TE is still above ~50%, try the 35%
  cap on that slate. It is one line in week.toml: `[optimizer] flex_te_max_share = 0.35`.

## 3. Questionable players: their work goes to the backups

Until now a player marked Q was held out of our lineups (standing rule) and scored 0 in 25% of his draws, but his
teammates were never told he might sit. In week 7 Breece Hall and Tyjae Spears sat, and their backups scored 19.4
(Braelon Allen) and 38.0 (Pollard, the slate's best).

**How often they sit (the fitted share).**

| Sample | Players | Sat |
|---|---|---|
| History 2021-2025: listed Questionable, 50%+ of snaps over his last 3 games | 758 | **24%** (QB 47%, RB 20%, WR 22%, TE 17%) |
| Same, last practice "Did Not Participate" | 150 | **45%** |
| Same, last practice Limited / Full | 503 / 86 | 20% / 9% |
| Doug's `[status] questionable` lists, weeks 4, 6, 7 (his "uncertain Q") | 26 | **46%** (12; week 7: 5 of 8) |

Doug's list is not the league's Q list: he moves the Qs he expects to play to active, so his list sits about twice as
often. **45%** fits both his weeks 4-7 lists and the history's DNP group. When a Q player did play, he got 94% of his
usual snaps, so nothing is taken from him when he plays.

**Built** (`[model.injury] questionable_routing`, OFF; `project.questionable_routes`):
- Each RB / WR / TE marked Q sits in a fixed `questionable_inactive_prob` share of the draws.
- In exactly those draws his teammates get his targets and carries, routed as if he were ruled out: by position,
  WR depth split, present share.
- Same random noise, so a backup's big games line up with the draws where the starter sits. This is what a GPP
  needs: Allen's ceiling, not just a higher average.
- No other player's draws move.
- QBs are left out: a QB's volume goes to his backup QB, not his receivers.
- `QBump` in proj.csv shows the points gained.
- Test value: `questionable_inactive_prob = 0.45`.

Week 7 projections with it on:
- **Braelon Allen 8.7 → 11.3**, **Pollard 9.3 → 10.7**, Jeanty 15.1 → 16.0, Sutton 7.8 → 8.5, Mumpfield 6.1 → 6.9,
  Kittle 14.1 → 14.6.
- The Q players themselves fall (Nacua 16.9 → 13.3, Evans 9.8 → 7.2) but are held out anyway.

| Week | Base | Q routing | Note |
|---|---|---|---|
| 4 | 114.6 / 16 / 3 / 191.8 | 114.5 / **19** / **4** / 183.1 | 7 Q players; week 4 allowed Q players in lineups (12% cap) |
| 5 | 113.9 / 7 / 0 / 179.0 | identical | week 5's status lists had no Q players |
| 6 | 103.9 / 6 / 1 / 158.9 | 103.7 / 7 / 1 / 158.9 | |
| 7 | 100.9 / 11 / 0 / 151.4 | 100.7 / 11 / 0 / 151.1 | Allen 5 → 16 lineups; Pollard stays at 4 (his yellow cap) |

The average is flat (-0.1, 0, -0.2, -0.2: noise), with more top-10% lineups in two weeks and one more top-1% in week 4.
No week is worse by more than a point. In week 7 the backup that paid off most, Pollard, was capped at 4 by Doug's
yellow, so routing could not add him. Without the yellows (the week-8 rule) it would have.

**Recommendation: adopt it at 0.45** (`questionable_routing = true`, `questionable_inactive_prob = 0.45`) for
week 8. The lineup test is neutral on average and slightly better at the top. The case rests on the fit: Doug's Q
lists sit almost half the time, and the backups then get the work. **Doug decides; it stays OFF until he says so.**

## 4. Salary-floor cap relief +3 → +1 (done)

`[optimizer] floor_cap_overflow = 1` in defaults.toml. A player at the cap may now go one lineup over it, only for a
lineup that cannot otherwise reach $59,000. Week 7 keeps +3 in its own week.toml, so it still reproduces.

| Week | Relief +3 | Relief +1 | Max exposure +3 / +1 |
|---|---|---|---|
| 4 | 114.6 / 16 / 3 / 191.8 | 112.4 / 11 / 1 / 164.0 | 28 / 26 |
| 5 | 113.9 / 7 / 0 / 179.0 | 113.8 / 7 / 0 / 179.0 | 27 / 26 |
| 6 | 103.9 / 6 / 1 / 158.9 | 103.2 / 5 / 1 / 158.9 | 28 / 26 |
| 7, model cap 27 | 100.9 / 11 / 0 / 151.4 | **stalls at 147** | 30 / - |
| 7, control cap 45 | 98.0 / 8 / 1 / 157.8 | 98.4 / 9 / 1 / 157.8 | 48 / 46 |
| 7, pool cap 45 | 96.1 / 4 / 0 / 148.9 | 96.1 / 4 / 0 / 148.9 (identical) | 45 / 45 |

**Does 150 still build?** Weeks 4-6 yes, and the week-7 control and pool sets yes. **The week-7 model set at cap 27
does not** (147). Week 7 with +1 builds if:
- relief is +2 (101.6 / 13 / 0 / 151.4);
- the cap is 28 (101.3 / 12 / 1 / 162.7); or
- **the week-8 reads rule is used: yellows shadow-only. That builds at cap 25** (105.9 / 21 / 1 / 162.2).

So with week 8's rules a stall is less likely than in week 7. If one happens, the standing rule applies: stop and ask
Doug (cap +1 first, or relief +2).

**Cost to flag:** +1 lowered the average in week 4 (-2.2, top-10% 16 → 11, top-1% 3 → 1) and week 6 (-0.7), and was
level in week 5. Holding players to cap + 1 shifts lineups onto lower-projected fill-ins. It is Doug's call and is in
place. He may want to weigh week 4 before week 8's final run.

## 5. Reads from week 8: red applied, yellow and green shadow-only (done)

Recorded in CLAUDE.md (standing rules) and set up in `config/2026-w08/week.toml`:
- Reds go in `[prefs] red`.
- Yellows go in `[shadow.yellow]` and greens in `[shadow.green]`.
- `[prefs.yellow]` and `[prefs.green]` stay empty.
- `analyze_results.py` already grades shadow yellows: "yellow (shadow) added".

Points a lineup each colour was worth (re-runs with only that colour changed):

| Week | Red | Yellow | Green | Source |
|---|---|---|---|---|
| 4 | +3.0 (red and yellow together) | | +1.3 | week6_prep section 7 |
| 5 | +1.4 (shadow) | +0.6 (shadow) | -1.7 (shadow) | week5_review / reads_lineups.csv |
| 6 | +1.4 | -0.5 | none listed | week6_review |
| 7 | -1.6 | **-4.8** | +0.3 (shadow, boost mode); -2.0 floor mode; Kyren minimum -0.8 | week7_review, this doc |
| **Weeks 5-7** | **+1.2** | **-4.7** | | |

Reds helped in weeks 5 and 6 (and, with yellows, in week 4) and cost 1.6 in week 7. Yellows were roughly even until week 7's -4.8: four yellowed QBs scored 20+,
and Pollard, capped at 4, scored 38.

## 6. Harrison, the ARI double count, Jacobs (done)

**Week 8 schedule check (nflverse games.csv, Oct 26).** Byes: **HOU, NO, NYG, SF**. Green Bay plays **Thursday**
(CAR@GB), and PHI@WAS and CHI@SEA are the night games. The likely main slate is 11 games and 22 teams: BAL@BUF,
TEN@CIN, ARI@DAL, MIN@DET, IND@JAX, LV@NYJ, CLE@PIT, ATL@TB, LAC@LAR, KC@DEN, NE@MIA. So:

- **Harrison** is not on the week-8 slate. His entry is set as Doug asked (`new_target_share = 0.15`,
  `first_week_factor = 0.9`, also under `[shadow.trade]`) and applies from the next slate Houston is on (week 9).
  This week only the Arizona side runs.
- **Josh Jacobs** (GB) will not be on the Sunday main slate either. The week-8 config has a note to flag him for
  Doug's read if he turns up; otherwise his read waits for week 9, when he will have two games of data.

**ARI double count, fixed.** New `[model.injury] trade_old_team` (`usage.trade_volume`):
- **`"present_share"` (new default):** a traded player's old teammates get his volume the way an OUT player's is
  handed out under present share. Each teammate's gain is scaled by the part of his sample the traded player was
  still there for, so it fades with every game they play without him.
- **`"full"`:** the old rule, in full every week. Pinned in weeks 6-7.

On week 7 the fix takes 1.5 points off Arizona's players (Virgil 7.3 → 6.7, Michael Wilson 12.4 → 12.1, Bourne
8.1 → 7.8, McBride 14.9 → 14.7). That was the double count. Other players move ≤ 0.1 (random-stream noise). In week 8
ARI will have played three games without him, so the gain shrinks again. Remove the trade entry after about three
Houston games, as planned.

## 7. Grading crash (fixed)

`analyze_results.py` crashed on week 7's shadow-green re-run. In floor mode the 57 shadow greens forced green QBs into
185 lineups of 150.

Now:
- **`optimize.assign_forced`** scales every green QB's forced lineups down in proportion when they don't fit, so the
  QBs fill exactly 150. It prints a warning, e.g. `Jared Goff 27 -> 22, Brock Purdy 26 -> 21, ...`.
- **`analyze.reads_lineups`** records a run that cannot build (with the error) and carries on with the others.

Week 7's shadow greens in floor mode now build 150: **98.9 / 7 / 0 / 147.3**, against 100.9 as entered, so **-2.0 a
lineup** (boost mode was +0.3). Week 7's committed `reads_lineups.csv` (the scratch re-runs) is left as it was. Tests:
`tests/test_week8.py`.

## 8. Control and pool sets

- **Cap-45 control:** kept. `config/2026-w08/week.toml` has `[grading] extra_sets = ["model_cap45"]` and the
  command in a comment. Build it with the final run, as in week 7.
- **Pool:** Doug's note reads "Pool: [keep 2 more weeks / stop]", with neither option picked. **Question for Doug:
  keep it (weeks 8-9) or stop?** `[pool]` in the week-8 config is empty until he answers. In week 7 the pool was -1.9
  a lineup against the control (96.1 / 4 / 0 / 148.9 vs 98.0 / 8 / 1 / 157.8).

## Defaults changed today

| Setting | Was | Now | Doug's item |
|---|---|---|---|
| `[optimizer] floor_cap_overflow` | 3 | **1** | 4 |
| `[model.injury] trade_old_team` | (full) | **"present_share"** | 6 |
| `[optimizer] flex_te_max_share` | n/a | 0 (off) | 2, not adopted |
| `[model.injury] questionable_routing` | n/a | false (off) | 3, not adopted |

## Files

- `src/dfs/project.py`: `questionable_routes`, Q routing in `build`, `QBump` column.
- `src/dfs/usage.py`: `trade_volume(..., st, old_team)`.
- `src/dfs/optimize.py`: `flex_te_max_share` (`solve_lineup(te_flex=...)`), `assign_forced` overflow.
- `src/dfs/analyze.py`: `reads_lineups` keeps going when one run fails.
- `src/diff_players.py`: new.
- `tests/test_week8.py`: 9 tests.
- `config/defaults.toml`: four settings above.
- Pins: `config/2026-w06/week.toml`, `config/2026-w07/week.toml`.
- `config/2026-w08/week.toml`: template.
- `weeks/2026-w07/backtest_week8_prep.csv`: every lineup-test row.
- `weeks/2026-w07/questionable_sits_live.csv` and `weeks/history/questionable_sits.csv`: the Q fit rows.
- Scratch scripts (not in the repo): `lt_run.py`, `lt_relief7.py`, `lt_extra7.py`, `w7_sets_relief1.py`, `q_fit.py`,
  `q_live.py`.
