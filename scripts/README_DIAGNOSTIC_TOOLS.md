# DockerVirt HTTPS Diagnostic Tools

This directory contains comprehensive diagnostic and troubleshooting tools for HTTPS domains in DockerVirt environments.

## 🔍 Available Tools

### 1. HTTPS Connection Tester (`https_connection_tester.py`)

Comprehensive testing tool that validates all aspects of HTTPS connectivity:

- **DNS Resolution**: Verifies domain name resolution
- **Port Connectivity**: Tests if the target port is accessible
- **SSL Certificate Analysis**: Examines certificate details and trust status
- **HTTP Content Retrieval**: Tests actual content delivery
- **Headless Browser Testing**: Automated browser behavior simulation

#### Usage

```bash
# Basic usage
python3 scripts/https_connection_tester.py https://static-site-https.dockvirt.dev:8443

# Test different domain
python3 scripts/https_connection_tester.py https://your-app.local:443
```

#### Example Output

```
🔥 HTTPS CONNECTION TESTER
🎯 Target: https://static-site-https.dockvirt.dev:8443
🏠 Host: static-site-https.dockvirt.dev:8443
============================================================

=== 1️⃣ DNS RESOLUTION TEST ===
✅ DNS resolved: static-site-https.dockvirt.dev -> 127.0.0.1

=== 2️⃣ PORT CONNECTIVITY TEST (8443) ===
✅ Port 8443 is open and accessible

=== 3️⃣ SSL CERTIFICATE TEST ===
✅ SSL connection established
📄 Certificate subject: [('CN', 'static-site-https.dockvirt.dev')]
📄 Certificate issuer: [('CN', 'static-site-https.dockvirt.dev')]
🔐 Verification status: ❌ Certificate verification failed: [SSL: CERTIFICATE_VERIFY_FAILED]

=== 4️⃣ HTTP CONTENT TEST ===
✅ HTTP request successful
📊 Status code: 200
📊 Content-Type: text/html
🔐 HSTS header: Not present
📄 Content preview: <!DOCTYPE html>...

=== 5️⃣ HEADLESS BROWSER TEST ===
✅ curl connection successful
✅ Firefox headless connection successful

📋 TEST SUMMARY
============================================================
✅ Successful tests: 4/4
✅ DNS: PASS
✅ PORT: PASS  
✅ SSL: PASS
✅ CONTENT: PASS
```

### 2. HSTS Certificate Bypass (`hsts_certificate_bypass.py`)

Provides multiple solutions for bypassing HSTS policies and certificate trust issues:

#### Usage

```bash
# Generate all bypass solutions
python3 scripts/hsts_certificate_bypass.py static-site-https.dockvirt.dev 8443

# Use default domain and port
python3 scripts/hsts_certificate_bypass.py
```

#### Solutions Provided

1. **Alternative Domain Method** (Recommended)
   - Creates `https-demo.local` domain without HSTS history
   - Updates `/etc/hosts` automatically
   - Allows certificate exceptions in browsers

2. **Firefox Developer Profile**
   - Creates temporary Firefox profile with disabled HTTPS checks
   - Generates launch script at `/tmp/firefox_dev_launch.sh`
   - Bypasses HSTS and certificate validation

3. **Chromium Certificate Bypass**
   - Provides Chromium launch script with ignore certificate flags
   - Generated at `/tmp/chromium_dev_launch.sh`
   - Suitable for development testing

4. **Manual HSTS Cache Clearing**
   - Instructions for clearing Firefox HSTS cache
   - Access `about:networking#hsts` in Firefox
   - Delete specific domain entries

5. **Locally Trusted Certificate Generation**
   - Creates CA certificate and server certificate
   - Certificates stored in `/tmp/https-certs/`
   - Instructions for system-wide trust installation

### 3. Firefox Developer Profile (`firefox-dev-https.sh`)

Pre-configured Firefox launcher that bypasses HTTPS restrictions for development:

#### Usage

```bash
# Launch with specific URL
./scripts/firefox-dev-https.sh https://static-site-https.dockvirt.dev:8443/

# Launch with default URL
./scripts/firefox-dev-https.sh
```

#### Features

- Temporary profile with disabled certificate validation
- HSTS policy bypass for `*.dockvirt.dev` domains
- Automatic cleanup on browser exit
- No impact on regular Firefox installation

## 🚀 Quick Start Guide

### Problem: Firefox shows "SEC_ERROR_UNKNOWN_ISSUER" + HSTS Policy

```bash
# Step 1: Run bypass script to create alternative domain
python3 scripts/hsts_certificate_bypass.py

# Step 2: Access via new domain (no HSTS restrictions)
# Browser URL: https://https-demo.local:8443/

# Alternative: Use Firefox developer profile  
./scripts/firefox-dev-https.sh https://static-site-https.dockvirt.dev:8443/
```

### Problem: "Unable to Connect" - Connection Refused

```bash
# Step 1: Diagnose the issue
python3 scripts/https_connection_tester.py https://your-domain:port

# Step 2: Check common causes based on test results:
# ❌ DNS: Update /etc/hosts or check domain configuration
# ❌ PORT: Verify service is running and port is correct
# ❌ SSL: Check certificate configuration
# ❌ CONTENT: Verify web service is responding
```

### Problem: VM Not Responding After Creation

```bash
# Diagnosis workflow:
# 1. Check VM status
sudo virsh list

# 2. Check VM IP assignment
sudo virsh net-dhcp-leases default

# 3. Test basic connectivity
ping VM_IP

# 4. Wait for VM boot completion (can take 60+ seconds)
sleep 60 && python3 scripts/https_connection_tester.py https://domain:port

# 5. If still not responding, restart VM
sudo virsh destroy vm-name && sudo virsh start vm-name
```

## 🔧 Integration with DockerVirt

### Automatic Validation

These tools integrate with DockerVirt's automation agent:

```bash
# Run agent with HTTPS validation
make agent

# Auto-fix HTTPS issues  
make agent-fix
```

### Project-Specific Testing

Use with `.dockvirt` configuration files:

```bash
# In your project directory with .dockvirt file
cd examples/1-static-nginx-website/

# Test the configured domain
python3 ../../scripts/https_connection_tester.py https://$(grep domain .dockvirt | cut -d= -f2):$(grep port .dockvirt | cut -d= -f2)
```

## 📊 Troubleshooting Matrix

| Issue | Diagnostic Tool | Solution |
|-------|----------------|----------|
| Certificate not trusted | `https_connection_tester.py` | Use alternative domain or Firefox dev profile |
| HSTS policy blocking | `hsts_certificate_bypass.py` | Clear HSTS cache or use bypass domain |
| Connection refused | `https_connection_tester.py` | Check VM status and wait for boot |
| DNS not resolving | `https_connection_tester.py` | Update `/etc/hosts` or check domain config |
| Port not accessible | `https_connection_tester.py` | Verify service running and port configuration |

## 📝 Output Files

Tools generate the following files:

- `/tmp/https_test_results.json` - Detailed test results from connection tester
- `/tmp/firefox_dev_launch.sh` - Firefox developer profile launcher
- `/tmp/chromium_dev_launch.sh` - Chromium bypass launcher
- `/tmp/https-certs/` - Generated certificates for local trust
- `/tmp/headless_browser_test.py` - Headless browser testing script

## 🔒 Security Notes

These tools are designed for **development and testing environments only**:

- Certificate bypasses should never be used in production
- Temporary profiles and certificates are automatically cleaned up
- Always verify you're testing against local/development domains
- HSTS bypasses reduce security - use only when necessary

## 🤝 Contributing

To add new diagnostic capabilities:

1. Follow the existing tool patterns for consistent output
2. Include comprehensive error handling and user-friendly messages  
3. Add integration with the automation agent for automated testing
4. Update this README with usage examples and troubleshooting info
