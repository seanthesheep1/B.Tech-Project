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

fr2:                  ## FR-2  usable area from setback + derived GCR
	$(PY) python scripts/run_fr2_usable_area.py

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__
