#!/usr/bin/env python3
"""
VM Validation Script - sprawdza czy VM rzeczywiście działa poprawnie
"""
import subprocess
import time
import sys
import requests
import re

def run_cmd(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"

def validate_vm_complete(vm_name, domain, expected_port=80):
    """Complete VM validation"""
    print(f"🔍 VALIDATING VM: {vm_name}")
    print("=" * 50)
    
    # 1. Check if VM exists and is running
    print("1. Checking VM status...")
    success, stdout, stderr = run_cmd(f"virsh --connect qemu:///system list --state-running | grep {vm_name}")
    if not success:
        print(f"❌ VM {vm_name} is not running")
        return False
    print(f"✅ VM {vm_name} is running")
    
    # 2. Get VM IP
    print("2. Getting VM IP address...")
    success, stdout, stderr = run_cmd("virsh --connect qemu:///system net-dhcp-leases default")
    if not success:
        print(f"❌ Failed to get DHCP leases: {stderr}")
        return False
    
    vm_ip = None
    for line in stdout.splitlines():
        if vm_name in line:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)/\d+', line)
            if match:
                vm_ip = match.group(1)
                break
    
    if not vm_ip:
        print(f"❌ No IP found for VM {vm_name}")
        return False
    print(f"✅ VM IP: {vm_ip}")
    
    # 3. Test ping connectivity
    print("3. Testing network connectivity...")
    success, stdout, stderr = run_cmd(f"ping -c 2 -W 3 {vm_ip}")
    if not success:
        print(f"❌ Ping failed to {vm_ip}")
        return False
    print(f"✅ Ping successful to {vm_ip}")
    
    # 4. Test port accessibility
    print(f"4. Testing port {expected_port} accessibility...")
    success, stdout, stderr = run_cmd(f"timeout 5 nc -zv {vm_ip} {expected_port}")
    if not success:
        print(f"❌ Port {expected_port} not accessible on {vm_ip}")
        return False
    print(f"✅ Port {expected_port} is accessible")
    
    # 5. Test HTTP response
    print("5. Testing HTTP response...")
    try:
        response = requests.get(f"http://{vm_ip}/", timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP returned status {response.status_code}")
            return False
        if len(response.text) < 10:
            print(f"❌ HTTP response too short: {len(response.text)} chars")
            return False
        print(f"✅ HTTP response OK (status {response.status_code}, {len(response.text)} chars)")
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
        return False
    
    # 6. Test HTTP with Host header (for Caddy/reverse proxy)
    print("6. Testing HTTP with Host header...")
    try:
        headers = {'Host': domain}
        response = requests.get(f"http://{vm_ip}/", headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP with Host header returned status {response.status_code}")
            return False
        print(f"✅ HTTP with Host header OK (status {response.status_code})")
    except Exception as e:
        print(f"❌ HTTP with Host header failed: {e}")
        return False
    
    # 7. Check /etc/hosts entry
    print("7. Checking /etc/hosts entry...")
    success, stdout, stderr = run_cmd(f"grep '{vm_ip}.*{domain}' /etc/hosts")
    if not success:
        print(f"⚠️  /etc/hosts entry missing, adding...")
        success, _, _ = run_cmd(f"echo '{vm_ip} {domain}' | sudo tee -a /etc/hosts")
        if success:
            print(f"✅ Added {vm_ip} {domain} to /etc/hosts")
        else:
            print(f"❌ Failed to add /etc/hosts entry")
            return False
    else:
        print(f"✅ /etc/hosts entry exists")
    
    # 8. Test domain resolution
    print("8. Testing domain access...")
    try:
        response = requests.get(f"http://{domain}/", timeout=10)
        if response.status_code != 200:
            print(f"❌ Domain access returned status {response.status_code}")
            return False
        print(f"✅ Domain access OK: http://{domain}/")
    except Exception as e:
        print(f"❌ Domain access failed: {e}")
        return False
    
    print("=" * 50)
    print(f"✅ VM {vm_name} VALIDATION SUCCESSFUL")
    print(f"🌐 Access URL: http://{domain}/")
    print(f"🌐 Direct IP: http://{vm_ip}/")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python validate_vm.py <vm_name> <domain> [port]")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    domain = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    
    if validate_vm_complete(vm_name, domain, port):
        sys.exit(0)
    else:
        print(f"\n❌ VM {vm_name} VALIDATION FAILED")
        sys.exit(1)
