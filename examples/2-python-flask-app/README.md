# Przykład 2: Aplikacja webowa w Pythonie (Flask)

Ten przykład pokazuje, jak za pomocą `dockvirt` uruchomić prostą aplikację webową napisaną w Pythonie z użyciem frameworka Flask.

## Kroki do uruchomienia

1.  **Zbuduj obraz Dockera**:
    Przejdź do tego katalogu i zbuduj obraz, który będzie zawierał Twoją aplikację i jej zależności:
    ```bash
    cd examples/2-python-flask-app
    docker build -t my-flask-app:latest .
    ```

2.  **Uruchom VM za pomocą `dockvirt`**:
    Dzięki nowemu systemowi konfiguracji, uruchomienie jest bardzo proste:

    ```bash
    # Domyślnie użyje Ubuntu 22.04
    dockvirt up \
      --name flask-app \
      --domain flask-app.local \
      --image my-flask-app:latest \
      --port 5000
    ```

    Lub przetestuj na Fedorze:
    ```bash
    # Użyj Fedory 36
    dockvirt up \
      --name flask-app-fedora \
      --domain flask-app-fedora.local \
      --image my-flask-app:latest \
      --port 5000 \
      --os fedora36
    ```

3.  **Dodaj wpis do `/etc/hosts`**:
    Po uzyskaniu adresu IP od `dockvirt`, dodaj go do swojego pliku `/etc/hosts`:
    ```
    <adres_ip> flask-app.local
    ```

4.  **Otwórz aplikację w przeglądarce**:
    Odwiedź `http://flask-app.local`, aby zobaczyć swoją aplikację.

5.  **Usuń VM po zakończeniu**:
    ```bash
    dockvirt down --name flask-app
    ```

## Automatyczne pobieranie obrazów

Przy pierwszym uruchomieniu `dockvirt` automatycznie pobierze potrzebny obraz systemu operacyjnego:
- Ubuntu 22.04: `~/.dockvirt/images/jammy-server-cloudimg-amd64.img`
- Fedora 36: `~/.dockvirt/images/Fedora-Cloud-Base-36-1.5.x86_64.qcow2`

Obrazy są buforowane lokalnie, więc kolejne uruchomienia będą znacznie szybsze.
