ifeq ($(wildcard .env),.env)
include .env
export
endif
VIRTUAL_ENV := $(CURDIR)/.venv
LOCAL_PYTHON := $(VIRTUAL_ENV)/bin/python3.11
PROJECT_NAME := $(shell grep '^name = ' pyproject.toml | sed -E 's/name = "(.*)"/\1/')

LOCAL_MYPY := $(VIRTUAL_ENV)/bin/mypy
LOCAL_PYTEST := $(VIRTUAL_ENV)/bin/pytest
LOCAL_PYRIGHT := $(VIRTUAL_ENV)/bin/pyright
LOCAL_RUFF := $(VIRTUAL_ENV)/bin/ruff

define PRINT_TITLE
    $(eval PADDED_PROJECT_NAME := $(shell printf '%-15s' "[$(PROJECT_NAME)] " | sed 's/ /=/g'))
    $(eval PADDED_TARGET_NAME := $(shell printf '%-15s' "($@) " | sed 's/ /=/g'))
    $(if $(1),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g')$(shell echo " $(1) " | sed 's/[[:space:]]/ /g')),\
		$(eval TITLE := $(shell printf '%s' "=== $(PADDED_PROJECT_NAME) $(PADDED_TARGET_NAME)" | sed 's/[[:space:]]/ /g'))\
	)
	$(eval PADDED_TITLE := $(shell printf '%-126s' "$(TITLE)" | sed 's/ /=/g'))
	@echo ""
	@echo "$(PADDED_TITLE)"
endef

define HELP
Manage $(PROJECT_NAME) located in $(CURDIR).
Usage:

make env                      - Create python virtual env
make lock                     - Refresh poetry.lock without updating anything
make install                  - Create local virtualenv & install all dependencies
make update                   - Upgrade dependencies via poetry

make format                   - format with ruff format
make lint                     - lint with ruff check
make pyright                  - Check types with pyright
make mypy                     - Check types with mypy

make cleanenv                 - Remove virtual env and lock files
make cleanderived             - Remove extraneous compiled files, caches, logs, etc.
make cleanall                 - Remove all -> cleanenv + cleanderived

make merge-check-ruff-lint    - Run ruff merge check without updating files
make merge-check-ruff-format  - Run ruff merge check without updating files
make merge-check-mypy         - Run mypy merge check without updating files
make merge-check-pyright	  - Run pyright merge check without updating files

make runtests		          - Run tests for github actions (exit on first failure)
make test                     - Run unit tests
make test-with-prints         - Run tests with prints
make t                        - Shorthand -> test-with-prints

make check                    - Shorthand -> format lint mypy
make c                        - Shorthand -> check
make cc                       - Shorthand -> cleanderived check
make li                       - Shorthand -> lock install
make check-unused-imports     - Check for unused imports without fixing
make fix-unused-imports       - Fix unused imports with ruff

endef
export HELP

.PHONY: all help env lock install update format lint pyright mypy cleanderived cleanenv runtests test test-with-prints t check cc li merge-check-ruff-lint merge-check-ruff-format merge-check-mypy check-unused-imports fix-unused-imports test-name bump-version

all help:
	@echo "$$HELP"


##########################################################################################
### SETUP
##########################################################################################

env:
	$(call PRINT_TITLE,"Creating virtual environment")
	@if [ ! -d $(VIRTUAL_ENV) ]; then \
		echo "Creating Python virtual env in \`${VIRTUAL_ENV}\`"; \
		python3.11 -m venv $(VIRTUAL_ENV); \
		. $(VIRTUAL_ENV)/bin/activate && \
		echo "Created Python virtual env in \`${VIRTUAL_ENV}\`"; \
	else \
		echo "Python virtual env already exists in \`${VIRTUAL_ENV}\`"; \
	fi

install: env
	$(call PRINT_TITLE,"Installing dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) -m pip install --upgrade pip setuptools wheel && \
	$(LOCAL_PYTHON) -m pip install "poetry>=2.0.0,<2.1.0" && \
	$(LOCAL_PYTHON) -m poetry install && \
	echo "Installed kajson dependencies in ${VIRTUAL_ENV}";

lock: env
	$(call PRINT_TITLE,"Resolving dependencies without update")
	@. $(VIRTUAL_ENV)/bin/activate && \
	poetry lock && \
	echo poetry lock without update;

update: env
	$(call PRINT_TITLE,"Updating all dependencies")
	@. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) -m pip install --upgrade pip setuptools wheel && \
	poetry update && \
	echo "Updated dependencies in ${VIRTUAL_ENV}";

##############################################################################################
############################      Cleaning                        ############################
##############################################################################################

cleanderived:
	$(call PRINT_TITLE,"Erasing derived files and directories")
	@find . -name '.coverage' -delete && \
	find . -wholename '**/*.pyc' -delete && \
	find . -type d -wholename '__pycache__' -exec rm -rf {} + && \
	find . -type d -wholename './.cache' -exec rm -rf {} + && \
	find . -type d -wholename './.mypy_cache' -exec rm -rf {} + && \
	find . -type d -wholename './.ruff_cache' -exec rm -rf {} + && \
	find . -type d -wholename '.pytest_cache' -exec rm -rf {} + && \
	find . -type d -wholename '**/.pytest_cache' -exec rm -rf {} + && \
	find . -type d -wholename './logs/*.log' -exec rm -rf {} + && \
	find . -type d -wholename './.reports/*' -exec rm -rf {} + && \
	echo "Cleaned up derived files and directories";

cleanenv:
	$(call PRINT_TITLE,"Erasing virtual environment")
	find . -name '.Pipfile.lock' -delete && \
	find . -type d -wholename './.venv' -exec rm -rf {} + && \
	echo "Cleaned up virtual env and dependency lock files";

cleanall: cleanderived cleanenv cleanlibraries
	@echo "Cleaned up all derived files and directories";

##########################################################################################
### TESTING
##########################################################################################

runtests: env
	$(call PRINT_TITLE,"Unit testing for github actions")
	@echo "• Running unit tests"
	$(LOCAL_PYTEST) --exitfirst --quiet || [ $$? = 5 ]

test: env
	$(call PRINT_TITLE,"Unit testing without prints but displaying logs via pytest for WARNING level and above")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) -s -o log_cli=true -o log_level=WARNING -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) -s -o log_cli=true -o log_level=WARNING $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

test-with-prints: env
	$(call PRINT_TITLE,"Unit testing with prints and our rich logs")
	@echo "• Running unit tests"
	@if [ -n "$(TEST)" ]; then \
		$(LOCAL_PYTEST) -s -k "$(TEST)" $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	else \
		$(LOCAL_PYTEST) -s $(if $(filter 2,$(VERBOSE)),-vv,$(if $(filter 3,$(VERBOSE)),-vvv,-v)); \
	fi

t: test-with-prints
	@echo "> done: t = test-with-prints"

############################################################################################
############################               Linting              ############################
############################################################################################

format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	@$(LOCAL_RUFF) format .

lint: env
	$(call PRINT_TITLE,"Linting with ruff")
	@$(LOCAL_RUFF) check . --fix

pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	@$(LOCAL_PYRIGHT) --pythonpath $(LOCAL_PYTHON)

mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	@$(LOCAL_PYTHON) $(LOCAL_MYPY)


##########################################################################################
### MERGE CHECKS
##########################################################################################

merge-check-ruff-format: env
	$(call PRINT_TITLE,"Formatting with ruff")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) format --check -v .

merge-check-ruff-lint: env check-unused-imports
	$(call PRINT_TITLE,"Linting with ruff without fixing files")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check -v .

merge-check-pyright: env
	$(call PRINT_TITLE,"Typechecking with pyright")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYRIGHT) -p pyproject.toml

merge-check-mypy: env
	$(call PRINT_TITLE,"Typechecking with mypy")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_PYTHON) $(LOCAL_MYPY) --version && \
	$(LOCAL_PYTHON) $(LOCAL_MYPY) --config-file pyproject.toml

##########################################################################################
### SHORTHANDS
##########################################################################################

check-unused-imports: env
	$(call PRINT_TITLE,"Checking for unused imports without fixing")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check --select=F401 --no-fix .

c: format lint pyright mypy
	@echo "> done: c = check"

cc: cleanderived c
	@echo "> done: cc = cleanderived check"

check: cleanderived check-unused-imports c
	@echo "> done: check"

li: lock install
	@echo "> done: lock install"

check-TODOs: env
	$(call PRINT_TITLE,"Checking for TODOs")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check --select=TD -v .

fix-unused-imports: env
	$(call PRINT_TITLE,"Fixing unused imports")
	. $(VIRTUAL_ENV)/bin/activate && \
	$(LOCAL_RUFF) check --select=F401 --fix -v .

CURRENT_VERSION := $(shell grep '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/')
NEXT_VERSION := $(shell echo $(CURRENT_VERSION) | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g')

bump-version: env
	$(call PRINT_TITLE,"Bumping version from $(CURRENT_VERSION) to $(NEXT_VERSION)")
	@. $(VIRTUAL_ENV)/bin/activate && poetry version $(NEXT_VERSION)
	@echo "Version bumped to $(NEXT_VERSION)"
