# Makefile for dockvirt

.PHONY: help install build test-e2e publish clean version-patch version-minor version-major version-show dev-setup lint format test-examples install-system check test-commands docs doctor

# Configurable Python (allow overriding: make <target> PY=path/to/python)
# Auto-detect local venv if present, else fallback to system python3
PY ?= $(shell if [ -x .venv-3.13/bin/python ]; then echo .venv-3.13/bin/python; \
elif [ -x .venv/bin/python ]; then echo .venv/bin/python; \
else command -v python3; fi)
PIP = $(PY) -m pip

# Sensible defaults for tests
export LIBVIRT_DEFAULT_URI ?= qemu:///system
export DOCKVIRT_TEST_IMAGE ?= nginx:latest
export DOCKVIRT_TEST_OS_VARIANT ?= ubuntu22.04

help:
	@echo "Available commands:"
	@echo "  install         - Install production and development dependencies"
	@echo "  dev-setup       - Full setup of the development environment"
	@echo "  build           - Build the Python package"
	@echo "  test-e2e        - Run end-to-end tests"
	@echo "  test-commands   - Test all CLI commands from documentation"
	@echo "  test-examples   - Test all examples on different systems"
	@echo "  check           - Check system dependencies"
	@echo "  doctor          - Diagnose and optionally fix environment issues"
	@echo "  agent           - Run automation agent (no sudo changes)"
	@echo "  agent-fix       - Run automation agent with auto-fix and /etc/hosts updates"
	@echo "  heal            - Run dockvirt self-heal routines"
	@echo "  sdlc-quick      - Run quick SDLC (doctor summary + command tests)"
	@echo "  sdlc-full       - Run full SDLC (doctor fix, lint, tests, build)"
	@echo "  lint            - Check code with linters (flake8, black)"
	@echo "  format          - Format code (black, isort)"
	@echo "  docs            - Build documentation"
	@echo "  version-show    - Show current version"
	@echo "  version-patch   - Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  version-minor   - Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  version-major   - Bump major version (0.1.0 -> 1.0.0)"
	@echo "  publish         - Bump patch version and publish to PyPI"
	@echo "  clean           - Remove build artifacts and temporary files"
	@echo "  install-system  - Install system dependencies (Docker, libvirt)"
	@echo "  repair          - Run comprehensive command validation"

install:
	$(PIP) install -e .[dev]

build:
	$(PY) -m build

test-e2e:
	@echo "Using PY=$(PY)"
	@echo "LIBVIRT_DEFAULT_URI=$(LIBVIRT_DEFAULT_URI)"
	@echo "DOCKVIRT_TEST_IMAGE=$(DOCKVIRT_TEST_IMAGE)"
	@echo "DOCKVIRT_TEST_OS_VARIANT=$(DOCKVIRT_TEST_OS_VARIANT)"
	$(PY) -m pytest -v tests/test_e2e.py

# Versioning
version-show:
	@$(PY) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"

version-patch:
	@current_version=$$($(PY) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$major.$$minor.$$((patch + 1))"; \
	echo "Bumping version from $$current_version to $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Version updated to $$new_version"

version-minor:
	@current_version=$$($(PY) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$major.$$((minor + 1)).0"; \
	echo "Bumping version from $$current_version to $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Version updated to $$new_version"

version-major:
	@current_version=$$($(PY) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$((major + 1)).0.0"; \
	echo "Bumping version from $$current_version to $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Version updated to $$new_version"

# Development tools
dev-setup: install
	@echo "🔧 Setting up the development environment..."
	$(PIP) install flake8 black isort
	@echo "✅ Development environment ready"

lint:
	@echo "🔍 Linting the code..."
	$(PY) -m flake8 dockvirt/ --max-line-length=88 --ignore=E203,W503
	$(PY) -m black --check dockvirt/
	$(PY) -m isort --check-only dockvirt/

format:
	@echo "🎨 Formatting the code..."
	$(PY) -m black dockvirt/
	$(PY) -m isort dockvirt/
	@echo "✅ Code formatted"

# Publishing with automatic versioning
publish: clean version-patch build
	@echo "📦 Publishing package to PyPI..."
	@new_version=$$($(PY) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	echo "Publishing version $$new_version"; \
	$(PY) -m twine upload dist/*; \
	echo "✅ Version $$new_version published to PyPI"

clean:
	@echo "🧹 Cleaning artifacts..."
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -exec rm -f {} + 2>/dev/null || true
	@echo "✅ Artifacts cleaned"

# Installing system dependencies
install-system:
	@echo "🔧 Installing system dependencies..."
	./scripts/install.sh
	@echo "✅ System installation complete"

# Testing examples
test-examples: install
	@echo "🧪 Testing all examples..."
	$(PY) scripts/test_examples.py

# System dependency check
check:
	@echo "🔍 Checking system dependencies..."
	@$(PY) -c "from dockvirt.system_check import check_system_dependencies; check_system_dependencies()"

# Test all commands from documentation
test-commands: install
	@echo "🧪 Testing all dockvirt commands..."
	$(PY) scripts/test_commands_robust.py
	@echo "✅ Command testing complete - check test_results.md"

# Build documentation
docs:
	@echo "📚 Building documentation..."
	@echo "Documentation is in README.md and examples/"

# Automation Agent
agent:
	@echo "🤖 Running Dockvirt Automation Agent (summary mode)..."
	$(PY) scripts/agent.py run

agent-fix:
	@echo "🤖 Running Dockvirt Automation Agent with auto-fix (sudo may be required)..."
	$(PY) scripts/agent.py run --auto-fix --auto-hosts --skip-host-build

heal:
	@echo "🛠️ Running self-heal..."
	$(PY) -m dockvirt.cli heal --apply

sdlc-quick:
	@echo "🚀 Running quick SDLC pipeline..."
	$(PY) scripts/sdlc.py quick

sdlc-full:
	@echo "🏗️ Running full SDLC pipeline (may take a while)..."
	$(PY) scripts/sdlc.py full --fix --skip-host-build

# Doctor (diagnostics and optional fixes)
doctor:
	@echo "🩺 Running Dockvirt Doctor..."
	$(PY) scripts/doctor.py

doctor-fix:
	@echo "🩺 Running Dockvirt Doctor with auto-fix..."
	$(PY) scripts/doctor.py --fix --yes

# Repair and validate all commands
repair: install
	@echo "🔧 Validating all commands from documentation..."
	$(PY) scripts/test_commands_robust.py
	@echo "✅ Validation complete - check test_results.md"

# Quick development test
test-quick: install
	@echo "🎯 Running quick tests..."
	$(PY) -m dockvirt.cli --help > /dev/null && echo "✅ CLI works"
	$(PY) -m dockvirt.cli check || echo "⚠️  Some dependencies missing"
	@echo "✅ Quick test complete"
