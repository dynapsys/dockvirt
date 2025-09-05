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

## 🖥️ Użycie

Aby utworzyć nową maszynę wirtualną, użyj polecenia `dockvirt up`.

```bash
dockvirt up \
  --name my-app \
  --domain my-app.local \
  --image nginx:latest \
  --port 80 \
  --base-image /path/to/ubuntu-22.04.qcow2 \
  --os-variant ubuntu22.04
```

Po utworzeniu VM, `dockvirt` wyświetli jej adres IP. Dodaj go do pliku `/etc/hosts`, aby uzyskać dostęp przez domenę:

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
