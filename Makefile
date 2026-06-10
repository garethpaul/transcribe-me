.PHONY: audit build check format lint test verify

PYTHON ?= python3

format:
	$(PYTHON) -m ruff format --check .

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m compileall -q app.py scripts tests
	$(PYTHON) scripts/check_docs_plans.py

test:
	$(PYTHON) -m pytest -q

build:
	$(PYTHON) -m py_compile app.py

audit:
	$(PYTHON) -m pip_audit --requirement requirements.txt --no-deps --disable-pip

verify: format lint test build

check: verify audit
