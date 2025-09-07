#!/usr/bin/env python3
"""
DockerVirt LAN Diagnosis - Comprehensive testing of network exposure
Tests content, connectivity, and diagnoses the port forwarding solution
"""

import subprocess
import time
import json
import requests
import socket
from datetime import datetime

def run_cmd(cmd, timeout=10):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_url_content(url, description):
    """Test URL and analyze content"""
    print(f"\n🔍 Test: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        
        print(f"   Status: {response.status_code}")
        print(f"   Size: {len(response.text)} bytes")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        # Show first few lines of content
        lines = response.text.split('\n')[:5]
        for i, line in enumerate(lines):
            if line.strip():
                print(f"   Line {i+1}: {line.strip()[:80]}...")
        
        return True, response.text, response.status_code
        
    except requests.exceptions.ConnectException:
        print(f"   ❌ Connection refused")
        return False, "", 0
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout")
        return False, "", 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, "", 0

def check_port_listening(host, port):
    """Check if port is listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_iptables_rules():
    """Check current iptables configuration"""
    print("\n🔧 IPTABLES RULES ANALYSIS:")
    
    # Check NAT rules
    success, nat_rules, _ = run_cmd("sudo iptables -t nat -L PREROUTING -n --line-numbers")
    if success:
        print("   📋 NAT PREROUTING rules:")
        for line in nat_rules.split('\n'):
            if 'DNAT' in line or 'REDIRECT' in line:
                print(f"      {line}")
    
    # Check INPUT rules
    success, input_rules, _ = run_cmd("sudo iptables -L INPUT -n --line-numbers")
    if success:
        print("   📋 INPUT rules (port 80 access):")
        for line in input_rules.split('\n'):
            if '80' in line and 'ACCEPT' in line:
                print(f"      {line}")

def diagnose_vm_status():
    """Check DockerVirt VM status"""
    print("\n🖥️ VM STATUS DIAGNOSIS:")
    
    # Check if VM is running
    success, vm_list, _ = run_cmd("sudo virsh list --state-running")
    if success and 'static-site' in vm_list:
        print("   ✅ VM 'static-site' is running")
        
        # Get VM IP
        success, dhcp_info, _ = run_cmd("sudo virsh net-dhcp-leases default")
        if success:
            lines = dhcp_info.split('\n')
            for line in lines:
                if 'static-site' in line:
                    import re
                    ip_match = re.search(r'192\.168\.122\.\d+', line)
                    if ip_match:
                        vm_ip = ip_match.group()
                        print(f"   📍 VM Internal IP: {vm_ip}")
                        
                        # Test VM direct access
                        vm_accessible = check_port_listening(vm_ip, 80)
                        print(f"   🌐 VM port 80: {'✅ Open' if vm_accessible else '❌ Closed/Filtered'}")
                        
                        return vm_ip
    else:
        print("   ❌ VM 'static-site' not running")
    
    return None

def test_port_forwarding_chain():
    """Test the complete port forwarding chain"""
    print("\n🔗 PORT FORWARDING CHAIN TEST:")
    
    # Get host IP
    success, host_ip, _ = run_cmd("hostname -I | awk '{print $1}'")
    if not success or not host_ip:
        success, host_ip, _ = run_cmd("ip route get 8.8.8.8 | grep -oP 'src \\K\\S+'")
    
    if host_ip:
        host_ip = host_ip.strip()
        print(f"   📍 Host IP: {host_ip}")
        
        # Test chain: Host IP:80 → localhost:8080 → VM
        tests = [
            ("localhost:8080", "Direct localhost (existing forwarding)"),
            (f"{host_ip}:80", "Host IP port 80 (new forwarding)"),
            ("127.0.0.1:80", "Loopback port 80"),
        ]
        
        results = {}
        for url_part, desc in tests:
            url = f"http://{url_part}/"
            accessible = check_port_listening(url_part.split(':')[0], int(url_part.split(':')[1]))
            print(f"   {desc}: {'✅ Listening' if accessible else '❌ Not listening'}")
            
            if accessible:
                success, content, status = test_url_content(url, desc)
                results[desc] = {'accessible': True, 'content_length': len(content) if success else 0}
            else:
                results[desc] = {'accessible': False, 'content_length': 0}
        
        return results, host_ip
    
    return {}, None

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║            DockerVirt LAN Diagnosis Tool                     ║
║          Comprehensive Network Exposure Testing              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"🕐 Test started: {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Check VM status
    vm_ip = diagnose_vm_status()
    
    # 2. Check iptables rules
    check_iptables_rules()
    
    # 3. Test port forwarding chain
    forwarding_results, host_ip = test_port_forwarding_chain()
    
    # 4. Test content from different access methods
    print("\n📄 CONTENT TESTING:")
    
    content_results = {}
    
    # Test localhost:8080 (should work)
    success, content, status = test_url_content("http://localhost:8080/", "Original localhost:8080")
    content_results['localhost_8080'] = {'success': success, 'size': len(content) if success else 0}
    
    if host_ip:
        # Test host IP:80 (new forwarding)
        success, content, status = test_url_content(f"http://{host_ip}:80/", "Network-exposed host:80")
        content_results['host_80'] = {'success': success, 'size': len(content) if success else 0}
    
    # 5. Network accessibility test
    print("\n🌐 NETWORK ACCESSIBILITY TEST:")
    if host_ip:
        # Ping test
        success, _, _ = run_cmd(f"ping -c 2 {host_ip}")
        print(f"   📡 Host pingable: {'✅ Yes' if success else '❌ No'}")
        
        # Port scan
        port_80_open = check_port_listening(host_ip, 80)
        port_8080_open = check_port_listening(host_ip, 8080)
        
        print(f"   🚪 Port 80 on {host_ip}: {'✅ Open' if port_80_open else '❌ Closed'}")
        print(f"   🚪 Port 8080 on {host_ip}: {'✅ Open' if port_8080_open else '❌ Closed'}")
    
    # 6. Summary and diagnosis
    print("\n" + "="*70)
    print("📊 DIAGNOSIS SUMMARY")
    print("="*70)
    
    print(f"\n🖥️ VM STATUS:")
    print(f"   VM Running: {'✅ Yes' if vm_ip else '❌ No'}")
    if vm_ip:
        print(f"   VM IP: {vm_ip}")
    
    print(f"\n🌐 NETWORK STATUS:")
    if host_ip:
        print(f"   Host IP: {host_ip}")
        print(f"   Port 80 Access: {'✅ Working' if host_ip and forwarding_results.get('Host IP port 80 (new forwarding)', {}).get('accessible') else '❌ Not working'}")
    
    print(f"\n📄 CONTENT DELIVERY:")
    for test_name, result in content_results.items():
        status = "✅ Working" if result['success'] else "❌ Failed"
        size = f"({result['size']} bytes)" if result['success'] else ""
        print(f"   {test_name}: {status} {size}")
    
    # 7. Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not vm_ip:
        print("   🔧 Start DockerVirt VM: cd examples/1-static-nginx-website && dockvirt up")
    
    if host_ip and not forwarding_results.get('Host IP port 80 (new forwarding)', {}).get('accessible'):
        print("   🔧 Port forwarding may need time to propagate")
        print("   🔧 Try: sudo bash scripts/dockvirt_lan_simple.sh --port 8080")
    
    if content_results.get('localhost_8080', {}).get('success') and host_ip:
        print(f"   ✅ Access from other devices: http://{host_ip}")
        print(f"   📱 Test on smartphone/tablet in same WiFi")
    
    print("\n" + "="*70)
    print(f"🕐 Test completed: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
