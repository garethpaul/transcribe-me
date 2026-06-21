.DEFAULT_GOAL := check
.PHONY: __repository-make-authority audit build check format lint root-test test verify
.SECONDEXPANSION:

PYTHON ?= python3
override PYTHON := $(value PYTHON)
export PYTHON
override REPOSITORY_MAKE_DOLLAR := $$
override REPOSITORY_MAKE_OPEN := (
ifneq ($(findstring $(REPOSITORY_MAKE_DOLLAR)$(REPOSITORY_MAKE_OPEN),$(value PYTHON)),)
$(error PYTHON must be a literal executable path, not Make syntax)
endif
override SHELL := /bin/sh
override .SHELLFLAGS := -c

ifneq ($(filter command line,$(origin MAKEFLAGS)),)
$(error MAKEFLAGS must not be overridden for repository verification)
endif
override REPOSITORY_MAKE_FIRST_FLAGS := $(firstword $(MAKEFLAGS))
ifneq ($(filter -%,$(REPOSITORY_MAKE_FIRST_FLAGS)),)
override REPOSITORY_MAKE_FIRST_FLAGS :=
endif
override REPOSITORY_MAKE_SHORT_FLAGS := $(REPOSITORY_MAKE_FIRST_FLAGS) $(filter-out --%,$(filter -%,$(MAKEFLAGS)))
ifneq ($(findstring n,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring t,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring q,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring i,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(filter --just-print --dry-run --recon --touch --question --ignore-errors,$(MAKEFLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(strip $(MAKEFILES)),)
$(error MAKEFILES must be empty; repository verification requires this Makefile to be loaded alone)
endif
override MAKEFILES :=
ifneq ($(origin MAKEFILE_LIST),file)
$(error MAKEFILE_LIST must not be overridden)
endif
override REPOSITORY_SED := $(shell if [ -x /usr/bin/sed ]; then /usr/bin/printf '%s' /usr/bin/sed; elif [ -x /bin/sed ]; then /usr/bin/printf '%s' /bin/sed; fi)
override ROOT := $(shell path='$(subst ','"'"',$(value MAKEFILE_LIST))'; path=$$(printf '%s' "$$path" | '$(REPOSITORY_SED)' 's/^ //'); [ -f "$$path" ] || exit 1; directory=$${path%/*}; [ "$$directory" != "$$path" ] || directory=.; CDPATH= cd -- "$$directory" && /bin/pwd -P)
export ROOT
ifeq ($(strip $(ROOT)),)
$(error repository Makefile path could not be resolved)
endif

audit build check format lint root-test test verify: $$(if $$(filter file,$$(origin MAKEFILE_LIST)),,$$(error MAKEFILE_LIST must not be overridden))
audit build check format lint root-test test verify: $$(if $$(shell path=$$$$(/usr/bin/printf '%s' '$$(subst ','"'"',$$(MAKEFILE_LIST))' | '$$(REPOSITORY_SED)' 's/^ //') && [ -f "$$$$path" ] && /usr/bin/printf '%s' ok),,$$(error repository Makefile must be loaded alone))
audit build check format lint root-test test verify: __repository-make-authority

__repository-make-authority::
	@:

format:
	cd "$$ROOT" && "$$PYTHON" -I -B -m ruff format --check .

lint:
	cd "$$ROOT" && "$$PYTHON" -I -B -m ruff check .
	"$$PYTHON" -I -B -m compileall -q "$$ROOT/app.py" "$$ROOT/scripts" "$$ROOT/tests"
	"$$PYTHON" -I -B "$$ROOT/scripts/check_docs_plans.py"
	"$$PYTHON" -I -B "$$ROOT/scripts/test_ffprobe_stderr_contract.py"
	"$$PYTHON" -I -B "$$ROOT/scripts/test_audio_boundary_contract.py"

test:
	cd "$$ROOT" && "$$PYTHON" -I -B -c 'import sys, pytest; sys.path.insert(0, "."); raise SystemExit(pytest.main(["-q"]))'

build:
	"$$PYTHON" -I -B -m py_compile "$$ROOT/app.py"

audit:
	env -u PYTHONPATH "$$PYTHON" -I -B -m pip check
	env -u PYTHONPATH "$$PYTHON" -I -B -m pip_audit --requirement "$$ROOT/requirements.txt" --no-deps --disable-pip

root-test:
	/bin/sh "$$ROOT/scripts/test-makefile-root.sh"
	/bin/sh "$$ROOT/scripts/test-makefile-boundary.sh"

verify: root-test format lint test build

check: verify audit
