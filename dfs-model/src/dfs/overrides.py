"""Doug's projection reads ([overrides] in week.toml): rescale a player's simulated distribution to a new mean."""
from .project import summarize


def apply(proj, sims, overrides):
    """Returns (proj, sims) with each named player's sims scaled so the mean equals the override.
    Idempotent: re-applying the same reads gives the same result."""
    proj, sims = proj.copy(), sims.copy()
    missing = [n for n in overrides if n not in set(proj.Name)]
    if missing:
        raise KeyError(f'override names not in projections: {missing}')
    for name, mean in overrides.items():
        i = proj.index[proj.Name == name][0]
        sims[i] *= mean / sims[i].mean()
        for col, v in summarize(sims[i], proj.Salary[i]).items():
            proj.loc[i, col] = v
    return proj, sims
