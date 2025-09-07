#!/usr/bin/env python3
"""
DockerVirt Network Access Setup
Configures VM networking for access from other computers in the same network.
"""

import subprocess
import sys
import os
import json

def run_command(cmd, check=True):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def get_host_ip():
    """Get host machine IP address in local network."""
    print("🔍 Detecting host machine IP address...")
    
    # Try different methods to get IP
    commands = [
        "ip route get 1.1.1.1 | grep -oP 'src \\K[\\d.]+'",
        "hostname -I | awk '{print $1}'",
        "ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1"
    ]
    
    for cmd in commands:
        stdout, stderr = run_command(cmd, check=False)
        if stdout and '.' in stdout:
            print(f"✅ Host IP detected: {stdout}")
            return stdout
    
    print("❌ Could not detect host IP automatically")
    return None

def check_vm_status():
    """Check if DockerVirt VMs are running."""
    print("\n🔍 Checking DockerVirt VM status...")
    
    stdout, stderr = run_command("sudo virsh list", check=False)
    if "running" in stdout:
        print("✅ VMs are running")
        print(stdout)
        return True
    else:
        print("❌ No running VMs found")
        print("Run 'dockvirt up' in your project directory first")
        return False

def get_vm_ip():
    """Get VM IP address."""
    print("\n🔍 Getting VM IP address...")
    
    stdout, stderr = run_command("sudo virsh net-dhcp-leases default", check=False)
    if stdout and "192.168" in stdout:
        # Extract IP from DHCP leases
        lines = stdout.split('\n')
        for line in lines:
            if "192.168" in line:
                parts = line.split()
                for part in parts:
                    if "192.168" in part and "/" in part:
                        vm_ip = part.split('/')[0]
                        print(f"✅ VM IP: {vm_ip}")
                        return vm_ip
    
    print("❌ Could not detect VM IP")
    return None

def check_port_accessibility(host_ip, port=8443):
    """Check if port is accessible from host."""
    print(f"\n🔍 Checking port {port} accessibility...")
    
    # Test local port accessibility
    stdout, stderr = run_command(f"nc -zv localhost {port}", check=False)
    if "succeeded" in stdout or "succeeded" in stderr:
        print(f"✅ Port {port} is accessible locally")
        
        # Test external accessibility
        stdout, stderr = run_command(f"nc -zv {host_ip} {port}", check=False)
        if "succeeded" in stdout or "succeeded" in stderr:
            print(f"✅ Port {port} is accessible externally on {host_ip}")
            return True
        else:
            print(f"❌ Port {port} is not accessible externally")
            return False
    else:
        print(f"❌ Port {port} is not accessible locally")
        return False

def create_hosts_entry(host_ip, domain):
    """Create /etc/hosts entry suggestions."""
    print(f"\n📝 DNS Configuration Instructions")
    print("=" * 50)
    
    print(f"To access from OTHER computers in your network:")
    print(f"1. On each remote computer, add this line to /etc/hosts:")
    print(f"   {host_ip} {domain}")
    print()
    print(f"2. Command to add it:")
    print(f"   echo '{host_ip} {domain}' | sudo tee -a /etc/hosts")
    print()
    print(f"3. Then access via: https://{domain}:8443/")
    print()
    print(f"Alternative: Access directly via IP:")
    print(f"   https://{host_ip}:8443/")

def setup_firewall_rules(port=8443):
    """Setup firewall rules for external access."""
    print(f"\n🔥 Firewall Configuration")
    print("=" * 50)
    
    # Check if ufw is active
    stdout, stderr = run_command("sudo ufw status", check=False)
    if "Status: active" in stdout:
        print("UFW firewall is active. Adding rules...")
        
        # Add firewall rule
        stdout, stderr = run_command(f"sudo ufw allow {port}", check=False)
        if "Rules updated" in stdout:
            print(f"✅ Firewall rule added for port {port}")
        else:
            print(f"❌ Failed to add firewall rule: {stderr}")
    else:
        print("UFW firewall is not active")
    
    # Check iptables
    stdout, stderr = run_command("sudo iptables -L INPUT | grep -i drop", check=False)
    if stdout:
        print("⚠️  Iptables may be blocking connections")
        print("Consider adding rule:")
        print(f"   sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT")

def main():
    """Main setup function."""
    print("🌐 DockerVirt Network Access Setup")
    print("=" * 50)
    
    if os.geteuid() == 0:
        print("❌ Don't run this script as root. Run as regular user.")
        sys.exit(1)
    
    # Get domain from command line or use default
    domain = sys.argv[1] if len(sys.argv) > 1 else "flask-app.dockvirt.dev"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
    
    print(f"🎯 Target: {domain}:{port}")
    
    # Step 1: Get host IP
    host_ip = get_host_ip()
    if not host_ip:
        print("\n❌ Cannot proceed without host IP address")
        sys.exit(1)
    
    # Step 2: Check VM status
    if not check_vm_status():
        print("\n❌ Start your DockerVirt VM first with: dockvirt up")
        sys.exit(1)
    
    # Step 3: Get VM IP
    vm_ip = get_vm_ip()
    
    # Step 4: Check port accessibility
    port_accessible = check_port_accessibility(host_ip, port)
    
    # Step 5: Create DNS instructions
    create_hosts_entry(host_ip, domain)
    
    # Step 6: Firewall setup
    setup_firewall_rules(port)
    
    # Final summary
    print(f"\n📋 SUMMARY")
    print("=" * 50)
    print(f"✅ Host IP: {host_ip}")
    if vm_ip:
        print(f"✅ VM IP: {vm_ip}")
    print(f"{'✅' if port_accessible else '❌'} Port {port}: {'Accessible' if port_accessible else 'Not accessible'}")
    
    print(f"\n🎯 Access URLs:")
    print(f"   Local: https://localhost:{port}/")
    print(f"   Network: https://{host_ip}:{port}/")
    print(f"   Domain: https://{domain}:{port}/ (after DNS setup)")
    
    if not port_accessible:
        print(f"\n⚠️  TROUBLESHOOTING:")
        print(f"   - Wait for VM to fully boot (60+ seconds)")
        print(f"   - Check if service is running inside VM")
        print(f"   - Verify port forwarding configuration")
        print(f"   - Check firewall settings")

if __name__ == "__main__":
    main()
