# dockvirt

[![PyPI version](https://badge.fury.io/py/dockvirt.svg)](https://badge.fury.io/py/dockvirt)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Twórz lekkie, izolowane środowiska deweloperskie za pomocą jednego polecenia.**

`dockvirt` to narzędzie CLI, które automatyzuje proces tworzenia maszyn wirtualnych (VM) z wykorzystaniem libvirt/KVM. Umożliwia błyskawiczne uruchamianie aplikacji w kontenerach Docker, z prekonfigurowanym reverse proxy (Caddy), w pełni izolowanym od Twojego systemu operacyjnego.

---

## 🤔 Dlaczego dockvirt?

Pomysł na `dockvirt` narodził się z potrzeby stworzenia prostego, ale potężnego narzędzia do zarządzania środowiskami deweloperskimi, które łączyłoby zalety konteneryzacji (Docker) i wirtualizacji (KVM). Celem było stworzenie rozwiązania, które:

*   **Zapewnia pełną izolację**: W przeciwieństwie do samego Dockera, `dockvirt` uruchamia kontenery wewnątrz w pełni odizolowanej maszyny wirtualnej, co eliminuje problemy z konfliktami zależności, portów czy konfiguracji sieciowej na maszynie hosta.
*   **Jest lekkie i szybkie**: Dzięki wykorzystaniu `cloud-init` i obrazów chmurowych, proces tworzenia i konfiguracji VM jest zautomatyzowany i trwa zaledwie chwilę.
*   **Daje pełną kontrolę**: W odróżnieniu od narzędzi takich jak Multipass, `dockvirt` opiera się na standardowym ekosystemie libvirt, dając zaawansowanym użytkownikom pełną kontrolę nad każdym aspektem maszyny wirtualnej.

## 🆚 Porównanie z innymi narzędziami

| Narzędzie         | Główne zalety                                       | Główne wady                                             |
| ----------------- | --------------------------------------------------- | ------------------------------------------------------- |
| **dockvirt**      | Pełna izolacja (VM), prostota, automatyzacja        | Wymaga KVM (tylko Linux)                                |
| **Docker Compose**| Szybkość, prostota, duża popularność                | Brak pełnej izolacji od systemu hosta                   |
| **Vagrant**       | Wsparcie dla wielu providerów, elastyczność         | Wolniejszy start, bardziej złożona konfiguracja         |
| **Multipass**     | Bardzo prosty w użyciu, dobra integracja z Ubuntu   | Ograniczona kontrola, silne powiązanie z Canonical      |

## 🚀 Główne funkcje

*   **Automatyzacja od A do Z**: Tworzenie, konfigurowanie i usuwanie VM za pomocą prostych poleceń.
*   **Uniwersalność**: Działa na popularnych dystrybucjach Linuksa (Ubuntu, Fedora i inne).
*   **Elastyczność**: Pełna kontrola nad konfiguracją VM (RAM, CPU, dysk).
*   **Prekonfigurowane środowisko**: Automatyczna instalacja Dockera i Caddy wewnątrz VM.
*   **Izolacja**: Każde środowisko działa w oddzielnej maszynie wirtualnej.

## 🔧 Wymagania

*   System operacyjny Linux z obsługą KVM.
*   Zainstalowane pakiety: `qemu-kvm`, `libvirt-daemon-system`, `virt-manager`, `cloud-image-utils`.
*   Obraz chmurowy (`.qcow2`) dla wybranej dystrybucji (np. Ubuntu 22.04, Fedora Cloud Base).

## ⚙️ Instalacja

1.  **Zainstaluj z PyPI**:
    ```bash
    pip install dockvirt
    ```

2.  **Lub zainstaluj z repozytorium** (dla deweloperów):
    ```bash
    git clone https://github.com/dynapsys/dockvirt.git
    cd dockvirt
    make install
    ```

## 🏗️ Jak to działa?

### Przepływ procesu tworzenia VM

```mermaid
graph TD
    A[dockvirt up] --> B{Czy istnieje config.yaml?}
    B -->|Nie| C[Utwórz domyślny config.yaml]
    B -->|Tak| D[Wczytaj konfigurację]
    C --> D
    D --> E{Czy obraz OS istnieje lokalnie?}
    E -->|Nie| F[Pobierz obraz z URL]
    E -->|Tak| G[Użyj lokalnego obrazu]
    F --> G
    G --> H[Renderuj szablony cloud-init]
    H --> I[Utwórz ISO cloud-init]
    I --> J[Utwórz dysk VM z backing file]
    J --> K[Uruchom virt-install]
    K --> L[VM gotowa z Docker + Caddy]
```

### Architektura systemu

```
┌─────────────────────────────────────────────────────────────────┐
│                          HOST SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│  dockvirt CLI                                                   │
│  ├── config.py         (zarządzanie konfiguracją)              │
│  ├── image_manager.py  (pobieranie obrazów OS)                 │
│  ├── vm_manager.py     (tworzenie/usuwanie VM)                 │
│  └── cli.py           (interfejs użytkownika)                  │
├─────────────────────────────────────────────────────────────────┤
│  ~/.dockvirt/                                                   │
│  ├── config.yaml      (konfiguracja domyślna)                  │
│  ├── images/          (cache obrazów OS)                       │
│  └── vm_name/         (pliki cloud-init dla każdej VM)         │
├─────────────────────────────────────────────────────────────────┤
│  libvirt/KVM                                                    │
│  ├── virt-install     (tworzenie VM)                           │
│  ├── virsh            (zarządzanie VM)                         │
│  └── qemu-kvm         (wirtualizacja)                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        VIRTUAL MACHINE                         │
├─────────────────────────────────────────────────────────────────┤
│  Ubuntu/Fedora OS + cloud-init                                 │
│  ├── Docker Engine    (automatycznie zainstalowany)           │
│  └── docker-compose   (uruchamia kontenery)                   │
│      ├── Caddy        (reverse proxy na porcie 80/443)        │
│      └── App Container (Twoja aplikacja)                      │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Konfiguracja

`dockvirt` automatycznie tworzy plik konfiguracyjny `~/.dockvirt/config.yaml` przy pierwszym uruchomieniu:

```yaml
default_os: ubuntu22.04
images:
  ubuntu22.04:
    url: https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
    variant: ubuntu22.04
  fedora36:
    url: https://download.fedoraproject.org/pub/fedora/linux/releases/36/Cloud/x86_64/images/Fedora-Cloud-Base-36-1.5.x86_64.qcow2
    variant: fedora-cloud-base-36
```

## 🖥️ Użycie

Teraz używanie `dockvirt` jest znacznie prostsze - nie musisz już podawać ścieżek do obrazów:

```bash
# Użyj domyślnego OS (ubuntu22.04)
dockvirt up \
  --name my-app \
  --domain my-app.local \
  --image nginx:latest \
  --port 80

# Lub wybierz konkretny OS
dockvirt up \
  --name fedora-app \
  --domain fedora-app.local \
  --image httpd:latest \
  --port 80 \
  --os fedora36
```

Po utworzeniu VM, `dockvirt` wyświetli jej adres IP. Dodaj go do pliku `/etc/hosts`:

```
<adres_ip> my-app.local
```

## 📚 Przykłady użycia

Przygotowaliśmy kilka praktycznych przykładów, które pomogą Ci zacząć:

*   **[Przykład 1: Statyczna strona na Nginx](./examples/1-static-nginx-website)**
*   **[Przykład 2: Aplikacja webowa w Pythonie (Flask)](./examples/2-python-flask-app)**

## 🛠️ Development

Repozytorium zawiera `Makefile`, który ułatwia proces deweloperski. Zobacz plik [CONTRIBUTING.md](./CONTRIBUTING.md), aby dowiedzieć się, jak wnieść wkład w rozwój projektu.

## ✍️ Autor

**Tom Sapletta** - Doświadczony programista i entuzjasta otwartego oprogramowania. Pasjonat automatyzacji i tworzenia narzędzi ułatwiających pracę deweloperom.

## 📜 Licencja

Projekt jest udostępniany na licencji **Apache 2.0**. Szczegóły znajdują się w pliku [LICENSE](LICENSE).
