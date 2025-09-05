# Makefile for dockvirt

.PHONY: help install build test-e2e publish clean

help:
	@echo "Dostępne komendy:"
	@echo "  install      - Instaluje zależności produkcyjne i deweloperskie"
	@echo "  build        - Buduje paczkę Pythona"
	@echo "  test-e2e     - Uruchamia testy end-to-end (wymaga DOCKVIRT_TEST_IMAGE i DOCKVIRT_TEST_OS_VARIANT)"
	@echo "  publish      - Publikuje paczkę do PyPI"
	@echo "  clean        - Usuwa artefakty budowania i pliki tymczasowe"

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

publish:
	@echo "Publikowanie paczki do PyPI..."
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +
