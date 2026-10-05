"""Phase 2 #2: what leverage would have done on an archived slate. Rebuilds --week (current model + its overrides),
runs the optimizer per [optimizer.leverage] setting with (a) cross-validated predicted ownership and (b) actual
ownership (oracle), and grades lineups vs FanDuel results -> weeks/<week>/backtest_leverage.csv.
One slate is one draw of outcomes: read differences as a sketch, not a validation."""
import pandas as pd

from dfs import backtest as bt, config

week, cfg, a = config.cli(__doc__, [(['--weights'], dict(default='0.1,0.2,0.5,1.0', help='own_weight grid')),
                                    (['--caps'], dict(default='70,60', help='max_lineup_own grid (%)'))])
field = cfg['contest']['field_size']
settings = [dict(enabled=False)]
settings += [dict(enabled=True, own_weight=float(w)) for w in a.weights.split(',')]
settings += [dict(enabled=True, own_weight=0.0, stack_exponent=1.0), dict(enabled=True, own_weight=0.2, stack_exponent=1.0)]
settings += [dict(enabled=True, own_weight=0.0, max_lineup_own=float(c)) for c in a.caps.split(',')]
res = bt.leverage_backtest(week, cfg, settings, field, sources=('cv', 'actual'))
res.to_csv(week.output('backtest_leverage.csv'), index=False)
pd.set_option('display.width', 250)
cols = ['own_source', 'own_weight', 'stack_exponent', 'max_lineup_own', 'mean', 'sd', 'best', 'best_rank',
        'top_1pct', 'top_10pct', 'proj', 'own_proj', 'own_actual']
print(res.reindex(columns=cols).round(2).to_string(index=False))
act = pd.read_csv(week.results_players)['%Drafted'] * 100
print('Field reference: a random field lineup holds ~%.0f%% summed ownership (sum of own^2 / 100)' % ((act ** 2).sum() / 100))
