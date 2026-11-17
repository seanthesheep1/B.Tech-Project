.PHONY: setup test lint register clean
PY := uv run

setup:                ## create the pinned environment
	uv sync --extra dev

test:                 ## run the acceptance-criterion and geometry tests
	$(PY) pytest -q

lint:
	$(PY) ruff check .

register:             ## print the building register with provenance
	$(PY) python scripts/show_register.py

fr1:                  ## FR-1  fetch irradiance, run the 5% agreement check
	$(PY) python scripts/run_fr1_data.py

fr2:                  ## FR-2  usable area from the digitised geometry
	$(PY) python scripts/run_fr2_from_gpkg.py

fr4:                  ## FR-4  model generation for every candidate roof
	$(PY) python scripts/run_fr4_generation.py

fr3:                  ## FR-3  shading from neighbours, parapets and roof clutter
	$(PY) python scripts/run_fr3_shading.py

backtest:             ## FR-4  seasonal shape back-test against the metered fleet
	$(PY) python scripts/run_fr4_backtest.py

tilt:                 ## what tilt buys, once row spacing is counted against yield
	$(PY) python scripts/run_tilt_tradeoff.py

audit:                ## what each stage consumes and produces, and if it is current
	uv run python scripts/run_pipeline_audit.py

map:                  ## the Solar Map: ten roofs on the campus, two panels
	uv run python scripts/run_solar_map.py

economics:            ## what the potential costs and what it is worth
	uv run python scripts/run_economics.py

soiling:              ## does Delhi dust explain the back-test's winter bias?
	uv run python scripts/run_soiling.py

heights:              ## try to measure obstruction heights from their shadows
	uv run python scripts/run_shadow_heights.py

sensitivity:          ## how much FR-3 rests on the unmeasured obstruction heights
	uv run python scripts/run_obstruction_sensitivity.py

alarm:                ## the solar alarm: which plants have stopped or are sliding
	$(PY) python scripts/run_alarm.py

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__
