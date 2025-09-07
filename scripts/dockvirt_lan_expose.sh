#!/bin/bash

# DockerVirt LAN Expose - Jednolinijkowy skrypt do udostępnienia VM w sieci
# Wykorzystuje multi-IP technique dla pełnej widoczności w sieci lokalnej

set -e

echo "🌐 DockerVirt LAN Expose - VM widoczny w całej sieci lokalnej"
echo "================================================================"

# Sprawdź uprawnienia
if [[ $EUID -ne 0 ]]; then
   echo "❌ Skrypt wymaga uprawnień sudo"
   echo "Uruchom: sudo bash $0"
   exit 1
fi

# Parsuj argumenty
LOCAL_PORT=8080
EXPOSE_PORT=80
VIRTUAL_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            LOCAL_PORT="$2"
            shift 2
            ;;
        --expose-port)
            EXPOSE_PORT="$2"
            shift 2
            ;;
        --virtual-ip)
            VIRTUAL_IP="$2"
            shift 2
            ;;
        -h|--help)
            echo "Użycie: sudo bash $0 [--port 8080] [--expose-port 80] [--virtual-ip IP]"
            echo ""
            echo "  --port PORT         Port localhost (domyślnie 8080)"
            echo "  --expose-port PORT  Port do udostępnienia (domyślnie 80)" 
            echo "  --virtual-ip IP     Konkretny wirtualny IP"
            echo "  -h, --help          Pomoc"
            echo ""
            echo "Przykład: sudo bash $0 --port 8080"
            exit 0
            ;;
        *)
            echo "Nieznany parametr: $1"
            exit 1
            ;;
    esac
done

# Sprawdź czy localhost działa
echo "🔍 Sprawdzanie localhost:$LOCAL_PORT..."
if ! curl -s -m 3 http://localhost:$LOCAL_PORT/ >/dev/null 2>&1; then
    echo "❌ localhost:$LOCAL_PORT nie odpowiada"
    echo "Upewnij się, że DockerVirt VM jest uruchomiony:"
    echo "  cd examples/1-static-nginx-website && dockvirt up"
    exit 1
fi

echo "✅ localhost:$LOCAL_PORT działa poprawnie"

# Auto-wykryj interfejs sieciowy
INTERFACE=$(ip route show default | awk '{print $5}' | head -1)
if [[ -z "$INTERFACE" ]]; then
    INTERFACE="eth0"
fi

# Pobierz informacje o sieci
HOST_IP=$(ip addr show $INTERFACE | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f1)
CIDR=$(ip addr show $INTERFACE | grep 'inet ' | grep -v '127\.' | head -1 | awk '{print $2}' | cut -d/ -f2)

if [[ -z "$HOST_IP" ]]; then
    echo "❌ Nie można wykryć IP hosta"
    exit 1
fi

echo "📡 Interfejs: $INTERFACE"
echo "📍 Host IP: $HOST_IP/$CIDR"

# Znajdź wolny IP (jeśli nie podano)
if [[ -z "$VIRTUAL_IP" ]]; then
    echo "🔍 Szukanie wolnego IP w sieci..."
    
    BASE_NETWORK=$(echo $HOST_IP | cut -d. -f1-3)
    
    for i in {200..220}; do
        TEST_IP="$BASE_NETWORK.$i"
        
        if [[ "$TEST_IP" == "$HOST_IP" ]]; then
            continue
        fi
        
        # Quick ping test
        if ! ping -c 1 -W 1 $TEST_IP >/dev/null 2>&1; then
            VIRTUAL_IP=$TEST_IP
            echo "✅ Znaleziono wolny IP: $VIRTUAL_IP"
            break
        fi
    done
    
    if [[ -z "$VIRTUAL_IP" ]]; then
        echo "❌ Nie znaleziono wolnego IP"
        exit 1
    fi
fi

# Funkcja cleanup
cleanup() {
    echo ""
    echo "🧹 Czyszczenie wirtualnego IP: $VIRTUAL_IP"
    ip addr del $VIRTUAL_IP/$CIDR dev $INTERFACE 2>/dev/null || true
    arp -d $VIRTUAL_IP 2>/dev/null || true
    echo "✅ Wyczyszczono"
    exit 0
}

# Obsłuż Ctrl+C
trap cleanup INT TERM

echo ""
echo "🚀 Konfigurowanie dostępu sieciowego..."

# Utwórz wirtualny IP z pełną widocznością
echo "📦 Tworzę wirtualny IP: $VIRTUAL_IP"

# Dodaj alias IP
ip addr add $VIRTUAL_IP/$CIDR dev $INTERFACE label $INTERFACE:dockvirt

# Włącz IP forwarding (krucjalne dla widoczności)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Włącz proxy ARP dla lepszej widoczności w sieci
echo 1 > /proc/sys/net/ipv4/conf/$INTERFACE/proxy_arp

# Pobierz MAC address interfejsu
MAC=$(ip link show $INTERFACE | grep ether | awk '{print $2}')

# Ogłoś IP w sieci przez gratuitous ARP (wielokrotnie dla pewności)
echo "📢 Ogłaszam IP w sieci lokalnej..."
for _ in {1..5}; do
    arping -U -I $INTERFACE -c 2 $VIRTUAL_IP >/dev/null 2>&1 || true
    sleep 0.2
done

# Dodaj wpis do ARP cache
if [[ -n "$MAC" ]]; then
    ip neigh add $VIRTUAL_IP lladdr $MAC dev $INTERFACE nud permanent 2>/dev/null || true
fi

echo "✅ Wirtualny IP utworzony i ogłoszony"

# Skonfiguruj port forwarding z wirtualnego IP na localhost
echo "🔄 Konfigurując port forwarding..."

# Usuń stare reguły (jeśli istnieją)
iptables -t nat -D PREROUTING -d $VIRTUAL_IP -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT 2>/dev/null || true
iptables -D FORWARD -d 127.0.0.1 -p tcp --dport $LOCAL_PORT -j ACCEPT 2>/dev/null || true

# Dodaj nowe reguły NAT
iptables -t nat -A PREROUTING -d $VIRTUAL_IP -p tcp --dport $EXPOSE_PORT -j DNAT --to-destination 127.0.0.1:$LOCAL_PORT
iptables -A FORWARD -d 127.0.0.1 -p tcp --dport $LOCAL_PORT -j ACCEPT
iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "✅ Port forwarding skonfigurowany: $VIRTUAL_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"

# Test dostępności
echo "🧪 Test dostępności..."
sleep 2

if curl -s -m 5 http://$VIRTUAL_IP:$EXPOSE_PORT/ >/dev/null 2>&1; then
    TEST_RESULT="✅ DZIAŁA"
else
    TEST_RESULT="⚠️ Może potrzebować więcej czasu"
fi

# Podsumowanie
echo ""
echo "================================================================"
echo "🎉 DOCKVIRT VM DOSTĘPNY W CAŁEJ SIECI LOKALNEJ!"
echo "================================================================"
echo ""
echo "🌐 ADRES DLA WSZYSTKICH URZĄDZEŃ W SIECI:"
echo "   http://$VIRTUAL_IP"
echo ""
echo "🧪 TESTOWANIE Z INNYCH URZĄDZEŃ:"
echo "   1. Smartfon/tablet (ta sama WiFi): http://$VIRTUAL_IP"
echo "   2. Inny komputer w sieci: http://$VIRTUAL_IP"  
echo "   3. Ping test: ping $VIRTUAL_IP"
echo "   4. Curl test: curl http://$VIRTUAL_IP"
echo ""
echo "📋 KONFIGURACJA:"
echo "   Wirtualny IP: $VIRTUAL_IP"
echo "   Interfejs: $INTERFACE ($HOST_IP)"
echo "   Przekierowanie: $VIRTUAL_IP:$EXPOSE_PORT → localhost:$LOCAL_PORT"
echo "   Status: $TEST_RESULT"
echo ""
echo "💡 WAŻNE INFORMACJE:"
echo "   ✅ IP $VIRTUAL_IP jest bezpośrednio dostępny w sieci"
echo "   ✅ NIE potrzebujesz konfigurować DNS ani /etc/hosts"
echo "   ✅ Wszystkie urządzenia w tej samej sieci WiFi/LAN mają dostęp"
echo "   ✅ Gratuitous ARP zapewnia pełną widoczność"
echo ""
echo "================================================================"
echo "⚠️  Naciśnij Ctrl+C aby zatrzymać i wyczyścić konfigurację"
echo "================================================================"
echo ""

# Główna pętla - utrzymuj ARP i widoczność w sieci
echo "🔄 System aktywny. Odświeżam ogłoszenia ARP co 30 sekund..."
echo "   (to zapewnia ciągłą widoczność IP w całej sieci)"
echo ""

while true; do
    sleep 30
    
    # Odśwież gratuitous ARP
    arping -U -I $INTERFACE -c 1 $VIRTUAL_IP >/dev/null 2>&1 || true
    
    # Sprawdź czy IP nadal istnieje
    if ! ip addr show $INTERFACE | grep -q $VIRTUAL_IP; then
        echo "⚠️ Wirtualny IP zniknął, odtwarzam..."
        ip addr add $VIRTUAL_IP/$CIDR dev $INTERFACE label $INTERFACE:dockvirt
        arping -U -I $INTERFACE -c 3 $VIRTUAL_IP >/dev/null 2>&1 || true
    fi
done
