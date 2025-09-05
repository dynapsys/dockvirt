# Przykład 1: Statyczna strona na Nginx

Ten przykład pokazuje, jak za pomocą `dockvirt` uruchomić prostą stronę statyczną serwowaną przez serwer Nginx.

## Kroki do uruchomienia

1.  **Uruchom VM za pomocą `dockvirt`**:
    Przejdź do tego katalogu i uruchom `dockvirt`. Dockerfile i pliki aplikacji zostaną automatycznie skopiowane do VM i zbudowane tam:

    ```bash
    cd examples/1-static-nginx-website
    # Po prostu uruchom - wszystkie parametry są w pliku .dockvirt
    # Docker image zostanie zbudowany automatycznie wewnątrz VM
    dockvirt up
    ```

    Lub nadal możesz używać parametrów CLI:
    ```bash
    # Użyj domyślnego Ubuntu 22.04
    dockvirt up \
      --name static-site \
      --domain static-site.local \
      --image my-static-website:latest \
      --port 80

    # Lub użyj Fedory
    dockvirt up \
      --name static-site-fedora \
      --domain static-site-fedora.local \
      --image my-static-website:latest \
      --port 80 \
      --os fedora38
    ```

3.  **Dodaj wpis do `/etc/hosts`**:
    Po uzyskaniu adresu IP od `dockvirt`, dodaj go do swojego pliku `/etc/hosts`:
    ```
    <adres_ip> static-site.local
    ```

4.  **Otwórz stronę w przeglądarce**:
    Odwiedź `http://static-site.local`, aby zobaczyć swoją stronę.

5.  **Usuń VM po zakończeniu**:
    ```bash
    dockvirt down --name static-site
    ```

## Co się dzieje w tle?

Gdy uruchamiasz `dockvirt up`, narzędzie:
1. Automatycznie pobiera obraz Ubuntu 22.04 (przy pierwszym uruchomieniu)
2. Tworzy maszynę wirtualną z Docker i Caddy
3. Uruchamia Twój kontener z reverse proxy
4. Konfiguruje dostęp przez domenę
