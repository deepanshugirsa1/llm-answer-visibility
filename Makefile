PY ?= python3
export PYTHONPATH := src

.PHONY: install test run report check baseline all clean

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -q

run:
	$(PY) -m lav.cli run

report:
	$(PY) -m lav.cli report --out data/report.json

check:
	$(PY) -m lav.cli check --baseline data/baseline.json

baseline: report
	cp data/report.json data/baseline.json

all: run report check

clean:
	rm -rf data .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
