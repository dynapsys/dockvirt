# Makefile for dockvirt

.PHONY: help install build test-e2e publish clean version-patch version-minor version-major version-show dev-setup lint format test-examples install-system

help:
	@echo "Dostępne komendy:"
	@echo "  install         - Instaluje zależności produkcyjne i deweloperskie"
	@echo "  dev-setup       - Pełna konfiguracja środowiska deweloperskiego"
	@echo "  build           - Buduje paczkę Pythona"
	@echo "  test-e2e        - Uruchamia testy end-to-end"
	@echo "  lint            - Sprawdza kod linterm (flake8, black)"
	@echo "  format          - Formatuje kod (black, isort)"
	@echo "  version-show    - Pokazuje aktualną wersję"
	@echo "  version-patch   - Zwiększa wersję patch (0.1.0 -> 0.1.1)"
	@echo "  version-minor   - Zwiększa wersję minor (0.1.0 -> 0.2.0)"
	@echo "  version-major   - Zwiększa wersję major (0.1.0 -> 1.0.0)"
	@echo "  publish         - Automatycznie zwiększa patch i publikuje do PyPI"
	@echo "  clean           - Usuwa artefakty budowania i pliki tymczasowe"
	@echo "  install-system  - Instaluje zależności systemowe (Docker, libvirt)"
	@echo "  test-examples   - Testuje wszystkie examples na różnych systemach"

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
	echo "✅ Wersja zaktualizowana na $$new_version"

# Dodatkowe narzędzia deweloperskie
dev-setup: install
	@echo "🔧 Konfigurowanie środowiska deweloperskiego..."
	pip install flake8 black isort
	@echo "✅ Środowisko deweloperskie gotowe"

lint:
	@echo "🔍 Sprawdzanie kodu linterem..."
	flake8 dockvirt/ --max-line-length=88 --ignore=E203,W503
	black --check dockvirt/
	isort --check-only dockvirt/

format:
	@echo "🎨 Formatowanie kodu..."
	black dockvirt/
	isort dockvirt/
	@echo "✅ Kod sformatowany"

# Publikowanie z automatycznym wersjonowaniem
publish: clean version-patch build
	@echo "📦 Publikowanie paczki do PyPI..."
	@new_version=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	echo "Publikuję wersję $$new_version"; \
	twine upload dist/*; \
	echo "✅ Wersja $$new_version opublikowana do PyPI"

clean:
	@echo "🧹 Czyszczenie artefaktów..."
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -exec rm -f {} + 2>/dev/null || true
	@echo "✅ Artefakty wyczyszczone"

# Instalacja zależności systemowych
install-system:
	@echo "🔧 Instalowanie zależności systemowych..."
	./scripts/install.sh
	@echo "✅ Instalacja systemowa zakończona"

# Testowanie examples
test-examples:
	@echo "🧪 Testowanie wszystkich examples..."
	python3 scripts/test_examples.py
	@echo "✅ Testowanie zakończone - sprawdź test_results.md"
