# DockerVirt - Lista Zadań Do Realizacji

## 🚨 Krytyczne Problemy (Wysokie Priorytety)

### 1. Problem z Zależnościami - ModuleNotFoundError: jinja2
**Status:** ❌ Do naprawy  
**Priorytet:** Wysoki  
**Opis:** Testy nie działają z powodu braku jinja2 w zależnościach projektu  

**Rozwiązania:**
- [x] Dodać jinja2 do dependencies w pyproject.toml
- [ ] Zaktualizować requirements.txt
- [ ] Przetestować instalację w czystym środowisku

```bash
# Fix command
pip install jinja2
```

### 2. CLI nie Odpowiada Poprawnie na Niektóre Komendy
**Status:** ❌ Do naprawy  
**Priorytet:** Wysoki  
**Opis:** `dockvirt --help` działa, ale inne komendy zwracają błędy lub nie odpowiadają

**Rozwiązania:**
- [x] Dodać więcej debugowania do CLI
- [x] Sprawdzić import statements w cli.py
- [ ] Przetestować podstawowe komendy ręcznie
- [ ] Dodać logging do każdej funkcji CLI

### 3. Testy Examples Zawsze Failują z powodu jinja2
**Status:** ❌ Do naprawy  
**Priorytet:** Wysoki  
**Opis:** scripts/test_examples.py nie może zaimportować jinja2 podczas testów

**Rozwiązania:**
- [x] Naprawić import jinja2
- [ ] Refaktoryzować test_examples.py aby używał CliRunner
- [ ] Dodać proper error handling w testach
- [ ] Stworzyć mock environment dla testów

### 4. Brak Walidacji Komend w README
**Status:** ❌ Do naprawy  
**Priorytet:** Wysoki  
**Opis:** Komendy w plikach README mogą być nieaktualne lub niepoprawne

**Rozwiązania:**
- [ ] Przejrzeć wszystkie komendy w README.md
- [ ] Przejrzeć wszystkie komendy w examples/*/README.md
- [ ] Zaktualizować nieaktualne składnie komend
- [ ] Dodać automatyczne testy komend z markdown

## 📋 Rozwój Funkcjonalności (Średnie Priorytety)

### 5. Rozszerzone Logowanie dla Debugowania
**Status:** ❌ Do naprawy  
**Priorytet:** Średni  
**Opis:** Brak szczegółowych logów utrudnia debugowanie problemów

**Rozwiązania:**
- [ ] Dodać Python logging module do wszystkich modułów
- [ ] Stworzyć konfigurowalne poziomy logów (DEBUG, INFO, WARN, ERROR)
- [ ] Dodać logi do vm_manager.py
- [ ] Dodać logi do image_manager.py
- [ ] Dodać logi do config.py

```python
import logging

# Przykład implementacji
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### 6. Automatyczne Testowanie Komend z Markdown
**Status:** ✅ Częściowo zrobione  
**Priorytet:** Średni  
**Opis:** scripts/test_commands.py został rozszerzony, ale jeszcze nie działa w pełni

**Rozwiązania:**
- [x] Rozszerzyć test_commands.py o lepszą analizę markdown
- [ ] Naprawić problemy z uruchamianiem testów CLI
- [ ] Dodać reportowanie w formacie markdown
- [ ] Zintegrować z make repair

### 7. Usprawnienia Make Targets
**Status:** ✅ Częściowo zrobione  
**Priorytet:** Średni  
**Opis:** Makefile został częściowo przetłumaczony, ale można go jeszcze poprawić

**Rozwiązania:**
- [x] Przetłumaczyć wszystkie komentarze z polskiego na angielski
- [x] Dodać target 'repair' który uruchamia test_commands.py
- [ ] Dodać target 'lint-fix' który naprawia błędy automatycznie
- [ ] Dodać target 'test-all' który uruchamia wszystkie testy

## 🔧 Poprawki w Dokumentacji

### 8. Komendy do Sprawdzenia i Naprawienia w README

**Główny README.md:**
```bash
# Sprawdź te komendy:
dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000
dockvirt up --name backend --domain backend.local --image backend-app:latest --port 8080  
dockvirt up --name db --domain db.local --image postgres:latest --port 5432

# Sprawdź czy te składnie są aktualne:
dockvirt up \
  --name my-app \
  --domain my-app.local \
  --image nginx:latest \
  --port 80
```

**examples/1-static-nginx-website/README.md:**
```bash
# Do sprawdzenia:
dockvirt up
dockvirt up --name static-site --domain static-site.local --image my-static-website:latest --port 80
```

**examples/2-python-flask-app/README.md:**
```bash
# Do sprawdzenia:
dockvirt up
dockvirt up --os fedora38
dockvirt up --name flask-app --domain flask-app.local --image my-flask-app:latest --port 5000
```

**examples/3-multi-os-comparison/README.md:**
```bash
# Do sprawdzenia:
dockvirt up --name ubuntu-test --domain ubuntu-test.local --image multi-os-demo:latest --port 80
dockvirt up --name fedora-test --domain fedora-test.local --image multi-os-demo:latest --port 80 --os fedora38
```

### 9. Potencjalne Problemy w Komendach
**Status:** ❌ Do zbadania  
**Priorytet:** Średni  

**Możliwe problemy:**
- Niepoprawne nazwy obrazów Docker (mogą nie istnieć)
- Brak wymaganych argumentów w niektórych komendach
- Nieaktualne opcje CLI (--os vs --variant)
- Porty, które mogą być już zajęte w systemie

## 🚀 Usprawnienia Techniczne

### 10. Lepsze Error Handling
**Status:** ❌ Do zrobienia  
**Priorytet:** Średni  

**Rozwiązania:**
- [ ] Dodać try-catch bloki we wszystkich funkcjach CLI
- [ ] Stworzyć custom exception classes
- [ ] Dodać walidację argumentów wejściowych
- [ ] Dodać sprawdzanie dostępności portów przed tworzeniem VM

### 11. Testy Jednostkowe
**Status:** ❌ Do zrobienia  
**Priorytet:** Średni  

**Rozwiązania:**
- [ ] Stworzyć tests/ katalog
- [ ] Dodać testy dla vm_manager.py
- [ ] Dodać testy dla config.py
- [ ] Dodać testy dla image_manager.py
- [ ] Dodać mock testy dla CLI

### 12. CI/CD Pipeline
**Status:** ❌ Do zrobienia  
**Priorytet:** Niski  

**Rozwiązania:**
- [ ] Stworzyć .github/workflows/test.yml
- [ ] Dodać automatyczne testowanie na różnych wersjach Python
- [ ] Dodać automatyczne publikowanie na PyPI
- [ ] Dodać security scanning

## 📊 Plan Implementacji

### Faza 1 (Krytyczne): 
1. [x] Naprawić problem z jinja2
2. [ ] Dodać logging do CLI
3. [ ] Przetestować i naprawić podstawowe komendy CLI
4. [ ] Sprawdzić i naprawić komendy w README

### Faza 2 (Funkcjonalność):
1. [ ] Dokończyć implementację test_commands.py
2. [ ] Dodać kompleksowe logowanie
3. [ ] Stworzyć testy jednostkowe
4. [ ] Poprawić dokumentację

### Faza 3 (Polishing):
1. [ ] Dodać CI/CD
2. [ ] Dodać more advanced features
3. [ ] Optimization i performance improvements

## 🛠️ Komendy do Uruchomienia

```bash
# Sprawdź obecny stan testów
make test-examples

# Sprawdź komendy z README
make repair

# Zainstaluj zależności
make install

# Uruchom testy
python3 scripts/test_commands.py
python3 scripts/test_examples.py

# Sprawdź CLI manual
dockvirt --help
dockvirt up --help
```

## 📝 Notatki dla Programistów

### Struktura Projektu:
```
dockvirt/
├── dockvirt/           # Główny kod biblioteki
│   ├── cli.py         # Command line interface
│   ├── vm_manager.py  # Zarządzanie VM (WYMAGA JINJA2!)
│   ├── config.py      # Konfiguracja
│   └── ...
├── scripts/           # Skrypty narzędziowe
│   ├── test_commands.py   # ✅ Rozszerzony tester komend
│   └── test_examples.py   # ❌ Wymaga naprawy
├── examples/          # Przykłady użycia
└── tests/            # ❌ Brak testów jednostkowych
```

### Najważniejsze Pliki do Naprawy:
1. `dockvirt/vm_manager.py` - dodać logging
2. `scripts/test_examples.py` - naprawić CliRunner usage
3. `pyproject.toml` - dodać brakujące dependencies
4. Wszystkie `README.md` - sprawdzić aktualne komendy

---
**Ostatnia aktualizacja:** 2025-09-05  
**Status:** W trakcie implementacji  
**Kolejne kroki:** Wykonać Fazę 1 zadań krytycznych
