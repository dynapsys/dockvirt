# Przykład 3: Porównanie różnych systemów operacyjnych

Ten przykład pokazuje, jak łatwo przełączać się między różnymi systemami operacyjnymi w `dockvirt` oraz jak skonfigurować własne obrazy.

## Dostępne systemy operacyjne

`dockvirt` domyślnie obsługuje:

- **Ubuntu 22.04** (`ubuntu22.04`) - domyślny
- **Fedora 36** (`fedora36`)

## Szybkie testy różnych OS

### 1. Ubuntu 22.04 (domyślny)

```bash
dockvirt up \
  --name ubuntu-test \
  --domain ubuntu-test.local \
  --image nginx:latest \
  --port 80
```

### 2. Fedora 36

```bash
dockvirt up \
  --name fedora-test \
  --domain fedora-test.local \
  --image nginx:latest \
  --port 80 \
  --os fedora36
```

## Konfiguracja własnych obrazów

Możesz dodać własne obrazy, edytując plik `~/.dockvirt/config.yaml`:

```yaml
default_os: ubuntu22.04
images:
  ubuntu22.04:
    url: https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
    variant: ubuntu22.04
  fedora36:
    url: https://download.fedoraproject.org/pub/fedora/linux/releases/36/Cloud/x86_64/images/Fedora-Cloud-Base-36-1.5.x86_64.qcow2
    variant: fedora-cloud-base-36
  # Dodaj własny obraz
  debian12:
    url: https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2
    variant: debian12
```

Następnie użyj:
```bash
dockvirt up \
  --name debian-test \
  --domain debian-test.local \
  --image nginx:latest \
  --port 80 \
  --os debian12
```

## Porównanie wydajności

Możesz uruchomić te same aplikacje na różnych systemach operacyjnych, aby porównać wydajność:

```bash
# Test na Ubuntu
time dockvirt up --name perf-ubuntu --domain ubuntu.local --image nginx:latest --port 80

# Test na Fedorze  
time dockvirt up --name perf-fedora --domain fedora.local --image nginx:latest --port 80 --os fedora36
```

## Czyszczenie

```bash
dockvirt down --name ubuntu-test
dockvirt down --name fedora-test
dockvirt down --name debian-test
```

## Cache obrazów

Obrazy są przechowywane w `~/.dockvirt/images/`:
```bash
ls -la ~/.dockvirt/images/
# jammy-server-cloudimg-amd64.img
# Fedora-Cloud-Base-36-1.5.x86_64.qcow2
# debian-12-generic-amd64.qcow2
```
