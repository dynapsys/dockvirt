# Przykład 2: Aplikacja webowa w Pythonie (Flask)

Ten przykład pokazuje, jak za pomocą `dockvirt` uruchomić prostą aplikację webową napisaną w Pythonie z użyciem frameworka Flask.

## Kroki do uruchomienia

1.  **Zbuduj obraz Dockera**:
    Przejdź do tego katalogu i zbuduj obraz, który będzie zawierał Twoją aplikację i jej zależności:
    ```bash
    docker build -t my-flask-app:latest .
    ```

2.  **Uruchom VM za pomocą `dockvirt`**:
    Użyj `dockvirt`, aby utworzyć maszynę wirtualną i uruchomić w niej kontener z Twoją aplikacją. Pamiętaj, aby podać prawidłową ścieżkę do obrazu chmurowego (`--base-image`) i jego wariant (`--os-variant`).

    ```bash
    dockvirt up \
      --name flask-app \
      --domain flask-app.local \
      --image my-flask-app:latest \
      --port 5000 \
      --base-image /path/to/your/cloud-image.qcow2 \
      --os-variant fedora-cloud-base-36
    ```

3.  **Dodaj wpis do `/etc/hosts`**:
    Po uzyskaniu adresu IP od `dockvirt`, dodaj go do swojego pliku `/etc/hosts`:
    ```
    <adres_ip> flask-app.local
    ```

4.  **Otwórz aplikację w przeglądarce**:
    Odwiedź `http://flask-app.local`, aby zobaczyć swoją aplikację.
