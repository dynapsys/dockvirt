#!/usr/bin/env python3
"""
DockerVirt Network Diagnostic & Auto-Fix
Szczegółowy skrypt diagnostyczny z automatyczną naprawą
"""

import subprocess
import sys
import os
import time
import re
from datetime import datetime

class DockerVirtDiagnostic:
    def __init__(self):
        self.results = {}
        self.fixes = []
        self.host_ip = None
        self.vm_ip = None
        
    def log(self, message, level="INFO"):
        """Log z kolorami"""
        colors = {
            "INFO": "\033[36m",    # Cyan
            "SUCCESS": "\033[32m", # Green  
            "WARNING": "\033[33m", # Yellow
            "ERROR": "\033[31m",   # Red
            "RESET": "\033[0m"     # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{level}] {message}{reset}")
    
    def run_cmd(self, cmd, desc, timeout=10):
        """Uruchom komendę z logowaniem"""
        self.log(f"🔍 {desc}")
        self.log(f"Komenda: {cmd}")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                self.log(f"✅ SUCCESS (exit {result.returncode})", "SUCCESS")
            else:
                self.log(f"❌ FAILED (exit {result.returncode})", "ERROR")
            
            if result.stdout and result.stdout.strip():
                print(f"📤 STDOUT:\n{result.stdout}")
            if result.stderr and result.stderr.strip():
                print(f"📥 STDERR:\n{result.stderr}")
                
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            
        except subprocess.TimeoutExpired:
            self.log(f"⏰ TIMEOUT po {timeout}s", "WARNING")
            return False, "", f"Timeout after {timeout}s"
        except Exception as e:
            self.log(f"💥 EXCEPTION: {e}", "ERROR")
            return False, "", str(e)
    
    def test_host_network(self):
        """Test sieci hosta"""
        self.log("=" * 50)
        self.log("FAZA 1: SIEĆ HOSTA", "INFO")
        self.log("=" * 50)
        
        # Wykryj IP hosta
        success, stdout, stderr = self.run_cmd(
            'ip route get 1.1.1.1 | awk "{print $7}" | head -1',
            "Wykrywanie IP hosta w sieci lokalnej"
        )
        
        if success and stdout:
            self.host_ip = stdout.strip()
            self.log(f"🌐 Host IP: {self.host_ip}", "SUCCESS")
        else:
            self.log("❌ Nie można wykryć IP hosta", "ERROR")
            self.fixes.append("# Sprawdź konfigurację sieci hosta")
            
        # Test dostępu do internetu
        success, stdout, stderr = self.run_cmd(
            "ping -c 2 8.8.8.8",
            "Test dostępu do internetu",
            timeout=15
        )
        
        if not success:
            self.fixes.append("# Sprawdź połączenie internetowe")
    
    def test_libvirt(self):
        """Test libvirt"""
        self.log("=" * 50)
        self.log("FAZA 2: LIBVIRT", "INFO") 
        self.log("=" * 50)
        
        # Status libvirtd
        success, stdout, stderr = self.run_cmd(
            "sudo systemctl is-active libvirtd",
            "Status usługi libvirtd"
        )
        
        if not success:
            self.log("❌ libvirtd nie działa", "ERROR")
            self.fixes.append("sudo systemctl start libvirtd")
            self.fixes.append("sudo systemctl enable libvirtd")
        
        # Sieci libvirt
        success, stdout, stderr = self.run_cmd(
            "sudo virsh net-list --all",
            "Lista sieci libvirt"
        )
        
        if success and "default" in stdout:
            if "active" not in stdout or "yes" not in stdout:
                self.log("⚠️ Sieć default nieaktywna", "WARNING")
                self.fixes.append("sudo virsh net-start default")
                self.fixes.append("sudo virsh net-autostart default")
        else:
            self.log("❌ Brak sieci default", "ERROR")
            self.fixes.append("# Utwórz sieć default libvirt")
    
    def test_vm_status(self):
        """Test statusu VM"""
        self.log("=" * 50)
        self.log("FAZA 3: STATUS VM", "INFO")
        self.log("=" * 50)
        
        # Lista VM
        success, stdout, stderr = self.run_cmd(
            "sudo virsh list --all",
            "Lista wszystkich VM"
        )
        
        if success:
            if "static-site" in stdout and "running" in stdout:
                self.log("✅ VM static-site działa", "SUCCESS")
            elif "static-site" in stdout:
                self.log("⚠️ VM static-site istnieje ale nie działa", "WARNING")
                self.fixes.append("sudo virsh start static-site")
            else:
                self.log("❌ VM static-site nie istnieje", "ERROR")
                self.fixes.append("cd /home/tom/github/dynapsys/dockvirt/examples/1-static-nginx-website && dockvirt up")
        
        # IP VM
        success, stdout, stderr = self.run_cmd(
            "sudo virsh net-dhcp-leases default",
            "DHCP leases - IP maszyn"
        )
        
        if success and stdout:
            vm_ip_match = re.search(r'192\.168\.122\.\d+', stdout)
            if vm_ip_match:
                self.vm_ip = vm_ip_match.group()
                self.log(f"🖥️ VM IP: {self.vm_ip}", "SUCCESS")
            else:
                self.log("⚠️ Nie znaleziono IP VM", "WARNING")
    
    def test_vm_connectivity(self):
        """Test łączności z VM"""
        if not self.vm_ip:
            self.log("⏭️ Pomijanie testów VM - brak IP", "WARNING")
            return
            
        self.log("=" * 50)
        self.log("FAZA 4: ŁĄCZNOŚĆ Z VM", "INFO")
        self.log("=" * 50)
        
        # Ping do VM
        success, stdout, stderr = self.run_cmd(
            f"ping -c 3 {self.vm_ip}",
            f"Ping do VM {self.vm_ip}",
            timeout=15
        )
        
        if not success:
            self.log("❌ Brak łączności z VM", "ERROR")
            self.fixes.append(f"# Sprawdź sieć VM: ping {self.vm_ip}")
            return
        
        # SSH do VM
        success, stdout, stderr = self.run_cmd(
            f"nc -zv {self.vm_ip} 22",
            f"Test portu SSH VM {self.vm_ip}:22"
        )
        
        # HTTP na VM
        success, stdout, stderr = self.run_cmd(
            f"nc -zv {self.vm_ip} 80",
            f"Test portu HTTP VM {self.vm_ip}:80"
        )
        
        if not success:
            self.log("❌ Port 80 na VM niedostępny", "ERROR")
            self.fixes.append(f"# Sprawdź Docker w VM: ssh ubuntu@{self.vm_ip}")
            self.fixes.append(f"# Na VM uruchom: sudo docker ps")
        else:
            # Test HTTP request
            success, stdout, stderr = self.run_cmd(
                f"curl -s -m 10 http://{self.vm_ip}:80/",
                f"HTTP request do VM {self.vm_ip}"
            )
            
            if success and stdout:
                self.log("✅ VM HTTP działa!", "SUCCESS")
            else:
                self.log("⚠️ VM odpowiada ale bez zawartości", "WARNING")
    
    def test_port_forwarding(self):
        """Test port forwarding"""
        self.log("=" * 50)
        self.log("FAZA 5: PORT FORWARDING", "INFO")
        self.log("=" * 50)
        
        # Test localhost:80
        success, stdout, stderr = self.run_cmd(
            "nc -zv localhost 80",
            "Test localhost:80"
        )
        
        if not success:
            self.log("❌ localhost:80 niedostępny", "ERROR")
            self.fixes.append("# Sprawdź port forwarding DockerVirt")
            self.fixes.append("# VM musi przekierowywać port 80 na host")
        
        # Test external IP
        if self.host_ip:
            success, stdout, stderr = self.run_cmd(
                f"nc -zv {self.host_ip} 80",
                f"Test external IP {self.host_ip}:80"
            )
            
            if not success:
                self.log(f"❌ {self.host_ip}:80 niedostępny z sieci", "ERROR")
                self.fixes.append("# Port forwarding nie działa dla sieci zewnętrznej")
                self.fixes.append("sudo ufw allow 80")
                self.fixes.append(f"# Sprawdź firewall dla {self.host_ip}:80")
    
    def test_firewall(self):
        """Test firewall"""
        self.log("=" * 50)
        self.log("FAZA 6: FIREWALL", "INFO")
        self.log("=" * 50)
        
        # UFW status
        success, stdout, stderr = self.run_cmd(
            "sudo ufw status",
            "Status UFW firewall"
        )
        
        if success and "Status: active" in stdout:
            if "80" not in stdout:
                self.log("⚠️ UFW aktywny ale port 80 nie otwarty", "WARNING")
                self.fixes.append("sudo ufw allow 80")
                self.fixes.append("sudo ufw allow from 192.168.0.0/16 to any port 80")
        
        # Procesy na porcie 80
        success, stdout, stderr = self.run_cmd(
            "sudo netstat -tulpn | grep :80",
            "Procesy nasłuchujące na porcie 80"
        )
        
        if not success or not stdout:
            self.log("⚠️ Brak procesów na porcie 80", "WARNING")
            self.fixes.append("# Brak processów na porcie 80 - sprawdź DockerVirt port forwarding")
    
    def create_fix_script(self):
        """Utwórz skrypt naprawczy"""
        if not self.fixes:
            self.log("✅ Nie znaleziono problemów do naprawy!", "SUCCESS")
            return None
            
        fix_script = """#!/bin/bash
# DockerVirt Auto-Fix Script
# Generated by diagnostic script

set -e  # Exit on any error

echo "🔧 DockerVirt Auto-Fix Script"
echo "=============================="
echo ""

"""
        
        for i, fix in enumerate(self.fixes, 1):
            if fix.startswith("#"):
                fix_script += f"{fix}\n"
            else:
                fix_script += f"""
echo "Fix {i}: {fix}"
{fix}
sleep 2
"""

        fix_script += """

echo ""
echo "✅ Auto-fix completed!"
echo ""
echo "🧪 Test accessibility:"
"""

        if self.host_ip:
            fix_script += f"""echo "From this computer: http://localhost:80/"
echo "From network: http://{self.host_ip}:80/"
"""

        if self.vm_ip:
            fix_script += f"""echo "Direct VM access: http://{self.vm_ip}:80/"
"""

        fix_script += """
echo ""
echo "🔄 Re-run diagnostic: python3 scripts/dockvirt_diagnostic.py"
"""
        
        script_path = "/tmp/dockvirt_autofix.sh"
        with open(script_path, 'w') as f:
            f.write(fix_script)
        os.chmod(script_path, 0o755)
        
        self.log(f"📜 Skrypt naprawczy: {script_path}", "SUCCESS")
        return script_path
    
    def print_summary(self):
        """Podsumowanie"""
        self.log("=" * 60)
        self.log("🎯 PODSUMOWANIE DIAGNOSTYKI", "INFO")
        self.log("=" * 60)
        
        print(f"🌐 Host IP w sieci: {self.host_ip or 'NIEZNANY'}")
        print(f"🖥️ VM IP: {self.vm_ip or 'NIEZNALEZIONY'}")
        print(f"🔧 Problemów do naprawy: {len([f for f in self.fixes if not f.startswith('#')])}")
        
        if self.host_ip and self.vm_ip:
            self.log("📋 DOSTĘP Z SIECI LOKALNEJ:", "INFO")
            print(f"   • Z tego komputera: http://localhost:80/")  
            print(f"   • Z sieci lokalnej: http://{self.host_ip}:80/")
            print(f"   • Bezpośrednio VM: http://{self.vm_ip}:80/")
            print(f"")
            print(f"📝 Konfiguracja DNS dla innych komputerów:")
            print(f"   sudo nano /etc/hosts")
            print(f"   {self.host_ip} static-site.dockvirt.dev")
            print(f"   Następnie: http://static-site.dockvirt.dev:80/")
    
    def run_full_diagnostic(self):
        """Uruchom pełną diagnostykę"""
        self.log("🚀 DockerVirt Network Diagnostic & Auto-Fix", "INFO")
        self.log(f"Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.test_host_network()
            self.test_libvirt()
            self.test_vm_status()
            self.test_vm_connectivity()
            self.test_port_forwarding()
            self.test_firewall()
            
            # Utwórz skrypt naprawczy
            fix_script = self.create_fix_script()
            
            self.print_summary()
            
            if fix_script:
                print(f"\n🔧 AUTOMATYCZNA NAPRAWA:")
                print(f"   bash {fix_script}")
                print(f"\n🔍 PONOWNA DIAGNOSTYKA:")
                print(f"   python3 scripts/dockvirt_diagnostic.py")
            
        except KeyboardInterrupt:
            self.log("\n⏹️ Diagnostyka przerwana przez użytkownika", "WARNING")
        except Exception as e:
            self.log(f"\n💥 BŁĄD podczas diagnostyki: {e}", "ERROR")

def main():
    if os.geteuid() == 0:
        print("❌ Nie uruchamiaj jako root!")
        sys.exit(1)
    
    diagnostic = DockerVirtDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()
