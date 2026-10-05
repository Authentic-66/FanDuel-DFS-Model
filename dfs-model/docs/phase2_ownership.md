# Phase 2 #2: Ownership model and leverage (Oct 5, 2026)

**Status:** ownership projection is ON (`[ownership]`). It adds `Own_proj` to proj.csv/projections.csv,
`Own_proj_%` / `Exp_minus_Own` to exposure.csv, and writes stacks.csv. **Leverage in the optimizer is OFF**
(`[optimizer.leverage] enabled = false`). With leverage off the lineups are bit-identical to the previous code (checked).

## The model
- Target: logit(%Drafted), with a floor of 0.5%. Anything under 0.5% counts as "contrarian" and isn't modelled finer.
- Features, all known before lock: log salary, our projection *after Doug's overrides*, value (proj per $1k), FanDuel
  FPPG, team implied total, game total, volume gained from OUT teammates (`GainedVol`, targets + carries per game), and
  position intercepts. Each feature is a key in the `[ownership] features` list in the config.
- Ridge regression (λ = 10, standardized features), fit on players projected ≥ 2. After fitting, each position gets a
  logit shift so its total ownership matches what the field has to roster: QB 100%, DST 100%, and RB/WR/TE at their
  training shares (week 4: 256% / 322% / 119%; the FLEX goes RB > WR > TE).
- Training rows: each results week is rebuilt as it stood before lock (current model plus that week's overrides) and
  cached in `weeks/<week>/ownership_train.csv`. The model is refit on every run from all earlier results weeks, so week 5
  uses week 4, week 6 uses weeks 4–5, and so on. If the projection model changes materially, delete the cache.
- Why the post-override projection: Doug's reads capture news that the field sees too. They fit slightly better than
  the raw model (CV MAE 3.0 vs 3.2).

## Fit on week 4 (10-fold CV within the slate; `python src/fit_ownership.py --week 2026-w04`)
Scored on players with actual ≥ 1% or Proj ≥ 5, a set that doesn't depend on the model. Null = each player gets the
position's average ownership.

| Pos | n | r (%) | r (log %) | MAE (pts) | null MAE |
|---|---|---|---|---|---|
| QB | 28 | 0.60 | 0.57 | 2.4 | 2.8 |
| RB | 43 | 0.61 | 0.84 | 3.6 | 5.6 |
| WR | 65 | 0.53 | 0.79 | 3.5 | 4.3 |
| TE | 26 | 0.72 | 0.82 | 2.4 | 4.0 |
| DST | 22 | 0.55 | 0.26 | 2.9 | 3.1 |
| **All** | 184 | 0.56 | 0.73 | **3.2** | 4.2 |

Largest coefficients: value (+0.40), salary (+0.29), projection (+0.28), FPPG (+0.27), gained volume (+0.13). Implied
total and game total add almost nothing.

**Sanity check failed: Parker Washington comes out at 4.6% (actual 30.2%).** No pre-lock feature we have marks him.
He was $7,100 with a 12.8 projection (1.80 pts/$1k, below average for a WR), had no injury news, and his JAC teammates
were all active. Same miss for the other mid-priced chalk: Aaron Jones 6% (actual 40%), Jeremiyah Love 5% (33%), Jordan
Addison 6% (23%), Travis Kelce 4% (21%), Michael Wilson 4% (20%), Bears DST 5% (20%). The model overshoots the top
projections: JSN 49% (24%), Josh Allen 20% (13%). In short, the field is flatter and more narrative-driven than any
projection-based model will be. QB ownership is the weakest part (Stroud 2.6% vs 11.5%, Lawrence 2.7% vs 10.6%).

**Lead worth tracking: the FanDuel "Guru" lineup.** The Guru lineup Doug was served (and entered as his 150th) had six
players owned 17–40%: Jones 40%, JSN 24%, Addison 23%, Kelce 21%, Higgins 20%, B. Allen 19%, plus MIN DST at 18%. In a
$0.05 field, FanDuel's in-app suggestions look like a big source of chalk. Adding a Guru flag in CV improved RB/TE fit,
but that coefficient comes from 9 players in one week, so it is **not** in the model. The week-4 list is saved as
`[contest] guru` in `config/2026-w04/week.toml`. Recording it every week (and any FanDuel projection shown pre-lock)
is the cheapest way to fix the mid-price-chalk miss.

**Stacks would not have been fixed.** With CV ownership, stacks.csv would have flagged only BUF as CHALK. It would have
rated JAC as our most contrarian stack (Lawrence 2.7%) when it was actually chalk (10.6%, P. Washington 30%). HOU (Stroud
11.5%) was also chalk and wasn't flagged. So this model would have repeated the week-4 Jaguars mistake.

## Leverage options (config, `[optimizer.leverage]` in defaults.toml or week.toml)
- `own_weight`: points subtracted from each player's objective per 1% projected ownership. Summed over the lineup,
  that penalizes the lineup's total ownership.
- `max_lineup_own`: hard cap on a lineup's summed projected ownership (%; 0 = off).
- `stack_exponent`: stack-team draw weight × (mean field QB own / team's QB own)^exponent (0 = off).
- stacks.csv (written whenever Own_proj exists): our stack share vs the QB's projected ownership, top receivers,
  CHALK flag (QB ≥ `[ownership] chalk_qb_own` = 10%), and Leverage = our share / field share (< 1 = chalkier than the field).

## Week-4 leverage backtest (`python src/backtest_leverage.py --week 2026-w04`; `weeks/2026-w04/backtest_leverage.csv`)
Setup: week 4 rebuilt with the current model (prior blend on) and Doug's overrides and review lists, 150 lineups per
setting, scored against actual FanDuel points. Ranks come from results_top2000 and the field quantiles (596,809 entries).
"cv" = out-of-fold predicted ownership, which is roughly what a pre-lock model could have known. "actual" = real
%Drafted, an oracle showing the most that leverage could do.

| Ownership | Setting | Mean | Best (rank) | Top 1% | Top 10% | Lineup proj | Lineup own: pred / actual |
|---|---|---|---|---|---|---|---|
| — | **off (baseline)** | 112.8 | 182.2 (617) | 2 | 20 | 126.2 | 73 / 88 |
| cv | own_weight 0.1 | 112.1 | 168.4 (4,618) | 2 | 18 | 125.7 | 72 / 90 |
| cv | own_weight 0.2 | 113.2 | 177.3 (1,232) | 6 | 21 | 124.8 | 69 / 86 |
| cv | own_weight 0.5 | 111.3 | 174.0 (1,756) | 2 | 20 | 121.3 | 60 / 83 |
| cv | own_weight 1.0 | 107.3 | 157.9 (13,809) | 0 | 13 | 116.0 | 51 / 74 |
| cv | stack_exponent 1 | 110.2 | 168.7 (4,533) | 2 | 19 | 125.5 | 72 / 88 |
| cv | 0.2 + stack 1 | 111.8 | 179.4 (991) | 6 | 16 | 124.6 | 70 / 86 |
| cv | cap 70% | 110.0 | 167.2 (4,962) | 2 | 23 | 123.1 | 64 / 86 |
| cv | cap 60% | 109.9 | 171.4 (3,754) | 2 | 25 | 119.4 | 57 / 80 |
| actual | own_weight 0.1 | 112.7 | 197.5 (65) | 3 | 18 | 125.8 | 83 |
| actual | own_weight 0.2 | 113.2 | 178.7 (1,054) | 4 | 22 | 124.7 | 74 |
| actual | own_weight 0.5 | 112.9 | 164.6 (5,712) | 1 | 21 | 121.7 | 62 |
| actual | own_weight 1.0 | 107.6 | 171.8 (3,645) | 1 | 16 | 114.9 | 50 |
| actual | stack_exponent 1 | 110.8 | 195.0 (87) | 5 | 20 | 126.1 | 85 |
| actual | cap 70% | 115.0 | 174.3 (1,672) | 2 | 18 | 122.0 | 65 |

Field reference: a random field lineup holds about 128% summed ownership. Week-4 field average score was 107.3.

What this does and doesn't say:
- **One slate can't validate leverage.** The best-lineup rank swings from 65 to 1,054 between two neighbouring oracle
  settings (0.1 vs 0.2) and from 617 to 4,618 between off and 0.1. That is one lineup's luck, not a signal. Top-1% counts
  are 0–6 out of 150. Mean differences of 1–2 points are inside the noise too, since the 150 lineups are highly correlated.
- **Our lineups were already low-owned.** Even with leverage off, they summed to 88% actual ownership vs about 128% for
  the field. Doug's 25-lineup caps, red/yellow lists and starters-only rule already do much of what a leverage term does.
- **Predicted leverage is partly an illusion.** With CV ownership, a 0.5 penalty cuts *predicted* lineup ownership from
  73% to 60%, but *actual* only from 88% to 83%. The model can't see the mid-priced chalk, so it ends up fading the wrong
  players.
- **Heavy penalties cost real points.** own_weight 1.0 costs about 10 points of lineup projection and was the worst
  setting on actuals, with both cv and actual ownership. 0.2 cost about 1.4 points of projection and was not worse on
  this slate. If Doug wants to try leverage, 0.2 is the most defensible starting value, and it is still unvalidated.
- Down-weighting chalk stacks (`stack_exponent`) moved stacks toward teams the model thought were contrarian (SEA,
  from Darnold's low projected ownership) and away from BUF/SF. With the stack misses above, that isn't trustworthy yet.

## Next
- Refit weekly. With 2+ weeks the CV is leave-one-week-out, the honest test of next-week prediction. Re-check the
  Parker-Washington-type misses as weeks accumulate.
- Record `[contest] guru` (pre-lock) and `[contest] field_size` each week. Test a Guru feature once there are 3+ weeks.
- Re-run backtest_leverage on every new week. Consider turning leverage on only after the effect holds up on several slates.
