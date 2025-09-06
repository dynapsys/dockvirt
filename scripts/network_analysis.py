#!/usr/bin/env python3
"""
Comprehensive Network Analysis for DockerVirt HTTPS Domains
Analyzes DNS, ping, curl, routing, and certificates
"""
import subprocess
import json
import socket
import ssl
import urllib.request
import urllib.error
from pathlib import Path
import sys
import time

DOMAINS = [
    "flask-app.dockvirt.dev",
    "static-site.dockvirt.dev", 
    "frontend.dockvirt.dev"
]

def run_cmd(cmd, timeout=10):
    """Execute command with timeout"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def analyze_dns(domain):
    """Analyze DNS resolution with dig"""
    print(f"\n🔍 DNS Analysis for {domain}")
    print("=" * 50)
    
    # Check if dig is available
    success, _, _ = run_cmd("which dig")
    if not success:
        print("❌ dig not available, using nslookup")
        success, stdout, stderr = run_cmd(f"nslookup {domain}")
    else:
        success, stdout, stderr = run_cmd(f"dig {domain} +short")
    
    if success:
        if stdout.strip():
            print(f"✅ DNS Resolution: {stdout.strip()}")
        else:
            print("⚠️  No DNS records found")
    else:
        print(f"❌ DNS Error: {stderr}")
    
    # Check /etc/hosts
    try:
        with open('/etc/hosts', 'r') as f:
            hosts_content = f.read()
            if domain in hosts_content:
                for line in hosts_content.split('\n'):
                    if domain in line and not line.strip().startswith('#'):
                        print(f"📋 /etc/hosts: {line.strip()}")
            else:
                print(f"⚠️  {domain} not found in /etc/hosts")
    except Exception as e:
        print(f"❌ /etc/hosts read error: {e}")

def analyze_ping(domain):
    """Analyze ping connectivity"""
    print(f"\n🏓 Ping Analysis for {domain}")
    print("=" * 50)
    
    success, stdout, stderr = run_cmd(f"ping -c 3 -W 2 {domain}")
    
    if success:
        lines = stdout.split('\n')
        for line in lines:
            if 'PING' in line or 'bytes from' in line or 'packet loss' in line or 'rtt' in line:
                if 'packet loss' in line:
                    if '0% packet loss' in line:
                        print(f"✅ {line.strip()}")
                    else:
                        print(f"⚠️  {line.strip()}")
                else:
                    print(f"📊 {line.strip()}")
    else:
        print(f"❌ Ping failed: {stderr}")

def analyze_routing(domain):
    """Analyze routing to domain"""
    print(f"\n🗺️  Routing Analysis for {domain}")
    print("=" * 50)
    
    # Get IP for traceroute
    try:
        ip = socket.gethostbyname(domain)
        print(f"📍 Resolved IP: {ip}")
        
        # Check if it's local
        if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
            print(f"🏠 Local/Private IP detected")
        
        # Simple route check
        success, stdout, stderr = run_cmd(f"ip route get {ip}")
        if success:
            print(f"🛤️  Route: {stdout.strip()}")
        
        # Network interface check
        success, stdout, stderr = run_cmd("ip addr show | grep -E '(inet|UP)'")
        if success:
            print("🔗 Network Interfaces:")
            for line in stdout.split('\n'):
                if 'inet' in line or 'UP' in line:
                    print(f"   {line.strip()}")
                    
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
    except Exception as e:
        print(f"❌ Routing analysis error: {e}")

def analyze_http_https(domain):
    """Analyze HTTP and HTTPS connectivity"""
    print(f"\n🌐 HTTP/HTTPS Analysis for {domain}")
    print("=" * 50)
    
    ports = [
        (80, "HTTP"),
        (443, "HTTPS"),
        (8443, "HTTPS-Alt")
    ]
    
    for port, protocol in ports:
        print(f"\n--- {protocol} (Port {port}) ---")
        
        # Test port connectivity
        success, stdout, stderr = run_cmd(f"nc -z -w 3 {domain} {port}")
        if success:
            print(f"✅ Port {port} open")
        else:
            print(f"❌ Port {port} closed/filtered")
            continue
        
        # Test HTTP/HTTPS with curl
        if protocol.startswith("HTTPS"):
            url = f"https://{domain}:{port}/"
            curl_cmd = f"curl -I -k -m 5 --connect-timeout 3 '{url}'"
        else:
            url = f"http://{domain}:{port}/"
            curl_cmd = f"curl -I -m 5 --connect-timeout 3 '{url}'"
        
        success, stdout, stderr = run_cmd(curl_cmd)
        
        if success:
            lines = stdout.split('\n')
            for line in lines[:10]:  # First 10 lines
                if line.strip():
                    if 'HTTP/' in line:
                        status = line.strip()
                        if '200' in status:
                            print(f"✅ {status}")
                        elif '301' in status or '302' in status:
                            print(f"🔄 {status}")
                        else:
                            print(f"⚠️  {status}")
                    elif line.startswith('Location:') or line.startswith('Server:'):
                        print(f"📋 {line.strip()}")
        else:
            print(f"❌ curl failed: {stderr}")

def analyze_certificates(domain):
    """Analyze SSL certificates"""
    print(f"\n🔐 Certificate Analysis for {domain}")
    print("=" * 50)
    
    # Check local certificates
    cert_dir = Path.home() / ".dockvirt" / "certs" / "domains"
    domain_name = domain.replace('.dockvirt.dev', '')
    cert_file = cert_dir / f"{domain_name}-cert.pem"
    key_file = cert_dir / f"{domain_name}-key.pem"
    
    print(f"📁 Local certificates:")
    print(f"   Cert: {cert_file} - {'✅' if cert_file.exists() else '❌'}")
    print(f"   Key: {key_file} - {'✅' if key_file.exists() else '❌'}")
    
    if cert_file.exists():
        # Analyze certificate
        success, stdout, stderr = run_cmd(f"openssl x509 -in {cert_file} -text -noout")
        if success:
            for line in stdout.split('\n'):
                if 'Subject:' in line or 'Issuer:' in line or 'Not Before:' in line or 'Not After:' in line:
                    print(f"📜 {line.strip()}")
    
    # Test live certificate
    for port in [443, 8443]:
        print(f"\n--- Live Certificate Test (Port {port}) ---")
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, port), timeout=3) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    print(f"✅ SSL Connection successful")
                    print(f"🔒 TLS Version: {ssock.version()}")
                    print(f"🔒 Cipher: {ssock.cipher()}")
                    if cert:
                        print(f"📜 Subject: {cert.get('subject', 'N/A')}")
                        print(f"📜 Issuer: {cert.get('issuer', 'N/A')}")
                        
        except socket.timeout:
            print(f"⏱️  Connection timeout on port {port}")
        except ConnectionRefusedError:
            print(f"❌ Connection refused on port {port}")
        except Exception as e:
            print(f"❌ SSL test failed on port {port}: {e}")

def check_vm_status():
    """Check libvirt VM status"""
    print(f"\n🖥️  VM Status Analysis")
    print("=" * 50)
    
    # Check libvirt VMs
    success, stdout, stderr = run_cmd("export LIBVIRT_DEFAULT_URI=qemu:///system && virsh list --all")
    if success:
        print("📊 VM Status:")
        for line in stdout.split('\n'):
            if line.strip() and not line.startswith('Id') and not line.startswith('---'):
                print(f"   {line}")
    else:
        print(f"❌ VM status check failed: {stderr}")
    
    # Check DHCP leases
    success, stdout, stderr = run_cmd("export LIBVIRT_DEFAULT_URI=qemu:///system && virsh net-dhcp-leases default")
    if success:
        print("\n📡 DHCP Leases:")
        for line in stdout.split('\n'):
            if line.strip() and not line.startswith('Expiry') and not line.startswith('---'):
                print(f"   {line}")
    else:
        print(f"❌ DHCP leases check failed: {stderr}")

def main():
    """Main analysis function"""
    print("🔍 DockerVirt Network Analysis")
    print("=" * 60)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check VM status first
    check_vm_status()
    
    # Analyze each domain
    for domain in DOMAINS:
        print(f"\n{'='*60}")
        print(f"🌐 ANALYZING: {domain}")
        print('='*60)
        
        analyze_dns(domain)
        analyze_ping(domain) 
        analyze_routing(domain)
        analyze_http_https(domain)
        analyze_certificates(domain)
    
    print(f"\n{'='*60}")
    print("✅ Network Analysis Complete")
    print('='*60)

if __name__ == "__main__":
    main()
