#!/usr/bin/env python3
"""
DockerVirt LAN Expose - Prosty skrypt udostępniający VM w sieci lokalnej
Pracuje z istniejącym localhost:8080 forwarding
"""

import os
import sys
import subprocess
import time
import signal

def run_cmd(cmd, check=True, capture=True):
    """Uruchamia komendę shell"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return result.returncode == 0, "", ""
    except subprocess.CalledProcessError as e:
        return False, "", str(e)

def get_network_info():
    """Pobiera informacje o sieci"""
    # Znajdź główny interfejs
    success, interface, _ = run_cmd("ip route show default | awk '{print $5}' | head -1")
    if not success or not interface:
        interface = "eth0"
    
    # Pobierz IP hosta
    success, host_ip, _ = run_cmd(f"ip addr show {interface} | grep 'inet ' | grep -v '127.' | head -1 | awk '{{print $2}}' | cut -d/ -f1")
    if not success or not host_ip:
        print("❌ Nie można pobrać IP hosta")
        return None, None, None
    
    # Pobierz sieć
    success, cidr_info, _ = run_cmd(f"ip addr show {interface} | grep 'inet ' | grep -v '127.' | head -1 | awk '{{print $2}}'")
    if success and '/' in cidr_info:
        cidr = cidr_info.split('/')[1]
    else:
        cidr = "24"
    
    print(f"📡 Interfejs: {interface}")
    print(f"📍 Host IP: {host_ip}/{cidr}")
    
    return interface, host_ip, cidr

def find_free_ip(host_ip):
    """Znajdź wolny IP w tej samej sieci"""
    base_parts = host_ip.split('.')
    base_network = '.'.join(base_parts[:3])
    
    # Spróbuj IP od .200 do .220
    for i in range(200, 221):
        test_ip = f"{base_network}.{i}"
        if test_ip == host_ip:
            continue
            
        # Quick ping test
        success, _, _ = run_cmd(f"ping -c 1 -W 1 {test_ip}", check=False)
        if not success:  # Brak odpowiedzi = wolny
            print(f"🔍 Wolny IP: {test_ip}")
            return test_ip
    
    return None

def create_virtual_ip(interface, virtual_ip, cidr):
    """Tworzy wirtualny IP"""
    # Dodaj IP alias
    success, _, error = run_cmd(f"ip addr add {virtual_ip}/{cidr} dev {interface} label {interface}:dockvirt")
    if not success:
        print(f"❌ Błąd dodawania IP: {error}")
        return False
    
    # Włącz IP forwarding
    run_cmd("echo 1 > /proc/sys/net/ipv4/ip_forward", check=False)
    
    # Ogłoś w sieci przez ARP
    run_cmd(f"arping -U -I {interface} -c 3 {virtual_ip}", check=False, capture=False)
    
    print(f"✅ Utworzono wirtualny IP: {virtual_ip}")
    return True

def setup_port_forwarding(virtual_ip, local_port=8080, expose_port=80):
    """Przekieruj z wirtualnego IP na localhost:port"""
    # Usuń stare reguły
    run_cmd(f"iptables -t nat -D PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination 127.0.0.1:{local_port}", check=False)
    
    # Dodaj nową regułę
    success, _, error = run_cmd(f"iptables -t nat -A PREROUTING -d {virtual_ip} -p tcp --dport {expose_port} -j DNAT --to-destination 127.0.0.1:{local_port}")
    if not success:
        print(f"❌ Błąd port forwarding: {error}")
        return False
    
    # Zezwól na forward
    run_cmd(f"iptables -A FORWARD -d 127.0.0.1 -p tcp --dport {local_port} -j ACCEPT", check=False)
    
    print(f"✅ Port forwarding: {virtual_ip}:{expose_port} → localhost:{local_port}")
    return True

def test_access(virtual_ip, port=80):
    """Test dostępności"""
    success, _, _ = run_cmd(f"curl -s -m 3 http://{virtual_ip}:{port}/", check=False)
    if success:
        print(f"✅ Test: {virtual_ip}:{port} - działa!")
        return True
    else:
        print(f"❌ Test: {virtual_ip}:{port} - nie odpowiada")
        return False

def cleanup(interface, virtual_ip, cidr):
    """Usuwa wirtualny IP"""
    print(f"\n🧹 Usuwam wirtualny IP: {virtual_ip}")
    run_cmd(f"ip addr del {virtual_ip}/{cidr} dev {interface}", check=False)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
DockerVirt LAN Expose - Udostępnia VM w całej sieci lokalnej

Użycie: sudo python3 expose_to_lan.py [--port PORT]

Opcje:
  --port PORT    Port localhost (domyślnie 8080)
  -h, --help     Pomoc

Przykład:
  sudo python3 expose_to_lan.py --port 8080
        """)
        return
    
    # Parsuj argumenty
    local_port = 8080
    if '--port' in sys.argv:
        try:
            port_idx = sys.argv.index('--port') + 1
            local_port = int(sys.argv[port_idx])
        except:
            pass
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║              DockerVirt LAN Expose                           ║
║        Udostępnia VM całej sieci lokalnej                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Sprawdź uprawnienia
    if os.geteuid() != 0:
        print("❌ Skrypt wymaga uprawnień sudo")
        print(f"Uruchom: sudo python3 {sys.argv[0]}")
        return
    
    # Sprawdź czy localhost działa
    print(f"🔍 Sprawdzanie localhost:{local_port}...")
    success, _, _ = run_cmd(f"curl -s -m 3 http://localhost:{local_port}/", check=False)
    if not success:
        print(f"❌ localhost:{local_port} nie odpowiada")
        print("Upewnij się, że DockerVirt VM działa")
        return
    
    print(f"✅ localhost:{local_port} działa")
    
    # Pobierz info o sieci
    interface, host_ip, cidr = get_network_info()
    if not interface or not host_ip:
        print("❌ Nie można wykryć sieci")
        return
    
    # Znajdź wolny IP
    virtual_ip = find_free_ip(host_ip)
    if not virtual_ip:
        print("❌ Nie znaleziono wolnego IP")
        return
    
    # Obsługa Ctrl+C
    def cleanup_handler(sig, frame):
        cleanup(interface, virtual_ip, cidr)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        print(f"\n🚀 Konfigurowanie dostępu sieciowego...")
        
        # Utwórz wirtualny IP
        if not create_virtual_ip(interface, virtual_ip, cidr):
            return
        
        # Skonfiguruj forwarding
        if not setup_port_forwarding(virtual_ip, local_port, 80):
            cleanup(interface, virtual_ip, cidr)
            return
        
        # Test
        time.sleep(2)
        success = test_access(virtual_ip, 80)
        
        # Podsumowanie
        print("\n" + "="*60)
        print("🎉 DOCKVIRT VM DOSTĘPNY W CAŁEJ SIECI!")
        print("="*60)
        
        print(f"\n🌐 ADRES DLA INNYCH URZĄDZEŃ:")
        print(f"   http://{virtual_ip}")
        
        print(f"\n🧪 TESTOWANIE:")
        print(f"   1. Z tego komputera: curl http://{virtual_ip}")
        print(f"   2. Z telefonu/tabletu: http://{virtual_ip}")
        print(f"   3. Z innego komputera: http://{virtual_ip}")
        print(f"   4. Ping test: ping {virtual_ip}")
        
        print(f"\n📋 KONFIGURACJA:")
        print(f"   Wirtualny IP: {virtual_ip}")
        print(f"   Przekierowanie: {virtual_ip}:80 → localhost:{local_port}")
        print(f"   Status: {'✅ DZIAŁA' if success else '❌ PROBLEM'}")
        
        print(f"\n💡 WAŻNE:")
        print(f"   - Urządzenia muszą być w tej samej sieci")
        print(f"   - NIE potrzebujesz konfigurować DNS")
        print(f"   - IP {virtual_ip} jest bezpośrednio dostępny")
        
        print("\n" + "="*60)
        print("⚠️  Naciśnij Ctrl+C aby zatrzymać")
        print("="*60)
        
        # Główna pętla - odświeżaj ARP
        while True:
            time.sleep(30)
            run_cmd(f"arping -U -I {interface} -c 1 {virtual_ip}", check=False, capture=False)
            
    except KeyboardInterrupt:
        pass
    finally:
        cleanup(interface, virtual_ip, cidr)

if __name__ == "__main__":
    main()
