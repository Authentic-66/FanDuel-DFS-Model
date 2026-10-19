# Doug's pool mode (built Oct 19, 2026)

A second set of 150 lineups built only from Doug's player pool, inside the existing model: same projections, sims,
objective, stack rules, salary floor and standing rules. Written to `weeks/<week>/pool/`, apart from the model's
files, and graded every week by `analyze_results.py` whether entered or not (shadow).

**One deviation from the spec, decided by Doug on Oct 19 (section 6: WR 14, cap 40):** with the pool sizes in the spec, 150 lineups
can't be built at cap 25. They can't be built at cap 40 either, at least not with the stand-in pools tested here. Pool
mode applies the standing rule "raise to 40 if infeasible" to pool players only. If it still can't finish 150, it stops
and says what to change. It never raises the cap past 40 on its own.

## 1. How to use it

In `config/<week>/week.toml`:

```toml
[pool]
ranked = true      # optional: lists are in Doug's rank order -> small objective boost by rank
QB  = ["Josh Allen", "Matthew Stafford", ...]          # ~10
RB  = ["Kyren Williams", "D'Andre Swift", ...]          # ~10
WR  = ["Puka Nacua", "Chris Olave", ...]                # ~10 (see section 3: 14 is what built in the tests)
TE  = ["Brock Bowers", "Trey McBride", ...]             # ~8
DST = ["Kansas City Chiefs", "PIT", ...]                # ~5; FanDuel name or team code
```

Then, after `model.py`:

```
python src/optimize.py --week 2026-w07 --pool          # -> weeks/2026-w07/pool/
python src/optimize.py --week 2026-w07 --pool --subdir test   # -> weeks/2026-w07/pool/test/ (comparisons)
```

Output in `weeks/<week>/pool/`: `upload.csv` (FanDuel format, exact header), `readable.csv` (plus a `Filler` column:
the lineup's non-pool player), `exposure.csv` (plus `Pool`: rank, or `filler`), `projections.csv`, `stacks.csv`, and
`pool.csv` (every listed player: rank, objective multiplier, projection, lineups, and why he was held out if he was).
The model's own files in `weeks/<week>/` are never touched by `--pool`.

Settings (defaults.toml `[pool]`, any of them can be overridden in week.toml):

| key | default | meaning |
|---|---|---|
| `max_filler` | 1 | players per lineup from outside the pool |
| `ranked` | false | lists are in rank order |
| `rank_boost` | 0.05 | rank 1 objective x 1.05, falling linearly to x 1.00 for the last listed (pending Doug's OK) |
| `raise_cap_to` | 40 | cap for pool players when the capacity check fails at the standing 25; 0 = stop instead |

## 2. Rules

Same as the model: projections and sims (`proj.csv`, `sims.npy`, Doug's overrides), objective (0.6 x mean + 0.4 x one
draw), stack shape (QB + 2 of his WR/TE + 1 bring-back, per-team `[stacks.rules]`), stack weights, roster, $60K cap,
max 4 per team, no DST facing our players, max overlap 6, the $59K salary floor with cap relief to 28, the questionable
rule, red and yellow reads.

Pool specifics:
- **Pool players** skip `starters_only` and `min_proj`, as green players do: if Doug lists a backup, the backup is
  eligible. They are still held out if OUT, questionable (standing rule), red, or a QB who isn't the week's starter.
  `pool.csv` shows each held-out player and the reason.
- **Filler** (at most 1 per lineup): any player the model itself could use (starters, not red, projected 4+, not Q) who
  is not in the pool. The filler also has to pass the role-guard test (2026 data; WR/TE 3+ targets + carries a game),
  checked even in weeks where the guard is switched off. The filler is never the QB, because the stack QB comes from
  the pool. He can be a stack receiver, the bring-back, the flex or the DST. Fillers keep the standing cap of 25.
- **Stacks**: only pool QBs are stacked. A pool QB's team is dropped from the stack draw (with a printed note) when one
  filler can't complete his stack, e.g. no pool receiver from his team and no pool player on the other side. The
  opposing QB doesn't count as a bring-back, since a lineup holds one QB. A pool QB's team with no `[stacks.weights]`
  entry gets the smallest listed weight.
- **Green** forcing (`[prefs.green]`) is not used in pool mode, since the pool replaces it. Green has been shadow-only
  since week 6, so nothing changes.
- **Ranked pools**: each pool player's objective value is multiplied by his rank factor (rank 1 x 1.05 ... last
  x 1.00). It is small on purpose: a 20-point player at rank 1 gains 1 point over the same player ranked last.

## 3. The exposure cap: why 25 can't work with these pool sizes

Before building, pool mode checks a lower bound: can the usable pool fill every roster slot at the cap, with at most
150 fillers in total (1 per lineup), none at QB?

With the spec's sizes (QB 10, RB 10, WR 10, TE 8, DST 5) and 150 lineups:

| cap | WR slots short | RB short | DST short | RB+WR+TE incl. FLEX short | fillers needed | allowed |
|---|---|---|---|---|---|---|
| 25 | 450 - 250 = 200 | 300 - 250 = 50 | 150 - 125 = 25 | 1050 - 700 = 350 | **375** | 150 |
| 32 | 130 | 0 | 0 | 154 | 154 | 150 |
| 33 | 120 | 0 | 0 | 126 | 126 | 150 |
| 40 | 50 | 0 | 0 | 0 | 50 | 150 |

So cap 25 is impossible by arithmetic alone, before salary, stacks or overlap: 375 fillers are needed and 150 are
allowed. Doug's standing rule already covers this ("raise to 40 only if infeasible"), so pool mode raises **pool
players** to 40 and prints why; fillers stay at 25. Set `raise_cap_to = 0` to stop with the numbers instead.

Passing the check is necessary but not enough. In the tests (section 4), every week stalled short of 150 at cap 40
with 10 WRs: the stacks run dry, because each pool QB needs two of his own receivers, and with one filler a lineup
can borrow at most one of them from outside the pool. When that happens pool mode stops with the stack counts it
reached and what to change. It never goes past 40 by itself.

What worked on week 4 (each change on its own; nothing else changed):

| change | lineups built |
|---|---|
| spec sizes, cap 40 | 138 (stalled) |
| salary floor off | stalled |
| max overlap 7 | stalled |
| proportional stack allocation | stalled |
| WR 12 / WR 12 + TE 10 | 148 / 149 (stalled) |
| **WR 14, cap 40** | **150** |
| cap 45 / 50 / 60 | 150 |
| 2 fillers per lineup | 150 |

**Doug's call:** (a) send ~14 WRs (and a receiver or two for each pool QB) and keep the cap at 40; (b) allow a pool
cap of 45 (`[pool] raise_cap_to = 45`); or (c) allow 2 fillers (`max_filler = 2`). Option (a) changes no rule.

## 4. Test on weeks 4-6

Run in a scratch copy of the repo (nothing in `weeks/` or `config/` here was written). Projections were rebuilt
in-process from each week's own config, with the week-7 salary floor turned on ($59K, relief to 28).

**Stand-in pool** (Doug has no real pool for these weeks): week-4 greens that are on that week's slate, in Doug's
listed order, then a stack-aware top-up the way a pool would be built. Each pool QB (stack-weighted teams first)
gets his best receiver and one opposing skill player, then each position is filled by model projection to the
spec's sizes. Week-4 reds and red teams, and each week's own reds, are left out. `ranked = true` (greens first, then
by projection). Greens found: week 4: 11 of 11; week 5: 6 (Cousins, McCaffrey, Montgomery, E. Wilson, Likely,
Hockenson); week 6: 7 (Allen, Cousins, K. Williams, Wicks, Nacua, Lemon, Likely).

Spec sizes (WR 10) at cap 40: **stalled at 138, 138 and 145 lineups** (weeks 4, 5, 6) with the message above.

WR 14 at cap 40: **150 lineups each week, every rule checked on every lineup, no violations**: 9 distinct players
and a legal roster, salary $59,000-60,000 (no lineup below the floor), max 4 per team, the stack shape (including
BUF's Cook rule in week 4), no DST facing our players, at most 1 filler and never a QB, every filler passes the
role-guard test, exposure within the caps (pool 40, fillers 25 + floor relief, yellow caps), max overlap 6.

| week | lineups with a filler | filler positions | stack teams dropped | mean salary | mean proj |
|---|---|---|---|---|---|
| 4 | 149 | WR 79, TE 37, RB 29, DST 4 | none | $59,773 | 120.0 |
| 5 | 150 | WR 98, TE 29, RB 14, DST 9 | HOU | $59,743 | 125.7 |
| 6 | 147 | WR 86, RB 35, TE 15, DST 11 | IND | $59,745 | 128.7 |

Almost every lineup uses its filler, and mostly on a WR: another sign the WR list is the tight one.

**Grading** (the new `analyze_results.py` section; average, top-10% count, top-1% count, best):

| week | set | avg | top 10% | top 1% | best (rank) |
|---|---|---|---|---|---|
| 4 | pool (stand-in) | 119.2 | 31 | 9 | 177.8 (1,165) |
| 4 | model | 111.1 | 19 | 1 | 188.7 (234) |
| 4 | entered | 111.2 | 20 | 4 | 178.7 (1,058) |
| 5 | pool (stand-in) | 129.3 | 9 | 1 | 191.8 (5,326) |
| 5 | model | 108.3 | 3 | 0 | 184.9 (13,708) |
| 5 | entered | 108.9 | 4 | 0 | 184.9 (13,708) |
| 6 | pool (stand-in) | 107.9 | 8 | 0 | 154.5 (9,275) |
| 6 | model | 104.0 | 8 | 1 | 158.4 (5,089) |
| 6 | entered | 104.6 | 8 | 1 | 158.4 (5,089) |

"model" = `weeks/<week>/upload.csv` as built that week. **These numbers only show that the grading works; they are
not evidence for pool mode.** The pool runs use today's code (later projection fixes), cap 40 instead of 25 and the
salary floor, so they differ from the archived model lineups in more than the pool. A fair test needs the model rebuilt
the same way, and two-slate lineup tests are noise anyway (docs/week6_prep.md 9.1). No result was used to pick the pool.

The CLI path was also run end to end on the scratch week 6 (`optimize.py --pool`, then `analyze_results.py`):
files written to `weeks/2026-w06/pool/` in the scratch copy, upload header exact, `pool/grade.csv` written.

## 5. The normal model is unchanged

The optimizer only gains optional arguments (`build_lineups(..., pool_mode=None)`, `solve_lineup(..., outside=None)`)
that do nothing when not given. Proof: week 6 built with the code before and after this change gives **identical**
lineups (150 of 150), and both match the archived week-6 `upload.csv` 150 of 150. The only other optimizer edit is
the message when a build fails: it now lists the stacks built so far (also when proportional allocation runs out of
teams, which used to end with "stack weights sum to zero").

Tests: `tests/test_pool.py` (pool lists and name errors, rank factors, the capacity arithmetic above, the filler
role-guard test, and a small solve proving at most one non-pool player). Full suite: 92 tests OK.

## 6. Doug's decisions (Oct 19)

1. **Pool sizes: QB 10, RB 10, WR 14, TE 8, DST 5, cap 40** (option (a) of section 3; the WR 14 size that built
   150 valid lineups on weeks 4-6). Nothing in the code enforces sizes; this is what Doug sends.
2. **`rank_boost = 0.05` stays.** Ranking is optional (`ranked = true` only when the lists are in rank order).
3. **Auto-raise to 40 is fine** (the standing rule). Beyond 40 pool mode stops and Claude asks Doug: never set
   `raise_cap_to` above 40 or `max_filler` above 1 without his OK.
4. **Questionable pool players follow the model's rule:** held out unless Doug clears them on Sunday (cleared = taken
   off `[status] questionable`, as for the model). No pool exemption.
5. **Week 7 is shadow:** build both sets (model in `weeks/2026-w07/`, pool in `weeks/2026-w07/pool/`), enter the
   model's lineups, grade both with `analyze_results.py` after the slate.

Defaults already match 2 and 3 (`[pool]` in defaults.toml), so no code changed.

Still open: if Doug ever enters the pool lineups with a free entry, the 149-lineup files would come from the same
snippet as for the model (not built for pool mode).
