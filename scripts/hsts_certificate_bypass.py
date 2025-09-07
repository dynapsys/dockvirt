#!/usr/bin/env python3
"""
HSTS + Certificate Bypass Solutions
Provides multiple working solutions for HSTS and self-signed certificate issues
"""

import subprocess
import os
import sys
import time

class HTTPSBypassSolutions:
    def __init__(self, domain="static-site-https.dockvirt.dev", port=8443):
        self.domain = domain
        self.port = port
        self.url = f"https://{domain}:{port}"
        
    def clear_firefox_hsts_cache(self):
        """Method 1: Clear Firefox HSTS cache"""
        print("=== METHOD 1: CLEAR FIREFOX HSTS CACHE ===")
        print("🔧 Instrukcje usunięcia HSTS cache:")
        print("   1. Otwórz Firefox")
        print("   2. Wpisz: about:networking#hsts")
        print("   3. W 'Delete domain security policies' wpisz: static-site-https.dockvirt.dev")
        print("   4. Kliknij 'Delete'")
        print("   5. Restart Firefox")
        print("   6. Spróbuj ponownie otworzyć stronę")
        print()
        
    def use_alternative_domain(self):
        """Method 2: Use alternative domain without HSTS"""
        print("=== METHOD 2: ALTERNATIVE DOMAIN (RECOMMENDED) ===")
        
        # Create alternative domain
        alt_domain = "https-demo.local"
        alt_url = f"https://{alt_domain}:{self.port}"
        
        print(f"🔧 Tworzenie alternatywnej domeny bez HSTS: {alt_domain}")
        
        # Update /etc/hosts
        try:
            # Remove old entry
            subprocess.run(f"sudo sed -i '/{alt_domain}/d' /etc/hosts", shell=True)
            # Add new entry
            subprocess.run(f"echo '127.0.0.1 {alt_domain}' | sudo tee -a /etc/hosts", shell=True)
            print(f"✅ /etc/hosts updated: {alt_domain} -> 127.0.0.1")
            print(f"🌐 Nowy URL bez HSTS: {alt_url}")
            print(f"📖 Otwórz w Firefox: {alt_url}")
            return alt_url
        except Exception as e:
            print(f"❌ Failed to update hosts: {e}")
            return None
    
    def create_firefox_dev_profile(self):
        """Method 3: Create Firefox developer profile"""
        print("=== METHOD 3: FIREFOX DEVELOPER PROFILE ===")
        
        profile_script = f"""#!/bin/bash
# Firefox Developer Profile - bypasses HTTPS checks
PROFILE_DIR="/tmp/firefox-dev-profile-$$"
mkdir -p "$PROFILE_DIR"

cat > "$PROFILE_DIR/user.js" << 'EOF'
// Disable HTTPS restrictions for development
user_pref("security.tls.insecure_fallback_hosts", "*.dockvirt.dev,*.local,localhost");
user_pref("security.mixed_content.block_active_content", false);
user_pref("security.mixed_content.block_display_content", false);
user_pref("security.cert_pinning.enforcement_level", 0);
user_pref("security.tls.hello_downgrade_check", false);
user_pref("browser.xul.error_pages.expert_bad_cert", true);
user_pref("network.stricttransportsecurity.preloadlist", false);
user_pref("security.tls.strict_fallback_hosts", "");
EOF

echo "🚀 Starting Firefox Developer Profile..."
firefox --profile "$PROFILE_DIR" --no-remote "{self.url}" &
echo "✅ Firefox Developer Profile started"
echo "🔧 Profile location: $PROFILE_DIR"
"""
        
        with open('/tmp/firefox_dev_launch.sh', 'w') as f:
            f.write(profile_script)
        os.chmod('/tmp/firefox_dev_launch.sh', 0o755)
        
        print("✅ Firefox developer profile script created")
        print("🚀 Run: /tmp/firefox_dev_launch.sh")
        
    def use_chromium_ignore_certs(self):
        """Method 4: Use Chromium with certificate ignore"""
        print("=== METHOD 4: CHROMIUM WITH CERTIFICATE BYPASS ===")
        
        chromium_script = f"""#!/bin/bash
# Chromium with certificate bypass
echo "🚀 Starting Chromium with certificate bypass..."
chromium-browser \\
    --ignore-certificate-errors \\
    --ignore-ssl-errors \\
    --ignore-certificate-errors-spki-list \\
    --disable-web-security \\
    --allow-running-insecure-content \\
    --disable-features=VizDisplayCompositor \\
    --user-data-dir=/tmp/chromium-dev \\
    "{self.url}" &
echo "✅ Chromium started with certificate bypass"
"""
        
        with open('/tmp/chromium_dev_launch.sh', 'w') as f:
            f.write(chromium_script)
        os.chmod('/tmp/chromium_dev_launch.sh', 0o755)
        
        print("✅ Chromium bypass script created")
        print("🚀 Run: /tmp/chromium_dev_launch.sh")
        
    def create_trusted_certificate(self):
        """Method 5: Create locally trusted certificate"""
        print("=== METHOD 5: LOCALLY TRUSTED CERTIFICATE ===")
        
        print("🔧 Creating CA and trusted certificate...")
        
        # Create CA certificate
        ca_commands = [
            "mkdir -p /tmp/https-certs",
            "cd /tmp/https-certs",
            
            # Create CA private key
            "openssl genrsa -out ca.key 2048",
            
            # Create CA certificate
            f"openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj '/CN=Local HTTPS CA'",
            
            # Create server private key
            "openssl genrsa -out server.key 2048",
            
            # Create certificate signing request
            f"openssl req -new -key server.key -out server.csr -subj '/CN={self.domain}'",
            
            # Create server certificate signed by CA
            "openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt"
        ]
        
        try:
            for cmd in ca_commands:
                subprocess.run(cmd, shell=True, check=True)
            
            print("✅ Certificates created in /tmp/https-certs/")
            print("🔧 To install CA certificate:")
            print("   Ubuntu/Debian: sudo cp /tmp/https-certs/ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates")
            print("   Firefox: Import /tmp/https-certs/ca.crt in Settings > Privacy & Security > Certificates")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Certificate creation failed: {e}")
    
    def headless_browser_test(self):
        """Method 6: Test with headless browser"""
        print("=== METHOD 6: HEADLESS BROWSER TEST ===")
        
        headless_test = f"""
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions

print("🔍 Testing with requests (Python)...")
try:
    response = requests.get("{self.url}", verify=False, timeout=5)
    print(f"✅ Python requests: Status {response.status_code}")
    print(f"📊 Content length: {len(response.content)} bytes")
    print(f"📄 Title in content: {'title' in response.text.lower()}")
except Exception as e:
    print(f"❌ Python requests failed: {e}")

print("\\n🔍 Testing with headless Firefox...")
try:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    
    driver = webdriver.Firefox(options=options)
    driver.get("{self.url}")
    
    title = driver.title
    print(f"✅ Headless Firefox: Title '{title}'")
    driver.quit()
    
except Exception as e:
    print(f"❌ Headless Firefox failed: {e}")
"""
        
        with open('/tmp/headless_browser_test.py', 'w') as f:
            f.write(headless_test)
            
        print("✅ Headless browser test script created")
        print("🚀 Run: python3 /tmp/headless_browser_test.py")
        
    def run_all_solutions(self):
        """Run all bypass solutions"""
        print("🔥 HSTS + CERTIFICATE BYPASS SOLUTIONS")
        print(f"🎯 Target: {self.url}")
        print("🔍 Problem: Firefox HSTS policy + SEC_ERROR_UNKNOWN_ISSUER")
        print("=" * 70)
        
        self.clear_firefox_hsts_cache()
        print()
        
        alt_url = self.use_alternative_domain()
        print()
        
        self.create_firefox_dev_profile()
        print()
        
        self.use_chromium_ignore_certs()
        print()
        
        self.create_trusted_certificate() 
        print()
        
        self.headless_browser_test()
        print()
        
        # Summary and recommendations
        print("=" * 70)
        print("🏆 RECOMMENDED SOLUTIONS (in order of effectiveness):")
        print("=" * 70)
        print("1️⃣ BEST: Use alternative domain without HSTS")
        if alt_url:
            print(f"   🌐 Open: {alt_url}")
        print()
        print("2️⃣ GOOD: Firefox developer profile") 
        print("   🚀 Run: /tmp/firefox_dev_launch.sh")
        print()
        print("3️⃣ ALTERNATIVE: Chromium with bypass")
        print("   🚀 Run: /tmp/chromium_dev_launch.sh")
        print()
        print("4️⃣ MANUAL: Clear HSTS cache")
        print("   🔧 Firefox: about:networking#hsts")
        print()
        print("5️⃣ ADVANCED: Install trusted certificate")
        print("   📁 Certificates in: /tmp/https-certs/")

if __name__ == "__main__":
    domain = sys.argv[1] if len(sys.argv) > 1 else "static-site-https.dockvirt.dev"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
    
    bypass = HTTPSBypassSolutions(domain, port)
    bypass.run_all_solutions()
