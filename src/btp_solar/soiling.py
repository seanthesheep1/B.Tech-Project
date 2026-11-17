"""Dust on the glass: the one loss the weather both causes and removes.

The back-test leaves a residual with a definite sign. The model puts more
energy into the winter months than the fleet actually delivers, and the gap
survived everything thrown at it: shading moved the shape error from 0.101 to
0.097, and the row-spacing suspicion turned out to be unfounded. Soiling is
what is left, and it is the only candidate whose seasonality matches.

Why Delhi makes this a seasonal story rather than a constant derate
-------------------------------------------------------------------
NASA POWER's daily rainfall for this point, averaged over 2014 to 2023:

    Jul 238 mm   Aug 160 mm   Sep 118 mm        monsoon, panels washed
    Nov   3 mm   Dec   8 mm   Feb  15 mm        effectively no rain at all

November averages **one wet day every ten years**. Dust therefore accumulates
from October through to the pre-monsoon showers with almost nothing to remove
it, and it does so over exactly the months the back-test says the model is too
optimistic. A flat annual soiling percentage cannot produce that; it would
lower every month equally and leave the shape untouched.

Avoiding the obvious trap
-------------------------
It would be easy, and wrong, to tune the soiling rate until the back-test
passes and then report that the back-test passes. The rate would have absorbed
whatever the model was getting wrong, soiling or not, and the agreement would
mean nothing.

So the rate is never fitted. It is swept across the band the published
literature reports for northern India, the whole curve is reported, and the
question asked is a falsifiable one: *does a physically ordinary amount of dust
account for the residual, or does it take an absurd amount?* An answer at
0.1%/day would be evidence. An answer needing 3%/day would be evidence against,
and would be reported as such.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import config

#: Kimber's threshold: rain past this in a day is taken to wash the modules.
#: 6 mm is roughly the quarter-inch the model was published with.
CLEANING_THRESHOLD_MM = 6.0

#: Days after a wash during which the ground stays damp and dust does not lift.
GRACE_PERIOD_DAYS = 14

#: Ceiling on accumulated loss. Dust self-limits: a thick layer sheds.
MAX_SOILING = 0.30

#: The band swept, as a fraction of output lost per dry day. Reported
#: measurements in northern India sit between a few tenths of a percent and
#: about one percent a day through the dry season; the sweep is deliberately
#: wider at both ends so the answer is not boxed in by the prior.
SOILING_RATE_SWEEP = (0.0005, 0.0010, 0.0015, 0.0020, 0.0030, 0.0050, 0.0080)

#: pvlib's own default, carried as the neutral reference point.
DEFAULT_SOILING_RATE = 0.0015


def load_daily_rainfall(path: Path):
    """NASA POWER daily PRECTOTCORR as a pandas Series indexed by date.

    POWER marks absent days with a large negative sentinel rather than a null,
    which would read as negative rainfall and silently suppress every wash.
    """
    import pandas as pd

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    values = document["properties"]["parameter"]["PRECTOTCORR"]
    index = pd.to_datetime(list(values.keys()), format="%Y%m%d")
    series = pd.Series(list(values.values()), index=index, dtype=float)
    series = series.where(series > -900.0)
    if series.isna().all():
        raise ValueError(f"{path} carries no usable rainfall")
    return series.interpolate(limit_direction="both").clip(lower=0.0)


def soiling_loss(
    rainfall,
    soiling_rate: float = DEFAULT_SOILING_RATE,
    cleaning_threshold_mm: float = CLEANING_THRESHOLD_MM,
    grace_period_days: int = GRACE_PERIOD_DAYS,
    max_soiling: float = MAX_SOILING,
    manual_wash_dates=None,
):
    """Fraction of output lost to dust on each day, by the Kimber model."""
    from pvlib import soiling as pvlib_soiling

    if not 0.0 <= soiling_rate < 1.0:
        raise ValueError(f"soiling rate {soiling_rate} is not a daily fraction")
    return pvlib_soiling.kimber(
        rainfall,
        cleaning_threshold=cleaning_threshold_mm,
        soiling_loss_rate=soiling_rate,
        grace_period=grace_period_days,
        max_soiling=max_soiling,
        manual_wash_dates=manual_wash_dates,
    )


def monthly_mean_loss(loss) -> list[float]:
    """Average soiling loss in each calendar month, January first."""
    grouped = loss.groupby(loss.index.month).mean()
    return [float(grouped.get(month, 0.0)) for month in range(1, 13)]


def apply_monthly(monthly_energy: list[float], monthly_loss: list[float]) -> list[float]:
    """Knock the month's soiling loss off that month's energy."""
    if len(monthly_energy) != 12 or len(monthly_loss) != 12:
        raise ValueError("both series must be twelve months long")
    return [e * (1.0 - l) for e, l in zip(monthly_energy, monthly_loss)]


def annual_loss(monthly_energy: list[float], monthly_loss: list[float]) -> float:
    """Energy-weighted annual soiling loss.

    Weighted, not a plain average of the twelve: the dirtiest months in Delhi
    are also among the dimmest, so an unweighted mean overstates what soiling
    actually costs over a year.
    """
    before = sum(monthly_energy)
    if before <= 0:
        raise ValueError("no energy to lose")
    return 1.0 - sum(apply_monthly(monthly_energy, monthly_loss)) / before


def cleaning_schedule(dates, rainfall):
    """Wash dates as a pandas DatetimeIndex, for a manual cleaning regime.

    Kept separate from the weather so a proposed cleaning contract can be
    priced against the dust it would actually remove, rather than assumed to
    deliver a round number.
    """
    import pandas as pd

    index = pd.DatetimeIndex(pd.to_datetime(list(dates)))
    inside = index[(index >= rainfall.index.min()) & (index <= rainfall.index.max())]
    if len(inside) != len(index):
        raise ValueError("some wash dates fall outside the rainfall record")
    return inside


def washes_each_year(rainfall, months: tuple[int, ...], day: int = 15):
    """A recurring wash on the same day of the given months, every year."""
    import pandas as pd

    years = sorted({d.year for d in rainfall.index})
    dates = [
        pd.Timestamp(year=y, month=m, day=day)
        for y in years
        for m in months
    ]
    return cleaning_schedule(
        [d for d in dates if rainfall.index.min() <= d <= rainfall.index.max()],
        rainfall,
    )
