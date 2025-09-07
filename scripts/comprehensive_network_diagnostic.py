#!/usr/bin/env python3
"""
DockerVirt Comprehensive Network Diagnostic Script
Szczegółowy skrypt diagnostyczny z timeoutami i logowaniem
"""

import subprocess
import json
import time
import socket
import requests
import os
import sys
from datetime import datetime
import threading
import signal

class NetworkDiagnostic:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {'passed': 0, 'failed': 0, 'warnings': 0},
            'recommendations': []
        }
        self.timeout_seconds = 30
        self.log_file = f"/tmp/dockvirt_diagnostic_{int(time.time())}.log"
        
    def log(self, message, level="INFO"):
        """Log message z timestampem"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def run_command_with_timeout(self, cmd, timeout=None, check_exit=True):
        """Uruchom komendę z timeoutem"""
        if timeout is None:
            timeout = self.timeout_seconds
            
        try:
            self.log(f"Executing: {cmd}")
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                timeout=timeout, check=check_exit
            )
            return True, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            self.log(f"TIMEOUT: Command exceeded {timeout}s: {cmd}", "ERROR")
            return False, "", f"Timeout after {timeout}s"
        except subprocess.CalledProcessError as e:
            self.log(f"FAILED: Command failed with exit code {e.returncode}: {cmd}", "ERROR")
            return False, e.stdout.strip(), e.stderr.strip()
        except Exception as e:
            self.log(f"ERROR: Exception running command: {cmd} - {str(e)}", "ERROR")
            return False, "", str(e)
    
    def test_basic_connectivity(self):
        """Test 1: Podstawowa łączność sieciowa"""
        self.log("=== TEST 1: PODSTAWOWA ŁĄCZNOŚĆ SIECIOWA ===")
        test_name = "basic_connectivity"
        self.results['tests'][test_name] = {}
        
        # Test internetu
        self.log("Testowanie dostępu do internetu...")
        success, stdout, stderr = self.run_command_with_timeout("ping -c 2 8.8.8.8", timeout=10)
        self.results['tests'][test_name]['internet'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test DNS
        self.log("Testowanie DNS...")
        success, stdout, stderr = self.run_command_with_timeout("nslookup google.com", timeout=10)
        self.results['tests'][test_name]['dns'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Sprawdź IP hosta w sieci lokalnej
        self.log("Wykrywanie IP hosta w sieci lokalnej...")
        success, stdout, stderr = self.run_command_with_timeout("ip route get 1.1.1.1 | awk '{print $7}' | head -1")
        host_ip = stdout if success else None
        self.results['tests'][test_name]['host_ip'] = {
            'success': success, 'ip': host_ip, 'stdout': stdout, 'stderr': stderr
        }
        
        if host_ip:
            self.log(f"Host IP w sieci lokalnej: {host_ip}")
        else:
            self.log("BŁĄD: Nie można wykryć IP hosta", "ERROR")
    
    def test_libvirt_status(self):
        """Test 2: Status libvirt"""
        self.log("=== TEST 2: STATUS LIBVIRT ===")
        test_name = "libvirt_status"
        self.results['tests'][test_name] = {}
        
        # Status libvirtd
        self.log("Sprawdzanie statusu libvirtd...")
        success, stdout, stderr = self.run_command_with_timeout("sudo systemctl is-active libvirtd")
        self.results['tests'][test_name]['service_status'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Lista sieci
        self.log("Sprawdzanie sieci libvirt...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh net-list --all")
        self.results['tests'][test_name]['networks'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Status sieci default
        self.log("Sprawdzanie sieci default...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh net-info default")
        self.results['tests'][test_name]['default_network'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Lista VM
        self.log("Lista maszyn wirtualnych...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh list --all")
        self.results['tests'][test_name]['vm_list'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
    
    def test_vm_status(self):
        """Test 3: Status konkretnej VM (static-site)"""
        self.log("=== TEST 3: STATUS VM STATIC-SITE ===")
        test_name = "vm_status"
        self.results['tests'][test_name] = {}
        
        # Status VM
        self.log("Sprawdzanie statusu VM static-site...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh domstate static-site")
        self.results['tests'][test_name]['vm_state'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # IP VM
        self.log("Sprawdzanie IP VM...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh domifaddr static-site")
        self.results['tests'][test_name]['vm_ip_domifaddr'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Alternatywny sposób sprawdzania IP
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh net-dhcp-leases default")
        self.results['tests'][test_name]['dhcp_leases'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Wyciągnij IP z wyników
        vm_ip = None
        if self.results['tests'][test_name]['dhcp_leases']['success']:
            lines = self.results['tests'][test_name]['dhcp_leases']['stdout'].split('\n')
            for line in lines:
                if 'static-site' in line or '192.168.122' in line:
                    parts = line.split()
                    for part in parts:
                        if '192.168.122' in part and '/' in part:
                            vm_ip = part.split('/')[0]
                            break
        
        self.results['tests'][test_name]['extracted_vm_ip'] = vm_ip
        if vm_ip:
            self.log(f"VM IP: {vm_ip}")
        else:
            self.log("OSTRZEŻENIE: Nie można wykryć IP VM", "WARNING")
    
    def test_vm_connectivity(self):
        """Test 4: Łączność z VM"""
        self.log("=== TEST 4: ŁĄCZNOŚĆ Z VM ===")
        test_name = "vm_connectivity"
        self.results['tests'][test_name] = {}
        
        vm_ip = self.results['tests'].get('vm_status', {}).get('extracted_vm_ip')
        if not vm_ip:
            self.log("Pomijanie testów łączności - brak IP VM", "WARNING")
            return
        
        # Ping VM
        self.log(f"Ping do VM {vm_ip}...")
        success, stdout, stderr = self.run_command_with_timeout(f"ping -c 3 {vm_ip}", timeout=15)
        self.results['tests'][test_name]['ping'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test portu SSH (22)
        self.log(f"Test portu SSH (22) na VM {vm_ip}...")
        success, stdout, stderr = self.run_command_with_timeout(f"nc -zv {vm_ip} 22", timeout=10)
        self.results['tests'][test_name]['ssh_port'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test portu HTTP (80)
        self.log(f"Test portu HTTP (80) na VM {vm_ip}...")
        success, stdout, stderr = self.run_command_with_timeout(f"nc -zv {vm_ip} 80", timeout=10)
        self.results['tests'][test_name]['http_port'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test HTTP request
        if self.results['tests'][test_name]['http_port']['success']:
            self.log(f"Test HTTP request do {vm_ip}...")
            success, stdout, stderr = self.run_command_with_timeout(f"curl -s -m 10 http://{vm_ip}:80/", timeout=15)
            self.results['tests'][test_name]['http_request'] = {
                'success': success, 'stdout': stdout, 'stderr': stderr
            }
    
    def test_port_forwarding(self):
        """Test 5: Port forwarding na hoście"""
        self.log("=== TEST 5: PORT FORWARDING ===")
        test_name = "port_forwarding"
        self.results['tests'][test_name] = {}
        
        # Test portu 80 na localhost
        self.log("Test portu 80 na localhost...")
        success, stdout, stderr = self.run_command_with_timeout("nc -zv localhost 80", timeout=5)
        self.results['tests'][test_name]['localhost_80'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test HTTP na localhost
        self.log("Test HTTP request na localhost:80...")
        success, stdout, stderr = self.run_command_with_timeout("curl -s -m 10 http://localhost:80/", timeout=15)
        self.results['tests'][test_name]['localhost_http'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Test na zewnętrznym IP
        host_ip = self.results['tests'].get('basic_connectivity', {}).get('host_ip', {}).get('ip')
        if host_ip:
            self.log(f"Test portu 80 na zewnętrznym IP {host_ip}...")
            success, stdout, stderr = self.run_command_with_timeout(f"nc -zv {host_ip} 80", timeout=5)
            self.results['tests'][test_name]['external_80'] = {
                'success': success, 'stdout': stdout, 'stderr': stderr
            }
            
            self.log(f"Test HTTP na zewnętrznym IP {host_ip}...")
            success, stdout, stderr = self.run_command_with_timeout(f"curl -s -m 10 http://{host_ip}:80/", timeout=15)
            self.results['tests'][test_name]['external_http'] = {
                'success': success, 'stdout': stdout, 'stderr': stderr
            }
    
    def test_docker_in_vm(self):
        """Test 6: Docker w VM"""
        self.log("=== TEST 6: DOCKER W VM ===")
        test_name = "docker_in_vm"
        self.results['tests'][test_name] = {}
        
        vm_ip = self.results['tests'].get('vm_status', {}).get('extracted_vm_ip')
        if not vm_ip:
            self.log("Pomijanie testów Docker - brak IP VM", "WARNING")
            return
        
        # Test SSH connection i Docker
        ssh_commands = [
            "whoami",
            "docker --version",
            "sudo docker ps -a",
            "sudo docker images",
            "sudo systemctl status docker"
        ]
        
        for cmd in ssh_commands:
            self.log(f"SSH command: {cmd}")
            full_cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 ubuntu@{vm_ip} "{cmd}"'
            success, stdout, stderr = self.run_command_with_timeout(full_cmd, timeout=20, check_exit=False)
            self.results['tests'][test_name][f'ssh_{cmd.replace(" ", "_")}'] = {
                'success': success, 'stdout': stdout, 'stderr': stderr
            }
    
    def test_firewall_settings(self):
        """Test 7: Ustawienia firewall"""
        self.log("=== TEST 7: USTAWIENIA FIREWALL ===")
        test_name = "firewall_settings"
        self.results['tests'][test_name] = {}
        
        # UFW status
        self.log("Sprawdzanie UFW...")
        success, stdout, stderr = self.run_command_with_timeout("sudo ufw status verbose")
        self.results['tests'][test_name]['ufw_status'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # iptables rules
        self.log("Sprawdzanie iptables...")
        success, stdout, stderr = self.run_command_with_timeout("sudo iptables -L -n")
        self.results['tests'][test_name]['iptables'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
        
        # Listening ports
        self.log("Sprawdzanie otwartych portów...")
        success, stdout, stderr = self.run_command_with_timeout("sudo netstat -tulpn | grep :80")
        self.results['tests'][test_name]['port_80_listeners'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
    
    def test_dockvirt_config(self):
        """Test 8: Konfiguracja DockerVirt"""
        self.log("=== TEST 8: KONFIGURACJA DOCKVIRT ===")
        test_name = "dockvirt_config"
        self.results['tests'][test_name] = {}
        
        # .dockvirt file
        config_file = "/home/tom/github/dynapsys/dockvirt/examples/1-static-nginx-website/.dockvirt"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
            self.results['tests'][test_name]['config_file'] = {
                'success': True, 'content': content
            }
            self.log(".dockvirt config file found")
        else:
            self.results['tests'][test_name]['config_file'] = {
                'success': False, 'error': 'Config file not found'
            }
            self.log("BŁĄD: .dockvirt config file not found", "ERROR")
        
        # VM XML config
        self.log("Sprawdzanie konfiguracji VM...")
        success, stdout, stderr = self.run_command_with_timeout("sudo virsh dumpxml static-site")
        self.results['tests'][test_name]['vm_xml'] = {
            'success': success, 'stdout': stdout, 'stderr': stderr
        }
    
    def generate_recommendations(self):
        """Generuj rekomendacje na podstawie wyników"""
        self.log("=== GENEROWANIE REKOMENDACJI ===")
        
        recommendations = []
        
        # Sprawdź VM status
        vm_state = self.results['tests'].get('vm_status', {}).get('vm_state', {})
        if vm_state.get('stdout') != 'running':
            recommendations.append({
                'priority': 'HIGH', 
                'issue': 'VM static-site nie działa',
                'solution': 'sudo virsh start static-site'
            })
        
        # Sprawdź port forwarding
        port_80_test = self.results['tests'].get('port_forwarding', {}).get('localhost_80', {})
        if not port_80_test.get('success', False):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Port 80 na localhost nie jest dostępny',
                'solution': 'Skonfiguruj port forwarding lub sprawdź Docker container w VM'
            })
        
        # Sprawdź VM connectivity
        vm_ping = self.results['tests'].get('vm_connectivity', {}).get('ping', {})
        if vm_ping and not vm_ping.get('success', False):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Brak łączności z VM',
                'solution': 'Sprawdź sieć libvirt: sudo virsh net-start default'
            })
        
        # Sprawdź Docker w VM
        docker_ps = self.results['tests'].get('docker_in_vm', {}).get('ssh_sudo_docker_ps_-a', {})
        if docker_ps and not docker_ps.get('success', False):
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Problem z dostępem do Docker w VM',
                'solution': 'SSH do VM i sprawdź Docker: ssh ubuntu@VM_IP'
            })
        
        # Sprawdź firewall
        ufw_status = self.results['tests'].get('firewall_settings', {}).get('ufw_status', {})
        if 'Status: active' in ufw_status.get('stdout', ''):
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'UFW firewall jest aktywny',
                'solution': 'sudo ufw allow 80 lub sudo ufw allow from 192.168.0.0/16'
            })
        
        self.results['recommendations'] = recommendations
        
        # Podsumowanie
        for test_name, test_data in self.results['tests'].items():
            if isinstance(test_data, dict):
                for subtest, result in test_data.items():
                    if isinstance(result, dict) and 'success' in result:
                        if result['success']:
                            self.results['summary']['passed'] += 1
                        else:
                            self.results['summary']['failed'] += 1
    
    def create_fix_script(self):
        """Utwórz skrypt naprawczy"""
        fix_script = """#!/bin/bash
# DockerVirt Auto-Fix Script
# Generated by comprehensive diagnostic

echo "🔧 DockerVirt Auto-Fix Script"
echo "=============================="

"""
        
        # Dodaj komendy naprawcze na podstawie rekomendacji
        for rec in self.results['recommendations']:
            if rec['priority'] == 'HIGH':
                fix_script += f"""
echo "Fixing: {rec['issue']}"
{rec['solution']}
sleep 2
"""
        
        fix_script += """
echo ""
echo "✅ Auto-fix completed. Please run the diagnostic script again to verify."
echo "Re-run: python3 scripts/comprehensive_network_diagnostic.py"
"""
        
        fix_script_path = "/tmp/dockvirt_autofix.sh"
        with open(fix_script_path, 'w') as f:
            f.write(fix_script)
        
        os.chmod(fix_script_path, 0o755)
        self.log(f"Skrypt naprawczy utworzony: {fix_script_path}")
        return fix_script_path
    
    def print_summary(self):
        """Wyświetl podsumowanie"""
        print("\n" + "="*60)
        print("🔍 PODSUMOWANIE DIAGNOSTYKI DOCKVIRT")
        print("="*60)
        print(f"📊 Testy: {self.results['summary']['passed']} ✅ / {self.results['summary']['failed']} ❌")
        print(f"📝 Log file: {self.log_file}")
        
        if self.results['recommendations']:
            print(f"\n🚨 ZNALEZIONE PROBLEMY ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"{i}. [{rec['priority']}] {rec['issue']}")
                print(f"   💡 Rozwiązanie: {rec['solution']}")
        else:
            print("\n✅ Nie znaleziono problemów!")
        
        # Sprawdź dostępność z sieci
        host_ip = self.results['tests'].get('basic_connectivity', {}).get('host_ip', {}).get('ip')
        external_http = self.results['tests'].get('port_forwarding', {}).get('external_http', {})
        
        print(f"\n🌐 DOSTĘP Z SIECI LOKALNEJ:")
        if host_ip:
            print(f"Host IP: {host_ip}")
            if external_http and external_http.get('success'):
                print(f"✅ Dostępne z sieci: http://{host_ip}:80/")
            else:
                print(f"❌ Niedostępne z sieci: http://{host_ip}:80/")
        
        print(f"\n📄 Szczegółowe wyniki zapisane w: /tmp/dockvirt_diagnostic_results.json")
    
    def run_all_tests(self):
        """Uruchom wszystkie testy"""
        self.log("🚀 Rozpoczynam kompleksową diagnostykę DockerVirt...")
        
        try:
            self.test_basic_connectivity()
            self.test_libvirt_status()  
            self.test_vm_status()
            self.test_vm_connectivity()
            self.test_port_forwarding()
            self.test_docker_in_vm()
            self.test_firewall_settings()
            self.test_dockvirt_config()
            
            self.generate_recommendations()
            
            # Zapisz wyniki
            with open('/tmp/dockvirt_diagnostic_results.json', 'w') as f:
                json.dump(self.results, f, indent=2)
            
            # Utwórz skrypt naprawczy
            fix_script = self.create_fix_script()
            
            self.print_summary()
            
            if self.results['recommendations']:
                print(f"\n🔧 Uruchom skrypt naprawczy: bash {fix_script}")
            
        except KeyboardInterrupt:
            self.log("Diagnostyka przerwana przez użytkownika", "WARNING")
        except Exception as e:
            self.log(f"BŁĄD podczas diagnostyki: {str(e)}", "ERROR")

def main():
    if os.geteuid() == 0:
        print("❌ Nie uruchamiaj jako root. Użyj: python3 script.py")
        sys.exit(1)
    
    diagnostic = NetworkDiagnostic()
    diagnostic.run_all_tests()

if __name__ == "__main__":
    main()
