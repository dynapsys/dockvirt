# DockerVirt Examples Test Report
==================================================

**Summary:**
- Total Examples: 3
- Successful Builds: 3

## 1-static-nginx-website

✅ **Build:** SUCCESS (image: my-static-website:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Command failed: cp: cannot create regular file '/home/tom/.dockvirt/test-1-static-nginx-website-ubuntu22.04/cidata.iso': Permission denied
failed to copy image to /home/tom/.dockvirt/test-1-static-nginx-website-ubuntu22.04/cidata.iso
 (domain: )
- ❌ fedora38: FAILED - Unknown operating system: fedora38 (domain: )

## 2-python-flask-app

✅ **Build:** SUCCESS (image: my-flask-app:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - Command failed: cp: cannot create regular file '/home/tom/.dockvirt/test-2-python-flask-app-ubuntu22.04/cidata.iso': Permission denied
failed to copy image to /home/tom/.dockvirt/test-2-python-flask-app-ubuntu22.04/cidata.iso
 (domain: )
- ❌ fedora38: FAILED - Unknown operating system: fedora38 (domain: )

## 3-multi-os-comparison

✅ **Build:** SUCCESS (image: multi-os-demo:latest)

**OS Compatibility:**
- ❌ ubuntu22.04: FAILED - HTTP on IP failed, domain not resolving locally (domain: multi-os-demo.local)
- ❌ fedora38: FAILED - Unknown operating system: fedora38 (domain: )
