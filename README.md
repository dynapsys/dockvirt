# dockvirt

**Twórz lekkie, izolowane środowiska deweloperskie za pomocą jednego polecenia.**

`dockvirt` to narzędzie CLI, które automatyzuje proces tworzenia maszyn wirtualnych (VM) z wykorzystaniem libvirt/KVM. Umożliwia błyskawiczne uruchamianie aplikacji w kontenerach Docker, z prekonfigurowanym reverse proxy (Caddy), w pełni izolowanym od Twojego systemu operacyjnego.

Jest to idealne rozwiązanie, jeśli szukasz alternatywy dla Multipass, ale z większą kontrolą i elastycznością, jaką oferuje ekosystem libvirt.

---

## 🚀 Główne funkcje

*   **Automatyzacja od A do Z**: Tworzenie, konfigurowanie i usuwanie VM za pomocą prostych poleceń.
*   **Uniwersalność**: Działa na popularnych dystrybucjach Linuksa (Ubuntu, Fedora i inne).
*   **Elastyczność**: Pełna kontrola nad konfiguracją VM (RAM, CPU, dysk).
*   **Prekonfigurowane środowisko**: Automatyczna instalacja Dockera i Caddy wewnątrz VM.
*   **Izolacja**: Każde środowisko działa w oddzielnej maszynie wirtualnej, co zapobiega konfliktom.

## 🔧 Wymagania

Przed rozpoczęciem upewnij się, że masz zainstalowane następujące pakiety:

*   **libvirt & KVM**: `qemu-kvm`, `libvirt-daemon-system`, `virt-manager`
*   **Narzędzia dodatkowe**: `cloud-image-utils` (zawiera `cloud-localds`)

Dodatkowo, potrzebujesz **obrazu chmurowego** (`.qcow2`) dla systemu operacyjnego, którego chcesz używać (np. Ubuntu 22.04, Fedora Cloud Base).

## ⚙️ Instalacja

1.  Sklonuj repozytorium:
    ```bash
    git clone https://github.com/dynapsys/dockvirt.git
    cd dockvirt
    ```

2.  Zainstaluj zależności (zalecane w wirtualnym środowisku):
    ```bash
    make install
    ```

## 🖥️ Użycie

### Tworzenie VM

Aby utworzyć nową maszynę wirtualną, użyj polecenia `dockvirt up`. Musisz podać ścieżkę do obrazu bazowego oraz jego wariant dla `virt-install`.

**Przykład dla Ubuntu:**

```bash
dockvirt up \
  --name my-app \
  --domain my-app.local \
  --image nginx:latest \
  --port 80 \
  --base-image /path/to/ubuntu-22.04.qcow2 \
  --os-variant ubuntu22.04
```

**Przykład dla Fedory:**

```bash
dockvirt up \
  --name fedora-app \
  --domain fedora-app.local \
  --image httpd:latest \
  --port 80 \
  --base-image /path/to/fedora-cloud-base.qcow2 \
  --os-variant fedora-cloud-base-36
```

Po utworzeniu VM, `dockvirt` wyświetli jej adres IP. Dodaj go do pliku `/etc/hosts`, aby uzyskać dostęp przez domenę:

```
<adres_ip> my-app.local
```

### Usuwanie VM

Aby usunąć maszynę wirtualną i wszystkie powiązane z nią zasoby, użyj polecenia `dockvirt down`:

```bash
dockvirt down --name my-app
```

## 🛠️ Development

Repozytorium zawiera `Makefile`, który ułatwia proces deweloperski.

*   **Instalacja zależności**: `make install`
*   **Uruchamianie testów E2E**: `make test-e2e` (wymaga ustawienia zmiennych `DOCKVIRT_TEST_IMAGE` i `DOCKVIRT_TEST_OS_VARIANT`)
*   **Budowanie paczki**: `make build`
*   **Publikacja w PyPI**: `make publish`
*   **Czyszczenie projektu**: `make clean`

## 📜 Licencja

Projekt jest udostępniany na licencji **Apache 2.0**. Szczegóły znajdują się w pliku [LICENSE](LICENSE).
