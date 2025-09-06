# Example 3: Comparing Different Operating Systems

This example shows how to easily switch between different operating systems in `dockvirt` and how to configure your own images.

## Available Operating Systems

`dockvirt` supports the following by default:

- **Ubuntu 22.04** (`ubuntu22.04`) - default
- **Fedora 38** (`fedora38`)

## Quick Tests of Different OS

This example shows a simple HTML page that will be automatically built inside the VM.

### 1. Ubuntu 22.04 (default)

```bash
cd examples/3-multi-os-comparison

dockvirt up \
  --name ubuntu-test \
  --domain ubuntu-test.local \
  --image multi-os-demo:latest \
  --port 80
```

### 2. Fedora 38

```bash
cd examples/3-multi-os-comparison
# Build happens inside the VM automatically.
# Optional (not required): pre-build on host
# docker build -t multi-os-demo:latest .

dockvirt up \
  --name fedora-test \
  --domain fedora-test.local \
  --image multi-os-demo:latest \
  --port 80 \
  --os fedora38
```

## Configuring Custom Images

You can add your own images by editing the `~/.dockvirt/config.yaml` file:

```yaml
default_os: ubuntu22.04
images:
  ubuntu22.04:
    url: https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
    variant: ubuntu22.04
  fedora38:
    url: https://download.fedoraproject.org/pub/fedora/linux/releases/38/Cloud/x86_64/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2
    variant: fedora38
  # Add your own image
  debian12:
    url: https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2
    variant: debian12
```

Then use:
```bash
dockvirt up \
  --name debian-test \
  --domain debian-test.local \
  --image nginx:latest \
  --port 80 \
  --os debian12
```

## Performance Comparison

You can run the same applications on different operating systems to compare performance:

```bash
# Test on Ubuntu
time dockvirt up --name perf-ubuntu --domain ubuntu.local --image nginx:latest --port 80

# Test on Fedora  
time dockvirt up --name perf-fedora --domain fedora.local --image nginx:latest --port 80 --os fedora38
```

## Cleanup

```bash
dockvirt down --name ubuntu-test
dockvirt down --name fedora-test
dockvirt down --name debian-test
```

## Image Cache

Images are stored in `~/.dockvirt/images/`:
```bash
ls -la ~/.dockvirt/images/
# jammy-server-cloudimg-amd64.img
# Fedora-Cloud-Base-38-1.6.x86_64.qcow2
# debian-12-generic-amd64.qcow2
```

Tip: If a reverse proxy is used in the VM (Caddy), IP-based HTTP checks may require a Host header:

```bash
curl -H 'Host: ubuntu-test.local' http://<ip>/
curl -H 'Host: fedora-test.local' http://<ip>/
```
