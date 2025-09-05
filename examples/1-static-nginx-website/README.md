# Przykład 1: Statyczna strona na Nginx

Ten przykład pokazuje, jak za pomocą `dockvirt` uruchomić prostą stronę statyczną serwowaną przez serwer Nginx.

## Kroki do uruchomienia

1.  **Zbuduj obraz Dockera**:
    Przejdź do tego katalogu i zbuduj obraz, który będzie zawierał Twoją stronę i konfigurację Nginx:
    ```bash
    cd examples/1-static-nginx-website
    docker build -t my-static-website:latest .
    ```

2.  **Uruchom VM za pomocą `dockvirt`**:
    Użyj `dockvirt`, aby utworzyć maszynę wirtualną i uruchomić w niej kontener z Twoją stroną. Pamiętaj, aby podać prawidłową ścieżkę do obrazu chmurowego (`--base-image`) i jego wariant (`--os-variant`).

    ```bash
    dockvirt up \
      --name static-site \
      --domain static-site.local \
      --image my-static-website:latest \
      --port 80 \
      --base-image /path/to/your/cloud-image.qcow2 \
      --os-variant ubuntu22.04
    ```

3.  **Dodaj wpis do `/etc/hosts`**:
    Po uzyskaniu adresu IP od `dockvirt`, dodaj go do swojego pliku `/etc/hosts`:
    ```
    <adres_ip> static-site.local
    ```

4.  **Otwórz stronę w przeglądarce**:
    Odwiedź `http://static-site.local`, aby zobaczyć swoją stronę.
