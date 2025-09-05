# Makefile for dockvirt

.PHONY: help install build test-e2e publish clean version-patch version-minor version-major version-show dev-setup lint format test-examples install-system

help:
	@echo "Available commands:"
	@echo "  install         - Installs production and development dependencies"
	@echo "  dev-setup       - Full setup of the development environment"
	@echo "  build           - Builds the Python package"
	@echo "  test-e2e        - Runs end-to-end tests"
	@echo "  lint            - Checks the code with a linter (flake8, black)"
	@echo "  format          - Formats the code (black, isort)"
	@echo "  version-show    - Shows the current version"
	@echo "  version-patch   - Bumps the patch version (0.1.0 -> 0.1.1)"
	@echo "  version-minor   - Bumps the minor version (0.1.0 -> 0.2.0)"
	@echo "  version-major   - Bumps the major version (0.1.0 -> 1.0.0)"
	@echo "  publish         - Automatically bumps the patch version and publishes to PyPI"
	@echo "  clean           - Removes build artifacts and temporary files"
	@echo "  install-system  - Installs system dependencies (Docker, libvirt)"
	@echo "  test-examples   - Tests all examples on different systems"

install:
	pip install -e .[dev]

build:
	python -m build

test-e2e:
	@if [ -z "$${DOCKVIRT_TEST_IMAGE}" ]; then \
		echo "Błąd: Zmienna środowiskowa DOCKVIRT_TEST_IMAGE nie jest ustawiona."; \
		exit 1; \
	fi
	@if [ -z "$${DOCKVIRT_TEST_OS_VARIANT}" ]; then \
		echo "Błąd: Zmienna środowiskowa DOCKVIRT_TEST_OS_VARIANT nie jest ustawiona."; \
		exit 1; \
	fi
	pytest -v tests/test_e2e.py

# Wersjonowanie
version-show:
	@python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"

version-patch:
	@current_version=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$major.$$minor.$$((patch + 1))"; \
	echo "Zwiększam wersję z $$current_version na $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Wersja zaktualizowana na $$new_version"

version-minor:
	@current_version=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$major.$$((minor + 1)).0"; \
	echo "Zwiększam wersję z $$current_version na $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Wersja zaktualizowana na $$new_version"

version-major:
	@current_version=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_version="$$((major + 1)).0.0"; \
	echo "Zwiększam wersję z $$current_version na $$new_version"; \
	sed -i "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "✅ Version updated to $$new_version"

# Additional development tools
dev-setup: install
	@echo "🔧 Setting up the development environment..."
	pip install flake8 black isort
	@echo "✅ Development environment ready"

lint:
	@echo "🔍 Linting the code..."
	flake8 dockvirt/ --max-line-length=88 --ignore=E203,W503
	black --check dockvirt/
	isort --check-only dockvirt/

format:
	@echo "🎨 Formatting the code..."
	black dockvirt/
	isort dockvirt/
	@echo "✅ Code formatted"

# Publishing with automatic versioning
publish: clean version-patch build
	@echo "📦 Publishing package to PyPI..."
	@new_version=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	echo "Publishing version $$new_version"; \
	twine upload dist/*; \
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
	python3 scripts/test_examples.py

repair: install
	@echo "🔧 Repairing commands from READMEs..."
	python3 scripts/test_commands_robust.py
	@echo "✅ Testing complete - check test_results.md"
