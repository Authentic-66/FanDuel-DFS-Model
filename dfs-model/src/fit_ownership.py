"""Fit the ownership model on every week with FanDuel results up to and including --week and report cross-validated
fit by position -> weeks/<week>/ownership_cv.csv (per-player out-of-fold predictions) and ownership_fit.csv."""
from dfs import config, ownership

week, cfg, a = config.cli(__doc__, [(['--refresh'], dict(action='store_true',
                                                           help='rebuild cached ownership_train.csv frames'))])
oc = cfg['ownership']
train, weeks = ownership.training_set(week, oc, refresh=a.refresh, include_self=True)
if train is None:
    raise SystemExit(f'no results_players.csv at or before {week.name}')
oof = ownership.cross_validate(train, oc)
rep = ownership.fit_report(train, oof)
cv = 'leave-one-week-out' if len(weeks) > 1 else f'{oc["folds"]}-fold within the week'
print(f'Ownership model: weeks {", ".join(weeks)}; {len(train)} players; CV = {cv}')
print('Fit on players with actual >= 1% or Proj >= 5 (r on %, r on log %, MAE in % points; null = position average):')
print(rep.to_string(index=False))
model = ownership.fit(train, oc)
print('\nStandardized coefficients (logit scale, full fit):')
for c, b in sorted(zip(model['cols'], model['coef']), key=lambda t: -abs(t[1])):
    print(f'  {c:12s} {b:+.2f}')
out = train.assign(Own_pct=(train.own * 100).round(2), Own_cv=(oof * 100).round(2))
out = out.drop(columns='own').sort_values('Own_pct', ascending=False)
print('\nTop 20 actual ownership vs cross-validated prediction:')
print(out.head(20)[['week', 'Name', 'Pos', 'Salary', 'Proj', 'Own_pct', 'Own_cv']].to_string(index=False))
out.to_csv(week.output('ownership_cv.csv'), index=False)
rep.to_csv(week.output('ownership_fit.csv'), index=False)
