#!/usr/bin/env python3
"""
DockerVirt Network Expose - Prosty skrypt do udostępnienia VM w sieci LAN
Wykorzystuje istniejące port forwarding i tworzy wirtualne IP
"""

import os
import sys
import subprocess
import socket
import time
import ipaddress
import argparse
import signal
import re

class DockerVirtNetworkExpose:
    """Upraszczona wersja dla istniejącego port forwarding"""
    
    def __init__(self, interface=None):
        self.interface = interface or self.detect_interface()
        self.virtual_ips = []
        self.vm_ports = []
        
    def detect_interface(self):
        """Auto-wykrywa interfejs sieciowy"""
        try:
            # Spróbuj znaleźć interfejs z domyślną trasą
            cmd = "ip route show default | awk '{print $5}' | head -1"
            interface = subprocess.check_output(cmd, shell=True).decode().strip()
            
            if not interface:
                # Fallback - znajdź interfejs z IP (nie localhost, nie docker)
                cmd2 = "ip addr show | grep -E 'inet.*192\\.|inet.*10\\.|inet.*172\\.' | grep -v '127\\.' | head -1"
                result = subprocess.check_output(cmd2, shell=True).decode()
                if result:
                    # Wyciągnij nazwę interfejsu z końca linii
                    interface = result.strip().split()[-1]
            
            return interface or "eth0"
            
        except:
            return "eth0"
    
    def check_permissions(self):
        """Sprawdza czy można uruchomić jako sudo"""
        if os.geteuid() != 0:
            print("❌ Skrypt wymaga uprawnień sudo")
            print(f"Uruchom: sudo python3 {sys.argv[0]}")
            return False
        return True
    
    def get_network_info(self):
        """Pobiera info o sieci lokalnej"""
        try:
            # Pobierz IP i sieć dla interfejsu
            cmd = f"ip addr show {self.interface} 2>/dev/null | grep 'inet '"
            result = subprocess.check_output(cmd, shell=True).decode()
            
            # Wyciągnij pierwszy IP/CIDR
            for line in result.split('\n'):
                if 'inet ' in line and not '127.' in line:
                    parts = line.split()
                    for part in parts:
                        if '/' in part and not part.startswith('127.'):
                            ip_cidr = part
                            ip = ip_cidr.split('/')[0]
                            cidr = ip_cidr.split('/')[1]
                            
                            # Oblicz sieć
                            network = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
                            
                            print(f"📡 Interfejs: {self.interface}")
                            print(f"📍 Host IP: {ip}/{cidr}")
                            print(f"🌐 Sieć: {network}")
                            
                            return ip, str(network.network_address), cidr
            
        except Exception as e:
            print(f"❌ Błąd sieci: {e}")
        
        return None, None, None
    
    def find_free_ip(self, network_base, cidr):
        """Znajdź jeden wolny IP w sieci"""
        try:
            network = ipaddress.IPv4Network(f"{network_base}/{cidr}", strict=False)
            
            # Zacznij od .200 dla bezpieczeństwa
            for ip in network.hosts():
                last_octet = int(str(ip).split('.')[-1])
                if last_octet < 200:
                    continue
                if last_octet > 220:  # Sprawdź tylko 20 adresów
                    break
                    
                ip_str = str(ip)
                
                # Quick ping test
                ping_cmd = f"ping -c 1 -W 1 {ip_str} >/dev/null 2>&1"
                if subprocess.run(ping_cmd, shell=True).returncode != 0:
                    print(f"🔍 Znaleziono wolny IP: {ip_str}")
                    return ip_str
            
        except Exception as e:
            print(f"❌ Błąd szukania IP: {e}")
        
        return None
    
    def create_virtual_ip(self, virtual_ip, cidr="24"):
        """Tworzy wirtualny IP na interfejsie"""
        try:
            # Dodaj alias
            label = f"{self.interface}:dockvirt1"
            cmd = f"ip addr add {virtual_ip}/{cidr} dev {self.interface} label {label}"
            subprocess.run(cmd, shell=True, check=True)
            
            # Włącz IP forwarding
            subprocess.run("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True)
            
            # Ogłoś w sieci przez gratuitous ARP
            arp_cmd = f"arping -U -I {self.interface} -c 3 {virtual_ip} >/dev/null 2>&1"
            subprocess.run(arp_cmd, shell=True)
            
            self.virtual_ips.append(virtual_ip)
            print(f"✅ Utworzono wirtualny IP: {virtual_ip}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd tworzenia IP: {e}")
            return False
    
    def setup_forwarding_to_localhost(self, virtual_ip, localhost_port=8080, expose_port=80):
        """Przekieruj ruch z wirtualnego IP na localhost:port"""
        try:
            # Usuń istniejące reguły
            subprocess.run(
                f"iptables -t nat -D PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination 127.0.0.1:{localhost_port} 2>/dev/null", 
                shell=True
            )
            
            # Dodaj nową regułę NAT
            nat_cmd = f"iptables -t nat -A PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination 127.0.0.1:{localhost_port}"
            subprocess.run(nat_cmd, shell=True, check=True)
            
            # Zezwól na forward
            forward_cmd = f"iptables -A FORWARD -d 127.0.0.1 -p tcp --dport {localhost_port} -j ACCEPT"
            subprocess.run(forward_cmd, shell=True)
            
            print(f"✅ Port forwarding: {virtual_ip}:{expose_port} → localhost:{localhost_port}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Błąd port forwarding: {e}")
            return False
    
    def test_connectivity(self, virtual_ip, port=80):
        """Test dostępności wirtualnego IP"""
        try:
            test_cmd = f"curl -s -m 3 http://{virtual_ip}:{port}/ >/dev/null 2>&1"
            if subprocess.run(test_cmd, shell=True).returncode == 0:
                print(f"✅ Test connectivity: {virtual_ip}:{port} - SUCCESS")
                return True
            else:
                print(f"❌ Test connectivity: {virtual_ip}:{port} - FAILED")
                return False
        except:
            return False
    
    def cleanup(self):
        """Usuwa wirtualne IP"""
        if self.virtual_ips:
            print("\n🧹 Czyszczenie wirtualnych IP...")
            for ip in self.virtual_ips:
                try:
                    subprocess.run(f"ip addr del {ip}/24 dev {self.interface} 2>/dev/null", shell=True)
                    print(f"   ✅ Usunięto: {ip}")
                except:
                    pass

def main():
    parser = argparse.ArgumentParser(description='DockerVirt Network Expose - Udostępnij VM w sieci LAN')
    parser.add_argument('-i', '--interface', help='Interfejs sieciowy')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port localhost (default: 8080)')
    parser.add_argument('--virtual-ip', help='Konkretny IP wirtualny')
    parser.add_argument('--expose-port', type=int, default=80, help='Port do udostępnienia (default: 80)')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║            DockerVirt Network Expose                         ║
║          Udostępnij VM w całej sieci LAN                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Sprawdź czy localhost:port działa
    print(f"🔍 Sprawdzanie localhost:{args.port}...")
    test_local = subprocess.run(f"curl -s -m 3 http://localhost:{args.port}/ >/dev/null 2>&1", shell=True)
    
    if test_local.returncode != 0:
        print(f"❌ localhost:{args.port} nie odpowiada")
        print("Upewnij się, że DockerVirt VM jest uruchomiony i dostępny na tym porcie")
        sys.exit(1)
    
    print(f"✅ localhost:{args.port} działa poprawnie")
    
    # Inicjalizacja
    exposer = DockerVirtNetworkExpose(args.interface)
    
    if not exposer.check_permissions():
        sys.exit(1)
    
    # Pobierz info o sieci
    host_ip, network_base, cidr = exposer.get_network_info()
    if not host_ip:
        print("❌ Nie można wykryć sieci")
        sys.exit(1)
    
    # Obsługa sygnałów
    def cleanup_handler(sig, frame):
        print("\n\n⚠️ Zatrzymywanie...")
        exposer.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        # Znajdź lub użyj podanego IP
        if args.virtual_ip:
            virtual_ip = args.virtual_ip
            print(f"🎯 Używam podanego IP: {virtual_ip}")
        else:
            virtual_ip = exposer.find_free_ip(network_base, cidr)
            if not virtual_ip:
                print("❌ Nie znaleziono wolnego IP")
                sys.exit(1)
        
        print(f"\n🚀 Konfigurowanie dostępu sieciowego...")
        
        # Utwórz wirtualny IP
        if not exposer.create_virtual_ip(virtual_ip, cidr):
            sys.exit(1)
        
        # Skonfiguruj przekierowanie
        if not exposer.setup_forwarding_to_localhost(virtual_ip, args.port, args.expose_port):
            sys.exit(1)
        
        # Test
        time.sleep(1)
        success = exposer.test_connectivity(virtual_ip, args.expose_port)
        
        # Podsumowanie
        print("\n" + "="*65)
        print("✅ DOCKVIRT VM DOSTĘPNY Z CAŁEJ SIECI LOKALNEJ")
        print("="*65)
        
        print(f"\n🌐 ADRES SIECIOWY:")
        print(f"   http://{virtual_ip}:{args.expose_port}")
        
        print(f"\n🧪 TEST Z INNYCH URZĄDZEŃ:")
        print(f"   1. Smartfon/tablet: http://{virtual_ip}")
        print(f"   2. Inny komputer: http://{virtual_ip}")
        print(f"   3. Ping test: ping {virtual_ip}")
        
        print(f"\n📋 PRZEKIEROWANIE:")
        print(f"   {virtual_ip}:{args.expose_port} → localhost:{args.port}")
        print(f"   Status: {'✅ DZIAŁA' if success else '❌ PROBLEM'}")
        
        print(f"\n💡 WSKAZÓWKI:")
        print(f"   - NIE trzeba konfigurować DNS ani /etc/hosts")
        print(f"   - Urządzenia muszą być w tej samej sieci WiFi/LAN")
        print(f"   - IP {virtual_ip} jest bezpośrednio dostępny")
        
        print("\n" + "="*65)
        print("⚠️  Naciśnij Ctrl+C aby zatrzymać")
        print("="*65 + "\n")
        
        # Główna pętla - utrzymuj ARP
        while True:
            time.sleep(30)
            # Odśwież ARP co 30 sekund
            subprocess.run(f"arping -U -I {exposer.interface} -c 1 {virtual_ip} >/dev/null 2>&1", shell=True)
            
    except KeyboardInterrupt:
        print("\nZatrzymywanie...")
    finally:
        exposer.cleanup()

if __name__ == "__main__":
    main()
