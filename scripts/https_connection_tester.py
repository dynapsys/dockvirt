#!/usr/bin/env python3
"""
HTTPS Connection Tester - Comprehensive analysis tool
Tests connection, DNS, content, and headless browser behavior
"""

import sys
import ssl
import socket
import requests
import subprocess
import urllib3
from urllib.parse import urlparse
import json
import time

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HTTPSConnectionTester:
    def __init__(self, url):
        self.url = url
        self.parsed_url = urlparse(url)
        self.host = self.parsed_url.hostname
        self.port = self.parsed_url.port or 443
        self.results = {}
        
    def test_dns_resolution(self):
        """Test DNS resolution"""
        print("=== 1️⃣ DNS RESOLUTION TEST ===")
        try:
            ip = socket.gethostbyname(self.host)
            self.results['dns'] = {'success': True, 'ip': ip}
            print(f"✅ DNS resolved: {self.host} -> {ip}")
            return True
        except Exception as e:
            self.results['dns'] = {'success': False, 'error': str(e)}
            print(f"❌ DNS resolution failed: {e}")
            return False
    
    def test_port_connectivity(self):
        """Test basic port connectivity"""
        print(f"\n=== 2️⃣ PORT CONNECTIVITY TEST ({self.port}) ===")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                self.results['port'] = {'success': True}
                print(f"✅ Port {self.port} is open and accessible")
                return True
            else:
                self.results['port'] = {'success': False, 'error': f'Connection refused (code: {result})'}
                print(f"❌ Port {self.port} connection failed (code: {result})")
                return False
        except Exception as e:
            self.results['port'] = {'success': False, 'error': str(e)}
            print(f"❌ Port connectivity test failed: {e}")
            return False
    
    def test_ssl_certificate(self):
        """Test SSL certificate details"""
        print("\n=== 3️⃣ SSL CERTIFICATE TEST ===")
        try:
            # Create SSL context that accepts self-signed certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Get certificate info
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cert = ssock.getpeercert()
                    
            # Also try to get certificate with verification (will fail but gives us error details)
            try:
                context_verify = ssl.create_default_context()
                with socket.create_connection((self.host, self.port), timeout=5) as sock:
                    with context_verify.wrap_socket(sock, server_hostname=self.host) as ssock:
                        verified_cert = ssock.getpeercert()
                        verification_status = "✅ Certificate verified"
            except ssl.SSLError as ssl_e:
                verification_status = f"❌ Certificate verification failed: {ssl_e}"
            
            self.results['ssl'] = {
                'success': True,
                'certificate': cert,
                'verification': verification_status
            }
            
            print(f"✅ SSL connection established")
            print(f"📄 Certificate subject: {cert.get('subject', 'N/A')}")
            print(f"📄 Certificate issuer: {cert.get('issuer', 'N/A')}")
            print(f"📄 Valid from: {cert.get('notBefore', 'N/A')}")
            print(f"📄 Valid to: {cert.get('notAfter', 'N/A')}")
            print(f"🔐 Verification status: {verification_status}")
            
            return True
            
        except Exception as e:
            self.results['ssl'] = {'success': False, 'error': str(e)}
            print(f"❌ SSL certificate test failed: {e}")
            return False
    
    def test_http_content(self):
        """Test HTTP content retrieval"""
        print("\n=== 4️⃣ HTTP CONTENT TEST ===")
        try:
            # Test with requests (ignoring SSL verification)
            response = requests.get(self.url, verify=False, timeout=10)
            
            self.results['content'] = {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.content),
                'content_preview': response.text[:200]
            }
            
            print(f"✅ HTTP request successful")
            print(f"📊 Status code: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📊 Content length: {len(response.content)} bytes")
            print(f"🔐 HSTS header: {response.headers.get('Strict-Transport-Security', 'Not present')}")
            print(f"📄 Content preview: {response.text[:100]}...")
            
            return True
            
        except Exception as e:
            self.results['content'] = {'success': False, 'error': str(e)}
            print(f"❌ HTTP content test failed: {e}")
            return False
    
    def test_headless_browser(self):
        """Test connection using headless browser"""
        print("\n=== 5️⃣ HEADLESS BROWSER TEST ===")
        
        # Test with curl first (simpler)
        try:
            print("🔍 Testing with curl...")
            curl_result = subprocess.run([
                'curl', '-k', '-I', '--connect-timeout', '5', self.url
            ], capture_output=True, text=True, timeout=10)
            
            if curl_result.returncode == 0:
                print("✅ curl connection successful")
                print("📊 curl headers:")
                for line in curl_result.stdout.split('\n')[:5]:
                    if line.strip():
                        print(f"   {line}")
            else:
                print(f"❌ curl connection failed: {curl_result.stderr}")
                
        except Exception as e:
            print(f"❌ curl test failed: {e}")
        
        # Test with Firefox headless if available
        try:
            print("\n🔍 Testing with Firefox headless...")
            
            # Create a simple Python script to test with Selenium
            firefox_test_script = f'''
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException

options = Options()
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--ignore-certificate-errors-spki-list") 
options.add_argument("--disable-web-security")

try:
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(10)
    
    print("🌐 Attempting to load: {self.url}")
    driver.get("{self.url}")
    
    title = driver.title
    current_url = driver.current_url
    page_source_length = len(driver.page_source)
    
    print(f"✅ Firefox headless connection successful")
    print(f"📄 Page title: {{title}}")
    print(f"🔗 Current URL: {{current_url}}")
    print(f"📊 Page source length: {{page_source_length}} chars")
    
    driver.quit()
    
except WebDriverException as e:
    print(f"❌ Firefox WebDriver error: {{e}}")
except TimeoutException as e:
    print(f"❌ Firefox timeout: {{e}}")
except Exception as e:
    print(f"❌ Firefox headless test failed: {{e}}")
'''
            
            # Write and execute the Firefox test
            with open('/tmp/firefox_headless_test.py', 'w') as f:
                f.write(firefox_test_script)
            
            firefox_result = subprocess.run([
                'python3', '/tmp/firefox_headless_test.py'
            ], capture_output=True, text=True, timeout=15)
            
            print(firefox_result.stdout)
            if firefox_result.stderr:
                print(f"Firefox stderr: {firefox_result.stderr}")
                
            self.results['headless_browser'] = {
                'curl_success': curl_result.returncode == 0 if 'curl_result' in locals() else False,
                'firefox_output': firefox_result.stdout
            }
            
        except Exception as e:
            print(f"❌ Headless browser test failed: {e}")
            self.results['headless_browser'] = {'success': False, 'error': str(e)}
    
    def test_hsts_bypass_methods(self):
        """Test methods to bypass HSTS"""
        print("\n=== 6️⃣ HSTS BYPASS METHODS TEST ===")
        
        # Method 1: Direct IP access
        if 'dns' in self.results and self.results['dns']['success']:
            ip = self.results['dns']['ip']
            print(f"🔍 Testing direct IP access: https://{ip}:{self.port}")
            
            try:
                direct_ip_url = f"https://{ip}:{self.port}"
                response = requests.get(direct_ip_url, verify=False, timeout=5)
                print(f"✅ Direct IP access works (status: {response.status_code})")
            except Exception as e:
                print(f"❌ Direct IP access failed: {e}")
        
        # Method 2: Different port
        print(f"\n🔍 Testing alternative approaches:")
        print(f"💡 Method 1: Use direct IP: https://{self.results['dns']['ip']}:{self.port}")
        print(f"💡 Method 2: Clear HSTS cache in Firefox: about:networking#hsts")
        print(f"💡 Method 3: Use different domain (no HSTS history)")
        print(f"💡 Method 4: Use incognito/private browsing")
        
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print(f"🔥 HTTPS CONNECTION TESTER")
        print(f"🎯 Target: {self.url}")
        print(f"🏠 Host: {self.host}:{self.port}")
        print("=" * 60)
        
        # Run all tests
        self.test_dns_resolution()
        self.test_port_connectivity() 
        self.test_ssl_certificate()
        self.test_http_content()
        self.test_headless_browser()
        self.test_hsts_bypass_methods()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        success_count = sum(1 for test, result in self.results.items() 
                          if isinstance(result, dict) and result.get('success', False))
        total_tests = len([k for k in self.results.keys() if k != 'headless_browser'])
        
        print(f"✅ Successful tests: {success_count}/{total_tests}")
        
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                status = "✅" if result.get('success', False) else "❌"
                print(f"{status} {test_name.upper()}: {'PASS' if result.get('success', False) else 'FAIL'}")
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS:")
        if not self.results.get('dns', {}).get('success'):
            print("   - Fix DNS resolution first")
        elif not self.results.get('port', {}).get('success'):
            print("   - Check if service is running on the port")
        elif not self.results.get('ssl', {}).get('success'):
            print("   - Fix SSL certificate configuration")
        elif self.results.get('content', {}).get('success'):
            print("   - Server works! Issue is likely HSTS/certificate trust")
            print("   - Use Firefox developer profile with disabled certificate checks")
            print("   - Clear HSTS cache: about:networking#hsts")
        
        return self.results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 https_connection_tester.py <https_url>")
        print("Example: python3 https_connection_tester.py https://static-site-https.dockvirt.dev:8443")
        sys.exit(1)
    
    url = sys.argv[1]
    tester = HTTPSConnectionTester(url)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('/tmp/https_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: /tmp/https_test_results.json")
