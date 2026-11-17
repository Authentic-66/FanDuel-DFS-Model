# NFL cheat sheet (the commands Doug runs himself, weeks 11-12)

Run everything from the model folder (PowerShell or Git Bash):

```
cd "D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model"
```

`<week>` = `2026-w11` or `2026-w12` (both are already set up in `config/<week>/week.toml`). The model, rules and
sets are **frozen through week 12** (Doug, Nov 16). **Entry = 20 lineups ($1): the flex shadow's 20
highest-projected lineups.** Every other set is built and graded on paper.

## 1. Friday update (after FanDuel's Friday injury tags)

1. Download FanDuel's player list for the Sunday main slate. Save it as `data/<week>/fd_players_friday.csv`.
   Optional, record only: FanDuel Research projections as `data/<week>/fdr_projections_fri.csv`.
2. Run:

   ```
   python src/weekly.py --week <week> --stage friday
   ```

   It takes 5-8 minutes. It diffs the list against the previous one, refreshes the nflverse stats, sets statuses
   from FanDuel's tags, fetches the lines, runs the model and builds every set, checks them, and writes the
   **preview** entry to `weeks/<week>/entry_20/upload.csv`. Don't upload the preview.
3. Review sheet (news calls only):

   ```
   python src/review_sheet.py --week <week> build
   ```

   Open `data/<week>/review_sheet.xlsx`. Mark only news-based calls (a backup who becomes the starter, a player back from IR, a real role change):
   - **Color** = `red` (left out of every set).
   - **Cap** = a number (most lineups he can be in).
   - **Note** = why.

   Save it as `data/<week>/review_sheet_reviewed.xlsx`, then run:

   ```
   python src/review_sheet.py --week <week> apply
   python src/weekly.py --week <week> --stage friday --keep-list --no-fetch
   ```

   `apply` prints the reds, caps and notes it wrote into `week.toml`. Check them.

**Check in the Friday output:**
- The player-list changes (new O / Q tags, players added or removed).
- `statuses: N out ..., N questionable (held out): ...`: the Q list is everyone FanDuel tags Q. They stay out of
  lineups unless FanDuel clears them by Sunday.
- `stack weights: ...`. A team at 1-3 has a low implied total.
- The model warnings (after `--- model.py ---`), especially **a team with no starting QB** or the wrong starter.
  Fix it in `week.toml` under `[status.starting_qb]` (e.g. `SEA = "Drew Lock"`, exact FanDuel name) and rerun with
  `--keep-list --no-fetch`. A team with no starting QB gets 0 stacks.
- `--- rule check ---`: every set `0 problems`. "N under $59,000" is allowed (salary-floor fallback).
- If the run stops with `INVALID` or `FAILED`, don't upload anything. The message says which step. Lines not yet
  posted for a game: rerun later, or add `--keep-lines` to keep the existing `lines.csv`.

## 2. Sunday final (after about 11:30 CT, when the early-game inactives are out)

1. Download FanDuel's player list again and save it as `data/<week>/fd_players_sunday.csv`. FanDuel marks official
   inactives `NA`. The script counts them as out.
2. Run:

   ```
   python src/weekly.py --week <week> --stage sunday
   ```

3. **Upload file: `weeks/<week>/entry_20/upload.csv`** (FanDuel: Upload lineups, 20 entries). The 20 lineups
   with names are in `entry_20/readable.csv`, and player counts are in `entry_20/exposure.csv`.

**Check in the Sunday output** (same as Friday, plus):
- `=== ENTRY (upload this): ... ===`, `20 lineups from flex_shadow`, the stacks and the most-used players. If
  it says `PREVIEW`, you ran `--stage friday`.
- 4pm-game players FanDuel still tags Q stay out (inactives for late games come out after you upload). That's the
  standing pull-questionables rule.

### Late news (clear or cap a player)

Edit `config/<week>/week.toml`, in the DOUG'S CALLS part at the top or the `[prefs]` blocks:
- Clear a player FanDuel still shows Q / O / IR: add him to `active = ["Exact Name"]` under `[status]`.
- Cap a player: under `[prefs.player_cap]` add `"Exact Name" = 3` (at most 3 lineups per set).
- Rule a player out on news: add him to `out = [...]`, or to `red = [...]` in `[prefs]`.
- New starter: `[status.starting_qb]` `TEAM = "Name"`; a backup RB / WR taking the job: `[prefs.starter_override]`
  `TEAM = ["Name"]`.

Then rerun without re-reading the list:

```
python src/weekly.py --week <week> --stage sunday --keep-list --no-fetch
```

- **Not uploaded yet:** upload the new `entry_20/upload.csv`.
- **Already uploaded:** the rerun saved the earlier entry in `entry_20_<HHMM>/`. On the contest's edit-entries page,
  download the edit-entries file (header starts `entry_id,contest_id,...`), save it in `data/<week>/`, then run:

  ```
  python src/edit_entries.py --week <week> --template data/<week>/<that file>.csv
  ```

  Upload `weeks/<week>/entry_20/edit_entries.csv` on the edit-entries page. It prints how many entries changed. Any
  entry that wasn't one of the uploaded 20 (a free entry) is left as it was.

## 3. After the slate (Monday or Tuesday)

1. Download the contest's All Entries export into `data/<week>/raw/` (the file name doesn't matter). Save the Prizes
   tab as `data/<week>/prizes_pooch-punt.csv` (`rank_from,rank_to,prize`) if the prize table changed. Without
   it, the latest earlier table is used.
2. Run:

   ```
   python src/paper_results.py
   ```

   It updates `docs/paper_results.md` (net by week for every set, full and top 20, plus the entered row) and
   `docs/paper_results.csv`. The ENTERED row is your 20 as entered: won, net, cashed, best.
3. Note the winnings and anything odd (inactives, late swaps) for the week-12 summary.

## What is frozen (weeks 11-12)

No rule changes and no new tests (bug fixes only). The model, `config/defaults.toml` and the set list in
`src/weekly.py` stay the same. Your weekly calls (news reds, caps, statuses, starting QBs, starter overrides, extra stack
receivers) are inputs, not rule changes. The pool set stops: it needs a full pool review. After week 12: one-page
summary of the paper results, then you decide whether to continue.

## Files

| What | Where |
|---|---|
| Your calls | `config/<week>/week.toml` (top part + `[prefs]`) |
| Automatic statuses + stack weights (rewritten each run) | `config/<week>/auto.toml` |
| Lines | `data/<week>/lines.csv` |
| Entry (upload) | `weeks/<week>/entry_20/upload.csv` |
| Every set | `weeks/<week>/` (model) and `model_cap45/`, `flex_shadow/`, `nodraw/`, `median70*/` |
| Run logs | `weeks/<week>/model_log.txt`, `build_log_*.txt` |
| Paper table | `docs/paper_results.md`, `docs/paper_results.csv` |
