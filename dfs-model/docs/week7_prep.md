# Week 7 prep (Oct 18, 2026)

Doug's list, in his order. Two items are adopted on his instruction (1 and 2); items 3 and 4 are recommendations only;
item 5 is his trade read. Scratch scripts (not in the repo) did every test against archived weeks; nothing in
`weeks/2026-w04..06` was rewritten.

| # | Item | Status |
|---|---|---|
| 1 | Name matching: skip defensive players with no offensive volume | **ON by default** (bug fix) |
| 2 | Salary floor $59,000, cap relief to 28 for floor lineups only | **ON by default**; Doug: keep as built, no relief for yellow caps |
| 3 | Calibration on Vegas totals + WR/TE implied-total term | Doug: keep 0.36. WR correction built, **OFF**; lineup test in section 6 |
| 4 | Ownership: Guru flag, cheap-new-role flag | Doug: dropped. He records full Guru lists when he uses Guru |
| 5 | Harrison: share 0.15, first-week factor 0.5 | Set in `config/2026-w07/week.toml` (HOU hosts NYG Sunday 1:00) |
| 6 | WR implied-total correction, weeks 4-6 lineup test | Recommend adopting (section 6) |
| 7 | Role guard: no 2026 data -> 0; WR/TE role floor of 3 a game | **ON by default** (test clean); RB left out of the floor (section 7) |
| 7a | Nickname aliases (Josh / Joshua Palmer and 5 more) | **ON** (bug fix found by the guard's warning) |

Doug's decisions after the first pass (Oct 18): floor kept as built; calibration slope kept at 0.36; WR correction
built switched off and lineup-tested; both ownership flags dropped; new role guard, switched on if its test was clean.

## 1. Name matching

**Cause.** FanDuel and nflverse are joined by name: `data.norm_name` lowercases, keeps letters only and drops Jr./Sr./
II/III/IV, so "Michael Carter II" and "Michael Carter" share the key `michaelcarter`. When two nflverse players share a
key, the one with the most attempts + carries + targets wins (`usage.aggregate`). That works when both have rows, but
the TEN running back has not played in 2026, so the PHI cornerback's four 0-volume games were the only 2026 rows under
the key. The back then carried the cornerback's team (the warning) and four empty games, with his 2025 Arizona volume
blended in on top.

**Fix.** `[model] skip_defense_names = true` (defaults.toml; `data.no_offense`, applied in `data.load_stats`): stat
rows of players listed at a non-offensive position (defence, K, P, LS) **with no attempts, carries or targets** in the
season are dropped before matching. Two-way players with offensive touches (Travis Hunter, listed CB) keep every row.
Fullbacks and blocking tight ends with no touches are still offensive and stay. Because every caller of `load_stats`
gets it, the history fits use it too. `false` restores the old matching.

**gsis IDs and position.** FanDuel's player list has no gsis or nflverse ID, so the join has to stay name-based.
Requiring the FanDuel position to equal the nflverse position would wrongly drop same-person label differences found
in the audit below (fullbacks FanDuel lists as TE, Hunter CB/WR, Ryan Miller WR/TE, Brady Russell RB/TE, Bernhard
Raimann OT/TE). The rule above requires an offensive position *or* offensive volume, which is the part of "require
position" that catches the bad matches.

**Test.** `tests/test_names.py` (5 tests): Carter / Carter II share a key; with only the cornerback's rows, the old
matching gives the back PHI and the fix drops the key; when both have rows the back still wins; Hunter keeps both games;
a fullback with no touches is kept. Full suite: 75 tests OK.

### 1.1 Weeks 4-6 before and after

Projections rebuilt in memory with each week's config (nothing written):

- **Fix off = the old code, bit for bit** (projection and draw checksums, all players, all three weeks). Week 6 also
  matches the archived `weeks/2026-w06/proj.csv` exactly.
- **Fix on, real changes: two players.**

| Player | FanDuel | nflverse match before | Week 4 | Week 5 | Week 6 | Lineups |
|---|---|---|---|---|---|---|
| Michael Carter | TEN RB, $4,000 | Michael Carter II, PHI CB | 3.5 → 0.0 | not in the projections | 2.6 → 0.0 | 0 |
| Marcus Jones | NE WR, $4,000 | himself (a CB with no 2026 offensive touches) | 0.0 → 0.0 | 0.0 → 0.0 | 0.8 → 0.0 | 0 |

  Jones's 0.8 in week 6 was his share of an NE absence being handed out. Both are below `min_proj = 4`, so neither
  could be in a lineup; both scored 0 every week. The Carter warning is gone (week 4 still warns about TB's starting
  QB, which is unrelated).
- **Everything else moved by 0.0-0.4 points** (week 4: 5 players, max 0.1; week 5: 29, max 0.4; week 6: 20, max 0.3;
  plus the simulated draws of most players). This is **random-stream noise, not a model change**: a player without
  stats takes the fallback simulation, which draws a different count of random numbers, and every player after him
  on the slate gets different draws. Proof: with the fix on and the two players' old usage rows put back (plus Jones's
  old stat rows in week 6, used by the present-share rule), all three weeks reproduce the old projections and draws
  exactly.

So "unchanged apart from the warning" holds for every projection that mattered: the only real changes are two
$4,000 players projected under 4 who were never in a lineup. Archived lineups are not affected (the archived
`proj.csv` files are what grading uses). A from-scratch re-run of weeks 4-6 would reshuffle some lineups through the
draw noise, as any change does.

**Side finding worth fixing (backlog):** the projection draws share one random stream across the slate, so touching
one player changes every later player's draws. Giving each player his own seeded stream (seed from the player's id)
would keep unrelated players identical between runs and remove part of the noise in two-slate lineup tests.

### 1.2 Audit of every match, weeks 4-6

Every FanDuel QB/RB/WR/TE on the three slates against the nflverse player his key resolves to, current season (before
the week) and prior season:

| Kind | Fix off | Fix on |
|---|---|---|
| Different person matched | **Michael Carter** (TEN RB → PHI CB Carter II, current season, all three weeks); **Brandon Johnson** (PIT WR → a PHI DB, prior season, weeks 5-6) | none |
| Long snappers / linemen FanDuel lists as TE, defender listed WR (Ben Mann, Beau Gardner, Mitchell Fraboni, Andrew DePaola, Cal Adomitis, William Wagner, James Winchester, Tyler Ott, Daniel Brunskill, Danny Pinter, Dominique Robinson) | matched to their own 0-volume rows | dropped (no offensive touches); projections stay 0 |
| Same person, different position label | Hunter (CB), Ryan Miller (WR), Brady Russell (RB), Andrew Beck / Connor Heyward / Riley Nowakowski (FB), Robbie Ouzts (RB), Justin Shorter (TE), Bernhard Raimann (OT) | unchanged (correct matches) |
| Team mismatch, current season | Carter (PHI vs TEN); Jimmy Horn Jr. (CAR → CLE, 1 target, a real move) | Horn only |
| Key shared by two offensive players | none | none |

Brandon Johnson's bad prior-season match changed nothing: the DB had 2 games, under the prior blend's minimum, so it
was never blended. **Bad matches that changed a projection: Carter only (3.5 and 2.6). Bad matches that changed a
lineup: none.**

### 1.3 A related gap: players with no stats at all (Phil Mafah)

Phil Mafah (NYG RB, $4,000) has no 2026 nflverse rows and one 2025 game, so he takes the fallback projection from
FanDuel's FPPG (9.9, from a single game): 10.6, 10.4 and 10.7 in weeks 4-6. He scored 0 all three weeks. He never
reached a lineup only because starters-only ranks Skattebo above him; if Skattebo were ruled out, Mafah would become
NYG's RB1 at $4,000 and projected 10.6, and the optimizer would load up on him. **Recommendation:** fallback players
(no stat rows in either season) project at most a small floor, or are flagged on the exposure sheet. Not changed.

## 2. Salary floor (adopted)

`[optimizer] min_salary = 59000` and `floor_cap_overflow = 3` in defaults.toml (`optimize.solve_lineup`). For each
lineup: solve with salary >= $59,000; if no lineup can reach it, players at the standing 25-lineup cap may be used up to
28 times for that lineup only; if that fails too, the lineup is built without the floor. Yellow caps and
`[prefs.player_cap]` limits are never relaxed. The optimizer prints how many lineups used relief. Weeks 4-6 pin
`min_salary = 0` in their week.toml so their "as entered" re-runs still reproduce. CLAUDE.md records: "Doug approved
cap relief to 28 for salary-floor lineups only (week 7)."

Verified with the repo code (archived projections and sims, final configs):

| Week | Run | Avg | Top 10% | Top 1% | Best | Avg salary | Under $59,000 | Used relief | Max exposure |
|---|---|---|---|---|---|---|---|---|---|
| 6 | Floor off (pinned) | 104.0 | 8 | 1 | 158.4 | $59,077 | 39 | | 25 |
| 6 | **Floor + relief** | 104.2 | 6 | 1 | 158.4 | $59,651 | 0 | 7 | 28 (16 players over 25) |
| 5 | Floor off (pinned) | 108.3 | 3 | 0 | 184.9 | $58,719 | 58 | | 25 |
| 5 | **Floor + relief** | 110.6 | 3 | 0 | 184.9 | $59,566 | 0 | 3 | 28 (11 players over 25) |

The pinned runs reproduce the entered lineups exactly. Week 5 matches the review's scratch test exactly. **Week 6 does
not: 6 / 1 here against 10 / 2 in the review (docs/week6_review.md 8.1).** The only difference is that the scratch
version also gave relief to yellow-capped players (Penix, Huntley, Kamara...), and I read "capped players" as the
players at the 25 cap, so a yellow read is never loosened. The top-end gain in week 6 came from that, or from the
reshuffle it caused; two slates cannot tell which. Average and spend are better either way. If Doug wants relief for
yellow-capped players too, it is a one-line change.

## 3. Top-tier bias: calibration with Vegas totals, plus the WR/TE implied-total term

Doug's premise needs one correction: the current `top_slope = 0.36` was already fit on 2021-2025 with each game's
Vegas implied total (`fit_history.py`, "vegas" rows, Oct 12). It was redone here with the current model (routing,
week-6 defaults, the name fix), leave-one-season-out, recent seasons weighted 0.75 per year back, 12,193 player-weeks
(weeks 4-18). Each variant is fit on four seasons and graded on the fifth. The WR/TE term is a mean-only shift:
projection + b x projection x (implied / 22.5 - 1), b per position.

**Fitted values.** Slopes: top 0.357 (folds 0.32-0.41), RB 0.119 (0.11-0.13), the same as the current 0.36 / 0.12.
WR/TE term: **WR b = -0.34 (folds -0.29 to -0.41), TE -0.27 (-0.21 to -0.33)**, the same sign and size in every fold.
QB +0.04 and RB +0.13 were also estimated, and adding them makes the top tier worse.

The WR over-reaction is visible without any fit. Current calibration, projected minus actual, by team implied total:

| Implied total | < 19 | 19-21.5 | 21.5-24 | 24-26.5 | 26.5+ |
|---|---|---|---|---|---|
| WR gap | +0.35 | +0.15 | +0.92 | +1.22 | +1.67 |
| TE gap | -0.51 | +0.54 | +0.54 | +0.38 | +0.59 |
| RB gap | +0.10 | +0.49 | +0.17 | +0.07 | +0.14 |
| QB gap | -0.63 | -0.61 | -0.20 | -0.64 | -0.48 |

**History (out of season, weighted):**

| Variant | Bias | RMSE | 14-20 gap | 20+ gap (n) |
|---|---|---|---|---|
| No calibration | +0.74 | 7.32 | +1.37 | +2.54 (1,034) |
| Current (0.36 / 0.12) | +0.30 | 7.25 | +0.39 | +0.17 (482) |
| Refit slopes | +0.30 | 7.25 | +0.38 | +0.15 (491) |
| **Current + WR/TE term** | **+0.26** | **7.24** | **+0.21** | **-0.04 (440)** |
| Refit slopes + implied term, all 4 positions | +0.26 | 7.24 | +0.31 | -0.11 (468) |

**Live weeks 4-6**, rebuilt with today's code (uncalibrated pipeline, players with FanDuel FPPG >= 5, starting QBs only;
351 player-weeks), with the full-sample fit applied:

| Variant | Bias | RMSE | 14-20 gap | 20+ gap (n) | Wk 4 20+ | Wk 5 20+ | Wk 6 20+ |
|---|---|---|---|---|---|---|---|
| No calibration | +2.09 | 7.72 | +2.11 | +4.68 (37) | +4.0 | +1.9 | +7.3 |
| Current (0.36 / 0.12) | +1.54 | 7.48 | +1.18 | +3.14 (14) | +4.8 | -4.8 | +7.8 |
| **Current + WR/TE term** | **+1.50** | **7.45** | +1.27 | **+2.81 (14)** | +4.7 | -5.0 | +7.1 |

What this says:

1. **The "+5 to +8 three weeks running" is mostly gone with today's code.** The review numbers (+6.3, +4.9, +7.8) came
   from each week's code as run; weeks 4-5 had no calibration then. With the current calibration the three weeks are
   +4.8, -4.8 and +7.8, pooled +3.1 on 14 players. With a player-level spread of about 7.5 points, that is about 1.5
   standard errors: not enough to justify a steeper slope, and the history says the slope is right.
2. **The live projections have a level bias the history cannot see: +1.5 against +0.3.** Some 9.7% of live
   slate players scored 0 (inactive, hurt early, or no role: Mafah three times, Judkins, Warren, DJ Moore, Skattebo in
   week 6), against 3.5% of history rows, because the history only contains players who recorded a stat that week.
   Without the zeros the live bias is +0.9. That is a "will he play / keep the role" risk, not a slope problem;
   section 1.3 and the Q handling are where to attack it.
3. **The WR/TE term is a small, consistent improvement**, in history (20+ gap +0.17 to -0.04, RMSE 7.25 to 7.24) and in
   the live weeks (20+ +3.1 to +2.8, RMSE 7.48 to 7.45). It mostly trims WRs on high-total teams (Nacua in week 6:
   23.7 to 20.4; he scored 11).

**Recommendation:** keep `top_slope` 0.36 / `rb_slope` 0.12. Build the WR/TE implied-total term into
`project.adjust` as a switched-off option (`[model.implied_sensitivity] WR = -0.34, TE = -0.27`, mean-only like the
calibration), run the four-number lineup test on weeks 4-6, and decide together. Separately, address the zero-score
risk (fallback players, players with no stat row in recent games).

## 4. Ownership: Guru flag and cheap-new-role flag

Training frames for weeks 4-6 rebuilt in memory with today's code (the cached `ownership_train.csv` files predate it,
and refreshing them would overwrite them). Leave-one-week-out. "15%+" = the 49 players the field owned at 15% or more
across the three weeks. Guru data: week 4 holds only Doug's 9 picks, week 5 the full 21 suggestions, week 6 none.

| Features | MAE, all graded players | MAE, 15%+ owned (49) | Bias on 15%+ | Wk 4 / 5 / 6 MAE on 15%+ |
|---|---|---|---|---|
| Current | 2.98 | 12.24 | -9.8 | 13.7 / 13.6 / 10.0 |
| + Guru flag | **2.88** | **12.08** | -8.7 | 12.7 / 14.1 / 10.0 |
| + cheap new role (gained volume >= 1, <= $7,000) | 2.99 | 12.29 | -9.8 | 13.7 / 13.6 / 10.2 |
| + cheap new role (routing bump >= 1.5, <= $7,000) | 2.97 | 12.24 | -9.8 | 13.7 / 13.6 / 10.0 |
| + Guru + cheap new role | 2.89 | 12.12 | -8.7 | 12.7 / 14.1 / 10.2 |
| + mid-price value term | 2.93 | 12.26 | -10.3 | 12.7 / 14.1 / 10.6 |
| Sharpness factor on the logits (fit on training weeks) | 3.02 | 12.41 | -8.9 | 14.1 / 13.6 / 10.1 |

**None of them fixes the miss.** The chalk is under-predicted by about 10 points whatever the features. The cheap-new-
role flag adds nothing beyond the gained-volume feature already in the model. Guru helps a little where Doug picked
(Jones 5% to 9%, Wilson 16% to 28%, Warren 24% to 37%), but over-shoots on Guru names the field did not chase (Gibbs 50%
vs 39%, St. Brown 38% vs 29%, Goff 23% vs 18%), so week 5, the one week with the full lists, gets *worse* (13.6 to 14.1).
The players behind the miss (Jones 40% / 5%, Love 33% / 6%, Wilson 51% / 16%, Likely 38% / 10%, London 32% / 11%) were
news-driven calls; nothing in salary, projection, value, totals or gained volume points at them.

**Recommendation:** adopt nothing yet. Have Doug record Guru's full suggestion lists every week (three weeks with
complete lists would settle whether the flag earns its place). The more useful step may be a pre-lock ownership source
the field itself sees (FanDuel's own projected ownership or a public ownership projection), entered like Guru.

## 5. Harrison (Doug's trade read)

Houston hosts the Giants on Sunday at 1:00 ET, so both sides of the trade run in week 7. `config/2026-w07/week.toml`
(new, a template like week 6's) has `new_target_share = 0.15`, `first_week_factor = 0.5`: **7.5% of Houston's targets**.
The same values are recorded under `[shadow.trade]` to be scored by hand after the games. Basis: 12 of about 59 snaps
(~20%) and 4 of 32 targets in London.

One note on the Arizona side: the trade entry still hands his full Arizona volume to his old teammates. Their week-6
game was already played without him, so about one game in five of their sample already reflects the change. That is
a small double count. No change for week 7; the entry should come out after about three Houston games, as planned.

## 6. WR implied-total correction: built (off) and lineup-tested

`[model.implied_sensitivity]` in defaults.toml, `project.implied_shift` in `project.adjust`: after the calibration and
before the spread, each WR's draws move by b x mean x (implied / 22.5 - 1), with b = -0.34. It is a mean-only shift,
as fit in section 3. `enabled = false`; `TE = 0.0` (the history fit is -0.27, tested below as a second variant). With
it off, projections are bit-identical to before.

Lineup test: each week's final config with the week-7 salary floor on, projections rebuilt with today's code (name
fix and aliases on), 150 lineups, scored on actual points:

| Week | Run | Avg | Top 10% | Top 1% | Best (est. rank) |
|---|---|---|---|---|---|
| 4 | Base | 111.3 | 11 | 2 | 164.7 (5,683) |
| 4 | **WR correction** | **115.5** | **22** | **4** | **178.3 (1,112)** |
| 4 | WR + TE correction | 115.1 | 21 | 5 | 174.1 (1,719) |
| 5 | Base | 112.4 | 7 | 0 | 179.0 (22,158) |
| 5 | **WR correction** | 113.4 | 7 | 0 | 179.0 |
| 5 | WR + TE correction | 113.5 | 7 | 0 | 179.0 |
| 6 | Base | 104.1 | 6 | 0 | 153.8 (10,507) |
| 6 | **WR correction** | 102.9 | 5 | 0 | 149.1 (18,777) |
| 6 | WR + TE correction | 103.1 | 5 | 1 | 162.2 (3,808) |

WR correction against base: average **+4.2, +0.9, -1.3** (mean +1.3 a lineup); top-10% 11→22, 7→7, 6→5; top-1%
2→4, 0→0, 0→0; best +13.6, 0, -4.7. Better in two weeks of three, and week 4's jump is larger than any one change
should cause, so part of it is the usual reshuffle. Week 6 is the week Nacua (trimmed 23.7 → 20.4 by the correction)
busted, yet the run with him trimmed scored lower: the reshuffle cuts both ways. WR + TE behaves about the same.

**Recommendation: adopt the WR correction for week 7** (`enabled = true`). The case rests mainly on the history:
-0.34 in every left-out season (-0.29 to -0.41), WR over-projection rising steadily with the team total, and better
calibration in history and on the live weeks. The lineup test agrees on balance (better average and top end in two
weeks of three) without being proof. Leave TE at 0 until it shows up in a test of its own.

## 7. Role guard (on)

`[model.role_guard]` in defaults.toml (`project.role_guard`, `project.role_volume`; `tests/test_role_guard.py`):

1. **No 2026 data → 0.** A skill player with no current-season stat rows (until now projected from FanDuel FPPG alone,
   the fallback) projects 0 unless he has a read in `[overrides]`. The run prints `WARNING: role guard: no 2026 usage
   data, projected 0 unless given an [overrides] read: ...`, listing those who would have projected 3+, e.g. week 6:
   Shane Buechele (BUF QB, 5.1), Jaydon Blue (PHI RB, 4.1), Cedric Tillman (NO WR, 4.8), Isaiah Hodgins (PIT WR,
   4.0), Tyler Johnson (NYJ WR, 3.6), Jaret Patterson (CLE RB, 3.5), Phil Mafah (NYG RB, 11.1). With a read the player
   comes back (checked: Mafah with a 5.0 read projects 5.0).
2. **Role floor.** WR and TE must average **3+ targets + carries a game in their 2026 games played**, measured from
   the current-season rows before the prior-season blend and before injury / trade routing. Otherwise they project 0,
   and the run prints the list. Braelon Allen-type backups who already had volume qualify (5+ a game); Wetjen (0
   targets, 5.1 points all from routing) does not. Overrides exempt here too.

Mechanics: the guarded players' draws are taken and then set to 0, so no other player's simulation changes (no
random-stream shift). A zeroed player cannot hold starter depth, so the next eligible player at the position moves
up, as with excluded Q players (in weeks 4-6 nobody new entered the pool that way). Weeks 4-6 pin `enabled = false`.

**Why RB is not in the floor (Claude's call, against "skill players" in Doug's spec):** running backs who inherit the
job do get the work. Bam Knight (RoleVol 1.5) had 17 touches with Love out in week 6, Tyrone Tracy 17.5 points in week
6, Jaleel McLaughlin 13 touches, Roschon Johnson 12. For receivers, routed volume mostly does not show up (Wetjen 0).
With RB in the floor the weeks 4-6 lineups are **identical** (an RB only enters the pool as his team's RB1, and every
RB1 had 3+ a game), so leaving RB out costs nothing in the test. It only matters when a backup becomes the RB1 late,
and then the guard would zero the obvious replacement. To apply the spec as written: `positions = ["RB", "WR", "TE"]`.

### 7.1 Test on weeks 4-6

| Week | Players guarded who would project 3+ | In the optimizer pool before | Entered lineup slots removed | Those slots scored |
|---|---|---|---|---|
| 4 | 51 | 7 | 15 (Joshua Palmer 10, Zach Ertz 5) | 0.8 and 2.3 |
| 5 | 42 | 10 | 11 (Theo Wease 7, Troy Franklin 2, Jauan Jennings 1, Elic Ayomanor 1) | 2.1, 2.6, 0.0, 2.2 |
| 6 | 43 | 5 | 17 (Cedric Tillman 7, Kaden Wetjen 5, Elic Ayomanor 3, Cody White 2) | 0.0, 0.0, 0.8, 0.0 |

**43 entered lineup slots removed; those players averaged 1.0 point, against 5.9 projected.** Every one of them is a WR
or TE (or no-data), so the WR/TE-only floor removes exactly the same slots. Lineup re-runs (same settings as section 6):

| Week | Base avg / top 10% / top 1% / best | Role guard | WR/TE-only floor |
|---|---|---|---|
| 4 | 111.3 / 11 / 2 / 164.7 | 111.4 / 12 / 2 / 167.0 | same as role guard |
| 5 | 112.4 / 7 / 0 / 179.0 | 113.2 / 7 / 0 / 179.0 | same |
| 6 | 104.1 / 6 / 0 / 153.8 | 104.1 / 6 / 0 / 152.0 | same |

Average +0.1, +0.8, -0.1 a lineup; top-10% +1, 0, 0; top-1% unchanged; best +2.3, 0, -1.8. No week worse in any way
that matters.

**Real starters blocked.** Of the guarded players the model counted as starters (in the pool), four had a real role
that week (6+ targets + carries): **Tyquan Thornton (KC WR, week 4: 8 touches, 28.6 points, 0.3% owned)**, Oronde
Gadsden (LAC TE1, week 4: 9 touches, 6.3), Jerry Jeudy (CLE, week 5: 7 touches, 3.4) and Darnell Mooney (NYG, week 5:
7 touches, 2.4). None was in our lineups, so the guard would have cost nothing, but Thornton shows its price: a
low-volume starter can still have a big game. Outside the pool, a few low-volume players had big games (Omar Cooper Jr.
22.3, Darius Cooper 16.8, Kyle Williams 16.6, Josh Cuevas 12.4, all projected under 4 and never in our lineups).

**Verdict: clean enough, switched on.** It removed 43 slots that scored 1.0, never made a lineup set worse by more than
0.1, and blocked no player we actually rostered. The cost is the occasional Thornton. If Doug wants one of them, an
`[overrides]` read brings the player back.

### 7.2 Found by the guard: nickname mismatches (aliases, on)

The "no 2026 data" list turned up six players whose FanDuel and nflverse names differ by more than case or a suffix,
so they had no stats and ran on FanDuel FPPG. With the guard on, they would have been zeroed for a name problem:

| FanDuel | nflverse | Effect of the fix |
|---|---|---|
| Joshua Palmer (BUF WR) | Josh Palmer | week 4: 8.7 → 5.3 (in 10 entered lineups; scored 0.8); week 6: 5.2 → 4.2 |
| Mitch Tinsley (CIN WR) | Mitchell Tinsley | week 5: 7.6 → 6.1 (in 10 entered lineups; scored 0) |
| Matt Hibner (BAL TE) | Matthew Hibner | week 4: 7.1 → 2.9 |
| Hollywood Brown (PHI WR) | Marquise Brown | week 4: 0.7 → 7.6, week 6: 0.6 → 4.7 |
| Nick Singleton (TEN RB) | Nicholas Singleton | 0.4 → 2.0 |
| Drew Ogletree (IND TE) | Andrew Ogletree | 0.0 → 1.0 |

`[names.aliases]` in defaults.toml (nflverse name → FanDuel name, applied in `data.load_stats`, so every caller gets
it; test in `tests/test_names.py`). Teammates move where a newly matched player's volume now counts: Mark Andrews +0.7
in week 6 (Hibner out), Wicks -1.4 and Lemon -0.6 in week 4 (Brown's share), Pollard +0.8 in week 5. Everything else
moves ≤ 0.3 (random stream). Most of these players still fail the role floor (Palmer 2.5 a game, Hibner 1.5); Tinsley
passes (7 in his one game). New aliases go in the same table as the warning shows them. **Check the warning list every
week: a name on it is either a player with no 2026 snaps or a missing alias.**

## Files

- `src/dfs/data.py` (`no_offense`, `skip_defense_names`, `[names.aliases]`), `config/defaults.toml`,
  `tests/test_names.py`.
- `src/dfs/project.py` (`role_guard`, `role_volume`, `implied_shift`; proj gains `RoleVol`, `NoData`, `RoleGuard`),
  `config/defaults.toml` (`[model.role_guard]` on, `[model.implied_sensitivity]` off), `tests/test_role_guard.py`,
  `config/2026-w04..06/week.toml` (`[model.role_guard] enabled = false`, as entered).
- `src/dfs/optimize.py` (salary floor + relief, `FLOOR_LOG`), `config/defaults.toml` (`min_salary`, `floor_cap_overflow`),
  `config/2026-w04..06/week.toml` (`min_salary = 0`, as entered).
- `config/2026-w07/week.toml`: new template with the Harrison read.
- `docs/week6_review.md`: winnings filled in ($5.96, net -$1.49, running total -$3.88).
