"""FR-4: generation estimation.

A pvlib model chain: Perez transposition onto the tilted plane, an explicit
cell-temperature model because Delhi summers cost real yield, and the itemised
loss stack from config rather than a single lumped derate.

Two properties of the input data shape this module, and both are reportable:

1. **The chosen irradiance source carries global irradiance only.** Part 3
   selected NASA POWER over PVGIS because it reproduced the measured seasonal
   shape of the campus fleet, but NASA POWER's hourly product gives
   ``ALLSKY_SFC_SW_DWN`` and no beam or diffuse component. Perez transposition
   needs them separately, so the global series must be decomposed first. The
   decomposition is an assumption like any other: run the chain with both
   DIRINT and Erbs and report the spread.

2. **There are ten years of it, not a typical year.** 87,648 hourly rows,
   2014 to 2023. Rather than collapsing that to one year, every year is
   modelled and the annual figure is reported as a mean with its
   year-to-year spread.

The irradiance and temperature half of the chain depends only on the site, not
on the building, so it is computed once per weather source and then scaled by
each roof's capacity. Shading is what will differentiate the roofs, and it
arrives in Part 6; until then ``beam_shading`` is unity and that is stated in
the output rather than left implicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from . import config

if TYPE_CHECKING:  # pragma: no cover - import cost
    import pandas as pd


# --- the parts that need no weather data --------------------------------

def total_loss_fraction(losses: dict[str, float] | None = None) -> float:
    """Combine the itemised losses multiplicatively, not by addition.

    Adding percentages overstates the loss; each stage acts on what the
    previous one passed through.
    """
    losses = losses if losses is not None else config.LOSSES
    remaining = 1.0
    for value in losses.values():
        if not 0.0 <= value < 1.0:
            raise ValueError(f"loss fraction {value} is outside [0, 1)")
        remaining *= 1.0 - value
    return 1.0 - remaining


def specific_yield(annual_energy_kwh: float, capacity_kwp: float) -> float:
    """Annual energy per installed kilowatt, the number the FR-4 band applies to."""
    if capacity_kwp <= 0:
        raise ValueError("capacity must be positive")
    return annual_energy_kwh / capacity_kwp


def capacity_factor(annual_energy_kwh: float, capacity_kwp: float) -> float:
    return specific_yield(annual_energy_kwh, capacity_kwp) / 8766.0


def wind_at_module_height(
    speed_m_s, measured_height_m: float, exponent: float = config.WIND_SHEAR_EXPONENT
):
    """Bring a wind speed to module height by the power law.

    NASA POWER reports wind at 2 m and PVGIS at 10 m. The cell-temperature
    model is sensitive to wind, so comparing the two sources without this
    correction would make the PVGIS case run spuriously cooler.
    """
    if measured_height_m <= 0:
        raise ValueError("measurement height must be positive")
    return speed_m_s * (config.MODULE_WIND_HEIGHT_M / measured_height_m) ** exponent


# --- weather loading ----------------------------------------------------

def load_nasa_hourly(path: Path) -> pd.DataFrame:
    """NASA POWER hourly JSON to a localised frame of ghi, temp_air, wind_speed.

    **The time standard has to be read from the file, not assumed.** The hourly
    API defaults to ``LST`` - local solar time at the requested longitude, where
    hour 12 is solar noon - and returns ``UTC`` only when asked. Our download
    did not ask, so it is LST. Reading those labels as UTC puts solar noon at
    17:00 IST, which silently destroys every transposition, cell temperature and
    yield figure downstream while leaving the annual irradiation total intact.
    The FR-1 work in Part 3 compared annual and monthly totals only, so it is
    unaffected; anything hourly is not.

    Labels mark the *start* of the hour, so the timestamp is moved to the hour's
    midpoint before any solar position is computed. Using the hour start biases
    the sun east all year.
    """
    import json

    import pandas as pd

    document = json.loads(path.read_text(encoding="utf-8"))
    raw = document["properties"]["parameter"]
    header = document.get("header", {})
    standard = header.get("time_standard", "UTC").upper()

    frame = pd.DataFrame(
        {
            "ghi": pd.Series(raw["ALLSKY_SFC_SW_DWN"], dtype="float64"),
            "temp_air": pd.Series(raw["T2M"], dtype="float64"),
            "wind_speed": pd.Series(raw["WS2M"], dtype="float64"),
        }
    )
    labels = pd.to_datetime(frame.index, format="%Y%m%d%H", utc=True)

    if standard == "LST":
        # Local solar time at this longitude: solar noon sits at label hour 12,
        # so the true UTC instant is the label minus longitude/15 hours.
        offset = pd.Timedelta(hours=config.SITE_LON / 15.0)
    elif standard == "UTC":
        offset = pd.Timedelta(0)
    else:
        raise ValueError(
            f"{path.name} reports time_standard {standard!r}; expected LST or UTC"
        )

    frame.index = labels - offset + pd.Timedelta(minutes=30)
    frame = frame.tz_convert(config.SITE_TZ).sort_index()

    fill = float(header.get("fill_value", -999.0))
    if (frame <= fill + 1).to_numpy().any():
        raise ValueError(f"{path.name} carries fill values; check the download")
    frame["wind_speed"] = wind_at_module_height(frame["wind_speed"], 2.0)
    frame.attrs["source"] = "nasa_power"
    frame.attrs["components"] = "global_only"
    frame.attrs["time_standard"] = standard
    frame.attrs["tmy"] = False
    return frame


def load_pvgis_hourly(path: Path) -> pd.DataFrame:
    """PVGIS TMY JSON to the same frame, with its own beam and diffuse components.

    A typical meteorological year is assembled from months of different real
    years, so the timestamps are not contiguous. They are still the true dates
    of each month, which is what the solar position needs.
    """
    import json

    import pandas as pd

    rows = json.loads(path.read_text(encoding="utf-8"))["outputs"]["tmy_hourly"]
    frame = pd.DataFrame(
        {
            "ghi": [float(r["G(h)"]) for r in rows],
            "dni": [float(r["Gb(n)"]) for r in rows],
            "dhi": [float(r["Gd(h)"]) for r in rows],
            "temp_air": [float(r["T2m"]) for r in rows],
            "wind_speed": [float(r["WS10m"]) for r in rows],
        },
        index=pd.to_datetime(
            [r["time(UTC)"] for r in rows], format="%Y%m%d:%H%M", utc=True
        )
        + pd.Timedelta(minutes=30),
    )
    frame = frame.tz_convert(config.SITE_TZ).sort_index()
    frame["wind_speed"] = wind_at_module_height(frame["wind_speed"], 10.0)
    frame.attrs["source"] = "pvgis_tmy"
    frame.attrs["components"] = "measured"
    frame.attrs["tmy"] = True
    return frame


# --- the site chain, computed once ---------------------------------------

@dataclass
class SiteChain:
    """Plane-of-array irradiance and cell temperature for the campus.

    Independent of building, because every candidate array carries the same
    tilt and azimuth. Capacity scales it; shading will differentiate it.
    """

    poa_direct: pd.Series
    poa_diffuse: pd.Series
    cell_temperature: pd.Series
    source: str
    decomposition: str
    is_tmy: bool = False
    # Kept so FR-3's horizons can be evaluated against the same hours without
    # recomputing the solar position for 87,648 rows a second time.
    solar_azimuth: pd.Series | None = None
    solar_elevation: pd.Series | None = None

    @property
    def poa_global(self) -> pd.Series:
        return self.poa_direct + self.poa_diffuse

    def mean_annual_poa_kwh_per_m2(self) -> float:
        """Plane-of-array irradiation in a year, averaged over complete years.

        A typical meteorological year is one nominal year even though its
        timestamps span several real ones, so it is summed whole rather than
        grouped by calendar year.
        """
        poa = self.poa_global
        if self.is_tmy:
            return float(poa.sum()) / 1000.0
        hours = poa.groupby(poa.index.year).size()
        complete = [y for y, n in hours.items() if n >= 8000]
        kept = poa[poa.index.year.isin(complete)]
        return float(kept.sum()) / 1000.0 / len(complete)


def build_site_chain(
    weather: pd.DataFrame,
    decomposition: str | None = None,
    tilt_deg: float | None = None,
) -> SiteChain:
    """Transpose the horizontal irradiance onto the array plane and get cell temperature.

    Steps 1 to 5 of the chain: solar position, decomposition where the source
    supplies global irradiance only, Perez transposition, then cell temperature
    from air temperature and wind.
    """
    from pvlib import irradiance, location, temperature

    decomposition = decomposition or config.DECOMPOSITION_MODEL
    tilt_deg = config.MODULE_TILT_DEG if tilt_deg is None else tilt_deg

    site = location.Location(
        config.SITE_LAT, config.SITE_LON, config.SITE_TZ, config.SITE_ELEVATION_M
    )
    solpos = site.get_solarposition(weather.index)

    if "dni" in weather and "dhi" in weather:
        dni, dhi, used = weather["dni"], weather["dhi"], "source_components"
    else:
        dni, dhi = decompose_global(
            weather["ghi"], solpos["zenith"], weather.index, decomposition
        )
        used = decomposition

    extra = irradiance.get_extra_radiation(weather.index)
    airmass = site.get_airmass(solar_position=solpos)["airmass_relative"]

    poa = irradiance.get_total_irradiance(
        surface_tilt=tilt_deg,
        surface_azimuth=config.MODULE_AZIMUTH_DEG,
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=dni,
        ghi=weather["ghi"],
        dhi=dhi,
        dni_extra=extra,
        airmass=airmass,
        albedo=config.GROUND_ALBEDO,
        model=config.TRANSPOSITION_MODEL,
    ).fillna(0.0)

    cell = temperature.faiman(
        poa_global=poa["poa_global"],
        temp_air=weather["temp_air"],
        wind_speed=weather["wind_speed"],
    )
    return SiteChain(
        poa_direct=poa["poa_direct"],
        poa_diffuse=poa["poa_diffuse"],
        cell_temperature=cell,
        source=weather.attrs.get("source", "unknown"),
        decomposition=used,
        is_tmy=bool(weather.attrs.get("tmy", False)),
        solar_azimuth=solpos["azimuth"],
        solar_elevation=solpos["apparent_elevation"],
    )


def decompose_global(ghi, zenith, index, model: str):
    """Separate a global horizontal series into beam and diffuse.

    Required because the primary source gives global irradiance only. DIRINT is
    the default; Erbs is kept as the sensitivity case, and the difference
    between them is reported rather than hidden.
    """
    import numpy as np
    from pvlib import irradiance

    if model == "dirint":
        dni = irradiance.dirint(ghi, zenith, index).fillna(0.0)
        # Close the energy balance: whatever the beam component does not
        # account for on the horizontal is diffuse. Clipped at the horizon,
        # where cos(zenith) goes to zero and the division is meaningless.
        cos_zenith = np.cos(np.radians(zenith.clip(upper=90.0)))
        dhi = (ghi - dni * cos_zenith).clip(lower=0.0)
        return dni, dhi
    if model == "erbs":
        out = irradiance.erbs(ghi, zenith, index)
        return out["dni"].fillna(0.0), out["dhi"].fillna(0.0)
    raise ValueError(f"unknown decomposition model {model!r}; use dirint or erbs")


# --- per building --------------------------------------------------------

@dataclass
class ChainResult:
    """One building's modelled generation, year by year."""

    building_id: str
    capacity_kwp: float
    annual_kwh: dict[str, float]
    monthly_kwh: dict[int, float]
    source: str
    decomposition: str
    loss_fraction: float
    shading_applied: bool
    sky_view_factor: float = 1.0

    @property
    def mean_annual_kwh(self) -> float:
        return sum(self.annual_kwh.values()) / len(self.annual_kwh)

    @property
    def sd_annual_kwh(self) -> float:
        import statistics

        if len(self.annual_kwh) < 2:
            return 0.0
        return statistics.stdev(self.annual_kwh.values())

    @property
    def specific_yield(self) -> float:
        return specific_yield(self.mean_annual_kwh, self.capacity_kwp)

    @property
    def capacity_factor(self) -> float:
        return capacity_factor(self.mean_annual_kwh, self.capacity_kwp)

    def as_row(self) -> dict[str, float | str]:
        """The register columns this result is responsible for."""
        # Energy is written as whole kilowatt-hours. The register is CSV so that
        # a changed number shows up as a readable diff, and 4.263e+05 is not one.
        return {
            "annual_energy_kwh": round(self.mean_annual_kwh),
            "annual_energy_sd_kwh": round(self.sd_annual_kwh),
            "specific_yield": self.specific_yield,
            "capacity_factor": self.capacity_factor,
            "total_loss_fraction": self.loss_fraction,
            "irradiance_source": self.source,
            "decomposition_model": self.decomposition,
            "shading_applied": "yes" if self.shading_applied else "no",
        }


def run_model_chain(
    building_id: str,
    site: SiteChain,
    capacity_kwp: float,
    beam_shading: pd.Series | None = None,
    losses: dict[str, float] | None = None,
    sky_view_factor: float = 1.0,
) -> ChainResult:
    """Scale the site chain to one roof's capacity and apply the loss stack.

    Steps 6 to 8: DC power with the module temperature coefficient, a flat
    inverter efficiency, then the itemised losses combined multiplicatively and
    applied once.

    ``beam_shading`` is the hourly fraction of beam irradiance that reaches the
    array, so 1.0 is unshaded. It multiplies the direct component only, because
    diffuse light arrives from the whole sky and a neighbouring building does
    not remove all of it. The diffuse share is scaled instead by
    ``sky_view_factor``, the fraction of the sky the array can still see. Part 6
    supplies both.
    """
    from pvlib import pvsystem

    if capacity_kwp <= 0:
        raise ValueError("capacity must be positive")

    if not 0.0 < sky_view_factor <= 1.0:
        raise ValueError(f"sky view factor {sky_view_factor} is not a fraction")

    direct = site.poa_direct if beam_shading is None else site.poa_direct * beam_shading
    poa = direct + site.poa_diffuse * sky_view_factor

    dc_kw = pvsystem.pvwatts_dc(
        effective_irradiance=poa,
        temp_cell=site.cell_temperature,
        pdc0=capacity_kwp,
        gamma_pdc=config.MODULE_TEMP_COEFF_PER_C,
    ).clip(lower=0.0)

    loss = total_loss_fraction(losses)
    ac_kw = dc_kw * config.INVERTER_EFFICIENCY * (1.0 - loss)

    annual, monthly = _annual_and_monthly(ac_kw, site.is_tmy)

    return ChainResult(
        building_id=building_id,
        capacity_kwp=capacity_kwp,
        annual_kwh=annual,
        monthly_kwh=monthly,
        source=site.source,
        decomposition=site.decomposition,
        loss_fraction=loss,
        shading_applied=beam_shading is not None or sky_view_factor < 1.0,
        sky_view_factor=sky_view_factor,
    )


def _annual_and_monthly(
    ac_kw: pd.Series, is_tmy: bool
) -> tuple[dict[str, float], dict[int, float]]:
    """Split an hourly series into annual totals and a mean monthly profile.

    A typical meteorological year is assembled from months taken from different
    real years, so grouping it by calendar year would scatter one year's energy
    across ten buckets. It is one nominal year and is labelled as such.

    For a real multi-year series, any calendar year that is not complete is
    dropped rather than reported as a low year: shifting from local solar time
    to UTC moves a few night hours across the first year boundary, and those
    hours would otherwise appear as a spurious extra year.
    """
    if is_tmy:
        annual = {"tmy": float(ac_kw.sum())}
        monthly = {int(m): float(v) for m, v in ac_kw.groupby(ac_kw.index.month).sum().items()}
        return annual, monthly

    hours = ac_kw.groupby(ac_kw.index.year).size()
    complete = [int(y) for y, n in hours.items() if n >= 8000]
    if not complete:
        raise ValueError("no complete calendar year in the series")

    kept = ac_kw[ac_kw.index.year.isin(complete)]
    annual = {str(int(y)): float(v) for y, v in kept.groupby(kept.index.year).sum().items()}
    monthly = {
        int(m): float(v) / len(complete)
        for m, v in kept.groupby(kept.index.month).sum().items()
    }
    return annual, monthly
