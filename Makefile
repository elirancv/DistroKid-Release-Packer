.PHONY: help install install-js install-all setup run run-js example validate \
        clean clean-all test test-cov test-unit test-integration \
        check check-python check-node init quick docs readme \
        lint format lint-fix info version ensure-config

.DEFAULT_GOAL := help

# ------------------------------------------------------------------------------
# OS detection
# ------------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
    IS_WINDOWS := 1
else
    IS_WINDOWS := 0
endif

# ------------------------------------------------------------------------------
# Core commands
# ------------------------------------------------------------------------------
PYTHON := $(if $(IS_WINDOWS),python,python3)
PIP    := $(if $(IS_WINDOWS),pip,pip3)
NODE   := node
NPM    := npm

# ------------------------------------------------------------------------------
# Project config
# ------------------------------------------------------------------------------
PROJECT_NAME := DistroKid Release Packer
VERSION      := 2.3.0
CONFIG       := configs/release.json
CONFIG_EX    := configs/release.example.json
PY_FILES     := scripts/*.py
RELEASES_DIR := runtime/output

# ------------------------------------------------------------------------------
# Shell behavior (Unix)
# ------------------------------------------------------------------------------
ifeq ($(IS_WINDOWS),0)
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
endif

# ------------------------------------------------------------------------------
# Colors (Unix only)
# ------------------------------------------------------------------------------
ifeq ($(IS_WINDOWS),1)
    BLUE :=
    GREEN :=
    YELLOW :=
    NC :=
else
    BLUE := \033[0;34m
    GREEN := \033[0;32m
    YELLOW := \033[0;33m
    NC := \033[0m
endif

define log
	@echo "$(BLUE)==>$(NC) $(1)"
endef

define ok
	@echo "$(GREEN)✓$(NC) $(1)"
endef

define warn
	@echo "$(YELLOW)⚠$(NC) $(1)"
endef

# ------------------------------------------------------------------------------
# Help (auto-generated)
# ------------------------------------------------------------------------------
help: ## Show this help message
ifeq ($(IS_WINDOWS),1)
	@echo $(PROJECT_NAME)
	@echo.
	@echo Available targets:
	@echo   help                 Show this help message
	@echo   install              Install Python dependencies
	@echo   install-js           Install JavaScript dependencies
	@echo   install-all          Install all dependencies
	@echo   setup                Install deps and create config if missing
	@echo   run                  Run Python packer
	@echo   run-js               Run JavaScript packer
	@echo   quick                Setup and run
	@echo   validate             Validate release.json
	@echo   example              Show example configuration
	@echo   check                Verify dependencies
	@echo   test                 Run all tests
	@echo   test-unit            Run unit tests
	@echo   test-integration     Run integration tests
	@echo   test-cov             Run tests with coverage
	@echo   clean                Remove temporary files
	@echo   clean-all            Remove all generated artifacts
	@echo   lint                 Run pylint
	@echo   format               Format code with black
	@echo   docs                 List documentation
	@echo   readme               Preview README
	@echo   info                 Show project info
	@echo   version              Show version
	@echo   init                 Alias for setup
	@echo.
else
	@echo "$(BLUE)$(PROJECT_NAME)$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "$(GREEN)Available targets:$(NC)\n"} \
	     /^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[33m%-20s\033[0m %s\n", $$1, $$2}' \
	     $(MAKEFILE_LIST)
endif

# ------------------------------------------------------------------------------
# Dependency installation
# ------------------------------------------------------------------------------
install: ## Install Python dependencies
	$(call log,Installing Python dependencies)
	$(PIP) install -r requirements.txt
	$(call ok,Python dependencies installed)

install-js: ## Install JavaScript dependencies
	$(call log,Installing JavaScript dependencies)
	$(NPM) install
	$(call ok,JavaScript dependencies installed)

install-all: install install-js ## Install all dependencies

# ------------------------------------------------------------------------------
# Config handling
# ------------------------------------------------------------------------------
ensure-config:
ifeq ($(IS_WINDOWS),1)
	@if not exist $(CONFIG) ( \
		echo Creating $(CONFIG) from example... && \
		copy $(CONFIG_EX) $(CONFIG) && \
		echo Please edit $(CONFIG) and re-run && \
		exit /b 1 \
	)
else
	@if [ ! -f $(CONFIG) ]; then \
		echo "$(YELLOW)Config missing – creating $(CONFIG)$(NC)"; \
		cp $(CONFIG_EX) $(CONFIG); \
		echo "$(YELLOW)Edit $(CONFIG) and re-run$(NC)"; \
		exit 1; \
	fi
endif

setup: install ## Install deps and create config if missing
ifeq ($(IS_WINDOWS),1)
	@if not exist $(CONFIG) copy $(CONFIG_EX) $(CONFIG)
else
	@test -f $(CONFIG) || cp $(CONFIG_EX) $(CONFIG)
endif
	$(call ok,Project setup complete)

# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------
run: ensure-config ## Run Python packer
	$(call log,Running packer (Python))
	$(PYTHON) scripts/pack.py $(CONFIG)

run-js: ensure-config ## Run JavaScript packer
	$(call log,Running packer (JavaScript))
	$(NODE) scripts/pack.js $(CONFIG)

quick: setup run ## Setup and run

# ------------------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------------------
validate: ensure-config ## Validate release.json
	$(call log,Validating $(CONFIG))
	@$(PYTHON) -c "import json; json.load(open('$(CONFIG)'))"
	$(call ok,Valid JSON)

example: ## Show example configuration
	$(PYTHON) scripts/pack.py --example

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------
check-python:
ifeq ($(IS_WINDOWS),1)
	@$(PYTHON) -c "import mutagen, PIL" 2>nul || (echo Missing Python deps. Run: make install && exit 1)
	@echo Python dependencies OK
else
	@$(PYTHON) -c "import mutagen, PIL" 2>/dev/null || (echo "Missing Python deps. Run: make install" && exit 1)
	@echo "Python dependencies OK"
endif

check-node:
ifeq ($(IS_WINDOWS),1)
	@$(NODE) -e "require('node-id3'); require('sharp')" 2>nul || (echo Missing JS deps. Run: make install-js && exit 1)
	@echo JavaScript dependencies OK
else
	@$(NODE) -e "require('node-id3'); require('sharp')" 2>/dev/null || (echo "Missing JS deps. Run: make install-js" && exit 1)
	@echo "JavaScript dependencies OK"
endif

check: check-python check-node ## Verify dependencies

test: check-python ## Run all tests
ifeq ($(IS_WINDOWS),1)
	@$(PYTHON) -m pytest tests/ -v 2>nul || (echo pytest not found. Install with: pip install pytest && exit 1)
else
	@command -v pytest >/dev/null 2>&1 || (echo "pytest not found. Install with: pip install pytest" && exit 1)
	pytest tests/ -v
endif

test-unit: check-python ## Run unit tests
ifeq ($(IS_WINDOWS),1)
	@$(PYTHON) -m pytest tests/unit/ -v 2>nul || (echo pytest not found. Install with: pip install pytest && exit 1)
else
	@command -v pytest >/dev/null 2>&1 || (echo "pytest not found. Install with: pip install pytest" && exit 1)
	pytest tests/unit/ -v
endif

test-integration: check-python ## Run integration tests
ifeq ($(IS_WINDOWS),1)
	@$(PYTHON) -m pytest tests/integration/ -v 2>nul || (echo pytest not found. Install with: pip install pytest && exit 1)
else
	@command -v pytest >/dev/null 2>&1 || (echo "pytest not found. Install with: pip install pytest" && exit 1)
	pytest tests/integration/ -v
endif

test-cov: check-python ## Run tests with coverage (fails if below 70%)
ifeq ($(IS_WINDOWS),1)
	@$(PYTHON) -m pytest tests/ -v --cov=scripts --cov-report=term --cov-report=html --cov-config=.coveragerc 2>nul || (echo pytest not found. Install with: pip install pytest pytest-cov && exit 1)
	$(call ok,Coverage report generated - minimum 70% required)
else
	@command -v pytest >/dev/null 2>&1 || (echo "pytest not found. Install with: pip install pytest pytest-cov" && exit 1)
	pytest tests/ -v --cov=scripts --cov-report=term --cov-report=html --cov-config=.coveragerc
	$(call ok,Coverage report generated - minimum 70% required)
endif

# ------------------------------------------------------------------------------
# Cleaning
# ------------------------------------------------------------------------------
clean: ## Remove temporary files
	$(call log,Cleaning temporary files)
ifeq ($(IS_WINDOWS),1)
	@powershell -Command "Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force" 2>$nul || true
	@powershell -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force" 2>$nul || true
else
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} +
endif
	$(call ok,Clean complete)

clean-all: clean ## Remove all generated artifacts
	$(call warn,Removing $(RELEASES_DIR))
ifeq ($(IS_WINDOWS),1)
	@if exist $(RELEASES_DIR) powershell -Command "Remove-Item -Recurse -Force $(RELEASES_DIR)" || echo Directory not found
else
	@test "$(RELEASES_DIR)" != "/" && rm -rf $(RELEASES_DIR)
endif
	$(call ok,Full cleanup complete)

# ------------------------------------------------------------------------------
# Dev tools
# ------------------------------------------------------------------------------
lint: check-python ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	@$(PYTHON) -m ruff check scripts/ pack.py || true
	@$(call ok,Linting complete)

format: check-python ## Format code with ruff
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	@$(PYTHON) -m ruff format scripts/ pack.py
	@$(call ok,Formatting complete)

lint-fix: check-python ## Run ruff linter and auto-fix issues
	@echo "$(BLUE)Running ruff linter with auto-fix...$(NC)"
	@$(PYTHON) -m ruff check --fix scripts/ || true
	@$(PYTHON) -m ruff format scripts/
	@$(call ok,Linting and formatting complete)

# ------------------------------------------------------------------------------
# Docs & info
# ------------------------------------------------------------------------------
docs: ## List documentation
	@echo README.md
	@echo QUICK_START.md
	@echo HOW_IT_WORKS.md
	@echo USAGE_GUIDE.md
	@echo scripts/README.md

readme: ## Preview README
ifeq ($(IS_WINDOWS),1)
	@powershell -Command "Get-Content README.md -TotalCount 30"
else
	@head -30 README.md
endif

info: ## Show project info
	@echo "$(BLUE)$(PROJECT_NAME)$(NC)"
	@echo Version: $(VERSION)
	@echo Python: $$($(PYTHON) --version)
	@echo Node: $$($(NODE) --version 2>/dev/null || echo Not installed)

version: ## Show version
	@echo $(VERSION)

init: setup ## Alias for setup
