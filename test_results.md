# DockerVirt Examples Test Report
==================================================

**Summary:**
- Total Examples: 3
- Successful Builds: 3

## 1-static-nginx-website

✅ **Build:** SUCCESS (image: my-static-website:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Command failed: WARNING  --os-type is deprecated and does nothing. Please stop using it.
ERROR    Requested operation is not valid: network 'default' is not active
Domain installation does not appear to have been successful.
If it was, you can restart your domain by running:
  virsh --connect qemu:///session start test-1-static-nginx-website-ubuntu22.04
otherwise, please restart your installation.

- ❌ fedora38: FAILED - Unknown operating system: fedora38

## 2-python-flask-app

✅ **Build:** SUCCESS (image: my-flask-app:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Command failed: WARNING  --os-type is deprecated and does nothing. Please stop using it.
ERROR    Requested operation is not valid: network 'default' is not active
Domain installation does not appear to have been successful.
If it was, you can restart your domain by running:
  virsh --connect qemu:///session start test-2-python-flask-app-ubuntu22.04
otherwise, please restart your installation.

- ❌ fedora38: FAILED - Unknown operating system: fedora38

## 3-multi-os-comparison

✅ **Build:** SUCCESS (image: multi-os-demo:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Command failed: WARNING  --os-type is deprecated and does nothing. Please stop using it.
ERROR    Requested operation is not valid: network 'default' is not active
Domain installation does not appear to have been successful.
If it was, you can restart your domain by running:
  virsh --connect qemu:///session start test-3-multi-os-comparison-ubuntu22.04
otherwise, please restart your installation.

- ❌ fedora38: FAILED - Unknown operating system: fedora38
