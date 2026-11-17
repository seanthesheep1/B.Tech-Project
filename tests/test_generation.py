"""FR-4 helpers that do not need the full pvlib chain."""

from __future__ import annotations

import pytest

from btp_solar import config, fr4_generation


def test_losses_combine_multiplicatively_not_additively():
    """Adding the percentages overstates the loss; each acts on what is left."""
    additive = sum(config.LOSSES.values())
    combined = fr4_generation.total_loss_fraction()
    assert combined < additive
    assert combined == pytest.approx(1 - (0.97 * 0.98 * 0.985 * 0.99 * 0.995 * 0.98 * 0.985),
                                     abs=1e-9)


def test_default_loss_stack_is_in_a_believable_range():
    """Roughly 11 to 16 per cent before shading, per the workflow note."""
    assert 0.10 <= fr4_generation.total_loss_fraction() <= 0.16


def test_an_impossible_loss_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        fr4_generation.total_loss_fraction({"soiling": 1.2})


def test_specific_yield_and_capacity_factor_agree():
    energy, capacity = 145_000.0, 100.0
    assert fr4_generation.specific_yield(energy, capacity) == pytest.approx(1450.0)
    assert fr4_generation.capacity_factor(energy, capacity) == pytest.approx(1450.0 / 8766.0)


def test_zero_capacity_is_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        fr4_generation.specific_yield(1000.0, 0.0)


# --- the model chain -----------------------------------------------------
# These need the downloaded irradiance series, so they skip rather than fail on
# a fresh clone. Everything above runs unconditionally.

NASA = config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json"
PVGIS = config.DATA / "pvgis_tmy_28.545_77.192.json"

needs_nasa = pytest.mark.skipif(not NASA.exists(), reason="NASA POWER series not downloaded")
needs_pvgis = pytest.mark.skipif(not PVGIS.exists(), reason="PVGIS TMY not downloaded")


@pytest.fixture(scope="module")
def nasa():
    return fr4_generation.load_nasa_hourly(NASA)


@pytest.fixture(scope="module")
def site_chain(nasa):
    return fr4_generation.build_site_chain(nasa, "dirint")


@needs_nasa
def test_wind_is_brought_to_module_height(nasa):
    """NASA reports at 2 m and PVGIS at 10 m; the cell model needs one height."""
    assert fr4_generation.wind_at_module_height(5.0, 2.0) == pytest.approx(5.0)
    assert fr4_generation.wind_at_module_height(5.0, 10.0) < 5.0
    with pytest.raises(ValueError, match="height must be positive"):
        fr4_generation.wind_at_module_height(5.0, 0.0)


@needs_nasa
def test_local_solar_time_puts_the_sun_overhead_at_midday(nasa):
    """The regression test for the bug that would silently void every yield.

    NASA POWER's hourly API defaults to local solar time, not UTC. Reading
    those labels as UTC moves solar noon to about 17:00 IST: annual irradiation
    is unchanged, so nothing looks wrong, but every transposition and cell
    temperature is computed against the wrong sun.
    """
    assert nasa.attrs["time_standard"] == "LST"
    midday = nasa[nasa.index.hour.isin((11, 12))]["ghi"].mean()
    evening = nasa[nasa.index.hour.isin((17, 18))]["ghi"].mean()
    assert midday > 3 * evening, "solar noon is not where it should be"

    peak_hour = nasa.groupby(nasa.index.hour)["ghi"].mean().idxmax()
    assert peak_hour in (11, 12), f"peak irradiance at hour {peak_hour}, not midday"


@needs_nasa
def test_the_series_reproduces_the_part_3_annual_irradiation(nasa):
    """1744.7 kWh/m2/yr, the figure the FR-1 source decision rests on."""
    years = nasa.groupby(nasa.index.year)["ghi"].agg(["sum", "size"])
    complete = years[years["size"] >= 8000]
    assert len(complete) == 10
    assert complete["sum"].mean() / 1000 == pytest.approx(1744.7, abs=5.0)


@needs_nasa
def test_tilting_south_gains_over_the_horizontal(site_chain, nasa):
    """A 15 degree south plane at 28.5 N must collect more than the horizontal.

    POA below GHI is the signature of a broken transposition - a wrong time
    standard, a wrong azimuth convention or a lost beam component - and it is
    worth one assertion because the failure is otherwise invisible.
    """
    ghi = nasa["ghi"].sum() / 1000
    poa = site_chain.poa_global.sum() / 1000
    assert 1.03 < poa / ghi < 1.20, f"POA/GHI of {poa / ghi:.3f} is not physical"


@needs_nasa
def test_cell_temperature_stays_physical(site_chain):
    """Hot, but not impossible. 100 C would mean the irradiance is misaligned."""
    cell = site_chain.cell_temperature
    assert cell.max() < 85.0
    assert 50.0 < cell.max()
    assert cell.min() > -5.0


@needs_nasa
def test_the_decomposition_choice_barely_moves_a_low_tilt_array(nasa):
    """DIRINT and Erbs disagree on the sky, and at 15 degrees it hardly matters.

    The two models put the diffuse fraction several points apart, but a plane
    tilted only 15 degrees sees almost the whole sky, so the annual total is
    nearly unchanged. That is the justification for not treating the
    decomposition as a major uncertainty at this tilt - and it would not hold
    at 28 degrees.
    """
    dirint = fr4_generation.build_site_chain(nasa, "dirint")
    erbs = fr4_generation.build_site_chain(nasa, "erbs")
    a = fr4_generation.run_model_chain("A", dirint, 100.0).specific_yield
    b = fr4_generation.run_model_chain("B", erbs, 100.0).specific_yield
    assert abs(a - b) / a < 0.02


@needs_nasa
def test_an_unknown_decomposition_model_is_rejected(nasa):
    with pytest.raises(ValueError, match="unknown decomposition"):
        fr4_generation.build_site_chain(nasa, "guesswork")


@needs_nasa
def test_specific_yield_lands_in_the_fr4_band(site_chain):
    result = fr4_generation.run_model_chain("B01", site_chain, 288.6)
    assert config.SPECIFIC_YIELD_RANGE[0] <= result.specific_yield <= config.SPECIFIC_YIELD_RANGE[1]


@needs_nasa
def test_ten_complete_years_are_modelled_and_none_is_spurious(site_chain):
    """Shifting from local solar time to UTC moves night hours across a year
    boundary; a partial year must be dropped, not reported as a bad year."""
    result = fr4_generation.run_model_chain("B01", site_chain, 288.6)
    assert sorted(result.annual_kwh) == [str(y) for y in range(2014, 2024)]
    assert result.sd_annual_kwh / result.mean_annual_kwh < 0.05


@needs_nasa
def test_energy_scales_linearly_with_capacity(site_chain):
    """No part of the chain may depend on array size in this pass."""
    small = fr4_generation.run_model_chain("S", site_chain, 50.0)
    large = fr4_generation.run_model_chain("L", site_chain, 500.0)
    assert large.mean_annual_kwh == pytest.approx(10 * small.mean_annual_kwh, rel=1e-9)
    assert large.specific_yield == pytest.approx(small.specific_yield, rel=1e-9)


@needs_nasa
def test_shading_reduces_output_and_is_recorded(site_chain):
    """Beam shading must bite, must touch only the beam, and must be declared."""
    import pandas as pd

    unshaded = fr4_generation.run_model_chain("U", site_chain, 100.0)
    half = pd.Series(0.5, index=site_chain.poa_direct.index)
    shaded = fr4_generation.run_model_chain("S", site_chain, 100.0, beam_shading=half)

    assert shaded.mean_annual_kwh < unshaded.mean_annual_kwh
    # Diffuse light survives, so halving the beam must not halve the output.
    assert shaded.mean_annual_kwh > 0.5 * unshaded.mean_annual_kwh
    assert unshaded.as_row()["shading_applied"] == "no"
    assert shaded.as_row()["shading_applied"] == "yes"


@needs_nasa
def test_a_roof_with_no_capacity_is_rejected(site_chain):
    with pytest.raises(ValueError, match="capacity must be positive"):
        fr4_generation.run_model_chain("X", site_chain, 0.0)


@needs_pvgis
def test_a_typical_year_is_one_year_not_ten():
    """A TMY borrows months from different real years. Grouped by calendar year
    its energy scatters across a decade and the annual figure comes out ten
    times too small."""
    chain = fr4_generation.build_site_chain(fr4_generation.load_pvgis_hourly(PVGIS))
    assert chain.is_tmy
    result = fr4_generation.run_model_chain("B01", chain, 100.0)
    assert list(result.annual_kwh) == ["tmy"]
    assert result.specific_yield > 1000.0
    assert 1800 < chain.mean_annual_poa_kwh_per_m2() < 2400


@needs_nasa
@needs_pvgis
def test_pvgis_still_reads_high_on_a_tilted_plane(nasa):
    """The FR-1 disagreement does not go away; tilt amplifies it.

    Part 3 found PVGIS 10.1 per cent high on annual GHI, concentrated in
    winter. Tilt gain is largest when the sun is lowest, so the gap widens on
    the array plane. This pins the direction and rough size, so that FR-4's
    cross-check failing is a known consequence rather than a surprise.
    """
    ours = fr4_generation.run_model_chain(
        "A", fr4_generation.build_site_chain(nasa, "dirint"), 100.0).specific_yield
    theirs = fr4_generation.run_model_chain(
        "B", fr4_generation.build_site_chain(fr4_generation.load_pvgis_hourly(PVGIS)),
        100.0).specific_yield
    assert theirs > ours
    assert 0.10 < (theirs - ours) / ours < 0.25


@needs_nasa
def test_a_reduced_sky_view_cuts_the_diffuse_but_not_the_beam(site_chain):
    """Obstructions take diffuse light by blocking sky, beam by blocking the sun.

    The two are applied separately, so a roof that sees less sky must lose
    output even with the sun in full view all year.
    """
    open_sky = fr4_generation.run_model_chain("O", site_chain, 100.0)
    enclosed = fr4_generation.run_model_chain("E", site_chain, 100.0, sky_view_factor=0.8)

    assert enclosed.mean_annual_kwh < open_sky.mean_annual_kwh
    # Diffuse is roughly half the plane-of-array total here, so a fifth off the
    # diffuse must not take a fifth off the output.
    assert enclosed.mean_annual_kwh > 0.85 * open_sky.mean_annual_kwh
    assert enclosed.as_row()["shading_applied"] == "yes"
    assert open_sky.as_row()["shading_applied"] == "no"


@needs_nasa
def test_an_impossible_sky_view_factor_is_rejected(site_chain):
    for bad in (0.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="not a fraction"):
            fr4_generation.run_model_chain("X", site_chain, 100.0, sky_view_factor=bad)


@needs_nasa
def test_lowering_the_tilt_raises_the_winter_share(nasa):
    """The physics behind the tilt sweep: tilt gain is largest when the sun is
    lowest, so a flatter array puts less of its year into winter. If this ever
    inverts, the conclusion drawn from the back-test does not hold."""
    def winter_share(tilt):
        chain = fr4_generation.build_site_chain(nasa, tilt_deg=tilt)
        result = fr4_generation.run_model_chain("T", chain, 100.0)
        total = sum(result.monthly_kwh.values())
        return sum(result.monthly_kwh[m] for m in (1, 2, 11, 12)) / total

    assert winter_share(0.0) < winter_share(15.0) < winter_share(28.0)


@needs_nasa
def test_specific_yield_rises_with_tilt_but_the_roof_is_what_is_fixed(nasa):
    """Steeper arrays earn more per kilowatt and fit fewer kilowatts on a roof.
    Reporting specific yield alone would recommend the wrong design."""
    yields = {}
    for tilt in (0.0, 15.0, 28.0):
        chain = fr4_generation.build_site_chain(nasa, tilt_deg=tilt)
        yields[tilt] = fr4_generation.run_model_chain("T", chain, 100.0).specific_yield
    assert yields[0.0] < yields[15.0] < yields[28.0]
