# Przykład 2: Aplikacja webowa w Pythonie (Flask)

Ten przykład pokazuje, jak uruchomić prostą aplikację Flask w Pythonie za pomocą `dockvirt`.

## Kroki do uruchomienia

1.  **Uruchom VM za pomocą `dockvirt`**:
    Dockerfile i pliki aplikacji zostaną automatycznie skopiowane do VM i zbudowane tam:
    Wykorzystaj plik `.dockvirt` dla maksymalnej wygody:

    ```bash
    # Użyj domyślnej konfiguracji z pliku .dockvirt
    dockvirt up
    
    # Lub zmień OS na Fedorę (edytuj .dockvirt lub użyj parametru)
    dockvirt up --os fedora38
    ```

    Możesz też ignorować plik `.dockvirt` i używać pełnych parametrów:
    ```bash
    # Pełna komenda z parametrami
    dockvirt up \
      --name flask-app \
      --domain flask-app.local \
      --image my-flask-app:latest \
      --port 5000 \
      --os ubuntu22.04
    ```

2.  **Dodaj wpis do `/etc/hosts`**:
    Po uzyskaniu adresu IP od `dockvirt`, dodaj go do swojego pliku `/etc/hosts`:
    ```
    <adres_ip> flask-app.local
    ```

3.  **Otwórz aplikację w przeglądarce**:
    Odwiedź `http://flask-app.local`, aby zobaczyć swoją aplikację.

4.  **Usuń VM po zakończeniu**:
    ```bash
    dockvirt down --name flask-app
    ```

## Automatyczne pobieranie obrazów

Przy pierwszym uruchomieniu `dockvirt` automatycznie pobierze potrzebny obraz systemu operacyjnego:
- Ubuntu 22.04: `~/.dockvirt/images/jammy-server-cloudimg-amd64.img`
- Fedora 38: `~/.dockvirt/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2`

Obrazy są buforowane lokalnie, więc kolejne uruchomienia będą znacznie szybsze.

## Co się dzieje w tle?

Gdy uruchamiasz `dockvirt up`, narzędzie:
1. Automatycznie pobiera obraz Ubuntu 22.04 lub Fedora 38 (przy pierwszym uruchomieniu)
2. Kopiuje Dockerfile, app.py, requirements.txt i inne pliki aplikacji do VM
3. Tworzy maszynę wirtualną z Docker i Caddy
4. Buduje Docker image z aplikacją Flask wewnątrz VM
5. Uruchamia kontener z aplikacją z reverse proxy
6. Konfiguruje dostęp przez domenę
