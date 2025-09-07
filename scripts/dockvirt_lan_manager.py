#!/usr/bin/env python3
"""
DockerVirt LAN Manager - VM widoczne w całej sieci lokalnej
Tworzy wirtualne IP dla DockerVirt VM dostępne z każdego urządzenia w sieci
"""

import os
import sys
import subprocess
import socket
import threading
import time
import json
import ipaddress
import argparse
import signal
import re
from datetime import datetime

class DockerVirtLANManager:
    """Zarządza DockerVirt VM z pełną widocznością w sieci lokalnej"""
    
    def __init__(self, interface=None):
        self.interface = interface or self.detect_interface()
        self.virtual_ips = []
        self.vm_mappings = {}  # vm_name -> (virtual_ip, vm_ip, port)
        self.active_vms = []
        
    def check_root(self):
        """Sprawdza uprawnienia root"""
        if os.geteuid() != 0:
            print("❌ Ten skrypt wymaga uprawnień sudo!")
            print(f"Uruchom: sudo python3 {sys.argv[0]}")
            sys.exit(1)
    
    def detect_interface(self):
        """Auto-wykrywa główny interfejs sieciowy"""
        try:
            cmd = "ip route | grep default | awk '{print $5}' | head -1"
            interface = subprocess.check_output(cmd, shell=True).decode().strip()
            if not interface:
                # Fallback - znajdź aktywny interfejs z IP
                cmd2 = "ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1"
                result = subprocess.check_output(cmd2, shell=True).decode()
                interface = result.split()[-1] if result else "eth0"
            
            print(f"🔍 Auto-wykryto interfejs: {interface}")
            return interface
        except:
            print("⚠️ Nie można wykryć interfejsu, używam eth0")
            return "eth0"
    
    def get_network_info(self):
        """Pobiera informacje o sieci lokalnej"""
        try:
            cmd = f"ip addr show {self.interface}"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            # Wyciągnij IP i maskę
            ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)'
            match = re.search(ip_pattern, result)
            
            if match:
                ip = match.group(1)
                cidr = match.group(2)
                network = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
                
                print(f"📡 Interfejs: {self.interface}")
                print(f"📍 Host IP: {ip}/{cidr}")
                print(f"🌐 Sieć: {network.network_address}/{cidr}")
                print(f"🔢 Dostępne hosty: {network.num_addresses - 2}")
                
                return str(ip), str(network.network_address), cidr
            
        except Exception as e:
            print(f"❌ Błąd pobierania informacji o sieci: {e}")
            return None, None, None
    
    def find_available_ips(self, base_network, cidr, count=5):
        """Znajduje wolne IP w sieci lokalnej"""
        network = ipaddress.IPv4Network(f"{base_network}/{cidr}", strict=False)
        available_ips = []
        
        print(f"🔍 Szukanie {count} wolnych IP w sieci {network}...")
        
        # Zacznij od .150 aby uniknąć konfliktów z DHCP
        start_range = 150
        checked = 0
        
        for ip in network.hosts():
            if int(str(ip).split('.')[-1]) < start_range:
                continue
            
            if checked >= 50:  # Max 50 sprawdzeń
                break
            
            ip_str = str(ip)
            
            # Test ping
            ping_result = subprocess.run(
                f"ping -c 1 -W 1 {ip_str}", 
                shell=True, capture_output=True
            )
            
            if ping_result.returncode != 0:  # Brak odpowiedzi = wolny
                # Dodatkowy test ARP
                arp_result = subprocess.run(
                    f"arping -c 1 -w 1 {ip_str} 2>/dev/null", 
                    shell=True, capture_output=True
                )
                
                if arp_result.returncode != 0:
                    available_ips.append(ip_str)
                    print(f"   ✅ Dostępny: {ip_str}")
                    
                    if len(available_ips) >= count:
                        break
            
            checked += 1
        
        return available_ips
    
    def create_virtual_ip(self, ip_address, label, cidr="24"):
        """Tworzy wirtualny IP widoczny w sieci"""
        try:
            full_label = f"{self.interface}:{label}"
            
            # Dodaj alias IP
            cmd = f"ip addr add {ip_address}/{cidr} dev {self.interface} label {full_label}"
            subprocess.run(cmd, shell=True, check=True)
            
            # Włącz forwarding
            subprocess.run("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True)
            
            # Włącz proxy ARP
            subprocess.run(f"echo 1 > /proc/sys/net/ipv4/conf/{self.interface}/proxy_arp", shell=True)
            
            # Ogłoś w sieci
            self.announce_ip_in_network(ip_address)
            
            self.virtual_ips.append((ip_address, full_label))
            print(f"✅ Utworzono wirtualny IP: {ip_address}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd tworzenia IP {ip_address}: {e}")
            return False
    
    def announce_ip_in_network(self, ip_address):
        """Ogłasza IP w sieci przez gratuitous ARP"""
        try:
            # Gratuitous ARP
            subprocess.run(f"arping -U -I {self.interface} -c 3 {ip_address} 2>/dev/null", shell=True)
            
            # Dodaj do ARP cache
            mac = self.get_interface_mac()
            if mac:
                subprocess.run(f"ip neigh add {ip_address} lladdr {mac} dev {self.interface} nud permanent 2>/dev/null", shell=True)
            
            print(f"   📢 Ogłoszono {ip_address} w sieci")
            
        except Exception as e:
            print(f"   ⚠️ Nie udało się ogłosić {ip_address}: {e}")
    
    def get_interface_mac(self):
        """Pobiera MAC address interfejsu"""
        try:
            cmd = f"ip link show {self.interface} | grep ether | awk '{{print $2}}'"
            return subprocess.check_output(cmd, shell=True).decode().strip()
        except:
            return None
    
    def get_running_vms(self):
        """Pobiera listę uruchomionych DockerVirt VM"""
        try:
            # Lista VM z virsh
            cmd = "sudo virsh list --state-running"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            vms = []
            for line in result.split('\n')[2:]:  # Skip header
                if line.strip() and not line.startswith('-'):
                    parts = line.split()
                    if len(parts) >= 2:
                        vm_name = parts[1]
                        if vm_name != "Name":  # Skip header
                            vms.append(vm_name)
            
            return vms
            
        except Exception as e:
            print(f"❌ Błąd pobierania VM: {e}")
            return []
    
    def get_vm_ip(self, vm_name):
        """Pobiera IP VM z DHCP leases"""
        try:
            cmd = f"sudo virsh net-dhcp-leases default | grep {vm_name}"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            # Wyciągnij IP
            ip_match = re.search(r'192\.168\.122\.\d+', result)
            if ip_match:
                vm_ip = ip_match.group()
                print(f"   📍 VM {vm_name} IP: {vm_ip}")
                return vm_ip
            
        except:
            pass
        
        return None
    
    def setup_port_forwarding(self, virtual_ip, vm_ip, vm_port=80, expose_port=80):
        """Konfiguruje przekierowanie portów z wirtualnego IP do VM"""
        try:
            # Usuń istniejące reguły (jeśli są)
            subprocess.run(
                f"iptables -t nat -D PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination {vm_ip}:{vm_port} 2>/dev/null", 
                shell=True
            )
            
            # Dodaj nowe reguły
            nat_cmd = f"iptables -t nat -A PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination {vm_ip}:{vm_port}"
            forward_cmd = f"iptables -A FORWARD -d {vm_ip} -p tcp --dport {vm_port} -j ACCEPT"
            
            subprocess.run(nat_cmd, shell=True, check=True)
            subprocess.run(forward_cmd, shell=True, check=True)
            
            # Zezwól na ruch zwrotny
            subprocess.run("iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT", shell=True)
            
            print(f"   🔄 Port forwarding: {virtual_ip}:{expose_port} → {vm_ip}:{vm_port}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Błąd port forwarding: {e}")
            return False
    
    def configure_vm_for_lan(self, vm_name, virtual_ip):
        """Konfiguruje pojedynczy VM dla dostępu z sieci LAN"""
        vm_ip = self.get_vm_ip(vm_name)
        if not vm_ip:
            print(f"   ❌ Nie można pobrać IP dla VM {vm_name}")
            return False
        
        # Sprawdź czy VM odpowiada na porcie 80
        vm_responding = False
        for port in [80, 8080, 3000, 8000]:  # Typowe porty web
            test_cmd = f"timeout 3 curl -s http://{vm_ip}:{port}/ >/dev/null 2>&1"
            if subprocess.run(test_cmd, shell=True).returncode == 0:
                print(f"   ✅ VM {vm_name} odpowiada na porcie {port}")
                
                # Skonfiguruj port forwarding
                if self.setup_port_forwarding(virtual_ip, vm_ip, port, 80):
                    self.vm_mappings[vm_name] = (virtual_ip, vm_ip, port)
                    vm_responding = True
                    break
        
        if not vm_responding:
            print(f"   ⚠️ VM {vm_name} nie odpowiada na typowych portach web")
            # Spróbuj port forwarding na port 80 mimo wszystko
            if self.setup_port_forwarding(virtual_ip, vm_ip, 80, 80):
                self.vm_mappings[vm_name] = (virtual_ip, vm_ip, 80)
        
        return True
    
    def test_vm_accessibility(self, virtual_ip, vm_name):
        """Testuje dostępność VM przez wirtualny IP"""
        try:
            test_cmd = f"timeout 5 curl -s http://{virtual_ip}:80/"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Test dostępności: {vm_name} ({virtual_ip}) - SUCCESS")
                return True
            else:
                print(f"   ❌ Test dostępności: {vm_name} ({virtual_ip}) - FAILED")
                return False
                
        except:
            print(f"   ❌ Test dostępności: {vm_name} ({virtual_ip}) - ERROR")
            return False
    
    def cleanup_virtual_ips(self):
        """Usuwa wszystkie wirtualne IP"""
        print("\n🧹 Czyszczenie wirtualnych IP...")
        for ip, label in self.virtual_ips:
            try:
                subprocess.run(f"ip addr del {ip}/24 dev {self.interface}", shell=True)
                subprocess.run(f"arp -d {ip} 2>/dev/null", shell=True)
                print(f"   ✅ Usunięto: {ip}")
            except:
                print(f"   ⚠️ Nie udało się usunąć: {ip}")
    
    def print_access_summary(self):
        """Wyświetla podsumowanie dostępu"""
        if not self.vm_mappings:
            print("❌ Brak skonfigurowanych VM")
            return
        
        print("\n" + "="*70)
        print("✅ DOCKVIRT VM DOSTĘPNE Z CAŁEJ SIECI LOKALNEJ")
        print("="*70)
        
        print("\n📋 LISTA VM (dostępne z każdego urządzenia w sieci):\n")
        
        for vm_name, (virtual_ip, vm_ip, port) in self.vm_mappings.items():
            print(f"   🖥️  {vm_name}")
            print(f"      📍 Adres sieciowy: http://{virtual_ip}")
            print(f"      🔗 VM Internal: {vm_ip}:{port}")
            print()
        
        print("="*70)
        print("🧪 JAK PRZETESTOWAĆ:")
        print("="*70)
        
        first_vm = list(self.vm_mappings.values())[0]
        virtual_ip = first_vm[0]
        
        print("\n1. Z TEGO KOMPUTERA:")
        print(f"   curl http://{virtual_ip}")
        print(f"   Przeglądarka: http://{virtual_ip}")
        
        print("\n2. Z INNEGO KOMPUTERA/LAPTOPA W SIECI:")
        print("   Otwórz przeglądarkę i wpisz powyższy adres")
        print("   NIE POTRZEBUJESZ konfigurować DNS ani hosts!")
        
        print("\n3. ZE SMARTFONA/TABLETU:")
        print("   Połącz z tą samą siecią WiFi")
        print(f"   Wpisz: http://{virtual_ip}")
        
        print("\n4. PING TEST Z INNEGO KOMPUTERA:")
        for vm_name, (virtual_ip, _, _) in self.vm_mappings.items():
            print(f"   ping {virtual_ip}  # {vm_name}")
        
        print("\n" + "="*70)
        print("⚠️  Naciśnij Ctrl+C aby zatrzymać i wyczyścić")
        print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description='DockerVirt LAN Manager - VM widoczne w sieci')
    parser.add_argument('-i', '--interface', help='Interfejs sieciowy (auto-detect)')
    parser.add_argument('-v', '--vm', action='append', help='Konkretne VM do konfiguracji')
    parser.add_argument('--base-ip', help='Bazowy zakres IP (auto jeśli pominięte)')
    parser.add_argument('--test-only', action='store_true', help='Tylko test bez tworzenia IP')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║              DockerVirt LAN Manager                          ║
║        VM dostępne z całej sieci lokalnej                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Inicjalizacja
    manager = DockerVirtLANManager(args.interface)
    
    if not args.test_only:
        manager.check_root()
    
    # Pobierz informacje o sieci
    host_ip, network_base, cidr = manager.get_network_info()
    if not host_ip:
        print("❌ Nie można pobrać informacji o sieci")
        sys.exit(1)
    
    # Pobierz listę VM
    running_vms = manager.get_running_vms()
    if not running_vms:
        print("❌ Brak uruchomionych DockerVirt VM")
        print("Uruchom VM przez: cd examples/[projekt] && dockvirt up")
        sys.exit(1)
    
    print(f"\n🖥️ Znalezione uruchomione VM: {', '.join(running_vms)}")
    
    # Filtruj VM jeśli podano konkretne
    if args.vm:
        running_vms = [vm for vm in running_vms if vm in args.vm]
        if not running_vms:
            print("❌ Żadne z podanych VM nie jest uruchomione")
            sys.exit(1)
    
    if args.test_only:
        print("\n🧪 TRYB TEST-ONLY: Sprawdzanie dostępności VM")
        for vm_name in running_vms:
            vm_ip = manager.get_vm_ip(vm_name)
            if vm_ip:
                for port in [80, 8080, 3000]:
                    test_cmd = f"timeout 3 curl -s http://{vm_ip}:{port}/ >/dev/null"
                    if subprocess.run(test_cmd, shell=True).returncode == 0:
                        print(f"   ✅ {vm_name} ({vm_ip}:{port}) - dostępny")
                        break
                else:
                    print(f"   ❌ {vm_name} ({vm_ip}) - brak odpowiedzi na portach web")
        sys.exit(0)
    
    # Obsługa sygnałów
    def cleanup_handler(sig, frame):
        print("\n\n⚠️ Zatrzymywanie i czyszczenie...")
        manager.cleanup_virtual_ips()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # Znajdź dostępne IP
        needed_ips = len(running_vms)
        available_ips = manager.find_available_ips(network_base, cidr, needed_ips)
        
        if len(available_ips) < needed_ips:
            print(f"❌ Potrzeba {needed_ips} IP, znaleziono tylko {len(available_ips)}")
            sys.exit(1)
        
        print(f"\n🚀 Konfigurowanie {needed_ips} VM dla dostępu sieciowego...\n")
        
        # Konfiguruj każdy VM
        for i, vm_name in enumerate(running_vms):
            virtual_ip = available_ips[i]
            
            print(f"📦 Konfiguracja {i+1}/{needed_ips}: {vm_name}")
            
            # Utwórz wirtualny IP
            if manager.create_virtual_ip(virtual_ip, f"dockvirt_{vm_name}"):
                # Skonfiguruj VM
                if manager.configure_vm_for_lan(vm_name, virtual_ip):
                    # Test dostępności
                    time.sleep(1)  # Daj czas na propagację
                    manager.test_vm_accessibility(virtual_ip, vm_name)
            
            print()  # Odstęp
        
        # Ponowne ogłoszenie w sieci
        print("📢 Ogłaszanie IP w sieci...")
        for ip, _ in manager.virtual_ips:
            manager.announce_ip_in_network(ip)
        
        # Pokaż podsumowanie
        manager.print_access_summary()
        
        # Główna pętla - odświeżanie ARP
        print("✅ System aktywny. Odświeżam tablice ARP co 30 sekund...")
        while True:
            time.sleep(30)
            for ip, _ in manager.virtual_ips:
                try:
                    subprocess.run(f"arping -U -I {manager.interface} -c 1 {ip} 2>/dev/null", shell=True)
                except:
                    pass
            
    except KeyboardInterrupt:
        print("\nZatrzymywanie...")
    finally:
        manager.cleanup_virtual_ips()

if __name__ == "__main__":
    main()
