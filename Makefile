.PHONY: audit build check format lint test verify

override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PYTHON ?= python3

format:
	cd "$(ROOT)" && $(PYTHON) -m ruff format --check .

lint:
	cd "$(ROOT)" && $(PYTHON) -m ruff check .
	$(PYTHON) -m compileall -q "$(ROOT)/app.py" "$(ROOT)/scripts" "$(ROOT)/tests"
	$(PYTHON) "$(ROOT)/scripts/check_docs_plans.py"
	$(PYTHON) "$(ROOT)/scripts/test_ffprobe_stderr_contract.py"

test:
	cd "$(ROOT)" && $(PYTHON) -m pytest -q

build:
	$(PYTHON) -m py_compile "$(ROOT)/app.py"

audit:
	env -u PYTHONPATH $(PYTHON) -m pip check
	env -u PYTHONPATH $(PYTHON) -m pip_audit --requirement "$(ROOT)/requirements.txt" --no-deps --disable-pip

verify: format lint test build

check: verify audit
